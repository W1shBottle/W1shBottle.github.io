---
title: "设备运维工单开发 — 08 SQL 统计、事务与 JDBC 查询"
description: "从 COUNT、LEFT JOIN 统计和分页，到事务回滚、双连接版本冲突；再用 Java 完成参数化查询、SQL NULL 读取与查询方法提取。"
date: 2026-10-28T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "MySQL", "SQL", "JDBC", "事务", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 8
chapter_title: "SQL 统计、事务与 JDBC 查询"
---

> 本篇按 **2026 年 10 月 28 日**归档，接续[上一篇 JOIN 入门](/posts/ops-ticket-20261026/)，把之后尚未整理的统计、分页、事务和 JDBC 练习合在一起，不把所有内容都算成同一天完成。学习路线见[学习栏目](/learning/)，当前实现与验收范围见[项目文档](/learning/project-docs/)。

之前我主要在 MySQL 客户端里写 SQL。这一段学习先补上关联查询的结果验证，再学习统计、分页和事务，最后让 Java 真正连上数据库，并通过一个方法查询不同状态的工单。

当前练习库里有两张工单：编号 1 的空调工单处于 `IN_PROGRESS`，处理人为 2；编号 3 的打印机工单处于 `OPEN`，处理人为 `NULL`。编号不连续是正常的，不能用记录条数猜编号。下面的结果对应这份练习数据，实际练习前仍要先查询确认，不要重复执行种子脚本来凑结果。

## 1 JOIN 的结果，继续用于筛选和统计

上篇已经讲过：普通 `SELECT ... JOIN ...` 产生查询结果，不会自动创建一张持久化的新表。这次我在工单、设备、报修人和处理人的关联查询中加入：

```sql
WHERE t.status = 'OPEN'
```

结果只剩打印机工单，处理人仍然是 `NULL`。因为处理人使用 `LEFT JOIN`，没有匹配处理人的工单不会因此丢失。

接着按状态统计：

```sql
SELECT status, COUNT(*) AS ticket_count
FROM ticket
GROUP BY status
ORDER BY status;
```

这份数据中 `IN_PROGRESS` 和 `OPEN` 各有 1 张。`GROUP BY` 把状态相同的结果行放到同一组，`COUNT(*)` 统计每组行数。

### COUNT(*) 和 COUNT(列) 的区别

```sql
SELECT COUNT(*) AS total_count,
       COUNT(assignee_id) AS assigned_count
FROM ticket;
```

我得到的结果是 `2` 和 `1`：

- `COUNT(*)` 统计结果行数，不要求每一列都有值。
- `COUNT(assignee_id)` 只统计这一列不是 SQL `NULL` 的行。
- 数值 `0`、空字符串和 `NULL` 不是同一个概念，前两者不会因为“看起来空”就被 `COUNT(列)` 忽略。

### LEFT JOIN 后为什么不能总用 COUNT(*) 数工单

```sql
SELECT d.id, d.name,
       COUNT(*) AS joined_row_count,
       COUNT(t.id) AS ticket_count
FROM device AS d
LEFT JOIN ticket AS t ON t.device_id = d.id
GROUP BY d.id, d.name
ORDER BY d.id;
```

| 设备 | 连接结果行数 COUNT(*) | 工单数 COUNT(t.id) |
| --- | ---: | ---: |
| 投影仪 | 1 | 0 |
| 空调 | 1 | 1 |
| 打印机 | 1 | 1 |

投影仪没有工单，但左连接仍保留它，对应的工单列补为 `NULL`，所以这一组仍有一行。此时 `COUNT(*)=1` 不等于“有一张工单”。工单主键 `t.id` 本身不为空，因此 `COUNT(t.id)` 能跳过这条补空行。

我当时理解成“每台设备都有工单时，这条查询才可以用 `COUNT(*)` 数工单”。在这个简单连接里，这样判断可以；但继续连接其他一对多表时，同一张工单可能被展开成多行，到时 `COUNT(t.id)` 也可能重复计数，需要先检查连接关系，按问题选择去重或预聚合。

