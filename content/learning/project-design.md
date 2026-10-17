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

核对日期：2026-10-17。本文描述当前实现，计划中的改造单独标明。

## 1. 当前结构

所有业务类、Demo 和测试均使用 `cn.wishbottle.opsticket` 包，分别位于 Maven 的 `src/main/java` 与 `src/test/java` 源码根下。

```text
保存端：TicketService → findAll → TicketFileStore.save → UTF-8 Properties
读取端：Properties → loadAll → 全部记录校验与 restore → 完整列表
                                                   ↓
                                        新 TicketService 逐张 add
                                                   ↓
                                        查询、筛选、继续 create

新增的独立练习：TicketRepository ← InMemoryTicketRepository
                              （尚未注入 TicketService）
```

| 类或接口 | 当前职责 |
| --- | --- |
| Ticket | 数据封装、编号标题校验、派单规则和恢复入口 |
| TicketStatus | OPEN、IN_PROGRESS、RESOLVED、CLOSED 状态名称 |
| TicketService | 内置 LinkedHashMap，新增、查询、筛选和自动编号创建 |
| TicketFileStore | 列表与 UTF-8 Properties 文件转换；读回时检查字段、类型、重复编号和业务一致性 |
| TicketRepository | 约定 add、findById、findAll、update 四种存取操作 |
| InMemoryTicketRepository | 用自己的 LinkedHashMap 实现接口，尚未取代 Service 中的 Map |
| TicketStartupDemo | 缺文件使用空服务；其他加载错误停止启动 |
| TicketRestartSaveDemo / TicketRestartLoadDemo | 两次独立进程运行，验证保存与重启恢复 |
| TicketLoadFailureDemo / TicketInvalidNumberDemo / TicketInvalidStatusDemo | 检查特定坏存档的异常类型与完整消息 |
| 三个 JUnit 测试类 | 标题 6 项、文件往返 2 项、仓库查询 2 项 |

其余对象、集合、单张/多张文件 Demo 和 ArrayPractice、TitleValidationPractice 保留学习过程。当前没有数据库、网络层或正式应用菜单。

## 2. 领域对象与状态

Ticket 的 id 为 long，title 为 String，status 初始 OPEN，assigneeId 为可空的 Long。创建要求编号为正；标题先检查 null，再 trim，拒绝空白和长度超过 50。rename 先完成校验再赋值，失败保留原标题。

assign 要求工程师编号 > 0 且状态为 OPEN，成功时修改处理人并转为 IN_PROGRESS。restore 要求状态非 null，OPEN 没有处理人，其他状态有正数处理人，再通过构造器校验编号和标题。能恢复 RESOLVED/CLOSED 不等于已经提供提交处理和验收方法。

## 3. 当前公开方法契约

| 方法 | 返回与失败行为 |
| --- | --- |
| TicketService.add(Ticket) | 拒绝 null 和重复编号，通过后加入 Map |
| TicketService.findById(long) | 找到返回原对象；未找到返回 null |
| TicketService.findByStatus(TicketStatus) | 拒绝 null；返回按插入顺序排列的新列表，无匹配返回空列表 |
| TicketService.findAll() | 返回包含现有对象引用的新列表 |
| TicketService.create(String) | 遍历取最大编号，使用最大值加 1 构造工单、add 并返回；空服务从 1 开始 |
| TicketFileStore.save(List<Ticket>, Path) | 拒绝 null 列表、路径或列表元素；用 UTF-8 写文件；I/O 失败向外抛 IOException |
| TicketFileStore.loadAll(Path) | 拒绝 null 路径；所有记录成功后才返回新列表；缺文件等抛 IOException，内容错误抛 IllegalArgumentException |
| Ticket.restore(long, String, TicketStatus, Long) | 校验后构造新对象，恢复原编号、标题、状态与处理人 |

create 的 maxId 每次从 0 开始，但会遍历现有数据；恢复编号 1、2、5 后得到下一号 6，而不是 size()+1 得到的 4。先构造后 add，使标题校验失败时不会新增记录。当前没有并发控制或数据库序列。

## 4. 接口、实现类与 Optional

```java
public interface TicketRepository {
    void add(Ticket ticket);
    Optional<Ticket> findById(long id);
    List<Ticket> findAll();
    void update(Ticket ticket);
}
```

这些没有方法体的接口方法默认 public、abstract。当前普通实现类声明 `implements TicketRepository` 后，必须实现它们（或从父类继承符合要求的实现）。`@Override` 是让编译器核对覆盖关系的注解，建议使用，但删掉注解本身不等于删掉方法实现。

```java
TicketRepository repository = new InMemoryTicketRepository();
```

变量类型是接口，实际对象是内存实现，调用 add 等方法执行具体实现。InMemoryTicketRepository 的 add 拒绝已有编号；update 则要求编号已存在，用传入的新对象替换旧值，不会新增未知编号。两个方法都拒绝 null。

findById 使用 `Optional.ofNullable(ticketsById.get(id))`：有对象时包装该对象，无对象时返回空 Optional；`orElseThrow()` 在有值时取出、无值时抛异常，`isEmpty()` 检查是否没有值。当前 Service.findById 仍返回 Ticket/null，接入仓库时需要明确处理这项接口差异。

新建接口和实现类并没有自动改变已有 Service 的行为；当前文件存储也未实现仓库接口。

## 5. 集合与引用边界

Service 和内存仓库使用 LinkedHashMap，保持插入顺序。`put` 对已有键会替换值，因此新增前必须检查重复编号；更新则先检查存在。

