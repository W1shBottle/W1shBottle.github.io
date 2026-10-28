"""Build a daily, public GitHub discovery edition; no browser API calls or secrets.

Only the GitHub REST API is used. Stars are totals, not daily growth. An edition
is committed atomically after all six searches succeed; failures keep its date.
"""
import argparse
from datetime import datetime, timedelta, timezone, date
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CHINA = timezone(timedelta(hours=8))
CATEGORIES = {'ai': 'AI 与智能应用', 'dev': '开发工具', 'useful': '实用软件'}
QUOTAS = {'ai': 3, 'dev': 4, 'useful': 3}
SEARCHES = [('ai', 'llm'), ('ai', 'rag'), ('dev', 'developer-tools'),
            ('dev', 'cli'), ('useful', 'self-hosted'), ('useful', 'productivity')]
REPO_NAME = re.compile(r'[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}\Z')
EXCLUDE = {'awesome-list', 'awesome', 'tutorial', 'tutorials', 'interview', 'course', 'courses'}


def edition_date(now):
    # 08:17 CST is the first existing hourly workflow after this cutoff.
    local = now.astimezone(CHINA)
    return (local - timedelta(hours=8)).date()


def clean_text(value, limit):
    if not isinstance(value, str):
        return ''
    return ' '.join(value.split())[:limit]


def normalize(item, now):
    if not isinstance(item, dict):
        return None
    name = item.get('full_name', '')
    stars, repo_id = item.get('stargazers_count'), item.get('id')
    if not isinstance(name, str) or not REPO_NAME.fullmatch(name):
        return None
    if type(stars) is not int or stars < 1000 or type(repo_id) is not int or repo_id <= 0:
        return None
    if any(item.get(key) is not False for key in ('fork', 'archived', 'private', 'disabled')):
        return None
    try:
        pushed = datetime.fromisoformat(item['pushed_at'].replace('Z', '+00:00'))
        if pushed.tzinfo is None or not now - timedelta(days=90) <= pushed <= now + timedelta(minutes=5):
            return None
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    topics = item.get('topics') or []
    if not isinstance(topics, list):
        return None
    topics = {x.lower() for x in topics if isinstance(x, str)}
    short = name.split('/')[1].lower()
    if topics & EXCLUDE or short.startswith('awesome-') or short.endswith('-tutorial'):
        return None
    description = clean_text(item.get('description'), 320)
    if not description:
        return None
    return {'id': repo_id, 'name': name, 'url': 'https://github.com/' + name,
            'description': description, 'stars': stars,
            'language': clean_text(item.get('language'), 40),
            'pushed_at': pushed.isoformat(timespec='seconds')}


def request_json(url):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'WishBottle-Daily-Discovery/1.0',
               'X-GitHub-Api-Version': '2022-11-28'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as response:
        if response.status != 200:
            raise ValueError('GitHub returned a non-200 response')
        body = response.read(4_000_001)
        if len(body) > 4_000_000:
            raise ValueError('GitHub response too large')
        return json.loads(body)


def collect(now, fetcher):
    cutoff = (now - timedelta(days=90)).date().isoformat()
    candidates = {}
    for category, topic in SEARCHES:
        query = f'topic:{topic} stars:>=1000 archived:false fork:false pushed:>={cutoff}'
        url = 'https://api.github.com/search/repositories?' + urllib.parse.urlencode(
            {'q': query, 'sort': 'stars', 'order': 'desc', 'per_page': 50})
        payload = fetcher(url)
        if (not isinstance(payload, dict) or not isinstance(payload.get('items'), list)
                or payload.get('incomplete_results') is not False):
            raise ValueError('Incomplete GitHub search response')
        for raw in payload['items']:
            repo = normalize(raw, now)
            if repo:
                existing = candidates.setdefault(repo['id'], dict(repo, categories=[]))
                if category not in existing['categories']:
                    existing['categories'].append(category)
    return list(candidates.values())


