{
  "title": "工单项目设计与数据约定",
  "description": "现有类、存档与Web入门设计，以及待实施的数据库业务和AI边界。",
  "date": "2026-10-21T00:00:00+08:00",
  "lastmod": "2026-11-14T00:00:00+08:00",
  "weight": 180,
  "group": "project-docs",
  "draft": false
}

[返回项目首页](/learning/project-docs/) · [需求](/learning/project-requirements/) · [运行与验收](/learning/project-verification/)

核对日期：2026-11-14；本次只读审查并调整计划，未新增功能。第1—9节记录原控制台及可复用结构；第10—12节为数据库/Web/AI/Agent目标；第13—17节保留历史接线快照；第18节记录11月8日多列DTO、领域对象与只读Repository分层；第19节记录11月9日数据库创建POST、自增主键与约束错误处理。正式 Web 仍连接 Service 与文件仓库；`/api/db`提供只读查询和创建POST，数据库派单/解决/验收尚未闭环。

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
| 原有四个 JUnit 测试类 | 标题 6、文件往返 2、内存仓库 7、Service 2，共 17 项；2026-11-13 另加 8 项隔离测试 |

原有启动、两阶段重启和坏数据 Demo 保留；它们与正式 ConsoleApp 的运行入口和数据路径不同。正式业务仍用文件仓库；独立JDBC已有查询/更新实验，当前Web已有工单查询/创建和Service接线。SQL三表和JDBC Demo不等于正式业务已接库。

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

## 11. Python模型与Java业务边界（计划）

当前Java已有数据库查询/创建练习接口，认证与真实业务授权未完成；Python组件和模型调用尚不存在。Java工单后端（A）与Python基础（Y）并行 → Python模型调用（B）→ 只读Agent（G）→ 知识检索与评测（C）→ 按条件与Java联调。

先在Python使用虚构工单，通过模型SDK生成summary/category/missingInformation，程序校验字段与类型；key/模型/端点从环境注入，超时和429/5xx/无效输出单独处理，模型调用放在Java数据库事务外。模拟故障不能算真实模型验证。

## 12. Python只读Agent、检索及Java联调（计划）

先用Python函数查询本机假工单，模型请求工具后程序校验执行并回传，限制步数、调用数、耗时和返回大小；无结果、歧义、失败有明确路径。按需引入LangChain/LangGraph；记录任务、模型/提示版本、工具参数/结果摘要、耗时及错误，不能包含密钥。

Java业务接口只读联调先限定本机隔离演示数据。真实用户数据必须先完成Java端身份/资源授权和服务间可信身份传递；不得把模型生成的userId视为授权。Python通过受控HTTP工具调用Java，不暴露任意SQL/文件/命令。写工具需具体确认和重新鉴权及版本/幂等校验，后置。

C阶段加入自编资料检索、可定位引用和固定任务评测。任务恢复先覆盖等待输入后继续与重启中断可解释；多Agent/MCP/复杂调度按需后置。

## 13. 2026-10-29 独立 JDBC 更新事务练习（历史快照，以第16节及页首为当前状态）

`src/test/java/cn/wishbottle/opsticket/JdbcTicketUpdateDemo.java` 是手动运行的 main Demo，与正式 ConsoleApp→Service→Repository 链路分开。

- `printTicket(Connection,long)` 查询并打印 id/title/version；`findTicketVersion(Connection,long)` 返回 long，记录不存在时抛 IllegalArgumentException。调用方传入同一个连接，两个方法只关闭各自的 statement/resultSet。
- `updateTitle(Connection,long,String,long)` 执行 `UPDATE ticket SET title=?, version=version+1 WHERE id=? AND version=?`。预期影响一行，不符合则抛 IllegalStateException；不新建连接、不提交、不关闭调用方连接。
- `main` 关闭自动提交，先读版本再更新，成功后 commit；SQLException 或 RuntimeException 时 rollback。`simulateFailure=true` 会在更新之后、提交之前抛异常；当前源码为false，运行会尝试真实提交。
- 查询与更新通过同一连接进行，所以同一事务可以读到自己未提交的修改。不同方法的局部sql/statement互不冲突；传入Connection引用不会创建新连接。
- 提取期间曾只有方法定义、main仍执行旧块，经反馈后已改为调用updateTitle并删除重复SQL。提交/回滚的决定保留在调用方。

范围：此Demo没有接入Ticket的完整标题/状态/归属校验，也没有操作日志、请求幂等或生产异常处理。`version`是业务列而非MySQL软件版本，不保存旧标题。旧版本失败不能无条件刷新版本强行重试。HTTP/JSON仅开始讲解，`GET /api/tickets/{id}`仍为计划接口。


## 14. 2026-10-30 Spring Boot Web 入门（历史快照，以第16节及页首为当前状态）

