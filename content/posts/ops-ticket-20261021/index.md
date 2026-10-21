---
title: "设备运维工单开发 — 06 仓库切换与控制台交付"
description: "把第三周尚未归档的学习合并记录：仓库契约、构造器注入、文件自动保存与恢复、控制台交互、可执行 JAR、Lambda 和 Map 两数之和，以及两种仓库的共用流程验收。"
date: 2026-10-21T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "接口", "集合", "文件读写", "异常处理", "JUnit", "Maven", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 6
chapter_title: "仓库切换与控制台交付"
---

> 本篇按 **2026 年 10 月 21 日**归档，合并记录[10 月 17 日笔记](/posts/ops-ticket-20261017/)之后已经学过、但尚未整理成文的内容，不把这些学习虚构成同一天完成，也不拆分推测中间每天的经历。课程路线见[学习栏目](/learning/)，当前代码的运行方法和边界见[项目文档](/learning/project-docs/)。

上一篇停在仓库接口入门：内存仓库已经出现，但还没有接入 `TicketService`。这一段学习把它真正接了进去，再实现文件仓库、控制台菜单和可执行 JAR，最后用同一套业务流程验证两种仓库。

我中途有过两种困惑：一是测试写得很像，感觉一直在重复断言；二是类越来越多，分不清 `memory`、文件仓库和 Service 各自做什么。后面先把这些关系讲清楚，再往下做功能。这篇保留关键代码、疑问和验证边界，不把跟写、经指导修正、助手检查都算成独立完成。

## 1 仓库测试：值相同、对象相同和 Optional 是三件事

内存仓库继续实现四个约定：新增、按编号查询、查询全部、更新。新增重复编号应拒绝，更新不存在的编号也应拒绝；这些失败不能悄悄替换原来的数据。

更新测试使用了两个不同对象，但编号相同：

```java
Ticket original = new Ticket(1L, "投影仪无信号");
Ticket replacement = new Ticket(1L, "投影仪无法开机");

repository.add(original);
repository.update(replacement);

Ticket found = repository.findById(1L).orElseThrow();
assertSame(replacement, found);
assertEquals(1, repository.findAll().size());
```

我按要求注释过 `update`：测试确实失败；恢复后通过。这说明检查能发现“根本没有执行更新”的情况。

### assertEquals 和 assertSame 分别检查什么

```java
assertEquals("投影仪无法开机", found.getTitle());
assertSame(replacement, found);
```

第一句比较标题值；第二句检查是不是同一个对象。一般对象的 `assertEquals` 依据 `equals` 比较，不能把它理解成“自动比较全部字段”。当前 `Ticket` 没有重写 `equals`，若要明确表达引用相同，用 `assertSame` 更直接。

我写过类似下面的错误断言：

```java
assertSame(original, repository.findById(1L));
```

左边是 `Ticket`，右边却是 `Optional<Ticket>`。`Optional` 是表达“可能找到，也可能没找到”的容器，不能直接拿它和工单比引用。找到时先取出工单：

```java
assertSame(original, repository.findById(1L).orElseThrow());
```

查不到时则检查容器为空：

```java
assertTrue(repository.findById(999L).isEmpty());
```

`orElseThrow()` 表示没有结果就抛异常；测试本来预期有这张工单时，缺失就应该使测试失败。`orElse(null)` 则表示没有结果时返回 `null`，它与前者的失败方式不同。

### 返回列表的隔离，只隔离列表结构

`findAll()` 返回 `new ArrayList<>(ticketsById.values())`。新列表与仓库不是同一个集合，所以：

```java
List<Ticket> result = repository.findAll();
result.clear();
```

清空的是返回的列表，仓库里的记录仍然存在。但列表里的元素没有被逐个复制，工单对象仍可能是仓库中的原对象。这不是深拷贝。

这一阶段仓库类实际保留 **7 个 JUnit 测试**：新增后查询、查询缺失、重复编号拒绝、正常更新、拒绝更新不存在编号、拒绝新增 `null`、返回列表结构隔离。`update(null)` 与已有练习类似，我选择跳过重复手写；实现中有对应校验，但没有新增这项测试，不能把它算进通过数量，也不继续记成没交的作业。

## 2 Service 接收仓库：传进来的是引用，不是复制数据

