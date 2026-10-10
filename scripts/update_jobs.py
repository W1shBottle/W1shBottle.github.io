"""Fetch public recruitment metadata. No login, cookies, CVs or private APIs."""
import argparse
from datetime import datetime, timedelta, timezone
from html import unescape
import hashlib
from functools import partial
import json
from pathlib import Path
import re
import sys
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'static/data/hangzhou-jobs.json'
TTL = timedelta(hours=72)
HIK_URL = 'https://talent.hikvision.com/home/socity/position?postId=3DBC4346A3391150639BCB4895723F64'


def fetch(url, body=None):
    headers = {'User-Agent': 'WishBottle-Jobs/1.0 (public recruitment summaries)', 'Accept': 'application/json,text/html'}
    if body is not None:
        parsed = urlsplit(url)
        headers.update({'Content-Type': 'application/json', 'Referer': f'{parsed.scheme}://{parsed.netloc}/jobs'})
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        if response.status != 200:
            raise ValueError('HTTP response not successful')
        return response.read(4_000_000).decode('utf-8-sig')


def stamp(now):
    return now.astimezone(timezone.utc).isoformat(timespec='seconds')


def skills(text):
    names = ['Java', 'Python', 'Spring Boot', 'Spring Cloud', 'MySQL', 'Redis', 'RAG', 'Agent', 'LangChain', 'FastAPI', 'Linux', 'Git', 'SQL', '大模型']
    compact = re.sub(r'\s+', '', text).lower()
    return [name for name in names if name.lower().replace(' ', '') in compact][:8]


def relevant(title, locations, category, description=''):
    if not any('杭州' in loc for loc in locations):
        return False
    if not ('实习' in category or '校园' in category or '校招' in category or '实习' in title):
        return False
    if re.search(r'HR|人力|招聘专员|经理|销售|售前|运营|前端|客户端|移动开发|测试|测评|投研|交付|安全工程师|数据策略|调优|硬件|芯片|训练|研究员', title, re.I):
        return False
    java = re.search(r'Java|后端|服务端', title, re.I)
    ai = re.search(r'AI|人工智能|大模型|Agent', title, re.I)
    development = re.search(r'开发|研发|工程|编程|RAG|Agent', title + description, re.I)
    if '算法' in title:
        return False
    return bool(java or (ai and development))


def enrich(duty, requirement, degree=None, salary=None, series=''):
    """Only factual fields and short topic labels; never invent missing requirements."""
    duty, requirement = plain(duty), plain(requirement)
    text = series + ' ' + requirement
    education = degree if isinstance(degree, str) and degree.strip() else None
    if not education:
        found = re.search(r'(?:本科|硕士|博士|大专)(?:及以上)?(?:学历)?', requirement)
        education = found[0] if found else None
    cohort = re.search(r'(20\d{2}|\d{2})届', text)
    cohort = (cohort[1] if len(cohort[1]) == 4 else '20' + cohort[1]) + '届' if cohort else None
    topics = [('后端|服务端|接口', '后端接口'), ('金融', '金融软件'), ('Agent|智能体', 'Agent 开发'),
              ('RAG|检索增强|知识库', '知识库 / RAG'), ('部署', '部署与工程化'),
              ('数据处理', '数据处理'), ('数据库|SQL', '数据库'), ('微服务|分布式', '微服务 / 分布式')]
    focus = [label for pattern, label in topics if re.search(pattern, duty, re.I)][:4]
    duration = re.findall(r'(?:每周\s*[一二三四五六七\d]+\s*天|[至少不少于]*\s*\d+\s*个?月)', requirement)
    return {'education': education, 'salary': salary if isinstance(salary, str) and salary.strip() else None,
            'cohort': cohort, 'skills': skills(duty + ' ' + requirement), 'focus': focus,
            'internshipDuration': ' · '.join(duration[:2]) or None}


