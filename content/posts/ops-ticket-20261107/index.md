---
title: "设备运维工单开发 — 13 MyBatis 接口映射与数据库查询接线"
description: "从 @Mapper、@Select、@Param 与 #{} 到代理对象和 HTTP 查询链路，接通第一条真实 MySQL 查询，并用 200/404/400 验证边界。"
date: 2026-11-07T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Spring Boot", "MyBatis", "MySQL", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 13
chapter_title: "MyBatis 接口映射与数据库查询接线"
---

> 接续[上一篇 断点追踪请求转换与统一异常响应](/posts/ops-ticket-20261104/)，对应[学习栏目](/learning/)中的文件版 Web 实践。今天第一次让 Spring Boot 的 HTTP 查询真正经过 MyBatis 访问 MySQL，并用 200、404、400 三种结果确认调用链和错误边界。正式工单业务仍使用文件仓库；创建、完整对象映射、权限和 Agent 尚未接入。

## 1 今天要补上的缺口

前面已经完成：

```text
HTTP Client
  → Spring MVC Controller
  → TicketService
  → FileTicketRepository
  → Properties 文件
```

这条链证明 Web、依赖注入和业务服务已经接上，但数据来源仍然是文件。

SQL 和独立 JDBC Demo 也做过，可是两者还没有进入 Web 请求。今天要验证一条新的最小链路：

```text
HTTP GET
  → DatabaseTicketController
  → TicketMapper
  → MyBatis
  → MySQL
  → JSON 响应
```

这个阶段只查询一列 `title`，先确认“HTTP 请求真的能触发数据库查询”，不一次加入完整对象、写入、事务和权限。

## 2 MyBatis 在 Spring Boot 中负责什么

这一课需要分清三个角色：

| 角色 | 负责什么 |
| --- | --- |
| Spring Boot | 启动 Web 服务、读取配置、创建对象、注入依赖 |
| MyBatis | 把 Mapper 方法调用转换成 SQL，并把结果转换成 Java 值 |
| MySQL 驱动 | 根据 JDBC URL、账号和密码建立数据库连接 |

`pom.xml` 中使用 MyBatis Spring Boot Starter，把 MyBatis 和 Spring 的生命周期接在一起。`application.properties` 提供数据源地址：

```properties
spring.datasource.url=jdbc:mysql://127.0.0.1:3306/ops_ticket_dev
spring.datasource.username=root
spring.datasource.password=${OPS_TICKET_DB_PASSWORD}
```

密码通过 IDEA 运行配置中的环境变量提供，不写进配置文件。依赖存在只代表项目有相应库；启动应用并发起请求后，才真正验证了数据源可用。

## 3 一个只有声明、没有方法体的 Mapper

今天的核心接口是：

```java
@Mapper
public interface TicketMapper {

    @Select("SELECT title FROM ticket WHERE id = #{id}")
    String findTitleById(@Param("id") long id);
}
```

拆开看：

- `@Mapper`：告诉 MyBatis-Spring 扫描这个接口；
- `@Select(...)`：给方法配置要执行的 SQL；
- `String`：返回值类型；
- `findTitleById`：方法名；
- `@Param("id") long id`：给参数命名并限定为长整数；
- `#{id}`：SQL 参数占位符；
- 方法最后是分号，没有 `{ ... }` 方法体。

Java 方法声明的基本顺序是：

```text
返回类型 方法名(参数列表)
```

所以代码必须先写 `String`，再写 `findTitleById`。注解写在方法上方，换行只是可读性，不是额外语法。

这个接口不能直接 `new`，因为接口没有实现。MyBatis-Spring 在启动时扫描 `@Mapper`，为接口注册一个代理对象。真正调用方法时，代理对象拦截调用，再根据 `@Select` 执行 SQL。

## 4 `@Param`、`#{}` 和预编译参数

SQL 写的是：

```sql
SELECT title FROM ticket WHERE id = #{id}
```

这里的 `#{id}` 不是直接把 Java 字符串拼进 SQL。MyBatis 会把它转换成 JDBC 预编译参数：

```sql
SELECT title FROM ticket WHERE id = ?
```

再绑定调用时传入的值：

```java
preparedStatement.setLong(1, id);
```

所以：

```java
@Param("id")
```

和：

```sql
#{id}
```

两边的名字需要对应。它们建立一个明确的“方法参数 → SQL 占位符”关系。

这里使用 `#{}`，而不是 `${}`。`#{}` 走预编译参数绑定，适合普通输入；`${}` 更接近直接文本替换，不应该拿来接收普通用户输入。

## 5 为什么没有 TicketMapperImpl

我一开始把 `@Mapper` 理解成“注解直接创建实现类”。更准确的过程是：

```text
@Mapper 标记接口
  → MyBatis-Spring 扫描
  → MapperFactoryBean 注册 Mapper
  → SqlSession.getMapper(...)
  → MyBatis 生成代理对象
  → Spring 把代理对象注入 Controller
```

代理对象实现了 `TicketMapper` 接口，所以可以被赋给这个类型。它一般会在运行时显示成类似 `jdk.proxy2.$Proxy...` 的名字，不是项目里某个能搜到的 Java 文件。

代理对象本身不手写 SQL，它拦截方法调用；MyBatis 读取方法对应的 SQL 配置，执行查询并转换结果。

因此，“接口没有方法体却能执行 SQL”不是 Java 自动提供了业务实现，而是 MyBatis 在运行时提供了代理实现。

## 6 临时 Controller 怎样接收请求

当前只读入口是：

```java
@GetMapping("/api/db/tickets/{id}/title")
public Map<String, String> findTitle(
        @PathVariable(name = "id") long id
) {
    String title = ticketMapper.findTitleById(id);

    if (title == null) {
        throw new ResponseStatusException(
                HttpStatus.NOT_FOUND,
                "数据库工单不存在：" + id
        );
    }

    Map<String, String> result = new LinkedHashMap<>();
    result.put("title", title);
    return result;
}
```

