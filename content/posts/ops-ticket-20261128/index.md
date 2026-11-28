---
title: "设备运维工单开发 — 20 接口路径收口与列表三角色隔离"
description: "启动第 14 周 A2 工程规范收口：将工单接口统一收口至 /api/v1/tickets 并下线 3 个无权限调试读接口，补齐单条详情的工程师权限与列表查询的 SQL WHERE 三角色隔离，完成分页前置设计。"
date: 2026-11-28T22:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Spring Boot", "MyBatis", "Spring Security", "SQL", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 20
chapter_title: "接口路径收口与列表三角色隔离"
---

> 接续[上一篇：查询归属隔离、操作日志与事务回滚验证](/posts/ops-ticket-20261127/)。今天先把后续学习路线收口为纯 Java 后端（统一第 1–17 周，补齐 Redis 与 RabbitMQ，AI 留待二期独立 Python 服务），随即进入**第 14 周 A2 工程规范收口**的第一步：收口 `/api/v1/tickets` 接口路径、下线越权调试接口、落地列表接口的三角色数据库层隔离，并为下一步动态筛选与分页做好设计。

## 1 收口 `/api/v1/tickets` 与下线 3 个无权限调试接口

之前 `DatabaseTicketController` 里还留着 `/api/db/tickets` 的练习路径，以及 3 个早期练习 MyBatis 映射时写下的调试读接口：
- `GET /api/db/tickets/{id}/title`（`findTitle`）
- `GET /api/db/tickets/{id}/domain`（`findDomain`）
- `GET /api/db/domain/tickets`（`findAllDomains`）

这 3 个接口既没有 `@PreAuthorize` 角色校验，也没有数据归属隔离——如果不清理，任何登录用户直接调 `/api/db/domain/tickets` 就能绕过权限把全表工单拉出来，属于越权后门。

我在 `DatabaseTicketController` 类上加上 `@RequestMapping("/api/v1/tickets")`，把所有业务接口收口为标准版本路径，并删除了上述 3 个调试读接口。删除前确认过：底层 `DatabaseTicketRepository.create(...)` 依然会通过 `findById` 构造领域对象 `Ticket` 做业务规则校验，删掉调试 HTTP 入口不会影响任何正式功能（仅早期未接认证的 `DatabaseTicketHttpTest` 仍指向旧路径，留待后续统一重构测试）。

代码复核时抓到 1 处漏改：`close` 方法的 `@PostMapping("/api/db/tickets/{id}/close")` 忘了去掉旧前缀。加上类级 `@RequestMapping` 后会拼成 `/api/v1/tickets/api/db/tickets/{id}/close`，及时改成了 `@PostMapping("/{id}/close")`，并顺手删掉了 `findSummary` 中未使用的局部变量 `currentAuthorities`。

## 2 补齐单条详情 `GET /api/v1/tickets/{id}` 的工程师权限

上一篇给单条查询加归属隔离时，`@PreAuthorize` 只放行了 `ADMIN` 和 `REPORTER`，漏掉了 `ENGINEER`。这次顺手补齐：
- 权限注解改为 `@PreAuthorize("hasAnyRole('ADMIN', 'REPORTER', 'ENGINEER')")`；
- 参照 `findLogs` 补上工程师归属拦截：当角色是 `ENGINEER` 且 `summary.getAssigneeId() == null || !summary.getAssigneeId().equals(currentUser.getId())` 时返回 `403`，避免未派单工单的 `null` 处理人触发空指针。

## 3 列表接口三角色隔离：为什么过滤必须写在 SQL `WHERE` 里

在改 `GET /api/v1/tickets` 之前，先明确了三个角色在列表页的可见范围：
- `ADMIN`：查看全部工单；
- `REPORTER`：只看自己报修的工单（`reporter_id = 当前用户`）；
- `ENGINEER`：只看派单给自己的工单（`assignee_id = 当前用户`）。

为什么这个条件不能偷懒写成“先 `findAllSummaries()` 把全表查到 Java 里，再用 `for` 循环过滤”？这次彻底理清了三层原因：
1. **保护 JVM 堆内存与数据库 I/O**：Java 程序里所有 `new` 出来的对象都放在 JVM 堆内存（Heap）中。如果表里有 5 万条工单，全表查出来每行都会 `new` 一个 `TicketSummary`，并发请求一多既拖垮数据库 I/O 和网络带宽，又容易直接触发 `OutOfMemoryError`；写在 `WHERE` 里可以走索引，只传回命中的那几条。
2. **分页必须先过滤再 `LIMIT`**：假设库里 100 条工单中只有第 15、28、40 条属于 `reporter_a`，前端请求第 1 页、每页 10 条。如果 SQL 先 `LIMIT 10` 取出第 1–10 条再进 Java 过滤，第 1 页会直接变成 0 条，总数 `total` 也会错成 100；只有先在 SQL 里 `WHERE` 过滤再 `LIMIT`，每页条数和总数才准确。

