{
  "title": "学习",
  "description": "沿着同一个设备运维工单项目，学习 Java 后端、AI 应用与效果验证。按阶段验收推进，用技能清单记录实际掌握。",
  "date": "2026-10-12T12:00:00+08:00",
  "lastmod": "2026-10-28T12:00:00+08:00",
  "draft": false
}

沿用设备运维工单项目：**A 后端业务与基础工程 → B 一个真实 AI 功能 → C 验证与改进**。完成一个可运行、能解释的小版本后就接入 AI；RAG、受控 Agent 按实际需要升级，Redis、消息队列和微服务不作为前置条件。

**2026-10-28 当前进度：** JOIN 的 OPEN 筛选、COUNT/GROUP BY/HAVING、稳定分页与同条件总数已按指导练习并反馈结果；SQL 提交/回滚、条件更新和双连接版本竞争已有运行反馈。JdbcTicketQueryDemo 已使用同一 Connection 依次查询 OPEN/IN_PROGRESS，处理 SQL NULL 并提取 printTicketsByStatus，学习者反馈运行成功、助手读取源码核对。Java 更新事务尚待亲手练习，正式业务仍用文件仓库，Web/权限/AI 未接入。

新版[阶段计划](/learning/schedule/)对应项目任务和进阶标准，[技能 To-do List](/learning/checklists/)列出 55 项具体技能。已勾选的项目只代表那一个解释或操作已有证据，不能据此判定整门技术已掌握。原课程“周号”保留为材料索引，不再代表固定工期。

下一步：在单独的 JdbcTicketUpdateDemo 中学习 executeUpdate、setAutoCommit(false)、影响行数和显式 rollback：读取当前版本，修改指定标题后回滚，重新查询确认标题与版本恢复；先讲清事务边界，再由学习者亲手实现。 最新日结：[SQL统计、事务与JDBC查询](/posts/ops-ticket-20261028/)。实现与学习验收边界见[项目文档](/learning/project-docs/)。
