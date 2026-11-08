---
title: "设备运维工单开发 — 14 多列对象映射与只读数据库分层"
description: "从 TicketSummary 多列映射和 assignee_id 转驼峰，到 Ticket.restore、Optional、Service 与只读 Repository，梳理数据库查询如何从临时 Mapper 调用走向分层结构。"
date: 2026-11-08T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Spring Boot", "MyBatis", "MySQL", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 14
chapter_title: "多列对象映射与只读数据库分层"
---

> 接续 [上一篇 MyBatis 接口映射与数据库查询接线](/posts/ops-ticket-20261107/)。上一篇只查询一列 `title`，今天把数据库查询推进到多列查询、`TicketSummary` DTO、领域对象 `Ticket` 转换，以及 Controller → Service → Repository → Mapper 的只读分层。正式 `/api/tickets` 仍使用文件仓库，数据库写入还没有形成可调用的完整接口。

## 1 今天补上的缺口

11 月 7 日已经验证：

```text
HTTP GET
→ DatabaseTicketController
→ TicketMapper
→ MyBatis
→ MySQL
→ String / JSON
```

但 Mapper 只返回一列：

```java
String findTitleById(@Param("id") long id);
```

这条链路只能证明数据库连接、参数绑定和单列结果映射成功，不能证明一个包含多个字段的对象也能正确映射。

今天的起点因此是：

```text
SELECT id, title, status, assignee_id
FROM ticket
WHERE id = ?
```

目标不是马上写数据库，而是先回答三个问题：

1. 多列结果怎样进入一个 Java 对象；
2. 这个对象是领域对象 `Ticket`，还是专门用于查询的 DTO；
3. 查询逻辑怎样从 Controller 中移到 Service 和 Repository。

## 2 TicketSummary 是查询 DTO

先新建查询数据对象：

```java
public class TicketSummary {

    private long id;
    private String title;
    private String status;
    private Long assigneeId;

    // getter / setter
}
```

它的职责只有两个：

```text
MyBatis：数据库列 → setter → TicketSummary
Jackson：TicketSummary → getter → JSON
```

它不负责标题校验，也不负责派单规则。

这里有两个类型选择：

- `id` 使用 `long`，因为主键非空；
- `assigneeId` 使用 `Long`，因为 `assignee_id` 可以为 `NULL`，未派单时必须能表示 `null`。

一开始我还不清楚 `setId`、`setTitle` 中的值从哪里来。后来把链路拆开：

```text
路径中的 id = 2
→ Controller 传入 Mapper
→ SQL 查询数据库
→ 数据库返回 id、title、status、assignee_id
→ MyBatis 调用 setId、setTitle、setStatus、setAssigneeId
→ Jackson 调用 getter 生成 JSON
```

Controller 只提供了查询条件 `id`；其它字段是 SQL 查询结果。

## 3 多列查询与列表映射

`TicketMapper` 先增加单行对象查询：

```java
@Select("""
        SELECT id, title, status, assignee_id
        FROM ticket
        WHERE id = #{id}
        """)
TicketSummary findSummaryById(@Param("id") long id);
```

再增加列表查询：

```java
@Select("""
        SELECT id, title, status, assignee_id
        FROM ticket
        ORDER BY id
        """)
List<TicketSummary> findAllSummaries();
```

返回值从：

```java
TicketSummary
```

变成：

```java
List<TicketSummary>
```

含义是：

```text
一行查询结果 → 一个 TicketSummary
多行查询结果 → List<TicketSummary>
```

我实际请求 `GET /api/db/tickets` 后得到 200，数据库里当时有编号 1 和 3，没有编号 2：

```json
[
  {
    "id": 1,
    "status": "IN_PROGRESS",
    "title": "空调不制冷（提交练习）"
  },
  {
    "id": 3,
    "status": "OPEN",
    "title": "打印机卡纸（JDBC 提交练习）"
  }
]
```

这同时验证了三件事：

- 多行记录能映射成多个对象；
- 编号不连续是正常现象，查不到 id=2 不等于接口出错；
- JSON 字段顺序和 Java 属性声明顺序不同，不影响按字段名映射。

