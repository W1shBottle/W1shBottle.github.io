---
title: "设备运维工单开发 — 04 测试入门与基础补全"
description: "补完坏存档和空列表测试，整理 main/test/data，接触 Maven 与 8 个 JUnit 测试，再回到前两周补齐数组、标题校验、Set 去重、Map 计数和服务恢复。"
date: 2026-10-16T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Maven", "JUnit", "测试", "集合", "文件读写", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 4
chapter_title: "测试入门与基础补全"
---

> 本篇统一记录 **2026 年 10 月 16 日开始、延续到 10 月 17 日凌晨**的学习，归档日期记为 **10 月 16 日**。这是“设备运维工单开发”系列第 4 篇，承接[多张工单存取与 Demo 自测](/posts/ops-ticket-20261014/)。课程路线见[学习栏目](/learning/)，当前实现和运行方式见[项目文档](/learning/project-docs/)。

这次先补完坏存档和空列表测试，再整理代码目录、接触 Maven 和 JUnit。随后我重新核对了原计划：Maven 原本安排在第三周，而前两周还有基础练习和恢复流程没有验收。因此后半段转回查漏补缺，补了数组、标题校验、static、Set 去重和 Map 计数，最后把文件读回的工单加入服务。

这篇记录的是实际学习过程：有按提示编写的代码，也有我独立实现的方法、根据反馈修正的错误，以及助手代跑的临时检查。当前永久保留的 JUnit 测试是 **8 个**；后面提到的其他验收数量，不与这 8 个混算。

## 1 坏存档测试：抛异常以后，还能拿到前半份结果吗

上次 `loadAll` 已能读回两张工单，但缺字段测试还没有完成。这次使用正常存档的副本 `data/tickets-invalid.properties`，删除第二张工单的 `ticket.1.title` 整行，保留第一张记录。

这里要区分“缺字段”和“值为空”：

```properties
# 有这个键，只是值为空
ticket.1.title=
```

上面表示空标题；彻底删除这一项，才会使 `getProperty("ticket.1.title")` 返回 `null`，进入缺字段检查。

我一开始以为，第一张已经加入 `result`，即使第二张抛异常，调用方也能得到第一张。实际执行顺序是：

```text
恢复第一张 → 加入方法内部的 result
读取第二张 → 发现缺标题 → 抛出异常
return result 没有执行
调用方进入匹配的 catch
```

方法内部暂时有一张工单，不等于调用方已经收到了返回值。当前 `result` 是方法内部创建的列表，只有整个循环成功后才返回；抛异常时，这次调用没有正常返回列表。

### 怎样证明“应该失败”的情况真的失败

`TicketLoadFailureDemo` 的关键结构如下：

```java
try {
    store.loadAll(path);
    throw new AssertionError("缺少标题的存档应该被拒绝，但读取正常返回了");
} catch (IllegalArgumentException e) {
    if (!"存档缺少必要字段".equals(e.getMessage())) {
        throw new AssertionError("异常原因不符合预期：" + e.getMessage(), e);
    }
    System.out.println("测试通过：缺少标题的存档被正确拒绝");
} catch (IOException e) {
    throw new AssertionError("测试失败：文件未能正常读取", e);
}
```

这个测试有三种结果：

| 实际行为 | 测试如何判断 |
| --- | --- |
| 抛出预期的 `IllegalArgumentException`，消息也正确 | 通过，说明坏内容被拒绝 |
| `loadAll` 正常返回 | 主动抛出 `AssertionError`，测试失败 |
| 找不到文件，或发生其他 I/O 问题 | 测试失败；没有读到文件不能算验证了坏内容 |

我问过：“自己抛出的 `AssertionError` 被哪个 catch 接住？”这里的两个 catch 都不会接住它。`AssertionError` 属于 `Error`，不是 `IllegalArgumentException`，也不是 `IOException`；它会继续向外传递，交给运行环境报告失败。

`throw` 不是无条件关闭整个程序。它中断当前正常路径，并寻找匹配的异常处理；如果最终没有被处理，运行环境才会报告未捕获的异常或错误。

我运行了坏文件测试，也按要求用正常内容检查过“本应报错却正常返回”的失败分支，最后恢复了对应的坏文件路径。正常读取 Demo 的故意错误预期也已改回 `1001L`。

