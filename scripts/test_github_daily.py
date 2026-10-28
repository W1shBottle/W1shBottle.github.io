import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import update_github_daily as feed

NOW = datetime(2026, 10, 28, 1, 0, tzinfo=timezone.utc)


def raw(repo_id=1, **changes):
    item = dict(id=repo_id, full_name=f'owner{repo_id}/project', description='A useful project',
                stargazers_count=1200, language='Python', pushed_at=NOW.isoformat(),
                fork=False, archived=False, private=False, disabled=False, topics=['llm'])
    item.update(changes)
    return item


def candidates(count=30):
    return [dict(feed.normalize(raw(i), NOW), categories=[category])
            for category, base in [('ai', 0), ('dev', 100), ('useful', 200)]
            for i in range(base+1, base+count+1)]


def payload(url):
    category = 'ai' if ('topic%3Allm' in url or 'topic%3Arag' in url) else (
        'dev' if ('topic%3Adeveloper-tools' in url or 'topic%3Acli' in url) else 'useful')
    base = {'ai': 0, 'dev': 100, 'useful': 200}[category]
    return {'items': [raw(i) for i in range(base+1, base+31)], 'incomplete_results': False}


class FilteringTests(unittest.TestCase):
    def test_normalize_constructs_safe_url_and_retains_plain_text(self):
        p = feed.normalize(raw(html_url='javascript:alert(1)', description='  <script> hello  \n world '), NOW)
        self.assertEqual('https://github.com/owner1/project', p['url'])
        self.assertEqual('<script> hello world', p['description'])  # Hugo must escape this text.

    def test_ineligible_or_malformed_repos_are_excluded(self):
        for change in [dict(archived=True), dict(fork=True), dict(private=True), dict(disabled=True),
                       dict(stargazers_count=999), dict(stargazers_count=True), dict(description=None),
                       dict(full_name='x/<script>'), dict(full_name='../../bad'), dict(topics=['awesome-list']),
                       dict(pushed_at=(NOW-timedelta(days=91)).isoformat()), dict(pushed_at='invalid'),
                       dict(pushed_at='2026-10-28T00:00:00'), dict(id=-1)]:
            with self.subTest(change=change):
                self.assertIsNone(feed.normalize(raw(**change), NOW))

    def test_edition_cutoff_uses_china_time_at_eight(self):
        self.assertEqual('2026-10-27', feed.edition_date(NOW.replace(hour=0)-timedelta(seconds=1)).isoformat())
        self.assertEqual('2026-10-28', feed.edition_date(NOW.replace(hour=0)).isoformat())

    def test_search_deduplicates_and_rejects_incomplete_responses(self):
        result = feed.collect(NOW, lambda _: {'items': [raw()], 'incomplete_results': False})
        self.assertEqual(1, len(result))
        self.assertEqual(['ai', 'dev', 'useful'], result[0]['categories'])
        for bad in [{}, {'items': [], 'incomplete_results': True}, {'items': None, 'incomplete_results': False}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                feed.collect(NOW, lambda _: bad)

    def test_quota_determinism_and_daily_rotation(self):
        pool = candidates()
        day = NOW.date()
        selected = feed.choose(pool, day, [])
        self.assertEqual(selected, feed.choose(list(reversed(pool)), day, []))
        self.assertEqual(10, len({r['id'] for r in selected}))
        for category, quota in feed.QUOTAS.items():
            self.assertEqual(quota, sum(r['category'] == category for r in selected))
        self.assertNotEqual(selected, feed.choose(pool, day+timedelta(days=1), []))

    def test_seven_day_cooldown_and_small_pool_relaxation(self):
        pool = candidates()
        history = []
        for offset in range(8):
            day = NOW.date()+timedelta(days=offset)
            selected = feed.choose(pool, day, history)
            seen = {i for h in history for i in h['ids']}
            # With 30 dev candidates, 7 days (28) can be fully unique.
            if offset < 7:
                self.assertFalse(seen & {r['id'] for r in selected})
            history.append({'date': day.isoformat(), 'ids': [r['id'] for r in selected]})
        small = [dict(r, categories=[r['category']]) for r in selected]
        self.assertEqual(10, len(feed.choose(small, day+timedelta(days=1), history)))
        with self.assertRaises(ValueError):
            feed.choose(small[:9], day, history)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.output = self.root/'data/github_daily.json'
        self.cache = self.root/'.cache/github-daily.json'
        self.assertEqual('updated', feed.refresh(self.root, NOW, payload))
        self.original = self.output.read_bytes()

    def test_same_day_never_refetches(self):
        fetch = Mock(side_effect=AssertionError('Unexpected request'))
        self.assertEqual('unchanged', feed.refresh(self.root, NOW+timedelta(hours=4), fetch))
        fetch.assert_not_called()
        self.assertEqual(self.original, self.output.read_bytes())

    def test_api_failures_preserve_contents_and_original_date(self):
        for error in [TimeoutError(), ValueError('bad JSON'), OSError('rate limit')]:
            self.assertEqual('fallback', feed.refresh(self.root, NOW+timedelta(days=1), Mock(side_effect=error)))
            self.assertEqual(self.original, self.output.read_bytes())

    def test_partial_success_does_not_publish_partial_edition(self):
        fetch = Mock(side_effect=[payload('topic%3Allm'), TimeoutError()])
        self.assertEqual('fallback', feed.refresh(self.root, NOW+timedelta(days=1), fetch))
        self.assertEqual(self.original, self.output.read_bytes())

    def test_restored_cache_wins_over_old_tracked_seed(self):
        self.assertEqual('updated', feed.refresh(self.root, NOW+timedelta(days=1), payload))
        newer = self.cache.read_bytes()
        self.output.write_bytes(self.original)
        fetch = Mock(side_effect=AssertionError('Unexpected request'))
        self.assertEqual('unchanged', feed.refresh(self.root, NOW+timedelta(days=1), fetch))
        fetch.assert_not_called()
        self.assertEqual(newer, self.output.read_bytes())

    def test_corrupt_cache_uses_seed_and_no_seed_fails_closed(self):
        self.cache.write_text('{corrupt', encoding='utf-8')
        self.assertEqual('unchanged', feed.refresh(self.root, NOW, payload))
        self.cache.unlink()
        self.output.unlink()
        with self.assertRaises(RuntimeError):
            feed.refresh(self.root, NOW, Mock(side_effect=TimeoutError()))
        self.assertFalse(self.output.exists())

    def test_cache_validation_rejects_unsafe_links_duplicates_and_future_dates(self):
        data = json.loads(self.original)
        broken = copy.deepcopy(data)
        broken['projects'][0]['url'] = 'javascript:alert(1)'
        self.assertFalse(feed.validate_snapshot(broken))
        broken = copy.deepcopy(data)
        broken['projects'][1] = broken['projects'][0]
        self.assertFalse(feed.validate_snapshot(broken))
        broken = copy.deepcopy(data)
        broken['history'][0]['ids'] = 'not an array'
        self.assertFalse(feed.validate_snapshot(broken))
        data['date'] = '2099-01-01'
        feed.write_snapshot(self.cache, data)
        self.assertIsNone(feed.read_snapshot(self.cache, NOW.date()))


if __name__ == '__main__':
    unittest.main()
