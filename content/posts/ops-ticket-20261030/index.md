---
title: "设备运维工单开发 — 10 HTTP、Maven 与第一个 Spring Boot 接口"
description: "从浏览器 Network 认识请求与响应，读懂 Maven/POM，启动 Spring Boot，返回文本和 JSON，再学习查询参数与路径变量。"
date: 2026-10-30T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "HTTP", "Maven", "Spring Boot", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 10
chapter_title: "HTTP、Maven 与第一个 Spring Boot 接口"
---

> 本篇按 **2026 年 10 月 30 日**归档，接续[上一篇 JDBC 更新事务](/posts/ops-ticket-20261029/)，对应[学习栏目](/learning/)的 A1 阶段。今天从“运行 main 操作数据库”走到“启动 Java Web 应用接收请求”。现在的 HTTP 接口仍是入门练习，正式控制台继续使用文件仓库，不能把编号回显当成真实工单查询。

## 1 HTTP、请求和响应到底是什么

我一开始不理解“后端接收请求”。用工单场景理解：以后在网页点击“查看编号 3 的工单”，浏览器需要向 Java 程序发送一条消息，表达自己想做什么。这条消息叫请求；Java 处理后返回的消息叫响应。

**HTTP 是双方组织、交换这些消息时遵循的通信规则。** 一次交互通常是客户端发出请求，服务器返回响应。浏览器可以充当客户端，正在运行的 Java Web 应用可以处理服务端的请求。

```text
浏览器发出 HTTP 请求
        ↓
Java 后端接收并处理请求
        ↓
返回 HTTP 响应
        ↓
浏览器读取、展示结果
```

HTTP 不会自动执行 SQL。要查询数据库，仍然需要后端代码根据请求调用相应业务和数据访问逻辑。

我还问了博客里的“服务器”指谁。当前博客由 GitHub Pages 托管，可能通过 CDN 缓存节点提供页面；访问博客没有经过我电脑上的工单 Java 程序，也没有查询我的 MySQL。后来访问 `localhost:8080`，才是在访问自己电脑上的 Web 应用。

## 2 在 Network 里观察真实响应

我先打开博客发现页，在开发者工具 Network 中看到了：

| 字段 | 当时看到的内容 | 含义 |
| --- | --- | --- |
| Request URL | `https://wishbottle.cn/discover/` | 请求的地址 |
| Request Method | `GET` | 请求获取资源 |
| Status Code | `304 Not Modified` | 可以继续使用浏览器已有的缓存内容 |

304 不是失败；在这次缓存校验中，响应不重新传送页面正文，浏览器复用已有内容。后来我勾选“停用缓存”，保持开发者工具打开，切到博客首页，在“响应”中看到了 `<!doctype html>`、`<html>`、`<head>` 和 `<title>WishBottle</title>`。

这说明返回的是 HTML 文本，浏览器会解析它，并加载样式等资源，最终呈现网页。截图证明我观察了 HTML 正文，但没有显示首页这次请求的状态码，不能补写成截图已经验证了 200。