## 2 空列表、空文件和文件不存在，是三件事

接着完成 `TicketEmptyDemo`：保存一个空列表，再读回来，要求结果非 null 且没有元素。

```java
List<Ticket> emptyTickets = new ArrayList<>();
Path path = Paths.get("data", "tickets-empty.properties");

store.save(emptyTickets, path);
List<Ticket> loaded = store.loadAll(path);

if (loaded == null || !loaded.isEmpty()) {
    throw new AssertionError("应该读回非 null 的空集合");
}
```

空列表保存后仍有有效的存档结构，主要内容是：

```properties
count=0
```

读取时创建空 `ArrayList`，因为 `count` 为 0，循环不执行，最后返回这个列表。`Properties.store` 还可能写入注释，所以它也不一定只占一行。

| 情况 | 当前行为 |
| --- | --- |
| 合法存档，`count=0` | 返回空列表 |
| 零字节文件，没有 `count` | 抛出“存档缺少工单数量” |
| 路径指向的文件不存在 | 文件 API 抛出 I/O 异常 |
| 方法返回 `null` | 不符合空列表测试的预期 |

本次完成了空列表存取，尚未完成“首次启动没有文件时，应用以空服务开始”的流程。不能因为能读空列表，就把不存在的文件也算处理好了。

## 3 把业务代码、练习和存档分开

这一轮把文件按职责整理为：

```text
项目根目录/
├─ pom.xml
├─ src/
│  ├─ main/java/       # Ticket、TicketService、TicketFileStore 等
│  └─ test/java/       # Demo、基础练习、JUnit 测试
├─ data/              # 手动演示使用的 Properties 存档
├─ docs/              # 需求、设计与验收说明
└─ README.md
```

业务代码放在 `src/main/java`，Demo 和测试放在 `src/test/java`。把 Demo 放进测试目录只是分类；有 `main` 的 Demo 仍需主动运行，不会仅因为所在目录叫 test 就自动变成 JUnit 测试。

存档路径也相应改为：

```java
Paths.get("data", "tickets.properties")
```

这是相对路径，实际位置取决于运行时的工作目录。当前 Demo 约定从项目根目录运行，必要时用 `path.toAbsolutePath()` 检查。移动文件后，只改资源管理器里的位置，而不改代码路径或工作目录，仍然可能读错文件。

目录整理过程中，IDEA 曾只显示少量根目录文件，运行配置也失效。后来核对并修复了模块内容根、源码根和测试源码根，关闭后重新打开项目，恢复正常识别。这个过程提醒我：IDEA 的目录展示还受项目配置影响，不能只凭项目树异常就断定源码丢失。

IDEA 常见的蓝色源码目录、绿色测试目录、排除目录背景，与 Git 的文件名颜色含义不同。`.idea` 和 `.iml` 是 IDE 配置，`out`、Maven 后来的 `target` 是构建输出；这些不是新写的业务功能。当前目录已整理，但业务类尚未迁入具名包。

## 4 Maven 负责什么，pom.xml 又是什么

看到 “Load Maven Project” 提示后，我开始把项目按 Maven 项目加载。Maven 帮助统一依赖、编译和测试等构建步骤；`pom.xml` 描述这个项目及其构建配置。

这次接触到的几项配置：

| 配置 | 含义 |
| --- | --- |
| `groupId`、`artifactId`、`version` | 项目的标识和版本；三者也用于标识依赖 |
| `dependencies` | 项目需要使用哪些外部库 |
| `scope` 为 `test` | 这个依赖用于测试代码，不作为业务运行所需依赖 |
| `build/plugins` | 指定执行编译、测试等构建工作的插件 |
| `maven.compiler.release` | 指定 Java 编译的目标版本及可用标准 API 范围 |
| `project.build.sourceEncoding` | 指定源码编码，本项目为 UTF-8 |

当前配置中的具体版本如下。这些是本项目当时实际使用的版本，不是要求所有项目都照搬：

