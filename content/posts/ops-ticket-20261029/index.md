---
title: "设备运维工单开发 — 09 JDBC 更新、版本检查与事务边界"
description: "从参数绑定与影响行数，到同一连接中的查询、旧版本拒绝、提交和故障回滚；提取更新方法，明确事务由谁管理，再认识 HTTP 请求与响应。"
date: 2026-10-29T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "MySQL", "JDBC", "事务", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 9
chapter_title: "JDBC 更新、版本检查与事务边界"
---

> 本篇按 **2026 年 10 月 29 日**归档，接续[上一篇 JDBC 查询](/posts/ops-ticket-20261028/)。这次我在独立 Demo 中练习 Java 更新事务，沿用[学习栏目](/learning/)的同一个工单项目；正式控制台仍使用文件仓库，尚未接入 Web 或 AI。

上次是让 Java 从数据库读出工单，这次是让 Java 修改工单，并决定保留还是撤销修改。我按指导编写了 `JdbcTicketUpdateDemo`，经历了先统一回滚、再检查版本、最后成功提交与失败回滚的过程。

我中间反复问了几个问题：SQL 字符串被改了吗？没有提交为什么查得到新标题？第一次更新成功为什么还会失败？把这些问题串起来，才能理解事务实际控制的是什么。

## 1 新 Demo 的入口与数据库连接

`JdbcTicketUpdateDemo.java` 位于 `src/test/java/cn/wishbottle/opsticket/`，与之前的查询 Demo 同包，有自己的 `main`。它是我手动运行的练习程序，不是 JUnit 测试，`mvn test` 不会自动执行它。

连接仍通过 `DriverManager.getConnection(...)` 创建；密码从本机环境变量 `OPS_TICKET_DB_PASSWORD` 获取。新类有自己的 IDEA 运行配置，之前查询 Demo 中设置的环境变量不一定会自动带过来。密码只在本机配置，不写进源码或公开笔记。

连接的基本用法沿用上次；这次新增的重点是：

```java
connection.setAutoCommit(false);
```

关闭自动提交后，后续更新不会每条执行完就自动提交，由当前连接上的 `commit()` 或 `rollback()` 决定如何结束事务。

## 2 SQL、statement 与数据库数据是三件事

我开始看到 `main` 和查询方法里都声明了 `String sql`，以为它们可能互相影响。其实它们是不同方法中的局部变量：一个保存 `UPDATE` 文字，一个保存 `SELECT` 文字，重名也不冲突。

以更新语句为例：

```java
String sql = """
        UPDATE ticket
        SET title = ?,
            version = version + 1
        WHERE id = ?
          AND version = ?
        """;

PreparedStatement statement = connection.prepareStatement(sql);
```

这句赋值从右向左理解：连接调用 `prepareStatement(sql)`，驱动返回一个实现 `PreparedStatement` 接口的对象，再由变量 `statement` 引用它。具体对象由驱动创建，所以这里没有自己写 `new`。

它与我之前学过的“接口类型的变量引用实现类对象”可以联系起来。`PreparedStatement` 是 JDBC 接口，`statement` 只是变量名；这时候还没有执行更新。

```java
statement.setString(1, "打印机卡纸（JDBC 提交练习）");
statement.setLong(2, 3L);
statement.setLong(3, expectedVersion);

int affectedRows = statement.executeUpdate();
```

| 代码 | 作用 |
| --- | --- |
| `setString(1, ...)` | 给第一个 `?` 绑定新标题 |
| `setLong(2, 3L)` | 给第二个 `?` 绑定编号 3；`3L` 是 long 值 |
| `setLong(3, expectedVersion)` | 给第三个 `?` 绑定预期版本 |
| `executeUpdate()` | 执行更新，并返回影响行数 |

参数位置从 **1** 开始。设置参数不会改写原来的 `sql` 字符串，其中的 `?` 仍然存在；绑定的参数属于 `statement`。参数绑定也不是自己拼接 SQL 字符串。

真正被 `UPDATE` 修改的是数据库中的记录：`title` 被新标题替换，`version` 在原值上加一。没有放在 `SET` 里的字段保持原值。`id` 和预期版本在 `WHERE` 中用于筛选，不是被改成别的值。

因此不用手写整条旧记录，但也不能完全忽略数据库当前内容：记录要存在、版本要匹配。以后如果规定“已关闭工单不能改标题”，还要加入状态规则。当前 Demo 没有实现这项额外规则。

## 3 ResultSet 负责读结果，查询方法共用连接

