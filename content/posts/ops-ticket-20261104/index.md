---
title: "设备运维工单开发 — 12 断点追踪请求转换与统一异常响应"
description: "用断点区分请求体转换与业务校验，理解缺字段、setter、响应体与泛型，编写统一异常处理并验证 400/404 的状态和错误说明。"
date: 2026-11-04T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Spring Boot", "HTTP", "异常处理", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 12
chapter_title: "断点追踪请求转换与统一异常响应"
---

> 接续[上一篇 Spring 依赖注入与工单查询创建接口](/posts/ops-ticket-20261031/)，对应[学习栏目](/learning/)中的文件版 Web 实践。这次先验证重启恢复，再用断点观察请求体如何进入 Java 对象，最后为请求体转换错误和业务错误返回统一的错误说明。实现仍使用文件仓库；数据库业务、权限和 AI 尚未接入。

## 1 重启后，工单数据从哪里回来

我停止并重新启动 `OpsTicketApplication`，再次请求：

```http
GET http://localhost:8080/api/tickets/2
```

仍然查到了此前创建的编号 2。这补上了上一篇还没有单独确认的重启恢复实验。

当前配置使用 `data/tickets-app.properties`，这是相对于程序工作目录的路径。创建 `FileTicketRepository` 时，构造器读取文件，再把工单装入内部的内存仓库。后续查询调用 `memory.findById`，不会每发一次 GET 都重新读取文件。

这里的 **GET 是 HTTP 请求方法，表示查询或获取数据**；Java 中的 `getTitle()` 是读取字段的方法，两者不能只因为都有 get 就混为一谈。浏览器地址栏访问上面的地址时会发送 GET；创建工单使用的 POST 则通过 IDEA HTTP Client 发送。

## 2 用断点观察真实执行顺序

这次我在指导下追踪下面的流程：

```text
HTTP Client 发送 POST JSON
    → Spring MVC 读取请求体，Jackson 转换成 CreateTicketRequest
    → setTitle 把输入放进 DTO 字段
    → Controller 调用 getTitle 读取字段
    → TicketService.create 组织创建
    → Ticket 构造器校验标题
    → 校验成功才交给仓库保存
```

断点设置在可执行语句旁，例如 DTO 中的 `this.title = title;`、Controller 中的 `String title = request.getTitle();`。红点表示设置了断点，是否真的暂停还要看当前执行位置和 Debug 变量窗口。

我一度设置了下一个断点，却发现请求已经运行结束。**新增断点不会让过去的请求倒回去执行**；Resume Program 只是继续当前执行过程，直到遇到下一个有效断点或完成请求。成功 POST 每次都会新增工单，所以后续调试改用会被校验拒绝的空白标题请求，不靠反复创建来观察流程。

| 调试动作 | 用途 |
| --- | --- |
| Resume Program／继续运行 | 运行到下一个有效断点或请求结束 |
| Step Over／单步跳过 | 执行当前语句，通常不进入被调用方法；被调用方法里另有断点时仍可能暂停 |
| Step Into／单步进入 | 进入当前语句调用的方法 |
| Step Out／单步跳出 | 执行完当前方法，回到调用它的位置 |

我的 IDEA 使用自定义键位，界面提示 Step Into 是 F11，因此以后以动作名称和工具提示为准。不能照着另一套键位机械地按键。

在 `request.getTitle()` 那一行点单步进入，会进入 DTO 的 getter；只有执行位置来到 `ticketService.create(title)` 时，单步进入才会进入 Service。截图中 getter 的 `return title;` 也设了断点，它同样会影响暂停位置。

## 3 JSON 的 title 怎样进入 setTitle

正常请求的标题来自 JSON 中的值：

```http
POST http://localhost:8080/api/tickets
Content-Type: application/json

{
  "title": "打印机卡纸"
}
```

对于当前 DTO 的默认映射，可以把转换过程理解为下面的 Java 操作。这是解释用的等价示意，不需要另外写进 Controller：

```java
CreateTicketRequest request = new CreateTicketRequest();
request.setTitle("打印机卡纸");
```

setter 执行：

```java
public void setTitle(String title) {
    this.title = title;
}
```

