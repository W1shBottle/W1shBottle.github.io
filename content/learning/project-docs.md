{
  "title": "设备运维工单项目文档",
  "description": "当前控制台与 SQL 进度、Java＋AI 路线和运行入口。",
  "date": "2026-10-21T00:00:00+08:00",
  "lastmod": "2026-10-28T00:00:00+08:00",
  "weight": 160,
  "group": "project-docs",
  "draft": false
}

> 本组文档对应项目当前实现，与[总体规划](/learning/project/)配合阅读。后续功能以各页的实现状态为准。

围绕“设备报修 → 派单 → 处理 → 验收”逐步开发的 **Java＋AI 学习项目**，沿用现有工单主题和代码。当前仍是 **v0.1 控制台实现**：内存/文件仓库、自动保存和启动恢复可运行；MySQL 三表和 SQL 练习已有成果，独立 JDBC Demo 已可查询真实数据库，正式控制台尚未改用数据库仓库。HTTP、处理/验收、登录权限、AI 和 Agent 均待实现。项目定位改变不代表功能已完成。

文档核对日期：2026-10-28。路线改为 A 后端业务与基础工程 → B 一个真实 AI 功能 → C 验证与改进；受控 Agent 按需要扩展。历史笔记保留当时进度，课程材料原“周号”只作索引，不承诺固定周数掌握。

## 项目文档

| 文档 | 解决的问题 |
| --- | --- |
| [需求与开发计划](/learning/project-requirements/) | 业务规则、已实现功能和待完成任务 |
| [设计与数据约定](/learning/project-design/) | 类的分工、方法契约、状态和存档格式 |
| [运行与验收](/learning/project-verification/) | 环境、运行命令、测试证据和验收边界 |