OpsTicketApplication位于根包cn.wishbottle.opsticket，使用@SpringBootApplication和SpringApplication.run启动，扫描子包controller。Web Starter带入内嵌Tomcat与Spring MVC。当前链路为浏览器→Tomcat→Spring MVC→Controller→Map序列化响应，没有经过TicketService或数据库。

| 类/方法 | 当前职责与契约 |
| --- | --- |
| HelloController.hello(String name) | GET /api/hello；@RequestParam(name="name", defaultValue="访客")获取查询参数；返回`Map<String,String>`，含message与project。缺失/空字符串使用默认值，未做trim或长度校验 |
| TicketController.readTicketId(long ticketId) | GET /api/tickets/{id}；@PathVariable(name="id")将路径段转成long；返回`Map<String,Long>`仅包含id。正负及数据库存在性均未检查；类型无法转换默认预期400，实操待反馈 |

@RestController使组件被识别并将返回值写入响应体；@GetMapping中的路径决定匹配，不由Java方法名决定。Map是Java内存对象，JSON是序列化后的数据格式；当前不手动拼JSON。所有Controller均为跟练实现，无Web自动测试。

POM保留JUnit5.14.4属性、驱动26.10.0和既有编译/测试/JAR插件。spring-boot-maven-plugin尚未配置，不能用当前ConsoleApp清单声称Web JAR已交付。下一步先验证路径参数，再设计真实查询返回对象和不存在的404处理。


## 15. 2026-10-31 文件仓库 Web 接线与请求 DTO（历史快照，以第16节及页首为当前状态）

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


## 16. 2026-11-04 请求转换与基础统一错误响应

当前Web继续使用文件仓库。文件仓库构造时恢复存档，正常GET查询内存；重启读取编号2已有学习者运行反馈。

- `dto/CreateTicketRequest`承载输入，JSON存在title时按当前默认映射调用setter；缺字段的{}跳过setter、字段保持null。显式null与缺字段不同，不能理解成Java方法调用少传参数。
- `dto/ErrorResponse`只保存final message，通过构造器赋值和getter供JSON输出；本类没有决定HTTP状态码。
- `exception/GlobalExceptionHandler`由RestControllerAdvice注册，方法由Spring按异常类型调用。当前有两个方法，不是全部异常的兜底。
- `handleUnreadableBody`处理HttpMessageNotReadableException，用ResponseStatus固定400，响应message为“请求体缺失或格式不正确”。涵盖请求体无法读取或转换；不能把此类型只解释成JSON语法错误。
- `handleStatusException`处理ResponseStatusException；从getReason取说明，null时使用“请求处理失败”，通过ResponseEntity.status(e.getStatusCode()).body(new ErrorResponse(message))保留状态码并返回统一响应体。
- 现有Controller对IllegalArgumentException的包装仍在；查不到工单时原有ResponseStatusException(404, reason)直接交给处理器。没有笼统把所有异常改成400。

有效空白标题在创建Ticket时失败，未执行Service后面的add；格式错误JSON在准备RequestBody参数时失败，未进入Controller方法。异常处理器可接管后一条路径。ResponseEntity携带状态、响应头和响应体，ErrorResponse只是本次body的数据类型；JSON序列化由Spring在返回处理阶段完成。

本段保留11月4日状态；路径参数类型错误已在此后补上，但存储错误、其他内部异常、Bean Validation、requestId日志、权限、数据库事务、幂等和并发保护仍未统一覆盖。Service编号仍为maxId+1，成功POST仍会新增，不代表数据库主键或重复请求契约已经实现。


## 17. 2026-11-07 MyBatis 只读查询接线

临时数据库链路为：

```text
HTTP Client → Tomcat → Spring MVC → DatabaseTicketController
            → TicketMapper 代理 → MyBatis → MySQL
```

- `TicketMapper` 使用 `@Mapper`，`findTitleById` 通过 `@Select("SELECT title FROM ticket WHERE id = #{id}")` 查询单列；`@Param("id")` 与 `#{id}` 对应，使用预编译参数绑定。
- MyBatis-Spring 启动时注册 Mapper，`SqlSession.getMapper(...)` 在运行时生成实现接口的代理对象；Spring 通过构造器把它注入 `DatabaseTicketController`。
- `DatabaseTicketController` 的 GET `/api/db/tickets/{id}/title` 调用 Mapper，查到标题后组装 `Map<String,String>` 并由 Jackson 返回 JSON；无记录抛 404，非数字路径在参数转换阶段返回 400。
- 这条链路绕过 `TicketService` 和文件仓库，仅用于验证数据库接线。最终结构仍是 Controller → Service → Repository/Mapper → 数据库，数据库映射不能长期由临时 Controller 直接承担。
- 现阶段只完成单列只读。完整列映射、`@Results`/`resultMap` 或构造器映射、领域 `Ticket` 转换、数据库写入、自增主键、事务和状态流均待后续实现。

