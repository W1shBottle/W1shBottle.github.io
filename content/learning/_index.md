{
  "title": "学习",
  "description": "围绕设备运维工单项目，学习Java后端、模型调用、只读Agent、知识检索与评测，按真实证据验收。",
  "date": "2026-10-12T12:00:00+08:00",
  "lastmod": "2026-11-07T00:00:00+08:00",
  "draft": false
}

沿用设备运维工单项目：**A 后端业务与基础工程 → B 模型调用入门 → G 只读运维 Agent → C 知识检索与评测改进**。G成为明确主线；评测从B/G开始积累。保留原C技能编号，字母用于稳定索引，学习按这里的顺序推进。

**2026-11-07最新进展：** 文件版Web已接入Service与构造器注入；当天又通过临时只读接口接通 MyBatis→MySQL，学习者验证编号1返回200与标题JSON、999返回404、abc在参数转换阶段返回400。正式工单业务仍用文件仓库；完整对象映射、数据库写入、权限、状态流、模型与Agent均待实现。

新版[阶段计划](/learning/schedule/)对应交付与门槛，[技能清单](/learning/checklists/)共63项，其中58项计入主线、5项按需扩展。**原6项验收保持不变；新增Agent和知识检索任务使分母由49变为58，验收比例由12%变为10%，不代表已有进展减少。** 跟练仍单独显示，任务难度不同，百分比不用于估算剩余时间。旧周号只作教材索引。

下一步：新建 `TicketSummary`（id、title、status），在 `TicketMapper` 增加多列 `findSummaryById`，验证 MyBatis 对象映射与 JSON；之后再处理列名差异、领域 `Ticket` 转换、数据库写入和自增主键。

最新学习复盘是[MyBatis 接口映射与数据库查询接线](/posts/ops-ticket-20261107/)。当前实现与验收见[项目文档](/learning/project-docs/)，可打开[连续阅读版](/learning/downloads/reader.html)或[下载自学包](/learning/downloads/java-internship-self-study.zip)。
