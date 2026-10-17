---
title: "设备运维工单开发 — 05 重启验收与仓库接口入门"
description: "完成自动编号、启动恢复、坏存档提示和两阶段重启验收；进入第三周，核对 Java/Maven、迁移包结构，学习接口、实现类、异常链与仓库的首批 JUnit 测试。"
date: 2026-10-17T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "文件读写", "异常处理", "Maven", "JUnit", "接口", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 5
chapter_title: "重启验收与仓库接口入门"
---

> 本篇记录 **2026 年 10 月 17 日**的学习，承接[测试入门与基础补全](/posts/ops-ticket-20261016/)。上一篇已经把 16 日开始、延续到 17 日凌晨的学习统一归入 16 日；本篇从后续的自动编号开始，不重复计算那段进度。课程路线见[学习栏目](/learning/)，当前运行方式和实现边界见[项目文档](/learning/project-docs/)。

今天先把第二周剩余的文件恢复流程做完：自动编号、首次启动、坏存档提示、两个进程之间的保存与恢复，以及失败时保留原文件。完成运行和理解检查后，我才进入第三周，核对 Java/Maven 环境、移动到正式包结构、提交 Git，并开始学习仓库接口和实现类。

我有一处很明确的学习反馈：代码已经写到 `implements` 和 `@Override`，但接口的概念还没有讲清楚。因此后半段先停下来补概念，再写最初的两个仓库测试。这里记录的是按指导实现、经解释后理解以及具体检查的范围，不代表已经独立完成整套分层设计。

## 1 自动创建工单：编号取最大值加一

之前调用 `new Ticket(...)` 时，编号由调用方传入。现在我在 `TicketService` 中加入：

```java
public Ticket create(String title) {
    long maxId = 0;
    for (Ticket ticket : ticketsById.values()) {
        if (ticket.getId() > maxId) {
            maxId = ticket.getId();
        }
    }

    Ticket ticket = new Ticket(maxId + 1, title);
    add(ticket);
    return ticket;
}
```

这个方法依次做三件事：

1. 遍历已有工单，找出最大编号。
2. 用最大编号加一和传入标题构造工单。
3. 复用 `add` 加入服务，再把新工单返回给调用方。

这里复用了前面数组求最大值的思路，但初始值可以是 `0`：合法工单编号都大于零，空服务不进入循环，第一张自然得到编号 `1`。

编号不能用 `findAll().size() + 1`。例如已有 `1、2、5`，数量加一是 `4`，而当前约定是从最大编号后继续，应该得到 `6`。恢复的编号是 `1001、1002` 时，新建也应该得到 `1003`，而不是 `3`。

### 创建失败时，服务不能多一张工单

顺序同样重要：

```java
Ticket ticket = new Ticket(maxId + 1, title);
add(ticket);
```

如果标题非法，构造器会在第一行抛异常，第二行就不会执行。因此检查不能只看“是否报错”，还要比较创建前后的工单数量。

我补了这些 Demo 场景：

| 场景 | 验证结果 |
| --- | --- |
| 已有 1001、1002 后创建 | 得到 1003，服务能找到刚返回的同一个对象 |
| 再创建一次 | 得到 1004，数量增加到 4 |
| 新建空服务后创建 | 编号为 1，数量为 1 |
| 用纯空白标题创建 | 抛出异常，服务数量不变 |

这些检查先在原来的 `TicketServiceDemo` 中完成。它们是带断言的可运行 Demo，不等同于新增了四个 JUnit 测试。

## 2 启动时，缺文件和坏文件不能混成一种情况

第一次使用程序时可能没有存档；已经有存档但内容损坏，则是另一件事。

我新建 `TicketStartupDemo`，让它负责启动阶段的恢复和分支处理：

