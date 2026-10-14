{
  "title": "工单项目设计与数据约定",
  "description": "类的职责、方法契约、状态规则与 Properties 存档格式。",
  "date": "2026-10-14T00:00:00+08:00",
  "lastmod": "2026-10-14T00:00:00+08:00",
  "weight": 180,
  "group": "project-docs",
  "draft": false
}

[返回项目首页](/learning/project-docs/) · [需求](/learning/project-requirements/) · [运行与验收](/learning/project-verification/)

核对日期：2026-10-14。本文描述当前实现，待实现内容单独标明。

## 1. 当前结构

```text
TicketFileDemo → TicketService.findAll() → List<Ticket>
                                            ↓
                               TicketFileStore.save
                                            ↓
                                  UTF-8 Properties 文件
                                            ↓
                               TicketFileStore.loadAll
                                            ↓
                 检查 count → 循环解析 → Ticket.restore
                                            ↓
                         List<Ticket> → TicketLoadDemo 断言和打印
```

保存端已经从服务取得列表；读取端返回列表，尚未整体装回服务。当前没有数据库或网络层。

| 类 | 职责 |
| --- | --- |
| Ticket | 数据、编号标题校验、派单规则和恢复入口 |
| TicketStatus | 四种状态名称 |
| TicketService | LinkedHashMap 管理工单，添加、编号查询、筛选、返回全部列表 |
| TicketFileStore | 工单列表与 UTF-8 Properties 文件之间的转换和读写 |
| TicketDemo / TicketPractice / TicketArrayDemo | 早期对象和数组练习 |
| TicketServiceDemo | 派单、集合查询与引用关系演示 |
| TicketFileDemo | 创建两张工单、加入服务、调用 save |
| TicketLoadDemo | 调用 loadAll，断言数量与字段，打印结果或异常提示 |

目前没有 package 声明。迁入 Maven 后再组织包和标准目录。TicketLoadFailureDemo 仍是布置的练习，尚未创建。

## 2. Ticket 字段与规则

| 字段 | 类型 | 当前约定 |
| --- | --- | --- |
| id | long | > 0，由调用方提供，无公开修改入口 |
| title | String | 非 null，trim 后非空，String.length() ≤ 50 |
| status | TicketStatus | 新建 OPEN，派单改为 IN_PROGRESS，恢复可还原合法存档状态 |
| assigneeId | Long | 未派单为 null，其他状态要求正数处理人编号 |

编号唯一性由 TicketService.add 检查；单个 Ticket 构造器不能检查其他记录。loadAll 目前也没有做跨记录唯一性检查。

## 3. 公开方法契约

| 方法 | 正常结果 | 拒绝条件或特殊结果 |
| --- | --- | --- |
| new Ticket(id, title) | 新建 OPEN、无处理人的工单 | 非正编号、非法标题抛 IllegalArgumentException |
| rename(newTitle) | 校验并更新 trim 后的标题 | 校验失败保留原标题 |
| assign(engineerId) | OPEN 变为 IN_PROGRESS 并设置处理人 | 非正编号抛 IllegalArgumentException，非 OPEN 抛 IllegalStateException；失败不改状态和处理人 |
| Ticket.restore(id, title, status, assigneeId) | 创建新对象并恢复字段 | 状态为空、状态与处理人冲突、构造器校验失败时抛 IllegalArgumentException |
| getId/getTitle/getStatus/getAssigneeId | 返回当前字段 | assigneeId 可为 null |
| service.add(ticket) | 按编号加入集合 | null 或重复编号抛 IllegalArgumentException，不覆盖旧记录 |
| service.findById(id) | 返回原工单引用 | 不存在返回 null |
| service.findByStatus(status) | 按插入顺序返回新列表 | null 状态被拒绝，无匹配返回空列表 |
| service.findAll() | 按插入顺序返回全部工单的新列表 | 元素仍引用服务里的原工单 |
| store.save(tickets, path) | 将列表写为 count 和分组字段 | null 列表、null 元素或 null 路径被拒绝；空列表写 count=0；IOException 向外传递 |
| store.loadAll(path) | 按序号解析并返回新建工单列表 | null 路径、缺失/非法 count、缺字段、非法类型或业务数据被拒绝；IOException 向外传递 |