右边的 `title` 是本次方法调用收到的参数，左边的 `this.title` 是当前 DTO 对象的字段。参数不是凭空出现的，是 JSON 转换过程把对应值传进来。

## 4 缺字段，和传入 null，是两回事

发送 `{}` 时，我观察到没有经过 `setTitle` 的断点。最初我把它理解成“没有 String，所以这个方法没有参数”。后来把原因修正为：**JSON 没提供 title 字段，因此解析器跳过这个属性的赋值，没有调用 setter。**

对象仍能创建，字段 `private String title;` 没有赋值时，默认值为 `null`。

| JSON | 当前默认映射下的含义 |
| --- | --- |
| `{}` | 没提供 title，不调用 setter，字段保持默认的 null |
| `{"title": null}` | 提供了字段，值是 null，可以调用 `setTitle(null)` |
| `{"title": "   "}` | 提供了字段，setter 收到空格字符串 |

第一种没有命中 setter 是本次断点观察结果；显式 `title: null` 的行为在这次课上按当前映射规则说明，没有另算一次独立运行验收。

`setTitle(String title)` 始终要求一个参数。`setTitle(null)` 是合法的 Java 调用；如果直接在 Java 代码中写 `setTitle()`，少了参数，会编译失败。**缺少 JSON 字段，不会变成一次少传参数的方法调用。**

## 5 从 getter 到 Service，再到标题校验

Controller 中先读输入：

```java
String title = request.getTitle();
Ticket created = ticketService.create(title);
```

`request.getTitle()` 返回 DTO 字段值，Controller 将这个值存入自己的局部变量 `title`，再作为参数传给 Service。同名不代表所有方法共用一个局部变量。

在 Controller 方法中，`this` 是 `TicketController` 对象；进入 DTO getter 后，`this` 是 `CreateTicketRequest` 对象。Debug 窗口中的调用栈显示 `create:80 → getTitle:13`，可以据此判断是谁调用了当前方法。

Service 的创建逻辑仍是：

```java
long maxId = 0;
for (Ticket ticket : repository.findAll()) {
    if (ticket.getId() > maxId) {
        maxId = ticket.getId();
    }
}
Ticket ticket = new Ticket(maxId + 1, title);
add(ticket);
return ticket;
```

先找最大编号，再尝试构造工单。**调用构造器不代表构造一定成功。** 标题全部是空格时，`Ticket.validateTitle` 会发现去空白后的结果为空：

```java
String trimmedTitle = title.trim();
if (trimmedTitle.isEmpty()) {
    throw new IllegalArgumentException("工单标题不能为空");
}
```

构造器抛出异常后，Service 后面的 `add(ticket)` 不会执行，流程返回 Controller 的 `catch`，再包装成状态为 400 的 `ResponseStatusException`。当前最大编号加一只是文件版的学习实现，尚未处理并发创建，也不是未来数据库生成主键的方案。

## 6 同样返回 400，失败位置可能不同

我又在请求中故意漏掉冒号：

```http
POST http://localhost:8080/api/tickets
Content-Type: application/json

{
  "title" "打印机卡纸"
}
```

这一次 Controller 的断点没有停，HTTP Client 返回了 400。原因是 `@RequestBody` 的参数转换必须先成功，Spring 才能调用 Controller 方法；语法错误让请求在准备参数时就失败。

| 场景 | 能否进入当前 Controller 方法 | 出错的位置 |
| --- | --- | --- |
| 标题是空格字符串 | 能 | 进入 Service，创建 Ticket 时触发标题规则 |
| `{}` 缺少 title | 能 | DTO 字段保留 null，随后由 Ticket 的 null 检查拒绝 |
| JSON 故意缺冒号 | 不能 | 请求体转换失败，参数尚未准备完成 |

空白标题与错误 JSON 的 400 有本次运行反馈；缺字段的 null 校验路径可从源码说明。本次收尾的三项统一响应验收另列在后面，不把所有推导都写成已独立实测。

Controller 方法内部的 `try-catch` 能处理执行到它里面时抛出的异常；请求体解析失败发生得更早，需要用 Spring 的异常处理机制接管。