响应可以分成状态、响应头和响应体。用 HTTP/1.1 的写法示意：

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 3,
  "title": "打印机卡纸",
  "status": "OPEN"
}
```

- `1.1` 是 HTTP 协议版本，不是 Java 或项目版本。
- `200` 是 HTTP 状态码，`OK` 是文字说明。
- `Content-Type` 是响应头，说明正文的类型。
- 空行下面的 JSON 是响应体。这里是格式示例，不是已完成的数据库查询结果。

我问了 `application/json` 中的 `application`。内容类型一般是“大类别/具体类型”：`text/html` 是 HTML，`image/png` 是 PNG，`application/json` 表示 JSON 格式的应用数据。`application` 不是某个 Java 变量或项目名称。

| 状态码 | 在当前学习中的理解 |
| --- | --- |
| 200 | 请求成功；工单业务状态仍可以是 OPEN 或 IN_PROGRESS |
| 304 | 缓存校验后可以复用已有内容，不重新传送正文 |
| 400 | 请求参数等不符合要求，例如路径文字不能转换成 long |
| 404 | 找不到请求对应的资源；具体原因要结合路由和业务判断 |
| 500 | 服务端发生未妥善处理的内部错误 |

HTTP 状态码与 JSON 中的 `status` 是两件事：成功查到一张 OPEN 工单，HTTP 仍然可以是 200。

## 3 API、JSON 和 Map 的区别

API 是程序对外提供功能的接口约定。在 HTTP 场景中，约定通常包括请求方法、地址、参数和返回结果。例如未来的工单查询接口可以是 `GET /api/tickets/3`。

路径里的 `/api` 只是常用命名，不是必须的关键字；它不会自动连接数据库。

JSON 是一种数据表示格式：

```json
{
  "id": 3,
  "title": "打印机卡纸",
  "assigneeId": 2,
  "status": "IN_PROGRESS"
}
```

字段名和字符串使用双引号，数字、布尔值和 null 不加引号；字段用逗号分隔，最后一项后面不加逗号。`2` 是数字，`"2"` 是字符串，`null` 表示没有具体值，`"null"` 则是四个字母组成的字符串。

这次练习要求把编号 3 的工单交给编号 2 的处理人。我最初把 `id` 改成了 2，却保留 `assigneeId: null`。经提示后区分清楚：**id 表示哪张工单，assigneeId 表示交给谁。** 修改示例 JSON 文本也不会自动修改数据库。

Map 和 JSON 都能表达键值关系，但不是同一个东西：

| Map | JSON |
| --- | --- |
| Java 程序内存中的数据结构 | 表示、传输数据的文本格式 |
| 能调用 put/get/remove 等方法 | 文本本身没有 Java 方法，要先解析 |
| 泛型限制键和值的类型 | 有对象、数组、字符串、数字、布尔值、null 等类型 |

```text
Java Map / 类对象 → 序列化 → JSON 文本
JSON 文本 → 反序列化 → 合适的 Java 对象
```

JSON 不只对应 Map，也可以对应适合的 Java 类对象。

## 4 Maven 与 POM：为什么一个配置文件能引入很多库

我添加 Spring Boot 配置后，又完整回顾了一次 Maven。Maven 是管理依赖并组织编译、测试、打包的工具；`pom.xml` 是它读取的项目配置文件。POM 全称 Project Object Model，使用 XML 格式。

| 工具 | 职责 |
| --- | --- |
| JDK | 提供 Java 编译器和运行环境等 |
| Maven | 解析依赖、组织构建 |
| IDEA | 编辑、调试代码，也能调用 Maven |
| Spring Boot | 帮助配置和启动 Java 应用 |

POM 不是从上往下执行的 Java 业务代码。我的文件主要由这些部分组成：

```xml
<project>
    <!-- POM 模型版本 -->
    <modelVersion>4.0.0</modelVersion>
    <!-- parent：继承的父 POM 配置 -->
    <!-- groupId / artifactId / version：当前项目坐标 -->
    <!-- properties：可复用的配置值 -->
    <!-- dependencies：项目使用的库 -->
    <!-- build / plugins：构建工具及配置 -->
</project>
```

自己的项目坐标是 `cn.wishbottle:ops-ticket:0.1.0-SNAPSHOT`：groupId 是分组，artifactId 是项目/模块名称，version 是项目版本。SNAPSHOT 表示开发中的快照。groupId 常采用反写域名的形式，但不会自动创建 Java 包。

这些版本各有各的含义：

| 配置值 | 谁的版本 |
| --- | --- |
| modelVersion 4.0.0 | POM 模型格式，不是 Maven 安装版本 |
| parent 4.1.2 | 本次采用的 Spring Boot 父项目版本 |
| 0.1.0-SNAPSHOT | 工单项目版本 |
| java.version 21 | 项目的 Java 版本设置 |
| mysql-connector-j 26.10.0 | MySQL Java 驱动版本，不是服务端版本 |

本次在项目坐标前加入：

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>4.1.2</version>
    <relativePath/>
</parent>
```

它继承 Spring Boot 的版本管理和构建默认值，不是 Java 类继承。空的 relativePath 表示不按默认相对路径寻找本地父 POM，通过仓库解析。父 POM 管理依赖版本，不等于自动引入全部功能，所以还需要声明 Web 依赖。