原先 `TicketService` 自己有 Map，新建的内存仓库也有自己的 Map。两个对象各管一份数据，因此向一个里面添加工单，另一个不会自动出现相同记录。

现在把 Service 自己的 Map 换成仓库字段：

```java
private final TicketRepository repository;

public TicketService(TicketRepository repository) {
    if (repository == null) {
        throw new IllegalArgumentException("仓库不能为null");
    }
    this.repository = repository;
}
```

调用方决定使用哪个仓库：

```java
TicketRepository repository = new InMemoryTicketRepository();
TicketService service = new TicketService(repository);
```

`this.repository = repository` 保存的是传入对象的引用。它没有 `new` 一个仓库，也没有把 Map 的内容复制到另一处。Service 后面的 `add`、`findAll` 等操作都委托给这个仓库。

这种由构造器接收依赖的写法，已经是构造器注入；目前是我手动组装对象，不需要 Spring 才能使用。

### 修改构造器以后，旧 Demo 为什么一起报错

原来的 `new TicketService()` 不再匹配新构造器，调用点都需要传入仓库。修改途中还存在变量名没有同步的问题。那次我明确请求助手直接修复，助手调整了这些调用并进行回归；不是我独立一次完成了所有迁移。

Service 仍保留原来的对外查询约定：

```java
public Ticket findById(long id) {
    return repository.findById(id).orElse(null);
}
```

所以当前仓库查不到返回空 `Optional`，Service 查不到返回 `null`。调用时要看清是哪一层的方法，不能只根据方法同名判断返回类型。

### 为什么改完对象，还要显式 update

标题和派单规则仍由 `Ticket` 负责，Service 串起“找工单、执行规则、更新仓库”的流程：

```java
Ticket ticket = findById(id);
if (ticket == null) {
    throw new IllegalArgumentException("工单不存在：" + id);
}

ticket.rename(newTitle);
repository.update(ticket);
```

内存仓库保存的是同一个对象引用，直接 `ticket.rename` 后，查出来可能已经是新标题。但文件仓库还需要知道这次修改，才能写回文件，所以 `update` 不能省掉。

这也暴露出测试的边界：只检查内存里标题变了，不一定能证明调用过 `update`。后面的文件重新加载，才补上“修改有没有真正保存”的行为验证。

Service 的两项 JUnit 分别验证了注入仓库里的最大编号能继续编号，以及修改标题后仓库中的结果。它们不是全部业务场景的完整覆盖。

## 3 文件仓库：复用内存仓库，再加保存与启动恢复

我最开始觉得 `FileTicketRepository` 只是又多出一个不明用途的类，后来把它拆开才理解：

| 类 | 当前职责 |
| --- | --- |
| `Ticket` | 一张工单的字段和规则 |
| `TicketService` | 创建、改标题、派单和查询的业务流程 |
| `TicketRepository` | 存储操作的共同接口 |
| `InMemoryTicketRepository` | 用 Map 管理运行期间的工单 |
| `TicketFileStore` | 将列表写成文件，或从文件恢复列表 |
| `FileTicketRepository` | 组合内存仓库与文件工具，接入自动保存和恢复 |

文件仓库有这几个字段：

```java
private final Path path;
private final TicketFileStore store = new TicketFileStore();
private final InMemoryTicketRepository memory =
        new InMemoryTicketRepository();
```

`memory` 是我给字段取的名字，它引用一个内存仓库对象，不是 Java 自带的特殊机制。

```text
启动：文件 → store.loadAll → memory 内部的 Map
查询：直接查 memory
新增或更新：先改 memory → 再保存当前全部工单
下次启动：用文件恢复一个新的 memory
```

### 为什么构造器使用 memory.add

构造器中读取文件，再逐张装入内存：

```java
try {
    List<Ticket> tickets = store.loadAll(path);
    for (Ticket ticket : tickets) {
        memory.add(ticket);
    }
} catch (NoSuchFileException e) {
    // 第一次使用，没有存档，保留空仓库
}
```

这里使用 `memory.add`，只恢复运行期间的数据。后面文件仓库自己的 `add` 会自动保存，如果恢复时也调用它，就会在装回数据的过程中反复写文件。

只有没有存档文件的 `NoSuchFileException` 按首次使用处理。其他读取错误继续向外传，坏数据的校验异常也继续向外传，不能一概忽略后当成空仓库启动。