```xml
<properties>
    <maven.compiler.release>21</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
</properties>

<dependencies>
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.14.4</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

编译使用 `maven-compiler-plugin:3.13.0`，运行测试使用 `maven-surefire-plugin:3.5.5`。JUnit 是测试库，Surefire 是 Maven 中负责运行测试的插件，两个角色不同。

加载过程中遇到过编译插件 “not found” 的提示，处理后 Maven 构建和测试已运行通过。插件下载或解析问题与业务方法写错不是同一种问题，不能把这类提示都当成 Java 语法错误。

### JDK 版本不等于 Maven 版本

JDK 提供 Java 编译和运行工具；Maven 本身也有自己的版本，并需要 Java 来运行。IDEA 的项目 SDK、Maven 使用的 Java，以及终端中的 `java`，可能没有自动指向同一套 JDK。

本次验证使用 JDK 21 和 IDEA 内置的 Maven 3.9.9。配置 `release=21` 不会自动安装 JDK 21，也不会自动修改终端的默认 Java。这个差异仍要在后续统一环境时继续处理。

在已经配置好 JDK 与 Maven 命令的环境中，常见命令是：

```text
mvn compile    编译业务代码
mvn test       编译所需代码并运行测试
mvn package    继续到打包阶段
```

本次实际完成了测试运行，不把它写成已经验收了可直接分发的可执行 JAR。Maven 的完整生命周期、具名包和仓储接口仍留在后续计划中。

## 5 第一个 JUnit 测试：准备、执行、验证

以前在 Demo 里手写 `if`，不符合预期就抛 `AssertionError`。JUnit 把测试组织成带 `@Test` 的方法，并提供断言和统一的结果报告。

第一个测试检查改名是否真的改变了工单：

```java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class TicketTest {
    @Test
    void renameShouldUpdateTitle() {
        // 准备
        Ticket ticket = new Ticket(1001L, "投影仪无信号");

        // 执行
        ticket.rename("打印机卡纸");

        // 验证
        assertEquals("打印机卡纸", ticket.getTitle());
    }
}
```

这里不再需要自己写 `main`：测试运行器找到 `@Test` 方法并调用。业务程序的入口和测试方法的执行方式不同；以前的 Demo 仍可保留，用来观察执行过程。

`assertEquals(expected, actual)` 中，前一个参数是预期值，后一个是实际结果。预期和实际写反，不一定改变是否通过，却会让失败报告难读。

更关键的是，实际值必须来自被测试对象。曾经在标题边界测试里只比较准备好的字符串，这样不能证明 `rename` 生效；修正后比较的是 `ticket.getTitle()`。

我还故意注释掉 `ticket.rename(...)`，确认测试由通过变为失败，再恢复代码重新运行。这个小动作验证了测试确实依赖被测行为，不是无论实现怎样都能通过。

## 6 assertThrows：把异常本身也作为检查对象

修改为非法标题时，我不仅检查抛异常，还检查异常消息和旧标题是否保留：

```java
Ticket ticket = new Ticket(1001L, "投影仪无信号");

IllegalArgumentException exception = assertThrows(
        IllegalArgumentException.class,
        () -> ticket.rename(null)
);

assertEquals("工单标题不能为null", exception.getMessage());
assertEquals("投影仪无信号", ticket.getTitle());
```

`IllegalArgumentException.class` 表示期望的异常类型。`() -> ticket.rename(null)` 把“稍后执行这次调用”的动作交给 JUnit；JUnit 执行它并检查结果。

- 抛出符合要求的异常：返回捕获到的异常对象，还能继续检查消息。
- 没有抛异常，或抛出不符合要求的异常：测试失败。
- 抛异常之后旧标题仍应保持不变，所以还要读取 `ticket.getTitle()`。

这里复习了“先校验，再赋值”。如果先把非法值写入字段，再发现不合法，虽然报错，原对象也可能已经被破坏。

`TicketTest` 最终保留了 6 个测试：

| 测试场景 | 检查内容 |
| --- | --- |
| 正常改名 | 对象中的标题变为新标题 |
| 传入 `null` | 抛预期异常、消息正确、旧标题不变 |
| 50 个字符 | 正常接受并写入对象 |
| 51 个字符 | 拒绝、消息正确、旧标题不变 |
| 两端空格包围 50 个字符 | 先 trim，再按处理后的长度校验 |
| 纯空格标题 | 拒绝、消息正确、旧标题不变 |

这 6 个都是当前源码里的 JUnit 测试。构造器、所有派单规则和文件错误分支并没有因此自动获得完整的 JUnit 覆盖。

## 7 文件测试与 @TempDir：同名文件不代表同一个文件

接着在 `TicketFileStoreTest` 中写文件存取测试：

```java
@TempDir
Path tempDir;