## 7 先定义错误响应的数据

我在 `dto` 包编写了 `ErrorResponse`：

```java
package cn.wishbottle.opsticket.dto;

/**
 * 错误响应的数据：向客户端说明请求为什么失败。
 */
public class ErrorResponse {

    private final String message;

    public ErrorResponse(String message) {
        this.message = message;
    }

    // Spring 将响应对象转成 JSON 时，通过 getter 读取信息
    public String getMessage() {
        return message;
    }
}
```

这个类保存我们希望返回给客户端的错误说明。对象由 Java 代码通过构造器赋值，再通过 getter 提供给 JSON 转换，因此这次只需要构造器和 getter。

它和 `CreateTicketRequest` 的用途不同：前者承载服务器返回的错误内容，后者承载客户端提交的输入。

## 8 接上统一异常处理器

在 `exception` 包编写 `GlobalExceptionHandler`，位于启动类根包的子包中，可以被 Spring 扫描：

```java
package cn.wishbottle.opsticket.exception;

import cn.wishbottle.opsticket.dto.ErrorResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.http.ResponseEntity;
import org.springframework.web.server.ResponseStatusException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    // 请求体无法读取或转换时，由 Spring 调用这个方法
    @ExceptionHandler(HttpMessageNotReadableException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleUnreadableBody() {
        return new ErrorResponse("请求体缺失或格式不正确");
    }

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<ErrorResponse> handleStatusException(
            ResponseStatusException e
    ) {
        // 取出 Controller 放进异常里的错误说明
        String message = e.getReason();
        if (message == null) {
            message = "请求处理失败";
        }

        ErrorResponse body = new ErrorResponse(message);

        // 保留异常原有的状态码，并设置响应内容
        return ResponseEntity.status(e.getStatusCode()).body(body);
    }
}
```

- `@RestControllerAdvice`：让 Spring 识别处理类，并把处理方法的返回值写入响应体。
- `@ExceptionHandler(某种异常.class)`：指定处理哪一类异常；`.class` 提供类型信息，不会在这里创建异常对象。
- `handleUnreadableBody`：处理请求体无法读取或转换的情况，返回通用说明，状态固定为 400。这个类型也可能代表缺少请求体或数据格式不匹配，不能只把它理解成“少冒号”。
- `handleStatusException`：接住现有 Controller 抛出的 `ResponseStatusException`，保留它原有的状态码和错误说明。

这些处理方法由 Spring 调用，不用在 main 中自己调用。Controller 原有的异常包装流程仍在使用；本次没有把所有 Java 异常都笼统转成 400。

## 9 参数 e、getReason 和默认说明从哪里来

例如详情接口查不到工单时，现有 Controller 执行：

```java
if (ticket == null) {
    throw new ResponseStatusException(
            HttpStatus.NOT_FOUND,
            "工单不存在：" + ticketId
    );
}
```

当请求的编号是 999，异常对象记录着 404 和“工单不存在：999”。Spring 再把这个异常对象传给 `handleStatusException` 的参数 `e`。

`getReason()` 是 Spring 的 `ResponseStatusException` 提供的方法，不是我自己写的，也不是所有异常都有的方法。它读取创建异常时给出的 reason；`getStatusCode()` 读取 HTTP 状态。普通 `Exception` 提供 `getMessage()`，不能据此假设它也有 `getReason()`。

```java
String message = e.getReason();
if (message == null) {
    message = "请求处理失败";
}
```

这里判空的是**异常中的说明**，不是请求中的 title。如果创建状态异常时没提供说明，就使用默认文字。前面将编号写死为 999 只是代入示例，实际 Controller 仍用 `ticketId` 拼接，不需要另加一段重复的 throw。

## 10 响应体、ResponseEntity 和尖括号

这两行是我今天反复确认的地方：

```java
ErrorResponse body = new ErrorResponse(message);
return ResponseEntity.status(e.getStatusCode()).body(body);
```

第一行先创建 `ErrorResponse` 对象，构造器把 message 保存到字段，再用变量 `body` 引用它。

