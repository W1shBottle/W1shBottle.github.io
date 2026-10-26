---
title: "设备运维工单开发 — 07 MySQL 三表关系、条件查询与 JOIN 入门"
description: "从 MySQL 建库、三表和约束实验，到 NULL、引号、LIKE、组合查询与 JOIN；用工单和用户对比左右连接，区分已验证结果与待验收练习。"
date: 2026-10-26T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "MySQL", "SQL", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 7
chapter_title: "MySQL 三表关系、条件查询与 JOIN 入门"
---

> 本篇按 **2026 年 10 月 26 日**归档，汇总[上一篇控制台交付](/posts/ops-ticket-20261021/)之后尚未整理的 MySQL 学习，不把中间的练习都算成今天完成。组合查询已有实际输出；JOIN 已讲解并写进查询文件，完整查询仍待我执行核对。阶段路线和任务入口分别见[学习栏目](/learning/)与[技能清单](/learning/checklists/)。

此前工单保存在 Properties 文件里。这一段学习开始使用 MySQL：先认识数据库、创建三张业务表，再练习增删改查与约束，最后把只显示编号的工单查询，扩展成能显示设备名和用户名的关联查询。

## 1 先分清：Java 程序、MySQL 和 SQL 文件

MySQL 是管理数据的数据库软件。运行中的服务端负责存储、查询和约束数据；`mysql` 命令行客户端负责连接服务端、发送 SQL、显示结果。IDEA 的 Terminal 只是我打开客户端的地方。

我的第一条核对语句是：

```sql
SELECT VERSION(), DATABASE();
```

实际显示版本 `8.0.44`，`DATABASE()` 最初是 `NULL`，表示这条连接还没有选择默认数据库。建好练习库后执行：

```sql
USE ops_ticket_dev;
SELECT DATABASE();
```

结果才变成 `ops_ticket_dev`。重新连接时，仍应确认当前库，不能只凭 IDEA 打开了项目来判断。

我还问过：“保存了 SQL 文件，为什么还要去控制台执行？”因为保存 `.sql` 只是在磁盘上保存文本；让已连接的客户端执行语句，数据库才会真正建表、插入或修改数据。`mysql>` 是提示符，不是 SQL 的一部分；通常以分号结束一条语句。

目前项目把练习分成五个文件：

| 文件 | 用途 |
| --- | --- |
| `sql/01_schema.sql` | `device`、`app_user`、`ticket` 建表语句 |
| `sql/02_seed.sql` | 演示设备、用户和工单 |
| `sql/03_queries.sql` | 条件查询与本次 JOIN 练习 |
| `sql/04_constraints.sql` | 故意触发唯一、外键、CHECK 失败 |
| `sql/05_updates.sql` | 停用设备、条件派单 |

这些是学习脚本，还不是可重复执行的自动迁移流程，尤其不能把预期报错的约束练习当成初始化步骤全部重跑。Java 控制台也尚未连接 MySQL，仍在使用原来的文件仓库。

## 2 三张表各存什么，编号怎么联系起来

| 表 | 保存的内容 | 这次认识的关键列 |
| --- | --- | --- |
| `device` | 设备 | `id`、唯一编码 `code`、名称、位置、`enabled` |
| `app_user` | 用户 | `id`、唯一用户名、密码哈希占位列、角色、`enabled` |
| `ticket` | 工单 | 标题、描述、设备编号、报修人编号、可空处理人编号、状态、版本和时间 |

`enabled` 表示是否启用。当前 MySQL 表使用 `BOOLEAN`，查询常显示 `1` 或 `0`，`DESC` 中对应 `tinyint(1)`；它不会自动形成“禁止停用设备报修”这样的完整业务判断。

我通过 `DESC device;` 看表结构。其中 `Field` 是列名，`Type` 是类型，`Null` 表示是否允许空值，`Key` 中的 `PRI`、`UNI` 分别标识主键、唯一索引，`Extra` 中的 `auto_increment` 表示自增。这里的 `DESC device` 是查看结构；`ORDER BY id DESC` 中的 `DESC` 则是按编号降序。

工单保存的是关联对象的编号：

```text
ticket.device_id   → device.id
ticket.reporter_id → app_user.id
ticket.assignee_id → app_user.id（未派单时为 NULL）
```

