{
  "title": "工单项目设计与数据约定",
  "description": "现有类、存档与Web入门设计，以及待实施的数据库业务和AI边界。",
  "date": "2026-10-21T00:00:00+08:00",
  "lastmod": "2026-10-31T00:00:00+08:00",
  "weight": 180,
  "group": "project-docs",
  "draft": false
}

[返回项目首页](/learning/project-docs/) · [需求](/learning/project-requirements/) · [运行与验收](/learning/project-verification/)

核对日期：2026-10-31。第1—9节记录原控制台设计；第10—12节为完整数据库/Web/AI目标；第13节为独立JDBC事务，第14节保留10月30日入门阶段，第15节是当前文件版Web实现。

2026-10-28 环境补充：本机数据库为 MySQL 8.4.13，驱动为 Connector/J 26.10.0。独立 JdbcTicketQueryDemo 已完成参数化状态查询、SQL NULL读取和方法提取；它直接查询练习库，没有接入下图的正式Service/Repository。正式业务仍使用内存/文件仓库；10月29日更新事务跟练见第13节。环境维护与验收见[运行与验收第 10 节](/learning/project-verification/#10-2026-10-28-mysql-升级验收)。

## 1. 当前结构

业务类使用 cn.wishbottle.opsticket 包，位于 src/main/java；JUnit、Demo 和练习位于 src/test/java 的同名包。

```text
ConsoleApp → TicketService → TicketRepository（接口）
                              ├─ InMemoryTicketRepository → LinkedHashMap
                              └─ FileTicketRepository
                                  ├─ memory：内部内存仓库，负责查询与校验
                                  └─ store：TicketFileStore，负责读写 Properties
```

| 类或接口 | 当前职责 |
| --- | --- |
| Ticket / TicketStatus | 工单状态、编号标题校验、派单和恢复规则 |
| ConsoleApp | 菜单、输入解析、输出、启动及操作异常提示 |
| TicketService | 接收仓库依赖；创建、改标题、派单和查询用例，不再持有自己的 Map |
| TicketRepository | 约定 add、findById、findAll、update |
| InMemoryTicketRepository | LinkedHashMap 存储、重复编号和未知编号检查 |
| FileTicketRepository | 启动时恢复到内部内存仓库；变更后自动保存 |
| TicketFileStore | UTF-8 Properties 与工单列表转换、存档校验 |
| TicketRepositorySwitchDemo | 共用业务流程运行两种实现，再新建文件仓库验证恢复 |
| 四个 JUnit 测试类 | 标题 6、文件往返 2、内存仓库 7、Service 2，共 17 项 |

原有启动、两阶段重启和坏数据 Demo 保留；它们与正式 ConsoleApp 的运行入口和数据路径不同。当前 Java 尚无数据库访问和网络层；sql 目录已有独立练习三表，不能与 Java 运行能力混为一谈。

## 2. 领域对象与状态

Ticket 的 id 为 final long，仅在构造器中赋值，避免意外改变用于仓库查询的编号；title 为 String，status 初始 OPEN，assigneeId 为可空的 Long。创建要求编号为正；标题先检查 null，再 trim，拒绝空白和长度超过 50。rename 先完成校验再赋值，失败保留原标题。

assign 要求工程师编号 > 0 且状态为 OPEN，成功时修改处理人并转为 IN_PROGRESS。restore 要求状态非 null，OPEN 没有处理人，其他状态有正数处理人，再通过构造器校验编号和标题。能恢复 RESOLVED/CLOSED 不等于已经提供提交处理和验收方法。

## 3. 当前公开方法契约

| 方法 | 返回与失败行为 |
| --- | --- |
| TicketService.add(Ticket) | 委托仓库 add；拒绝 null 和重复编号；文件实现还会保存 |
| TicketService.findById(long) | 找到返回原对象；未找到返回 null |
| TicketService.findByStatus(TicketStatus) | 拒绝 null；返回按插入顺序排列的新列表，无匹配返回空列表 |
| TicketService.findAll() | 委托仓库，返回包含现有对象引用的新列表 |
| TicketService.rename(long, String) | 查找工单，不存在抛 IllegalArgumentException；调用对象校验改名，再 repository.update |
| TicketService.assign(long, long) | 查找工单，不存在抛 IllegalArgumentException；调用对象派单，再 repository.update |
| TicketService.findByKeyword(String) | 拒绝 null 和 trim 后空白；按标题 contains 筛选，区分大小写 |
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

findById 使用 `Optional.ofNullable(ticketsById.get(id))`：有对象时包装该对象，无对象时返回空 Optional；`orElseThrow()` 在有值时取出、无值时抛异常，`isEmpty()` 检查是否没有值。Service.findById 已用 repository.findById(id).orElse(null) 转为 Ticket/null，保持已有调用方约定。

Service 构造器接收 TicketRepository 并拒绝 null，保存的是传入仓库的引用。替换为 new FileTicketRepository(path) 后，Service 的规则无需复制。FileTicketRepository 实现接口；TicketFileStore 本身仍是读写工具，不实现该接口。

文件仓库构造时创建新的 memory，loadAll 成功后用 memory.add 装入，避免恢复时触发再次保存。add/update 则先修改 memory，再调用私有 saveAll 写入 memory.findAll()。

接口方法没有声明 IOException，实现方法不能额外声明该受检异常。文件仓库在保存时捕获 IOException，用 UncheckedIOException(message, cause) 包装后抛出；构造器则声明 throws IOException。

## 5. 集合与引用边界

Map 由内存仓库持有，Service 通过仓库访问；文件仓库复用内部内存仓库的 LinkedHashMap，保持插入顺序。`put` 对已有键会替换值，因此新增前必须检查重复编号；更新则先检查存在。

findAll 和 findByStatus 返回新列表，清空列表不改变内部 Map。列表元素仍是原 Ticket 引用，修改其中一个工单的标题会影响仓库/服务中对应对象；这是浅层结构隔离，不是深拷贝。Optional 包装的也不是对象副本。

loadAll 通过 restore 创建新 Ticket，随后 service.add 保存这些对象引用。文件去重使用循环外的 HashSet<Long>，先 contains 检查再 add 记录；contains 不会自动记住编号。文件列表顺序由序号决定，不依赖 Set 顺序。

ArrayPractice.countOccurrences 使用 LinkedHashMap<Integer, Integer>，键是数组元素，值是次数；getOrDefault 后 put 更新计数，空数组返回空 Map，null 被拒绝，保持首次出现顺序。ArrayPractice.twoSum 用双循环检查不同下标；twoSumByMap 用 HashMap 保存“数字 → 下标”，先查找差值，再存当前元素，避免同一元素重复使用；找不到返回空数组。练习按普通整数样例验证，尚未专门处理整数溢出边界。

Lambda 示例用 list.forEach(ticket -> ...) 表示对每个元素执行操作，并不创建新的 Ticket。所有集合操作目前都按单线程场景设计。

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

正式入口 ConsoleApp 使用 data/tickets-app.properties，按工作目录解析。启动时构造 FileTicketRepository 和 Service；IOException 或存档 IllegalArgumentException 会提示并 return。缺文件分支由文件仓库处理为空仓库，父目录仍需事先存在。

菜单使用 nextLine 读取，编号用 Long.parseLong 转换。操作内先 catch NumberFormatException，再 catch IllegalArgumentException；业务错误或 IllegalStateException 提示后继续菜单。UncheckedIOException 表示保存失败，提示后 return，不执行成功提示。启动失败和保存失败当前使用 return，未设置非零进程退出码。

新建文件仓库会创建自己的 Map 并从文件恢复，不共享旧仓库的 Map。TicketRepositorySwitchDemo 在同一进程内验证这一过程；下面保留的第二周 Demo 才是两次独立进程的历史验收。

TicketStartupDemo 在 try 外创建空服务，加载成功后逐张 add。NoSuchFileException 必须在其父类 IOException 前捕获：缺文件继续打印启动完成、数量 0；其他 IOException 或 IllegalArgumentException 提示原因并 return，停止启动。该 Demo 不调用 save。

两阶段验收中，保存端创建 1、2、3，将第 2 张派给处理人 20，并写入单独的重启存档；结束进程后，读取端恢复三张，检查全部字段和 OPEN 的 1、3，再 create 得到编号 4。新建 4 只在内存，读取端没有保存，所以重复运行仍从原来三张开始。

坏存档启动前后哈希一致，证明这些读取失败路径没有改写文件；不代表后续保存操作具备抗中断保障。

## 9. 构建、保存限制与后续拆分

pom.xml 使用 release 21、UTF-8、JUnit Jupiter 5.14.4（test 作用域）、maven-compiler-plugin 3.13.0、maven-surefire-plugin 3.5.5。业务与测试编译产物分别为 target/classes、target/test-classes，Surefire 报告位于 target/surefire-reports。maven-jar-plugin 3.4.1 在 Manifest 中配置 Main-Class 为 cn.wishbottle.opsticket.ConsoleApp。clean package 编译、测试、打包后可用 java -jar target/ops-ticket-0.1.0-SNAPSHOT.jar 启动；Maven 不自动执行 main Demo。现已加入Boot父POM与Web MVC依赖，但原JAR仍以ConsoleApp为入口，不自动包含所有运行依赖，也不包含JUnit测试依赖；Web通过IDEA运行OpsTicketApplication，尚未配置Boot重打包。

save 在内存准备 Properties 后才打开 Writer，null 列表元素会提前被拒绝；打开后直接截断或覆盖目标文件，写入中途失败仍可能破坏存档。save 不检查传入列表的重复编号，正常 Service/Repository 新增会拒绝重复，loadAll 另行防重。

内存仓库的主要边界和列表结构隔离已有测试，Service 已接入接口。文件仓库先改内存再保存，失败不回滚内存；直接覆盖也可能损坏旧文件，多进程同时写入没有保护。当前SQL三表、JOIN和SQL/JDBC事务已有跟练，当前Web已接文件版查询和创建，下一阶段再接数据库；原子替换、备份和并发控制仍属未实现能力。

## 10. 计划中的数据库与 Web 迁移

### 从已有实现演进

当前 Java 的 id/title/status/assigneeId 不等于数据库完整实体。按垂直功能逐步引入 description、deviceId、reporterId、version、时间字段，不一次生成全套 DTO/Controller/Mapper。

```text
浏览器/接口工具 → Spring Security → Controller（请求校验）
 → Service（身份/归属/状态规则，事务边界）
 → MyBatis Mapper（绑定参数、条件SQL） → MySQL
```

沿用Java21与Maven，已接Boot4.1.2/Web MVC；MyBatis尚未添加，接入时核对与Boot4的兼容版本。普通JAR仍启动ConsoleApp，Web启动类已成功运行，Boot可执行Web包尚未配置。数据库调用链仍是目标，当前文件版HTTP查询和创建不等于数据库迁移已完成。

**创建与 ID。** 当前 `TicketService.create` 的 maxId+1 和 `add(Ticket)` 预先携带 ID 只适合内存/文件课。数据库创建输入不带自选 ID；Mapper 插入后返回自增 ID，再构建/读取合法 Ticket。使用专门的插入数据对象接 generated key，不为了框架把当前 final id 粗暴改成任意可写。到这一课一起调整 Service/持久化契约和测试；旧实现可保留练习用途，不强求所有实现永远共用旧四方法接口。

**数据表。** 已有 app_user、device、ticket。随后增加 `ticket_action_log(id, ticket_id, actor_id, action, from_status, to_status, note, created_at, request_key, request_hash)`；创建时 from_status 可空，resolve 的 note 保存非空处理说明。request_key/request_hash 用于 CREATE 幂等，其他日志可空；唯一约束范围为 actor_id/action/request_key。时间、字符串上限、外键及索引在建表课明确。无评论/独立 resolution 表，未来需要退回历史时再扩展。

**事务与并发。** Service 的创建和日志同事务；派单/解决/验收的工单更新和日志同事务。更新条件包括 id、前置状态、expectedVersion，成功后 version+1；受影响行数为 0 时按当前身份检查后返回适当的不存在/冲突响应。数据库 CHECK 只检查当前行合法形状，不替代权限、合法迁移或并发检查。

**重复请求。** CREATE 由客户端生成 requestKey；服务按规范化输入计算 requestHash。已有相同操作者/动作/key 且 hash 相同，返回原 ticketId；hash 不同返回 409。新工单与 CREATE 日志共同提交；并发唯一键冲突时先回滚，再在新的查询中读已有结果。其余状态操作重复请求返回明确冲突，不重复产生状态或日志；暂不引入通用幂等组件/Redis 锁。网络错误后先按 key 或详情核对结果，不盲目重发不同 key。

### 最小数据库版 HTTP 业务契约（目标；当前文件版子集见第15节）

| 请求 | 服务端约束 |
| --- | --- |
| POST /api/auth/login、POST /api/auth/logout、GET /api/me | Spring Security＋Session，保留 CSRF；框架 PasswordEncoder，不自行设计密码算法 |
| GET /api/devices | 返回可报修的启用设备，首版设备由种子初始化 |
| GET /api/users/engineers | 仅管理员可读启用工程师的最少编号/名称信息，不返回密码等私密字段 |
| POST /api/tickets | title/description/deviceId/requestKey；reporterId 从会话取；首次201返回ticketId，同键同输入重试200返回原ticketId |
| GET /api/tickets、GET /api/tickets/{id} | 所有过滤前先落实可见范围；分页上限/稳定排序，禁止通过猜 ID 跨用户读数据 |
| POST /api/tickets/{id}/assign | ADMIN；engineerId＋expectedVersion；用户存在、ENGINEER、启用、OPEN |
| POST /api/tickets/{id}/resolve | 指定工程师；处理说明＋expectedVersion；IN_PROGRESS |
| POST /api/tickets/{id}/accept | 原报修人；expectedVersion；RESOLVED |

参数错 400、未认证 401、已认证但无权操作 403、资源不存在 404、版本/状态/重复键内容冲突 409、依赖不可用 503。对无权读取的工单可统一返回 404 以避免存在性泄露，整组读接口使用同一约定并测试。未知内部错误不暴露堆栈或凭证，返回 requestId 供日志定位。

登录种子的 `NOT_A_LOGIN_HASH` 是当前 SQL 占位文本，不可用作真实密码哈希。认证课再使用框架生成虚构演示账号哈希，数据库凭证/模型密钥从环境取，配置示例不放秘密。先在本机学习，权限与工程门槛通过再对外部署。

Java contains 与 MySQL 排序规则的大小写行为、String.length 与 CHAR_LENGTH 对 emoji 的计数不同；数据库课程需确定统一输入/搜索约定并补边界验证，不能默认为语义完全相同。

## 11. 计划中的 AI 边界与失败路径

首版建议接口为 `POST /api/tickets/{id}/ai-assistance`，读取会话有权访问的工单；失败与业务写入解耦。返回建议对象而非自动更新业务数据：

```json
{
  "summary": "对现有描述的简短忠实摘要",
  "category": "UNKNOWN",
  "missingInformation": ["尚缺少的故障现象或发生时间"]
}
```

示例仅展示协议，**不是模型实测结果**。分类限定 DISPLAY/PRINTING/HVAC/OTHER/UNKNOWN，输入不足不能凭空确定；程序校验必需字段、类型、枚举、字符串长度、列表数量和整体响应大小。category 先不作为数据库字段；首版 summary 仅展示/复制参考，不提供写回。当前 rename 是控制台用例，不是已有 HTTP 接口。后续确需人工采纳改标题时，再明确报修人归属、可修改状态、expectedVersion 及日志事务，增加相应端点并测试。

计划新增 `ai/ModelClient`、`ai/AiAssistanceService`、`controller/AiAssistanceController` 及对应 DTO/测试，均当前不存在。先用 Java HTTP 客户端理解请求与响应，再决定是否引入 Spring AI；不为 AI 拆 Python 服务，不引入 Agent 框架作为第一步。

调用链：授权读取→选取最少必要输入→模型调用→结构/业务校验→返回建议。远程调用不在数据库写事务里。输入文本视为数据，不能让工单中的“忽略之前要求”等内容更改权限或工具能力；不将密码、密钥或整个用户表发给模型。

配置待选：供应商、base URL、模型名、API key 环境变量、费用上限、超时、重试及请求/响应长度上限。实现时按实际 API 文档核对是否支持原生 JSON Schema；即便支持仍做服务端校验。超时/429/5xx可做有上限的重试，鉴权失败和不合法请求不盲重试；无有效结果则明确“暂不可用/资料不足”，保留用户输入和正常业务入口。

日志记录 requestId、内部用户标识、模型/提示版本、耗时、状态、token 使用量与错误类别；避免默认记录完整敏感正文，异常也不打印密钥。成本按实际供应商价格和真实用量计算；缺价格/usage 时记未知或有说明的估算，不填 0 冒充免费。

## 12. 可选 RAG / Agent 的准入

先运行需求与验收中的 B/C 案例，有明确缺口才升级。RAG 适用于需要手册证据的问答：授权资料导入、来源版本、检索、引用定位、无依据拒答分别可检查。资料原文作为不可信输入，不能发出权限命令。

只读 Agent 先复用现有 Service 公开两个有界工具：按状态查询当前用户可见工单、按编号读取授权详情；程序决定允许的工具、参数 schema、分页/字段上限，不能暴露任意 SQL。每次执行检查身份，模型提供的 userId 不作为身份来源。

多步骤时设置总步数、总调用次数/时间/费用限制，保留工具结果和失败，控制上下文长度、过期数据与重试；无权限/无结果有明确停止条件。写工具必须把具体动作和版本交给用户确认，再次鉴权和校验后走原事务接口；不得把一句宽泛同意当永久写权限。首个只读能力稳定前不做多 Agent。


## 13. 2026-10-29 独立 JDBC 更新事务练习

`src/test/java/cn/wishbottle/opsticket/JdbcTicketUpdateDemo.java` 是手动运行的 main Demo，与正式 ConsoleApp→Service→Repository 链路分开。

- `printTicket(Connection,long)` 查询并打印 id/title/version；`findTicketVersion(Connection,long)` 返回 long，记录不存在时抛 IllegalArgumentException。调用方传入同一个连接，两个方法只关闭各自的 statement/resultSet。
- `updateTitle(Connection,long,String,long)` 执行 `UPDATE ticket SET title=?, version=version+1 WHERE id=? AND version=?`。预期影响一行，不符合则抛 IllegalStateException；不新建连接、不提交、不关闭调用方连接。
- `main` 关闭自动提交，先读版本再更新，成功后 commit；SQLException 或 RuntimeException 时 rollback。`simulateFailure=true` 会在更新之后、提交之前抛异常；当前源码为false，运行会尝试真实提交。
- 查询与更新通过同一连接进行，所以同一事务可以读到自己未提交的修改。不同方法的局部sql/statement互不冲突；传入Connection引用不会创建新连接。
- 提取期间曾只有方法定义、main仍执行旧块，经反馈后已改为调用updateTitle并删除重复SQL。提交/回滚的决定保留在调用方。

范围：此Demo没有接入Ticket的完整标题/状态/归属校验，也没有操作日志、请求幂等或生产异常处理。`version`是业务列而非MySQL软件版本，不保存旧标题。旧版本失败不能无条件刷新版本强行重试。HTTP/JSON仅开始讲解，`GET /api/tickets/{id}`仍为计划接口。


## 14. 2026-10-30 Spring Boot Web 入门

OpsTicketApplication位于根包cn.wishbottle.opsticket，使用@SpringBootApplication和SpringApplication.run启动，扫描子包controller。Web Starter带入内嵌Tomcat与Spring MVC。当前链路为浏览器→Tomcat→Spring MVC→Controller→Map序列化响应，没有经过TicketService或数据库。

| 类/方法 | 当前职责与契约 |
| --- | --- |
| HelloController.hello(String name) | GET /api/hello；@RequestParam(name="name", defaultValue="访客")获取查询参数；返回`Map<String,String>`，含message与project。缺失/空字符串使用默认值，未做trim或长度校验 |
| TicketController.readTicketId(long ticketId) | GET /api/tickets/{id}；@PathVariable(name="id")将路径段转成long；返回`Map<String,Long>`仅包含id。正负及数据库存在性均未检查；类型无法转换默认预期400，实操待反馈 |

@RestController使组件被识别并将返回值写入响应体；@GetMapping中的路径决定匹配，不由Java方法名决定。Map是Java内存对象，JSON是序列化后的数据格式；当前不手动拼JSON。所有Controller均为跟练实现，无Web自动测试。

POM保留JUnit5.14.4属性、驱动26.10.0和既有编译/测试/JAR插件。spring-boot-maven-plugin尚未配置，不能用当前ConsoleApp清单声称Web JAR已交付。下一步先验证路径参数，再设计真实查询返回对象和不存在的404处理。


## 15. 2026-10-31 文件仓库 Web 接线与请求 DTO

TicketConfig 使用 @Configuration 和两个 @Bean 方法创建 FileTicketRepository 与 TicketService。Controller 通过唯一构造器接收 Service；默认单例在当前容器内共享，控制台是独立入口，不与 Web 进程共享 Map。

调用链：HTTP Client → Tomcat → Spring MVC → Controller → TicketService → FileTicketRepository → 内存仓库/Properties文件。查询走恢复后的内存，成功创建走自动保存，没有 MyBatis 或数据库访问。

| 请求 | 当前行为 | 证据 |
| --- | --- | --- |
| GET /api/hello[?name=...] | 问候 JSON，缺参使用访客 | 上课用户反馈 |
| GET /api/tickets/{id} | 文件仓库中真实工单；未知编号404，非数字路径400 | 课堂助手GET验证1/999；早期abc由用户反馈 |
| GET /api/tickets[?keyword=...] | 不传查全部；有效关键词筛选；无匹配返回[]；空值或空白400 | 课堂助手实际GET五个场景 |
| POST /api/tickets | JSON标题→DTO→Service创建并自动保存，返回Ticket与201；非法标题400 | 用户201截图，源码/存档核对；空白标题及数量不变由用户反馈 |

列表和创建均显式支持末尾斜杠；详情路径没有额外配置尾斜杠。GET与POST同路径按请求方法区分；不要保留两个相同GET映射。错误原因可能不显示在默认响应体，尚未统一错误JSON。

CreateTicketRequest 只有 title/getTitle/setTitle。@RequestBody 通过消息转换组件/Jackson 将 JSON 转成 DTO；参数名不是 JSON 匹配依据，setTitle 对应 title 属性。DTO只携带输入，Title业务校验保留在Ticket中。Controller返回Ticket/List，@RestController让返回值写入响应体；JSON序列化发生在方法返回之后。

create中IllegalArgumentException被包装成ResponseStatusException(400, message, cause)；默认错误响应不保证显示业务说明。Spring的参数转换异常可能在进入方法前发生，尚未增加统一异常处理。当前直接返回Ticket便于入门，后续按字段暴露需要拆响应DTO。

保存失败不会撤销已改的内存；单例Map、最大编号加一、文件覆盖写入均未做并发保护；反复POST会创建多张。HTTP改名/派单、登录权限、数据库事务、处理验收和AI仍是后续任务。仅本机单人学习，不作为生产部署版本。
