---
title: "设备运维工单开发 — 16 创建事务、仓库分层与数据库派单"
description: "复盘创建后的回查和事务提交，梳理请求 DTO、查询 DTO 与仓库接口的分工，并用 Apifox 在隔离数据库中练习工单派单。"
date: 2026-11-15T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Spring Boot", "MyBatis", "MySQL", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 16
chapter_title: "创建事务、仓库分层与数据库派单"
---

> 接续[上一篇：数据库创建 POST 与自增主键](/posts/ops-ticket-20261109/)。这篇整理上一篇之后尚未归档的学习：创建工单后为什么还要回查、事务何时提交、数据在各层如何流动，以及数据库派单的成功路径练习。

## 1 从一次创建请求看分层

创建工单时，客户端发送标题、设备编号和报修人编号。结合现在的代码，处理过程可以画成：

~~~text
请求 JSON
  ↓
CreateDatabaseTicketRequest
  ↓
DatabaseTicketController
  ↓
DatabaseTicketCommandService
  ↓  按 TicketWriteRepository 的约定调用
DatabaseTicketRepository
  ↓
TicketMapper → MyBatis → 数据库
  ↓
取得新编号、回查并转换成 Ticket
  ↓
返回给 Controller，由 Spring 转成 JSON 响应
~~~

`Controller` 负责接收 HTTP 请求和组织响应；`Service` 负责校验和安排业务；`Repository` 定义或实现数据访问；`Mapper` 中的 SQL 交给 MyBatis 执行。层与层之间通过方法调用传递数据。

这里的 `DatabaseTicketCommandService` 是**业务服务层**。名字里的 `Command` 表示它处理创建、派单等会改变数据的操作；`DatabaseTicketQueryService` 负责查询。

## 2 接口仓库和实现类分别做什么

之前我问过：Service 是不是调用仓库接口的方法，再由实现类执行？现在的数据库写入链路正是这样：

~~~java
// Service 中的字段类型是接口
private final TicketWriteRepository ticketWriteRepository;

// Service 调用接口约定的方法
return ticketWriteRepository.assign(ticketId, engineerId);
~~~

`TicketWriteRepository` 规定“可以创建、派单”，真正的数据库实现是 `DatabaseTicketRepository`。Spring 创建并注入实现对象后，Service 就可以通过接口调用，不用自己写 SQL。实现类再调用 `TicketMapper`，由 MyBatis 执行映射的 SQL。

查询与写入的约定目前分成 `TicketQueryRepository`、`TicketWriteRepository`，同一个 `DatabaseTicketRepository` 实现这两个接口。`Mapper` 负责具体 SQL，在这种分层里承担接近 DAO 的数据库访问职责。

旧的 `TicketRepository` 仍用于文件版和内存版，它没有被删除。目前文件版 `/api/tickets` 和数据库版 `/api/db/tickets` 使用不同的数据来源；数据库功能完善前，不能把两边的数据当成自动同步，也没有因为这次派单就删除文件仓库。

## 3 三种数据对象各在什么时候出现

我之前容易把“请求对象”和“数据库查询结果”混在一起。按这次创建流程区分：

| 对象 | 什么时候使用 | 主要作用 |
| --- | --- | --- |
| `CreateDatabaseTicketRequest` | 客户端发送创建请求时 | 接收 JSON 中的 `title`、`deviceId`、`reporterId` |
| `TicketInsert` | Repository 准备插入时 | 装入要插入的数据；数据库生成的编号回填到它的 `id` |
| `TicketSummary` | Mapper 查询数据库之后 | 接收查询出的 `id`、`title`、`status`、`assigneeId` |
| `Ticket` | 需要领域工单对象时 | 表示工单并承载标题、状态等规则 |

例如查询数据库时，`assignee_id` 可以映射为 `assigneeId`。摘要查询接口可以直接返回 `TicketSummary`，Spring 再把它转换成 JSON；需要领域对象时，`TicketSummaryConverter` 会调用 `Ticket.restore` 做状态与处理人的规则检查。

DTO 是 Java 对象，不是发送到网络上的 JSON 文本。请求进来时，框架把 JSON 中匹配的字段读进请求对象；响应返回时，再把可序列化对象转换成 JSON。

## 4 什么叫“回查”

