{
  "title": "第 14 至 17 周 工程收口、Redis、RabbitMQ 与交付",
  "description": "统一周号第 14–17 周：A2 工程收口、M1 Redis、M2 RabbitMQ、并发测试、Docker/Linux 部署、压测与面试交付。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 60,
  "group": "course",
  "draft": false,
  "lastmod": "2026-11-28T00:00:00+08:00"
}

更新于 2026-11-28。接续[第 7 至 13 周 Web 接口与登录权限](/learning/web-security/)，本页对应统一周号 **第 14–17 周**：专注把 **Java 21 / Spring Boot / MyBatis / MySQL / Redis / RabbitMQ** 后端工程彻底做透；不采用 Spring AI，二期独立 Python（FastAPI + LangGraph）Agent 服务与微服务拆分设计作为后置扩展（`O01–O04`）。

## 第 14 周 A2 工程规范收口与索引优化

**目标：把练习态接口升级为符合团队规范、文档齐全、可独立打包运行的后端服务。**

| 本周任务 | 核心产出与验收要点 |
| --- | --- |
| 接口收口与三角色列表分页（E03） | 将 `/api/db/tickets` 收口为 `/api/v1/tickets`，清理无权限调试接口；补齐列表三角色归属隔离 + MyBatis 动态多条件分页，补 `/api/v1/devices`（含 `device_type`/`model`） |
| 联合索引与 `EXPLAIN` 实测（S06） | 为 `ticket` 补 `(reporter_id, status, created_at)`、`(assignee_id, status, created_at)`、`(status, created_at)`，为 `ticket_action_log` 补 `note` 列与 `(ticket_id, created_at)`；造 1–5 万条测试数据对比 `EXPLAIN` 前后 `type/key/rows` |
| Controller 瘦身与统一响应（E01/E02） | 引入 `spring-boot-starter-validation`（`@Valid`）、自定义 `LoginUser` 移除 Controller 越层查 `UserMapper`、统一包装体 `Result<T>(code, message, data, requestId)`，将 404/403/409 分类下沉到 Service |
| 文档、日志与 Fat JAR（E07/E08/E09） | 接入 SpringDoc OpenAPI 3 / Knife4j 在线接口文档；`OncePerRequestFilter` 注入 SLF4J + MDC `requestId`；在 `pom.xml` 补 `spring-boot-maven-plugin` 并显式配置内嵌 Tomcat 线程参数 |

候选联合索引示例（以实际造数分布的 `EXPLAIN` 结果为准，不为每个字段盲目建索引）：

```sql
EXPLAIN
SELECT id, title, status, created_at
FROM ticket
WHERE reporter_id = 1 AND status = 'OPEN'
ORDER BY created_at DESC, id DESC
LIMIT 20;

CREATE INDEX idx_ticket_reporter_status_time
ON ticket (reporter_id, status, created_at DESC, id DESC);
```

## 第 15 周 M1 Redis 缓存、JWT 与防重幂等

**目标：围绕高频查询、登录态与防重提交真实痛点落地 Redis，并理解缓存一致性与锁的边界。**

| 本周任务 | 核心产出与验收要点 |
| --- | --- |
| Redis 接入与基础命令（R01） | Docker 启动隔离 Redis，接入 `Spring Data Redis`，配好 Key/Value 序列化与连接超时；掌握 String/Hash/List/ZSet 与 TTL |
| JWT + Redis 登录态升级（E02/R03） | 淘汰 HTTP Basic，接入 Spring Security + JWT 过滤器；利用 Redis 保存登出黑名单/登录态缓存，验证退出登录后旧 Token 失效 |
| 设备与工单 Cache-Aside 缓存（R02） | 查询先走 Redis 再回源 MySQL；落地**空值短 TTL 防穿透**、**随机 TTL 防雪崩**、**工单写操作提交后删除缓存**；模拟停掉 Redis 验证安全回源降级 |
| 创建防重幂等、限流与分布式锁对比（R03/R04/E05） | 请求头 `X-Request-Id` 结合 Redis `SET key value NX EX`（与 MySQL 唯一约束双保险）拦截重复报修提交；加简易限流；结合派单场景对比 Redisson 分布式锁与数据库 `expectedVersion` 乐观锁适用边界 |

> 安全红线：严禁把报修人私有列表塞进公共缓存 Key，缓存读取前必须先过 Spring Security 认证与归属校验。