`ORDER BY id` 不是装饰。没有排序时，数据库返回顺序可能不稳定，测试结果也更难比较。

## 4 从 assignee_id 到 assigneeId

数据库列名是：

```text
assignee_id
```

Java 属性名是：

```java
private Long assigneeId;
```

最开始可以通过 SQL 别名手工对齐：

```sql
assignee_id AS assigneeId
```

但这意味着每个查询都要重复写别名。

后来在 `application.properties` 中开启统一规则：

```properties
mybatis.configuration.map-underscore-to-camel-case=true
```

于是：

```text
assignee_id → assigneeId
device_id   → deviceId
created_at  → createdAt
updated_at  → updatedAt
```

SQL 可以保持数据库原本的列名：

```sql
SELECT id, title, status, assignee_id
FROM ticket
ORDER BY id
```

这里也分清了三种做法：

| 做法 | 适用场景 |
| --- | --- |
| `AS` 别名 | 偶尔一个特殊列名 |
| `map-underscore-to-camel-case` | 大量统一的下划线列名 |
| `@Results` / `resultMap` | 复杂、复用或无法按统一规则转换的映射 |

我确认加上 `assigneeId` 后，列表输出与预期一致，说明全局映射已经生效。`IN_PROGRESS` 的工单有处理人，`OPEN` 工单的 `assigneeId` 为 `null`。

## 5 TicketSummary 与领域对象 Ticket

`TicketSummary` 能返回 JSON，为什么不直接把它当工单使用？

因为 `Ticket` 不是数据袋子，它是领域对象：

```java
public class Ticket {
    private final long id;
    private String title;
    private TicketStatus status;
    private Long assigneeId;
}
```

它负责：

- 编号必须为正数；
- 标题去首尾空白后非空且不超过 50 个字符；
- 只有 `OPEN` 状态能派单；
- `OPEN` 不能有处理人；
- 非 `OPEN` 必须有有效处理人。

因此不能这样创建：

```java
Ticket ticket = new Ticket(summary.getId(), summary.getTitle());
```

这会把数据库中的 `IN_PROGRESS` 和 `assigneeId` 丢掉，错误地变成一张新的 `OPEN` 工单。

也不能让 MyBatis 随便通过无参构造器和 setter 填 `Ticket`，因为当前 `Ticket`：

- 没有无参构造器；
- `id` 是 `final`；
- 状态是枚举；
- 字段没有公开 setter；
- 构造和恢复都要经过业务校验。

正确的转换入口是 `Ticket.restore`。新增转换类：

```java
public final class TicketSummaryConverter {

    private TicketSummaryConverter() {
    }

    public static Ticket toTicket(TicketSummary summary) {
        if (summary == null) {
            return null;
        }

        TicketStatus status =
                TicketStatus.valueOf(summary.getStatus());

        return Ticket.restore(
                summary.getId(),
                summary.getTitle(),
                status,
                summary.getAssigneeId()
        );
    }
}
```

转换过程是：

```text
数据库字符串 "IN_PROGRESS"
→ TicketStatus.IN_PROGRESS
→ Ticket.restore 检查状态与处理人的组合
→ 得到合法 Ticket
```

这也回答了“为什么没有转换类时也能输出 JSON”：

```text
返回 TicketSummary → JSON
返回 Ticket       → JSON
```

如果两边 getter 暴露的字段相同，JSON 表面上可能完全一样。区别在 Java 对象的职责：

```text
TicketSummary：搬运查询数据
Ticket：承载业务状态与规则
```

## 6 从 Controller 直接调用 Mapper 到只读分层

完成对象转换后，临时 Controller 中出现了这些职责：

```text
接收 HTTP
调用 Mapper
判断 null
转换 TicketSummary
决定 404
```

这些逻辑都堆在 Controller 中，数据库和领域转换会与 HTTP 耦合。

因此先增加 `DatabaseTicketQueryService`：

```java
@Service
public class DatabaseTicketQueryService {

    private final TicketMapper ticketMapper;
    private final TicketQueryRepository ticketQueryRepository;

    public DatabaseTicketQueryService(
            TicketMapper ticketMapper,
            TicketQueryRepository ticketQueryRepository
    ) {
        this.ticketMapper = ticketMapper;
        this.ticketQueryRepository = ticketQueryRepository;
    }
}
```

