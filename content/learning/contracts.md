{
  "title": "设备工单的数据与接口约定",
  "description": "四表结构、RESTful 接口契约、权限与乐观锁规则、Redis/RabbitMQ 约定与二期 Python Agent 边界。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 100,
  "group": "tools",
  "draft": false,
  "lastmod": "2026-11-28T00:00:00+08:00"
}

2026-11-28 核对：项目已清理早期控制台与文件仓库演示代码并按标准 8 子包分层；已将工单接口收口为 `/api/v1/tickets` 并下线 3 个无权限调试读接口，在真实 MySQL 跑通 `POST /api/v1/tickets`（自动取登录人）、`assign`/`resolve`/`close` 四态闭环 + `expectedVersion` 乐观锁、`GET /api/v1/tickets` 列表 / `GET /api/v1/tickets/{id}` 详情 / `GET /api/v1/tickets/{id}/logs` 三角色归属隔离，以及 `ticket_action_log` + `@Transactional` 事务与 H2 外键失败回滚测试。当前按统一第 14–17 周推进：**第 14 周继续动态分页、`/api/v1/devices` 与联合索引 → 第 15 周 M1 Redis → 第 16 周 M2 RabbitMQ → 第 17 周并发测试与 Docker 部署**，二期再以独立 Python 服务对接 Agent 能力。

## 当前样本和状态

`ops_ticket_dev` 已有 `device`、`app_user`、`ticket`、`ticket_action_log` 四张表；建表依据项目 `sql/01_schema.sql`。用户/设备实际编号为 1 至 4、1 至 3：`reporter_a=1`、`engineer_a=2`、`admin_a=3`、`reporter_b=4`；投影仪=1（已停用）、空调=2、打印机=3。所有实测均以真实 `SELECT` 为准，旧教材中的 101/102/103 仅作隔离教学样本。

## 第一版的角色与流程

```text
报修人创建 OPEN → 管理员派单 IN_PROGRESS → 指定工程师解决 RESOLVED → 原报修人验收 CLOSED
```

- `REPORTER` 只能看自己创建的工单与日志；`ENGINEER` 只能看指派给自己的工单与日志；`ADMIN` 查看全部。
- 操作人身份一律由服务端认证上下文获取，绝不信任请求体自报的 `reporterId` 或 `actorId`。
- 派单要求目标用户存在、启用且角色为 `ENGINEER`；创建要求目标设备启用。外键只保证引用存在，CHECK 只保证单行约束，不能替代业务权限与状态机校验。

## 表结构与演进约定

| 表 | 当前状态 | 字段与演进约定 |
| --- | --- | --- |
| `app_user` | 已有 SQL | `id`、`username`、`password_hash`（BCrypt）、`role`、`enabled` |
| `device` | 已有 SQL | `id`、`code`、`name`、`location`、`enabled`；第 14 周按需补 `device_type`、`model` 字段以贴合设备运维场景 |
| `ticket` | 已有 SQL | `id`、`title`、`description`、`device_id`、`reporter_id`、`assignee_id`、`status`、`version`、`created_at`、`updated_at`；第 14 周补 `(reporter_id, status, created_at)`、`(assignee_id, status, created_at)`、`(status, created_at)` 联合索引 |
| `ticket_action_log` | 已有 SQL | `id`、`ticket_id`、`actor_id`、`action`、`from_status`、`to_status`、`created_at`；第 14 周补 `note` 处理说明、`from_status` 允许 `NULL`（记录 `CREATE`）及 `(ticket_id, created_at)` 索引 |
| 幂等防重 / 通知记录 | 第 15–16 周补齐 | 创建防重采用 `X-Request-Id`（Redis `SET NX EX` + 数据库唯一约束双保险）；MQ 消费按 `messageId` 去重并记录通知/SLA 超时告警流水 |

编号在 Java 中用 `long`/`Long`，MySQL 用 `BIGINT AUTO_INCREMENT`。待派单处理人为 SQL `NULL`（Java `Long null`）。开发库 `ops_ticket_dev`，集成/并发测试使用独立 `ops_ticket_test`。

## 目标 RESTful 接口契约（第 14 周由 `/api/db` 收口至 `/api/v1`）