执行顺序是：

```text
GET /api/db/tickets/1/title
  → Spring 把路径中的 "1" 转成 long
  → 调用 findTitle(1)
  → 调用 ticketMapper.findTitleById(1)
  → 代理对象执行 SQL
  → MySQL 返回 title
  → Controller 组装 Map
  → Jackson 把 Map 转换成 JSON
```

查询到结果时，响应类似：

```json
{
  "title": "数据库中的工单标题"
}
```

`Map` 是 Java 对象，JSON 是 HTTP 响应文本。这里不是 MyBatis 直接把 Map 变成 JSON，而是 Spring MVC 使用 Jackson 完成最后一步序列化。

## 7 三种请求结果分别说明什么

| 请求 | 实际路径 | 预期结果 | 说明 |
| --- | --- | --- | --- |
| 存在的工单 | `/api/db/tickets/1/title` | 200 + JSON | Spring、MyBatis、MySQL 和 JSON 转换全部成功 |
| 合法但不存在的编号 | `/api/db/tickets/999/title` | 404 | 请求进入 Controller，SQL 执行了，但没有对应记录 |
| 非数字编号 | `/api/db/tickets/abc/title` | 400 | 参数转 `long` 失败，Controller 没有进入，SQL 没有执行 |

`999` 和 `abc` 虽然都是失败，但失败位置不同：

```text
999：业务数据不存在
abc：HTTP 路径参数转换失败
```

`abc` 的 400 由 `MethodArgumentTypeMismatchException` 统一处理。`999` 的 404 来自 Controller 主动抛出的 `ResponseStatusException`。这说明“都是错误响应”不代表属于同一种错误。

## 8 实际验证结果

我按顺序请求了三个地址并观察断点和 HTTP Client：

- `/api/db/tickets/1/title` 返回 200，正文中能看到数据库里的标题；
- `/api/db/tickets/999/title` 进入 Controller，Mapper 返回 `null`，随后返回 404；
- `/api/db/tickets/abc/title` 没有进入 Controller，参数转换阶段返回 400。

控制台结果和预期一致。这次验证来自我的课堂运行反馈；日结没有再次发送请求或查询数据库。

这一步证明：

- MyBatis Starter 已进入运行时；
- `OPS_TICKET_DB_PASSWORD` 等数据源配置有效；
- `@Mapper` 注册的代理对象能被构造器注入；
- `@Select` 的 SQL 真正访问了 MySQL；
- 单列结果能映射成 `String`；
- 路径参数错误和数据库无记录可以返回不同状态。

## 9 当前边界和容易误判的地方

今天完成的是**只读单列查询**，不是完整数据库业务。

| 已有 | 尚缺 |
| --- | --- |
| 通过编号查询标题 | 查询完整工单对象 |
| 临时 Controller 直接调用 Mapper | Controller → Service → Repository/Mapper 的正式分层 |
| 只读 SQL | 数据库创建、更新、状态流和事务 |
| 单列 `String` 映射 | 多列对象映射、字段别名和枚举 |
| 手动 HTTP 验证 | Web 自动化测试和正式数据库集成测试 |

因此不能把今天写成“数据库 Web 业务已经完成”。正式 `/api/tickets` 仍走 `TicketService` 和文件仓库，数据库查询只在临时 `/api/db/tickets/{id}/title` 入口中使用。

直接由 Controller 调用 Mapper 只适合验证链路。最终仍要保持：

```text
Controller → Service → Repository/Mapper → 数据库
```

## 10 下次从单列走向对象映射

现在 Mapper 返回：

```java
String findTitleById(...);
```

下一步要查询多列：

```sql
SELECT id, title, status
FROM ticket
WHERE id = ?
```

但 `Ticket` 领域对象有 `final id`、专用构造器和业务校验，不适合直接让 MyBatis 通过默认无参构造器加 setter 创建。因此先建立查询专用 DTO，例如 `TicketSummary`，包含：

```java
private long id;
private String title;
private String status;
```

再让 Mapper 返回：

```java
TicketSummary findSummaryById(@Param("id") long id);
```

先验证多列结果能映射成对象并返回 JSON，之后再学习：

- 数据库列名和 Java 属性名不一致时怎么处理；
- `@Results`、`resultMap` 和构造器映射；
- 查询结果怎样转换成领域 `Ticket`；
- 数据库仓库怎样接入 Service；
- 创建后怎样取得数据库自增主键。

## 11 本次验收

| 项目 | 结果 |
| --- | --- |
| 数据库查询链路 | 我的课堂请求返回 200 和标题 JSON |
| 数据库无记录 | 进入 Controller，返回 404 |
| 非数字路径参数 | 未进入 Controller，返回 400 |
| MyBatis 代理与注解 | 经讲解、提问和重新表述后理解 |
| 正式 JUnit | 仍为 17 项，本次没有新增或重跑 |
| 数据库写入 | 未实现 |
| Ticket 完整对象映射 | 未实现 |
| Service/数据库仓库接入 | 未实现 |

下次先从 `TicketSummary` 和 `findSummaryById` 接续。继续对照[技能清单](/learning/checklists/)、[项目设计](/learning/project-design/)和[运行验收](/learning/project-verification/)阅读。

参考：[MyBatis Mapper Annotations](https://mybatis.org/mybatis-3/java-api.html)、[MyBatis Spring Boot Starter](https://mybatis.org/spring-boot-starter/mybatis-spring-boot-autoconfigure/)、[Spring Boot DataSource Configuration](https://docs.spring.io/spring-boot/reference/data/sql.html)。
