{
  "title": "设备运维工单项目文档",
  "description": "当前控制台、JDBC与Web练习进度，Java＋AI路线和运行入口。",
  "date": "2026-10-21T00:00:00+08:00",
  "lastmod": "2026-11-14T00:00:00+08:00",
  "weight": 160,
  "group": "project-docs",
  "draft": false
}

> 本组文档对应项目当前实现，与[总体规划](/learning/project/)配合阅读。后续功能以各页的实现状态为准。

围绕“设备报修 → 派单 → 处理 → 验收”逐步开发的 **Java＋AI 学习项目**。现有v0.1控制台包含内存/文件仓库、自动保存和恢复；SQL与独立JDBC已有跟练成果。现已加入 **Spring Boot 工单查询、创建与基础统一错误响应**，通过 Bean 配置和构造器注入复用原有 Service/文件仓库。2026-11-09 完成数据库创建 POST：`CreateDatabaseTicketRequest`、`DatabaseTicketCommandService`、`POST /api/db/tickets`、`@Options` 自增主键回填、回查 `Ticket` 和 201 JSON；外键/标题 CHECK 错误统一转 400。正式工单业务仍使用文件仓库，数据库派单/解决/验收、登录权限、AI与Agent仍待实现。

文档核对日期：2026-11-14；最近学习证据更新到11月9日：学习者编写数据库创建 POST 四块代码并自行请求，得到真实自增id=9；助手编译并验证合法201、GET列表、外键/标题/编号错误400和数据库行，随后按学习者要求删除测试行并把自增重置为4。路线改为Java工单业务与Python基础并行，随后完成Python模型调用、只读Agent、资料检索与评测，最后按权限条件与Java联调。数据库临时只读查询、创建POST与约束错误映射已接通，正式业务、数据库派单/解决/验收、权限与AI仍待实现；历史笔记保留当时进度。

## 项目文档

