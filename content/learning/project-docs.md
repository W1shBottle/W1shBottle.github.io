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

围绕“设备报修 → 派单 → 处理 → 验收”逐步开发的 Java 项目。当前处于 **v0.1 开发阶段**，已实现领域对象、集合管理、工单列表文件存取和基础自动化测试；版本名称是里程碑规划，尚未发布正式版本。

文档核对日期：2026-10-17（凌晨）。本次学习归 2026-10-16，包含持续到次日凌晨的学习。

## 项目文档

| 文档 | 解决的问题 |
| --- | --- |
| [需求与开发计划](/learning/project-requirements/) | 业务规则、已实现功能和待完成任务 |
| [设计与数据约定](/learning/project-design/) | 类的分工、方法契约、状态和存档格式 |
| [运行与验收](/learning/project-verification/) | 环境、运行命令、测试证据和验收边界 |

课程路线见 [博客学习板块](https://wishbottle.cn/learning/)。课程负责安排学习顺序，仓库文档描述项目现状；源码、实际验证和学习记录共同作为进度依据。

## 当前能力与边界

- 工单编号、标题校验，修改标题时复用校验规则，非法修改保留原标题。
- 待处理工单派给正数编号的工程师，拒绝重复派单。
- 使用 LinkedHashMap 按编号管理工单，支持编号查询、状态筛选和取得全部工单。
- TicketFileStore.save 以 UTF-8 保存列表；loadAll 按 count 读取、检查字段、恢复工单，使用 Set 拒绝存档中的重复编号。
- 空列表保存为 count=0，读回非 null 的空列表；第二张工单缺字段时抛异常，不返回部分结果。
- TicketLoadDemo 在完整读取成功后，把工单逐张加入新 TicketService，并查询恢复后的数量和状态。
- 已引入 Maven 和 JUnit Jupiter，当前有 8 个正式 JUnit 测试：标题修改 6 项、文件往返 2 项。普通 Demo 与独立练习仍保留。

**尚未实现**自动生成编号的 TicketService.create(String title)、首次无文件时初始化空服务、带记录位置和字段名的完整错误提示，以及保存—退出—重启—继续编号的整体验收。保存直接覆盖目标文件，尚无原子替换或备份保护。数据库、HTTP 接口、登录权限与完整状态流属于后续规划。

## 快速运行

当前使用 Maven，编译目标为 **Java 21**。先配置 JDK 21 和 Maven，并在项目根目录检查：

```powershell
java -version
javac -version
mvn -v
mvn test
```

三处 Java 环境应核对一致，尤其是 mvn -v 中实际使用的 Java。项目的 JUnit 依赖与插件首次运行时需要下载；JDK 8 已不适用于当前完整项目。

也可以在 IDEA 中加载 pom.xml，设置项目 SDK 和 Maven Runner 使用 JDK 21，再在 Maven 面板运行 test。没有配置命令行 mvn 时，可先使用 IDEA 自带的 Maven；项目尚未提供 Maven Wrapper。

mvn test 自动执行符合命名约定的 JUnit 测试，**不会自动执行每个 Demo 的 main 方法**。需要运行普通演示时，先编译测试源码，再运行对应类：

```powershell
mvn test-compile
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' TicketServiceDemo
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' TicketLoadDemo
```

上面的 classpath 分隔符适用于 Windows PowerShell。IDEA 中也可直接运行 Demo 的 main。项目仍使用默认包；文件 Demo 的工作目录必须为项目根目录，使用其中的 data/。

当前没有可直接 java -jar 启动的应用入口配置。详细输出、存档写入影响及测试范围见 [运行与验收](/learning/project-verification/)。

## 目录

```text
JavaProject/
├── pom.xml                       # Java 21、JUnit 和 Maven 插件配置
├── README.md
├── docs/
│   ├── requirements.md
│   ├── design.md
│   └── verification.md
├── src/
│   ├── main/java/                # 4 个业务类
│   │   ├── Ticket.java
│   │   ├── TicketStatus.java
│   │   ├── TicketService.java
│   │   └── TicketFileStore.java
│   └── test/java/                # JUnit、main Demo 与独立练习
│       ├── TicketTest.java
│       ├── TicketFileStoreTest.java
│       ├── TicketDemo.java
│       ├── TicketPractice.java
│       ├── TicketArrayDemo.java
│       ├── TicketServiceDemo.java
│       ├── TicketFileDemo.java
│       ├── TicketLoadDemo.java
│       ├── TicketLoadFailureDemo.java
│       ├── TicketEmptyDemo.java
│       ├── ArrayPractice.java
│       └── TitleValidationPractice.java
├── data/
│   ├── tickets.properties        # 正常两张工单存档
│   ├── tickets-invalid.properties # 缺少第二张标题的测试副本
│   ├── tickets-empty.properties  # count=0 的空列表存档
│   ├── ticket-demo.properties    # 早期单张工单练习
│   └── ticket-invalid.properties # 早期单张坏存档练习
└── .gitignore
```

TicketFileDemo 会生成或覆盖 data/tickets.properties，TicketEmptyDemo 会生成或覆盖 data/tickets-empty.properties。当前 save 不自动创建父目录，需保留 data 文件夹。JUnit 文件测试使用 @TempDir 分配的临时目录，不操作这些项目存档。

target/ 为 Maven 生成目录，out/ 是早期编译输出；两者及 .qa/、.idea/、*.class 均已忽略，不提交构建产物。

## 学习进度与下一步

第一周的数组最大值、独立标题校验和 static 概念补验收已经完成；第二周已补齐 Set 检测重复编号、Map 统计数字次数、读回列表加入服务。主线仍在第二周，整周尚未完成。

Maven 属于原计划第三周，本次提前接触了 Maven 和 JUnit；保留现有工具和测试，暂停继续扩展第三周内容，先补齐前两周验收。

下一步由学习者实现 **TicketService.create(String title)**：遍历当前工单找最大编号，用最大编号加 1 创建并加入服务，返回新工单；空服务从 1 开始，标题非法时不增加记录。该方法目前仅布置，尚未编写或验收。随后补首次无文件、坏存档明确报错，以及完整重启后继续编号的流程。

新增业务功能时同步更新需求、方法契约和验收记录。测试通过只代表对应场景通过，不等同于全部业务或整周学习目标完成。
