---
title: "设备运维工单开发 — 02 Map 集合与工单存档恢复"
description: "完成状态筛选和 Map 改造，通过 UTF-8 Properties 文件保存、读取并恢复工单，理解集合引用、类型转换和恢复校验。"
date: 2026-10-13T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "集合", "文件读写", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 2
chapter_title: "Map 集合与工单存档恢复"
---

> 这是“设备运维工单开发”系列第 2 篇，承接[上一篇的工单封装、Git 与派单规则](/posts/ops-ticket-20261012/)。项目对应博客的[Java 实习学习路线](/learning/)，最新功能说明见[项目文档](/learning/project-docs/)。学生管理系统的旧笔记仍保留在[原系列](/series/#java)。

今天从按状态筛选继续，先把工单集合改为按编号管理，再完成单张工单的文件保存、读取、类型转换与对象恢复。

最终跑通的过程是：

```text
Ticket 对象 → Properties 字符串字段 → UTF-8 文件
UTF-8 文件 → Properties 字符串字段 → 类型转换 → Ticket.restore → 新的 Ticket 对象
```

代码是在逐步提示下编写、经检查和运行验证完成的。下面记录实现过程与需要继续巩固的知识，不把跟写通过当作已经能独立设计完整的持久化模块。

## 1 按状态筛选返回什么

上一课只留下了 findByStatus 的方法骨架。今天补齐了参数检查、遍历和返回值：

```java
public List<Ticket> findByStatus(TicketStatus status) {
    if (status == null) {
        throw new IllegalArgumentException("工单状态不能为null");
    }
    List<Ticket> result = new ArrayList<>();
    for (Ticket ticket : ticketsById.values()) {
        if (ticket.getStatus() == status) {
            result.add(ticket);
        }
    }
    return result;
}
```

这里展示的是完成 Map 改造后的版本。没有匹配项就返回空列表；return 放在循环结束后，才能收集所有匹配的工单。TicketStatus 是枚举，可以直接用 == 比较枚举值。

写出方法还不等于运行时会看到结果。Demo 需要调用方法、接收结果，并明确打印或检查；Java 不会自动把返回值显示在控制台。

## 2 新列表和新工单是两回事

我一度想把引用关系概括为“没有 new 就指向同一个对象”，后来发现这个判断不够准确：调用处没有写 new，方法内部仍可能创建并返回新对象。

在 findByStatus 中，每次调用都会执行：

```java
List<Ticket> result = new ArrayList<>();
```

所以两次查询得到两个不同的列表。但是加入列表时：

```java
result.add(ticket);
```

保存的是已有工单的引用，没有复制工单。

| 操作 | 结果 |
| --- | --- |
| 清空查询结果列表 | 不会清空服务内部的集合 |
| 再次调用查询方法 | 会重新创建列表，重新收集匹配项 |
| 对列表里的工单调用 rename | 服务中同一张工单的标题也会改变 |
| 比较列表里的工单与编号查询结果 | 可以是同一个对象，引用比较为 true |

Demo 中的实际输出包括：

```text
清空前：1
结果列表：0
重新查询：1
重新查询标题：打印机卡纸
是否同一对象：true
```

这也不代表结果列表会自动更新：如果之后改变工单状态，列表中的对象能显示新状态，但列表不会自动重新筛选成员。需要再次调用 findByStatus。

## 3 用 Map 按工单编号管理

工单编号是业务标识，不是列表下标。今天把原来的列表管理改成：

```java
private final Map<Long, Ticket> ticketsById = new LinkedHashMap<>();
```

Map 是接口，描述键值映射的操作；LinkedHashMap 是具体实现。这里的键是工单编号，值是工单对象。泛型类型参数不能直接写基本类型 long，所以使用 Long；传入 long 编号时 Java 会自动装箱。

| 方法 | 当前用途 |
| --- | --- |
| get(id) | 按编号取工单；当前服务中找不到就返回 null |
| containsKey(id) | 判断编号是否已存在 |
| put(id, ticket) | 保存编号与工单的对应关系 |
| values() | 取得值的集合视图，供状态筛选遍历 |

findById 不再手动循环：

```java
public Ticket findById(long id) {
    return ticketsById.get(id);
}
```

新增时仍然必须先检查：

```java
public void add(Ticket ticket) {
    if (ticket == null) {
        throw new IllegalArgumentException("工单不能为null");
    }
    if (ticketsById.containsKey(ticket.getId())) {
        throw new IllegalArgumentException("工单编号已存在");
    }
    ticketsById.put(ticket.getId(), ticket);
}
```

put 本身允许覆盖同一个键的旧值，拒绝重复编号是项目的业务规则。

当前使用默认的 LinkedHashMap，遍历按插入顺序进行。例如依次加入 3003、1001、2002，遍历也按这个顺序，不会自动按编号大小排序。values() 是关联原 Map 的视图，不能把它当作独立副本随意 clear。

final 限制字段重新指向另一个 Map，不禁止向当前 Map 添加数据。当前实现仍是单线程练习，containsKey 再 put 不构成并发安全的新增操作。

## 4 Properties 保存的是字符串字段

Properties 可以用键值对组织数据。当前练习只使用 setProperty 和 getProperty，将键和值都按字符串处理：

```java
Properties data = new Properties();
data.setProperty("count", "1");
data.setProperty("ticket.0.id", Long.toString(ticket.getId()));
data.setProperty("ticket.0.title", ticket.getTitle());
data.setProperty("ticket.0.status", ticket.getStatus().name());

if (ticket.getAssigneeId() == null) {
    data.setProperty("ticket.0.assigneeId", "");
} else {
    data.setProperty("ticket.0.assigneeId",
            Long.toString(ticket.getAssigneeId()));
}
```

这里的编号要转换为字符串，枚举用 name() 保存名称。未派单时处理人保存为空字符串，不能直接给 setProperty 传 null。

约定的逻辑内容如下，实际保存时键的顺序可能不同：

```properties
count=1
ticket.0.id=1001
ticket.0.title=投影仪无信号
ticket.0.status=IN_PROGRESS
ticket.0.assigneeId=20
```

ticket.0 中的 0 是第 0 条记录的序号，真正的工单编号在对应的 id 值中。带点的键只是命名约定，不会自动创建嵌套对象或数组。

setProperty 只修改内存中的 Properties，此时还没有写入文件。它保存的是字段当时的字符串值，后续修改 Ticket 也不会自动更新这些值。

## 5 用 Writer 把字段写入文件

TicketFileDemo 先创建编号 1001 的工单，再派给工程师 20。字段准备好后执行：

```java
Path path = Paths.get("ticket-demo.properties");

try (BufferedWriter writer =
             Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
    data.store(writer, "Ticket demo");
} catch (IOException e) {
    System.out.println("保存失败：" + e.getMessage());
    return;
}

System.out.println("保存成功：" + path.toAbsolutePath());
```

Path 表示文件路径；BufferedWriter 负责写字符；store 才真正把 Properties 的内容写出去。第二个参数是文件注释，不是文件名。

try 后面括号中声明的资源会在离开代码块时自动关闭。catch 中的 return 则保证写入失败后不会继续打印“保存成功”。

相对路径根据程序的工作目录解析，不是根据 Java 源文件的位置。运行保存和读取 Demo 时，要确认它们使用同一工作目录。

目前保存会覆盖同名文件，且没有临时文件替换或备份机制。这是单张工单的演示代码，后续保存整个集合时还需要处理写入失败对旧存档的影响。

## 6 中文乱码要先判断发生在哪一层

今天遇到标题中文显示乱码。检查发现实际文件已经是正确的 UTF-8，问题出在 IDEA 查看 Properties 文件时使用的编码。将 Properties 文件编码设置为 UTF-8，并按正确编码重新加载后，显示恢复正常。

这次经验是先区分：

- Java 源文件是否正确保存。
- 写文件时使用什么编码。
- 读文件时使用什么编码。
- IDE 或终端用什么方式显示内容。

不要看到乱码就直接把乱码文字重新保存。当前代码通过 Reader 和 Writer 显式指定 UTF-8；不能把它与 Properties 的字节流重载混为一谈。

## 7 用 Reader 读回字段

TicketLoadDemo 中先加载文件：

```java
Path path = Paths.get("ticket-demo.properties");
Properties loaded = new Properties();

System.out.println("读取文件：" + path.toAbsolutePath());

try (BufferedReader reader =
             Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
    loaded.load(reader);
} catch (IOException e) {
    System.out.println("读取失败：" + e.getMessage());
    return;
}
```

load 把文件里的键值读入 loaded，不会自动生成 Ticket。

随后取出必要字段：

```java
String idText = loaded.getProperty("ticket.0.id");
String title = loaded.getProperty("ticket.0.title");
String statusText = loaded.getProperty("ticket.0.status");
String assigneeText = loaded.getProperty("ticket.0.assigneeId");

if (idText == null || title == null
        || statusText == null || assigneeText == null) {
    throw new IllegalArgumentException("存档缺少必要字段");
}
```

这里不能把 null 和空字符串当作同一回事：

| 文件情况 | getProperty 的结果 | 本项目含义 |
| --- | --- | --- |
| 没有处理人这个键 | null | 缺少必要字段 |
| 写着 ticket.0.assigneeId= | 空字符串 | 未派单，没有处理人 |
| 写着 ticket.0.assigneeId=20 | 字符串 "20" | 需要转换并校验的处理人编号 |

只有确认 assigneeText 不为 null，后面调用 isEmpty() 才安全。

## 8 字符串还需要转换成类型

getProperty 读到的 "1001" 是 String。转换代码如下：

```java
long id = Long.parseLong(idText);
TicketStatus status = TicketStatus.valueOf(statusText);

Long assigneeId;
if (assigneeText.isEmpty()) {
    assigneeId = null;
} else {
    assigneeId = Long.valueOf(assigneeText);
}
```

Long.parseLong 返回基本类型 long；Long.valueOf(String) 返回包装类型 Long。处理人允许为 null，因此使用 Long。

TicketStatus.valueOf 要求名称匹配枚举定义，包括大小写。非法数字会导致 NumberFormatException，不存在的枚举名称会导致 IllegalArgumentException。

类型转换通过不代表业务合法。例如 "-1" 可以解析为 long，但不能作为合法工单编号。

当前代码只在文件读取处捕获 IOException；缺字段、非法数字、非法枚举或恢复校验失败的异常仍会向外抛出。友好地报告坏存档并保留原服务数据，是后续加载器要完成的工作。

## 9 用恢复入口保留原状态

只执行 new Ticket(id, title)，对象会使用初始的 OPEN 状态和空处理人。这适合新建工单，却不能完整恢复已经派单的存档。

在 Ticket 类中增加：

```java
public static Ticket restore(long id, String title,
                             TicketStatus status, Long assigneeId) {
    if (status == null) {
        throw new IllegalArgumentException("工单状态不能为null");
    }

    if (status == TicketStatus.OPEN) {
        if (assigneeId != null) {
            throw new IllegalArgumentException("待派单工单不能有处理人");
        }
    } else {
        if (assigneeId == null || assigneeId <= 0) {
            throw new IllegalArgumentException("已派单工单必须有有效处理人");
        }
    }

    Ticket ticket = new Ticket(id, title);
    ticket.status = status;
    ticket.assigneeId = assigneeId;
    return ticket;
}
```

这是一个静态工厂方法，可以通过 Ticket.restore(...) 调用。方法内部的 new 才创建对象，最后 return 把新对象的引用交给调用方。

new Ticket(id, title) 复用构造器的编号和标题检查；恢复方法额外检查状态和处理人是否匹配。它位于 Ticket 类内部，所以能访问该类对象的 private 字段。static 方法没有 this，这里通过局部变量 ticket 指明要操作的对象。

assigneeId == null || assigneeId <= 0 使用短路求值：左边成立时不执行右边，避免对 null 自动拆箱。

当前约定 OPEN 必须没有处理人，另外三种状态必须有正数处理人编号。恢复 RESOLVED 或 CLOSED 只是在重建存档状态，不表示项目已经实现“提交处理结果”或“验收关闭”的业务方法。恢复入口将来用于持久化层，不应直接暴露为可任意设置状态的业务接口。

## 10 从恢复后的对象读取结果

最后在 TicketLoadDemo 中调用：

```java
Ticket restored = Ticket.restore(id, title, status, assigneeId);

System.out.println("编号：" + restored.getId());
System.out.println("标题：" + restored.getTitle());
System.out.println("状态：" + restored.getStatus());
System.out.println("处理人：" + restored.getAssigneeId());
```

实际输出：

```text
编号：1001
标题：投影仪无信号
状态：IN_PROGRESS
处理人：20
```

这次输出取自恢复后的对象。它和保存前的工单具有相同字段，但属于重新创建的对象；文件没有保存 Java 对象在内存中的引用。

本次检查编译了全部源码，并在助手创建的临时验证程序中完成 21 项恢复检查，全部通过：

- 四种状态与合法处理人组合能够恢复，编号和标题保持预期。
- null 状态、OPEN 带处理人被拒绝。
- 其他三种状态的处理人为 null、0 或负数时被拒绝。
- 0 和负数工单编号、null 或空白标题被拒绝。
- 50 长度标题可以恢复，51 长度标题被拒绝；标题首尾空格会被清除。

读取前后的示例存档哈希一致，读取没有修改原文件。这些是助手运行的临时检查，当前仓库还没有 JUnit 测试套件，也没有逐项修改坏文件来验证整个加载流程。

## 11 把项目文档跟上代码

今天给项目补齐了 README 和三份 docs 文档，并同步到了博客学习板块：

- [项目概览](/learning/project-docs/)：当前能力、目录和运行入口。
- [需求与开发计划](/learning/project-requirements/)：业务规则、功能状态和里程碑。
- [设计与数据约定](/learning/project-design/)：方法契约、引用关系、文件格式。
- [运行与验收](/learning/project-verification/)：运行方式、预期输出与验收范围。

学习笔记保存当天的过程和理解；项目文档随当前代码更新。以后读到历史文章中的旧实现，要结合当天阶段理解，不要求把过去的笔记全部改成最新代码。

## 12 今天完成到哪里

| 内容 | 实际进度 |
| --- | --- |
| 状态筛选 | 按步骤完成，参数、匹配结果和列表独立性经检查通过 |
| Map 改造 | 按步骤完成，编号查询、重复编号拒绝与插入顺序经检查通过 |
| Properties 字段转换 | 经提示修正，支持已派单和未派单的字段表达 |
| UTF-8 文件写入与读取 | 单张示例工单运行通过，中文显示问题已解决 |
| 类型转换和对象恢复 | 按示例完成，实际读取与 21 项恢复检查通过 |
| 项目文档 | 已补齐并发布，结束时更新到对象恢复阶段 |
| 多张工单保存与加载 | 尚未实现，count 目前写入但没有读取使用 |
| 完整存档异常处理 | 尚未实现，解析异常仍向外抛出 |

下一次先把 Demo 中的文件读写抽取成专门的持久化类，再逐步接入 TicketService 和多张工单。需要继续练习的是独立组织“读字段、转类型、校验、恢复对象”的顺序，以及加载失败时不污染原有数据。

复习时可以先合上代码回答三个问题：为什么清空结果列表不影响服务集合？为什么空处理人和缺字段要分开处理？为什么恢复入口仍然要调用构造器？