第二行组织整份 HTTP 响应。**ResponseEntity 管整份回复，响应体是回复里的具体内容。** 状态码、响应头、响应体共同组成响应，例如：

```http
HTTP/1.1 404
Content-Type: application/json

{
  "message": "工单不存在：999"
}
```

404 是状态码，空行后面的 JSON 是响应体。查询成功时的工单 JSON 也是响应体，响应体并不专指错误说明。

`ResponseEntity<ErrorResponse>` 中，前面的 ResponseEntity 是 Spring 提供的类，尖括号里的 ErrorResponse 是我编写的数据类。整个写法是一个类型，表示“响应体采用 ErrorResponse 的 HTTP 响应”。

我用数组对照理解：

```java
ErrorResponse[] errors;                    // 数组元素是 ErrorResponse
ResponseEntity<ErrorResponse> response;    // 响应体是 ErrorResponse
```

数组用 `类型[]` 指定元素类型，泛型用 `<类型>` 指定通用类中的类型参数。这里只类比“声明具体内容的类型”；当前响应体是一个错误说明对象，不是错误数组。类型信息帮助编译器检查是否匹配，不会自动创建错误对象。

链式调用可以拆开理解，下面是说明用写法，不需要重复加入程序：

```java
ErrorResponse body = new ErrorResponse(message);
ResponseEntity.BodyBuilder builder =
        ResponseEntity.status(e.getStatusCode());
ResponseEntity<ErrorResponse> response = builder.body(body);
return response;
```

`status(...)` 先设置状态，返回一个继续配置响应的构建器；`body(...)` 放入响应体并生成 ResponseEntity。**`.body(body)` 中，点号后的 body 是方法名，括号中的 body 是我定义的变量名。** 变量改叫 errorInfo 时就写 `.body(errorInfo)`。

此时返回的仍是 Java 对象。Spring 随后读取状态和响应体，把 ErrorResponse 通过 getter 转成 JSON，再发送给客户端。它不是在构造器里就变成了网络上的 JSON 文本。

## 11 今天实际验证了什么

写好处理器后，我重新启动应用，用 HTTP Client 逐条检查；三种响应的状态码和 message 都符合预期：

| 请求 | 状态码 | 响应体 message |
| --- | --- | --- |
| JSON 故意缺少冒号 | 400 | 请求体缺失或格式不正确 |
| 标题全是空格 | 400 | 工单标题不能为空 |
| GET /api/tickets/999 | 404 | 工单不存在：999 |

这三项以及重启后查询编号 2，来自我在本机的运行反馈；助手读取了最新源码，并在课堂用 JDK 21 完成离线 compile 检查。今天没有新增 Web 自动测试，现有 17 项 JUnit 没有作为今天的新测试重跑；HTTP Client 手动验收与 JUnit 是不同的验证方式。

我在 Services 的 HTTP Request 响应区查看状态码，Debug 窗口用于查看暂停位置和变量。请求暂停在断点时，客户端等待响应是正常现象；继续运行并执行完请求后才有最终结果。

## 12 当前边界与下次任务

当前只有两类异常接入了统一错误响应。路径参数类型错误、存储失败、其他内部错误，以及权限和状态冲突的处理仍要按实际业务补齐，不能因为处理类叫 Global 就认定所有错误已统一。

正式 Web 仍复用文件仓库，没有接入 MyBatis/MySQL 业务，也没有实现认证授权、完整状态流或 AI。本轮代码是在指导下完成，ResponseEntity、泛型和请求转换还需要用独立变体巩固。

下一次先独立请求 `GET /api/tickets/abc`：记录状态码、响应体和 Controller 是否被执行，再判断当前两类处理方法是否覆盖它，学习路径参数类型转换错误的专门处理。之后继续按[阶段计划](/learning/schedule/)推进数据库业务。

实现和验收现状见[项目文档](/learning/project-docs/)与[学习时间线](/learning/#progress)。

参考：[Spring RequestBody](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/requestbody.html)、[统一异常处理](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-exceptionhandler.html)、[Controller Advice](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-advice.html)、[ResponseEntity](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/responseentity.html)、[ResponseStatusException](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/server/ResponseStatusException.html)。
