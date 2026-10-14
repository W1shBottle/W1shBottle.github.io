from datetime import datetime, timedelta, timezone
import unittest
from update_jobs import refresh, relevant, stamp, bachelor_eligible


class JobsTests(unittest.TestCase):
    def test_only_relevant_student_development_jobs(self):
        self.assertTrue(relevant('Java开发工程师', ['浙江省·杭州市'], '校园招聘'))
        self.assertTrue(relevant('AI实习生', ['杭州市'], '实习生招聘', '参与Agent应用开发'))
        self.assertFalse(relevant('Java开发工程师', ['北京市'], '校园招聘'))
        self.assertFalse(relevant('Java高级开发', ['杭州市'], '社会招聘'))
        self.assertFalse(relevant('HR（AI方向）实习生', ['杭州市'], '实习生招聘', 'AI应用开发'))
        self.assertFalse(relevant('AI产品经理实习生', ['杭州市'], '实习生招聘'))
        self.assertFalse(relevant('AI业务经理', ['杭州市'], '校园招聘', '研发AI应用'))

    def test_baseline_new_jobs_and_updates_are_not_confused(self):
        now = datetime(2026, 10, 10, tzinfo=timezone.utc)
        def job(identifier, title='Java开发'):
            return {'id':identifier,'sourceId':'test','title':title,'education':'本科','checkedAt':stamp(now)}
        def provider(items):
            return [('test','Test','https://example.org',lambda _: items)]
        initial = refresh({}, provider([job('a')]), now)
        self.assertIsNone(initial['jobs'][0]['newAt'])
        same = refresh(initial, provider([job('a')]), now+timedelta(hours=1))
        self.assertIsNone(same['jobs'][0]['changedAt'])
        changed = refresh(same, provider([job('a','Java实习'),job('b')]), now+timedelta(hours=2))
        indexed = {j['id']:j for j in changed['jobs']}
        self.assertEqual(indexed['a']['firstSeenAt'],stamp(now))
        self.assertIsNotNone(indexed['a']['changedAt'])
        self.assertIsNotNone(indexed['b']['newAt'])
        again = refresh(changed, provider([job('a','Java实习'),job('b')]), now+timedelta(hours=3))
        self.assertEqual({j['id']:j for j in again['jobs']}['b']['newAt'],indexed['b']['newAt'])

    def test_failure_retains_original_timestamp_and_expires_old_jobs(self):
        now = datetime(2026, 10, 10, tzinfo=timezone.utc)
        old = stamp(now - timedelta(hours=2))
        previous = {'jobs': [{'id': 'recent', 'sourceId': 'test', 'education': '本科', 'checkedAt': old},
                             {'id': 'expired', 'sourceId': 'test', 'education': '本科', 'checkedAt': stamp(now-timedelta(hours=73))}],
                    'sources': [{'id': 'test', 'checkedAt': old}]}
        def failure(_):
            raise TimeoutError()
        result = refresh(previous, [('test', 'Test', 'https://example.org', failure)], now)
        self.assertEqual([job['id'] for job in result['jobs']], ['recent'])
        self.assertEqual(result['jobs'][0]['checkedAt'], old)
        self.assertEqual(result['sources'][0]['checkedAt'], old)
        self.assertEqual(result['sources'][0]['status'], 'error')

    def test_successful_empty_result_removes_closed_jobs(self):
        now = datetime(2026, 10, 10, tzinfo=timezone.utc)
        previous = {'jobs': [{'id':'removed', 'sourceId':'test', 'education':'本科', 'checkedAt':stamp(now)}]}
        result = refresh(previous, [('test','Test','https://example.org',lambda _: [])], now)
        self.assertEqual(result['jobs'], [])
        self.assertEqual(result['sources'][0]['status'], 'ok')


class EducationTests(unittest.TestCase):
    def test_explicit_degree_requirements(self):
        import json
        from pathlib import Path
        cases = json.loads(Path(__file__).with_name('education_cases.json').read_text(encoding='utf-8'))
        for education, expected in cases:
            with self.subTest(education=education):
                self.assertEqual(bachelor_eligible(education), expected)

    def test_refresh_filters_new_and_cached_jobs(self):
        now = datetime(2026, 10, 14, tzinfo=timezone.utc)
        jobs = [{'id': str(i), 'sourceId': 'test', 'title': 'Java开发', 'education': education,
                 'checkedAt': stamp(now-timedelta(hours=1))}
                for i, education in enumerate(['本科及以上', '硕士研究生', None, '大专及以上'])]
        source = ('test', 'Test', 'https://example.org')
        result = refresh({}, [(*source, lambda _: jobs)], now)
        self.assertEqual([j['id'] for j in result['jobs']], ['0'])
        self.assertEqual(result['sources'][0]['count'], 1)
        def failed(_):
            raise TimeoutError()
        previous = {'jobs': jobs, 'sources': [{'id':'test','checkedAt':stamp(now-timedelta(hours=1))}]}
        cached = refresh(previous, [(*source, failed)], now)
        self.assertEqual([j['id'] for j in cached['jobs']], ['0'])
        self.assertEqual(cached['sources'][0]['count'], 1)
        self.assertEqual(cached['jobs'][0]['checkedAt'], stamp(now-timedelta(hours=1)))


if __name__ == '__main__':
    unittest.main()