## 2 WHERE、HAVING 与分页

要筛出有工单的设备，可以在刚才的分组查询后使用：

```sql
HAVING COUNT(t.id) > 0
```

结果是空调和打印机。改成 `HAVING COUNT(t.id) = 0` 后，只剩投影仪。

可以先按逻辑理解：`WHERE` 筛选参与分组的行，`HAVING` 筛选分组后的结果。例如“只统计待派单工单”与“只保留统计数大于 0 的设备”是不同层面的条件。尤其不要随手把右表筛选放到 `WHERE`，把左连接保留的空行又排除掉。

分页练习使用稳定的主键排序：

```sql
SELECT id, title, status
FROM ticket
ORDER BY id
LIMIT 1 OFFSET 0;
```

`LIMIT 1` 表示最多取 1 条；`OFFSET 0` 表示跳过 0 条。把 OFFSET 改成 1，就是跳过第一条再取一条。我的第一页是空调，第二页是打印机。

带筛选的列表和总数要采用一致条件：

```sql
SELECT id, title, status
FROM ticket
WHERE status = 'OPEN'
ORDER BY id
LIMIT 1 OFFSET 0;

SELECT COUNT(*) AS total_count
FROM ticket
WHERE status = 'OPEN';
```

待派单第一页是打印机，总数为 1；把 OFFSET 改为 1 后，当前页为空，总数仍是 1。**当前页行数不是符合条件的总数**。以后列表条件增加了，总数查询也要同步，不能一个筛选、另一个统计全表。

## 3 事务：修改、提交和回滚各是什么

我先认识了 InnoDB：它是 MySQL 的存储引擎，负责具体的数据存取，并支持事务等能力。这里的工单表使用 InnoDB；不能把这些回滚结论套到所有存储引擎上。

```sql
START TRANSACTION;

UPDATE ticket
SET title = '空调不制冷（事务练习）'
WHERE id = 1;

SELECT id, title FROM ticket WHERE id = 1;

ROLLBACK;
```

在同一连接里，UPDATE 后可以看到刚改的标题；`ROLLBACK` 后恢复到本次事务开始修改前的值。

随后我换成 `COMMIT` 实验：提交后标题保留，再执行 `ROLLBACK` 也不会把已经提交的那次修改撤销。回滚针对当前事务里尚未提交的修改，不是任意历史记录的“撤销按钮”。

### 如果既不 COMMIT，也不 ROLLBACK

显式事务可能一直保持打开，持有的锁可能让别的连接等待，自己的连接仍可以看到自己的未提交修改。其他连接能看到什么还受隔离级别和查询方式影响，不能认为“我能看到，别人也一定能看到”。连接断开时，尚未提交的事务修改会回滚；正常代码应该明确结束事务，不靠关闭窗口来代替处理。

### 第二条语句报错，为什么第一条修改还在

这次练习在一个事务内先改成正常标题，再把标题设为空字符串：

```sql
START TRANSACTION;

UPDATE ticket
SET title = '空调不制冷（等待回滚）'
WHERE id = 1;

-- 空标题违反表中的 CHECK，预期失败
UPDATE ticket SET title = '' WHERE id = 1;

-- 在同一个连接里观察第一条修改
SELECT id, title FROM ticket WHERE id = 1;

ROLLBACK;
```

本次 CHECK 错误使第二条语句失败，但没有自动撤销整个事务中前面成功的操作。第一条修改仍未提交，随后 `ROLLBACK` 才把它撤销。

因此我可以说“第二条本身没有成功写入，回滚时主要撤销的是第一条成功但未提交的修改”。不过不同错误的回滚范围可能不同，例如死锁可能导致整个事务被回滚，不能概括成“所有 SQL 错误都只影响一条语句”。

我还问了 `ROLLBACK` 后的 `0 rows affected`。它是这条事务控制命令的反馈，不是被恢复记录数；判断回滚是否生效，应在回滚后重新查询数据。