```xml
<properties>
    <java.version>21</java.version>
    <maven.compiler.release>21</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <junit-jupiter.version>5.14.4</junit-jupiter.version>
</properties>
```

属性可以通过 `${属性名}` 引用。`maven.compiler.release` 控制编译目标和可用标准 API 范围，但写 21 不会自动安装或切换 JDK；IDEA、Maven 实际使用的 JDK 也要正确。UTF-8 源码编码设置不等于所有终端和数据库编码都自动统一。

本次保留已有 JUnit 5.14.4，通过属性与父 POM 管理版本，删除 JUnit 依赖里重复的 version；MySQL 驱动继续显式使用 26.10.0。新增：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webmvc</artifactId>
</dependency>
```

Starter 是一组相关依赖的入口，会进一步引入 Spring MVC、内嵌 Tomcat 等组件。依赖还会依赖别的库，这叫传递依赖，所以下载数量可能大于自己写的 dependency 数量。已有版本管理时可以省略 version；普通未管理的依赖不能随便省略。

依赖通常缓存到本机 Maven 仓库，缺少时按配置访问远程仓库；不需要手动复制进 src。Java 的 `import` 只影响源码里的名称引用，不负责下载库。

## 5 scope、插件和构建命令

JUnit 使用 `scope=test`，意味着它主要用于测试编译和运行。省略 scope 时默认是 compile；runtime 则用于运行及测试运行，不用于主源码编译。

**dependency 是项目需要的库，plugin 是 Maven 构建时使用的工具。** 当前三个插件分工如下：

| 插件 | 当前版本 | 作用 |
| --- | --- | --- |
| maven-compiler-plugin | 3.13.0 | 编译 Java 源码 |
| maven-surefire-plugin | 3.5.5 | 组织执行单元测试 |
| maven-jar-plugin | 3.4.1 | 打包主程序，并记录入口 |

JAR 清单中的入口仍是 `cn.wishbottle.opsticket.ConsoleApp`。添加 Web 依赖不会自动替换入口，普通 JAR 插件也不会默认打入全部外部依赖。本次还没有添加 Spring Boot 打包插件，所以不能把原来的 java -jar 命令当作已经验证的 Web 启动方式。

Maven 约定 `src/main/java` 为主源码，`src/test/java` 为测试源码，resources 放资源，target 放构建结果。测试目录中的 main Demo 会被编译，但不会因此自动执行 main；JdbcTicketUpdateDemo 不会因为 mvn test 就自动修改数据库。

| 操作 | 实际含义 |
| --- | --- |
| IDEA Reload Maven Project | 重新解析 POM、依赖和项目配置，不等于启动服务或执行测试 |
| mvn compile | 编译主源码及相关前置步骤 |
| mvn test | 执行到测试阶段，包括前面的编译等步骤 |
| mvn package | 执行到打包阶段，通常包含编译和测试 |
| mvn verify | 执行到验证阶段，检查范围取决于配置 |
| mvn install | 将项目产物安装到本地 Maven 仓库供其他项目引用 |
| mvn clean | 清理构建输出，默认不删除源码、存档和 MySQL 数据 |

默认生命周期里，执行后面的阶段会经过前面的阶段；clean 属于另一套生命周期。`mvn clean package` 是先清理，再走到打包。deploy 通常指发布产物到远程 Maven 仓库，不是自动把网站部署上线。BUILD SUCCESS 表示本次命令成功，不等于所有业务正确或服务器已启动。

我反馈添加配置后测试通过。现有永久 JUnit 仍是之前的 17 项，本次没有新增 Web 自动测试；日结没有重跑它们，不能把 HTTP 临时请求算成新增 JUnit。

## 6 启动 Spring Boot：Tomcat 在哪里

在主源码根包中创建了 `OpsTicketApplication`：

```java
package cn.wishbottle.opsticket;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class OpsTicketApplication {
    public static void main(String[] args) {
        SpringApplication.run(OpsTicketApplication.class, args);
    }
}
```

`@SpringBootApplication` 是注解，启用配置、自动配置和组件扫描等能力，默认扫描它所在包及子包。`OpsTicketApplication.class` 是这个类的类型信息，不是文件路径，也不是手动 new 对象；args 是 main 接到的命令行参数。

以前的 Demo 执行完就结束；Web 应用启动后保持运行、等待请求。我提供的日志截图显示使用 Java 21.0.8、Spring Boot 4.1.2，Tomcat 在 8080 端口启动，应用启动成功。

Tomcat 是 Web 服务器，也是 Servlet 容器。当前先理解它负责接收 HTTP 请求和发送响应；Spring MVC 把请求匹配到 Controller 方法，Controller 执行我写的处理逻辑，Spring Boot 帮忙配置和启动这些组件。Servlet 的详细机制尚未展开。

```text
浏览器 → Tomcat → Spring MVC → Controller 方法
浏览器 ← HTTP 响应 ← 方法处理结果
```

随后访问 `http://localhost:8080/`，我反馈看到 404。这个阶段服务器已经运行，但没有处理首页的对应内容。要区分“服务器没有运行、连接失败”和“服务器返回 404”。