@Test
void saveAndLoadShouldPreserveEmptyList() throws IOException {
    TicketFileStore store = new TicketFileStore();
    List<Ticket> emptyTickets = new ArrayList<>();
    Path path = tempDir.resolve("tickets-empty.properties");

    store.save(emptyTickets, path);
    List<Ticket> loaded = store.loadAll(path);

    assertNotNull(loaded);
    assertTrue(loaded.isEmpty());
}
```

**`tickets-empty.properties` 在这里是准备在临时目录中新建的文件名，只是碰巧与 `data` 里的文件同名。这段测试没有读取 `data/tickets-empty.properties`。**

要把这几步分别理解：

1. `@TempDir` 让 JUnit 提供临时目录，并负责其测试生命周期中的清理。
2. `tempDir.resolve("tickets-empty.properties")` 组合出子文件路径，**只得到 Path，不创建文件**。
3. `store.save(emptyTickets, path)` 才把空列表写入这个路径，创建测试文件。
4. `store.loadAll(path)` 读取刚才保存的同一个临时文件。

可以把位置想象成：

```text
项目的 data/tickets-empty.properties      手动 Demo 的存档
JUnit 临时目录/tickets-empty.properties   本次测试新建的文件
```

文件名一样，父目录不同，实际文件就不同。这样测试可以自己准备输入，不依赖我之前是否运行过 Demo，也不会因为测试正常执行而覆盖 `data` 里的存档。

测试方法声明 `throws IOException`，表示本次文件操作出问题时把异常交给测试运行器报告；没有捕获异常并只打印“失败”后继续假装测试通过。

### 两张工单的往返测试

第二个文件测试自己准备两张工单：第一张编号 1001、标题“投影仪无信号”，派给工程师 20；第二张编号 1002、标题“打印机卡纸”，保持 OPEN 且处理人为 null。

保存到 `tempDir.resolve("tickets.properties")`，再读取，检查列表非 null、数量为 2，然后分别检查每张工单的四个字段。例如：

```java
assertEquals(1001L, loadedFirst.getId());
assertEquals("投影仪无信号", loadedFirst.getTitle());
assertEquals(TicketStatus.IN_PROGRESS, loadedFirst.getStatus());
assertEquals(Long.valueOf(20L), loadedFirst.getAssigneeId());

assertEquals(1002L, loadedSecond.getId());
assertEquals("打印机卡纸", loadedSecond.getTitle());
assertEquals(TicketStatus.OPEN, loadedSecond.getStatus());
assertNull(loadedSecond.getAssigneeId());
```

处理人类型是可为空的 `Long`，未派单用真正的 `null`；不是字符串 `"null"`。已派单检查的是数值是否相等，不是两个包装对象的引用是否相同。

今天用到的断言可以这样记：

| 断言 | 检查什么 |
| --- | --- |
| `assertEquals(expected, actual)` | 实际结果与预期是否相等 |
| `assertNotNull(value)` | 结果是否不是 null |
| `assertNull(value)` | 结果是否为 null |
| `assertTrue(condition)` | 条件是否成立 |
| `assertThrows(type, action)` | 执行动作时是否抛出指定类型的异常 |

截至本次日结，`TicketTest` 的 6 个加上 `TicketFileStoreTest` 的 2 个，共 **8 个 JUnit 测试已通过**。此前布置过将“第二张缺标题”改写为 JUnit 测试，但尚未写入文件，当前还是 Demo 验证，不能算作第 9 个测试。

## 8 TicketStatus.IN_PROGRESS 前面一定要带类型吗

我问过这行里的 `TicketStatus` 能不能省略：

```java
assertEquals(TicketStatus.IN_PROGRESS, loadedFirst.getStatus());
```

`TicketStatus` 是枚举类型，`IN_PROGRESS` 是这个类型定义的枚举常量。当前写法明确指出常量属于哪个枚举，可读性也好。

Java 可以通过静态导入省略某些静态成员前面的类名。比如我们已经使用：

```java
import static org.junit.jupiter.api.Assertions.assertEquals;
```

所以后面可以直接写 `assertEquals(...)`。

不过，**当前 `TicketStatus` 仍在默认包中，这一阶段继续写 `TicketStatus.IN_PROGRESS`**。以后将枚举放入具名包，才可以按实际包名静态导入它，例如下面只是未来目录调整后的示意：

```java
// 前提：TicketStatus 已声明在 com.example.opsticket 包中
import static com.example.opsticket.TicketStatus.IN_PROGRESS;