| 文档 | 解决的问题 |
| --- | --- |
| [需求与开发计划](/learning/project-requirements/) | 业务规则、已实现功能和待完成任务 |
| [设计与数据约定](/learning/project-design/) | 类的分工、方法契约、状态和存档格式 |
| [运行与验收](/learning/project-verification/) | 环境、运行命令、测试证据和验收边界 |
| [2026-11-13 全面检查记录](/learning/project-verification/#20-2026-11-13-隔离审查验证) | 本次修复、测试、实际学习证据和剩余风险 |

学习入口：[路线说明](/learning/start/) · [阶段计划](/learning/schedule/) · [技能清单](/learning/checklists/) · [实际学习进度](/learning/#progress)。本组项目文档记录实现与验收，课程材料记录后续学习安排。

## 当前功能与职责

- `ConsoleApp` 负责菜单、输入与输出，支持新建、查看全部、修改标题、派单、按标题关键词查询和退出。数字格式或业务输入错误会提示并返回菜单。
- `Ticket` 负责编号、标题和派单规则：编号为正数；标题去除首尾空白后非空且不超过 50 个字符；仅待派单工单可以派给正数编号的工程师。
- `TicketService` 通过构造器接收 `TicketRepository`，共用创建、改标题、派单和查询逻辑。创建编号为已有最大编号加 1，空仓库从 1 开始；关键词按去除首尾空白后的文字做区分大小写的包含匹配。状态筛选方法已实现，尚未接入菜单。
- `TicketRepository` 约定 `add`、`findById`、`findAll`、`update`。新增重复编号、更新不存在编号会被拒绝；查询不存在编号时仓库返回空 `Optional`，Service 的 `findById` 则返回`null`。
- `InMemoryTicketRepository` 使用 `LinkedHashMap` 保存运行期间的数据，程序结束后不保留。
- `FileTicketRepository` 内部复用内存仓库：启动时从文件恢复，查询时访问内存，新增或更新时先修改内存，再保存全部工单。缺少存档文件时按空仓库启动；其他读取错误或坏存档会使控制台提示并停止启动。
- `TicketFileStore` 以 UTF-8 和 Properties 格式读写列表，用 `count` 记录数量；加载时检查缺字段、数字和状态格式、负数量、重复编号，以及状态与处理人的一致性。加载失败不返回部分结果，包装异常时保留原始原因。

- `OpsTicketApplication` 启动 Spring Boot；`config/TicketConfig` 注册文件仓库与 Service；`TicketController` 构造器注入 Service，支持详情、列表、关键词和创建。`dto/CreateTicketRequest` 接收创建标题，`tickets.http` 保存手动验收请求。
- `dto/ErrorResponse`承载message；`exception/GlobalExceptionHandler`处理请求体无法读取/转换、ResponseStatusException和方法参数类型不匹配。前者固定400，第二类保留原状态及reason，第三类返回参数名并固定400。现有Controller内的异常包装保留，不代表全部错误分支已经覆盖。
- `dto/TicketSummary`承载数据库查询的`id/title/status/assigneeId`，`TicketSummaryConverter`把DTO转换为领域`Ticket`并调用`Ticket.restore`校验状态与处理人组合。`application.properties`已开启`map-underscore-to-camel-case`，`assignee_id`可自动映射到`assigneeId`。
- `DatabaseTicketQueryService`组织数据库只读查询：标题、摘要、摘要列表、单张领域对象和领域对象列表。领域查询通过`TicketQueryRepository`接口和`DatabaseTicketRepository`实现，返回`Optional<Ticket>`或`List<Ticket>`；Controller只负责HTTP参数与404。
- `mapper/TicketMapper`使用`@Mapper`、`@Select`、`@Param`和`#{}`查询MySQL；`@Insert`、`@Options(useGeneratedKeys...)`与`insertTicket`已接通`POST /api/db/tickets`，`DatabaseTicketRepository.create`完成插入、主键检查和回查；`DatabaseTicketCommandService`负责校验与委托，`GlobalExceptionHandler`把外键/标题约束错误转400。

## 快速构建与运行

使用 **JDK 21** 和 Maven。在 IDEA 中加载 `pom.xml`，确认项目 SDK 与 Maven 使用的 JDK；命令行操作在项目根目录进行：

```powershell
java -version
javac -version
mvn -v
mvn clean package
java -jar target/ops-ticket-0.1.0-SNAPSHOT.jar
```

`clean` 清理 `target`；`package` 执行编译、JUnit 测试和打包。成功显示 `BUILD SUCCESS`，生成 `target/ops-ticket-0.1.0-SNAPSHOT.jar`。JAR 已配置入口 `cn.wishbottle.opsticket.ConsoleApp`，可以用 `java -jar` 启动。

以上 `mvn` 命令要求终端能够找到 Maven；也可使用 IDEA 的 Maven 面板或其自带 Maven 可执行文件。项目没有 Maven Wrapper，首次构建需要下载依赖；依赖和插件已缓存后可尝试 `mvn -o package`。新终端中应重新确认 Java 与 Maven 的 JDK。

### Web 运行与接口（2026-11-07）

在 IDEA 重新加载 Maven，使用 JDK21 运行 `cn.wishbottle.opsticket.OpsTicketApplication.main`，工作目录为项目根目录，默认端口8080。`TicketConfig` 创建仓库时读取 `data/tickets-app.properties`；文件缺失可空仓库启动，其他IO错误或坏存档使启动失败。修改代码后重启。

| 请求 | 当前行为 | 证据 |
| --- | --- | --- |
| GET /api/hello[?name=...] | 问候 JSON，缺参使用访客 | 上课用户反馈 |
| GET /api/tickets/{id} | 文件仓库中真实工单；未知编号404，非数字路径400 | 课堂助手GET验证1/999；早期abc由用户反馈 |
| GET /api/tickets[?keyword=...] | 不传查全部；有效关键词筛选；无匹配返回[]；空值或空白400 | 课堂助手实际GET五个场景 |
| POST /api/tickets | JSON标题→DTO→Service创建并自动保存，返回Ticket与201；非法标题400 | 用户201截图，源码/存档核对；空白标题及数量不变由用户反馈 |
| POST /api/db/tickets | JSON标题/deviceId/reporterId→CommandService→Repository INSERT，返回Ticket与201；外键/标题/编号错误400 | 学习者自行POST得到id=9；助手验证201/400矩阵与数据库行 |
| GET /api/db/tickets/{id}/title | 临时只读接口直接调用MyBatis Mapper查询MySQL的title；查到返回JSON，无记录404，非数字路径400 | 学习者Debug反馈1=200标题JSON、999=404、abc=400；不是正式数据库业务 |
| GET /api/db/tickets/{id} | 返回`TicketSummary`；字段含id/title/status/assigneeId，无记录404 | 学习者反馈多列映射与JSON符合预期 |
| GET /api/db/tickets | 返回`List<TicketSummary>`；按id排序 | 学习者反馈200、编号1和3两条JSON、无编号2 |
| GET /api/db/tickets/{id}/domain | 通过Repository查询并转换成`Ticket`；无记录404 | 源码核对；未单独记录本轮运行正文 |
| GET /api/db/domain/tickets | 返回`List<Ticket>`；逐行调用`Ticket.restore` | 源码核对；未单独记录本轮运行正文 |

列表和创建均显式支持末尾斜杠；详情路径没有额外配置尾斜杠。GET与POST同路径按请求方法区分；不要保留两个相同GET映射。请求体转换错误、Controller抛出的ResponseStatusException和方法参数类型不匹配已由GlobalExceptionHandler统一返回带message的JSON；状态码仍按400/404区分。尚未统一全部异常分支。

在 IDEA 打开 `tickets.http`，逐条运行请求。成功 POST 每次都会新增并写文件；目前不是幂等接口。创建截图中编号2，具体编号以当时数据为准。先查列表、提交空白标题、再查列表，验证失败没有新增。2026-11-04学习者反馈重启后GET编号2恢复成功；同时反馈统一错误响应的三个场景通过，详见验收文档第15节。2026-11-07又反馈数据库临时接口1/999/abc分别符合200/404/400预期，详见第17节。2026-11-08反馈数据库多列列表接口返回编号1和3，补上`assigneeId`后输出符合预期；领域对象与Repository分层以源码核对为准，当时尚未新增Web自动测试。2026-11-09学习者编写数据库创建POST并自行请求得到id=9；助手用JDK 21启动应用验证合法201、GET列表、外键/标题/编号错误400并核对数据库行；完整矩阵不算学习者独立复跑。

普通 `java -jar` 仍启动 ConsoleApp，尚未配置 Spring Boot 可执行 Web 包。本机学习时使用一个进程访问存档；不要同时运行控制台和 Web 写同一文件，两者不共享运行中的 Map，也无并发保护。正式 `/api/tickets` 数据源仍是文件；`/api/db` 下已有的查询和创建接口使用数据库，独立 JDBC Demo 也不是正式业务数据源。

### MySQL 与 JDBC 环境（2026-10-28）

当前学习环境为 MySQL 8.4.13 LTS 与 Connector/J 26.10.0。在 IDEA 重新加载 Maven 依赖；数据库地址、账号和密码按自己的本机环境配置。升级前已有备份，助手完成恢复、数据一致性与真实 JDBC 验证；安装路径、账号材料和回退操作保留在本地，不公开。

学习者随后完成独立 JDBC 查询 Demo；正式控制台仍使用文件仓库，10月29日已跟练独立更新事务与故障回滚，正式数据库业务仍待接入。详见[运行与验收](/learning/project-verification/)。

### 存档位置

控制台与当前 Web 配置均使用 `data/tickets-app.properties`。这是相对于**运行时工作目录**的路径，并非相对于 JAR 所在目录；启动时会打印绝对路径。请在项目根目录运行，并确保 `data` 目录存在，保存方法不会自动创建父目录。

关闭后重新启动会恢复已有工单。成功的新建、修改标题和派单会自动保存，不需要手动调用文件工具。

### JDBC 查询与更新练习

测试源码中的 `JdbcTicketQueryDemo` 从 `OPS_TICKET_DB_PASSWORD` 读取数据库密码；在 IDEA 对应运行配置中填写，不写入源码或公开截图。同一个连接查询待派单和处理中工单，方法自行关闭 statement/resultSet，连接由 main 关闭。它是手动运行的 main Demo，不由 `mvn test` 自动执行。

`JdbcTicketUpdateDemo` 同样是手动 main Demo：`findTicketVersion` 返回当前版本，`updateTitle(Connection,long,String,long)` 只执行条件更新与影响行数检查；`main` 负责关闭自动提交、提交/回滚和连接生命周期。`simulateFailure=true` 在更新后、提交前抛出运行时异常，验证整次回滚；当前已改回 `false`，再次运行会尝试提交并使版本加一。运行前查询实际数据，不照抄旧版本。学习者已反馈提交、MySQL终端可见及故障回滚通过，本次日结只读核对，不重复操作数据库。

## 验证方式

```powershell
mvn test
```

2026-10-26 使用 JDK 21 执行离线 `package` 成功；2026-10-28 更新驱动后再次执行 `mvn test`，17 项测试全部通过。10月30日学习者反馈加入Boot配置后测试通过；日结未重跑，未新增Web自动测试。10月31日的HTTP Client练习是手动验收，没有增加JUnit数量。当时的 17 个 JUnit 测试：`TicketTest` 6 个、`TicketFileStoreTest` 2 个、`InMemoryTicketRepositoryTest` 7 个、`TicketServiceTest` 2 个。现有测试覆盖标题校验、文件往返、部分仓库契约和 Service 行为，不代表所有功能与故障场景均已自动覆盖。`update(null)` 的同类练习已跳过，不计入测试数量。

2026-11-04助手使用JDK21执行离线`compile`成功；学习者通过HTTP Client验证错误JSON400、空白标题400、未知编号404及各自message。当时17项JUnit没有重跑，也没有新增Web自动测试。

2026-11-13 助手在隔离副本使用 JDK 21 与 H2 内存数据库执行 `mvn -o test`：**25 项通过**，其中 17 项为原有测试，8 项为本次新增的事务、接口和边界测试。17 个原有 Demo 在隔离副本中运行成功。H2 不能替代真实 MySQL 兼容性测试；本次未连接或修改你的 MySQL，也未运行会提交 MySQL 更新的 JDBC Demo。测试由助手编写和执行，不视为学习者已掌握。详见[全面检查记录](/learning/project-verification/#20-2026-11-13-隔离审查验证)。

`mvn test` 不会自动运行带 `main` 的 Demo。两种仓库的共用业务流程与文件重新加载可以单独运行：

```powershell
mvn test-compile
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' cn.wishbottle.opsticket.TicketRepositorySwitchDemo
```

这是 Windows PowerShell 示例，其他系统的 classpath 分隔符可能不同。Demo 使用系统临时目录，每次运行创建新的验收文件，不修改项目 `data` 中的存档。两种仓库都应输出编号 1、标题“投影仪无法开机”、状态 `IN_PROGRESS`、工程师 20；新建文件仓库后应恢复相同内容，数量为 1。

2026-10-21 已实际编译运行该 Demo，确认两种实现的上述流程与新仓库重新加载通过。这是在同一进程内重新创建仓库；控制台关闭后重启的恢复，以及 JAR 菜单运行，学习者已反馈手动验证通过。

JUnit 文件往返测试使用 `@TempDir`，不操作项目存档。早期 Demo 仍保留：`TicketFileDemo`、`TicketEmptyDemo`、`TicketRestartSaveDemo` 会写各自的演示存档；`TicketAutoSaveDemo` 每次运行会向自己的存档新增一张工单，使用前应查看路径和写入行为。

## 目录

```text
JavaProject/
├── tickets.http                           # 手动 HTTP 请求
├── pom.xml
├── README.md
├── docs/                                  # 需求、设计和验收说明
├── sql/                                   # 三表及练习SQL；尚非自动迁移脚本
├── src/
│   ├── main/java/cn/wishbottle/opsticket/
│   │   ├── OpsTicketApplication.java       # Web启动入口
│   │   ├── controller/
│   │   │   ├── HelloController.java
│   │   │   ├── TicketController.java        # 文件版查询、关键词和创建
│   │   │   └── DatabaseTicketController.java # 数据库版查询和创建
│   │   ├── config/TicketConfig.java        # Bean 配置
│   │   ├── dto/、mapper/TicketMapper.java   # 请求/响应数据和数据库 SQL 映射
│   │   ├── DatabaseTicket*Service.java       # 数据库查询和创建业务
│   │   ├── DatabaseTicketRepository.java    # 数据库查询、创建及事务边界
│   │   ├── exception/GlobalExceptionHandler.java # 统一错误响应
│   │   ├── ConsoleApp.java
│   │   ├── Ticket.java
│   │   ├── TicketStatus.java
│   │   ├── TicketService.java
│   │   ├── TicketRepository.java
│   │   ├── InMemoryTicketRepository.java
│   │   ├── FileTicketRepository.java
│   │   └── TicketFileStore.java
│   └── test/java/                          # JUnit、隔离数据库测试、Demo 和练习
├── data/                                  # 控制台存档、演示数据与坏存档样本
│   ├── tickets-app.properties             # 控制台运行时保存
│   ├── tickets-auto-demo.properties       # 自动保存演示使用
│   └── ……其他演示存档与异常样本
└── .gitignore
```

`target/`、`out/`、`.qa/`、`.idea/`、`*.class`、`*.iml` 已忽略，不提交构建产物与本机 IDE 配置。两个本地运行存档 `data/tickets-app.properties`、`data/tickets-auto-demo.properties` 也已精准忽略；正常和错误验收样本继续保留在 Git 中。

## 已知限制

- 当前正式 Web 仍使用文件仓库查询与创建；`/api/db`提供只读摘要/领域对象查询和数据库创建POST，正式业务尚未切换到数据库仓库。数据库创建已接通`CreateDatabaseTicketRequest`、`DatabaseTicketCommandService`、`TicketWriteRepository`和`TicketMapper.insertTicket`；数据库派单/解决/验收、HTTP改名、登录权限及处理/验收状态流尚未接入。当前文件仓库新编号来自最大编号加一，没有并发或重复请求保护。
- 保存直接覆盖目标文件，尚无原子替换、备份或事务机制；写入中断可能损坏存档。
- 保存失败时控制台提示并退出，不打印操作成功；此前发生的内存修改不会自动回滚。
- 多个程序同时操作同一存档文件时没有并发保护。
- 查询返回的新列表隔离了列表结构，但其中的工单仍可能是仓库中的原对象。调用方修改工单后必须显式更新仓库，业务操作统一走 Service。

## 学习进度与下一步

截至 11 月 9 日，已用断点区分请求体转换与业务校验，完成 ErrorResponse 和方法参数类型错误等统一处理。11月9日完成数据库创建POST：`CreateDatabaseTicketRequest`、`DatabaseTicketCommandService`、`POST /api/db/tickets`、`DataIntegrityViolationException`处理已接通；学习者自行POST得到id=9，助手验证合法201、GET列表、外键/标题/编号错误400并核对数据库行。正式 `/api/tickets` 仍使用文件仓库；数据库派单/解决/验收、权限和AI尚未接入。

11 月 13 日助手补充了数据库创建的事务保护和自动验证；这属于代码已有能力，事务注解及测试原理仍需要本人学习。下一步先解释现有创建链路和事务，再进入数据库派单。

| 阶段 | 亲手交付 | 达标证据 |
| --- | --- | --- |
| A Java工单业务 | 读懂现有事务与数据库创建；逐步完成派单、状态与必要鉴权 | 能独立画请求链并解释回滚；派单接口、失败分支及授权按实际结果记录 |
| Y Python基础 | venv、数据结构、函数/异常、JSON/HTTP；用虚构工单写查询小程序 | 自己写并调试按ID查询和空结果；解释Java Map/List与Python dict/list的区别 |
| B Python模型调用 | 先用虚构数据请求一个模型，返回摘要和待补充信息；模拟错误 | 保存真实调用与模拟测试各一份证据，校验结构、超时与错误；没有API时仅标契约测试 |
| G Python只读Agent | 先对假数据接查询工具，完成查找→追问/详情→回答，记录步骤 | 真实模型发出工具调用、Python执行；无结果、坏参数、超时和步数限制可复现 |
| C 资料与评测 | 维护少量自编设备资料，检索并引用；用固定任务集改进 | 引用可定位；区分检索、工具、生成错误，记录真实样本数、耗时与用量 |
| L 安全联调 | Java提供经授权的只读工单接口，Python通过HTTP调用 | 隔离演示数据、真实身份与授权已验证；无权请求不能读取；超时/故障可解释 |

Python原型先使用虚构工单与受控只读工具；真实工单联调前Java必须具备认证、资源范围和服务身份校验。现有业务数据、接口和代码不因方案调整而改变。Redis基础及虚构数据缓存、会话记忆列入计划，在具备相应基础后逐步实践，不阻挡首个内存版Agent。MCP、SubAgent、写工具和微服务按需后置。

**下一项亲手任务**：先读 `DatabaseTicketRepository.create`，画出POST→Service→Repository→Mapper→MySQL调用链，解释 `@Transactional` 生效条件和失败回滚；同时开始Python基础，使用虚构工单列表练变量、列表、字典与函数。理解后继续数据库派单的接口和404/409；不在真实数据库上做未隔离的写入实验。