## 7 第一个 Controller 返回普通文本

在启动类的子包 `cn.wishbottle.opsticket.controller` 下创建 `HelloController`：

```java
@RestController
public class HelloController {
    @GetMapping("/api/hello")
    public String hello() {
        return "Hello, Ops Ticket!";
    }
}
```

`@RestController` 让 Spring 识别并管理这个请求处理组件，方法返回值会写入响应体。这里不用在 main 手动 new Controller。`@GetMapping` 将指定路径的 GET 请求对应到方法，路径取决于注解，不取决于方法名。

`return` 把结果交给框架；`System.out.println` 只打印到控制台，不能代替返回响应。保存后停止并重新运行 OpsTicketApplication，再访问 `/api/hello`，我反馈看到了问候文字。助手随后实际 GET 验证：200、`text/plain;charset=UTF-8`、正文 `Hello, Ops Ticket!`。

IDEA 中绿色豆子图标提示 Spring Bean，也就是交给 Spring 管理的对象；接口/地球图标与请求映射、导航或 HTTP Client 操作有关。黄色灯泡表示可用建议或快捷操作，不一定是错误。灰色 `new *` 通常是代码作者/版本控制内联提示，不是 Java 的 new 语句，具体以悬停说明为准。

## 8 从返回 String 到返回 Map，再到 JSON

接着把返回类型改成 `Map<String, String>`，用 LinkedHashMap 放入 message、project 两项，返回 result。助手实际请求后确认响应为 200、`application/json`，正文为：

```json
{"message":"Hello, Ops Ticket!","project":"ops-ticket"}
```

这里不是把内存中的 Map 直接搬到浏览器，而是框架通过 JSON 转换器将 Map 序列化。浏览器显示为一行或格式化的多行，不改变数据含义。

这个阶段返回的是示例问候信息，还没有创建、查询或修改工单。

## 9 RequestParam：让网址里的值进入 Java 方法

最后的 HelloController 源码如下：

```java
package cn.wishbottle.opsticket.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import java.util.LinkedHashMap;
import java.util.Map;

@RestController
public class HelloController {
    @GetMapping("/api/hello")
    public Map<String, String> hello(
            @RequestParam(name = "name", defaultValue = "访客") String name
    ) {
        Map<String, String> result = new LinkedHashMap<>();
        result.put("message", "你好，" + name);
        result.put("project", "ops-ticket");
        return result;
    }
}
```

请求 `/api/hello?name=小明` 时，`/api/hello` 是路径，问号开始查询参数，name 是参数名，小明是值。Spring 取出这个值并传入方法，可以理解成调用 hello("小明")。没有参数或值为空时使用默认值“访客”；空字符串与只有空格的字符串并非同一种情况，当前没有 trim/非空白业务校验。

我特别问了 `name = "name"` 为什么有两个 name：

| 写法 | 身份 |
| --- | --- |
| 左边的 name | 注解提供的属性名，意思是指定请求参数名称 |
| 右边的 "name" | 我填写的字符串，表示去请求里找哪个参数 |
| 后面的 String name | 接收值的 Java 方法参数 |