报修人和处理人都来自同一张用户表，只是扮演不同角色。工单自己的 `id` 是工单编号，不能拿它代替 `device_id` 去关联设备。

当前练习中，设备编号 1、2、3 分别是投影仪、空调、打印机；用户编号 1—4 分别是 `reporter_a`、`engineer_a`、`admin_a`、`reporter_b`。这些是虚构种子数据。表中的 `NOT_A_LOGIN_HASH` 只是占位文本，不是已经完成了登录功能。

## 3 从增删改查到数据库约束

`SELECT` 用来查询。例如：

```sql
SELECT * FROM device;

SELECT id, code, name, enabled
FROM device
WHERE code = 'PJ-001';
```

第一条查全部列；第二条只选指定列，并且只保留编码匹配的记录。这一阶段我还实际练过 `INSERT` 新增设备和用户、`UPDATE` 停用投影仪、`DELETE` 删除临时设备。删除后查询临时设备是 `Empty set`，原有三台设备仍在。

停用设备的语句保存在更新脚本中：

```sql
UPDATE device
SET enabled = FALSE
WHERE code = 'PJ-001';
```

`SET` 说明改什么，`WHERE` 限定改哪些记录。随后查启用设备，只剩空调和打印机；这是数据变化，需要用查询确认，不能把“没有报错”直接当成每一列都符合预期。

### 外键检查“有没有这个编号”

空调工单最初是设备编号 2、报修人编号 1、处理人 `NULL`、状态 `OPEN`。我尝试给工单填写不存在的设备编号 999，实际得到 **1452** 错误，提示 `fk_ticket_device`；查询后仍只有原来的工单。

这里的外键保证被引用的设备存在。处理人的外键同样只检查用户编号存在，不会顺便检查用户角色是不是 `ENGINEER`、账号是否启用。这些规则还需要业务代码验证。

### CHECK 检查一条记录内部是否自洽

这次成功派单使用了条件更新：

```sql
UPDATE ticket
SET assignee_id = 2,
    status = 'IN_PROGRESS'
WHERE id = 1
  AND status = 'OPEN';
```

我确认结果符合预期后，又尝试只把处理人清空：

```sql
-- 约束练习：在该工单已为 IN_PROGRESS 时预期失败
UPDATE ticket
SET assignee_id = NULL
WHERE id = 1;
```

这会违反当前的状态与处理人 CHECK：待派单 `OPEN` 对应无处理人，其余已定义状态要求有处理人。我的反馈是预期失败，数据仍保持派单后的状态。

CHECK 约束的是写入后的字段组合，不会替我校验“谁有权派单”，也不能仅凭它限制所有状态迁移。`version` 已经是数据库列，也不代表程序已经实现乐观锁。事务、完整状态流和权限都还在后面的任务中。

## 4 NULL、引号和 LIKE：几个容易混淆的细节

我曾把规则理解成“数字用 `=`，空值用 `IS`”。更准确地说：`=` 也可以比较普通字符串；检查空值用 `IS NULL` 或 `IS NOT NULL`。

```sql
WHERE id = 3
WHERE status = 'OPEN'
WHERE assignee_id IS NULL
```

上面是三个独立条件示例。SQL 的 `NULL` 表示缺失或未知，不是数字 `0`、空字符串 `''`，也不是字符串 `'NULL'`。`assignee_id = NULL` 不能筛出空处理人；这种比较的结果不是 TRUE，而 `WHERE` 只保留条件为 TRUE 的记录。

