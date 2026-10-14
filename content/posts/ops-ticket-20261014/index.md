---
title: "设备运维工单开发 03 多张工单存取与 Demo 自测"
description: "提取 TicketFileStore，理解 throw、throws 与 Reader，使用 count 保存和恢复多张工单，并在 Demo 中检查数量、字段和测试失败。"
date: 2026-10-14T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "文件读写", "异常处理", "测试", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 3
chapter_title: "多张工单存取与 Demo 自测"
---

> 这是“设备运维工单开发”系列第 3 篇，承接[上一篇的 Map 集合与单张工单恢复](/posts/ops-ticket-20261013/)。本文记录[Java 学习路线](/learning/)中当天实际完成的练习，当前项目说明见[项目文档](/learning/project-docs/)。此前的学生管理系统仍保留在[原系列](/series/#java)。

今天把文件读写从 Demo 中提取出来，再从一张工单扩展到多张工单。另一个变化是：我开始在 Demo 里写明确的检查条件，自己判断结果是否正确，而不只是看几行输出或等助手检查。

这些代码是在逐步提示下编写、根据反馈修正的。正常读取已运行通过，我也实际试过把预期编号改错，确认测试会报错；最后布置的“第二张工单缺标题”练习还没有完成，留到下次。

## 1 把文件操作交给 TicketFileStore

昨天，文件转换、读写和打印都挤在 Demo 中。今天把存取细节提取到 `TicketFileStore`：

| 类 | 现在负责什么 |
| --- | --- |
| `Ticket` | 一张工单的数据、业务校验和对象恢复 |
| `TicketService` | 管理内存里的多张工单，添加、查询和筛选 |
| `TicketFileStore` | 工单与 Properties 文件之间的转换和读写 |
| `TicketFileDemo` | 准备示例数据，调用保存并显示结果 |
| `TicketLoadDemo` | 调用读取，检查恢复结果并打印 |

我先提取了单张工单的 `save` 和 `load`，随后把保存参数改为列表，并实现返回列表的 `loadAll`。收尾时源码中使用的是：

```java
public void save(List<Ticket> tickets, Path path) throws IOException
public List<Ticket> loadAll(Path path) throws IOException
```

`TicketFileStore` 不再负责打印“读取失败”。它把结果返回给 Demo，或者把异常传给调用方，让调用方决定如何反馈。

## 2 throws 声明与 throw 执行不是一回事

我一开始把方法后面的 `throws IOException` 和方法体里的 `throw` 混在一起。

```java
public void save(List<Ticket> tickets, Path path) throws IOException {
    if (path == null) {
        throw new IllegalArgumentException("路径不能为null");
    }
    // 后面执行文件写入
}
```

- `throws IOException` 写在方法声明里，表示这个方法可能把文件读写异常传给调用方；写了声明不代表每次执行都会抛异常。
- `throw new ...` 是实际执行的语句。条件满足、执行到它时，当前正常执行路径就被中断。
- 即使方法里没有自己写 `throw new IOException(...)`，调用的文件 API 也可能抛出 IOException，再由本方法向外传递。

IOException 是受检异常，调用方通常需要捕获它，或者继续声明抛出。IllegalArgumentException 是运行时异常，不要求在方法声明里列出。

Demo 用两个分支区分故障：

```java
try {
    List<Ticket> tickets = store.loadAll(path);
    // 检查并打印读取结果
} catch (IOException e) {
    System.out.println("读取失败：" + e.getMessage());
} catch (IllegalArgumentException e) {
    System.out.println("存档内容不合法：" + e.getMessage());
}
```

例如文件不存在会进入第一种；必要字段缺失、编号无法转换或业务校验不通过，会进入第二种。NumberFormatException 也是 IllegalArgumentException 的子类。

## 3 Path、Reader 和两个 load 各做什么

今天我问过：“path 自带的 load 和我写的是两个不一样的吗？”实际需要先看调用点左边的对象是什么。

```java
Properties loaded = new Properties();

try (BufferedReader reader =
         Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
    loaded.load(reader);
}
```

| 名称 | 含义 |
| --- | --- |
| `path` | Path 对象，描述文件位置；它没有这里所说的 load 方法 |
| `reader` | 局部变量，引用一个 BufferedReader，按 UTF-8 将文件字节解码成字符 |
| `loaded` | Properties 对象，用来容纳解析出的字符串键值 |
| `loaded.load(reader)` | Java 提供的 Properties 方法，从 Reader 读取并解析键值 |
| `store.loadAll(path)` | 自己写的方法，还要检查字段、转换类型并恢复工单列表 |

`reader` 只是变量名，不是 Java 关键字。`try (...)` 的资源管理写法会在结束时关闭 Reader，包括读取过程中发生异常的情况。

文件里有字符串，并不等于内存里已经有 Ticket。数据还要经过后续的解析和校验。

## 4 用列表保存多张工单

为了拿到服务中的全部工单，我增加了：

```java
public List<Ticket> findAll() {
    return new ArrayList<>(ticketsById.values());
}
```

它返回一个新列表，清空这个列表不会删除服务中的记录；列表里的 Ticket 仍引用原来的对象。这和前一天的状态筛选结果一样，不是把每张工单都复制了一遍。

保存 Demo 创建两张工单，加入服务后调用：

```java
Path path = Paths.get("tickets.properties");
store.save(service.findAll(), path);
```

在 `save` 内部，先检查列表和路径，再按序号生成键：

```java
Properties data = new Properties();
data.setProperty("count", Integer.toString(tickets.size()));

for (int i = 0; i < tickets.size(); i++) {
    Ticket ticket = tickets.get(i);
    if (ticket == null) {
        throw new IllegalArgumentException("工单列表中不能为null");
    }

    String prefix = "ticket." + i + ".";
    data.setProperty(prefix + "id", Long.toString(ticket.getId()));
    data.setProperty(prefix + "title", ticket.getTitle());
    data.setProperty(prefix + "status", ticket.getStatus().name());
    if (ticket.getAssigneeId() == null) {
        data.setProperty(prefix + "assigneeId", "");
    } else {
        data.setProperty(prefix + "assigneeId",
                Long.toString(ticket.getAssigneeId()));
    }
}

try (BufferedWriter writer =
         Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
    data.store(writer, "Ticket demo");
}
```

这里的 `ticket.0`、`ticket.1` 是记录序号，不是工单编号。若每轮都使用固定的 `ticket.0.id`，后面的值就会覆盖前面的值。

我还问过保存时是否需要再检查 title 为 null。在当前 Ticket 的公开接口下，创建和修改标题已经统一校验，所以这里检查列表、列表元素和路径；不重复实现标题规则。读取文件时的数据来自外部，仍必须检查缺字段并通过恢复入口校验。

所有字段准备好后才打开 Writer，能避免列表中途发现 null 时已经覆盖文件。但真正开始写入后的 I/O 失败保护尚未实现，不能把这点当作完整的原子保存。

## 5 count 现在真正参与读取了

单张 Demo 时只读 `ticket.0`，count 没有参与控制流程。扩展到多张后，它决定循环次数：

```java
String countText = loaded.getProperty("count");
if (countText == null) {
    throw new IllegalArgumentException("存档缺少工单数量");
}

int count = Integer.parseInt(countText);
if (count < 0) {
    throw new IllegalArgumentException("工单数量不能为负数");
}
```

count 为 0 时循环不执行，方法返回空列表。缺少 count、负数或无法解析的文本则被拒绝。这些规则已经写入源码，但今天没有逐一完成对应的存档测试。

循环恢复的关键代码是：

```java
List<Ticket> result = new ArrayList<>();

for (int i = 0; i < count; i++) {
    String prefix = "ticket." + i + ".";
    String idText = loaded.getProperty(prefix + "id");
    String title = loaded.getProperty(prefix + "title");
    String statusText = loaded.getProperty(prefix + "status");
    String assigneeText = loaded.getProperty(prefix + "assigneeId");

    if (idText == null || title == null
            || statusText == null || assigneeText == null) {
        throw new IllegalArgumentException("存档缺少必要字段");
    }

    long id = Long.parseLong(idText);
    TicketStatus status = TicketStatus.valueOf(statusText);
    Long assigneeId;
    if (assigneeText.isEmpty()) {
        assigneeId = null;
    } else {
        assigneeId = Long.valueOf(assigneeText);
    }

    result.add(Ticket.restore(id, title, status, assigneeId));
}

return result;
```

我问“restore 存的是什么”时，进一步分清了两件事：`Ticket.restore(...)` 创建并还原一个内存对象；`result.add(...)` 把这个对象的引用加入列表。restore 本身不写文件。

恢复入口内部先检查状态与处理人组合，再通过 `new Ticket(id, title)` 复用编号和标题校验，设置合法的状态和处理人，最后返回对象。保存前后字段相同，不代表它们是同一个内存对象。

如果第二张工单出错，循环里的异常会让方法在 `return result` 之前结束，调用者拿不到只包含第一张工单的正常返回值。当前仍未将这个列表整体装入 TicketService，服务替换和失败保护要继续实现。

## 6 Demo 报错的两个原因

改造 `TicketLoadDemo` 时，我把读取和循环输出放进去，却遗漏了外层 `try {`，留下了跟在 for 后面的 catch。

正确嵌套关系是：

```java
try {
    List<Ticket> tickets = store.loadAll(path);
    for (Ticket ticket : tickets) {
        // 输出每张工单
    } // 结束 for
} catch (IOException e) { // 结束 try 后处理异常
    System.out.println("读取失败：" + e.getMessage());
} catch (IllegalArgumentException e) {
    System.out.println("存档内容不合法：" + e.getMessage());
}
```

另一个问题是文件名：保存用 `tickets.properties`，读取却写成了 `ticket.properties`，少一个 s。前一个问题属于编译错误；文件名不一致则可能导致运行时找不到文件或读错文件。

修正后，读回了两张工单：

```text
读回数量：2
1001 | 投影仪无信号 | IN_PROGRESS | 20
1002 | 打印机卡纸 | OPEN | null
```

## 7 Demo 也能测试，但要明确谁判断结果

今天讨论了一个问题：既然每次写完都要测试，那之前写的 Demo 不就是测试代码吗？

Demo 确实可以用来测试。最初的方式是准备数据、调用方法、打印输出，再由我对照预期判断。现在增加明确的判断条件，让代码自己发现结果不一致。

数量先检查，再访问下标，避免没读到两张工单时直接 get(1)：

```java
if (tickets.size() != 2) {
    throw new AssertionError("应该读回2张工单，实际为：" + tickets.size());
}
```

接着检查字段，下面是正常验收应使用的预期值：

```java
Ticket first = tickets.get(0);
if (first.getId() != 1001L
        || !"投影仪无信号".equals(first.getTitle())
        || first.getStatus() != TicketStatus.IN_PROGRESS
        || !Long.valueOf(20L).equals(first.getAssigneeId())) {
    throw new AssertionError("第一张工单的数据恢复不正确");
}

Ticket second = tickets.get(1);
if (second.getId() != 1002L
        || !"打印机卡纸".equals(second.getTitle())
        || second.getStatus() != TicketStatus.OPEN
        || second.getAssigneeId() != null) {
    throw new AssertionError("第二张工单的数据恢复不正确");
}

System.out.println("测试通过：两张工单的所有字段都正确");
```

`||` 表示任意一项不符合预期就失败。编号是 long，可以直接比较；处理人是允许 null 的 Long，已派单时用确定非空的 `Long.valueOf(20L).equals(...)` 比较数值，未派单时直接检查 `!= null`。

`null` 不加引号；`"null"` 是字符串，也不是空字符串 `""`。第二张工单预期没有处理人，所以“处理人不为 null”才是失败条件。

AssertionError 不会被现有的 IOException 和 IllegalArgumentException 两个 catch 捕获。因此检查失败时程序会报错，后面的“测试通过”不会执行。这里是显式抛出 AssertionError，不依赖 Java `assert` 关键字，也不需要启用 `-ea`。

正常场景在检查时重新编译运行通过。我还临时修改了预期编号，确认出现“第一张工单的数据恢复不正确”。这一步是在验证测试确实能发现错误。

收尾核对时，磁盘上的预期编号仍是用于故意失败的 `999L`。上面的示例使用正确的 `1001L`；下次先确认改回并保存，再运行正常验收，不能把故意失败版当作当前全绿的状态。

当前没有引入 JUnit 或 Maven。Demo 已有可重复执行的正常场景断言，但 IOException 和 IllegalArgumentException 仍只是被打印，并没有统一转成失败退出状态，所以还不是可直接用于 CI 的完整测试套件。

## 8 Git 与学习记录的小结

提取文件类和完善加载异常提示后，我完成了本地提交“提取工单文件存储类并完善加载异常提示”。后续的多张工单和断言修改仍有未提交内容，不能把前一次 commit 当作保存了全部新进度。

`git add src README.md docs` 时出现过 LF 将替换成 CRLF 的警告。这是换行符转换提示，不是中文内容乱码，也不代表暂存失败。可以继续用 git status 核对暂存区内容。

博客学习栏目今天增加了按实际练习记录的[学习时间线](/learning/#progress)。我最终选择主动提出整理请求，再按固定规则同步笔记、时间线和项目文档，没有启用定时自动发文。时间线的“当日已复盘”表示已整理当天记录，不等于全部内容都能独立完成。

## 9 今天完成到哪里，下次从哪里继续

| 内容 | 实际进度 |
| --- | --- |
| 文件存储类提取 | 按步骤完成，理解调用方与文件类的职责 |
| throw、throws、Reader | 结合调用过程讲解，并在代码中使用 |
| findAll 与多张保存 | 已实现，服务列表中的两张工单已保存 |
| count 与 loadAll | 按提示实现，多张工单正常读取通过 |
| 正常场景断言 | 数量、顺序和字段检查通过；错预期值能触发失败 |
| 缺字段坏文件测试 | 已讲解操作步骤，尚未创建并验收对应 Demo |
| 空列表、异常 count 的专项测试 | 代码已有相关行为，专项测试待补 |
| 重复编号、整体恢复服务、写入失败保护 | 待实现 |

下一次先确认正常 Demo 的预期编号已经恢复为 1001，再复制一份 `tickets.properties` 为 `tickets-invalid.properties`，删除副本中的整行 `ticket.1.title`。不要只清空标题，也不要改坏正常存档。

计划编写 `TicketLoadFailureDemo`：缺字段时应该抛出“存档缺少必要字段”；如果正常返回，测试反而失败；找不到文件的 IOException 不能算作成功拦截坏内容。还要临时补回标题，确认这份异常测试也能识别“本应失败却成功”的情况。

这个练习尚未完成，记录下来是为了下次接着做。之后再测试空列表和异常 count，最后把恢复出的工单完整交给服务管理。