创建时，`INSERT` 的影响行数告诉我们改了多少行；主键回填告诉我们数据库分配了哪个编号。它们不等于已经拿到所需的完整工单。

现在的 `DatabaseTicketRepository.create` 做了以下事情：

~~~text
构造 TicketInsert
→ 执行 INSERT，检查影响行数
→ 检查回填的 id
→ 按 id 查询刚才插入的记录
→ 将查询结果转换成 Ticket
~~~

最后这次“根据新编号再查询”就是**回查**。这样可以读取数据库保存的状态、处理人等数据，再返回实际的工单对象。

例如插入时没有传处理人，数据库按表规则给新工单默认状态；回查后才能按照查询结果构造并返回工单。`TicketInsert`、`TicketSummary` 和 `Ticket` 出现在不同环节，各自承担不同职责。

## 5 创建事务：什么时候提交，失败为什么回滚

助手在检查项目时，为 `DatabaseTicketRepository.create` 加了 `@Transactional`。创建方法中的插入、主键检查和回查需要作为一个整体：

~~~text
开始事务
  ↓
INSERT → 取得 id → 回查并转换 Ticket
  ↓
方法正常结束 → 提交
~~~

提交表示让这一事务的修改成为数据库中的已提交结果；回滚表示撤销该事务尚未提交的修改。这里回查沿用当前创建事务，因此能读取本事务刚写入的数据。

如果插入后发现没有拿到主键，或按新编号回查不到工单，代码会抛出 `IllegalStateException`。在当前由 Spring 管理、通过事务代理调用的情况下，未被拦截的运行时异常会触发回滚，这次插入不会作为成功结果提交。

对于**没有外层事务**的这次调用，正常路径的顺序是：

~~~text
Repository 方法算出 Ticket
→ Spring 事务代理提交
→ 调用方 Service 拿到 Ticket
→ Controller 交给框架生成 201 JSON
~~~

如果已经存在外层事务，实际提交时机会受事务传播等配置影响。直接 `new DatabaseTicketRepository(...)` 也不会自动获得 Spring 的事务代理。

事务不能代替登录授权，也不能自动保证重复请求只创建一条工单。这部分事务代码和隔离自动测试由助手补充；我在本次教学中复盘了提交、回滚和回查，独立改写和更多事务场景仍需练习。

## 6 数据库派单：输入是什么

这次要把待派单工单分配给一名工程师。接口是：

~~~text
POST /api/db/tickets/{id}/assign
~~~

路径中的 `id` 是工单编号；请求体中的 `engineerId` 是目标工程师编号。例如隔离练习使用：

~~~json
{
  "engineerId": 2
}
~~~

Spring 把请求体转换成 `AssignTicketRequest`。Controller 先检查工程师编号是否为 `null`；Service 再检查工单编号和工程师编号是否大于 0，然后通过 `TicketWriteRepository.assign` 委托数据库仓库。

其中 `Long` 可以用 `null` 表示请求里没有提供编号；转换成需要 `long` 的方法参数前，先检查是否为 `null`。

## 7 一条 SQL 同时更新处理人和状态

`TicketMapper` 中的派单语句如下：

~~~java
@Update("""
    UPDATE ticket
    SET assignee_id = #{engineerId},
        status = 'IN_PROGRESS',
        version = version + 1
    WHERE id = #{ticketId}
      AND status = 'OPEN'
      AND EXISTS (
          SELECT 1
          FROM app_user AS u
          WHERE u.id = #{engineerId}
            AND u.role = 'ENGINEER'
            AND u.enabled = 1
      )
    """)
int assignTicket(@Param("ticketId") long ticketId,
                 @Param("engineerId") long engineerId);
~~~

可以分成两部分看：

- `SET` 规定修改后的值：处理人改为传入的工程师，状态变成 `IN_PROGRESS`，版本号在原值上加一。标题没有写在 `SET` 中，因此这条语句不会修改标题。
- `WHERE` 规定哪些行可以更新：工单编号要匹配、当前状态要是 `OPEN`，并且存在对应的已启用工程师。`EXISTS (SELECT 1 ...)` 在这里检查是否存在符合条件的用户，不是把数字 1 当作工程师编号。