### 新增和更新如何自动保存

```java
@Override
public void add(Ticket ticket) {
    memory.add(ticket);
    saveAll();
}

@Override
public void update(Ticket ticket) {
    memory.update(ticket);
    saveAll();
}
```

这里的 `saveAll` 是把目前全部工单写入文件，不是在文件尾部追加一张。创建、修改标题和派单都通过 Service 走到仓库后，最终结果才能持久保存。

重复运行自动保存 Demo 时，它每次都会执行 `service.create`。所以产生的是标题可能相同、编号继续增加的新工单，不是反复修改同一张；只想观察已有记录，应运行读取 Demo。

## 4 IOException 为什么包装成 UncheckedIOException

文件保存方法声明了：

```java
public void save(List<Ticket> tickets, Path path) throws IOException
```

`IOException` 是受检异常，调用它的代码要捕获或声明。但是仓库接口的约定是：

```java
void add(Ticket ticket);
```

这里没有声明 `throws IOException`。实现接口时，不能给这个方法额外加上调用方必须处理的新受检异常，所以文件仓库在内部捕获，再包装成运行时异常：

```java
private void saveAll() {
    try {
        store.save(memory.findAll(), path);
    } catch (IOException e) {
        throw new UncheckedIOException("保存工单失败：" + path, e);
    }
}
```

这不是把错误吃掉，也不表示不需要处理错误。它把受检异常转换成 `UncheckedIOException` 继续往外传，最终由控制台提示并退出。第二个参数 `e` 保留了底层原因，承接上一篇的异常链知识。

构造器不属于接口的那四个方法，当前 `FileTicketRepository(Path path)` 仍可以声明 `throws IOException`，让组装程序的启动代码负责处理读取失败。

还有一个实现边界必须记住：现在是先改内存、再保存文件。保存失败时，之前的内存修改不会自动撤销；写文件采用直接覆盖，也没有原子替换和备份。程序退出提示不等于已经实现事务。

## 5 控制台把菜单、业务和文件连接起来

`ConsoleApp` 是当前正式入口，菜单支持：创建、查看全部、修改标题、派单、按标题关键词查询和退出。

菜单只负责读输入、调用 Service、显示结果。标题长度和派单状态规则留在 `Ticket`，文件操作留在仓库与文件工具中，避免每个菜单分支各写一套校验和保存。

### 输入先按一整行读取

```java
long id = Long.parseLong(scanner.nextLine().trim());
```

先用 `nextLine()` 取一整行，去掉首尾空白，再转成编号。这里没有混用 `nextInt()`，也就避免了数字读取后遗留换行造成的下一次空输入。

我也问过菜单字符串里的 `\n`：

```java
System.out.println("\n1. 新建工单");
```

它是换行转义，不是要显示字母 `n`。`println` 本身还会在输出结尾换行，因此开头的 `\n` 让菜单前额外空一行。

### 不是每种失败都要退出程序

| 失败 | 当前处理 |
| --- | --- |
| 编号输入 `abc` | 提示输入整数，回到菜单 |
| 标题非法、编号不存在 | 提示业务错误，回到菜单 |
| 重复派单等状态错误 | 提示操作失败，回到菜单 |
| 保存文件失败 | 提示并停止运行 |
| 启动读取失败或坏存档 | 不进入菜单，停止启动 |

`NumberFormatException` 是 `IllegalArgumentException` 的子类，写多个 `catch` 时先放数字格式的具体分支，才能给出专门提示。保存失败分支捕获 `UncheckedIOException`；成功消息必须放在 Service 调用正常返回之后，不能先宣布成功再执行保存。

我反馈过修改标题、派单和重启后的数据都正常，输入 `abc`、重复派单也能回到菜单。这些是我手动运行的结果，不是 Maven 自动执行的测试。

### 关键词校验的顺序

最初关键词处理写错了检查顺序。先 `trim()` 再检查 `null`，会在检查之前就产生空指针异常；`trim()` 的结果也不靠与 `null` 比较来判断空白。

正确顺序是：

```java
if (keyword == null) {
    throw new IllegalArgumentException("关键词不能为null");
}
String trimmed = keyword.trim();
if (trimmed.isEmpty()) {
    throw new IllegalArgumentException("关键词不能为空");
}
```