## 4 逐层实现列表查询与代码审查踩坑

按现有分层从底向上打通了按角色过滤的查询链路：
1. **`TicketMapper`**：新增 `findSummariesByReporterId(@Param("reporterId") long reporterId)` 与 `findSummariesByAssigneeId(@Param("assigneeId") long assigneeId)`，并在 3 个列表查询上统一改为 `ORDER BY id DESC`（最新工单排在最前）。
2. **`TicketQueryRepository` → `DatabaseTicketRepository` → `DatabaseTicketQueryService`**：将两个查询方法逐层透传到 Service。
3. **`DatabaseTicketController.findAllSummaries`**：加上 `@PreAuthorize("hasAnyRole('ADMIN', 'REPORTER', 'ENGINEER')")` 与 `Authentication` 参数，查出 `currentUser` 后按角色分流，其他未知角色统一在 `else` 分支抛 `403 FORBIDDEN`。

过程中核对了两处知识点与 3 个编码细节：
- **为什么数据库 `CHECK` 约束已经锁死了 3 种角色，`else` 还要抛 `403`**：这是“默认拒绝（Fail-Closed）”的安全习惯——既满足 Java 编译器对所有分支返回值的要求，也防止以后新增第 4 种角色（如访客）时意外落入默认分支泄露全表数据。
- **代码审查抓出并修正的 3 个问题**：
  1. 新增的两个列表方法返回类型在 4 个文件里误写成了单个 `TicketSummary`（一旦查出超过 1 条，MyBatis 运行时会直接抛 `TooManyResultsException`），统一修正为 `List<TicketSummary>`；
  2. `DatabaseTicketQueryService` 里复制粘贴重复写了两个 `AssigneeId` 方法，修正为 `findSummaryByReporterId` 与 `findSummaryByAssigneeId`；
  3. `findAllSummaries` 补上 `currentUser == null` 判空（返回 `401`），并将 `currentUser.getRole().equals("ADMIN")` 改成常量在左的 `"ADMIN".equals(currentUser.getRole())` 防空指针。

修改完成后启动项目，在 Apifox 上实测通过：
- `GET /api/v1/tickets`：`admin_a` 返回按 `id` 倒序的全部工单，`reporter_a`、`reporter_b` 仅返回各自报修的工单，`engineer_a` 仅返回指派给自己的工单；
- `GET /api/v1/tickets/{id}`：`engineer_a` 查指派给自己的工单返回 `200`，查未指派给自己的返回 `403`；
- `GET /api/db/tickets`：旧路径已返回 `404`。

## 5 下一步动态分页的前置设计

收尾前先敲定了下一步 `GET /api/v1/tickets?status=&keyword=&page=&size=` 的两个设计点（代码留待下次编写）：
- **分页偏移与上限**：`page` 从 1 开始时 `offset = size * (page - 1)`；必须给 `size` 设上限（如最大 `100`），防止恶意传超大 `size` 把数据库和 JVM 堆内存打爆。
- **统一分页响应 `PageResult<T>`**：单纯返回 `List<TicketSummary>` 不够前端渲染分页条，需要包装 `items`、`page`、`size`、`total`、`totalPages` 5 个字段，并通过 MyBatis XML 的 `<sql>` + `<where>` + `<if>` 让列表查询与 `COUNT(*)` 复用同一套过滤条件。

## 6 这次完成到哪里与下一步

- **本次亲手完成并验收**：`/api/v1/tickets` 路径收口、删除 3 个无权限调试读接口、`GET /api/v1/tickets/{id}` 补齐 `ENGINEER` 归属隔离、`GET /api/v1/tickets` 落地 SQL `WHERE` 三角色隔离并在 Apifox 实测通过；完成动态分页的前置公式与响应结构设计。
- **尚未完成的边界**：MyBatis XML 动态筛选与 `PageResult<T>` 分页代码尚未编写；旧的 `DatabaseTicketHttpTest` 仍使用 `/api/db` 路径待后续统一重构。
- **下一步**：开启 `mybatis.mapper-locations=classpath:mapper/*.xml`，新建 `PageResult<T>` 与 `TicketMapper.xml`，实现 `GET /api/v1/tickets` 的 `status`、`keyword`、`page`、`size` 动态筛选与分页并完成 Apifox 实测。

继续查看[学习进度](/learning/#progress)、[技能清单](/learning/checklists/)和[项目设计](/learning/project-design/)。