| 请求 | 输入与成功结果 | 核心规则 |
| --- | --- | --- |
| `POST /api/v1/auth/login`、`logout` | 登录签发 JWT（第 15 周接 Redis 黑名单） | Spring Security + BCrypt；淘汰 HTTP Basic |
| `GET /api/v1/devices` | 可报修启用设备列表（走 Redis 缓存） | 已登录可读；创建工单时服务端二次核验启用状态 |
| `POST /api/v1/tickets` | `title`、`description`、`deviceId` + Header `X-Request-Id`；成功 201 | `REPORTER`/`ADMIN`；身份取自 `LoginUser`；同 `X-Request-Id` 防重幂等 |
| `GET /api/v1/tickets` | `status`、`keyword`、`deviceId`、`page`、`size`；返回分页 `items`/`total` | 按三角色自动加数据归属过滤；稳定排序 `created_at DESC, id DESC` |
| `GET /api/v1/tickets/{id}` | 工单详情（含 `version`、`reporterId`、`assigneeId`） | 角色与资源归属校验，防越权读取 |
| `GET /api/v1/tickets/{id}/logs` | 工单操作流水列表 | 三角色归属隔离与详情一致 |
| `POST /api/v1/tickets/{id}/assign` | `engineerId`、`expectedVersion` | `ADMIN`、`OPEN`、启用 `ENGINEER`；同事务写 `ASSIGN` 日志 |
| `POST /api/v1/tickets/{id}/resolve` | `note`（处理说明）、`expectedVersion` | 指定 `ENGINEER`、`IN_PROGRESS`；同事务写 `RESOLVE` 日志 |
| `POST /api/v1/tickets/{id}/close` | `expectedVersion` | 原 `REPORTER`、`RESOLVED`；同事务写 `CLOSE` 日志 |

统一响应包装体：`Result<T>(code, message, data, requestId)`。状态码约定：参数校验失败 `400`、未认证 `401`、角色或资源越权 `403`、资源不存在 `404`、状态/版本/重复键冲突 `409`、服务内部错误 `500`（不暴露堆栈与凭证，返回 `requestId` 便于日志定位）。

## Redis 与 RabbitMQ 契约约定（第 15–16 周）

### Redis 键空间约定（M1）
- `device:detail:{id}` / `ticket:detail:{id}`：Cache-Aside 读缓存，空值短 TTL 防穿透、正常值带随机偏移 TTL 防雪崩；工单写操作提交后删除对应缓存键。
- `idemp:ticket:create:{userId}:{requestKey}`：创建防重键（`SET NX EX`），短时重复提交直接拦截。
- `auth:jwt:blacklist:{jti}`：JWT 主动登出黑名单，TTL 与 Token 剩余有效期一致。

### RabbitMQ 事件与死信约定（M2）
- **状态变更事件（Topic Exchange）**：路由键 `ticket.created` / `ticket.assigned` / `ticket.resolved` / `ticket.closed`，仅在数据库事务 `@TransactionalEventListener(phase = AFTER_COMMIT)` 后发送，消息体含 `messageId`、`ticketId`、`eventType`、`version`、`occurredAt`。
- **SLA 超时延迟队列（TTL + DLX）**：工单创建时投递延迟消息，超时进入死信队列；消费者回查工单状态，仍为 `OPEN` 则写入超时升级日志并触发告警，已派单则直接手动 ACK 忽略。
- **可靠性与幂等**：开启 Publisher Confirm/Return + 消息持久化；消费者开启手动 ACK 并基于 `messageId` 去重防重复消费。

## 二期独立 Python Agent 联调边界（后置 O02–O04）

未来启动独立 `ops-agent-py`（Python + FastAPI + LangGraph）服务时，严格遵守三条边界：
1. **不直连业务库**：Python Agent 只能通过本 Java 项目的受控 REST API（对照 OpenAPI 契约）或订阅 RabbitMQ 工单事件交互，禁止由模型拼 SQL 或直接写 MySQL。
2. **权限透传与最小权限**：调用 Java 只读查询工具时携带可信身份凭据，由 Java 端执行三角色数据归属隔离；模型输出、提示词或检索文档均不构成授权。
3. **人工确认与乐观锁写回**：Agent 只产出结构化诊断建议与引用来源，任何涉及派单或状态变更的操作必须由人工确认并走 Java 的 `expectedVersion` 乐观锁与事务审计接口。
