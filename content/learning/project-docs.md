{
  "title": "设备运维工单项目文档",
  "description": "项目当前能力、代码结构和运行入口。",
  "date": "2026-10-21T00:00:00+08:00",
  "lastmod": "2026-10-21T00:00:00+08:00",
  "weight": 160,
  "group": "project-docs",
  "draft": false
}

> 本组文档对应项目当前实现，与[总体规划](/learning/project/)配合阅读。后续功能以各页的实现状态为准。

围绕“设备报修 → 派单 → 处理 → 验收”逐步开发的 Java 学习项目。当前为 **v0.1 开发阶段**：已实现可运行的控制台、可切换的内存与文件仓库，以及文件自动保存与启动恢复。完整处理、验收流程仍待实现，尚未发布正式版本。

文档核对日期：2026-10-21。本页记录当前代码和验收情况；历史学习笔记保留各自日期的进度。

## 项目文档

| 文档 | 解决的问题 |
| --- | --- |
| [需求与开发计划](/learning/project-requirements/) | 业务规则、已实现功能和待完成任务 |
| [设计与数据约定](/learning/project-design/) | 类的分工、方法契约、状态和存档格式 |
| [运行与验收](/learning/project-verification/) | 环境、运行命令、测试证据和验收边界 |

课程路线见 [博客学习板块](https://wishbottle.cn/learning/)。README 与上述详细文档已按 2026-10-21 的实现和验收记录同步。

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

### 存档位置

正式控制台使用 `data/tickets-app.properties`。这是相对于**运行时工作目录**的路径，并非相对于 JAR 所在目录；启动时会打印绝对路径。请在项目根目录运行，并确保 `data` 目录存在，保存方法不会自动创建父目录。

关闭后重新启动会恢复已有工单。成功的新建、修改标题和派单会自动保存，不需要手动调用文件工具。

## 验证方式

```powershell
mvn test
```

目前有 17 个 JUnit 测试：`TicketTest` 6 个、`TicketFileStoreTest` 2 个、`InMemoryTicketRepositoryTest` 7 个、`TicketServiceTest` 2 个。现有测试覆盖标题校验、文件往返、部分仓库契约和 Service 行为，不代表所有功能与故障场景均已自动覆盖。`update(null)` 的同类练习已跳过，不计入测试数量。

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

- 当前为本地控制台程序，数据库、HTTP 接口、登录权限和完整的处理、验收状态流尚未实现。
- 保存直接覆盖目标文件，尚无原子替换、备份或事务机制；写入中断可能损坏存档。
- 保存失败时控制台提示并退出，不打印操作成功；此前发生的内存修改不会自动回滚。
- 多个程序同时操作同一存档文件时没有并发保护。
- 查询返回的新列表隔离了列表结构，但其中的工单仍可能是仓库中的原对象。调用方修改工单后必须显式更新仓库，业务操作统一走 Service。

## 学习进度与下一步

第一、二周基础与文件恢复验收已完成。第三周已完成 Java 21 环境核对、Maven 与包结构、接口和构造器传入依赖、两种仓库实现、控制台操作、可执行 JAR、关键词筛选、Lambda 入门，以及双循环和 Map 两种两数之和练习。

第三周代码阶段提交已完成（682b3c7）；共用业务流程、文件重新加载、17 项 JUnit 和打包已通过。README、需求、设计与验收文档已同步并以 ecc0f14 提交；之后的本次代码规范整理及补充验收记录尚未提交。下一阶段进入第四周的 MySQL 连接、独立练习库及用户、设备与工单三表设计。
