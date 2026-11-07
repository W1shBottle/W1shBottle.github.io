import unittest
from build_learning_dashboard import parse_tasks, summarize, make_snapshot


class DashboardEvidenceTests(unittest.TestCase):
    def test_guided_and_optional_do_not_inflate_acceptance(self):
        source = '\n'.join([
            '- [x] **J01 引用**：已经口述并验证。',
            '- [ ] **J02【已练习】接口**：跟写，需要独立变体。',
            '- [ ] **J03【待学】泛型**：尚未学习。',
            '- [x] **O01 检索**：选修实验有结果。'])
        tasks = parse_tasks(source, ['O01'])
        stats = summarize([t for t in tasks if not t['optional']])
        self.assertEqual((stats['total'], stats['accepted'], stats['practicing'], stats['percent']), (3, 1, 1, 33))

    def test_no_tasks_is_zero_and_all_accepted_is_100(self):
        self.assertEqual(summarize([])['percent'], 0)
        self.assertEqual(summarize([{'status':'accepted'}]*3)['percent'], 100)

    def test_duplicate_and_unknown_states_fail_instead_of_silent_counting(self):
        row = '- [x] **J01 引用**：已有证据。'
        for source in [row+'\n'+row, '- [ ] **J01【猜测完成】引用**：未确认。']:
            with self.assertRaises(ValueError):
                parse_tasks(source, [])

    def test_new_optional_item_cannot_silently_increase_denominator(self):
        with self.assertRaises(ValueError):
            parse_tasks('- [ ] **O01【按需】检索**：按需。', [])

    def test_deferred_extension_stays_optional_and_planned(self):
        row = '- [ ] **O06【后置】MCP**：主线完成后再做。'
        tasks = parse_tasks(row, ['O06'])
        self.assertEqual(tasks[0]['status'], 'planned')
        self.assertTrue(tasks[0]['optional'])
        with self.assertRaises(ValueError):
            parse_tasks(row, [])

    def test_total_uses_task_counts_not_average_stage_percentages(self):
        source = '- [x] **J01 引用**：已有证据。\n' + '\n'.join(
            f'- [ ] **W0{i}【待学】任务{i}**：待验收。' for i in range(1,4))
        plan = dict(version=1, optional_ids=[], current_group='web', focus_tasks=['W01'], groups=[
            dict(id='java', prefixes=['J']), dict(id='web', prefixes=['W'])])
        timeline = dict(updated='2026-10-31', current_project='ops-ticket', projects={'ops-ticket':'工单'},
                        stage='A1', entries=[dict(date='2026-10-31',project='ops-ticket',next='继续')])
        snapshot = make_snapshot(source, plan, timeline)
        self.assertEqual(snapshot['stats']['percent'],25)  # (1/4), not (100% + 0%)/2


if __name__ == '__main__':
    unittest.main()
