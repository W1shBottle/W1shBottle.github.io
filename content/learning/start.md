{
  "title": "Java 后端项目自学路线",
  "description": "基于 Java / Spring Boot / MyBatis / MySQL / Redis / RabbitMQ 的设备运维工单后端路线、当前进度与二期 Python Agent 规划。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 10,
  "group": "start",
  "draft": false,
  "lastmod": "2026-11-28T00:00:00+08:00"
}

更新于 2026-11-28（纯 Java 后端 4 周冲刺路线定稿）。围绕同一个**设备运维工单平台**，基于 **Java 21 / Spring Boot / MyBatis / MySQL / Redis / RabbitMQ** 推进 **A1 → A2 → M1 Redis（R01–R04）→ M2 RabbitMQ（M01–M04）**，不采用 Spring AI；AI / Agent 能力留待二期直接以独立 **Python（FastAPI + LangGraph）** 服务对接本项目。完整阶段任务见[阶段日程](/learning/schedule/)与[技能清单](/learning/checklists/)。

每周以可验证的小成果为目标，每天约 3 小时；旧教材中的“第几周”仅保留为章节索引，实际顺序以新版[阶段日程](/learning/schedule/)为准。课后答案是局部参考，不把看过或生成的代码计为已掌握。

## 路线总览

**起步（J01–J10）→ A1（数据库与 HTTP 业务闭环 S/W）→ A2（工程规范与交付 E01–E10）→ M1（Redis 缓存与幂等 R01–R04）→ M2（RabbitMQ 异步解耦与死信 M01–M04）→ 贯穿基础与面试（P01–P07，P05 按需）。**

二期后置扩展（`O01–O04`，不计入当前主线分母）：微服务拆分设计（Spring Cloud 概念）与独立 Python（FastAPI + LangGraph）Agent 服务。此前 11-25 草案中的 Java 侧 AI 条目（`B01–B09`、`C01–C04`、`D01–D02`）已归档暂不执行。

## 阅读入口

| 文件 | 用途 |
| --- | --- |
| [阶段日程](/learning/schedule/) | 纯 Java 4 周冲刺计划、当前实测进度、阶段门槛与下一步 |
| [Java与数据库](/learning/java-sql/) | Java/SQL 基础与 JDBC 查询、事务参考 |
| [Web与权限](/learning/web-security/) | HTTP 接口、MyBatis、四态流转、认证授权与错误处理 |
| [工程交付与测试参考](/learning/testing-delivery/) | 并发、测试、日志与部署交付参考 |
| [投递与面试](/learning/spring-applications/) | 岗位核对、能力证据表达与求职节奏 |
| [资料与排错](/learning/resources/) | 按阶段查官方文档与常见故障定位 |
| [技能 To-do List 与验收模板](/learning/checklists/) | 分阶段技术栈、主线 46 项与后置/按需 5 项验收状态 |
| [数据接口约定](/learning/contracts/) | 四表结构、最小接口、角色归属与演进边界 |

项目目录：`JavaProject`，包名 `cn.wishbottle.opsticket`，已清理早期控制台/文件演示代码并按标准 8 子包（`config`/`controller`/`domain`/`dto`/`exception`/`mapper`/`repository`/`service`）组织。

## 当前接续点（2026-11-28）

- **已完成跟练与实测**：真实 MySQL 跑通创建、派单（`assign`）、指定工程师解决（`resolve`）、原报障人验收关闭（`close`）四态闭环；落地 Spring Security + MySQL `app_user` 登录、`@PreAuthorize` 角色授权、`GET` 单条与日志的三角色归属隔离、`POST` 创建自动取登录人；在三条状态操作上实测 `expectedVersion` 乐观锁（`409`）；新建 `ticket_action_log` 表并用 `@Transactional` 绑定状态变更与审计日志，在隔离 H2 中编写外键失败回滚测试（4 项全绿）。
- **主线验收口径**：主线 46 项中已正式验收保持 **6 项（`J01–J06`）**，跟练待巩固保持 **22 项**，待学 **18 项**。
- **下一步（第 1 周优先）**：收口 `/api/v1/tickets` 列表三角色归属隔离与动态分页、补 `/api/v1/devices` 与联合索引 `EXPLAIN`；引入 `@Valid`、自定义 `LoginUser`、统一返回体 `Result<T>`、OpenAPI 接口文档、SLF4J + MDC 日志及可执行 Fat JAR / Tomcat 参数配置，随后依次接入 Redis 与 RabbitMQ。

## 纯 Java 后端核心交付边界

报修人选择启用设备并填写报修 → 管理员派给启用工程师 → 该工程师提交处理说明 → 原报修人验收关闭；各角色按归属查看工单与操作流水，管理员看全部。在此之上补齐三大生产级能力：

1. **工程规范与可观测**：RESTful 契约、OpenAPI 在线文档、`@Valid` + `Result<T>`、SLF4J + MDC `requestId`、联合索引 `EXPLAIN` 与内嵌 Tomcat 线程参数。
2. **Redis 缓存与防重**：JWT + Redis 登录态管理、设备与工单 Cache-Aside 缓存（穿透/雪崩/删缓存）、`X-Request-Id` 创建幂等防重与简易限流。
3. **RabbitMQ 异步与死信**：事务提交后（`AFTER_COMMIT`）异步通知解耦、TTL + 死信队列（DLX）工单超时未派单自动告警、Confirm + 手动 ACK + `messageId` 消费幂等。

## 每次学习的四件事

1. 说清这条业务需求需要什么知识，先读对应一两个类、配置或 SQL。
2. 自己完成一个小修改；助手给提示、审阅或局部示例，不一次生成整套功能。
3. 运行一个正常场景和一个有价值的失败场景，记录预期与实际；已掌握的同质练习可跳过。
4. 关掉答案解释输入、调用链、数据库/中间件变化和失败路径，再做一个变体。

## 离线阅读与准备

可打开[连续阅读版](/learning/downloads/reader.html)，或[下载完整自学包](/learning/downloads/java-internship-self-study.zip)后解压，用浏览器打开 `reader.html`；包内 Markdown 可独立阅读与记录。实际逐日进度以[学习看板与时间线](/learning/#progress)为准。
