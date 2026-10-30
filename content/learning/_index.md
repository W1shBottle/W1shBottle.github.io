{
  "title": "学习",
  "description": "沿着同一个设备运维工单项目，学习 Java 后端、AI 应用与效果验证。按阶段验收推进，用技能清单记录实际掌握。",
  "date": "2026-10-12T12:00:00+08:00",
  "lastmod": "2026-10-30T12:00:00+08:00",
  "draft": false
}

沿用设备运维工单项目：**A 后端业务与基础工程 → B 一个真实 AI 功能 → C 验证与改进**。完成一个可运行、能解释的小版本后就接入 AI；RAG、受控 Agent 按实际需要升级，Redis、消息队列和微服务不作为前置条件。

**2026-10-30 当前进度：** 已跟练HTTP/JSON与Maven/POM，接入Spring Boot 4.1.2和Web MVC，OpsTicketApplication可在8080启动；HelloController经历文本、Map转JSON和查询参数三个步骤。文本/固定JSON有助手实际GET证据，name默认值与传参由学习者反馈通过。TicketController已写路径编号回显，3/10/abc运行尚待反馈。正式控制台仍用文件仓库，Web未接Service或数据库，MyBatis、权限和AI待学。

新版[阶段计划](/learning/schedule/)对应项目任务和进阶标准，[技能 To-do List](/learning/checklists/)列出 55 项具体技能。已勾选的项目只代表那一个解释或操作已有证据，不能据此判定整门技术已掌握。原课程“周号”保留为材料索引，不再代表固定工期。

下一步：启动 OpsTicketApplication，分别访问 /api/tickets/3、/api/tickets/10、/api/tickets/abc，记录响应体和HTTP状态码；解释参数回显与真实工单查询的区别，再逐步接入业务与持久层。 最新日结：[HTTP、Maven与第一个Spring Boot接口](/posts/ops-ticket-20261030/)。实现与验收边界见[项目文档](/learning/project-docs/)。
