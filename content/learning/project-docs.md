{
  "title": "设备运维工单项目文档",
  "description": "纯 Java 后端（Spring Boot + MyBatis + MySQL + Redis + RabbitMQ）当前实现、接口与 4 周冲刺进度。",
  "date": "2026-10-21T00:00:00+08:00",
  "lastmod": "2026-11-28T00:00:00+08:00",
  "weight": 160,
  "group": "project-docs",
  "draft": false
}

> 本组文档对应项目当前实现，与[总体规划](/learning/project/)配合阅读。后续功能以各页的实现状态为准。

围绕“设备报修 → 派单 → 处理 → 验收”持续演进的 **纯 Java 后端实战项目**（Spring Boot + MyBatis + MySQL，规划接入 Redis 与 RabbitMQ）。项目已完成从早期内存/文件控制台原型向真实数据库 Web 后端的完整切换，并清理旧文件仓库与控制台演示代码，按标准 Spring Boot 8 子包组织。

文档核对日期：2026-11-28。截至 2026-11-27，真实 MySQL 已跑通 `OPEN → IN_PROGRESS → RESOLVED → CLOSED` 四态闭环、Spring Security 数据库登录（MySQL `app_user` + BCrypt）、`@PreAuthorize` 角色授权、单条详情与操作日志三角色归属隔离、创建工单自动绑定登录人、`expectedVersion` 乐观锁（`409`），以及 `ticket_action_log` 操作审计表 + `@Transactional` 事务绑定与 H2 外键失败自动回滚测试（4 项全绿）。2026-11-28 已将后续主线定稿为 **4 周纯 Java 后端冲刺（A2 工程规范收口 → M1 Redis → M2 RabbitMQ → 并发测试与 Docker 部署）**，不采用 Spring AI，AI / Agent 能力留待二期以独立 Python（FastAPI + LangGraph）服务对接本项目。

## 项目文档