```java
TicketFileStore store = new TicketFileStore();
TicketService service = new TicketService();

try {
    List<Ticket> tickets = store.loadAll(path);
    for (Ticket ticket : tickets) {
        service.add(ticket);
    }
} catch (NoSuchFileException e) {
    System.out.println("没有找到存档，使用空服务启动");
} catch (IOException e) {
    System.out.println("读取失败，停止启动：" + e.getMessage());
    return;
} catch (IllegalArgumentException e) {
    System.out.println("存档内容不合法，停止启动：" + e.getMessage());
    return;
}

System.out.println("启动完成，工单数量：" + service.findAll().size());
```

`service` 在 `try` 外面创建，所以正常加载和缺文件两个分支结束后，后面的代码都能使用它。

`NoSuchFileException` 是 `IOException` 的子类，必须先捕获更具体的异常。若把 `IOException` 放在前面，后面的缺文件分支就无法正常安排。

| 启动情况 | 当前程序的处理 |
| --- | --- |
| 正常存档 | 完整读回并加入服务，输出恢复后的数量 |
| 存档不存在 | 保持空服务，继续完成启动 |
| 其他读取错误 | 输出原因并 `return`，停止本次启动 |
| 存档内容不合法 | 输出原因并 `return`，停止本次启动 |

不能用一个宽泛的 `catch` 把所有错误都解释成“第一次使用”。否则坏文件也可能变成空服务，再被后续保存覆盖。

这一步的启动 Demo 只读取，不保存。测试时我改的是独立副本路径，测完恢复到正常的 `data/tickets.properties`。检查过程中有过“以为已改回，磁盘仍指向坏文件”的情况，后来重新确认了保存后的文件；以后不能只凭编辑器里看见改动就认为实际运行版本一定一致。

## 3 把“读取失败”细化到具体字段

之前缺少第二张标题时，消息只有“存档缺少必要字段”。它能拒绝坏数据，但不能直接指出位置。

我提取了读取必需字段的辅助方法：

```java
private String requireProperty(Properties data, String key) {
    String value = data.getProperty(key);

    if (value == null) {
        throw new IllegalArgumentException("存档缺少必要字段：" + key);
    }

    return value;
}
```

循环读取四个字段时统一调用：

```java
String idText = requireProperty(loaded, prefix + "id");
String title = requireProperty(loaded, prefix + "title");
String statusText = requireProperty(loaded, prefix + "status");
String assigneeText = requireProperty(loaded, prefix + "assigneeId");
```

第二条记录缺标题，现在会得到：

```text
存档缺少必要字段：ticket.1.title
```

这里的 `1` 是从零开始的记录下标，不是工单编号。

这个方法只检查 `null`，不能把空字符串也一律拒绝。文件中：

```properties
ticket.1.assigneeId=
```

表示“字段存在，目前没有处理人”，是未派单工单的合法存档形式。相反，完全删除这一行，才是缺少必需字段。

### 字段存在，还要区分能否转换成数字

例如 `ticket.1.id=abc` 有这个键，但 `abc` 无法转换成 `long`。我加入：

```java
private long parseLongProperty(String text, String key) {
    try {
        return Long.parseLong(text);
    } catch (NumberFormatException e) {
        throw new IllegalArgumentException(
                "存档字段格式错误：" + key
                        + "，应为整数，实际值：" + text,
                e
        );
    }
}
```

编号使用这个方法；处理人则先保留空字符串分支：

```java
Long assigneeId;
if (assigneeText.isEmpty()) {
    assigneeId = null;
} else {
    assigneeId = parseLongProperty(
            assigneeText, prefix + "assigneeId");
}
```

方法返回的 `long` 赋给 `Long` 变量时会自动装箱。空的处理人不参与数字转换，而是恢复成 `null`。

## 4 为什么新异常还要传入原来的 e

这是今天我连续追问最多的地方：

```java
throw new IllegalArgumentException(message, e);
```

这句先用构造器创建一个异常对象，再通过 `throw` 把它抛出。它使用两个参数：

- `message`：我补充的错误说明。
- `e`：刚才捕获的原始异常，作为新异常的原因保存。

它和只写消息的构造器都是合法的，是构造器重载：

```java
new IllegalArgumentException(message);
new IllegalArgumentException(message, e);
```