// 此后可直接使用 IN_PROGRESS
```

不能直接把这个未来的包名复制进当前项目。是否静态导入属于代码表达方式，不会改变工单真正的状态。

## 9 回到原计划：提前接触工具，不等于前两周都完成

学到这里，我提出重新核对计划。原课程第三周才安排 Maven；前两周的目标是工单对象、集合管理和文件恢复。当时虽然已有 8 个 JUnit 测试，数组独立练习、存档重复编号、恢复后继续操作等项目还没有全部验收。

因此接下来的教学顺序调整为：保留已经配置好的 Maven 和已经写好的测试，暂停扩展工具知识，先把前两周缺口补齐。

| 部分 | 本次日结的位置 |
| --- | --- |
| 第一周对象、标题校验、引用、Git | 已有练习；本次补了数组最大值、标题重写和 static 口述检查 |
| 第二周集合、文件恢复 | 已补去重、数字计数和读回后加入服务，整体仍未完成 |
| 第三周 Maven 与职责拆分 | 工具部分提前接触，不能据此把第三周整周标为完成 |

这一轮补漏并没有重新从头讲一遍所有数组操作，而是用短练习确认能否把已有知识写出来。第一周本轮补漏验收结束，第二周还要继续完成启动和编号续接。

## 10 数组最大值：初始值为什么不能随便写成 0

我在 `ArrayPractice` 中实现了：

```java
public static int findMax(int[] numbers) {
    if (numbers == null || numbers.length == 0) {
        throw new IllegalArgumentException();
    }

    int max = numbers[0];
    for (int i = 0; i < numbers.length; i++) {
        if (numbers[i] > max) {
            max = numbers[i];
        }
    }
    return max;
}
```

先处理 null 和空数组，才能安全读取 `numbers[0]`。用首元素作为起点，可以正确处理 `{-7, -2, -9}`：最大值为 -2；如果错误地初始化为 0，就可能返回数组里根本不存在的 0。

我起初不知道怎样在 `main` 里测试。正常值测试的结构是准备输入、调用、比较：

```java
int actual = findMax(new int[]{3, 8, 2, 8});
if (actual != 8) {
    throw new AssertionError("预期是8，实际是：" + actual);
}
```

异常测试则检查“该抛的异常有没有抛”：

```java
try {
    findMax(null);
    throw new AssertionError("传入null时应该抛出异常");
} catch (IllegalArgumentException e) {
    System.out.println("null输入测试通过");
}
```

普通数组和 null 两项按示例编写后，我补了全负数、单元素、空数组三项，共 5 项通过。检查时还发现，复制测试后两处失败消息仍打印第一项的 `actual`，应分别使用 `actual2`、`actual3`；后来已修正。

这类消息错误在测试通过时不会暴露，但真正失败时会误导排查。判断条件正确和失败提示正确，都值得检查。

## 11 独立重写标题校验，再确认 static 的边界

我根据既定规则，在 `TitleValidationPractice` 中重写了标题校验方法：

```java
public static String validateTitle(String title) {
    if (title == null) {
        throw new IllegalArgumentException();
    }
    String trimmedTitle = title.trim();
    if (trimmedTitle.length() < 1 || trimmedTitle.length() > 50) {
        throw new IllegalArgumentException();
    }
    return trimmedTitle;
}
```

重点是先排除 null，再 trim，最后判断处理后的长度。它是用于独立练习的方法，没有替换 `Ticket` 内部现有的业务校验。

我这次没有继续编写自己的 `main` 自测，选择由助手检查。助手的 8 项临时检查覆盖中文去空格、长度 1、长度 50、两端空格包围 50 字符，以及 null、空串、纯空格、51 字符，均通过。记录上应写“方法由我实现，边界检查由助手代验”，不能写成我独立建立了这套测试。

接着做了 static 的口头推演：如果把 `Ticket` 的 id、title 改成 static，先创建第一张，再创建第二张，通过第一张对象读取这两个字段会得到什么？

我回答会得到第二张的数据，因为 static 字段由类的所有对象共享。这个解释正确。

- 普通实例字段：每个对象各自保存，如每张工单的编号和标题。
- static 字段：类共享的一份数据，不能用它保存每张工单各自不同的值。
- static 方法：可以通过类调用；练习方法写成 static，不代表所有业务字段也应如此。

对象是否分别创建，与其访问的字段是否共享，是需要分别判断的两件事。

## 12 Set 去重：contains 只查，不会帮我记住编号

`TicketService.add` 已经会拒绝重复编号，但 `loadAll` 先把存档恢复到 `List`，这一步没有自动调用服务的添加校验。List 又允许重复，因此存档里两条记录都写成 1001 时，原来的加载过程仍可能读出两张。

这次在 `loadAll` 中加入 `Set<Long>`，记录已遇到的编号。Set 表达“不重复的一组值”，HashSet 是其一种实现。我们只需要判断是否出现过，不依赖它的遍历顺序。

我最初写成：

```java
if (seenIds.contains(id)) {
    throw new IllegalArgumentException("包含重复的编号");
}
```

但是没有向 `seenIds` 添加过编号，集合一直为空，所以重复输入仍未被拦住。

修正后的关键结构是：

```java
List<Ticket> result = new ArrayList<>();
Set<Long> seenIds = new HashSet<>();

