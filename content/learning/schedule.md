{
  "title": "Java 设备运维工单后端阶段学习计划",
  "description": "统一第 1–17 周纯 Java 后端路线：第 1–13 周业务与权限闭环，第 14–17 周工程收口、Redis、RabbitMQ 与部署交付（二期独立 Python Agent 后置）。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 20,
  "group": "start",
  "draft": false,
  "lastmod": "2026-11-28T00:00:00+08:00"
}

更新于 2026-11-28。全站统一采用 **第 1–17 周** 单一周号体系（不再区分新旧周号），每天约 3 小时，按可验收的最小任务推进。

**唯一主线：起步（J01–J10）→ A1（数据库与 HTTP 业务闭环 S/W）→ A2（工程规范与交付 E01–E10）→ M1（Redis 缓存与幂等 R01–R04）→ M2（RabbitMQ 异步解耦与死信 M01–M04）→ 贯穿基础与面试（P01–P07，P05 按需）。**

## 定稿边界与架构取舍（2026-11-28）

- **纯 Java 后端做透**：围绕 **Java 21 / Spring Boot 4.1.2 / MyBatis 4.1.0 / MySQL 8.4 / Redis / RabbitMQ** 落地完整企业级后端工程，覆盖权限隔离、事务回滚、乐观锁、联合索引、Cache-Aside 缓存、防重幂等、死信延迟告警、OpenAPI 接口文档、Tomcat 参数与 Docker Compose 一键部署。
- **不采用 Spring AI，二期独立 Python Agent**：不在 Java 侧编写大模型调用与离线评测；未来拓展 Agent 应用方向时直接以市场主流的 **Python（FastAPI + LangGraph）** 另起独立服务（`O02–O04`），复用本项目的 OpenAPI 接口、JWT 权限边界、乐观锁、Redis 与 RabbitMQ，两边解耦零返工。
- **不盲目硬拆微服务**：当前阶段保持高内聚单体工程，在架构文档中完整梳理设备域/工单域/通知域/AI 域的微服务拆分演进设计（`O01`），理解 Nacos、Gateway、OpenFeign 与最终一致性。完整验收口径见[技能 To-do List 与验收记录](/learning/checklists/)。

## 当前进度与实测证据（2026-11-28）

- **第 1–13 周已完成主体**：真实 MySQL 已跑通创建（自动绑定登录人）、派单（`assign`）、指定工程师解决（`resolve`）、原报障人验收关闭（`close`）四态闭环；已清理早期文件/控制台旧代码并统一为标准 Spring Boot 8 子包分层；已实测 Spring Security + MySQL `app_user` 登录、`@PreAuthorize` 角色授权、单条详情与日志三角色归属隔离、`expectedVersion` 乐观锁（`409`），以及 `ticket_action_log` 审计表 + `@Transactional` 事务绑定与 H2 外键失败回滚测试（4 项全绿）。
- **验收口径**：主线 46 项中已正式验收保持 **6 项（`J01–J06`）**，跟练待巩固保持 **22 项**，待学 **18 项**（另设 5 项按需/后置不计入分母）。本次纯方案与周号统一不新增任何验收勾选。

## 统一周次总览（第 1–17 周）

