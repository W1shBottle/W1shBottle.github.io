{
  "title": "学习",
  "description": "基于 Java / Spring Boot / MyBatis / MySQL 的设备运维工单与轻量 AI 功能：A1→A2→B01–B09→C01–C04，另设可选进阶 D01–D02。",
  "date": "2026-10-12T12:00:00+08:00",
  "lastmod": "2026-11-25T00:00:00+08:00",
  "draft": false
}

以现有 **Java / Spring Boot / MyBatis / MySQL** 设备运维工单系统作为唯一主线（**A1 → A2 → B01–B09 → C01–C04 + 可选进阶 D01–D02**）：先完成数据库业务、权限、事务与版本冲突闭环，再轻量落地模型调用、`@Async` 事务后异步分析回写、人工采纳与反馈日志闭环及效果评估，不引入 Kafka、Milvus、Neo4j、微调或本地推理部署。

此前并行记录的 Python / Redis / Python Agent 条目已归档暂不执行，现有全部验收勾选与跟练状态保持不变。

下一次先核对 `app_user` 表账号与占位密码哈希，准备切入数据库登录（`UserMapper.findByUsername()`），并补齐派单失败分支 404/409 的本人复验。

[技能清单](/learning/checklists/) · [11 月 15 日派单复盘](/posts/ops-ticket-20261115/) · [项目文档](/learning/project-docs/) · [连续阅读版](/learning/downloads/reader.html) · [下载自学包](/learning/downloads/java-internship-self-study.zip)
