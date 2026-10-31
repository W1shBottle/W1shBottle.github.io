{
  "title": "学习",
  "description": "沿着同一个设备运维工单项目，学习 Java 后端、AI 应用与效果验证。按阶段验收推进，用技能清单记录实际掌握。",
  "date": "2026-10-12T12:00:00+08:00",
  "lastmod": "2026-10-31T12:00:00+08:00",
  "draft": false
}

沿用设备运维工单项目：**A 后端业务与基础工程 → B 一个真实 AI 功能 → C 验证与改进**。完成一个可运行、能解释的小版本后就接入 AI；RAG、受控 Agent 按实际需要升级，Redis、消息队列和微服务不作为前置条件。

**2026-10-31 当前进度：** 已跟练 Spring Bean 配置与构造器注入，Web 复用 TicketService 和文件仓库，完成详情、列表、关键词查询与 POST 创建。课堂助手 GET 验证 200/400/404；学习者提供创建 201 截图，并反馈空白标题失败且数量不变。DTO、RequestBody、JSON 转换和异常 cause 经讲解；独立追踪仍需巩固。MyBatis/MySQL 业务、权限及 AI 尚未接入。

新版[阶段计划](/learning/schedule/)对应项目任务和进阶标准，[技能 To-do List](/learning/checklists/)列出 55 项具体技能。已勾选的项目只代表那一个解释或操作已有证据，不能据此判定整门技术已掌握。原课程“周号”保留为材料索引，不再代表固定工期。

下一步：先确认重启后编号 2 仍可查询，再用断点追踪 setTitle → Controller → Service；比较缺标题的 {} 与语法错误 JSON 的失败位置，区分参数转换和业务校验。 最新日结：[Spring依赖注入与工单查询创建接口](/posts/ops-ticket-20261031/)。实现与验收边界见[项目文档](/learning/project-docs/)。
