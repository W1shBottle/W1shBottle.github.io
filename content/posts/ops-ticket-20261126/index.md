---
title: "设备运维工单开发 — 18 乐观锁、资源归属授权与四态闭环"
description: "补齐派单 409 失败分支与 expectedVersion 乐观锁，实现指定工程师解决与原报障人验收关闭，在真实 MySQL 跑通四态生命周期，并完成旧代码清理与标准分层分包。"
date: 2026-11-26T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Spring Boot", "MyBatis", "MySQL", "Spring Security", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 18
chapter_title: "乐观锁、资源归属授权与四态闭环"
---

> 接续[上一篇：Spring Security 数据库登录与接口角色授权](/posts/ops-ticket-20261125/)。本篇整理 11 月 26 日（含 27 日凌晨）的后端核心推进：复验派单 `409` 分支、给写操作接入 `expectedVersion` 乐观锁、完成工程师解决（`resolve`）与原报障人验收关闭（`close`）两条状态流转及资源归属授权，并在提交 Git 检查点后清理旧文件仓库代码、按 Spring Boot 规范完成分层分包。

## 1 补齐派单 `409` 失败分支：从 `WHERE` 到回查分类

先查 `ops_ticket_dev.ticket` 确认了当前数据：1 号工单为 `IN_PROGRESS`，3、4、5 号工单为 `OPEN`。随后用 `admin_a` 在 Apifox 亲手复验了两种 `409` 场景：
- **重复派单**：向已是 `IN_PROGRESS` 的 1 号工单派单，不满足 `WHERE` 中的 `AND status = 'OPEN'`；
- **派给非工程师**：向 `OPEN` 工单传入 `engineerId = 1`（`reporter_a`），不满足 `WHERE` 中的 `AND EXISTS (... u.role = 'ENGINEER' AND u.enabled = 1)`。

两种情况的 `UPDATE` 受影响行数都是 `0`。Controller 拿到 `affectedRows == 0` 后，并不是直接返回固定错误，而是调用 `databaseTicketQueryService.findSummaryById(ticketId)` 回查一次：
- 返回 `null` → 工单根本不存在 → **`404 NOT_FOUND`**；
- 返回非 `null` → 工单存在，说明是状态、版本或目标工程师条件不满足 → **`409 CONFLICT`**。

## 2 给派单加上 `expectedVersion` 乐观锁

此前的派单 SQL 虽然写了 `SET version = version + 1`，但 `WHERE` 条件里并没有核对旧版本号。如果两个请求基于同一旧版本操作，或者以后 AI 基于旧版本生成了建议、期间工单又被别人修改，不校验旧版本就会发生静默覆盖。

实现分两步推进：
1. **先让查询返回版本号**：在 `TicketSummary` 新增 `private long version`，并在 `TicketMapper` 的摘要查询里补上 `version` 列。重启后实测 `GET /api/db/tickets/4` 返回 `version = 0`，`GET /api/db/tickets/3` 返回 `version = 3`。
2. **沿整条派单链路贯通 `expectedVersion`**：
   - `AssignTicketRequest` 新增 `private Long expectedVersion`。这里必须用包装类 **`Long`** 而不是基本类型 **`long`**——因为新工单的初始版本就是 `0`，如果用 `long`，客户端漏传该字段时会默认变成 `0`，反而误打误撞通过校验；用 `Long` 就能识别 `null` 并返回 `400`。
   - `TicketMapper.assignTicket` 在 `WHERE` 中加入 `AND version = #{expectedVersion}`，只有数据库当前版本匹配才允许更新并加 1。
   - `TicketWriteRepository` → `DatabaseTicketRepository` → `DatabaseTicketCommandService` → `DatabaseTicketController` 依次透传与校验。

过程中修掉了两处真实 Bug：
- Controller 判空时把第二个 `if` 误复制成了 `request.getEngineerId() == null`，修正为 `request.getExpectedVersion() == null`，并把 `request == null` 单独拆出返回 `"请求体不能为空"`；
- Service 校验一度误写成 `expectedVersion <= 0`（会拦死初始版本为 `0` 的所有新工单）且漏了分号，修正为 `expectedVersion < 0`。

重启后对 4 号工单（`OPEN`、`version = 0`）实测 4 组用例全部通过：
- 漏传 `expectedVersion` → **`400`**；
- 传入 `-1` → **`400`**；
- 传入错误版本 `99` → **`409`**；
- 传入正确版本 `0` → **`200`**，回查变为 `IN_PROGRESS`、`assigneeId = 2`、**`version = 1`**。

## 3 指定工程师解决工单（`resolve`）与资源归属授权

工单进入 `IN_PROGRESS` 后，下一步是 `POST /api/db/tickets/{id}/resolve`（`IN_PROGRESS → RESOLVED`）。这里立下一条安全底线：

> **任何“当前操作人是谁”都只能从服务端 `Authentication` 获取，绝不信任客户端 JSON 里传来的 `userId`。**

因此请求体 `ResolveTicketRequest` 只需要 `Long expectedVersion` 一个字段；后端在 `DatabaseTicketController` 中通过构造器注入 `UserMapper`，用 `userMapper.findByUsername(authentication.getName())` 查出当前登录用户的真实 `id`。

SQL 层在 `TicketMapper.resolveTicket`（修正了初版 `SET status = 'RESOLVED'` 后漏写逗号的语法错误）中同时卡死 4 个条件：`id`、`assignee_id`、`status = 'IN_PROGRESS'`、`version = #{expectedVersion}`。当 `affectedRows == 0` 时，Controller 回查工单摘要按序区分三种失败：