自己检查出缺字段时，并没有更早捕获的异常，所以直接传消息就可以。捕获已有异常、补充字段位置再抛出时，通常把原异常也传进去，保留最初失败的原因和调用位置。

以非法状态为例：

```java
TicketStatus.valueOf("DONE");
```

原异常能说明枚举里没有 `DONE`，但它不知道错误来自存档的哪条记录。外层补充的消息是：

```text
存档状态不合法：ticket.1.status，实际值：DONE
```

两份信息可以同时保留：

```text
新异常：哪条记录、哪个字段不合法
  └─ cause：原异常，说明底层为什么转换失败
```

这不是同时抛出两个异常，也不会因为把 `e` 传进去就重新执行出错代码；实际抛出的是一个新异常，它引用着原异常。

### 新异常最后被谁捕获

当前调用链是：

```text
Demo 调用 loadAll
→ loadAll 调用 parseStatusProperty
→ valueOf 失败，产生原异常
→ 辅助方法 catch 捕获原异常
→ 包装并抛出新异常
→ loadAll 没有捕获这个新异常，继续向外传播
→ Demo 的 catch 捕获新异常
```

在 Demo 的 `catch` 里：

```java
catch (IllegalArgumentException ex) {
    System.out.println(ex.getMessage());
    System.out.println(ex.getCause());
}
```

`getMessage()` 读取新补充的消息，`getCause()` 取得原异常对象。打印完整异常栈时，可以通过 `Caused by:` 看到原因链。

即使两个 `catch` 都把变量叫作 `e`，它们也是不同作用域里的变量，分别指向不同对象。异常被 Demo 捕获以后，由 Demo 决定如何提示或验证；程序不会回到 `loadAll` 失败的地方继续读下一条。

## 5 格式检查和业务校验分层处理

数字能转换，不代表符合业务规则；状态字符串存在，也不代表属于枚举。

### 状态转换

```java
private TicketStatus parseStatusProperty(String text, String key) {
    try {
        return TicketStatus.valueOf(text);
    } catch (IllegalArgumentException e) {
        throw new IllegalArgumentException(
                "存档状态不合法：" + key + "，实际值：" + text,
                e
        );
    }
}
```

`DONE` 不在当前枚举里，会在这里被拒绝。测试副本只修改状态，其他字段保持正常，避免还没有走到目标分支就先因缺标题而失败。

### count 的三类问题

`count` 使用相同的必需字段检查，再由 `parseIntProperty` 调用 `Integer.parseInt`：

```java
String countText = requireProperty(loaded, "count");
int count = parseIntProperty(countText, "count");

if (count < 0) {
    throw new IllegalArgumentException(
            "存档字段不合法：count，不能为负数，实际值：" + count);
}
```

| 内容 | 失败位置 |
| --- | --- |
| 没有 `count` 行 | 必需字段检查 |
| `count=abc` | 字符串转整数 |
| `count=-1` | 转换成功后的数量规则检查 |

`parseIntProperty` 与数字编号的辅助方法结构相同，只是返回类型和转换方法换成 `int`、`Integer.parseInt`。

### 恢复对象时，补上记录位置

`id=0` 能转换成数字，却不符合“编号必须大于零”。空标题和状态、处理人不匹配，也应该继续由 `Ticket` 的业务规则拒绝。

我没有在文件类重写一遍业务校验，而是在调用恢复方法的地方补上下文：

```java
try {
    Ticket ticket = Ticket.restore(id, title, status, assigneeId);
    result.add(ticket);
} catch (IllegalArgumentException e) {
    throw new IllegalArgumentException(
            "存档记录不合法：ticket." + i
                    + "，原因：" + e.getMessage(),
            e
    );
}
```

这里专门包住对象恢复的部分，前面的字段检查和转换仍保留各自清楚的错误消息。捕获后重新抛出，整次加载仍然失败，不会跳过坏记录后返回半份数据。

我分别使用副本测试了 `id=0`、空标题、`OPEN` 却带有处理人这三种业务错误；这些场景和 `count` 三个场景由我报告测试通过，助手核对了对应实现。不能把它们写成新增了六个正式 JUnit。