再遍历仓库工单，用 `ticket.getTitle().contains(trimmed)` 筛选。当前是区分大小写的包含匹配，不是分词搜索；没有匹配时返回空列表。

查看全部与关键词结果原本重复写输出循环，后来提取成：

```java
private static void printTickets(List<Ticket> tickets)
```

列表为空时提示并 `return`，退出的是这个辅助方法，不是整个菜单程序；`main` 在调用完成后仍继续循环。

### 启动失败需要在菜单循环之前处理

启动代码先创建文件仓库和 Service。读取失败捕获 `IOException`，内容非法捕获 `IllegalArgumentException`，打印原因后从 `main` 返回。只有成功初始化后才创建菜单输入循环。

我用独立坏存档副本验证过内容非法会提示并退出，之后恢复正常路径。失败启动不能被解释成“没有数据”，也不能紧接着创建新工单覆盖掉原文件。

## 6 Maven 打包完成后，为什么还要配置入口

上一篇完成了普通 JAR 打包，这次在 `maven-jar-plugin` 中指定了应用入口：

```xml
<configuration>
    <archive>
        <manifest>
            <mainClass>cn.wishbottle.opsticket.ConsoleApp</mainClass>
        </manifest>
    </archive>
</configuration>
```

打包后，JAR 的 `META-INF/MANIFEST.MF` 包含：

```text
Main-Class: cn.wishbottle.opsticket.ConsoleApp
```

这样 `java -jar` 才知道从哪个类的 `main` 启动。当前业务代码只用 JDK 类库，JUnit 是测试依赖；这一步没有学习第三方运行依赖的整体打包方案。

在项目根目录，使用 JDK 21 和可用的 Maven 执行：

```powershell
mvn clean package
java -jar target/ops-ticket-0.1.0-SNAPSHOT.jar
```

如果终端不能识别 `mvn`，继续用 IDEA 的 Maven 面板或其 Maven 可执行文件。配置 `pom.xml` 的 Java 版本，不等于永久修改了终端实际使用的 JDK。

我报告了打包成功，`java -jar` 能显示菜单和已有工单；助手另外检查了产物里的入口和类文件，并执行过 Maven 打包与 17 项测试复核。

### 相对路径相对于工作目录

正式存档路径是：

```java
Paths.get("data", "tickets-app.properties")
```

它相对于启动进程时的工作目录，而不是自动相对于 JAR 所在目录。把 JAR 放在哪里和从哪里执行命令，是两件事。启动打印 `path.toAbsolutePath()`，就是为了直接核对实际读写位置。

目前保存方法不会创建父目录，所以运行前要保证 `data` 目录存在。换工作目录后找不到旧工单，先检查实际路径，不能直接认为保存逻辑失效。

## 7 Lambda：传入一段操作

关键词查询保留了普通循环。随后我只阅读了 Lambda 的等价例子，理解基本写法：

```java
repository.findAll().forEach(
        ticket -> System.out.println(ticket.getId())
);
```

`ticket` 是这段操作的参数，每次指向当前遍历到的工单，类型可从集合推断。集合有三张工单，就执行三次打印；这不会因为换成 Lambda 而复制或新建工单。

之前的异常断言其实已经用过：

```java
() -> repository.add(null)
```

空括号表示这段操作没有参数，交给断言方法稍后执行。`ticket -> ...` 则接收一个参数。菜单中 `case "1" -> ...` 的箭头属于 `switch` 语法，不因为长得相同就也是 Lambda。

这一阶段只是入门阅读和理解检查，没有把全部循环重写成 Lambda，也没有声称已经学完 Stream。

## 8 两数之和：从双循环到 Map

数组练习保留在 `ArrayPractice`，与业务代码分开。题目是找两个不同下标，使对应元素之和等于目标值；找到返回下标数组，找不到返回空数组，`null` 输入则抛异常。

双循环版本让 `j` 从 `i + 1` 开始：

```java
for (int i = 0; i < numbers.length; i++) {
    for (int j = i + 1; j < numbers.length; j++) {
        if (numbers[i] + numbers[j] == target) {
            return new int[]{i, j};
        }
    }
}
return new int[0];
```