## 4 条件更新、影响行数和版本冲突

只允许待派单工单被派单，可以把条件直接放到 UPDATE：

```sql
UPDATE ticket
SET assignee_id = 2, status = 'IN_PROGRESS'
WHERE id = 3 AND status = 'OPEN';

SELECT ROW_COUNT() AS affected_rows;
```

在本次事务实验中，第一次影响 1 行；再执行相同语句时，状态已经不是 `OPEN`，影响 0 行。实验结束后回滚，恢复待派单状态。

`ROW_COUNT()` 要紧跟要观察的 UPDATE，并在同一连接里执行，否则观察到的可能已经是另一条语句。影响 0 行也不是 SQL 语法错误，可能只是条件没有匹配；具体要结合编号、状态和版本判断。

### 两个窗口都拿着 version=0，谁能修改成功

为避免后提交的人覆盖别人已经改过的内容，更新时同时检查旧版本，并将版本加一：

```sql
UPDATE ticket
SET title = '打印机卡纸（A修改）',
    version = version + 1
WHERE id = 3 AND version = 0;
```

我用两个连接编号不同的 MySQL 窗口练习。两边最初读到编号 3、`OPEN`、`version=0`。A 提交修改后，影响 1 行、版本变成 1；B 仍携带旧版本 0 更新，影响 0 行，最后保留 A 的标题。

如果 B 的 UPDATE 恰好在 A 未提交、仍持有锁时发出，它可能先等待，不一定立刻返回 0；这里记录的是 A 提交后旧版本更新未匹配的结果。

这验证了**这条带版本条件的 SQL**，不是说整个项目已经拥有完整的并发处理。当前控制台的文件仓库没有因此自动获得版本校验，HTTP 冲突响应和统一业务更新流程也还没实现。

## 5 从 MySQL 客户端走向 JDBC

API 可以先理解为一套约定好的调用入口。JDBC 是 Java 访问关系型数据库的一组标准接口；MySQL 驱动提供与 MySQL 通信的具体实现。

```text
我的 Java 代码
    → JDBC 接口
    → MySQL 驱动
    → MySQL 数据库
```

项目加入的依赖是：

```xml
<dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
    <version>26.10.0</version>
</dependency>
```

