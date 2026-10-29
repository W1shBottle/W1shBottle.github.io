{
  "title": "学习",
  "description": "沿着同一个设备运维工单项目，学习 Java 后端、AI 应用与效果验证。按阶段验收推进，用技能清单记录实际掌握。",
  "date": "2026-10-12T12:00:00+08:00",
  "lastmod": "2026-10-29T12:00:00+08:00",
  "draft": false
}

沿用设备运维工单项目：**A 后端业务与基础工程 → B 一个真实 AI 功能 → C 验证与改进**。完成一个可运行、能解释的小版本后就接入 AI；RAG、受控 Agent 按实际需要升级，Redis、消息队列和微服务不作为前置条件。

**2026-10-29 当前进度：** JDBC 查询已有跟练基础；JdbcTicketUpdateDemo 已完成参数化更新、自动读取版本、影响行数判断、提交与回滚、模拟后续失败，以及 printTicket/findTicketVersion/updateTitle 方法拆分。学习者反馈旧版本更新为1/0、成功提交可由MySQL终端查到、模拟失败回滚恢复；助手只读核对最新源码。正式业务仍用文件仓库。HTTP/JSON已初步讲解，Network面板观察待反馈；Spring Boot/MyBatis、权限和AI尚未接入。

新版[阶段计划](/learning/schedule/)对应项目任务和进阶标准，[技能 To-do List](/learning/checklists/)列出 55 项具体技能。已勾选的项目只代表那一个解释或操作已有证据，不能据此判定整门技术已掌握。原课程“周号”保留为材料索引，不再代表固定工期。

下一步：打开博客的浏览器 Network 面板，刷新并找到主文档请求，报告 Request URL、Request Method、Status Code；先理解请求与响应，再逐步接入 Spring Boot 和首条 GET /api/tickets/{id} 真实查询。不要重复执行已完成的提交练习来凑结果。 最新日结：[JDBC更新、版本检查与事务边界](/posts/ops-ticket-20261029/)。实现与学习验收边界见[项目文档](/learning/project-docs/)。