### 测试错误数据，不是看到异常就算通过

我一开始不知道非法编号 Demo 怎么组织，后来按给出的结构完成：

```java
try {
    store.loadAll(path);
    throw new AssertionError("非法编号应该被拒绝，但读取正常返回了");
} catch (IllegalArgumentException e) {
    String expected =
            "存档字段格式错误：ticket.1.id，应为整数，实际值：abc";
    if (!expected.equals(e.getMessage())) {
        throw new AssertionError("异常消息不符合预期", e);
    }
    System.out.println("测试通过：非法编号被拒绝，错误消息正确");
} catch (IOException e) {
    throw new AssertionError("测试文件未能正常读取", e);
}
```

正常返回说明没有拒绝坏数据；文件都没读到也不能算测试目标通过。只有捕获了预期异常，并核对具体消息，才能说明这次确实测到了非法编号。非法状态 Demo 沿用相同结构。

## 6 真正结束程序，再从文件恢复

之前分别有保存和加载的小 Demo，这次用两个独立运行的程序做完整重启验收。

保存端 `TicketRestartSaveDemo` 创建编号 `1、2、3` 的工单，把第二张派给 `20`，检查 `OPEN` 筛选结果是 `1、3`，然后保存到：

```text
data/tickets-restart.properties
```

第一张标题故意使用特殊字符：

```java
Ticket first = service.create("A=B\\C");
```

Java 源码中的 `\\` 表示实际字符串里的一个反斜杠，标题实际为 `A=B\C`。Properties 文件可能显示为 `A\=B\\C`，这是存储格式的转义，不是标题损坏，是否正确要读回后再比较。

保存程序显示“阶段一通过”并结束后，我单独运行 `TicketRestartLoadDemo`：

```text
读取文件
→ 得到恢复后的工单列表
→ 创建新的 TicketService
→ 循环 add
→ 验证三张工单
→ 新建第四张
```

读取端检查：

| 检查内容 | 预期 |
| --- | --- |
| 原有数量 | 3 张 |
| 第一张 | 特殊字符标题不变，OPEN，没有处理人 |
| 第二张 | 标题不变，IN_PROGRESS，处理人为 20 |
| 第三张 | 标题不变，OPEN，没有处理人 |
| OPEN 筛选 | 仍是编号 1、3 |
| 恢复后继续创建 | 新编号为 4，服务数量变为 4 |

读取 Demo 最初误放在 `src/main/java`，提醒后移到了 `src/test/java`。它是验收代码，不属于业务实现。

新建第四张发生在筛选检查之后，因为第四张也是 `OPEN`，顺序反过来，筛选数量就应该是三张了。

这一步没有再次调用保存，所以第四张只在内存中。重复运行读取 Demo 时，仍然从文件恢复原来的三张，再创建编号 `4`。不能把“内存新增”误认为“已经写回磁盘”。

## 7 坏存档保护与第二周理解验收

我复制重启存档，分别制造第三张编号重复、第三张状态为 `DONE` 两种问题。每个场景从正常副本开始，只改对应字段，让启动 Demo 读取坏副本。

预期有两点：程序停止启动，不出现“启动完成”；原文件内容不变。

为了检查第二点，我在修改好坏数据之后、运行程序之前记录哈希：

```powershell
$beforeHash = (Get-FileHash .\data\tickets-restart-invalid.properties).Hash
```

在 IDEA 运行后，回到同一个终端比较：

```powershell
(Get-FileHash .\data\tickets-restart-invalid.properties).Hash -eq $beforeHash
```

我报告两个场景都得到 `True`，并把启动路径恢复为正常存档。这是我的运行反馈，区别于助手另外执行的隔离检查。

这里验收的是“当前失败启动流程不改写坏文件”。它没有证明保存过程已经具备断电保护或原子替换；那些机制当前还没有实现。

### 三个口头检查

**同一个 Map 键 put 两次会怎样？** 我回答：数量仍为一，后值替换前值。因此新增工单前要用 `containsKey` 拒绝重复，避免原工单被覆盖。