这样不会让一个元素和自己配对，也不会把下标 `0、1` 与 `1、0` 重复比较。我运行 `{2, 7, 11, 15}`、目标 `9`，输出 `[0, 1]`。

### Map 存数字对应的下标

目标为 `9`，当前数字为 `7`，只需要知道前面是否出现过 `2`，以及它在哪个位置。因此 Map 的含义是：

```text
数字 → 之前出现位置的下标
```

这与之前数字计数练习的“数字 → 出现次数”不同。

```java
Map<Integer, Integer> seen = new HashMap<>();

for (int i = 0; i < numbers.length; i++) {
    int needed = target - numbers[i];
    if (seen.containsKey(needed)) {
        return new int[]{seen.get(needed), i};
    }
    seen.put(numbers[i], i);
}
return new int[0];
```

这里使用 `HashMap`，因为需要的是按 key 查找，不需要保留插入顺序。

关键是先查找再存入：Map 中只有前面位置的信息。同一个位置不能被使用两次，但两个位置的值可以一样。`{3, 3}`、目标 `6`，第一轮保存 `3 → 0`，第二轮就找到前面的 `3`，返回 `[0, 1]`。我运行了这个例子并得到预期输出。

双循环最坏时间复杂度是 `O(n²)`，Map 版本平均为 `O(n)`，代价是额外 `O(n)` 空间。这些例子验证了当前普通整数输入；极值整数的溢出边界没有在这次练习中系统展开。

## 9 同一段业务流程，切换两种仓库

我刚写到这里时，又混淆了一次“两种仓库”。重新理解后，可以用一句话说明：文件仓库是在内部内存仓库的基础上增加文件保存和启动恢复，两者对外遵守同一个接口。

所以共用方法的参数写接口：

```java
private static void runScenario(TicketRepository repository) {
    TicketService service = new TicketService(repository);
    Ticket ticket = service.create("投影仪无信号");
    service.rename(ticket.getId(), "投影仪无法开机");
    service.assign(ticket.getId(), 20L);
    // 查询并打印最终结果
}
```

同一个方法分别接收不同实现：

```java
runScenario(new InMemoryTicketRepository());

Path directory = Files.createTempDirectory("ops-ticket-check-");
Path path = directory.resolve("tickets.properties");
runScenario(new FileTicketRepository(path));
```

每次运行创建新的系统临时目录，不改动项目 `data` 中的已有工单。`resolve` 只是组合路径，真正创建文件发生在文件仓库第一次保存时。

两个仓库都从空数据开始，因此都得到编号 `1`，但它们属于各自独立的数据集合，不冲突。两次最终输出一致：

```text
1 | 投影仪无法开机 | IN_PROGRESS | 20
```

### 新建仓库，才能验证文件恢复

接着使用同一个路径，但新建一个文件仓库：

```java
TicketRepository reloadedRepository = new FileTicketRepository(path);
Ticket loaded = reloadedRepository.findById(1L).orElseThrow();
```

新仓库有新的内部 Map，构造器从刚才的文件读回工单。我不需要再次调用重命名、派单，也不需要在外面再手动调用 `loadAll`：前面的操作已经保存，构造器本身负责恢复。

这里不能重新调用 `runScenario`，因为它会再创建一张工单。预期只恢复刚才的一张，标题、状态和处理人不变，数量为 `1`。

我反馈两种仓库输出正常；助手在临时目录编译、运行过这个 Demo，复核两种实现与新仓库重新加载的结果。它验证的是同一进程内重新创建仓库；之前关闭控制台再启动的手动检查，才是实际结束程序后的恢复。两种证据不能混称。

## 10 交付说明、Git 和本轮验证

写完功能后，README 里“仓库尚未接入”“JAR 没有启动入口”等旧描述需要一起更新。我请助手根据当前代码同步 README、需求、设计和验收文档，明确了运行命令、数据位置和已知限制。

代码阶段已提交 `682b3c7`，随后项目文档提交 `ecc0f14`。提交前还遇到了 `AM`：文件先暂存过，之后又改了。暂存区不是自动跟随工作区变化，想提交最新内容，需要再执行 `git add`。

坏存档样本也是如此：工作区改成 `count=abc` 后，要再次暂存，才能提交真正用于失败验收的版本。不应该为了让 `git status` 变干净就把运行产生的所有文件都加入仓库。

当前保留的自动测试为：

