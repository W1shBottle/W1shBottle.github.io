{
  "title": "工单项目设计与数据约定",
  "description": "类的职责、方法契约、状态规则与 Properties 存档格式。",
  "date": "2026-10-13T00:00:00+08:00",
  "lastmod": "2026-10-13T00:00:00+08:00",
  "weight": 180,
  "group": "project-docs",
  "draft": false
}

[返回项目首页](/learning/project-docs/) · [需求](/learning/project-requirements/) · [运行与验收](/learning/project-verification/)

核对日期：2026-10-13。本文先描述当前源码，待实现的约定会单独标明。

## 1. 当前结构

```text
TicketServiceDemo → TicketService → LinkedHashMap<Long, Ticket>
                                      ↓
                                   Ticket → TicketStatus

TicketFileDemo → Ticket → Properties → UTF-8 文件
TicketLoadDemo ← Properties ← UTF-8 文件
```

两个文件 Demo 独立运行，目前没有接入 TicketService，也没有数据库或网络层。

| 类 | 职责 |
| --- | --- |
| Ticket | 保存一张工单的数据，执行编号、标题和派单校验 |
| TicketStatus | 定义四种状态名称 |
| TicketService | 管理内存中的多张工单，添加、编号查询、状态筛选 |
| TicketDemo / TicketPractice | 对象创建、标题修改与异常的练习入口 |
| TicketArrayDemo | 早期数组遍历练习 |
| TicketServiceDemo | 服务调用、派单和查询结果引用关系的演示入口 |
| TicketFileDemo | 构造一张示例工单，转换成字符串并写文件 |
| TicketLoadDemo | 从文件读回字符串并打印 |

这些类目前没有 package 声明。迁入 Maven 后再按职责组织包和标准目录。

## 2. Ticket 字段

| 字段 | 类型 | 当前约定 |
| --- | --- | --- |
| id | long | > 0；调用方提供；无公开修改入口 |
| title | String | 非 null；trim 后非空；length ≤ 50 |
| status | TicketStatus | 新建时 OPEN；当前只有 assign 可改为 IN_PROGRESS |
| assigneeId | Long | 新建时 null，表示未派单；派单后为正整数 |

long 无法表示 null，Long 可以，因此处理人使用 Long。编号是否重复由 TicketService 检查，不由单个 Ticket 构造器检查。

## 3. 公开方法契约

| 方法 | 正常结果 | 拒绝条件或特殊结果 |
| --- | --- | --- |
| new Ticket(id, title) | 创建 OPEN、无处理人的工单 | 非正编号或无效标题抛 IllegalArgumentException |
| rename(newTitle) | 校验并保存 trim 后的标题 | 无效标题抛 IllegalArgumentException，旧标题不变 |
| assign(engineerId) | 保存处理人，变为 IN_PROGRESS | 先检查非正编号，抛 IllegalArgumentException；再检查非 OPEN，抛 IllegalStateException |
| getId/getTitle/getStatus/getAssigneeId | 读取当前字段 | assigneeId 可能为 null |
| service.add(ticket) | 按编号加入集合 | null 或重复编号抛 IllegalArgumentException |
| service.findById(id) | 返回集合内的原工单引用 | 不存在返回 null；当前不单独校验查询编号 |
| service.findByStatus(status) | 返回新建的结果列表 | null 状态抛 IllegalArgumentException；无匹配返回空列表 |

Ticket 内的 validateTitle 是私有方法，创建和修改标题共用它。校验成功后才赋值，因此异常不会覆盖原标题。派单也先完成校验，再修改字段。

## 4. 集合与引用

字段声明使用 Map 接口，实现选择 LinkedHashMap，以保持插入顺序；编号不是数组下标。add 先检查重复，避免 put 直接替换同编号记录。

findByStatus 每次创建一个 ArrayList，但列表里的 Ticket 仍然是原对象：

- 对结果列表调用 clear，不会删除服务里的工单。
- 对结果中的 Ticket 调用 rename，会修改服务中同一张工单。
- findById 同样返回原对象，调用前要处理查询不到的情况。

当前采用单线程练习模型。LinkedHashMap 不是线程安全容器，containsKey 与 put 的组合也没有提供并发唯一性保障。

## 5. 当前文件格式

文件名：ticket-demo.properties。路径相对于程序的工作目录，不是相对于 Java 源文件。

逻辑内容示例（实际输出顺序和注释时间可能不同）：

```properties
count=1
ticket.0.id=1001
ticket.0.title=投影仪无信号
ticket.0.status=IN_PROGRESS
ticket.0.assigneeId=20
```

| 键 | 含义 |
| --- | --- |
| count | 记录数量；当前写入 Demo 固定为字符串 1 |
| ticket.0.id | 第 0 条记录的工单编号，十进制字符串 |
| ticket.0.title | 标题字符串 |
| ticket.0.status | 枚举 name()，例如 OPEN |
| ticket.0.assigneeId | 处理人编号字符串；未派单时为空字符串 |

ticket.0 中的 0 是记录序号，不是工单编号。Properties 的这些键本身是普通字符串，不会自动形成嵌套对象。字段写入 Properties 后是当时的字符串快照，不会跟随 Ticket 后续变化。

写入使用 Files.newBufferedWriter(path, UTF_8) 和 Properties.store(Writer, ...)；读取使用 Files.newBufferedReader(path, UTF_8) 和 Properties.load(Reader)。两边都显式指定 UTF-8，并用 try-with-resources 关闭资源。

应通过 Properties API 处理转义，不依赖文件中键的顺序或注释行内容。

## 6. 当前限制与恢复设计

当前读取仅调用 getProperty；结果都是 String，缺键会得到 null。它没有读取 count 来遍历记录，也没有完成格式与业务校验。IOException 会打印错误并结束 main；损坏转义可能引发的 IllegalArgumentException 尚未处理。

下一步恢复时计划检查：

- count、必需字段、编号格式与枚举名称合法。
- 工单编号 > 0，标题沿用领域校验，同一批数据编号不重复。
- OPEN 没有处理人；IN_PROGRESS、RESOLVED、CLOSED 必须有正数处理人编号。
- 恢复保留原状态，不把所有记录都重置为新建状态。
- 先完整解析校验，再替换服务数据，避免加载一半就污染现有集合。

恢复入口尚未实现。不能为了方便加载而添加不受约束的字段 setter。

当前保存 Demo 会直接覆盖同名文件，没有临时文件替换或备份策略。正式集合存档时再设计失败保护，避免写入失败后损坏已有数据。