## 18. 2026-11-08 多列映射、领域对象与只读 Repository

数据库只读链路已从单列`title`扩展为多列对象：

```text
HTTP Client
→ DatabaseTicketController
→ DatabaseTicketQueryService
→ TicketQueryRepository（接口）
→ DatabaseTicketRepository
→ TicketMapper 代理
→ MyBatis
→ MySQL
```

`TicketSummary`承载`id/title/status/assigneeId`，由MyBatis通过无参构造和setter填充。`assigneeId`使用`Long`表示可空处理人；`application.properties`开启`mybatis.configuration.map-underscore-to-camel-case=true`，使`assignee_id`映射到`assigneeId`。列表查询使用`ORDER BY id`，返回`List<TicketSummary>`；实际反馈为编号1和3，不存在编号2属于数据库当前状态。

`TicketSummaryConverter`把DTO转换为领域对象：先`TicketStatus.valueOf`，再调用`Ticket.restore(id,title,status,assigneeId)`。不把数据库行直接反射进`Ticket`，因为`Ticket`有final id、无无参构造器、枚举状态和状态/处理人组合校验。相同getter可能生成相同JSON，但DTO与领域对象的职责不同。

只读Repository接口为：

```java
Optional<Ticket> findById(long id);
List<Ticket> findAll();
```

`DatabaseTicketRepository`实现查询与DTO转换，`DatabaseTicketQueryService`负责应用层查询。`TicketMapper`是MyBatis动态代理，`DatabaseTicketRepository`是Spring普通Bean；构造器注入把代理和仓库按依赖顺序传入Controller/Service。HTTP 404由Controller决定，Repository用`Optional.empty()`表达未找到。

接口：`GET /api/db/tickets`、`/api/db/tickets/{id}`、`/api/db/tickets/{id}/domain`、`/api/db/domain/tickets`。前两者返回摘要DTO，后两者返回领域对象。

写入只做了准备：`TicketInsert`、`@Insert`、`@Options(useGeneratedKeys=true,keyProperty="id",keyColumn="id")`、`TicketWriteRepository`和`DatabaseTicketRepository.create`已存在；尚无`DatabaseTicketCommandService`、`CreateDatabaseTicketRequest`和POST Controller，也未验证自增主键或处理外键/CHECK错误，不能算数据库创建完成。

## 19. 2026-11-09 数据库创建 POST

创建链路：

```text
HTTP Client
→ DatabaseTicketController.create
→ DatabaseTicketCommandService.create
→ TicketWriteRepository.create
→ DatabaseTicketRepository.create
→ TicketMapper.insertTicket
→ MyBatis INSERT
→ MySQL 自增主键
→ findById 回查
→ Ticket / 201 JSON
```

- `CreateDatabaseTicketRequest` 承载 `title`、`deviceId`、`reporterId`；
- `DatabaseTicketCommandService` 校验标题空白/长度和编号正数，然后委托写仓库；
- `TicketMapper.insertTicket` 使用 `@Insert` 写入 `title/device_id/reporter_id`；
- `@Options(useGeneratedKeys=true, keyProperty="id", keyColumn="id")` 把数据库生成的 `id` 回填到 `TicketInsert.id`；
- `DatabaseTicketRepository.create` 检查影响行数与主键非空，再用 `findById` 读取数据库中的真实 `Ticket`；
- `DatabaseTicketController` 返回 201；`IllegalArgumentException` 由 Controller 转 400；外键/CHECK 的 `DataIntegrityViolationException` 由 `GlobalExceptionHandler` 统一转 400。

边界：`Ticket` 领域对象目前不含 `version` 和 `deviceId/reporterId`，HTTP 响应只有 `id/title/status/assigneeId`；版本条件和派单/解决/验收状态流仍待下一步。

## 20. 2026-11-13 创建事务与输入边界

创建时由 Spring 管理的 `DatabaseTicketRepository.create` 使用 `@Transactional`：同一事务内完成 INSERT、获取生成的主键和回查。回填主键缺失、回查失败抛出运行时异常时回滚。此保护依赖通过 Spring 创建的代理调用；直接 `new DatabaseTicketRepository(...)` 不会自动得到声明式事务。事务不能保证客户端重试不会创建两条，也不代替权限校验。

`spring.jackson.deserialization.accept-float-as-int=false` 禁止 JSON 小数被截断为整数；该设置对所有 JSON 整数属性生效，例如 3.8 和 3.0 不再当作 long 编号。文件保存前检查重复工单编号，发现重复时尚未打开覆盖文件；IO 写入中断仍没有原子替换保证。