| 周次 | 阶段 | 核心内容与亲手交付 | 当前状态 / 达标证据 |
| --- | --- | --- | --- |
| **第 1–6 周** | **起步 + A0**（J / S / W01） | Java 对象封装、集合/异常、Maven、MySQL 表约束、JOIN/统计/事务与 JDBC 练习（见[第 1 至 6 周](/learning/java-sql/)） | **已走完主体**（J01–J06 已验收，其余沿途巩固） |
| **第 7–13 周** | **A1 + A2 前半**（W / E01–E05） | Spring Boot Web、MyBatis 映射、四态闭环、Spring Security 数据库登录、三角色归属隔离、乐观锁与操作日志事务（见[第 7 至 13 周](/learning/web-security/)） | **已跑通主流程**（真实 MySQL 四态闭环 + H2 外键回滚 4 项全绿） |
| **第 14 周（当前）** | **A2 工程规范收口**（E01/E03/E07/E08/E09 + S06） | 收口 `/api/v1/tickets` 列表三角色隔离动态分页与 `/api/v1/devices`；补高频联合索引并造数跑 `EXPLAIN`；`@Valid` + `LoginUser` + `Result<T>` 瘦身 Controller；接入 OpenAPI 3 / Knife4j、SLF4J + MDC、Fat JAR 与 Tomcat 参数 | 多角色列表权限与动态分页实测、`EXPLAIN` 记录、在线接口文档可调用、`java -jar` 正常启动并见 `requestId` 日志 |
| **第 15 周** | **M1 Redis 缓存与幂等**（R01–R04 + E02/E05） | Docker 启动 Redis + Spring Data Redis；认证升级为 JWT + Redis；设备/工单 Cache-Aside 缓存（空值防穿透、随机 TTL 防雪崩、更新删缓存）；`X-Request-Id` 防重幂等与限流；对比 Redisson 分布式锁与乐观锁 | 实测缓存命中/回源/删缓存/防穿透、重复提交幂等拦截、JWT 登出黑名单生效 |
| **第 16 周** | **M2 RabbitMQ 异步与死信**（M01–M04） | Docker 启动 RabbitMQ + Spring AMQP；`@TransactionalEventListener(phase = AFTER_COMMIT)` 异步通知解耦；TTL + 死信队列（DLX）工单超时未派单自动升级告警；Publisher Confirm + 手动 ACK + `messageId` 消费幂等 | 实测事务回滚不误发、超时工单自动写入升级日志、已派单忽略、重复消息幂等去重 |
| **第 17 周** | **并发测试、部署与压测交付**（E06/E08/E09/E10/P07） | 真实 MySQL 隔离回滚与多线程并发派单测试；Docker Compose 一键编排与 Linux/备份恢复排错；JMeter/Wrk 缓存前后查询压测；完善《架构与接口设计文档》（含微服务演进设计 `O01`）与 5–8 分钟模拟面试 | 并发派单仅 1 次成功其余 409、一键编排与真实压测记录、可脱稿讲解项目架构与排错案例 |

> **全程并行（贯穿 P01–P07）**：每天 1–2 道力扣 Hot 100（兼练 ACM 输入输出模式）+ 结合项目持续整理 MySQL / Redis / RabbitMQ / JUC / JVM / Tomcat 核心笔记。

## 按阶段看网课与做练习

学习方式：遇到卡点再针对性看 1–2 集短视频并对照官方文档，看完立刻回到工单项目写最小变体并验证，不刷完大课再动手。

1. **第 14 周（事务、索引与 A2 收口）**：事务代理与回滚边界对照 [Spring 事务官方文档](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html) 及黑马 JavaWeb [P101 事务管理](https://www.bilibili.com/video/BV1yGydYEE3H/?p=101) / [P102 Spring 事务](https://www.bilibili.com/video/BV1yGydYEE3H/?p=102)；索引与执行计划对照 [MySQL 8.4 EXPLAIN 文档](https://dev.mysql.com/doc/refman/8.4/en/using-explain.html)；安全与内嵌 Tomcat 配置参考 [Spring Security 文档](https://docs.spring.io/spring-security/reference/index.html) 与 [Spring Boot Embedded Web Servers](https://docs.spring.io/spring-boot/reference/web/servlet.html#web.servlet.embedded-container)。
2. **第 15 周（M1 Redis 缓存与幂等）**：按需观看黑马 Redis [P4 认识 Redis](https://www.bilibili.com/video/BV1cr4y1671t/?p=4)、[P9–P13 常用类型](https://www.bilibili.com/video/BV1cr4y1671t/?p=9)、[P35–P38 缓存与更新策略](https://www.bilibili.com/video/BV1cr4y1671t/?p=35)，结合 [Spring Data Redis 官方文档](https://docs.spring.io/spring-data/redis/reference/) 直接落到设备/工单缓存与防重幂等。
3. **第 16 周（M2 RabbitMQ 异步与死信）**：对照 [RabbitMQ 官方 Tutorials](https://www.rabbitmq.com/tutorials) 与 [Spring AMQP 官方文档](https://docs.spring.io/spring-amqp/reference/) 落地 Direct/Topic Exchange、`AFTER_COMMIT` 通知、TTL + DLX 超时告警与手动 ACK 幂等。

## 历史路线归档说明

2026-11-14 至 11-24 曾短暂规划“Python + Redis + LangGraph”双栈并行方案；2026-11-25 曾短暂规划“纯 Java 侧 `B01–B09` / `C01–C04`”轻量 AI 方案；2026-11-28 结合实际岗位需求与技术栈分工，正式收口为**第 1–17 周统一编号的纯 Java 后端（含 Redis + RabbitMQ）**主线，AI / Agent 留待二期采用 Python 独立服务推进，旧草案条目已归档备查，不再作为当前执行计划。