def zhiye(now, host='dptech.zhiye.com', source_id='dptech', company='迪普科技'):
    records = {}
    for keyword in ('Java', 'AI', '后端', '大模型'):
        for page in range(10):
            payload = {'PageIndex': page, 'PageSize': 20, 'KeyWords': keyword, 'SpecialType': 0, 'PortalId': '',
                       'DisplayFields': ['Category', 'Kind', 'LocId', 'PostDate', 'Degree', 'Salary']}
            result = json.loads(fetch(f'https://{host}/api/Jobad/GetJobAdPageList', payload))
            if result.get('Code') != 200 or not isinstance(result.get('Data'), list) or not isinstance(result.get('Count'), int):
                raise ValueError('Recruitment list schema changed')
            rows = result['Data']
            if len(rows) != min(20, max(0, result['Count'] - page * 20)):
                raise ValueError('Incomplete recruitment page')
            for row in rows:
                title, category = row['JobAdName'], row['Category']
                detail = (row.get('Duty') or '') + (row.get('Require') or '')
                if row.get('Status') != 1 or not relevant(title, row.get('LocNames') or [], category, detail):
                    continue
                published = row['PostDate'][:10]
                # Portals may retain years-old positions; only show the current recruitment year.
                if datetime.fromisoformat(published).date() < (now - timedelta(days=365)).date():
                    continue
                end = row.get('EndTime') or ''
                if end and not end.startswith('0001') and datetime.fromisoformat(end[:10]).date() < now.date():
                    continue
                identifier = row['Id']
                if not re.fullmatch(r'[a-fA-F0-9-]{36}', identifier):
                    raise ValueError('Invalid public job identifier')
                records[identifier] = {'id': source_id + '-' + identifier, 'title': title, 'company': company,
                    'location': '杭州', 'locations': row['LocNames'], 'type': '实习' if '实习' in category else '校招',
                    'direction': 'Java 后端' if re.search(r'Java|后端', title, re.I) else 'AI 应用',
                    'publishedAt': published, 'url': f'https://{host}/campus/detail?jobAdId=' + identifier,
                    'source': company + '招聘官网', 'sourceId': source_id, 'checkedAt': stamp(now),
                    **enrich(row.get('Duty') or '', row.get('Require') or '', row.get('Degree'), row.get('Salary'), title)}
            if (page + 1) * 20 >= result['Count']:
                break
            if not rows or page == 9:
                raise ValueError('Incomplete recruitment pagination')
    return list(records.values())


dptech = zhiye


def ths(now):
    jobs = []
    for page in range(1, 11):
        result = json.loads(fetch(f'https://campus.10jqka.com.cn/api/v3/school_recruitment/apply/apply_list?type=school&page={page}&pageCount=100'))
        data = result.get('ex_data')
        if str(result.get('erro_code')) != '0' or not isinstance(data, dict) or not isinstance(data.get('apply_show_do_list'), list):
            raise ValueError('THS list schema changed')
        rows = data['apply_show_do_list']
        if len(rows) != min(100, max(0, data['total'] - (page-1)*100)):
            raise ValueError('Incomplete THS page')
        for row in rows:
            title, series, city = row['name'], row['apply_recruitment_series_name'], row['base']
            duty, requirements = row.get('intro') or '', row.get('requirement') or ''
            if not relevant(title, [city], series, duty):
                continue
            cohort = re.search(r'(20\d{2})届', series)
            if cohort and int(cohort[1]) < now.year:
                continue
            identifier = str(row['id'])
            if not identifier.isdigit():
                raise ValueError('Invalid THS public identifier')
            jobs.append({'id': 'ths-' + identifier, 'title': title, 'company': '同花顺', 'location': '杭州', 'locations': [city],
                         'type': '实习' if '实习' in series + title else '校招',
                         'direction': 'Java 后端' if re.search(r'Java|后端|服务端', title, re.I) else 'AI 应用',
                         'publishedAt': None, 'url': 'https://campus.10jqka.com.cn/job/detail?id=' + identifier,
                         'source': '同花顺招聘官网', 'sourceId': 'ths', 'checkedAt': stamp(now),
                         **enrich(duty, requirements, series=series)})
        if page >= data['pages']:
            break
        if not rows or page == 10:
            raise ValueError('Incomplete THS pagination')
    return jobs


def plain(html):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', html))).strip()


def hikvision(now):
    html = fetch(HIK_URL)
    # Restrict parsing to this job, excluding recommended jobs below it.
    html = html.split('相关职位')[0]
    match = re.search(r'<h2[^>]*>(.*?)</h2>', html, re.S)
    if any(word in plain(html) for word in ('职位已下线', '职位已关闭', '职位已过期', '招聘已结束')):
        return []
    if not match or '职位要求' not in html:
        raise ValueError('Recruitment detail unavailable or schema changed')
    title = plain(match.group(1))
    if not relevant(title, [title], '实习'):
        return []
    text = plain(html)
    date = re.search(r'发布时间\s*(\d{4}-\d{2}-\d{2})', text)
    if not date:
        raise ValueError('Missing job publish date')
    if datetime.fromisoformat(date[1]).date() < (now - timedelta(days=365)).date():
        return []
    return [{'id': 'hikvision-3DBC4346A3391150639BCB4895723F64', 'title': title, 'company': '海康威视',
             'location': '杭州', 'locations': ['浙江省杭州市'], 'type': '实习', 'direction': 'Java 后端',
             'publishedAt': date[1], 'url': HIK_URL, 'source': '海康威视招聘官网', 'sourceId': 'hikvision',
             'checkedAt': stamp(now), **enrich(text.split('职位描述')[-1].split('职位要求')[0], text.split('职位要求')[-1])}]