`executeQuery()` 返回 `ResultSet`，用于读取查询结果；`executeUpdate()` 返回 `int`，在本练习中表示更新影响的行数。两种返回值不能混用。

结果集最初位于第一行之前。`next()` 尝试移动到下一行，成功返回 `true`，之后才可以读字段。按主键查询至多一行，用 `if`；遍历多张工单时用 `while`。

这次增加的查询方法是：

```java
private static void printTicket(
        Connection connection, long ticketId
) throws SQLException {
    String sql = """
            SELECT id, title, version
            FROM ticket
            WHERE id = ?
            """;

    try (PreparedStatement statement = connection.prepareStatement(sql)) {
        statement.setLong(1, ticketId);
        try (ResultSet resultSet = statement.executeQuery()) {
            if (resultSet.next()) {
                System.out.println(
                        "编号：" + resultSet.getLong("id")
                                + "，标题：" + resultSet.getString("title")
                                + "，版本：" + resultSet.getLong("version")
                );
            } else {
                System.out.println("没有找到工单：" + ticketId);
            }
        }
    }
}
```

`main` 调用 `printTicket(connection, 3L)`，是把已有连接的引用传进去，不会新建连接。查询方法中的参数名即使也叫 `connection`，仍然引用调用方传来的那个对象。

```text
同一个 Connection
├── 创建用于 UPDATE 的 statement
└── 创建用于 SELECT 的 statement
```

两个语句对象可以不同，但它们使用同一个连接。只有再次调用 `DriverManager.getConnection(...)` 才是另外建立连接；连接相同的数据库，不代表是同一条连接。

资源也各自负责关闭：查询方法关闭自己创建的 `ResultSet`、`PreparedStatement`，`main` 关闭它创建的 `Connection`。关闭语句对象和提交事务是不同的动作。

## 4 更新已执行，不等于已经提交

我先练习修改后统一回滚，并分别打印修改前、修改后和回滚后的数据。

| 查询时机 | 标题 | 版本示意 |
| --- | --- | --- |
| 修改前 | 原标题 | N |
| UPDATE 后，尚未提交 | 新标题 | N＋1 |
| rollback 后 | 原标题 | N |

这里的 N 是运行前实际查到的版本，不能照抄最早练习里的 0 或 1。之前成功提交过更新后，当前版本可能已经更大。

我问“没 commit，为什么能输出新标题”，关键就在于：**同一个事务能查到自己已经执行、但尚未提交的修改。**

```text
executeUpdate() → 当前事务中数据已经修改
同一连接 SELECT → 看得到自己刚做的修改
rollback() → 撤销本次事务尚未提交的修改
再次 SELECT → 看到恢复后的值
```

`commit()` 不是执行修改的起点，而是提交当前事务。提交以后，再执行一次 `rollback()`，不能撤销先前已经提交的结果。`version` 也不是历史存档，不会自动保存旧标题。

在 MySQL 默认隔离级别下，另一个连接的普通查询看不到这些未提交的修改。对方已有读取事务时还可能继续使用旧快照，所以验证提交结果时，要确认对方没有一直停留在旧事务里。

## 5 版本条件与影响行数 1、0

`ticket.version` 是我们建表时定义的工单字段，不是 MySQL 软件版本号。它不会自己变化，是这句赋值让它加一：

```sql
version = version + 1
```

假设原版本为 1，第三个参数也绑定 1：

| 执行 | 数据库版本 | 参数要求版本 | 结果 |
| --- | --- | --- | --- |
| 第一次更新 | 1 | 1 | 匹配，更新后变为 2，影响 1 行 |
| 保留旧参数再次更新 | 2 | 1 | 不匹配，影响 0 行 |

实验中我复用同一个 `statement`，第二次只重新设置新标题，编号和预期版本参数继续保留。于是第二次不会把标题改成“旧版本不应该改成这个标题”。

SQL 返回 0，并不自动等于抛出 `SQLException`。语句可能正常执行，只是没有符合条件的记录。一般来说也可能是工单不存在，不能不加判断就把所有 0 都说成有人并发修改；当前实验已知是版本不匹配。

这个单连接实验说明旧版本条件会阻止更新，不等于正式业务已经有完整并发保护。之前 MySQL 双窗口的竞争实验也要与当前 Java 跟练分别记录。

## 6 从数据库读取版本，而不是写死 1L

最初用 `long expectedVersion = 1L` 便于理解参数位置，后来提取查询方法：

