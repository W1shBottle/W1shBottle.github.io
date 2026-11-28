{
  "title": "设备运维工单平台项目说明",
  "description": "纯 Java / Spring Boot / MyBatis / MySQL / Redis / RabbitMQ 设备运维工单后端：A1 业务闭环、A2 工程化、M1 Redis、M2 RabbitMQ 与二期 Python Agent 预留。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 15,
  "group": "start",
  "draft": false,
  "lastmod": "2026-11-28T00:00:00+08:00"
}

> 本页说明项目整体路线；具体代码现状与验收记录请配合[项目文档](/learning/project-docs/)和[学习时间线](/learning/#progress)阅读。计划中的能力不代表已经实现或掌握。

更新于 2026-11-28。项目统一采用 **Java 21 / Spring Boot 4.1.2 / MyBatis 4.1.0 / MySQL 8.4 / Redis / RabbitMQ**，专注打造贴近设备/工业软件与互联网后台真实场景的纯 Java 后端系统；不采用 Spring AI，AI / Agent 能力留待二期以独立 **Python（FastAPI + LangGraph）** 服务对接本项目。

## 当前实测进展（2026-11-28）

- **A1 核心业务**：已在真实 MySQL 跑通创建、派单（`assign`）、解决（`resolve`）、验收关闭（`close`）四态闭环，完成早期控制台/文件版旧代码清理并整理为标准 Spring Boot 8 子包分层。
- **A2 工程化（当前阶段）**：已实测 Spring Security + MySQL `app_user` 登录、`@PreAuthorize` 角色授权、`GET` 单条与日志的三角色归属隔离、`POST` 创建自动取登录人、`expectedVersion` 乐观锁（`409`）、`ticket_action_log` 审计表 + `@Transactional` 事务绑定与 H2 外键失败回滚测试（4 项全绿）。当前收尾列表分页权限、Controller 瘦身、OpenAPI 文档、SLF4J 日志与 Fat JAR 后进入 M1/M2。
- **M1 Redis / M2 RabbitMQ / 二期 Python Agent**：尚未开始编码，按第 14–17 周统一计划逐步推进。

## 目标与阶段

**A1（数据库与 HTTP 闭环）→ A2（工程规范与交付）→ M1（Redis 缓存与幂等 R01–R04）→ M2（RabbitMQ 异步解耦与死信 M01–M04）→ 二期后置（微服务拆分设计 O01 / 独立 Python Agent O02–O04）。**

| 阶段 | 亲手交付 | 达标证据 |
| --- | --- | --- |
| A1 后端业务闭环 | MySQL 建表、MyBatis 映射、创建/查询/派单/解决/关闭四态接口与规范分层、联合索引 `EXPLAIN` | 真实 MySQL 跑通四态流转与 400/404/409 分支，能独立画出调用链与解释执行计划 |
| A2 工程规范与交付（当前） | 三角色列表隔离分页、`@Valid` + `LoginUser` + `Result<T>`、OpenAPI 文档、SLF4J + MDC、Fat JAR / Tomcat 参数与并发回滚测试 | 多角色 `200/401/403/409` 实测、并发派单仅 1 次成功、在线接口文档可调与可复现部署 |
| M1 Redis 缓存与幂等（R01–R04） | JWT + Redis 登录态、设备/工单 Cache-Aside（防穿透/雪崩/删缓存）、`X-Request-Id` 防重幂等、缓存前后压测对比 | 命中/失效/防穿透与幂等拦截实测，保留真实压测条件与数据 |
| M2 RabbitMQ 异步与死信（M01–M04） | `AFTER_COMMIT` 异步通知、TTL + 死信队列（DLX）超时未派单告警、Confirm + 手动 ACK + `messageId` 消费幂等 | 事务回滚不误发、超时工单自动写入升级日志、重复投递幂等去重 |
| O 二期后置扩展（O01–O04） | 微服务演进拆分设计文档；独立 `ops-agent-py`（Python + FastAPI + LangGraph）服务对接本项目 | 不阻挡纯 Java 后端交付，后续直接复用 OpenAPI / JWT / Redis / RabbitMQ 形成跨语言闭环 |

## 第一版业务边界

设备来自虚构园区/实验室/工业检测终端记录，无真实硬件连接。只保留三种角色：

| 角色 | 首版职责 | 不可越过的边界 |
| --- | --- | --- |
| REPORTER 报修人 | 选启用设备、创建、查自己的工单与日志、验收关闭 | 不能冒充别人报修、查询别人记录或自行派单 |
| ENGINEER 工程师 | 查分给自己的工单与日志、提交处理结果 | 不能处理别人名下工单或代报修人验收 |
| ADMIN 管理员 | 查询全部工单与日志、给 OPEN 工单指定启用工程师 | 不能随意跳状态或代报修人验收 |

流程为 `OPEN → IN_PROGRESS → RESOLVED → CLOSED`。数据库包含 `device`、`app_user`、`ticket` 与 `ticket_action_log` 四张核心表（后续按需补通知/告警记录表）；状态更新与写审计日志在同一 `@Transactional` 事务内执行，状态变更通过前置状态与 `expectedVersion` 乐观锁保护。

具体实现与验收细节见[项目文档](/learning/project-docs/)、[需求](/learning/project-requirements/)、[设计](/learning/project-design/)、[验收](/learning/project-verification/)。

## 中间件与二期 Python Agent 衔接边界

1. **Redis**：服务于高频设备/工单读缓存、JWT 登录态/黑名单、创建工单 `X-Request-Id` 防重幂等；二期启动 Python Agent 时可直接复用同一套 Redis 承载 Agent 会话记忆与结果缓存。
2. **RabbitMQ**：服务于工单状态变更 `AFTER_COMMIT` 异步通知解耦与 TTL + DLX 工单 SLA 超时升级告警；二期启动 Python Agent 时可直接订阅同一工单事件队列触发异步分诊，无需改动 Java 核心业务代码。
3. **权限与安全护栏**：所有工单读写均受 Spring Security + 三角色归属隔离 + `expectedVersion` 乐观锁保护，为后续任何外部服务或 Agent 调用提供天然防越权、防覆盖底线。

## 技术与学习方式

沿用 **Java 21 / Spring Boot 4.1.2 / MyBatis 4.1.0 / MySQL 8.4.13**，通过 Docker Compose 统一编排 **Redis** 与 **RabbitMQ**。将“AI 辅助编程”和“项目本身能力”严格分开记录；每次约 3 小时按最小可验证任务推进，完整阶段安排见[阶段学习计划](/learning/schedule/)。