def fresh(item, now):
    try:
        age = now - datetime.fromisoformat(item['checkedAt'])
        return timedelta(0) <= age <= TTL
    except (KeyError, ValueError, TypeError):
        return False


def refresh(previous, providers, now):
    jobs, states = [], []
    prior_jobs = {job['id']: job for job in previous.get('jobs', [])}
    seen = dict(previous.get('seen', {}))
    for identifier, job in prior_jobs.items():
        seen.setdefault(identifier, {'firstSeenAt': job.get('firstSeenAt', job.get('checkedAt', stamp(now))),
                                     'lastSeenAt': job.get('checkedAt', stamp(now)), 'newAt': job.get('newAt')})
    known_sources = {source['id'] for source in previous.get('sources', []) if source.get('checkedAt')}
    for identifier, name, url, loader in providers:
        try:
            incoming = loader(now)
            for job in incoming:
                history = seen.get(job['id'])
                if history is None:
                    history = {'firstSeenAt': stamp(now), 'newAt': stamp(now) if identifier in known_sources else None}
                history['lastSeenAt'] = stamp(now)
                comparable = {key: value for key, value in job.items() if key not in ('checkedAt',)}
                fingerprint = hashlib.sha256(json.dumps(comparable, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                old = prior_jobs.get(job['id'], {})
                job.update({'firstSeenAt': history['firstSeenAt'], 'newAt': history.get('newAt'), 'fingerprint': fingerprint,
                            'changedAt': stamp(now) if old.get('fingerprint') and old['fingerprint'] != fingerprint else old.get('changedAt')})
                seen[job['id']] = history
            # A successful empty list removes all prior jobs from that source.
            jobs.extend(incoming)
            states.append({'id': identifier, 'name': name, 'url': url, 'status': 'ok', 'checkedAt': stamp(now), 'count': len(incoming)})
        except Exception as error:
            cached = [j for j in previous.get('jobs', []) if j.get('sourceId') == identifier and fresh(j, now)]
            jobs.extend(cached)
            last = next((s.get('checkedAt') for s in previous.get('sources', []) if s.get('id') == identifier), None)
            states.append({'id': identifier, 'name': name, 'url': url, 'status': 'error', 'checkedAt': last, 'count': len(cached)})
            print(f'WARNING {identifier}: {type(error).__name__}; retained {len(cached)} recent records', file=sys.stderr)
    jobs = list({job['id']: job for job in jobs}.values())
    jobs.sort(key=lambda job: job.get('publishedAt') or '', reverse=True)
    seen = {key: value for key, value in seen.items() if datetime.fromisoformat(value['lastSeenAt']) >= now-timedelta(days=90)}
    return {'schemaVersion': 1, 'attemptedAt': stamp(now), 'refreshMinutes': 60, 'maxAgeHours': 72,
            'sources': states, 'jobs': jobs, 'seen': seen}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    try:
        previous = json.loads(args.output.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        previous = {}
    providers = [('dptech', '迪普科技招聘官网', 'https://dptech.zhiye.com/jobs', dptech),
                 ('hikvision', '海康威视招聘官网', HIK_URL, hikvision),
                 ('hundsun', '恒生电子招聘官网', 'https://hscampus.zhiye.com/', partial(zhiye, host='hscampus.zhiye.com', source_id='hundsun', company='恒生电子')),
                 ('h3c', '新华三招聘官网', 'https://h3c.zhiye.com/', partial(zhiye, host='h3c.zhiye.com', source_id='h3c', company='新华三')),
                 ('dahua', '大华股份招聘官网', 'https://dahua.zhiye.com/', partial(zhiye, host='dahua.zhiye.com', source_id='dahua', company='大华股份')),
                 ('ths', '同花顺招聘官网', 'https://campus.10jqka.com.cn/', ths)]
    result = refresh(previous, providers, datetime.now(timezone.utc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(args.output)
    print(f'Jobs: {len(result["jobs"])}; sources OK: {sum(s["status"] == "ok" for s in result["sources"])}/{len(providers)}')


if __name__ == '__main__':
    main()