```java
private static long findTicketVersion(
        Connection connection, long ticketId
) throws SQLException {
    String sql = """
            SELECT version
            FROM ticket
            WHERE id = ?
            """;

    try (PreparedStatement statement = connection.prepareStatement(sql)) {
        statement.setLong(1, ticketId);
        try (ResultSet resultSet = statement.executeQuery()) {
            if (!resultSet.next()) {
                throw new IllegalArgumentException("工单不存在：" + ticketId);
            }
            return resultSet.getLong("version");
        }
    }
}
```

调用方接收返回值：

```java
long expectedVersion = findTicketVersion(connection, 3L);
```

与 `void printTicket(...)` 的区别是：前者返回一个 `long` 供后续更新使用，后者只是打印。即使通过 `return` 离开方法，try-with-resources 也会关闭它管理的查询资源，不会关闭作为参数传入的连接。

这里取得的是本次操作所依据的版本。旧版本更新失败后，不应该为了让它成功就随意重读版本并覆盖重试，否则可能绕过原本要保护的用户修改意图。

## 7 从只打印失败，到主动抛出异常

我为更新结果增加了检查：

```java
if (affectedRows != 1) {
    throw new IllegalStateException("修改未成功：工单不存在或版本已变化");
}
```

按主键更新一张工单，预期恰好影响一行。不符合预期时，由程序主动抛出业务异常，停止继续往下执行。

这是两个不同的失败来源：

- JDBC 执行 SQL 出错，可能抛出 `SQLException`。
- SQL 正常执行但没有更新到预期记录，由我的代码抛出 `IllegalStateException`。

`catch (SQLException | RuntimeException e)` 中的竖线表示捕获两类异常中的任意一类。`IllegalStateException` 和查询不存在工单时的 `IllegalArgumentException` 都属于运行时异常。

早期练习在 `finally` 里统一回滚，用于观察恢复过程。后来要加入成功提交，就把回滚移到 `catch`；不能继续把“所有路径都回滚”当作成功提交的流程。

## 8 成功提交，后续步骤失败则回滚

当前的事务核心如下。它位于已经建立连接的外层 try-with-resources 内，`simulateFailure` 是 `main` 中的实验开关。

```java
connection.setAutoCommit(false);

try {
    System.out.println("—— 修改前 ——");
    printTicket(connection, 3L);

    long expectedVersion = findTicketVersion(connection, 3L);
    updateTitle(connection, 3L, "打印机卡纸（JDBC 提交练习）", expectedVersion);

    System.out.println("—— 修改后，尚未提交 ——");
    printTicket(connection, 3L);

    if (simulateFailure) {
        throw new IllegalStateException("模拟后续操作失败");
    }

    connection.commit();
    System.out.println("本次修改已提交");
} catch (SQLException | RuntimeException e) {
    connection.rollback();
    System.out.println("操作失败，已回滚：" + e.getMessage());
}

System.out.println("—— 事务结束后 ——");
printTicket(connection, 3L);
```

`simulateFailure = true` 会在更新成功之后、提交之前故意抛异常。它不是数据库自己出故障，而是一个可控制的实验：假设后续业务步骤失败，前面的更新能否被一起撤销？

“更新成功为什么还会失败”指的是两个步骤：第一步 UPDATE 成功，并不能保证第二步也成功。例如以后可能有“修改工单，再保存操作日志”，第二步失败时，希望第一步也撤销。当前还没有实现这张日志表或日志写入，所以只用 `throw` 模拟，不能把它记成已完成日志事务。

成功路径：更新、检查都通过 → `commit()` → 新标题和增加后的版本保留。失败路径：中途抛异常 → 跳过提交 → `catch` 中回滚 → 恢复到本次事务之前。

我也在另一个 MySQL 终端查询成功提交的结果，确认新值不只是当前 Java 连接自己可见。模拟失败后回滚，不会撤销上一次已提交的结果。

当前源码的开关已经改回 `false`。再次运行会尝试真实提交，即使标题相同，成功更新仍会使版本加一。因此笔记里不把数据库最终版本写死为某个数字。

这是练习用异常处理，当前 catch 回滚后只打印原因，不构成完整的生产错误处理。回滚自身失败时保留原异常、提交时连接中断后的结果确认等问题尚未实现，不能把这个 Demo 当作生产事务组件。

## 9 提取 updateTitle：定义方法后，还要调用

提取后的更新方法是：

