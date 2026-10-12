---
title: "设备运维工单开发 01 工单封装 Git 与派单规则"
description: "从工单构造器和标题校验开始，建立管理集合的服务类，学习 Git 保存版本，再用枚举和异常约束派单过程。"
date: 2026-10-12T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "面向对象", "Git", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 1
chapter_title: "工单封装 Git 与派单规则"
---

> **项目与系列说明**：从这篇开始，我将主要练习项目从“学生管理系统”切换到“设备运维工单平台”，开启“设备运维工单开发”系列，并从第 1 篇重新编号。这个项目对应博客[“学习”栏目中的 Java 实习学习计划](/learning/)：“学习”栏目提供整体路线、阶段任务和参考资料，本系列则记录我按计划做项目时写过的代码、遇到的问题、修正过程和实际进度，方便把学习计划与每天的实践对应起来。
>
> 前六篇仍保留在[“学生管理系统”系列](/series/#java)中。新项目会继续用到其中练习过的集合、文件读写和类的拆分，并逐步扩展到数据库、Web 接口和部署。

今天完成的是内存中的工单对象、添加与查询，以及把待派单工单分配给工程师的规则；同时第一次用 Git 保存了代码版本。这次重点是把规则放进合适的类、说明对象之间的关系，并检查失败后数据是否保持原样。

今天的笔记既记录通过的验证，也保留几次很具体的错误。按状态筛选只写了方法骨架，留到下次完成。

## 1 工单对象要从创建时就合法

第一张工单先有两个字段：编号 `id` 和标题 `title`。规则是编号大于 0，标题不能为 `null`，去掉两端空白后不能为空，长度不能超过 50。

之前讨论学生成绩时，我知道 `private` 可以防止其他类直接改字段，但今天进一步明确了：访问限制本身不会检查数值范围。如果构造器直接给字段赋值，创建对象时仍然可能放进非法数据。

所以构造器也要检查规则，标题校验则提取成一个方法，供创建和改名复用。下面是 `Ticket` 中的关键片段：

```java
private long id;
private String title;

public Ticket(long id, String title) {
    if (id <= 0) {
        throw new IllegalArgumentException("工单编号必须大于0");
    }
    this.id = id;
    this.title = validateTitle(title);
}

public void rename(String newTitle) {
    this.title = validateTitle(newTitle);
}

private String validateTitle(String title) {
    if (title == null) {
        throw new IllegalArgumentException("工单标题不能为null");
    }
    String trimmedTitle = title.trim();
    if (trimmedTitle.isEmpty()) {
        throw new IllegalArgumentException("工单标题不能为空");
    }
    if (trimmedTitle.length() > 50) {
        throw new IllegalArgumentException("工单标题不能超过50");
    }
    return trimmedTitle;
}
```

`validateTitle()` 不只判断合法性，还把处理后的标题返回。先判断 `null`，才能安全调用 `trim()`。当前练习用 `String.length()` 检查长度；它计算 UTF-16 代码单元，不能当作所有 Unicode 字符的精确个数。

我练习了编号为 0、标题为 `null`、空字符串、全空白，以及长度 50 和 51 的情况。合法标题先去掉两端空白，再存入对象。

## 2 this 指向当前对象

构造器参数和字段都叫 `id` 时：

```java
this.id = id;
```

左边的 `this.id` 是当前对象的字段，右边的 `id` 是传入的参数。如果写成 `id = id`，两边都指向参数，字段不会得到这个值。

在调试器中，我观察到执行赋值前 `this.id` 是默认值 0，执行后变成 1001。这个过程把“传入参数”和“把参数保存到对象里”区分开了。

## 3 两个变量可以指向同一个对象

下面这句没有创建第二张工单：

```java
Ticket alias = first;
```

它复制的是引用值。`first` 和 `alias` 指向同一个对象，因此通过任意一个变量改名，再通过另一个读取，都能看到新标题。这不是两个对象互相同步，而是访问的本来就是同一个对象。

如果再执行：

```java
alias = new Ticket(1002L, "打印机卡纸");
```

这次才创建另一张工单，并让 `alias` 指向它。`first` 仍指向原来的工单。

数组练习中也有同样的区别：`new Ticket[3]` 创建一个有三个位置的数组，三个元素最初都是 `null`，不会自动创建三张工单。需要分别执行 `new Ticket(...)`，再把引用放进数组。

## 4 校验失败时为什么旧标题还在

改名方法中的这句赋值有先后顺序：

```java
this.title = validateTitle(newTitle);
```

必须先调用右侧方法，正常得到返回值后，才会更新左侧字段。如果校验抛出异常，这次赋值就不会完成，所以原来的标题保留。

我在 `TicketPractice` 中创建两张工单，先合法修改第一张，再尝试把它改成全空白。异常捕获后继续读取，第一张的编号和原有合法标题仍在，第二张也没有受到影响。

`throw` 和 `return` 都可能让执行离开当前方法，但含义不同：`return` 正常返回；`throw` 抛出异常，执行流程转向匹配的异常处理代码。如果当前方法没有处理它，异常继续传给调用者。整个调用链都没有捕获时，当前线程因异常结束。

捕获后也不会回到失败的语句重试，而是继续执行对应 `try-catch` 后面的代码。

## 5 用 Git 保存第一批版本

今天初始化了 Git 仓库，并学习了三个位置的关系：

```text
工作目录中的修改 → git add → 暂存区 → git commit → 本地提交
```

项目根目录的 `.gitignore` 写入：

```gitignore
.idea/
out/
.qa/
*.class
```

这些分别是 IDE 配置、编译输出、临时验证产物和字节码文件。当前练习保留源码与项目说明，编译结果可以重新生成。

第一次查看状态时，`.gitignore` 同时出现在“准备提交”和“尚未暂存的修改”中。原因是它加入暂存区之后又被编辑了，暂存区还保留着之前的内容。重新执行 `git add`，才会更新暂存区中的版本。

实际练习过的命令包括：

```powershell
git status
git add .gitignore README.md src
git diff --cached
git commit -m "完成工单对象与标题校验"
git log --oneline
```

之后给 `rename()` 加注释，再查看差异、暂存和提交，得到第二个版本“补充标题修改方法说明”。`git diff` 默认比较工作目录与暂存区，`git diff --cached` 比较暂存区与当前提交。普通 `git commit` 保存暂存区内容，编辑器里按保存并不等于完成 Git 提交。

`git log --oneline` 显示简短提交编号和说明；`HEAD -> main` 表示当前位于 `main` 分支，指向该提交。用 `git show 提交编号:src/Ticket.java` 可以查看旧版本文件，不会改动当前源码。差异进入分页查看器后，空格翻页，`q` 退出。

这两次提交保存的是当时的工单对象与注释，后面新增的服务类和派单功能还没有新的提交记录。本地提交也不会自动上传到远程仓库。

今天还移动了项目目录。只要隐藏的 `.git` 随项目完整移动，就不需要重新执行 `git init`。IDEA 中文件名变成红褐色，在这次场景中表示文件尚未被 Git 跟踪；忽略目录仍被 IDE 索引的提示，则是另一个设置，不代表忽略规则失败。终端乱码与 Git 所有权检查也属于不同问题，不能靠改显示编码一起解决。

## 6 服务对象负责管理工单集合

`Ticket` 表示一张工单，`TicketService` 管理多张工单。服务内部有自己的集合：

```java
private final ArrayList<Ticket> tickets = new ArrayList<>();
```

`private` 让外部不能直接访问这个字段，新增统一经过服务的检查。`final` 限制的是字段重新指向另一个集合，不妨碍对现有集合执行 `add()`。

按编号查找的方法返回集合中原来的对象，找不到返回 `null`：

```java
public Ticket findById(long id) {
    for (Ticket ticket : tickets) {
        if (ticket.getId() == id) {
            return ticket;
        }
    }
    return null;
}
```

我的第一版 `add()` 遇到 `null` 或重复编号就直接结束，虽然没有加入坏数据，调用者却无法判断这次新增是否成功。修改后，先明确抛出异常，再在全部检查通过后加入集合：

```java
public void add(Ticket ticket) {
    if (ticket == null) {
        throw new IllegalArgumentException("工单不能为null");
    }
    if (findById(ticket.getId()) != null) {
        throw new IllegalArgumentException("工单编号已存在");
    }
    tickets.add(ticket);
}
```

这里复用了 `findById()`，避免把同样的查找再写一遍。编号唯一是当前服务集合内的约束，今天还没有接入数据库，也没有实现多线程同时新增的控制。

## 7 创建对象和加入集合是两步

写 Demo 时，我创建了服务和两张工单，却忘记把工单加入服务：

```java
TicketService service = new TicketService();
Ticket first = new Ticket(1001L, "投影仪无信号");
```

这时服务内部的集合还是空的。调用 `service.findById(1001L)` 会得到 `null`。因为当时我没有接收返回值，又直接操作 `first`，这个遗漏没有立刻表现为报错。

补上添加，再接住查找结果：

```java
service.add(first);
Ticket found = service.findById(1001L);
```

`add(first)` 把工单的引用加入集合，没有复制一张新工单。`found`、`first` 和集合中对应的元素都指向同一个对象。对于可能不存在的编号，需要先检查查找结果是否为 `null`，才能调用对象的方法。

## 8 用枚举和业务方法约束派单

工单状态用枚举表示：

```java
public enum TicketStatus {
    OPEN,          // 待派单
    IN_PROGRESS,   // 处理中
    RESOLVED,      // 待验收
    CLOSED         // 已关闭
}
```

`Ticket` 新增两个字段，并提供对应 getter：

```java
private TicketStatus status = TicketStatus.OPEN;
private Long assigneeId;
```

新工单默认 `OPEN`。处理人用 `Long`，允许以 `null` 表示尚未分配；基本类型 `long` 不能取 `null`。

今天只实现从 `OPEN` 到 `IN_PROGRESS` 的派单。其余两个状态先定义下来，处理和验收功能还没有写。状态变化由业务方法控制：

```java
public void assign(long engineerId) {
    if (engineerId <= 0) {
        throw new IllegalArgumentException("工程师编号必须大于0");
    }
    if (status != TicketStatus.OPEN) {
        throw new IllegalStateException("状态必须是OPEN");
    }
    this.assigneeId = engineerId;
    this.status = TicketStatus.IN_PROGRESS;
}
```

编号非法用 `IllegalArgumentException`；对象当前状态不允许派单，用 `IllegalStateException`。两项检查都在赋值之前，重复派单失败时就不会覆盖原处理人。这是当前单线程练习中的行为，后续接入数据库时还要处理并发派单。

## 9 Demo 的 main 是运行入口

我问过为什么要在 `TicketServiceDemo` 中写 `main`。这个类需要单独启动，组合调用其他类并观察结果，所以使用当前学习的标准入口：

```java
public static void main(String[] args) {
    // 创建对象，调用业务方法，打印验证结果
}
```

`Ticket` 和 `TicketService` 提供数据与功能，由入口调用，不要求各自拥有 `main`。多个 Demo 各有入口，是为了分别运行不同实验。之前的 `TicketDemo`、`TicketPractice` 和 `TicketArrayDemo` 先保留，后面学习自动化测试时再整理重复验证。

## 10 一次重复派单暴露了引用关系

第二版 Demo 中，我先执行：

```java
found.assign(20L);
```

随后又在 `try` 外写了：

```java
firstTicket.assign(20L);
```

虽然变量名不同，它们指向的工单相同。第一句已把状态改成 `IN_PROGRESS`，第二句就属于重复派单，即使工程师编号仍然是 20，也不符合当前规则。

这次异常发生在后面的 `try` 之前，因此那个 `catch` 接不到，程序直接结束了。删除多余调用后，把预期失败的第二次派单放进 `try`，并在捕获后重新查询：

```java
try {
    found.assign(30L);
} catch (IllegalStateException e) {
    System.out.println(e.getMessage());
}

Ticket after = ticketService.findById(1001L);
System.out.println(after.getStatus() + ", " + after.getAssigneeId());

Ticket secondFound = ticketService.findById(1002L);
System.out.println(secondFound.getStatus() + ", " + secondFound.getAssigneeId());
```

加上第一次成功派单后的打印，最终 Demo 的实际输出是：

```text
IN_PROGRESS, 20
状态必须是OPEN
IN_PROGRESS, 20
OPEN, null
```

它验证了三件事：第一次派单成功；第二次失败后原处理人仍是 20；另一张工单仍待派单。异常处理后的查询确实执行到了，而不是程序提前结束后凭印象判断结果。

## 11 今天完成到哪里

| 内容 | 实际进度 |
| --- | --- |
| 工单编号和标题校验 | 跟写后完成边界练习，独立重写仍待练习 |
| 对象引用与调试 | 观察过字段赋值；Demo 中再次遇到共享引用问题，修改后验证通过 |
| Git | 完成两次本地提交，练习差异、暂存、提交和历史查看 |
| 添加与按编号查询 | 按需求编写，异常反馈经提示修正后验证通过 |
| 枚举和派单 | 实现正数编号检查、状态检查和合法派单，失败时保留原数据 |
| 综合 Demo | 经几次反馈补齐添加、查询和异常处理，运行通过 |
| 按状态筛选 | 已添加方法骨架，尚未实现和验证 |

今天没有重新从循环语法开始学完整一遍。已有的集合经验直接用于新项目，遇到引用、返回值和异常执行顺序的问题，再沿着实际代码检查。接下来的目标是逐渐减少提示，自己把业务规则组织成可验证的代码。

## 12 下次从状态筛选继续

下一项方法的签名是：

```java
public List<Ticket> findByStatus(TicketStatus status)
```

它要拒绝 `null` 参数，创建新的结果列表，把状态匹配的工单加入后返回；没有匹配项时返回空列表。当前文件中只有空方法体，因此这份工作中的源码暂时会出现缺少返回值的编译错误。上面的 Demo 输出来自加入这个骨架前已通过验证的版本，下次先完成方法再继续运行。

筛选后要验证：`OPEN` 找到 1002，`IN_PROGRESS` 找到 1001，`CLOSED` 返回空列表。还要验证清空结果列表不会清空服务内部的集合。

结果列表和内部集合是两个容器，但其中的工单仍然可以是同一个对象的引用。这个区别正好把今天遇到的问题接到下一次练习里。