for (int i = 0; i < count; i++) {
    // 读取并检查各个字段，解析出 id
    long id = Long.parseLong(idText);

    if (seenIds.contains(id)) {
        throw new IllegalArgumentException("存档中工单编号重复：" + id);
    }
    seenIds.add(id);

    // 继续转换状态、处理人，并恢复 Ticket
}
```

这是结构示意，字段读取仍使用现有代码。Set 必须在循环外创建，否则每一轮都会得到一个新的空集合，无法记住前面的编号。

`contains` 负责查询，`add` 才负责添加。也可以利用 `Set.add` 的返回值：第一次添加返回 true，已存在时返回 false。但当前代码保留“先查，再加”，方便理解执行顺序。

经提示修正后，助手在临时存档中重新检查了 3 个场景：1001/1002 正常恢复、`count=0` 返回空列表、1001/1001 抛出包含重复编号的异常，均通过。这 3 项是临时验收，没有新增为 JUnit 方法。

## 13 Map 计数：键是数字，值是次数

第二周另一个练习是在 `ArrayPractice` 中实现：

```java
public static Map<Integer, Integer> countOccurrences(int[] numbers)
```

例如输入 `{3, 8, 3, 2, 8, 3}`，需要得到 `{3=3, 8=2, 2=1}`。键是数字本身，值是它出现的次数。

我最初把方法写错位置，后来移回 `ArrayPractice`。检查时还暴露了几个逻辑问题：

| 当时的写法 | 为什么不符合要求 |
| --- | --- |
| 把下标 i 当作 Map 的键 | `{5}` 得到 `{0=1}`，统计的是位置而不是数字 |
| 外层只遍历 0～9 | 漏掉负数、12 等范围外的数字 |
| 空结果补入 `{0=0}` | 空数组没有任何数字，应返回空 Map |
| 使用 HashMap | 次数可以统计正确，但不能保证首次出现的顺序 |

修正逻辑后还漏了结束类的右括号，导致编译失败。那一轮没有运行旧 class 来冒充新代码通过；补上括号并换成 LinkedHashMap 后才重新验证。

最终方法是：

```java
public static Map<Integer, Integer> countOccurrences(int[] numbers) {
    if (numbers == null) {
        throw new IllegalArgumentException();
    }

    Map<Integer, Integer> occurrences = new LinkedHashMap<>();
    for (int i = 0; i < numbers.length; i++) {
        int number = numbers[i];
        int oldCount = occurrences.getOrDefault(number, 0);
        occurrences.put(number, oldCount + 1);
    }
    return occurrences;
}
```

`getOrDefault(number, 0)` 的意思是：已有这个数字就取出原次数，没有就返回默认值 0。它只读取，不会自动把数字放进 Map，也不会自动累加；更新必须通过 `put` 写回。

遍历 `{3, 8, 3}` 时，变化是：

```text
读到 3 → {3=1}
读到 8 → {3=1, 8=1}
读到 3 → {3=2, 8=1}
```

默认创建的 LinkedHashMap 按插入顺序迭代；更新已有键的值，不会把这个键移动到最后。所以结果保持数字首次出现的顺序。

空数组不进入循环，直接返回空 Map，根本不需要额外“补零”。助手临时验证了重复数字、负数与 0、单元素、空数组、大于 9 的数字、null 拒绝，以及键的首次出现顺序，共 7 项通过。我没有把这些检查写成永久测试；现有 `ArrayPractice.main` 中仍是最大值练习的 5 项检查。

## 14 从读回列表，到恢复进服务

之前 `loadAll` 只返回一个 `List<Ticket>`。新建的 `TicketService` 内部仍是空 Map，不会因为文件被读取过就自动拥有这些工单。

这次在 `TicketLoadDemo` 中加入：

```java
List<Ticket> tickets = store.loadAll(path);