```java
private static void updateTitle(
        Connection connection,
        long ticketId,
        String newTitle,
        long expectedVersion
) throws SQLException {
    String sql = """
            UPDATE ticket
            SET title = ?,
                version = version + 1
            WHERE id = ?
              AND version = ?
            """;

    try (PreparedStatement statement = connection.prepareStatement(sql)) {
        statement.setString(1, newTitle);
        statement.setLong(2, ticketId);
        statement.setLong(3, expectedVersion);

        int affectedRows = statement.executeUpdate();
        if (affectedRows != 1) {
            throw new IllegalStateException(
                    "修改未成功：工单不存在或版本已变化，编号：" + ticketId
            );
        }
    }
}
```

第一次检查时，我只增加了方法，`main` 仍然保留旧 SQL 和更新块。程序可以运行，但实际上还没有调用新方法。后来删除重复代码，在读取版本后调用 `updateTitle(...)`，才完成真正的提取。

现在的职责是：

| 位置 | 职责 |
| --- | --- |
| `printTicket` | 查询并打印当前工单，关闭自己的查询资源 |
| `findTicketVersion` | 查询并返回版本，不存在则抛异常 |
| `updateTitle` | 参数化更新并检查影响行数，关闭自己的 statement |
| `main` | 创建和关闭连接，组织调用、决定提交或回滚 |

`updateTitle` 不提交事务、不新建连接，也不关闭调用方的连接。这样 main 后续可以继续使用同一个连接执行其他操作，最后统一决定是否提交。这次只是独立 Demo 的职责拆分，还没有接入正式 `TicketService` 或数据库仓库。

## 10 IDEA 黄色提示，以及刚开始接触的 HTTP

IDEA 的 Problems 中有两类提醒：

- `Value of parameter 'ticketId' is always '3L'`：当前调用始终传 3。保留参数仍有意义，以后可以查其他编号。
- `No data sources are configured...`：编辑器没有配置用于 SQL 补全与直接执行的数据库工具连接，不等于 Java 的 JDBC 连接失败。两者分别配置。

这两类提示不影响本次已成功运行的练习；不能据此推断所有黄色提示都可以忽略。

JDBC 小节收尾后，开始讲 HTTP 请求与响应、GET、URL/端口/路径、JSON 和 200/404。例如未来计划实现：

```http
GET http://localhost:8080/api/tickets/3
```

返回内容的格式示意：

```json
{
  "id": 3,
  "title": "打印机卡纸",
  "status": "OPEN"
}
```

地址是未来接口设计，不是目前已经能访问的服务。JSON 示例也不是当日数据库实测结果。路径不会自动执行 SQL，需要 Java 接收请求并调用业务与查询逻辑。

布置的下一项练习是打开博客的浏览器 Network 面板，刷新后找到主文档请求，读取 Request URL、Request Method、Status Code。**截至今天日结，我还没有反馈这项实操结果。** Spring Boot、Controller、MyBatis 都尚未接入。

## 11 这次验证了什么，下一步从哪里继续

以下运行结果来自我的课堂反馈；助手读取了最新源码核对位置和调用关系。本次日结没有再次运行 Java 程序或查询、修改数据库。

| 范围 | 已有证据 |
| --- | --- |
| 修改后回滚 | 我反馈影响行数为 1，回滚后标题与版本恢复 |
| 三阶段查询 | 我反馈同一连接中能看到新标题，回滚后恢复 |
| 旧版本更新 | 我反馈第一次 1、第二次 0，回滚恢复 |
| 自动读版本 | `findTicketVersion` 已接入，反馈结果仍为 1、0 |
| 成功提交 | 我反馈 Java 显示已提交，另一个 MySQL 终端也查到新标题与增加后的版本 |
| 中途失败 | 加入模拟失败，反馈更新后能回滚 |
| 方法提取 | 曾出现只定义不调用，经检查修正；最终 main 已调用 updateTitle，反馈模拟失败后仍能回滚，开关已改回 false |

现有永久 JUnit 仍为之前的 17 项，今天没有新增 JDBC 自动测试，也没有在日结时重跑它们。上面的 main Demo 运行反馈不能加进 JUnit 通过数量。代码经过指导与检查完成，不把“跟写并理解”写成“能独立设计完整持久层”。

下一次先完成 Network 面板的三个字段观察，解释客户端与服务器的请求响应，再按实际进度接入 Spring Boot，逐步实现首条真实查询接口。项目当前行为和边界继续以[项目文档](/learning/project-docs/)和[技能清单](/learning/checklists/)为准。
