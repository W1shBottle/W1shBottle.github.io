---
title: "设备运维工单开发 — 19 查询归属隔离、操作日志与事务回滚验证"
description: "梳理标准 Spring Boot 分包职责，补齐查询归属隔离与创建自动取登录身份，建表并落地 ticket_action_log 审计日志，完成 @Transactional 事务回滚测试与日志查询接口。"
date: 2026-11-27T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Spring Boot", "MyBatis", "MySQL", "Spring Security", "事务", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 19
chapter_title: "查询归属隔离、操作日志与事务回滚验证"
---

> 接续[上一篇：乐观锁、资源归属授权与四态闭环](/posts/ops-ticket-20261126/)。本篇整理 11 月 27 日（含 28 日凌晨）的学习与实操：复盘标准 Spring Boot 分包规范，补齐查询归属隔离与创建接口的登录身份绑定，新建 `ticket_action_log` 操作审计表并将状态流转与写日志绑进 `@Transactional` 事务，亲手写出外键失败回滚测试，最后完成带三角色归属校验的日志查询接口。

## 1 复盘标准目录与 8 个子包的职责

昨天清理掉早期控制台与文件仓库代码后，今天先系统理清了标准 Maven + Spring Boot 的目录职责：
- 根包 `cn.wishbottle.opsticket` 只留启动类 `OpsTicketApplication`，因为 `@SpringBootApplication` 默认向下扫描同包及所有子包；
- 业务与框架代码按职责归位到 8 个全小写单数子包：`config/`（安全配置与数据库登录）、`controller/`（HTTP 入口）、`service/`（业务校验与事务编排）、`repository/`（读写接口隔离与领域对象组装）、`mapper/`（MyBatis SQL）、`domain/`（领域模型与状态枚举）、`dto/`（请求/响应传输对象）、`exception/`（全局异常处理）。

## 2 查询归属隔离与创建工单自动取登录人

上一篇只做了写操作的归属隔离，查询和创建还留着两个安全缺口：

1. **`GET /api/db/tickets/{id}` 查询归属隔离**：
   - 在 `DatabaseTicketController.findSummary()` 中先查出工单摘要（不存在返回 `404`），再通过 `userMapper.findByUsername(authentication.getName())` 查出当前登录用户（无效返回 `401`，修正了初版误写成 `404` 和多余 `if` 的小问题）；
   - 当角色是 `REPORTER` 且 `summary.getReporterId() != currentUser.getId()` 时返回 `403`；实测 4 号工单（`reporterId = 4`）：`admin_a` 返回 `200`、`reporter_b` 返回 `200`、`reporter_a` 返回 `403`。
2. **`POST /api/db/tickets` 创建工单不再信客户端传 `reporterId`**：
   - 从 `CreateDatabaseTicketRequest` 删除 `reporterId` 字段（入参只保留 `title` 与 `deviceId`）；
   - 给 `create()` 加上 `@PreAuthorize("hasAnyRole('REPORTER', 'ADMIN')")`，并直接用 `currentUser.getId()` 传给 `databaseTicketCommandService.create(...)`。
   - 首次测试 `engineer_a` 误返回 `400`（提示报障人编号必须大于 0），很快定位到是修改后未重启应用、跑的仍是旧代码；重启后实测：`engineer_a` 返回 `403`，`reporter_a` 创建返回 `201` 且自动绑定 `reporterId = 1`，`reporter_b` 再查该单被拦为 `403`。

## 3 新建 `ticket_action_log` 表与 `@Transactional` 事务绑定

`ticket` 表只保存工单当前最新状态，无法追溯“谁在何时把工单从什么状态改成了什么状态”。因此需要一张操作流水表 `ticket_action_log`。

我在 IDEA Query Console 中手写并执行建表 SQL（同步保存到 `sql/01_schema.sql`），包含 `id`、`ticket_id`、`actor_id`、`action`、`from_status`、`to_status`、`created_at` 7 列，使用 `ENGINE=InnoDB`，并按 `fk_<当前表>_<关联目标>` 规范命名外键（`fk_ticket_action_log_ticket`、`fk_ticket_action_log_actor`）。执行 `DESC ticket_action_log;`（`DESCRIBE` 的缩写，用于查看表结构骨架）确认 `PRI` 主键、`MUL` 外键索引与 `CURRENT_TIMESTAMP(6)` 默认值均已生效。

随后新建 `TicketActionLogMapper.insertLog(...)`，并在 `DatabaseTicketCommandService` 中构造器注入 `TicketActionLogMapper`：
- 在 `assign`（新增第 4 个参数 `actorId`，由 Controller 从 `Authentication` 获取管理员编号，与被派单的 `engineerId` 区分）、`resolve`、`close` 三个方法上统一加上 `@Transactional`；
- 只有在 `affectedRows == 1`（工单更新确实生效）时才调用 `insertLog(...)`，避免传错版本号返回 `0` 时产生假日志。

