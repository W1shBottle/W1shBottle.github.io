{
  "title": "工单项目设计与数据约定",
  "description": "类的职责、方法契约、状态规则与 Properties 存档格式。",
  "date": "2026-10-17T00:00:00+08:00",
  "lastmod": "2026-10-17T00:00:00+08:00",
  "weight": 180,
  "group": "project-docs",
  "draft": false
}

[返回项目首页](/learning/project-docs/) · [需求](/learning/project-requirements/) · [运行与验收](/learning/project-verification/)

核对日期：2026-10-17（凌晨）。本次学习归 2026-10-16。本文描述当前实现，未实现内容单独标明。

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
            检查 count、字段和重复编号 → Ticket.restore
                                            ↓
                                完整的 List<Ticket>
                                            ↓
                TicketLoadDemo → 新 TicketService → 逐张 add
                                            ↓
                               数量、编号和状态查询
```

保存端从服务取得列表；读取端在 loadAll 完整成功后，把列表装入新服务。尚无数据库、网络层或完整控制台菜单。

| 类 | 职责 |
| --- | --- |
| Ticket | 数据、编号标题校验、派单规则和恢复入口 |
| TicketStatus | 四种状态名称 |
| TicketService | LinkedHashMap 管理工单，添加、编号查询、状态筛选、返回全部列表 |
| TicketFileStore | 工单列表与 UTF-8 Properties 文件的转换和读写，加载时检查重复编号 |
| TicketDemo / TicketPractice / TicketArrayDemo | 早期对象和数组练习 |
| TicketServiceDemo | 派单、集合查询与引用关系演示 |
| TicketFileDemo | 创建两张工单、加入服务、调用 save |
| TicketLoadDemo | loadAll 后恢复新服务，查询数量和状态，并保留原来的字段断言 |
| TicketLoadFailureDemo | 验证缺少第二张标题时正确抛异常，其他结果判定失败 |
| TicketEmptyDemo | 保存空列表，再读回并检查非 null 且为空 |
| TicketTest | 6 个标题修改 JUnit 测试 |
| TicketFileStoreTest | 2 个文件往返 JUnit 测试，使用 @TempDir |
| ArrayPractice | 数组最大值与数字出现次数；main 目前只测试最大值 |
| TitleValidationPractice | 独立重写标题校验；当前没有 main 或 JUnit 测试方法 |

业务类位于 src/main/java；测试、Demo 和练习位于 src/test/java。已使用 Maven，但仍采用默认包，后续再安排包名和接口分层。业务类不依赖测试类。

## 2. Ticket 字段与规则

| 字段 | 类型 | 当前约定 |
| --- | --- | --- |
| id | long | > 0，由调用方提供，无公开修改入口 |
| title | String | 非 null，trim 后非空，String.length() ≤ 50 |
| status | TicketStatus | 新建 OPEN，派单改为 IN_PROGRESS，恢复可还原合法存档状态 |
| assigneeId | Long | 未派单为 null，其他状态要求正数处理人编号 |

这些数据属于每张工单的实例字段，不能改成所有工单共享的 static 字段。编号唯一性由 TicketService.add 和文件读取中的 Set 分别检查；单个 Ticket 构造器无法检查其他记录。

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
| store.loadAll(path) | 按序号解析并返回新建工单列表 | null 路径、缺失/非法 count、缺字段、重复编号、非法类型或业务数据被拒绝；IOException 向外传递 |

标题校验由 Ticket 负责，持久化类不重复实现标题规则。计划中的 create(String title) 尚不存在，不应作为当前可调用 API。

## 4. 集合与引用

Map 接口配合 LinkedHashMap 保持插入顺序，编号不是数组下标。add 在 put 前检查重复编号。

findAll 和 findByStatus 创建新 ArrayList，但共享 Ticket 引用：清空结果列表不删除服务记录；修改结果中的工单会修改原对象。findById 也返回原对象。

loadAll 通过 restore 创建新的 Ticket；再调用 service.add(ticket) 时，服务保存的是这些已恢复对象的引用，不会再次复制对象。

文件去重使用循环外的 Set<Long> seenIds = new HashSet<>()。每读到一个编号，先 contains 检查，重复则抛出包含编号的 IllegalArgumentException；不重复再 add。contains 只查询，不会自动记录编号。HashSet 不需要保持顺序，结果列表的顺序仍由文件序号决定。

ArrayPractice.countOccurrences 则使用 LinkedHashMap<Integer, Integer>：键是数组中的数字，值是次数。每次 getOrDefault(number, 0) 后，用 put(number, oldCount + 1) 写回。空数组返回空 Map，null 被拒绝；保持首次出现顺序，不限制数字在 0～9。

当前采用单线程模型，集合操作没有并发保障。

## 5. 文件格式与路径

正常保存和读取 Demo 使用 data/tickets.properties，失败测试使用 data/tickets-invalid.properties，空列表 Demo 使用 data/tickets-empty.properties。代码使用 Paths.get("data", "文件名")，路径相对于运行时工作目录；IDEA 文件 Demo 应以项目根目录为工作目录。

保存和读取方法接受调用方传入的 Path，不在 TicketFileStore 内硬编码 data。父目录需预先存在。两份早期单张练习文件也保留在 data 中。

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

空列表的有效存档包含 count=0，不是零字节空文件。count 是列表大小；ticket.i 中的 i 是从 0 开始的记录序号，与工单编号不同。四个字段的键必须存在，空处理人字符串表示 null；没有处理人键属于缺字段。状态写入 enum.name()，读取用 valueOf。

Properties 的键是普通字符串，不形成嵌套对象，也不保证输出顺序。读取按序号拼键，不依赖文件行顺序。使用其 API 处理转义；转换后的字符串是当时的快照，不随工单后续修改。

Files.newBufferedWriter/Reader 显式使用 UTF-8，Properties.store(Writer, ...) 与 load(Reader) 处理键值，try-with-resources 关闭资源。

JUnit 使用 @TempDir Path tempDir。tempDir.resolve("tickets-empty.properties") 只是组合临时目录中的路径；真正创建文件的是后续 save。这个名字与 data/tickets-empty.properties 恰好相同，**不是同一个文件，也不是读取现有 data 文件的快捷方式**。测试结束后临时资源由 JUnit 默认清理。

## 6. 加载流程与异常边界

1. 拒绝 null 路径，用 Reader 读取 Properties。
2. 检查 count 存在，用 Integer.parseInt 解析并拒绝负数。
3. 新建结果列表和 seenIds，按 0 到 count-1 逐条取四个字段并检查缺失。
4. 解析 id，检查重复并加入 seenIds；解析枚举、Long，空处理人字符串转 null。
5. 调用 Ticket.restore 并加入局部结果列表；全部完成后才返回。
6. TicketLoadDemo 取得完整列表后新建 TicketService，循环 add，再执行查询。

Ticket.restore 要求状态非 null，OPEN 无处理人，其他状态有正数处理人编号，再通过 new Ticket 复用标题和编号校验。restore 不写文件。能够恢复 RESOLVED、CLOSED 不代表相应业务流转已实现。

解析失败时不会正常返回部分列表；loadAll 不修改服务和原文件。当前恢复演示创建新服务，没有“用新数据整体替换已有服务”的接口，不把这个演示描述为通用事务恢复。

TicketLoadDemo 捕获 IOException 与 IllegalArgumentException 并打印提示；AssertionError 不会被这两个分支捕获。文件不存在目前仍抛 IOException，没有首次启动初始化分支。部分内容错误只给通用消息，尚未统一标出记录序号和字段。

当前不检测超出 count 的额外记录，没有格式版本号，也没有自动接续编号。

## 7. 构建与测试

pom.xml 固定了 Java release 21、UTF-8、JUnit Jupiter 5.14.4（test 作用域）、maven-compiler-plugin 3.13.0 和 maven-surefire-plugin 3.5.5。Maven 编译输出为 target/classes 与 target/test-classes，测试报告位于 target/surefire-reports。

测试方法使用 @Test，由测试引擎调用，不需要 main。现有 8 项 JUnit 不包括所有 main Demo 和助手临时验收；运行 mvn test 不能代替尚未完成的完整业务重启验证。

## 8. 当前保存限制与下一步

save 在内存中准备全部 Properties 后才打开 Writer，列表含 null 时不会因提前打开文件而覆盖旧内容。但写入会直接截断/覆盖同名文件，没有临时文件替换、备份或原子保存策略，写入过程中失败仍可能损坏已有存档。save 本身不检查传入列表的重复编号；正常服务通过 add 防重，loadAll 另行拒绝重复存档。

下一步先实现最大现有编号加 1 的 create(String title)，再区分首次无文件和存档损坏、补充错误上下文及重启验收，防止加载失败后把空数据保存到原存档。既有 Maven/JUnit 保留，主线继续补齐第二周。
