---
title: "设备运维工单开发 — 11 Spring 依赖注入与工单查询创建接口"
description: "把文件仓库和 Service 接到 HTTP，理解 Bean、DTO、RequestBody 与 JSON 转换，修正重复映射，用 HTTP Client 验证创建和非法标题。"
date: 2026-10-31T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Spring Boot", "HTTP", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 11
chapter_title: "Spring 依赖注入与工单查询创建接口"
---

> 本篇记录 **10 月 31 日至 11 月 1 日凌晨**的连续学习，统一归入 10 月 31 日。接续[上一篇 HTTP 与 Spring Boot 入门](/posts/ops-ticket-20261030/)，对应[学习栏目](/learning/)的 A1 阶段。这次把原有文件仓库和 Service 接到 HTTP 接口，完成真实工单查询与创建；数据仍存在文件里，尚未接入 MySQL 业务仓库。

## 1 从编号回显到真实查询

上一课的 `/api/tickets/{id}` 只把路径中的编号放进 Map 返回。我验证了：3 和 10 返回对应编号，abc 返回 400。这个结果说明路径参数可以转成 long，不代表编号对应的工单存在。

现在的目标是复用已有业务：Controller 接收编号，Service 调用仓库，仓库查询启动时从文件恢复到内存的数据。原来的控制台、领域规则、文件存档都继续保留。

```text
GET /api/tickets/1
        ↓
TicketController.findById(1)
        ↓
TicketService.findById(1)
        ↓
FileTicketRepository → 内部的 InMemoryTicketRepository
        ↓
真实 Ticket 对象 → JSON 响应
```

这里没有执行 JDBC 或 SQL。数据库练习中的编号、文件存档里的编号属于不同数据源，不能混在一起判断结果。

## 2 仓库、Service 和 Spring Bean 怎样连接

我忘了以前为什么要写这两行：

```java
TicketRepository repository = new FileTicketRepository(path);
TicketService service = new TicketService(repository);
```

第一行创建文件仓库，构造器读取存档并恢复内部数据；变量使用接口类型，实际对象是实现了接口的 FileTicketRepository。第二行创建业务服务，把刚才的仓库引用传进去。传引用不会复制仓库，也不会产生第二份 Map。

以前 ConsoleApp.main 手动组织这两步。现在启动的是 OpsTicketApplication，不会顺便执行 ConsoleApp.main，所以要给 Web 应用配置所需对象。

```java
@Configuration
public class TicketConfig {
    @Bean
    public TicketRepository ticketRepository() throws IOException {
        Path path = Path.of("data", "tickets-app.properties");
        return new FileTicketRepository(path);
    }

    @Bean
    public TicketService ticketService(TicketRepository repository) {
        return new TicketService(repository);
    }
}
```

- `@Configuration` 标明这是 Spring 配置类；它在启动类根包的子包里，能够被扫描。
- `@Bean` 告诉 Spring 调用方法，并管理返回的对象。被管理的对象叫 Bean。
- `ticketService` 方法的 repository 参数由 Spring 注入，是前面配置的仓库。
- 默认单例作用域是在当前容器中共享这个 Bean，不是每个 HTTP 请求都创建一套，也不是所有程序进程共用一个对象。
- `throws IOException` 声明创建仓库可能遇到读取异常；文件仓库内部只把缺少存档当作空仓库，其他错误会使启动失败。

相对路径以程序工作目录为起点，应在项目根目录启动。文件仓库只在创建时恢复存档，后续查询用内存；在程序运行时手动改文件，不会自动刷新到已有仓库对象。

Controller 再通过构造器接收 Service：

```java
private final TicketService ticketService;

public TicketController(TicketService ticketService) {
    this.ticketService = ticketService;
}
```

左边是对象字段，右边是参数。Spring 创建 Controller 时传入 Service。只有一个构造器时不必额外写 `@Autowired`。final 限制字段重新指向另一个对象，不代表对象内部的数据不能变化。

这就是构造器依赖注入：Controller 持有 Service，Service 持有仓库。拿到引用之后，还需要真正调用方法才会发生查询。

## 3 详情、列表与 404

详情方法由编号回显改成返回 Ticket：