| 文档 | 解决的问题 |
| --- | --- |
| [需求与开发计划](/learning/project-requirements/) | 业务规则、已实现功能、4 周纯 Java 冲刺与二期边界 |
| [设计与数据约定](/learning/project-design/) | 标准 8 子包结构、四表模型、权限与乐观锁、Redis/RabbitMQ 演进设计 |
| [运行与验收](/learning/project-verification/) | 环境、运行命令、历次实测证据与验收边界 |
| [2026-11-13 全面检查记录](/learning/project-verification/#20-2026-11-13-隔离审查验证) | 阶段隔离审查、修复与历史边界说明 |

学习入口：[路线说明](/learning/start/) · [阶段计划](/learning/schedule/) · [技能清单](/learning/checklists/) · [实际学习进度](/learning/#progress)。本组项目文档记录实现与验收，课程材料记录后续学习安排。

## 当前功能与标准 8 子包职责

根包 `cn.wishbottle.opsticket` 仅保留启动类 `OpsTicketApplication`（启用 `@EnableMethodSecurity`），其余业务按职责分为 8 个子包：

- `config/`：`DemoSecurityConfig`（`PasswordEncoder` + `SecurityFilterChain`）、`DatabaseUserDetailsService`（实现 `UserDetailsService`，读取 MySQL `app_user` 表完成 BCrypt 登录认证）。
- `controller/`：`DatabaseTicketController` 承接查询、创建、派单、解决、验收关闭与日志查询接口，并从 `Authentication` 读取可信操作人身份（第 1 周计划收口为 `/api/v1/tickets` 并进一步瘦身）。
- `service/`：`DatabaseTicketQueryService` 负责工单与流水查询编排；`DatabaseTicketCommandService` 负责参数校验、委托写仓库，并在 `assign`/`resolve`/`close` 上用 `@Transactional` 绑定工单更新与写审计日志。
- `repository/`：`TicketQueryRepository` 与 `TicketWriteRepository` 做读写接口隔离；`DatabaseTicketRepository` 实现读写委托、领域对象组装及 `create` 事务边界。
- `mapper/`：`TicketMapper`（创建自增主键回填、摘要查询、带 `expectedVersion` 乐观锁条件更新的 `assign`/`resolve`/`close`）、`UserMapper`（按用户名查 `AppUser`）、`TicketActionLogMapper`（审计流水写入与按工单查询）。
- `domain/`：`Ticket`、`TicketStatus` 与 `TicketSummaryConverter`（通过 `Ticket.restore` 校验状态与处理人组合规则）。
- `dto/`：`CreateDatabaseTicketRequest`、`AssignTicketRequest`、`ResolveTicketRequest`、`CloseTicketRequest`、`TicketInsert`、`TicketSummary`、`TicketActionLogItem`、`AppUser`、`ErrorResponse`。
- `exception/`：`GlobalExceptionHandler` 统一处理不可读请求体（400）、参数类型不匹配（400）、`ResponseStatusException`（保留原状态码）及数据库约束冲突（400）。

## 当前已接通的 HTTP 接口（截至 2026-11-27）

| 请求 | 权限与核心行为 | 实测证据 |
| --- | --- | --- |
| `POST /api/db/tickets` | `REPORTER` / `ADMIN`；从 `Authentication` 自动取 `reporterId`，MyBatis INSERT + `@Options` 回填自增主键并返回 201 | `engineer_a` 403、`reporter_a` 201 自动绑 `reporterId=1`、`reporter_b` 查该单 403 |
| `GET /api/db/tickets/{id}` | `ADMIN` / `REPORTER`；返回 `TicketSummary`（含 `version`、`reporterId`、`assigneeId`），`REPORTER` 仅可读自己的工单 | `admin_a` 200、`reporter_b` 200、`reporter_a` 越权 403、未知 404 |
| `POST /api/db/tickets/{id}/assign` | `ADMIN`；校验 `OPEN`、目标启用工程师与 `expectedVersion`，成功转为 `IN_PROGRESS`、版本 +1 并同事务写 `ASSIGN` 日志 | 4 号/5 号工单实测 400/403/404/409/200，错版本不写假日志 |
| `POST /api/db/tickets/{id}/resolve` | `ENGINEER`；校验当前登录工程师为工单指派人、`IN_PROGRESS` 与 `expectedVersion`，成功转为 `RESOLVED`、版本 +1 并写 `RESOLVE` 日志 | `admin_a` 403、非指派单 403、旧版本 409、正确版本 200 |
| `POST /api/db/tickets/{id}/close` | `REPORTER`；校验当前登录人为原报障人、`RESOLVED` 与 `expectedVersion`，成功转为 `CLOSED`、版本 +1 并写 `CLOSE` 日志 | 他人越权 403、旧版本 409、正确版本 200（真实 MySQL 跑通四态闭环） |
| `GET /api/db/tickets/{id}/logs` | `ADMIN` / `REPORTER` / `ENGINEER`；三角色归属隔离返回按时间排序的审计流水 | `admin_a` 200、指派工程师 200、非本人报障人 403、非指派工程师 403 |
| `GET /api/db/tickets` 及遗留调试读接口 | 列表接口尚未补齐角色隔离与动态分页；`/title`、`/domain` 等调试读接口待第 1 周收口清理 | 列入第 1 周 A2 收口优先项 |

## 环境与运行

- **核心技术栈**：JDK 21、Maven、Spring Boot 4.1.2、MyBatis Spring Boot Starter 4.1.0、Spring Security、MySQL 8.4.13 LTS（Connector/J 26.10.0）、H2（仅 `test` 作用域用于隔离事务/HTTP 测试）。
- **数据库配置**：本机练习库 `ops_ticket_dev`，密码通过环境变量 `OPS_TICKET_DB_PASSWORD` 注入（不写入源码或公开文档）。四张表建表语句维护在 `sql/01_schema.sql`（`device`、`app_user`、`ticket`、`ticket_action_log`）。
- **构建与测试**：

```powershell
mvn clean test
mvn compile
```

在 IDEA 中使用 JDK 21 运行 `cn.wishbottle.opsticket.OpsTicketApplication`（默认端口 8080）。`pom.xml` 尚未接入 `spring-boot-maven-plugin`，可执行 Web Fat JAR 与内嵌 Tomcat 线程池参数配置列入第 1 周任务。

### 自动化测试现状

- `TicketTest`（6 项）：领域对象标题校验与边界。
- `audit/DatabaseTicketTransactionTest`（4 项）：基于隔离 H2 与真实 MyBatis Mapper 验证创建事务回滚及 `assignRollsBackWhenActionLogInsertFails`（外键失败触发 `UPDATE ticket` 自动回滚）。
- `DatabaseTicketHttpTest`：基于 H2 的只读 HTTP 集成验证。
- 真实 MySQL 测试库的多线程并发派单测试与权限回归测试列入后续 A2/第 4 周补齐项。

## 目录结构

```text
JavaProject/
├── pom.xml
├── README.md
├── tickets.http                                  # 手动 HTTP 验收请求
├── docs/                                         # 需求、设计、验收与审查记录
├── sql/                                          # 四表结构与练习 SQL
└── src/
    ├── main/
    │   ├── java/cn/wishbottle/opsticket/
    │   │   ├── OpsTicketApplication.java         # Spring Boot 启动入口
    │   │   ├── config/                           # Spring Security 与数据库认证
    │   │   ├── controller/                       # HTTP 接口入口
    │   │   ├── domain/                           # Ticket、TicketStatus、领域转换器
    │   │   ├── dto/                              # 请求/响应/插入/审计 DTO
    │   │   ├── exception/                        # GlobalExceptionHandler
    │   │   ├── mapper/                           # MyBatis Mapper（工单/用户/审计日志）
    │   │   ├── repository/                       # 读写仓库接口与实现
    │   │   └── service/                          # 查询与命令服务（@Transactional）
    │   └── resources/application.properties
    └── test/java/                                # JUnit、H2 事务/HTTP 测试与历史 Demo
```

## 已知限制（当前待收口项）

- `GET /api/db/tickets` 列表接口尚未补齐三角色归属隔离与动态分页；`/api/db` 路径前缀及遗留无权限调试读接口待收口为标准 `/api/v1/tickets` 与 `/api/v1/devices`。
- `DatabaseTicketController` 目前直接注入 `UserMapper` 并存在较多手动判空与回查分支，待引入 `@Valid`、自定义 `LoginUser`、统一返回体 `Result<T>` 并将异常分类下沉到 `Service`。
- 认证目前为 HTTP Basic + 临时关闭 CSRF，待第 2 周升级为 Spring Security + JWT + Redis 登录态管理。
- `ticket` 联合索引、`ticket_action_log.note` 处理说明列、创建 `X-Request-Id` 幂等防重、OpenAPI 接口文档、SLF4J + MDC 日志、可执行 Fat JAR、Redis 缓存与 RabbitMQ 异步通知/死信超时告警均列入下方 4 周计划逐步落地。

## 学习进度与下一步（2026-11-28 更新）

2026-11-28 路线定稿：围绕纯 Java 后端（Spring Boot + MyBatis + MySQL + Redis + RabbitMQ）开展 **4 周冲刺**，放弃 Spring AI，不再在 Java 侧编写大模型调用与重度离线评测；AI / Agent 能力留待二期直接以独立 **Python（FastAPI + LangGraph）** 服务对接本项目。

| 阶段 | 计划周期 | 亲手交付 | 达标证据 |
| --- | --- | --- | --- |
| A1 后端业务闭环 | 已跑通主流程 | 四表建模、MyBatis 映射、四态闭环与标准 8 子包分层 | 真实 MySQL 4 号/5 号工单跑通全链路与 400/404/409 分支 |
| A2 工程规范收口（当前） | 第 1 周 | 收口 `/api/v1/tickets` 列表三角色隔离分页与 `/api/v1/devices`、联合索引 `EXPLAIN`、`@Valid` + `LoginUser` + `Result<T>`、OpenAPI 文档、SLF4J + MDC、Fat JAR 与 Tomcat 参数 | 多角色列表权限与动态分页实测、1–5 万条造数 `EXPLAIN`、在线接口文档可调用、`java -jar` 正常启动 |
| M1 Redis 缓存与幂等（R01–R04） | 第 2 周 | Spring Data Redis 接入、JWT + Redis 登录态/黑名单、设备与工单 Cache-Aside（防穿透/雪崩/删缓存）、`X-Request-Id` 防重幂等与限流、分布式锁对比 | 缓存命中/回源/失效与防穿透实测、重复创建拦截、JWT 登出生效 |
| M2 RabbitMQ 异步与死信（M01–M04） | 第 3 周 | Spring AMQP 接入、`AFTER_COMMIT` 状态变更异步通知、TTL + 死信队列（DLX）工单超时未派单告警、Publisher Confirm + 手动 ACK + `messageId` 消费幂等 | 事务回滚不误发消息、超时工单自动写入升级告警日志、重复消息幂等去重 |
| 并发测试、部署与压测交付 | 第 4 周 | 真实 MySQL 隔离回滚与多线程并发派单测试、Docker Compose 一键编排与 Linux 排错、缓存前后压测对比、《架构与接口设计文档》（含微服务演进方案） | 多线程并发派单仅 1 次成功其余 409、一键拉起全套服务与真实压测记录 |
| 二期独立 Python Agent（后置 O02–O04） | 二期按需 | 另起独立 `ops-agent-py`（FastAPI + LangGraph），复用本项目 OpenAPI / JWT / 乐观锁 / Redis / RabbitMQ | 不阻挡纯 Java 后端交付，二期完成后形成双栈能力 |

**下一项亲手任务（第 1 周起步）**：收口 `/api/v1/tickets` 列表接口的三角色归属隔离与动态条件分页，清理无权限 `/api/db` 调试读接口，并补齐 `/api/v1/devices` 与 `ticket` 高频联合索引 `EXPLAIN` 验证。
