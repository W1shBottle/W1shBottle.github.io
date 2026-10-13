{
  "title": "设备运维工单项目文档",
  "description": "项目当前能力、代码结构和运行入口。",
  "date": "2026-10-13T00:00:00+08:00",
  "lastmod": "2026-10-13T00:00:00+08:00",
  "weight": 160,
  "group": "project-docs",
  "draft": false
}

> 本组文档对应项目当前实现，与[总体规划](/learning/project/)配合阅读。后续功能以各页的实现状态为准。

围绕“设备报修 → 派单 → 处理 → 验收”逐步开发的 Java 项目。当前处于 **v0.1 开发阶段**，以控制台 Demo 验证领域对象、集合管理和文件读写；版本名称是里程碑规划，尚未发布正式版本。

文档核对日期：2026-10-13。

## 项目文档

| 文档 | 解决的问题 |
| --- | --- |
| [需求与开发计划](/learning/project-requirements/) | 为什么做、有哪些业务规则、已经做了什么、下一步做什么 |
| [设计与数据约定](/learning/project-design/) | 类如何分工、方法如何调用、状态和存档如何表达 |
| [运行与验收](/learning/project-verification/) | 怎么运行、如何判断结果正确、哪些验收还没有完成 |

课程路线见 [博客学习板块](https://wishbottle.cn/learning/)。课程负责安排学习顺序，本仓库文档负责描述项目本身；以源码与验证结果为依据更新。

## 当前能力

- 工单编号、标题校验，修改标题时复用校验规则。
- 待处理工单派给指定工程师，拒绝重复派单。
- 使用 LinkedHashMap 按编号管理工单，支持编号查询、状态筛选。
- 单张示例工单以 UTF-8 Properties 文件保存，另一个 Demo 读取、解析并通过校验恢复 Ticket 对象。

已完成单张工单恢复，尚未恢复整个 TicketService；count 未用于遍历，多张工单与加载失败保护仍待实现。数据库、HTTP 接口、登录权限与完整验收流程属于后续规划。

## 快速运行

当前是普通 Java 项目，没有 Maven 或 Gradle。需要 JDK（包含 javac）；本次命令验证使用 JDK 8。后续迁移 Maven 时计划统一到 JDK 21。

在项目根目录打开 PowerShell：

```powershell
New-Item -ItemType Directory -Force -Path out | Out-Null
$sourceFiles = (Get-ChildItem -LiteralPath .\src -Filter '*.java').FullName
javac -encoding UTF-8 -d out $sourceFiles
```

确认编译成功后运行：

```powershell
java '-Dfile.encoding=UTF-8' -cp out TicketServiceDemo
```

IDEA 中也可以直接运行对应类的 main 方法。文件读写 Demo 的运行顺序、工作目录与预期输出见 [运行与验收](/learning/project-verification/)。

## 目录

```text
JavaProject/
├── README.md
├── docs/
│   ├── requirements.md
│   ├── design.md
│   └── verification.md
├── src/
│   ├── Ticket.java
│   ├── TicketStatus.java
│   ├── TicketService.java
│   ├── TicketDemo.java
│   ├── TicketPractice.java
│   ├── TicketArrayDemo.java
│   ├── TicketServiceDemo.java
│   ├── TicketFileDemo.java
│   └── TicketLoadDemo.java
└── .gitignore
```

运行保存 Demo 会在工作目录生成 ticket-demo.properties；编译产物 out/ 已被 Git 忽略。

## 文档维护

新增业务功能时同步更新需求状态、方法契约和验收记录。数据库和 Web 阶段再补实际的数据库设计、接口文档与部署文档。演示成功仅代表对应场景通过；边界、异常和权限场景应分别记录。