findAll 和 findByStatus 返回新列表，清空列表不改变内部 Map。列表元素仍是原 Ticket 引用，修改其中一个工单的标题会影响仓库/服务中对应对象；这是浅层结构隔离，不是深拷贝。Optional 包装的也不是对象副本。

loadAll 通过 restore 创建新 Ticket，随后 service.add 保存这些对象引用。文件去重使用循环外的 HashSet<Long>，先 contains 检查再 add 记录；contains 不会自动记住编号。文件列表顺序由序号决定，不依赖 Set 顺序。

ArrayPractice.countOccurrences 使用 LinkedHashMap<Integer, Integer>，键是数组元素，值是次数；getOrDefault 后 put 更新计数，空数组返回空 Map，null 被拒绝，保持首次出现顺序。所有集合操作目前都按单线程场景设计。

## 6. 文件格式、编码与路径

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

count 是列表数量，ticket.i 的 i 是从 0 开始的记录位置，不是工单编号。四个键都必须存在；空 assigneeId 字符串表示 null，缺键则是坏存档。有效空列表存档包含 count=0，不是零字节文件。

Properties 的键是普通字符串，不构成嵌套对象；输出行序不保证，读取按 i 拼接键。状态用 enum.name() 保存，valueOf 读取。Writer/Reader 显式使用 UTF-8，try-with-resources 关闭资源；Properties API 负责等号、反斜杠等转义。Java 字面量 `"A=B\\C"` 表示实际标题 `A=B\C`，存档显示的转义形式由 load 还原。

调用方传 Path，存储类不硬编码 data，也不自动创建父目录。`Paths.get("data", "tickets.properties")` 相对于运行时工作目录，同样的字符串在两个不同工作目录下会指向不同文件。排查时比较保存端和读取端的 toAbsolutePath()。

JUnit 使用 `@TempDir Path tempDir`。`tempDir.resolve("tickets-empty.properties")` 只是得到临时目录中的路径，后续 save 才创建文件；这个文件与项目 data 中的同名文件位置不同，不会因此读取或覆盖现有存档。JUnit 默认清理临时资源。

## 7. 加载校验与异常传播

1. 用 UTF-8 Reader 加载 Properties。
2. requireProperty 检查 count 存在，parseIntProperty 转为 int，再拒绝负数。
3. 新建结果列表与 seenIds，按 count 逐条读取四个必要字段。
4. parseLongProperty 解析编号并检查重复；parseStatusProperty 解析状态；空处理人转 null，非空值解析为 long。
5. 调用 restore 进行业务校验；失败补充 ticket.i，成功则加入局部列表。
6. 全部成功才 return；调用方再把工单装入新服务。

| 输入问题 | 当前错误消息示例 |
| --- | --- |
| 缺少第二张标题键 | 存档缺少必要字段：ticket.1.title |
| 第二张编号为 abc | 存档字段格式错误：ticket.1.id，应为整数，实际值：abc |
| 第二张状态为 DONE | 存档状态不合法：ticket.1.status，实际值：DONE |
| count 为 abc | 存档字段格式错误：count，应为整数，实际值：abc |
| count 为 -1 | 存档字段不合法：count，不能为负数，实际值：-1 |
| 第二张编号为 0 | 存档记录不合法：ticket.1，原因：工单编号必须大于0 |
| 记录编号重复 | 存档中工单编号重复：2 |

requireProperty 只拒绝 null，不统一拒绝空字符串，因为空 assigneeId 合法。数字能被解析不等于符合业务规则，编号 0 还要由 Ticket 校验。

辅助方法捕获原异常后，用 `new IllegalArgumentException(message, e)` 包装；新异常包含更具体消息，cause 指向原异常。调用方 getMessage() 得到新说明，getCause() 取得原原因，打印调用栈时可见 Caused by。捕获后的代码由 catch 决定，不会回到 loadAll 的出错位置继续读下一条。AssertionError 不会被 IllegalArgumentException 或 IOException 的 catch 捕获。

读取不修改原文件，不返回部分结果，不提供替换已有服务的通用事务接口；当前也不检查 count 之外的多余记录或格式版本。

## 8. 启动与重启验收

TicketStartupDemo 在 try 外创建空服务，加载成功后逐张 add。NoSuchFileException 必须在其父类 IOException 前捕获：缺文件继续打印启动完成、数量 0；其他 IOException 或 IllegalArgumentException 提示原因并 return，停止启动。该 Demo 不调用 save。

两阶段验收中，保存端创建 1、2、3，将第 2 张派给处理人 20，并写入单独的重启存档；结束进程后，读取端恢复三张，检查全部字段和 OPEN 的 1、3，再 create 得到编号 4。新建 4 只在内存，读取端没有保存，所以重复运行仍从原来三张开始。

坏存档启动前后哈希一致，证明这些读取失败路径没有改写文件；不代表后续保存操作具备抗中断保障。

## 9. 构建、保存限制与后续拆分

pom.xml 使用 release 21、UTF-8、JUnit Jupiter 5.14.4（test 作用域）、maven-compiler-plugin 3.13.0、maven-surefire-plugin 3.5.5。业务与测试编译产物分别为 target/classes、target/test-classes，Surefire 报告位于 target/surefire-reports。clean package 编译并执行正式 JUnit 后打包普通 JAR，不自动执行 Demo，也未配置可直接 java -jar 的入口。

save 在内存准备 Properties 后才打开 Writer，null 列表元素会提前被拒绝；打开后直接截断或覆盖目标文件，写入中途失败仍可能破坏存档。save 不检查传入列表的重复编号，正常 Service/Repository 新增会拒绝重复，loadAll 另行防重。

下一步先补仓库失败边界与列表结构隔离测试，再通过接口拆分 Service；文件原子替换、备份、数据库和并发控制仍属后续工作。