学习入口：[路线说明](/learning/start/) · [阶段计划](/learning/schedule/) · [技能清单](/learning/checklists/) · [实际学习进度](/learning/#progress)。本组项目文档记录实现与验收，课程材料记录后续学习安排。

## 当前功能与职责

- `ConsoleApp` 负责菜单、输入与输出，支持新建、查看全部、修改标题、派单、按标题关键词查询和退出。数字格式或业务输入错误会提示并返回菜单。
- `Ticket` 负责编号、标题和派单规则：编号为正数；标题去除首尾空白后非空且不超过 50 个字符；仅待派单工单可以派给正数编号的工程师。
- `TicketService` 通过构造器接收 `TicketRepository`，共用创建、改标题、派单和查询逻辑。创建编号为已有最大编号加 1，空仓库从 1 开始；关键词按去除首尾空白后的文字做区分大小写的包含匹配。状态筛选方法已实现，尚未接入菜单。
- `TicketRepository` 约定 `add`、`findById`、`findAll`、`update`。新增重复编号、更新不存在编号会被拒绝；查询不存在编号时仓库返回空 `Optional`，Service 的 `findById` 则返回 `null`。
- `InMemoryTicketRepository` 使用 `LinkedHashMap` 保存运行期间的数据，程序结束后不保留。
- `FileTicketRepository` 内部复用内存仓库：启动时从文件恢复，查询时访问内存，新增或更新时先修改内存，再保存全部工单。缺少存档文件时按空仓库启动；其他读取错误或坏存档会使控制台提示并停止启动。
- `TicketFileStore` 以 UTF-8 和 Properties 格式读写列表，用 `count` 记录数量；加载时检查缺字段、数字和状态格式、负数量、重复编号，以及状态与处理人的一致性。加载失败不返回部分结果，包装异常时保留原始原因。

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

### MySQL 与 JDBC 环境（2026-10-28）

当前学习环境为 MySQL 8.4.13 LTS 与 Connector/J 26.10.0。在 IDEA 重新加载 Maven 依赖；数据库地址、账号和密码按自己的本机环境配置。升级前已有备份，助手完成恢复、数据一致性与真实 JDBC 验证；安装路径、账号材料和回退操作保留在本地，不公开。

学习者随后完成独立 JDBC 查询 Demo；正式控制台仍使用文件仓库，Java 更新事务待亲手实现。详见[运行与验收](/learning/project-verification/)。

### 存档位置

正式控制台使用 `data/tickets-app.properties`。这是相对于**运行时工作目录**的路径，并非相对于 JAR 所在目录；启动时会打印绝对路径。请在项目根目录运行，并确保 `data` 目录存在，保存方法不会自动创建父目录。

关闭后重新启动会恢复已有工单。成功的新建、修改标题和派单会自动保存，不需要手动调用文件工具。

### JDBC 查询练习

测试源码中的 `JdbcTicketQueryDemo` 从 `OPS_TICKET_DB_PASSWORD` 读取数据库密码；在 IDEA 对应运行配置中填写，不写入源码或公开截图。同一个连接查询待派单和处理中工单，方法自行关闭 statement/resultSet，连接由 main 关闭。它是手动运行的 main Demo，不由 `mvn test` 自动执行。

## 验证方式

```powershell
mvn test
```

2026-10-26 使用 JDK 21 执行离线 `package` 成功；2026-10-28 更新驱动后再次执行 `mvn test`，17 项测试全部通过。现有 17 个 JUnit 测试：`TicketTest` 6 个、`TicketFileStoreTest` 2 个、`InMemoryTicketRepositoryTest` 7 个、`TicketServiceTest` 2 个。现有测试覆盖标题校验、文件往返、部分仓库契约和 Service 行为，不代表所有功能与故障场景均已自动覆盖。`update(null)` 的同类练习已跳过，不计入测试数量。

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
├── pom.xml
├── README.md
├── docs/                                  # 需求、设计和验收说明
├── sql/                                   # 三表及练习SQL；尚非自动迁移脚本
├── src/
│   ├── main/java/cn/wishbottle/opsticket/
│   │   ├── ConsoleApp.java
│   │   ├── Ticket.java
│   │   ├── TicketStatus.java
│   │   ├── TicketService.java
│   │   ├── TicketRepository.java
│   │   ├── InMemoryTicketRepository.java
│   │   ├── FileTicketRepository.java
│   │   └── TicketFileStore.java
│   └── test/java/cn/wishbottle/opsticket/   # JUnit、Demo 和 ArrayPractice
├── data/                                  # 控制台存档、演示数据与坏存档样本
│   ├── tickets-app.properties             # 控制台运行时保存
│   ├── tickets-auto-demo.properties       # 自动保存演示使用
│   └── ……其他演示存档与异常样本
└── .gitignore
```

`target/`、`out/`、`.qa/`、`.idea/`、`*.class`、`*.iml` 已忽略，不提交构建产物与本机 IDE 配置。两个本地运行存档 `data/tickets-app.properties`、`data/tickets-auto-demo.properties` 也已精准忽略；正常和错误验收样本继续保留在 Git 中。

## 已知限制

- 当前为本地控制台程序；SQL 文件已有用户、设备、工单三表，独立 JDBC 查询 Demo 已实现，正式数据库仓库、HTTP、登录权限和处理/验收状态流尚未实现。
- 保存直接覆盖目标文件，尚无原子替换、备份或事务机制；写入中断可能损坏存档。
- 保存失败时控制台提示并退出，不打印操作成功；此前发生的内存修改不会自动回滚。
- 多个程序同时操作同一存档文件时没有并发保护。
- 查询返回的新列表隔离了列表结构，但其中的工单仍可能是仓库中的原对象。调用方修改工单后必须显式更新仓库，业务操作统一走 Service。

## 学习进度与下一步

前三个原课程单元已完成相应练习；部分接线与修复有助手帮助，不能记成全独立实现。JOIN 的 OPEN 筛选、COUNT/GROUP BY/HAVING、稳定分页与同条件总数已按指导练习并反馈结果；SQL 提交/回滚、条件更新和双连接版本竞争已有运行反馈。JdbcTicketQueryDemo 已使用同一 Connection 依次查询 OPEN/IN_PROGRESS，处理 SQL NULL 并提取 printTicketsByStatus，学习者反馈运行成功、助手读取源码核对。Java 更新事务尚待亲手练习，正式业务仍用文件仓库，Web/权限/AI 未接入。

| 阶段 | 具体交付 | 进入下一阶段的条件 |
| --- | --- | --- |
| A1 最小后端闭环 | Java 21＋Spring Boot＋MyBatis＋MySQL；创建/查询→派单→提交处理说明→验收关闭 | 单条链路持久化，状态规则与基础异常明确；本地学习使用，不提前公开部署 |
| A2 基础工程 | 三角色登录/归属权限、参数校验、事务与操作日志、重复/并发请求、关键测试、部署排错 | 能独立修改一项业务并解释请求→Service→SQL；权限失败、回滚和重启有实测 |
| B 首个 AI 功能 | 对有权访问的工单描述生成摘要、分类建议、待补充信息；用户决定采纳 | 真实模型调用、结构校验、超时/错误降级和固定案例；模型停用时业务仍可运行 |
| C 验证与改进 | 比较无 AI 基线，记录效果、失败、延迟与实际调用用量/成本 | 可复现评估和一次针对失败样本的改进；再决定是否做 RAG 或受控工具 Agent |

A1/A2 分别完成最小业务与基础工程；B/C 分别完成 AI 接入与效果验证。评估贯穿 B；Agent 是达到门槛后的可选升级，不是必须做的第四个大项目。

首版只保留工单闭环、必要查询和权限。设备和用户用演示种子数据；评论、退回、统计看板、全套管理界面、Redis、消息队列、微服务、Kubernetes 延后。AI 编程辅助与产品内 AI 功能分别验收，不以生成代码量计进度。

**下一项亲手任务**：在单独的 JdbcTicketUpdateDemo 中学习 executeUpdate、setAutoCommit(false)、影响行数和显式 rollback：读取当前版本，修改指定标题后回滚，重新查询确认标题与版本恢复；先讲清事务边界，再由学习者亲手实现。 学习复盘见[10月28日笔记](https://wishbottle.cn/posts/ops-ticket-20261028/)。