字符串在本项目里统一用单引号，例如 `'OPEN'`、`'打印机'`。双引号不是完全不能出现：MySQL 未启用 `ANSI_QUOTES` 时也能用双引号表示字符串；启用后双引号表示标识符。为避免依赖这个差异，我继续用单引号写字符串，必要时用反引号引用表名、列名。这个区别可对照 [MySQL 字符串文档](https://dev.mysql.com/doc/refman/8.0/en/string-literals.html)。

`LIKE` 配合 `%` 做模式匹配：

| 条件 | 含义 |
| --- | --- |
| `title LIKE '%打印机%'` | 标题包含“打印机” |
| `title LIKE '打印机%'` | 标题以“打印机”开头 |
| `title LIKE '%打印机'` | 标题以“打印机”结尾 |

`%` 匹配零个或多个字符。多个条件用 `AND` 连接，要求同时满足；修改查询条件只会改变查到什么，不会修改工单状态。

## 5 我实际完成的组合查询

这一条是我在聊天中提交了 SQL 和实际结果的练习：

```sql
SELECT id, title, assignee_id, status
FROM ticket
WHERE status = 'OPEN'
  AND assignee_id IS NULL
  AND title LIKE '%打印机%'
ORDER BY id;
```

实际返回一条：

| id | title | assignee_id | status |
| --- | --- | --- | --- |
| 3 | 打印机卡纸 | NULL | OPEN |

它同时要求待派单、没有处理人、标题含打印机。这里按实际结果记编号 **3**，不把“第二张工单”想当然写成编号 2；自增编号不保证连续，后续查询要以数据库实际值为准。

我接着问了两个问题。

**想全部查询时，SELECT 后面写什么？**

```sql
SELECT * FROM ticket;
```

`*` 表示全部列，省略 `WHERE` 表示不加行过滤。以后联表时 `*` 可能包含多张表的列，出现重名列；需要哪些业务字段，明确列出来更容易读。

**SELECT 后面的列顺序有影响吗？**

```sql
SELECT id, title FROM ticket ORDER BY id;
SELECT title, id FROM ticket ORDER BY id;
```

两条的记录相同，展示列的左右顺序不同。列顺序由 `SELECT` 列表决定；筛选哪些行由 `WHERE` 决定；行的排列由 `ORDER BY` 决定。没有 `ORDER BY` 时，不依赖返回顺序。

这次结果证明这条组合查询已写出并执行成功；不等于我已经独立验证了所有条件变体。解释、预测和排错仍可以穿插在下一个任务中，不必把整套练习重抄一遍。

## 6 JOIN：按关系配对，得到查询结果

进入关联查询时，我先问了 JOIN 是什么，又问“关联后会变成一张新表吗”。先看最小例子更容易理解：

```sql
SELECT ticket.title, device.name
FROM ticket
JOIN device ON ticket.device_id = device.id;
```

`FROM ticket` 选工单，`JOIN device` 把设备放进这次查询，`ON` 指定配对规则：工单中的设备编号等于设备表的主键。空调工单自己的编号是 1，设备编号是 2，因此匹配的是设备 2，而不是设备 1。

普通的这条 `SELECT ... JOIN` 返回一个结果集，不会创建第三张持久化表，也不会把原来两张表改掉。不要把结果“看起来像表格”，误解成数据库里新增了实体表。

下面是同一关系的别名写法，已经保存在查询文件中：

```sql
SELECT t.id, t.title, d.name AS device_name
FROM ticket AS t
JOIN device AS d ON t.device_id = d.id
ORDER BY t.id;
```

`t`、`d` 是这条语句内的表别名；`device_name` 是结果列的名字，都不会重命名原表或原列。如果要显示工单全部列再追加设备名，可以写 `SELECT t.*, d.name AS device_name`。

这里的普通 `JOIN` 按内连接理解：只保留满足 `ON` 的配对。后面的 LEFT/RIGHT JOIN 会额外保留指定一侧没有匹配的记录。语法与空值补齐规则可对照 [MySQL JOIN 文档](https://dev.mysql.com/doc/refman/8.0/en/join.html)。

## 7 LEFT JOIN 与 RIGHT JOIN，拿处理人来对比

以下都是**基于当前练习数据的预期结果，用于解释区别**，不是本次已经贴出运行结果的验收。

用于比较的工单：

| 工单 id | 标题 | assignee_id |
| --- | --- | --- |
| 1 | 空调不制冷 | 2 |
| 3 | 打印机卡纸 | NULL |

用于比较的用户：

| 用户 id | username |
| --- | --- |
| 1 | reporter_a |
| 2 | engineer_a |
| 3 | admin_a |
| 4 | reporter_b |

先统一选这些列：

```sql
SELECT t.id AS ticket_id, t.title,
       u.id AS user_id, u.username
FROM ticket AS t
LEFT JOIN app_user AS u ON t.assignee_id = u.id
ORDER BY t.id, u.id;
```

- 改成普通 `JOIN`：只配出工单 1 与工程师 2，打印机工单不会出现。
- 保持 `LEFT JOIN`：保留左边所有工单，打印机工单也显示，它的 `user_id`、`username` 补为 `NULL`。
- 改成 `RIGHT JOIN`：保留右边所有用户，得到下面的预期记录；为便于对照可按 `u.id, t.id` 排序。

| ticket_id | title | user_id | username |
| --- | --- | --- | --- |
| NULL | NULL | 1 | reporter_a |
| 1 | 空调不制冷 | 2 | engineer_a |
| NULL | NULL | 3 | admin_a |
| NULL | NULL | 4 | reporter_b |

`reporter_a` 虽然是空调工单的报修人，但本条 `ON` 匹配的是 **assignee_id**，不会因为他在别处有关联就配上。打印机工单的处理人是 `NULL`，没有匹配任何右侧用户；RIGHT JOIN 保留的是用户，不会额外保留这张未匹配的工单。

所以“右连接就是左连接反一下”要连表顺序一起理解：

```sql
FROM ticket AS t
RIGHT JOIN app_user AS u ON t.assignee_id = u.id

-- 同样的配对与保留规则，也可以写成：
FROM app_user AS u
LEFT JOIN ticket AS t ON t.assignee_id = u.id
```

这只是两个 `FROM/JOIN` 片段。使用相同的显式查询列时可得到对应结果；换了表顺序又用 `SELECT *`，列顺序也会跟着变化。哪个表的未匹配记录要留下，由 LEFT/RIGHT 决定；怎么匹配，由 ON 决定。一个用户如果处理多张工单，结果可以有多行，不是每个用户永远只有一行。

## 8 下一次从这条完整查询接着验收

完整查询已写入 `sql/03_queries.sql`：

```sql
SELECT t.id,
       t.title,
       d.name AS device_name,
       reporter.username AS reporter_name,
       assignee.username AS assignee_name,
       t.status
FROM ticket AS t
JOIN device AS d ON t.device_id = d.id
JOIN app_user AS reporter ON t.reporter_id = reporter.id
LEFT JOIN app_user AS assignee ON t.assignee_id = assignee.id
ORDER BY t.id;
```

同一个 `app_user` 用 `reporter`、`assignee` 两个别名分别查报修人与处理人，没有复制用户表。设备和报修人目前是必填外键，处理人允许空值，因此最后一处使用 LEFT JOIN，保留未派单工单。

按现有种子脚本和已反馈的数据，**预期**空调工单显示设备空调、报修人 `reporter_a`、处理人 `engineer_a`；打印机工单显示设备打印机、报修人 `reporter_b`、处理人 `NULL`。这份预期要由我实际执行核对，不能仅凭脚本存在就标成通过。

下次的小任务是：

1. 执行完整查询，核对两张工单及其设备、报修人、处理人。
2. 逐个解释 `ON` 的配对字段，以及最后为什么用 LEFT JOIN。
3. 自己加入只看 `OPEN` 的条件。`WHERE` 应在所有 JOIN/ON 后、`ORDER BY` 前；先预测哪行留下，再执行。

## 9 本次进度，以及 Java＋AI 路线

| 内容 | 当前证据与边界 |
| --- | --- |
| 连接、建库、三表、CRUD | 有我的操作反馈和实际查询结果 |
| 外键失败、派单、CHECK 失败 | 已反馈预期结果；不等于完整状态流或权限实现 |
| 打印机组合查询 | 我已提交 SQL，实际返回编号 3、OPEN、处理人 NULL |
| SELECT 列顺序、单双引号、JOIN 左右连接 | 已讲解；JOIN 示例和完整查询已保存，执行与独立变体待验收 |
| Java / 数据库接入 | 控制台仍读写文件；尚未接入 JDBC、MyBatis 或 Web |
| 正式 JUnit | 沿用 17 项，方案核对时已由助手构建通过；本次日结没有新增或重复运行 Java 测试 |

学习路线也在这一天调整为同一个项目的 **A 后端业务与工程基础 → B 一个有用的 AI 功能 → C 验证和改进**。先完成能独立运行的业务，再做有权限边界的工单摘要、分类建议等功能；AI 失败时人工业务仍要可用。Agent 根据实际需要再加，不用为了接入 AI 先堆满中间件。

这里只记录路线变化，不把规划算作实现。具体任务和验收继续维护在[阶段计划](/learning/schedule/)、[技能 To-do List](/learning/checklists/)和[项目文档](/learning/project-docs/)里；下一课仍先完成上面的 JOIN 验收。
