{
  "title": "学习",
  "description": "从 Java 设备工单到 Python 报修分诊助手，练习只读工具、资料检索、执行追踪与人工确认。",
  "date": "2026-10-12T12:00:00+08:00",
  "lastmod": "2026-11-24T00:00:00+08:00",
  "draft": false
}

在现有 Java 工单系统上做一个**设备报修分诊助手**。管理员收到一张报修单，Python Agent 帮他查设备资料，给出处理建议、依据和需要追问的内容。管理员查看建议后决定如何处置。

最近一次有记录的 Java 实操是 11 月 15 日。学习者按指导在隔离 H2 用 Apifox 查工单 101、派给工程师 2、再次查询，确认状态变为 IN_PROGRESS，也验证了工程师编号 0 返回 400。404 和 409 已由助手预检，留给本人复验。操作人授权、期望版本冲突、Python 工具与真实模型调用仍待实践。

下一次先做 Python 查询。用三张虚构设备工单写 `find_ticket(ticket_id)`，分别传入已有编号、缺失编号和非法输入，核对三种结果。 卡在字典或函数时，阶段计划有对应的课程分 P。[六个学习单元](/learning/schedule/#接下来的六个学习单元) · [按卡点看网课](/learning/schedule/#按阶段看网课与做练习)

[技能清单](/learning/checklists/) · [11 月 15 日派单复盘](/posts/ops-ticket-20261115/) · [项目文档](/learning/project-docs/) · [连续阅读版](/learning/downloads/reader.html) · [下载自学包](/learning/downloads/java-internship-self-study.zip)
