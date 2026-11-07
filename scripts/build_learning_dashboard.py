"""Derive the dashboard from the existing checklist; never estimate mastery."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'content/learning/checklists.md'
PLAN = ROOT / 'data/learning_dashboard_plan.json'
TIMELINE = ROOT / 'data/learning_progress.json'
OUTPUT = ROOT / 'data/learning_dashboard.json'
ROW = re.compile(r'^- \[([ x])\] \*\*([A-Z]\d{2})(?:【([^】]+)】)?\s*([^*]+)\*\*：(.+)$', re.M)


def parse_tasks(markdown, optional_ids):
    tasks, seen = [], set()
    for checked, task_id, label, title, description in ROW.findall(markdown):
        if task_id in seen:
            raise ValueError('Duplicate task: ' + task_id)
        seen.add(task_id)
        optional = task_id in optional_ids
        if checked == 'x':
            status = 'accepted'
        elif label in ('按需', '更后置', '后置', '待学'):
            status = 'planned'
        elif any(word in label for word in ('已练习', '已跟练', '实操通过', '正在学', '持续')):
            status = 'practicing'
        else:
            raise ValueError('Unrecognized learning state: ' + task_id + ' / ' + label)
        if label in ('按需', '更后置', '后置') and not optional:
            raise ValueError('Optional task must be excluded from denominator: ' + task_id)
        tasks.append(dict(id=task_id, title=title.strip(), status=status,
                          optional=optional, description=description.strip()))
    candidates = re.findall(r'^- \[[ x]\] \*\*[A-Z]\d{2}', markdown, re.M)
    if not tasks or len(candidates) != len(tasks):
        raise ValueError('Checklist contains missing or unparseable task rows')
    if not set(optional_ids).issubset(seen):
        raise ValueError('Unknown optional task ID')
    return tasks


def summarize(tasks):
    counts = {key: sum(t['status'] == key for t in tasks)
              for key in ('accepted', 'practicing', 'planned')}
    total = len(tasks)
    # Integer half-up rounding, not an average of rounded stage percentages.
    counts.update(total=total, percent=(counts['accepted'] * 200 + total) // (total * 2) if total else 0,
                  accepted_width=round(counts['accepted'] * 100 / total, 4) if total else 0,
                  practicing_width=round(counts['practicing'] * 100 / total, 4) if total else 0)
    return counts


def make_snapshot(markdown, plan, timeline):
    if plan['version'] != 1:
        raise ValueError('Unsupported dashboard plan version')
    tasks = parse_tasks(markdown, plan['optional_ids'])
    required = [t for t in tasks if not t['optional']]
    groups, assigned = [], []
    for group in plan['groups']:
        items = [t for t in required if t['id'][0] in group['prefixes']]
        assigned.extend(t['id'] for t in items)
        groups.append({**group, 'tasks': items, 'stats': summarize(items)})
    if sorted(assigned) != sorted(t['id'] for t in required):
        raise ValueError('Each required task must belong to exactly one group')
    if len({g['id'] for g in groups}) != len(groups):
        raise ValueError('Duplicate group ID')
    current = next(g for g in groups if g['id'] == plan['current_group'])
    focus = [t for t in current['tasks'] if t['id'] in plan['focus_tasks']]
    if len(focus) != len(set(plan['focus_tasks'])) or any(t['status'] == 'accepted' for t in focus):
        raise ValueError('Focus tasks must be unfinished tasks in the current group')
    latest = max((e for e in timeline['entries'] if e['project'] == timeline['current_project']), key=lambda e:e['date'])
    source = markdown + json.dumps(plan, sort_keys=True) + json.dumps(timeline, sort_keys=True)
    return dict(version=1, source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                updated=timeline['updated'], project=timeline['projects'][timeline['current_project']],
                stage=timeline['stage'], current_group=plan['current_group'], focus_tasks=focus,
                next=latest['next'], note=latest.get('note'), stats=summarize(required),
                groups=groups, optional_tasks=[t for t in tasks if t['optional']],
                total_items=len(tasks))


def serialized_snapshot():
    data = make_snapshot(SOURCE.read_text('utf-8'), json.loads(PLAN.read_text('utf-8')),
                         json.loads(TIMELINE.read_text('utf-8')))
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def validate_snapshot():
    if not OUTPUT.exists() or OUTPUT.read_text('utf-8') != serialized_snapshot():
        raise ValueError('Dashboard is stale. Run: python scripts/build_learning_dashboard.py')
    print('Learning dashboard OK: checklist, timeline and percentages are synchronized')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        validate_snapshot()
    else:
        OUTPUT.write_text(serialized_snapshot(), encoding='utf-8')
        validate_snapshot()