用 Apifox 对 5 号工单实测：
- 派单传错版本 `99` 返回 `409`，查 `ticket_action_log` 确认仍是 `0` 行；
- 依次跑完 `assign`（`admin_a`，`id = 3`）→ `resolve`（`engineer_a`，`id = 2`）→ `close`（`reporter_b`，`id = 4`），查表得到 5 号工单完整的 3 条审计流水（`ASSIGN`、`RESOLVE`、`CLOSE`）。

## 4 用外键失败亲手验证 `@Transactional` 自动回滚

正常提交验证通过后，还需要证明“写日志失败时，前面已成功的 `UPDATE ticket` 会被真正回滚”。

我先修复了 `src/test/java/audit/DatabaseTicketTransactionTest.java`（之前全面检查时助手建立的独立 H2 事务测试类）：在 H2 建表补上 `version` 列，在手动配置的 MyBatis 中注册 `TicketActionLogMapper` 并补齐 `DatabaseTicketCommandService` 构造器第 2 个参数，原有 3 项创建事务测试跑绿。

接着在其中新增第 4 个测试 `assignRollsBackWhenActionLogInsertFails()`：
- 在 H2 的 `setUp()` 中补建 `app_user`（插入合法工程师 `id = 2`）与带外键的 `ticket_action_log` 表；
- 创建一张 `OPEN` / `version = 0` 的测试工单，故意传入不存在的操作人 `actorId = 999` 调用 `service.assign(...)`；
- 第 1 条 `UPDATE ticket` 执行成功，紧接着第 2 条 `insertLog` 触发真实外键约束异常；
- 用 `assertThrows(RuntimeException.class, ...)` 与 `jdbc.queryForObject(...)` 断言回查工单的 `status` 仍是 `"OPEN"`、`version` 仍是 `0L`——4 项测试全绿，直观证明事务回滚生效。

## 5 暴露日志查询接口与三个架构细节复盘

最后新增 `TicketActionLogItem`（用 `LocalDateTime` 承接 `created_at`）、`TicketActionLogMapper.findByTicketId(...)`、`DatabaseTicketQueryService.findLogsByTicketId(...)` 与 `GET /api/db/tickets/{id}/logs`（`@PreAuthorize("hasAnyRole('ADMIN', 'REPORTER', 'ENGINEER')")`）。

代码复核时抓出一个严重 Bug：我在两个归属判断 `if` 里把 `currentUser.getRole()` 误写成了 `authentication.getName()`（用户名永远不等于角色名 `"REPORTER"`/`"ENGINEER"`，导致归属拦截形同虚设）。修正为 `currentUser.getRole()` 并重启后，重测 5 号工单（`reporterId = 4`、`assigneeId = 2`）与 3 号未派单工单：
- `admin_a` 查 5 号日志 → **`200`**（返回完整 3 条 JSON 数组）；
- `engineer_a` 查 5 号日志 → **`200`**；
- `reporter_a` 查 5 号日志 → **`403`**；
- `engineer_a` 查 3 号日志 → **`403`**。

这一步也一并理清了三个常见 Java / Spring 问题：
1. **为什么 `Service` 直接调用了 `TicketActionLogMapper`**：`TicketActionLogMapper` 本身就是接口（由 MyBatis 生成代理实现），对于简单流水读写无需硬套一层纯转发的 `Repository`；而原有的 `DatabaseTicketRepository` 保留了领域对象组装、`create` 事务封装以及读写接口隔离（`TicketQueryRepository` / `TicketWriteRepository`），无需折腾删除。
2. **为什么 `reporterId` 用 `!=`，而 `assigneeId` 用 `== null || !...equals(...)`**：`reporterId` 是基本类型 `long` 不会为 `null`，可直接用 `!=` 比较数值；`assigneeId` 是包装类对象 `Long`（未派单时为 `null`），既要先判 `null` 防空指针，又要用 `.equals(...)` 比较数值（避免超过 `-128 ~ 127` 缓存范围时 `==`/`!=` 比较对象内存地址出错）。
3. **为什么 `DatabaseTicketCommandService.create` 没贴 `@Transactional`**：它当前的 `@Transactional` 贴在下一层 `DatabaseTicketRepository.create(...)` 上，覆盖了插入、主键检查与回查。

## 6 这次完成到哪里与下一步

- **本次亲手完成并验收**：查询与创建的归属隔离和登录身份绑定、`ticket_action_log` 建表与三态审计日志、`@Transactional` 正常提交与 H2 外键失败回滚验证、`GET /api/db/tickets/{id}/logs` 三角色归属隔离。
- **尚未完成的边界**：`GET /api/db/tickets` 列表接口尚未补权限控制；回滚测试目前跑在独立 H2 内存库，真实 MySQL 测试库集成、SLF4J 规范日志与创建防重幂等仍待后续补齐。
- **下一步**：收尾 A2 剩余小边界（列表接口权限、SLF4J 日志与基础集成验证），随后正式进入 **B 阶段：Java AI 业务功能（B01–B09）**。

继续查看[学习进度](/learning/#progress)、[技能清单](/learning/checklists/)和[项目设计](/learning/project-design/)。