**已有 1、2、5，下一张编号为什么是 6？** 我回答：当前规则取最大编号加一；`maxId` 虽然从零开始，但随后遍历已有工单，不会每次都留在零。

**相同的相对路径为什么可能读不到保存的文件？** 我回答：要检查工作目录，相对路径前面的实际位置可能不同。补充的排查方式是同时看保存端、读取端的 `path.toAbsolutePath()`，并确认文件实际位于读取的位置。

结合前面的功能和运行检查，这一轮第二周验收完成。我随后进入第三周，不再把已经完成的自动编号、启动恢复继续写成待办。

## 8 第三周先核对环境，再用 Maven 构建

终端提示栏出现的 `0.1.0-SNAPSHOT` 是 Maven 项目版本，`SNAPSHOT` 表示开发阶段版本；旁边的 Java 版本提示则来自终端所检测到的运行环境。它们不是同一个信息。

今天发现 IDEA 的项目 SDK 和 `pom.xml` 目标已经是 Java 21，但终端之前仍优先找到 Java 8。这里要区分三件事：

| 位置 | 决定什么 |
| --- | --- |
| IDEA 项目 SDK | IDE 使用哪个项目 JDK |
| 启动 Maven 的 Java 环境 | Maven 自己运行在哪个 JDK 上 |
| `maven.compiler.release` | 源码编译面向的 Java 版本 |

`pom.xml` 写了 `21`，不等于它会自动把终端里的 Java 切换到 21。

我按指导在当前 PowerShell 会话设置 `JAVA_HOME`，并把对应 JDK 的 `bin` 放在 `Path` 最前面。核对 `java -version`、`javac -version` 和 Maven 的版本输出，三处都显示 **21.0.8**。

这次调整只对当时的终端会话有效，没有修改永久系统配置。终端本来不能直接识别 `mvn`，实际使用的是 IDEA 自带 Maven 的 `mvn.cmd` 完整路径，通过 PowerShell 的 `&` 调用；不能因此写成“系统全局 Maven 已安装配置完毕”。

### clean package 做了什么

这次执行的构建目标是：

```text
clean package
```

`clean` 清理旧的构建输出；`package` 会先经过编译、测试等前置阶段，成功后再打包。

```text
清理 target
→ 编译业务代码
→ 编译测试代码
→ 执行符合规则的 JUnit 测试
→ 打包普通 JAR
```

我报告构建输出 `BUILD SUCCESS`，当时是原有 **8 个 JUnit 全部通过**。

带 `main` 的 Demo 虽然位于测试源码目录，会被编译，但不会因为执行 `package` 就自动逐个运行。当前 JAR 也没有配置 `java -jar` 所需的应用启动入口，打包成功不等于已经得到可直接双击或 `java -jar` 运行的完整应用。

## 9 迁移到正式包：目录和声明都要对应

目前所有类统一进入：

```java
package cn.wishbottle.opsticket;
```

于是 `Ticket` 的完整类名变成：

```text
cn.wishbottle.opsticket.Ticket
```

业务类放在：

```text
src/main/java/cn/wishbottle/opsticket/
```

测试、Demo 和练习类放在：

```text
src/test/java/cn/wishbottle/opsticket/
```

两套源码根目录可以使用相同包名；业务代码和测试代码的职责区分来自源码根目录，不是必须给它们取不同的包名。

我使用 IDEA 的移动重构，过程中遇到了两种窗口：

- **Refactoring Preview**：列出将受影响的引用，是执行前预览。
- **Conflicts Detected**：提示可能有问题，需要查看具体内容，不能把所有冲突都当普通预览直接跳过。

当时部分冲突指向 README 中出现的测试类名，提示生产源码无法访问测试类。文档中的文字引用不一定表示 Java 依赖真的写错，但仍需要核对目标是否是测试源码根目录，以及是否开启了搜索文本出现位置。文本搜索还可能把文档中的简单类名一起换成完整类名。