## 第 16 周 M2 RabbitMQ 异步通知与死信队列 SLA 超时告警

**目标：落地生产级消息队列解耦与延迟告警，补齐可靠性投递与消费端幂等。**

| 本周任务 | 核心产出与验收要点 |
| --- | --- |
| RabbitMQ 与 Spring AMQP 接入（M01） | Docker 启动 RabbitMQ（含管理控制台），接入 `spring-boot-starter-amqp`，掌握 Direct/Topic Exchange、Queue、Binding 与 RoutingKey |
| 事务提交后异步通知解耦（M02） | 工单创建/派单/解决/关闭通过 `@TransactionalEventListener(phase = AFTER_COMMIT)` 发事件到 MQ，验证**事务回滚绝不误发消息**；消费者异步写通知记录并预留标准事件格式供二期 Python Agent 订阅 |
| TTL + 死信队列（DLX）超时告警（M03） | 新建工单发延迟消息，超时进入死信队列；消费者回查工单状态，若仍为 `OPEN` 则自动写入超时升级日志并触发告警，已派单则直接 ACK 忽略 |
| 可靠性投递与消费幂等（M04） | 开启 Publisher Confirm/Return 回调与消息持久化；消费者启用手动 ACK（`manual`）并基于 `messageId`（Redis 或去重表）实现消费幂等，重放同一消息不产生重复告警 |

## 第 17 周 并发测试、Docker 部署、压测与面试交付

**目标：补齐真实 MySQL 并发与回滚证据、一键容器编排、缓存压测数据，并能脱稿应对项目深度追问。**

| 本周任务 | 核心产出与验收要点 |
| --- | --- |
| 真实 MySQL 并发与回滚集成测试（E06） | 隔离测试库 `ops_ticket_test` 上用 `CountDownLatch` 启动多线程同时派单同一 `OPEN` 工单，验证仅 1 次成功、其余全部 409 且仅写 1 条审计日志；补真实 MySQL 外键/异常回滚测试与有界 `ThreadPoolExecutor` 拒绝策略实验 |
| Docker Compose 编排与备份恢复（E08） | 编写 `docker-compose.yml` 一键拉起 MySQL + Redis + RabbitMQ + Fat JAR；在 Linux 环境演练进程、端口与日志排错；用 `mysqldump` 备份并在空库恢复校验 |
| 缓存压测与技术交付文档（R04/E09/O01） | 使用 JMeter/Wrk 实测加 Redis 缓存前后的详情查询 QPS 与耗时（记录机器配置与并发数，不造假数字）；完善《架构与接口设计文档》（含 ER 图、四态图、错误码与微服务拆分演进设计 `O01`） |
| 项目表达与模拟面试（P07） | 整理 5–8 分钟脱稿项目讲稿与至少 1 个真实故障排查复盘；完成 1 次限时小改（如新增筛选条件并补测试），准备投递杭州 Java 后端日常/暑期实习 |

备份示例（恢复演练须使用新空库，绝不覆盖开发库）：

```powershell
mysqldump -u your_backup_user -p --single-transaction --no-tablespaces --set-gtid-purged=OFF --result-file=backups/ops_ticket_dev_backup.sql ops_ticket_dev
```

5–8 分钟项目讲解建议结构：**1 分钟业务与角色 → 2 分钟四态闭环与权限/乐观锁/事务回滚 → 2 分钟 Redis 缓存幂等与 RabbitMQ 死信超时告警 → 1–2 分钟真实排错案例、压测数据与二期规划（微服务拆分 + 独立 Python Agent）**。

## 二期后置扩展边界（O01–O04，不阻挡第 14–17 周交付）

- **O01（微服务拆分设计）**：当前保持高内聚单体，在架构文档中完整阐述按设备域/工单域/通知域/AI 域拆分的 Spring Cloud 演进方案（Nacos、Gateway、OpenFeign、最终一致性）。
- **O02–O04（独立 Python Agent 服务）**：第 17 周完成后，若向 Agent 开发方向延伸，直接采用市场主流的 **Python（FastAPI + LangGraph）** 另起 `ops-agent-py` 服务，复用本项目的 OpenAPI、JWT 权限、乐观锁、Redis 与 RabbitMQ，实现零返工跨语言扩展。

具体逐项验收口径与实时进度见[技能清单与验收模板](/learning/checklists/)与[阶段学习计划](/learning/schedule/)。