def choose(candidates, day, history):
    recent = {repo_id for entry in history
              if 0 <= (day - date.fromisoformat(entry['date'])).days <= 7
              for repo_id in entry['ids']}

    def rank(repo):
        # Stable daily rotation with a mild star-count weight, not a fake trend score.
        digest = hashlib.sha256(f'{day}:{repo["id"]}'.encode()).digest()
        uniform = (int.from_bytes(digest[:8], 'big') + 1) / (2**64 + 1)
        return -math.log(uniform) / math.log10(repo['stars'])

    ordered = sorted(candidates, key=lambda repo: (rank(repo), repo['id']))
    selected, ids, owners = [], set(), set()
    counts = dict.fromkeys(QUOTAS, 0)
    # First fill category quotas from unseen repos, then relax owner/cooldown if needed.
    for allow_repeat, allow_owner in [(False, False), (False, True), (True, False), (True, True)]:
        for category, quota in QUOTAS.items():
            for repo in ordered:
                if counts[category] >= quota:
                    break
                owner = repo['name'].split('/')[0].lower()
                if (repo['id'] in ids or category not in repo['categories']
                        or (not allow_repeat and repo['id'] in recent)
                        or (not allow_owner and owner in owners)):
                    continue
                selected.append({k: v for k, v in repo.items() if k != 'categories'} | {'category': category})
                counts[category] += 1
                ids.add(repo['id'])
                owners.add(owner)
    if len(selected) != 10:
        raise ValueError('Not enough eligible repositories for a complete edition')
    # Interleave categories; collapsed view also represents all three interests.
    grouped = {category: [x for x in selected if x['category'] == category] for category in QUOTAS}
    return [grouped[c].pop(0) for c in ['ai', 'dev', 'useful', 'dev', 'ai', 'useful', 'dev', 'ai', 'useful', 'dev']]


def validate_snapshot(data):
    try:
        if data['schema'] != 1 or type(data['schema']) is not int:
            return False
        if date.fromisoformat(data['date']).isoformat() != data['date']:
            return False
        generated = datetime.fromisoformat(data['generated_at'])
        if generated.tzinfo is None:
            return False
        projects = data['projects']
        if len(projects) != 10 or len({p['id'] for p in projects}) != 10:
            return False
        if len({p['name'].lower() for p in projects}) != 10:
            return False
        for p in projects:
            if (type(p['id']) is not int or p['id'] <= 0
                    or not REPO_NAME.fullmatch(p['name'])
                    or p['url'] != 'https://github.com/' + p['name']
                    or p['category'] not in CATEGORIES
                    or type(p['stars']) is not int or p['stars'] < 1000
                    or not isinstance(p['description'], str) or not p['description'] or len(p['description']) > 320
                    or not isinstance(p['language'], str) or len(p['language']) > 40):
                return False
        if len(data['history']) > 14:
            return False
        for entry in data['history']:
            date.fromisoformat(entry['date'])
            if not isinstance(entry['ids'], list) or len(entry['ids']) != 10:
                return False
            if any(type(i) is not int or i <= 0 for i in entry['ids']):
                return False
        return True
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def read_snapshot(path, target):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if validate_snapshot(data) and date.fromisoformat(data['date']) <= target:
            return data
    except (OSError, ValueError):
        pass
    return None


def write_snapshot(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def refresh(root=ROOT, now=None, fetcher=request_json, force=False):
    now = now or datetime.now(timezone.utc)
    day = edition_date(now)
    output = root / 'data/github_daily.json'
    cache = root / '.cache/github-daily.json'
    snapshots = [x for x in (read_snapshot(output, day), read_snapshot(cache, day)) if x]
    previous = max(snapshots, key=lambda x: (x['date'], x['generated_at'])) if snapshots else None
    if previous and previous['date'] == day.isoformat() and not force:
        data, status = previous, 'unchanged'
    else:
        try:
            history = previous['history'] if previous else []
            # A seed/cache edition itself also participates in the cooldown.
            if previous:
                history = [h for h in history if h['date'] != previous['date']]
                history += [{'date': previous['date'], 'ids': [p['id'] for p in previous['projects']]}]
            projects = choose(collect(now, fetcher), day, history)
            history = [h for h in history if 0 < (day - date.fromisoformat(h['date'])).days <= 13]
            history += [{'date': day.isoformat(), 'ids': [p['id'] for p in projects]}]
            data = {'schema': 1, 'date': day.isoformat(), 'generated_at': now.isoformat(timespec='seconds'),
                    'projects': projects, 'history': history}
            if not validate_snapshot(data):
                raise ValueError('Invalid generated edition')
            status = 'updated'
        except Exception as error:
            # Do not log request headers or tokens. Keep the original successful date.
            print(f'GitHub refresh unavailable ({type(error).__name__}); keeping last successful edition.', file=sys.stderr)
            if not previous:
                raise RuntimeError('No valid GitHub edition available; stop deployment') from None
            data, status = previous, 'fallback'
    write_snapshot(output, data)
    write_snapshot(cache, data)
    print(f'GitHub daily: {status}; edition={data["date"]}; projects={len(data["projects"])}')
    return status


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Explicitly replace today\'s edition; normally unnecessary')
    args = parser.parse_args()
    refresh(force=args.force)