```java
@GetMapping("/api/tickets/{id}")
public Ticket findById(@PathVariable(name = "id") long ticketId) {
    Ticket ticket = ticketService.findById(ticketId);
    if (ticket == null) {
        throw new ResponseStatusException(
                HttpStatus.NOT_FOUND, "工单不存在：" + ticketId);
    }
    return ticket;
}
```

Service 把仓库的空 Optional 转成 null，所以 Controller 必须处理未找到。课堂中助手实际请求编号 1 得到 200 和真实字段，请求 999 得到 404。

列表接口则返回 `List<Ticket>`，由框架转换成 JSON 数组：

```json
[
  {"id": 1, "title": "b", "assigneeId": 20, "status": "IN_PROGRESS"}
]
```

即使只有一张，外层也有 `[]`。没有符合条件的工单时，列表正常返回 `[]` 和 200；查询一个指定编号不存在时，才按当前契约返回 404。

## 4 路径、尾斜杠和重复映射

我发现 `/api/tickets` 与 `/api/tickets/` 的效果不同。课堂实际请求前者 200、后者 404：当前默认匹配不会自动忽略末尾斜杠。后来我显式配置两个路径：

```java
@GetMapping({"/api/tickets", "/api/tickets/"})
```

这只是让同一个方法匹配两种写法，不是新增一套业务。

两个 404 也要分清：尾斜杠未配置时，没有匹配到列表处理方法；`/api/tickets/999` 则已经进入详情方法，是查询不到对象后主动抛出的 404。

接关键词时我犯了一个错误：保留旧的无参 findAll，又新增带参数的 findAll，两者都是同样的 GET 路径。Java 允许参数不同的方法重载，但 Spring 不会仅凭 Java 参数不同就区分 HTTP 映射。检查源码后发现重复配置，当时服务端口也无法连接；删除旧方法后，实际请求恢复正常。

```text
http://localhost:8080/api/tickets?keyword=b
服务地址              路径        查询参数
```

接口是提供给客户端完成某项操作的入口，路径是 URL 的一部分。后面查询和创建可以都使用 `/api/tickets`：GET 表示查询，POST 表示提交创建。请求方法不同，与两段完全相同的 GET 映射冲突不是同一种情况。

## 5 可选关键词与异常转换

列表只保留这一个方法，复用原有 Service.findByKeyword：

```java
@GetMapping({"/api/tickets", "/api/tickets/"})
public List<Ticket> findAll(
        @RequestParam(name = "keyword", required = false) String keyword) {
    if (keyword == null) {
        return ticketService.findAll();
    }
    try {
        return ticketService.findByKeyword(keyword);
    } catch (IllegalArgumentException e) {
        throw new ResponseStatusException(
                HttpStatus.BAD_REQUEST, e.getMessage(), e);
    }
}
```

required=false 允许不传参数；不传时是 null，`?keyword=` 是空字符串。Service 先 trim，再拒绝空白关键词；无匹配结果属于正常查询。

| 请求 | 课堂助手实际结果 |
| --- | --- |
| `/api/tickets` | 200，全部工单 |
| `/api/tickets?keyword=b` | 200，匹配标题 b |
| `/api/tickets?keyword=xyz` | 200，空数组 |
| `/api/tickets?keyword=` | 400 |
| `/api/tickets?keyword=%20%20` | 400，编码后的两个空格 |

我又问了一次 e 是什么。它只是 catch 中的变量名，指向捕获的异常对象，不是关键字。`e.getMessage()` 取字符串说明；最后传入 e 是把原异常保存为 cause，保留排错线索。也可以把变量改名为 exception，不影响含义。错误响应不一定会把这段中文说明显示给客户端，当前先检查 HTTP 状态码，统一错误格式以后再做。

## 6 POST 请求和 DTO 为什么要单独写

创建请求长这样：

```http
POST http://localhost:8080/api/tickets
Content-Type: application/json

{
  "title": "打印机卡纸"
}
```

请求头与请求体之间有空行。用户只提交标题；编号、初始状态和处理人由后端决定。因此使用单独的 CreateTicketRequest 接收输入，而不是要求用户填写整个 Ticket。

```java
public class CreateTicketRequest {
    private String title;

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }
}
```