迁移后检查了目录、每个文件顶部的 `package` 声明，并再次构建、运行重启读取 Demo。这里要同时验证代码编译和实际运行，而不是只看文件在项目树里换了位置。

## 10 Git 阶段提交要包含最新内容

在继续接口练习前，我做了一次阶段提交：

```text
3239d49 完成第二周工单验收并接入Maven与包结构
```

提交前有一个容易忽略的问题：暂存区可能还留着文件更早的版本，工作区改好了，不代表暂存区自动更新。因此重新暂存并查看：

```powershell
git add -A
git status
git diff --cached --stat
```

`git add -A` 会记录新增、修改和删除。这次移动目录，旧位置删除也需要记录，Git 可能把对应变化识别为重命名。

项目还把 `*.iml` 加入忽略规则，与已有的 IDE 配置和构建产物一起排除。提交前要确认没有把 `target`、`.idea` 等内容混入。

这次是学习项目的**本地提交**。后面的仓库实现和两个新测试属于继续学习产生的工作，不能仅凭这个提交就认为当天之后的所有代码都已经提交。

## 11 接口、实现类和 @Override

第三周开始尝试把存储操作从服务中分离。我先写了仓库接口：

```java
public interface TicketRepository {

    void add(Ticket ticket);

    Optional<Ticket> findById(long id);

    List<Ticket> findAll();

    void update(Ticket ticket);
}
```

接口约定“可以进行哪些操作”，并不规定内部必须使用哪种存储方式。这四个普通抽象方法没有方法体，以分号结束；它们在接口里默认是 `public abstract`。

具体行为还需要明确：

| 方法 | 当前约定 |
| --- | --- |
| add | 新增；拒绝 null 和重复编号 |
| findById | 查到返回包含工单的 Optional，查不到返回空 Optional |
| findAll | 返回全部工单的新列表 |
| update | 更新已有编号；拒绝 null，编号不存在时拒绝 |

实现类声明为：

```java
public class InMemoryTicketRepository implements TicketRepository
```

`implements` 表示实现接口。当前这个普通类需要提供四个方法的实现，方法必须保持 `public`，不能缩小接口约定的访问范围。我能够解释：删掉 `update` 后，就没有完整实现这份约定，当前这个类会编译失败。

### @Override 是建议写的检查标记，不是实现逻辑

我曾以为四个方法是不是必须都写 `@Override`。实际区别是：

- 方法正确实现，即使省略注解，仍可编译。
- 注解写上后，编译器会核对它是否真的实现接口方法或重写父类方法。
- 注解不能替代方法体，更不能让缺少的方法自动实现。
- 普通辅助方法若不对应接口或父类方法，不要为了格式统一随便加它。

因此本次四个实现方法都标上 `@Override`，明确自己的意图。

### 接口类型的变量，指向实现类对象

```java
TicketRepository repository = new InMemoryTicketRepository();
```

左边是变量的接口类型，决定通过它可以调用接口约定的哪些方法；右边实际创建的是内存仓库对象。随后调用 `repository.add(...)`，执行的是内存仓库的具体实现。这是多态的一种使用方式。

今天的进度是借助这个实际例子理解概念，还没有完成 Service 对仓库的接入。以后再换存储实现的设想，也不能写成当前已经有了文件仓库或数据库仓库。

## 12 内存仓库的四个方法

`InMemoryTicketRepository` 用一个 `LinkedHashMap<Long, Ticket>` 保存数据：

```java
private final Map<Long, Ticket> ticketsById = new LinkedHashMap<>();
```

`add` 检查非空和重复编号后再 `put`；`update` 检查非空、编号已经存在，再用传入对象替换对应值。

两者的条件正好不同：

```text
add：编号已存在 → 拒绝
update：编号不存在 → 拒绝
```

查询方法使用新的返回类型：

```java
@Override
public Optional<Ticket> findById(long id) {
    return Optional.ofNullable(ticketsById.get(id));
}
```

`Map.get` 查不到返回 `null`，`Optional.ofNullable` 把它转换为空的 Optional；查到则返回包含该对象的 Optional。

`findAll` 返回：