当前是迁移中的过渡结构：

- 标题、摘要和摘要列表仍直接使用 Mapper；
- 领域对象和领域对象列表通过 Repository 查询。

查询调度逐步变成：

```text
Controller
→ DatabaseTicketQueryService
→ TicketQueryRepository
→ DatabaseTicketRepository
→ TicketMapper
→ MySQL
```

### 为什么增加 Repository 接口

只读接口是：

```java
public interface TicketQueryRepository {

    Optional<Ticket> findById(long id);

    List<Ticket> findAll();
}
```

实现类：

```java
@Repository
public class DatabaseTicketRepository
        implements TicketQueryRepository, TicketWriteRepository {
```

一个示例方法：

```java
@Override
public Optional<Ticket> findById(long id) {
    TicketSummary summary =
            ticketMapper.findSummaryById(id);

    if (summary == null) {
        return Optional.empty();
    }

    Ticket ticket =
            TicketSummaryConverter.toTicket(summary);

    return Optional.of(ticket);
}
```

Service 只依赖 `TicketQueryRepository`，不依赖具体的 `DatabaseTicketRepository`。以后即使换成缓存、文件或测试假仓库，Service 的查询代码也不用跟着改。

### Optional 表示什么

```java
Optional<Ticket>
```

表示“可能找到一张工单，也可能没有”。

```text
找到   → Optional.of(ticket)
没找到 → Optional.empty()
```

Service 再把：

```java
ticketQueryRepository.findById(id)
```

转换成当前 Controller 需要的：

```java
ticketQueryRepository.findById(id).orElse(null)
```

Controller 继续用 `null` 决定是否返回 HTTP 404。HTTP 状态码属于 Controller，不塞进 Repository。

## 7 Spring Bean 与 MyBatis 代理不是一回事

构造器注入并不是 Service 自己创建 Repository：

```java
public DatabaseTicketQueryService(
        TicketQueryRepository repository
) {
    this.repository = repository;
}
```

Spring 启动时扫描：

```java
@Repository
DatabaseTicketRepository
```

创建普通 Repository 对象，再把 MyBatis 创建的 `TicketMapper` 代理注入进去。创建 Service 时，Spring 又把这个 Repository 传给构造器。

两条依赖可以概括为：

```text
TicketMapper
→ MyBatis 创建动态代理
→ 调用方法时执行 SQL

DatabaseTicketRepository
→ Spring 创建普通 Bean
→ 内部持有 TicketMapper 代理
```

Spring 容器最终形成：

```text
Controller
→ DatabaseTicketQueryService
→ DatabaseTicketRepository
→ TicketMapper 代理
→ MySQL
```

接口的作用不是让运行时“少调用一次”，而是让 Service 只依赖查询契约。以后换实现时，改动集中在配置和新实现类中。

## 8 当前数据库只读接口

整理后的主要入口是：

| 请求 | 返回对象 | 说明 |
| --- | --- | --- |
| `GET /api/db/tickets/{id}/title` | `Map<String,String>` | 单列标题 |
| `GET /api/db/tickets/{id}` | `TicketSummary` | 单张工单摘要 |
| `GET /api/db/tickets` | `List<TicketSummary>` | 全部摘要 |
| `GET /api/db/tickets/{id}/domain` | `Ticket` | 单张领域对象 |
| `GET /api/db/domain/tickets` | `List<Ticket>` | 全部领域对象 |

路径中的 `db`、`domain`、`tickets` 都是我们自己定义的 URL 片段。它们本身不会连接数据库；真正执行 SQL 的是 Mapper。

理解路由时，关键不是 Java 方法名，而是注解：

```java
@GetMapping("/api/db/tickets/{id}")
```

Spring 用它与：

```text
GET /api/db/tickets/1
```

匹配，再把路径中的 `1` 转成：

```java
@PathVariable(name = "id") long id
```

400 和 404 也不同：

```text
/api/db/tickets/abc → 参数无法转成 long，未进入 Controller
/api/db/tickets/999 → 进入 Controller，SQL 无结果，返回 404
```