TicketService service = new TicketService();
for (Ticket ticket : tickets) {
    service.add(ticket);
}

System.out.println("服务中的工单数：" + service.findAll().size());
System.out.println(service.findById(1001L).getStatus());
System.out.println(service.findByStatus(TicketStatus.OPEN).size());
```

原有两张工单字段断言继续保留。实际运行得到服务中有 2 张工单，1001 的状态为 IN_PROGRESS，OPEN 数量为 1；助手又用临时检查确认 OPEN 工单就是 1002，处理人为 null。

这个循环保存的是读回对象的引用，没有为每张工单再复制一个对象。此后可以通过服务按编号查询、按状态筛选。

顺序上先让 `loadAll` 完整成功，再创建和填充新的服务。读文件中途抛异常，就不会执行后面的恢复循环。当前是 Demo 创建一个新服务并加入完整列表，尚未实现“把已有服务中的整批数据安全替换掉”的专用接口。

我的 Demo 本次增加的是三项输出核对；服务内 OPEN 具体编号和其他状态的自动断言由助手临时补充。这个区别也保留在学习记录中。

## 15 这次实际完成了什么，下一次接哪里

| 内容 | 本次状态 |
| --- | --- |
| 缺字段坏存档与异常测试 | Demo 已完成，明确失败原因和 AssertionError 的传播 |
| 空列表往返 | Demo 和 JUnit 均有对应实现 |
| 目录整理 | main/test/data 已分开，IDEA 识别问题已修复 |
| Maven 与 JUnit | 提前接触，8 个永久 JUnit 测试通过，暂缓继续扩展 |
| 数组最大值 | 我实现方法并补完 main，5 项检查通过，失败提示已修正 |
| 独立重写标题校验 | 我实现方法，助手 8 项临时边界检查通过 |
| static 字段 | 能正确解释两张工单共享字段的后果 |
| 存档重复编号 | 经提示修正 contains 漏 add，3 项临时检查通过 |
| 数字出现次数 | 经反馈修正并编译通过，7 项临时检查通过 |
| 文件列表恢复到服务 | 已加入、查询和筛选，运行结果符合预期 |
| 自动生成下一张工单编号 | 只布置了任务，尚未实现 |
| 首次缺文件、具体坏字段提示、完整重启验收 | 仍待后续完成 |

接下来先在 `TicketService` 中实现：

```java
public Ticket create(String title)
```

计划是遍历服务内已有工单找到最大编号，新编号取最大值加 1，再构造 Ticket、调用现有 add 并返回对象。空服务从 1 开始；恢复 1001、1002 后应创建 1003，再创建得到 1004。标题非法时，由 Ticket 构造器拒绝，服务数量不能增加。

**这个 create 方法目前尚未写入源码，以上是下次任务，不是本次已经完成的功能。**

编号续接之后，还要区分首次没有存档与存档损坏，让坏数据提示指出记录和字段，并完成真正退出程序、重新启动、恢复筛选结果和继续新建的验收。特殊字符与非法状态也要放进完整场景继续核对。不能因为文件读回和现有测试通过，就把第二周全部标为完成。