DTO 是 Data Transfer Object，数据传输对象。dto 是我为这类对象取的包名，不是 Java 关键字；放进这个包不会自动获得特殊功能。CreateTicketRequest 是自己写的类，不是 Spring 自带类型。

`CreateTicketRequest request` 与 `Ticket ticket` 的写法相同：前面是类型，后面是变量名。DTO 承载输入，Ticket 表示业务工单并维护规则。

## 7 setTitle 的参数到底来自哪里

我最容易混淆的是：getter 没有读取 HTTP 请求，它怎么拿到标题？

答案是先转换再调用业务方法。Controller 的参数写成：

```java
@RequestBody CreateTicketRequest request
```

Spring MVC 根据注解读取请求体，交给 JSON 转换组件准备 DTO。对于当前这个普通 JavaBean，可以把转换理解为以下示意动作：

```java
// 用来理解过程，不需要手动加入 Controller
CreateTicketRequest request = new CreateTicketRequest();
request.setTitle("打印机卡纸");
```

参数值来自 JSON 中 `"title"` 的值。当前 setter 写法按 JavaBean 属性命名约定匹配：setTitle 对应 title 属性，不是根据 setter 括号里的参数名字匹配。换成下面这样也一样：

```java
public void setTitle(String value) {
    this.title = value;
}
```

方法开始执行时，request 已准备好，所以 `request.getTitle()` 只是读对象字段。三个注解分别解决不同来源：PathVariable 取路径段，当前练习里的 RequestParam 取查询参数，RequestBody 取请求体并转换对象。RequestBody 不负责创建工单或保存文件。

## 8 返回的是 Ticket，为什么浏览器看到 JSON

当前创建方法：

```java
@PostMapping({"/api/tickets", "/api/tickets/"})
@ResponseStatus(HttpStatus.CREATED)
public Ticket create(@RequestBody CreateTicketRequest request) {
    String title = request.getTitle();
    try {
        Ticket created = ticketService.create(title);
        return created;
    } catch (IllegalArgumentException e) {
        throw new ResponseStatusException(
                HttpStatus.BAD_REQUEST, e.getMessage(), e);
    }
}
```

`return created` 的返回值仍是 Ticket 对象，不会把方法返回类型偷偷变成 String。因为类标了 RestController，Spring 把返回值作为响应体处理，在当前配置下交给 JSON 转换组件序列化。返回 String 时通常是文本，不应把 RestController 理解为“任何返回值都强制变 JSON”。

我问到“框架到底是谁”后，把职责重新拆开：

| 组件 | 当前作用 |
| --- | --- |
| Spring Boot | 自动配置并启动所需组件 |
| Tomcat | 接收 HTTP 请求、发送 HTTP 响应 |
| Spring MVC | 路由到 Controller，组织参数转换、方法调用和返回值处理 |
| Jackson | JSON 与 Java 对象之间的转换 |
| 我的 Controller / Service / 仓库 | 接收业务输入、校验并创建工单、保存文件 |

注解是给这些代码识别的说明，本身不是一段 JSON 解析算法。完整过程是：

```text
HTTP Client 发送 JSON → Tomcat 接收
    → Spring MVC 根据 POST 路径找到方法
    → @RequestBody 触发 Jackson 转换成 DTO
    → Controller 取标题 → Service 创建 Ticket → 文件仓库保存
    → Controller 返回 Ticket → 序列化为 JSON → HTTP 响应
```

正常返回用 201 Created；参数校验异常转成 400。当前创建还没有幂等控制，每次成功 POST 都会新增一张工单。

## 9 用 HTTP Client 验证成功和失败

项目根目录的 tickets.http 保存可执行请求，IDEA 左侧绿色三角可以发送指定的一条。浏览器地址栏通常发送 GET，不能靠直接打开地址验证这个 POST。

我的创建请求截图显示 HTTP/1.1 201，返回：

```json
{"id":2,"title":"打印机卡纸","assigneeId":null,"status":"OPEN"}
```

随后源码检查也确认文件存档 count=2，编号 2 的记录已写入。这证明创建与文件保存已经发生；它仍不是 MySQL INSERT。

HTTP Client 显示 Response file saved，是 IDEA 保存了响应记录；它与 `data/tickets-app.properties` 的业务存档不是同一个文件。