| 回查结果 | HTTP 状态码 | 原因 |
| --- | --- | --- |
| `summary == null` | `404` | 工单不存在 |
| `assigneeId` 为空或不等于当前登录工程师 `id` | `403` | 无权解决未指派给自己的工单 |
| 其余情况 | `409` | 工单状态不是 `IN_PROGRESS` 或版本号已变化 |

这一步也借着新注入的 `UserMapper` 复盘了**构造器注入**：Spring 启动时自动创建所需 Bean 并通过构造器赋值给 `private final` 成员变量；加 `final` 能在漏赋值时把问题拦在编译期，避免运行时空指针。

重启后用 Apifox 实测 4 组用例全部通过：
- `admin_a` 调用 `resolve` → **`403`**（角色不符）；
- `engineer_a` 解决未派单的 3 号工单 → **`403`**（资源归属拦截）；
- `engineer_a` 对 4 号工单传旧版本 `0` → **`409`**；
- `engineer_a` 对 4 号工单传正确版本 `1` → **`200`**，回查变为 `RESOLVED`、**`version = 2`**。

## 4 原报障人验收关闭（`close`）与四态闭环

为了完成最后一步 `POST /api/db/tickets/{id}/close`（`RESOLVED → CLOSED`），先在 `TicketSummary` 和摘要查询 SQL 中补上 `reporter_id`（`reporterId`），再按同样分层独立完成了 `TicketMapper.closeTicket`、`CloseTicketRequest`、Repository、Service 与 Controller `close`（`@PreAuthorize("hasRole('REPORTER')")`，回查时用 `summary.getReporterId() != currentUser.getId()` 拦截非原报障人返回 `403`）。

测试前把 `reporter_a` 和 `reporter_b` 的 `password_hash` 更新为本地练习密码对应的 BCrypt 哈希。首次请求 `reporter_a` 意外返回 `401`，按排查顺序核对 `CHAR_LENGTH(password_hash)` 均为 `60` 且控制台无格式警告，最后通过查看 Apifox「实际请求」里的 `Authorization: Basic ...` Base64 解码，抓出了真凶：**`Username` 输入框末尾多了一个隐形空格（`"reporter_a "`）**。

去掉空格后，对 4 号工单（`reporterId = 4` 即 `reporter_b`，`RESOLVED`，`version = 2`）实测 3 组用例全部通过：
- `reporter_a`（`id = 1`）尝试关闭 4 号工单 → **`403`**（报障人 A 动不了报障人 B 的单）；
- `reporter_b`（`id = 4`）传旧版本 `1` → **`409`**；
- `reporter_b` 传正确版本 `2` → **`200`**，最终回查 JSON：

~~~json
{
  "assigneeId": 2,
  "id": 4,
  "reporterId": 4,
  "status": "CLOSED",
  "title": "打印机缺纸",
  "version": 3
}
~~~

至此，一张工单在真实 MySQL 中完整走通了 `OPEN → IN_PROGRESS → RESOLVED → CLOSED` 四态生命周期。

## 5 清理早期旧代码与按 Spring Boot 规范分包

随着数据库主线跑通，目录里还混着早期未接数据库时的控制台与文件仓库代码（`ConsoleApp`、`TicketService`、`TicketRepository`、`FileTicketRepository`、`InMemoryTicketRepository`、`TicketFileStore`、`TicketController` 等）。也顺手理清了现有 `DatabaseTicketRepository` 的定位：它同时实现了只读接口 `TicketQueryRepository` 和写入接口 `TicketWriteRepository`，和旧接口 `TicketRepository` 无关。

按先存档再重构的工程习惯：
1. 本人先执行 Git 检查点提交，把四态闭环与旧代码一并锁进提交历史；
2. 随后由助手按确认清单移除 9 个旧主类与 17 个依赖旧文件仓库的测试/Demo，将 `pom.xml` 的 `<mainClass>` 改为 `OpsTicketApplication`，并移除 `DatabaseTicketHttpTest` 中原本用于替换旧文件仓库的初始化块；
3. 再由助手将散落在根包的 8 个类按职责迁入 `service/`、`repository/`、`domain/` 子包，根包只保留启动类 `OpsTicketApplication`（保证 `@SpringBootApplication` 向下扫描所有子包）。

清理与分包后执行 Maven 离线编译（`compile test-compile`：主代码 23 类 + 测试 11 类）零报错，`TicketTest` 6 项单元测试全部通过。这部分清理与分包迁移由助手协助完成，不计为本人独立重构。

## 6 这次完成到哪里与下一步

- **本次亲手完成并验收**：派单 `409` 分支与影响行数回查分类、`expectedVersion` 乐观锁（`assign` / `resolve` / `close`）、指定工程师解决与原报障人验收关闭的资源归属授权、真实 MySQL 四态闭环及 Base64 请求头排错。
- **尚未完成的边界**：`GET /api/db/tickets/{id}` 与列表接口尚未按报障人做查询归属隔离；`POST /api/db/tickets` 创建工单仍从请求体读 `reporterId`，尚未改为从 `Authentication` 自动获取；操作日志 `ticket_action_log` 与状态变更事务、创建防重幂等和双线程并发测试仍待补齐。
- **下一步**：给 `GET /api/db/tickets/{id}` 补上查询归属隔离（报障人 A 不能读取报障人 B 的工单），并把创建工单的 `reporterId` 改为从登录身份自动读取。

继续查看[学习进度](/learning/#progress)、[技能清单](/learning/checklists/)和[项目设计](/learning/project-design/)。
