{
  "title": "设备运维工单项目文档",
  "description": "项目当前能力、代码结构和运行入口。",
  "date": "2026-10-17T00:00:00+08:00",
  "lastmod": "2026-10-17T00:00:00+08:00",
  "weight": 160,
  "group": "project-docs",
  "draft": false
}

> 本组文档对应项目当前实现，与[总体规划](/learning/project/)配合阅读。后续功能以各页的实现状态为准。

围绕“设备报修 → 派单 → 处理 → 验收”逐步开发的 Java 项目。当前处于 **v0.1 开发阶段**，已完成第二周集合与文件恢复验收，进入第三周的 Maven、包结构和接口学习；尚未发布正式版本。

文档核对日期：2026-10-17。本页描述当前实现，2026-10-16 至 17 日凌晨的前一轮学习另按 10 月 16 日归档。

## 项目文档

| 文档 | 解决的问题 |
| --- | --- |
| [需求与开发计划](/learning/project-requirements/) | 业务规则、已实现功能和待完成任务 |
| [设计与数据约定](/learning/project-design/) | 类的分工、方法契约、状态和存档格式 |
| [运行与验收](/learning/project-verification/) | 环境、运行命令、测试证据和验收边界 |

课程路线见 [博客学习板块](https://wishbottle.cn/learning/)。课程安排学习顺序，仓库文档记录项目现状；源码、实际验证和学习记录共同作为进度依据。

## 当前能力与边界

- 工单编号、标题校验；修改标题时复用校验，失败保留原标题；仅待派单工单可以分配给正数编号的工程师。
- `TicketService` 使用 `LinkedHashMap` 管理工单，支持新增、编号查询、状态筛选和返回全部工单。`create(String title)` 按现有最大编号加 1 创建，空服务从 1 开始，非法标题不增加记录。
- `TicketFileStore` 以 UTF-8 保存列表，按 `count` 读回并恢复；检查缺字段、数字和状态格式、负数量、重复编号及状态与处理人一致性。错误会补充字段名或记录位置，包装异常时保留原始原因。
- `TicketStartupDemo` 在正常加载后恢复服务；缺文件时使用空服务，其他读取错误或内容错误会停止启动，不保存覆盖坏存档。
- 已通过两次独立运行验证创建、派单、保存、重启读取、状态筛选和接续编号 4；标题中的等号与反斜杠可以往返恢复。
- 已迁入 `cn.wishbottle.opsticket` 包，Maven 编译目标 Java 21。正式 JUnit 源码共 10 项：标题 6 项、文件往返 2 项、内存仓库查询 2 项；普通 Demo 与练习继续保留。
- 新增 `TicketRepository` 接口和 `InMemoryTicketRepository` 实现，提供 `add`、`findById`、`findAll`、`update`。**仓库尚未接入 `TicketService`**，两者目前各自持有 Map。

第二周验收通过不代表项目全部完成。仓库的重复新增、更新、空值和返回列表等边界测试仍待补齐；数据库、HTTP 接口、登录权限和完整状态流尚未实现。文件保存仍直接覆盖目标，尚无原子替换或备份机制。

## 快速构建与运行

使用 **JDK 21** 和 Maven。IDEA 中加载 `pom.xml`，核对项目 SDK 与 Maven Runner 使用的 JDK；也可以配置好命令行环境后，在项目根目录执行：

```powershell
java -version
javac -version
mvn -v
mvn clean package
```

`clean` 清理 `target` 构建产物，`package` 依次执行编译、测试、打包。成功时显示 `BUILD SUCCESS`，生成 `target/ops-ticket-0.1.0-SNAPSHOT.jar`。这是普通 JAR，尚未配置可直接 `java -jar` 启动的入口。

上述 `mvn` 命令以终端已配置 Maven 为前提；没有全局 `mvn` 时，可使用 IDEA 的 Maven 面板或自带 Maven 的可执行文件。当前学习中只在单个 PowerShell 会话临时切换过 `JAVA_HOME` 和 `PATH`，并核对 Java、javac 和 Maven 使用 Java 21.0.8；关闭终端后需要重新核对，未永久修改系统环境。项目没有 Maven Wrapper，首次运行需要下载依赖。

`mvn test` 运行符合命名约定的 JUnit 测试，**不会自动运行带 main 的 Demo**。下面是 Windows PowerShell 的示例：

```powershell
mvn test-compile
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' cn.wishbottle.opsticket.TicketServiceDemo
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' cn.wishbottle.opsticket.TicketRestartLoadDemo
```

包迁移后使用完整类名。文件 Demo 的工作目录应为项目根目录；第二条需要先存在 `data/tickets-restart.properties`。IDEA 中也可从移动后的 `main` 重新运行。详细输出和写入影响见 [运行与验收](/learning/project-verification/)。

## 目录

```text
JavaProject/
├── pom.xml
├── README.md
├── docs/
│   ├── requirements.md
│   ├── design.md
│   └── verification.md
├── src/
│   ├── main/java/cn/wishbottle/opsticket/  # 6 个业务源码文件（含接口）
│   │   ├── Ticket.java
│   │   ├── TicketStatus.java
│   │   ├── TicketService.java
│   │   ├── TicketFileStore.java
│   │   ├── TicketRepository.java
│   │   └── InMemoryTicketRepository.java
│   └── test/java/cn/wishbottle/opsticket/  # 18 个测试、Demo 与练习源码
│       ├── TicketTest.java
│       ├── TicketFileStoreTest.java
│       ├── InMemoryTicketRepositoryTest.java
│       ├── TicketStartupDemo.java
│       ├── TicketRestartSaveDemo.java
│       ├── TicketRestartLoadDemo.java
│       └── ……其他 Demo 与练习
├── data/
│   ├── tickets.properties                # 正常两张工单
│   ├── tickets-empty.properties          # count=0
│   ├── tickets-restart.properties        # 重启验收的三张工单
│   ├── tickets-invalid*.properties       # 缺字段、数字、状态等坏存档副本
│   ├── tickets-restart-invalid.properties
│   └── ticket-*.properties               # 早期单张工单练习
└── .gitignore
```

`TicketFileDemo` 会覆盖 `data/tickets.properties`；`TicketEmptyDemo` 会覆盖空列表存档；`TicketRestartSaveDemo` 会覆盖重启验收存档。读取和启动 Demo 不写文件，读取端新建的编号 4 只在内存中。`save` 不自动创建父目录，需保留 `data`。

JUnit 文件测试使用 `@TempDir`，不操作这些项目存档。`target/`、`out/`、`.qa/`、`.idea/`、`*.class`、`*.iml` 均已忽略，不提交构建产物和本机 IDE 配置。

## 学习进度与下一步

第一周补漏和第二周这一轮功能、运行、理解验收已完成。第三周已经完成环境核对、Maven 构建和包迁移，开始接口与实现类；`@Override` 建议标在接口实现方法上，但注解本身并非强制，实现接口约定的方法才是当前普通实现类的要求。

下一课先补 `InMemoryTicketRepositoryTest`：重复新增不能覆盖原对象；更新存在编号能替换对象，更新不存在编号不能偷偷新增；拒绝 null；清空 `findAll` 返回列表不改变仓库数量。区分“新列表”与“列表中的工单仍是原对象引用”。仓库行为验证后，再让 `TicketService` 通过接口使用仓库。