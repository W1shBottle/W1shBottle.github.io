{
  "title": "Java＋AI 项目自学路线",
  "description": "基于 Java / Spring Boot / MyBatis / MySQL 的工单后端与轻量 AI 应用路线、当前进度和推进方法。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 10,
  "group": "start",
  "draft": false,
  "lastmod": "2026-11-27T00:00:00+08:00"
}

更新于 2026-11-27（唯一主线已于 2026-11-25 定稿为纯 Java 路线）。围绕同一个**设备运维工单平台**，基于现有 **Java 21 / Spring Boot / MyBatis / MySQL** 推进 **A1 → A2 → B01–B09 → C01–C04（可选进阶 D01–D02）**，不引入 Kafka、Milvus、Neo4j、微调或本地推理部署。完整阶段任务见[阶段日程](/learning/schedule/)与[技能清单](/learning/checklists/)。

每周以可验证的小成果为目标，每天约 3 小时；旧教材中的“第几周”仅保留为章节索引，实际顺序以新版[阶段日程](/learning/schedule/)为准。课后答案是局部参考，不把看过或生成的代码计为已掌握。

## 路线总览

**A1（数据库与 HTTP 业务闭环）→ A2（认证授权、事务、乐观锁与工程交付）→ B（Java AI 业务功能 B01–B09）→ C（效果评估与单因子回归 C01–C04）→ 可选进阶 D（D01 MySQL 轻量 RAG / D02 外部 SOP 轻量 Skill）。**

此前记录的 Python（Y）、Redis（R）、LangGraph / Python 只读 Agent（G）规划已归档暂不执行，不再计入当前主线进度。

## 阅读入口

| 文件 | 用途 |
| --- | --- |
| [阶段日程](/learning/schedule/) | 纯 Java 主线定稿、当前实测进度、阶段门槛与下一步 |
| [Java与数据库](/learning/java-sql/) | Java/SQL 基础与 JDBC 查询、事务参考 |
| [Web与权限](/learning/web-security/) | HTTP 接口、MyBatis、四态流转、认证授权与错误处理 |
| [Java AI 功能与工程交付](/learning/testing-delivery/) | B01–B09、C01–C04、D01–D02 验收要求与并发/测试参考 |
| [投递与面试](/learning/spring-applications/) | 岗位核对、能力证据表达与求职节奏 |
| [资料与排错](/learning/resources/) | 按阶段查官方文档与常见故障定位 |
| [技能 To-do List 与验收模板](/learning/checklists/) | 分阶段技术栈、主线 51 项与按需 7 项验收状态 |
| [数据接口约定](/learning/contracts/) | 四表结构、最小接口、角色归属与 AI 建议边界 |

项目目录：`JavaProject`，包名 `cn.wishbottle.opsticket`，已清理早期控制台/文件演示代码并按标准 8 子包（`config`/`controller`/`domain`/`dto`/`exception`/`mapper`/`repository`/`service`）组织。

## 当前接续点（2026-11-27）

- **已完成跟练与实测**：真实 MySQL 跑通创建、派单（`assign`）、指定工程师解决（`resolve`）、原报障人验收关闭（`close`）四态闭环；落地 Spring Security + MySQL `app_user` 登录、`@PreAuthorize` 角色授权、`GET` 单条与日志的三角色归属隔离、`POST` 创建自动取登录人；在三条状态操作上实测 `expectedVersion` 乐观锁（`409`）；新建 `ticket_action_log` 表并用 `@Transactional` 绑定状态变更与审计日志，在隔离 H2 中编写外键失败回滚测试（4 项全绿）。
- **主线验收口径**：主线 51 项中已正式验收保持 6 项（`J01–J06`），跟练待巩固 22 项，待学 23 项。
- **下一步**：收尾 A2 剩余小边界（补齐 `GET /api/db/tickets` 列表接口权限、接入 SLF4J 日志与基础集成验证），随后正式进入 **B 阶段：Java AI 业务功能（B01–B09）**。

## 第一版只做这些

报修人选择启用设备并填写报修 → 管理员派给启用工程师 → 该工程师提交处理说明 → 原报修人验收关闭；各角色按归属查看工单与操作流水，管理员看全部。由 Java 判断角色、归属、状态、版本和字段；MySQL 持久化并提供约束。

B 阶段直接在现有 Spring Boot 项目中落地模型客户端、结构化输出校验、超时降级、`@Async` 有界线程池事务后异步触发回写，以及人工采纳 / 修改后采纳 / 驳回反馈闭环。AI 只给建议，人保留最终确认权；关闭 AI 后工单主业务不受影响。

## 每次学习的四件事

1. 说清这条业务需求需要什么知识，先读对应一两个类或 SQL。
2. 自己完成一个小修改；助手给提示、审阅或局部示例，不一次生成整套功能。
3. 运行一个正常场景和一个有价值的失败场景，记录预期与实际；已掌握的同质练习可跳过。
4. 关掉答案解释输入、调用链、数据库变化和失败路径，再做一个变体。

AI 辅助编程记录“工具帮了什么、我怎样确认”；项目 AI 功能记录“模型请求、结构化输出、失败降级、人工采纳率、质量和成本”。两者不混为同一能力。

## 离线阅读与准备

可打开[连续阅读版](/learning/downloads/reader.html)，或[下载完整自学包](/learning/downloads/java-internship-self-study.zip)后解压，用浏览器打开 `reader.html`；包内 Markdown 可独立阅读与记录。实际逐日进度以[学习看板与时间线](/learning/#progress)为准。