标题校验由 Ticket 统一负责，持久化类不重复实现标题规则。恢复文件数据仍通过 Ticket.restore 和构造器校验。

## 4. 集合与引用

Map 接口配合 LinkedHashMap 保持插入顺序，编号不是数组下标。add 在 put 前检查重复编号。

findAll 和 findByStatus 都创建新 ArrayList，但共享 Ticket 引用：清空结果列表不删除服务记录；修改结果中的工单会修改原对象。findById 也返回原对象。

loadAll 则通过 restore 创建新的 Ticket 对象，不是原服务对象的引用。当前采用单线程模型，LinkedHashMap 及 containsKey/put 组合不提供并发保障。

## 5. 文件格式

当前两个文件 Demo 都使用 tickets.properties，路径相对于程序工作目录。旧单张练习文件不再作为默认输入。

```properties
count=2
ticket.0.id=1001
ticket.0.title=投影仪无信号
ticket.0.status=IN_PROGRESS
ticket.0.assigneeId=20
ticket.1.id=1002
ticket.1.title=打印机卡纸
ticket.1.status=OPEN
ticket.1.assigneeId=
```

count 是列表大小；ticket.i 中的 i 是从 0 开始的记录序号，与工单编号不同。四个字段的键必须存在，空处理人字符串表示 null；没有处理人键属于缺字段。状态写入 enum.name()，读取用 valueOf。

Properties 的键是普通字符串，不形成嵌套对象，也不保证输出顺序。读取按序号拼键，不依赖文件行顺序。使用其 API 处理转义；转换后的字符串是当时的快照，不随工单后续修改。

Files.newBufferedWriter/Reader 两边都显式使用 UTF-8。Properties.store(Writer, ...) 与 load(Reader) 处理键值，try-with-resources 关闭资源。

## 6. 加载流程与异常边界

1. 拒绝 null 路径，用 Reader 读取 Properties。
2. 检查 count 存在，用 Integer.parseInt 解析并拒绝负数。
3. 新建结果列表，按 0 到 count-1 逐条取四个字段并检查缺失。
4. 转换 long、枚举、Long，空处理人字符串转 null。
5. 调用 Ticket.restore 并加入局部结果列表；全部完成后返回。

count=0 返回空列表。当前不会检测超出 count 的额外记录，也没有格式版本号或重复编号检查，这些不是已实现能力。

Ticket.restore 要求状态非 null，OPEN 无处理人，其他状态有正数处理人编号，再通过 new Ticket 复用标题和编号校验。restore 不写文件。能够恢复 RESOLVED、CLOSED 不代表相应业务流转已实现，也不应直接作为任意改状态的 Web 接口。

解析或校验抛异常时，不会正常返回部分列表；loadAll 不修改服务和原文件。但“坏文件不返回部分结果”的专门 Demo 尚未完成。调用方后续恢复服务时，还需要单独设计整体替换和失败保护。

TicketLoadDemo 捕获 IOException 与 IllegalArgumentException 并打印提示；正常场景断言抛 AssertionError，不会被这两个分支捕获。当前捕获的文件异常只打印，尚未统一表达为供 CI 使用的失败退出状态。

## 7. 当前保存限制

save 在内存中准备全部 Properties 后才打开 Writer，列表含 null 时不会因提前打开文件而覆盖旧内容。但实际写入会直接截断/覆盖同名文件，没有临时文件替换、备份或原子保存策略，写入过程中失败仍可能损坏已有存档。

后续需要完整校验并检测重复编号后恢复服务，区分首次启动无文件和存档损坏，避免加载失败后把空数据保存到原存档。