`#{ticketId}` 和 `#{engineerId}` 与 `@Param` 标出的名字对应，由 MyBatis 绑定参数。语句返回的是**影响行数**：

- `1`：有一行符合条件并完成更新。
- `0`：没有行符合全部条件，可能是工单不存在、状态不允许派单，或者目标工程师不可用。

`version = version + 1` 只表示成功更新时递增版本；当前 SQL 没有用 `expectedVersion` 与旧版本比较，不能把它说成完整的乐观锁或并发方案。

## 8 影响行数怎样变成 HTTP 响应

Controller 接收 Service 返回的影响行数。编号为 0 或负数时，Service 抛出 `IllegalArgumentException`，Controller 捕获后转换成 400；工程师编号缺失时也会返回 400。

当影响行数为 0，Controller 会再查询一次工单：

| 情况 | 当前响应 | 含义 |
| --- | --- | --- |
| 更新 1 行 | 200 | 返回“派单成功” |
| 参数为空或编号不为正数 | 400 | 请求参数不符合要求 |
| 更新 0 行，回查不到工单 | 404 | 工单不存在 |
| 更新 0 行，工单仍存在 | 409 | 工单状态不允许派单，或工程师不可用 |

影响行数和 HTTP 状态码是两个概念：`0 / 1` 来自数据库更新结果；Controller 根据结果决定返回哪一种 HTTP 响应。更新和之后的分类查询是分开的操作，并发变化时错误分类仍需进一步设计。

SQL 检查了**被派单的人**是否为可用工程师，但当前项目还没有验证**发起派单的人**是否有权限。前者不是后者。

## 9 用 Apifox 和隔离数据库练习

Apifox 是发送 HTTP 请求并查看响应的工具。IDEA 的 HTTP Client 可以做同一类练习；在 Apifox 中，我使用 GET 查询和 POST 提交 JSON。

本次助手启动的是临时 H2 内存数据库，准备了虚构工单和工程师，不是我平时连接的真实 MySQL。练习过程：

1. 查询虚构工单 101：`status` 是 `OPEN`，`assigneeId` 是 `null`。
2. 向该工单发送派单 POST，请求体中的 `engineerId` 为 2。
3. 再次 GET 查询：我反馈派单成功，状态和处理人变化都符合预期。

也就是：

~~~text
派单前：OPEN        / 没有处理人
派单后：IN_PROGRESS / 处理人编号 2
~~~

当前 `TicketSummary` 不包含 `version`，所以这次 GET 响应不能单独证明版本具体增加了多少。此前我反馈过工程师编号为 0 时返回 400；助手也用其他虚构工单预先检查过成功、重复派单 409、非工程师 409 和不存在的工单 404。助手检查与我亲手操作的成功路径分别记录。

H2 的 MySQL 兼容模式方便隔离练习，但不等于已经在真实 MySQL 上完成所有派单、约束和并发场景的验收。

## 10 IDEA 数据库工具和项目连接

IDEA 的 Database 工具可以连接数据库、查看表和运行 SQL；DataGrip 是 JetBrains 的独立数据库工具，使用思路相近。它们是客户端，MySQL 是保存和处理数据的数据库服务。

IDEA 里配置一个数据源，和 Spring Boot 中的数据源是两份配置；如果它们的服务器、端口和数据库相同，看到的就是同一套数据。两边使用的驱动配置也可以不同。查询 `SELECT` 和执行 `UPDATE`、`DROP` 的影响不同：写操作会改变连接到的数据库，因此练习写入时先确认连接对象。

## 11 这次完成到哪里

- 我在指导下编写并梳理了数据库派单的 Mapper、仓库、Service、请求 DTO 和 Controller；成功路径由我在隔离环境中用 Apifox 亲手验证。
- 助手此前完成了查询分层整理，并在隔离环境验证现有 25 项 JUnit；这些不能等同于我独立编写或掌握测试，也不能当作真实 MySQL 的全面验收。
- 下一步在隔离环境理解并亲手验证派单失败分支，继续区分 400、404 和 409；再逐步处理授权、版本冲突及其他状态流。Python 继续按已看课程少量复习后，使用虚构工单练习只读查询。

继续查看[学习进度](/learning/#progress)、[项目设计](/learning/project-design/)和[运行与验收](/learning/project-verification/)。