这期间 IDEA 对原驱动显示了依赖漏洞提示。它不是 XML 拼写错误，也不能仅因为 Maven 能下载就忽略。经备份、独立恢复和兼容性核验后，助手把本机 MySQL 从 8.0.44 升级到 8.4.13，并更新了驱动。版本适用范围见[Connector/J 26.10.0 官方说明](https://dev.mysql.com/doc/relnotes/connector-j/en/news-26-10-0.html)。

升级、旧项目兼容检查和临时 JDBC 验证属于助手完成的环境维护，不算我已独立掌握数据库迁移。备份占磁盘空间，停止的旧服务不会持续占用运行内存；这两件事也需要区分。这里不公开备份内容、账号密码或本机安装路径。

### 建立 Connection

我在测试源码目录中创建 `JdbcTicketQueryDemo`，使用环境变量提供密码：

```java
String password = System.getenv("OPS_TICKET_DB_PASSWORD");
if (password == null || password.isBlank()) {
    throw new IllegalStateException("请先配置数据库密码环境变量");
}
```

IDEA 的运行配置中设置这个变量，变量值只在本机填写，不写进 Java 文件。运行配置和环境变量不是同一个概念：`JdbcTicketQueryDemo` 与 `JdbcTicketQueryDemo (2)` 是两份运行配置，每份都可能有自己的环境变量。删掉多余运行配置，不会删除 Java 类。

```java
try (Connection connection =
         DriverManager.getConnection(url, username, password)) {
    System.out.println("数据库连接成功");
    System.out.println("当前数据库：" + connection.getCatalog());
}
```

URL 的格式是 `jdbc:mysql://127.0.0.1:3306/ops_ticket_dev`：本机、端口、数据库名。`getCatalog()` 核对当前数据库；配置了驱动依赖不等于已经连接成功，要以运行结果为准。

## 6 PreparedStatement：准备、绑定、执行是三步

我最初不理解下面这句：

```java
PreparedStatement statement = connection.prepareStatement(sql);
```

左边的 `PreparedStatement` 是类型，`statement` 是变量名。右边调用连接对象的方法，把 SQL 交给驱动，返回一个用于绑定参数和执行 SQL 的对象。虽然调用处没有写 `new`，仍然可以通过方法返回值得到对象引用。

```java
String sql = "SELECT id, title, status FROM ticket WHERE id = ?";

try (PreparedStatement statement = connection.prepareStatement(sql)) {
    statement.setLong(1, 3L);
    try (ResultSet resultSet = statement.executeQuery()) {
        // 读取查询结果
    }
}
```

三步分别是：

1. `prepareStatement(sql)`：准备操作对象，此时还没有执行这条查询。不能仅凭方法名就断言服务器已经完成了预编译，具体取决于驱动与配置。
2. `setLong(1, 3L)`：给第 **1** 个问号绑定 long 类型的 **3**。参数位置从 1 开始；问号外不要加引号，也不要自己拼接输入到 SQL。
3. `executeQuery()`：真正执行查询，返回结果集。返回后仍要读取结果，不会自动打印或变成 `Ticket`。

后来把条件换成 `WHERE status = ?`，参数类型也相应改为 `statement.setString(1, targetStatus)`。列名、排序方向等 SQL 结构不能随意用值参数的问号替代。

## 7 ResultSet、next() 和“当前这一行”

`ResultSet` 是查询结果集。刚拿到时，游标停在第一行前面：

```text
初始：第一行前面
next() → 第一行，返回 true
next() → 第二行（如果有），返回 true
next() → 没有下一行，返回 false
```

因此 `next()` 不仅判断有没有数据，还会移动当前位置。进入当前行后才能用 `getLong("id")`、`getString("title")` 读取列。

按主键最多查到一条时，可以用 `if (resultSet.next())`，没有结果就进入 else；按状态可能有多条时，使用 `while (resultSet.next())`。循环前不要再额外调用一次 next，否则容易跳过第一行。

```java
int count = 0;
while (resultSet.next()) {
    long id = resultSet.getLong("id");
    String title = resultSet.getString("title");
    String status = resultSet.getString("status");
    System.out.println(id + "：" + title + "，" + status);
    count++;
}
System.out.println("共找到 " + count + " 张工单");
```

没有结果时，循环一次都不执行，count 仍是 0。这里统计的是本次 Java 读到的行数，不是数据库所有记录数，也没有修改数据库。`status` 当前仍是 String，没有自动转换为 `TicketStatus` 枚举。

外面的 `try (ResultSet ...)` 会在离开代码块时自动关闭结果集、释放资源，不会删除数据库记录。`Connection` 和 `PreparedStatement` 也使用同样的资源管理方式。

## 8 SQL NULL 为什么不能直接当 long 读取

未派单工单的 `assignee_id` 是 SQL `NULL`。`getLong()` 返回基本类型 long，它不能容纳 Java null；遇到 SQL NULL 时会返回 0。

```java
long value = resultSet.getLong("assignee_id");

Long assigneeId = null;
if (!resultSet.wasNull()) {
    assigneeId = value;
}
```

| 数据库值 | getLong 返回 | wasNull() | 最终 Long |
| --- | ---: | --- | --- |
| 2 | 2 | false | 2 |
| NULL | 0 | true | null |
| 0（仅用于说明读取规则） | 0 | false | 0 |

`wasNull()` 判断的是**最后一次读取的列**，所以这里中间不要再读取 title 或其他列。Long 可以表达“没有处理人”，long 只能表达一个数值。把 SQL NULL 直接当 0 打印，会丢掉原来“尚未分配”的含义。

这次还遇到了：

```text
Unknown column 'statu' in 'field list'
```

连接成功不代表 SQL 正确。执行查询时，MySQL 找不到拼成 `statu` 的列；改回 `status` 后运行成功。排查时先看错误信息和自己代码的行号，不需要把一长串 classpath 当成故障原因。

## 9 提取查询方法，让 main 决定查什么

最后我把 SQL、参数绑定、遍历和计数提取为：

```java
private static void printTicketsByStatus(
        Connection connection, String targetStatus
) throws SQLException {
    String sql = """
            SELECT id, title, status, assignee_id
            FROM ticket
            WHERE status = ?
            ORDER BY id
            """;

    try (PreparedStatement statement = connection.prepareStatement(sql)) {
        statement.setString(1, targetStatus);
        try (ResultSet resultSet = statement.executeQuery()) {
            int count = 0;
            while (resultSet.next()) {
                long id = resultSet.getLong("id");
                String title = resultSet.getString("title");
                String status = resultSet.getString("status");
                long value = resultSet.getLong("assignee_id");
                Long assigneeId = null;
                if (!resultSet.wasNull()) {
                    assigneeId = value;
                }
                System.out.println("编号：" + id
                        + "，标题：" + title
                        + "，状态：" + status
                        + "，处理人编号：" + assigneeId);
                count++;
            }
            System.out.println("共找到 " + count + " 张工单");
        }
    }
}
```

`"""` 是 Java 文本块，可以分行写 SQL。这个项目使用 Java 21，支持这种语法。方法声明中的 `throws SQLException` 是异常声明，不是执行一次 throw；这里先让数据库异常向调用方传播，方便观察问题。

main 中建立一次连接，再依次调用：

```java
printTicketsByStatus(connection, "OPEN");
printTicketsByStatus(connection, "IN_PROGRESS");
```

资源归属很关键：main 创建并关闭 Connection；查询方法创建并关闭自己的 PreparedStatement 和 ResultSet。查询方法不能提前关闭借来的连接，否则第二次查询会失败。

这里使用 static 是为了让静态 main 直接调用这个练习方法，不表示所有方法都应该 static，也没有把连接做成全局共享字段。

## 10 这次验证了什么，接下来做什么

- 我按指导完成 JOIN 的 OPEN 筛选、统计和分页练习，并报告了对应结果：状态各 1、COUNT 为 2/1、无工单设备为投影仪、偏移后空页但总数仍为 1。
- 我执行了事务提交/回滚和双连接版本竞争，报告 A 影响 1 行、B 影响 0 行，最终保留 A 的标题和 version=1。SQL 文件与聊天反馈共同作为证据，不把文件存在当作每段都已独立验收。
- 我跟写并修改 JDBC Demo，完成连接、按编号/状态查询，修正列名拼写，保留处理人的 null，提取方法后报告运行成功。日结时助手读取了最新源码，确认同一连接依次查询两个状态、wasNull 位置和资源关闭边界正确；没有替我重写这段代码。
- 当天环境升级过程中，助手另外运行了 17 项已有 JUnit 和临时数据库检查。它们不等于我新增了 17 个 JDBC 测试；本次整理笔记不重复操作真实数据。

当前正式业务仍是控制台和文件仓库，JDBC 只在独立 Demo 中查询数据库；Java 更新事务、数据库仓库、Web、权限、AI 均未因此完成。`03_queries.sql` 已混入后续事务/版本实验，`06_transactions.sql` 也有事务练习，它们是学习记录，不是可以盲目整文件重跑的初始化脚本；当前 version 已为 1，旧的 `version=0` 实验不能直接期待仍影响 1 行。

**下次先学习 `executeUpdate()`，在单独的 JDBC 更新练习中关闭自动提交，带当前版本修改标题、检查影响行数，再显式回滚并确认原标题与版本恢复。** 先把 Java 中的事务边界讲清楚，再继续数据库业务接入，不直接跳到整套 Spring Boot 或 AI 工程。