```java
return new ArrayList<>(ticketsById.values());
```

这创建了新的列表，调用方清空或增删这个列表，不会直接增删仓库内部 Map 的条目。但是里面的 `Ticket` 仍是原对象引用，并没有深复制工单。后面测试列表隔离时，要把“集合是否独立”和“元素对象是否独立”分开。

当前 `TicketService` 仍然使用自己原来的 Map，`findById` 仍返回 `Ticket` 或 `null`；只有新仓库接口返回 `Optional<Ticket>`。不能在还没有接入之前，把服务也描述成已改用 Optional 或仓库。

## 13 新仓库的前两个 JUnit 测试

在测试包里，我按讲解写下 `InMemoryTicketRepositoryTest`。第一个检查新增后可以查询：

```java
@Test
void addedTicketShouldBeFound() {
    TicketRepository repository = new InMemoryTicketRepository();
    Ticket ticket = new Ticket(1L, "投影仪无信号");

    repository.add(ticket);
    Ticket found = repository.findById(1L).orElseThrow();

    assertEquals(1L, found.getId());
    assertEquals("投影仪无信号", found.getTitle());
    assertEquals(1, repository.findAll().size());
}
```

第二个检查不存在的编号：

```java
@Test
void missingTicketShouldReturnEmpty() {
    TicketRepository repository = new InMemoryTicketRepository();

    assertTrue(repository.findById(999L).isEmpty());
}
```

这里重点认识两个 Optional 方法：

| 方法 | 当前测试中的作用 |
| --- | --- |
| orElseThrow() | 有工单就取出；没有则抛异常，让“应该查到”的测试失败 |
| isEmpty() | 判断没有结果，用于验证不存在的编号 |

两个测试各自创建仓库，互不依赖，不要求先执行新增测试再执行空查询测试。

日结核对时，源码里已经有这两个新测试。助手将当前源码与 Maven 配置复制到隔离临时目录，用 Java 21 执行测试，**10 个正式 JUnit 全部通过，失败、错误、跳过均为 0**：原有标题测试 6 个、文件测试 2 个、新增仓库测试 2 个。这里明确记为助手对当前代码的复核；我没有另外回报这两个新测试的独立运行结果。

原有 8 个测试仍然保留。新增的 2 个属于同一套正式测试，和前面的 Demo、手工切换坏文件、哈希比较分别统计。

这两个测试目前验证的是基本新增、查询和空结果，没有证明更新、重复新增、null 拒绝和返回列表隔离都已通过。四个仓库方法已经写在源码里，不等于每个分支已经完成测试。

## 14 今日进度和下一次从哪里接着做

| 范围 | 今日状态 |
| --- | --- |
| 自动编号和创建失败不增数据 | 已完成 Demo 验证 |
| 首次缺文件、读取失败、坏内容的区分 | 已实现并检查启动分支 |
| 字段、数字、状态、count、业务恢复的错误提示 | 已实现；各场景按 Demo 和运行反馈分别记录 |
| 两个进程之间的保存、恢复与继续编号 | 已完成，包含特殊字符和状态筛选 |
| 坏文件不被改写 | 我报告两个哈希比较为 True |
| 第二周理解检查 | 已完成 Map、编号、工作目录三项问答 |
| 第三周 Java/Maven 环境与包结构 | 已核对并完成构建，环境调整仅限当时会话 |
| 接口、内存实现与最初两个仓库测试 | 已进入练习，概念在示例中继续巩固 |
| Service 接入仓库、更多存储实现 | 尚未完成 |

下一次先补 `InMemoryTicketRepositoryTest` 的剩余场景：重复新增被拒绝且原数据不变、更新已有工单、更新不存在编号被拒绝、null 参数拒绝，以及返回列表增删不影响仓库条目。理解并验证这些约定后，再把 `TicketService` 改为依赖 `TicketRepository`。

第二周的本轮验收已完成，第三周刚开始接口和仓库职责练习。文件仓库实现、真正的可替换存储、后续数据库与 Web 接口都还没有完成，学习进度以当前实现和实际验收为准。