## 9 排错与调试

### .http 文件中的 ###

IDEA 的 `.http` 文件中，`###` 用来分隔请求。多个请求前不写分隔符时，后面的 `GET` 可能被当成上一个请求内容，语法高亮也会异常。

```http
### 查询领域对象
GET http://localhost:8080/api/db/tickets/1/domain
```

`###` 后面的说明文字可省略，但多个请求之间最好保留分隔符。

### 看调用链

在 IDEA Debug 中暂停后，查看 `Frames`（帧/调用栈）。从 Controller 的调用使用 `F7 Step Into`，可以依次进入：

```text
DatabaseTicketController.findDomain
DatabaseTicketQueryService.findDomainById
DatabaseTicketRepository.findById
```

`Frames` 最上面是当前方法，下面是调用者。

### 数据库没有 id=2

实际查询得到编号 1 和 3，没有 2。`ticket.id` 是自增主键，不代表编号连续。执行：

```sql
SELECT id, title, status
FROM ticket
ORDER BY id;
```

能够确认数据库当前的记录。对不存在的 id 返回 404 是正确的。

## 10 数据库写入的准备与边界

今天已经开始准备写入，但还没有完成可调用的 POST 闭环。

已经保存的写入组件包括：

```java
public interface TicketWriteRepository {
    Ticket create(String title, long deviceId, long reporterId);
}
```

Mapper 中加入：

```java
@Insert("""
        INSERT INTO ticket (
            title,
            device_id,
            reporter_id
        )
        VALUES (
            #{title},
            #{deviceId},
            #{reporterId}
        )
        """)
@Options(
        useGeneratedKeys = true,
        keyProperty = "id",
        keyColumn = "id"
)
int insertTicket(TicketInsert ticketInsert);
```

`DatabaseTicketRepository.create` 的逻辑是：

```text
组装 TicketInsert
→ 执行 INSERT
→ 检查影响行数
→ 从 TicketInsert.id 取回自增主键
→ 再按新 id 查询并恢复成 Ticket
```

这里还没有：

- `DatabaseTicketCommandService`；
- `CreateDatabaseTicketRequest`；
- POST `/api/db/tickets`；
- 外键错误、标题约束错误的 HTTP 转换；
- 写入后的真实运行结果和自动测试。

因此不能把“Mapper 和 Repository 已经有 INSERT 代码”写成“数据库创建功能已完成”。

## 11 本次验证范围

本次有学习者运行反馈的证据：

- `GET /api/db/tickets` 返回 200；
- 数据库中的编号 1 和 3 被映射为两个 JSON 对象；
- 加上 `assigneeId` 后输出符合预期。

本次通过源码核对确认：

- `TicketSummary` 增加 `Long assigneeId`；
- 开启下划线转驼峰；
- `TicketSummaryConverter` 使用 `Ticket.restore`；
- 增加 `TicketQueryRepository` 和 `DatabaseTicketRepository`；
- 增加单张/全部领域对象查询接口；
- 开始准备 `TicketInsert`、`@Insert`、`@Options` 和 `TicketWriteRepository`。

边界：

- 正式 `/api/tickets` 仍使用文件仓库；
- 没有新增或重跑 JUnit，正式测试仍按 17 个方法记录；
- 没有新增 Web 自动测试；
- 领域对象接口和完整只读分层主要完成代码核对，没有把未单独反馈的请求写成已运行；
- 数据库写入没有 POST 接口和运行结果。

## 12 下次接续

下次从数据库创建工单继续：

```text
POST /api/db/tickets
→ CreateDatabaseTicketRequest
→ DatabaseTicketCommandService
→ TicketWriteRepository
→ INSERT
→ 自增主键
→ 重新查询 Ticket
→ 201 JSON
```

然后补：

- 设备或用户外键不存在时返回什么；
- 标题违反数据库约束时返回什么；
- 哪些错误属于 400/409，哪些应保持 500；
- 是否需要在 Service 层加事务边界。

继续对照 [学习栏目](https://wishbottle.cn/learning/)、[项目设计](https://wishbottle.cn/learning/project-design/) 和 [运行验收](https://wishbottle.cn/learning/project-verification/) 阅读。