所以也可以写 `@RequestParam(name = "nickname") String userName`，此时请求用 `?nickname=小明`，方法中使用 userName。注解中的等号是在设置注解属性，不是给方法变量赋值。

我反馈带 name 与不带 name 都正常。助手核对源码无误，但课堂最后一次请求本机 8080 时连接被拒绝，因此不能把最新带参数版本写成助手也已复跑通过；前面的普通文本和无参数固定 JSON 有实际请求证据。

## 10 PathVariable：路径里的编号

接下来讲了另一种传参方式：

| 地址 | 参数来源 | 注解 |
| --- | --- | --- |
| /api/hello?name=小明 | 查询参数 | @RequestParam |
| /api/tickets/3 | 路径中的一段 | @PathVariable |

日结时读取源码，TicketController 已经写成下面这样：

```java
package cn.wishbottle.opsticket.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import java.util.LinkedHashMap;
import java.util.Map;

@RestController
public class TicketController {
    @GetMapping("/api/tickets/{id}")
    public Map<String, Long> readTicketId(
            @PathVariable(name = "id") long ticketId
    ) {
        Map<String, Long> result = new LinkedHashMap<>();
        result.put("id", ticketId);
        return result;
    }
}
```

`{id}` 捕获一段路径，`@PathVariable(name="id")` 指定取它的值，再转换成 long 传给 ticketId。注解中的名字对应占位符；Java 参数名可以不同。Map 泛型使用 Long 而不是 long，put 时会自动装箱。

当前只是回显参数：访问 `/api/tickets/3` 预期得到 `{"id":3}`，改成 10 预期得到 10；传 abc 不能转换成 long，默认预期返回 400，方法体不会执行。**这些是待验证的预期，不是今天已经反馈通过的三个场景。**

该方法没有检查工单是否存在，也没校验编号必须大于零。数字 999 或负数不能仅凭能转换为 long 就当成合法业务；即使返回 200，也不能声称查到了数据库工单。当前没有 Service/Repository/Mapper 查询调用，后面要逐步补真实查询和错误契约。

## 11 今日证据与下次接续

| 内容 | 今天的证据与边界 |
| --- | --- |
| HTTP 观察 | 我提供发现页 GET/304 和首页 HTML 响应截图，理解请求/响应及缓存 |
| Maven 配置 | 已加入 Boot 父 POM/Web Starter，保留 Java21、JUnit5.14.4与驱动26.10.0；我反馈测试通过 |
| Web 启动 | 我提供启动日志并反馈首页404，启动类源码已核对 |
| 文本与固定 JSON | 我反馈文本成功；助手实际 GET 验证两个阶段均为200，内容类型分别为text/plain和application/json |
| 查询参数 | 我反馈带 name、不带 name 正常；源码正确，助手最后连接被拒绝，未复跑最新版本 |
| 路径参数 | TicketController 源码已写；3、10、abc 的运行结果仍待反馈 |
| 测试与持久化 | 现有17项JUnit未新增，日结不重跑Java或数据库；没有Web自动测试、数据库业务接口、权限或AI功能 |

下一次先启动 OpsTicketApplication，验证 `/api/tickets/3`、`/api/tickets/10` 和 `/api/tickets/abc`，报告响应体与状态码，解释为什么数字回显成功不等于工单存在。之后再让这个编号用于真实查询，逐步连接业务和持久层，不重复新建已存在的 Controller。

项目结构与运行方式见[项目文档](/learning/project-docs/)，后续技能状态见[清单](/learning/checklists/)。本次是经过讲解与提示完成的跟练，不能据此认为已经能独立设计整个 Web 后端。

参考：[Maven POM](https://maven.apache.org/guides/introduction/introduction-to-the-pom.html)、[构建生命周期](https://maven.apache.org/guides/introduction/introduction-to-the-lifecycle.html)、[Spring Boot 入门](https://docs.spring.io/spring-boot/tutorial/first-application/index.html)、[响应体转换](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/responsebody.html)、[请求参数](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/requestparam.html)、[路径映射](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-requestmapping.html)。版本按本次源码和课堂核对记录，官方文档后续可能更新。