| 测试类 | 数量 | 当前覆盖内容 |
| --- | --- | --- |
| `TicketTest` | 6 | 标题修改和校验 |
| `TicketFileStoreTest` | 2 | 临时目录中的空列表、多工单文件往返 |
| `InMemoryTicketRepositoryTest` | 7 | 部分仓库契约与列表结构隔离 |
| `TicketServiceTest` | 2 | 注入仓库后创建和修改标题 |
| 合计 | 17 | 已通过 Maven 复核 |

`mvn test` 不会自动运行每个带 `main` 的 Demo；仓库切换、菜单输入、JAR 启动的证据要分别记录。17 项通过也不等于所有文件故障和业务组合都已经自动覆盖。

现在仍存在这些边界：文件直接覆盖、没有原子替换或备份；保存失败不回滚内存；多进程操作同一个文件没有并发保护；列表里的工单仍可能共享引用。它们写进文档，并不代表此刻要提前把后面课程的所有机制做完。

### 本次一起检查了代码和目录规范

我这次还请助手检查项目结构，并修正已经发现的整理问题。当前 `src/main/java` 放业务实现，`src/test/java` 放 JUnit、Demo 与数组练习，`docs` 放文档，`data` 放存档和样本，这个阶段不需要为了形式再拆成很多包。

实际整理的是这些地方：

- 已完成的 `TODO` 改为普通说明，删除算法练习中仍写着“在这里补循环”的占位注释；否则读代码时容易误以为实现还没完成。
- 清理无用导入、把通配导入换成实际使用的类型，统一导入顺序、缩进、空行和文件末尾换行。
- 统一“工单不存在：编号”的错误消息，修正错字，以及文件存档注释被 IDE 重构成全限定类名的问题。
- 把 `Ticket` 字段集中到类前部，将创建后不再修改的 `id` 标记为 `final`，让编号不可重新赋值的约定由编译器约束。标题和状态仍然可通过业务方法改变，这不代表整个工单变成不可变对象。
- 旧的 IDEA 模块文件确认不再被活动 Maven 配置引用后，先备份再移出源码目录，保留当前有效的 IDE 配置。
- 精确忽略 `data/tickets-app.properties` 和 `data/tickets-auto-demo.properties` 两个运行存档，保留已有文件和其他正常、异常样本；没有用 `*.properties` 把教学样本一并排除。

这次没有改成另一套项目架构，也没有替换我的运行数据。整理后的改动需要与此前已经提交的学习代码区分开来。

### 整理后怎样复核

助手使用独立临时副本，以 JDK 21 执行 Maven 打包，17 项 JUnit 全部通过，并另外运行了以下检查：

- 仓库切换 Demo：两种实现输出一致，新文件仓库恢复出相同字段和一张工单。
- 数组 Demo：两种两数之和样例输出符合预期，原有最大值检查通过。
- 真正执行打包后的 JAR：创建、改标题、派单、关键词查询通过；非法数字、重复派单、空关键词和不存在编号得到提示，并能回到菜单。
- 结束一个 JVM，再启动新的 JVM：已有数据正确恢复，只读取时存档不发生变化。
- 临时坏存档的 `count=abc`：启动提示并停止，文件内容不被覆盖。

这些是助手在本次整理中新增执行的复核，补充了前面的手动反馈；它们没有变成项目里的新 JUnit 类，正式测试数量仍是 17。核对前后原项目的 Properties 文件内容和 Git 暂存区保持不变，验证没有占用真实存档来做破坏性试验。

## 11 下一次从数据库连接开始

前两周的基础和文件恢复已经完成验收；第三周的仓库接入、文件实现、控制台、JAR、关键词查询、Lambda 入门、两数之和和交付说明，已经完成这一阶段的学习与记录。

下一阶段是第四周 MySQL。当前只检查到本机有 MySQL、服务正在运行，并已确认客户端版本，尚未完成我本人登录、执行 SQL、创建练习数据库或设计表。不能因为系统安装了数据库，就把数据库学习记为完成。

下次先连接服务器，执行 `SELECT VERSION(), DATABASE();`，区分服务端版本与当前选中的数据库；然后创建项目专用练习库，再学习用户、设备、工单三张表。学习进度以实际完成和验证为准，不按日程日期自动跳到下一阶段。
