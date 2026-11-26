{
  "title": "学习",
  "description": "基于 Java / Spring Boot / MyBatis / MySQL 的设备运维工单与轻量 AI 功能：A1→A2→B01–B09→C01–C04，另设可选进阶 D01–D02。",
  "date": "2026-10-12T12:00:00+08:00",
  "lastmod": "2026-11-26T00:00:00+08:00",
  "draft": false
}

以现有 **Java / Spring Boot / MyBatis / MySQL** 设备运维工单系统作为唯一主线（**A1 → A2 → B01–B09 → C01–C04 + 可选进阶 D01–D02**）：先完成数据库业务、权限、事务与版本冲突闭环，再轻量落地模型调用、`@Async` 事务后异步分析回写、人工采纳与反馈日志闭环及效果评估，不引入 Kafka、Milvus、Neo4j、微调或本地推理部署。

此前并行记录的 Python / Redis / Python Agent 条目已归档暂不执行，现有全部验收勾选保持不变。

下一次先给 `GET /api/db/tickets/{id}` 补上查询归属隔离（报障人 A 不能查看报障人 B 的工单），并把创建工单的 `reporterId` 改为从登录身份自动读取。

[技能清单](/learning/checklists/) · [11 月 26 日乐观锁与四态闭环复盘](/posts/ops-ticket-20261126/) · [项目文档](/learning/project-docs/) · [连续阅读版](/learning/downloads/reader.html) · [下载自学包](/learning/downloads/java-internship-self-study.zip)