请求文件还追加了：

```http
### 查询新工单
GET http://localhost:8080/api/tickets/2

### 查询全部，核对数量
GET http://localhost:8080/api/tickets

### 空白标题，预期 400
POST http://localhost:8080/api/tickets
Content-Type: application/json

{"title":"   "}
```

我按“查询数量 → 提交空白标题 → 再查数量”的步骤检查，反馈没有问题：坏标题被拒绝、工单没有增加。这份记录是我的课堂反馈，助手日结没有再次发送写请求。

原因在 Service 的顺序：

```java
Ticket ticket = new Ticket(maxId + 1, title); // 校验失败就在这里抛异常
add(ticket);                                // 不再执行，不进入保存
return ticket;
```

停止应用、重新启动后 GET 编号 2 的恢复验证已经安排，请求也写好了，但本轮没有单独的重启结果反馈，保留为待确认。不能仅凭文件存在就记成重启验收通过。

## 10 注释、导包与 IDEA 面板

我发现旧代码容易忘，要求助手给项目补中文学习注释。此次注释覆盖当时的 36 个 Java 文件、6 份 SQL 和 pom.xml，解释用途、依赖关系、失败行为与测试目的。助手核对去除注释后的代码及配置未变化，数据和 Git 暂存区未改。后续新增 DTO 和接口属于之后的课堂修改，不能把它们混成“全程仅改注释”。

有用的注释应说明“为什么”“由谁调用”“数据来自哪里”，不用每行翻译语法。实现更新时也要更新注释：例如旧的“仅回显编号”不能留在已经查询真实工单的方法上。当前 Controller 类说明仍写“查询接口”，以后可改为“查询与创建接口”，不影响运行。

导包不必背完整路径。IDEA 中选中补全候选或在标红类型上 Alt+Enter 导入；多个同名类型要看来源，比如 List 选 java.util.List。pom.xml 添加依赖解决“项目有没有这个库”，import 解决“当前文件的简单类名指谁”。CreateTicketRequest 则是自己项目的类。

运行窗口中，Console 看日志，Beans 看 Spring 对象，Health 看已配置的健康检查，Mappings 看路由，Environment 看配置来源。显示 Actuator 未启用不表示业务接口坏了；目前没有添加 Actuator，不为看面板打断主线。

## 11 验收边界与下次任务

| 本轮内容 | 证据与边界 |
| --- | --- |
| 路径 3/10/abc | 我反馈回显与 400 符合预期，之后已换成真实查询 |
| 详情、列表与关键词 | 助手课堂实际 GET 验证 200、404、空列表、空关键词及空格 400 |
| 映射冲突 | 源码发现重复 GET，按提示删除后实际请求正常 |
| POST 创建 | 我的 201 截图与新增编号 2；存档字段另经读取核对 |
| 空白标题创建 | 我反馈失败状态与前后数量符合预期；不是新增 JUnit |
| 重启恢复 | 已安排，尚无本轮单独运行反馈 |
| 理解程度 | 多处经讲解、跟写和提示修正，仍需要亲自用断点追踪调用链 |

现有 17 项 JUnit 未新增，本次日结不重复运行数据库或创建工单。Web 已复用 Service 和文件仓库；MyBatis/MySQL 业务、权限、统一异常格式、并发和请求幂等、处理验收、Web 可执行包与 AI 都未完成。文件仓库先改内存再覆盖存档，失败没有事务回滚；当前本机学习版本不能按生产系统对外部署。

**下次先确认重启后编号 2 可查询，再用断点观察 setTitle → Controller → Service 的调用顺序。** 比较 `{}` 缺标题与语法错误 JSON，分清进入业务校验的 400 和在参数转换阶段就返回的 400；不重复抄同质断言，也不一次性生成后续系统。

继续对照[技能清单](/learning/checklists/)、[项目设计](/learning/project-design/)和[运行验收](/learning/project-verification/)阅读。

参考：[Spring Bean 配置](https://docs.spring.io/spring-framework/reference/core/beans/java/basic-concepts.html)、[RequestBody](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/requestbody.html)、[ResponseBody](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/responsebody.html)、[IDEA HTTP Client](https://www.jetbrains.com/help/idea/http-client-in-product-code-editor.html)。
