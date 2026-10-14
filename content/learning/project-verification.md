{
  "title": "工单项目运行与验收",
  "description": "编译运行步骤、预期输出、验收清单和常见问题。",
  "date": "2026-10-14T00:00:00+08:00",
  "lastmod": "2026-10-14T00:00:00+08:00",
  "weight": 190,
  "group": "project-docs",
  "draft": false
}

[返回项目首页](/learning/project-docs/) · [需求](/learning/project-requirements/) · [设计](/learning/project-design/)

核对日期：2026-10-14。

## 1. 环境与编译

当前为普通 Java 项目，没有第三方依赖、JUnit、Maven 或 Gradle。命令验证使用 Windows PowerShell 与 Temurin JDK 8（1.8.0_472），需要 java 和 javac；后续 Maven 阶段计划统一 JDK 21。

在项目根目录执行：

```powershell
java -version
javac -version
New-Item -ItemType Directory -Force -Path out | Out-Null
$sourceFiles = (Get-ChildItem -LiteralPath .\src -Filter '*.java').FullName
javac -encoding UTF-8 -d out $sourceFiles
```

编译成功后再运行，避免误跑旧 class。每次修改并保存源码后重新编译。IDEA 也可以运行对应类的 main；两个文件 Demo 的 Working directory 都应是包含 src 的项目根目录。

## 2. 工单服务演示

```powershell
java '-Dfile.encoding=UTF-8' -cp out TicketServiceDemo
```

已有运行证据覆盖首次派单、重复派单失败后原处理人保留、第二张工单不受影响、筛选结果列表独立但工单引用共享。新增 findAll 的演示输出为：

```text
全部工单数：2
结果列表数：0
服务中的工单数：2
```

清空返回的列表不会清空服务。本次日结整理没有重复运行这些已有证据的场景。

## 3. 多张工单正常保存和读取

TicketFileDemo 创建两张固定示例工单，加入服务后保存 findAll 的结果。它会覆盖工作目录下的 tickets.properties；有需保留的数据时先复制备份，或在单独练习目录运行。TicketLoadDemo 使用相同文件名。

正常验收前确认 TicketLoadDemo 第一张工单的预期编号为 1001L。收尾读取源码时仍为故意失败的 999L，需要改回并保存；这不表示文件恢复逻辑出错。

先保存，再读取：

```powershell
java '-Dfile.encoding=UTF-8' -cp out TicketFileDemo
java '-Dfile.encoding=UTF-8' -cp out TicketLoadDemo
```

保存端输出“保存成功：<工作目录>/tickets.properties”。正常读取预期：

```text
读取文件：<工作目录>/tickets.properties
测试通过：两张工单的所有字段都正确
读回数量：2
1001 | 投影仪无信号 | IN_PROGRESS | 20
1002 | 打印机卡纸 | OPEN | null
```

这个正常版本在教学检查时编译运行通过。断言先检查数量，再分别检查两张工单的编号、标题、状态与处理人，任何不一致都会抛 AssertionError。学习者还实际改错过预期编号，确认会报错；当前磁盘状态保留了该故意失败值，不能记作当前再次运行全通过。

这里只是固定示例场景的可重复断言，尚未建立完整测试套件。读取 IOException 和 IllegalArgumentException 仍会被打印后结束，不保证非零退出码；不能仅凭进程正常退出认定所有测试通过。

## 4. 下一项：第二张工单缺字段（待完成）

1. 复制 tickets.properties，副本命名 tickets-invalid.properties；避免用重命名重构改动正常文件及引用。
2. 从副本删除整行 ticket.1.title，保留 count=2 和其他字段；清空值测试的是空标题，含义不同。
3. 在待编写的 TicketLoadFailureDemo 中调用 loadAll。
4. 只有捕获预期的 IllegalArgumentException 且消息为“存档缺少必要字段”才算通过；正常返回应抛 AssertionError，IOException 不能算通过。
5. 临时补回标题，再运行应触发测试失败，之后恢复坏文件副本。

本练习目前只有教学步骤，没有对应源码或完成反馈。后续再测试空列表、count=0、缺失/负数/非法 count 以及重复编号。

## 5. 验收范围

| 场景 | 当前证据与限制 |
| --- | --- |
| 单张对象合法/非法状态恢复 | 前一课助手临时程序 21 项检查通过；不是仓库中的 JUnit 套件 |
| 文件类提取与单张存取 | 当天提取阶段已由助手验证，之后接口升级为多记录 |
| 单张非法数字与缺文件提示 | 提取阶段临时存档验证过内容异常与读取失败两个分支；不当作多记录坏文件验收 |
| 多张保存 | 当前示例存档含 count=2 和两张工单字段，保存检查已通过 |
| 多张正常读取及断言 | 正确预期版本经助手编译运行通过；用户也报告正常输出 |
| 改错预期编号 | 用户报告能触发 AssertionError；收尾源码仍为 999L，恢复正确预期后再跑正常测试 |
| 第二张缺标题，不返回部分结果 | 源码在 return 前抛异常；专门 Demo 与运行验证待完成 |
| 空列表与异常 count | 实现已有对应分支，专项存档测试待补 |
| 重复编号、整体恢复服务 | 待实现及验收 |
| 写入中途失败保护 | 未实现原子替换或备份 |
| 首次无文件自动初始化服务 | 待设计；当前 Demo 只报告读取失败 |

本次笔记整理依据已有运行记录和最新源码，没有为了文档补写学习者代码，也没有覆盖现有存档。

## 6. 常见问题

### catch 下面为什么一片报错

检查外层是否缺少 try，以及 for 与 try 的右括号是否分别闭合。catch 不能直接跟在 for 后面。

### 找不到文件

查看读取端打印的绝对路径。当前文件名是 tickets.properties，注意复数 s；保存和读取使用同一个工作目录。旧 ticket-demo.properties 不是当前默认文件。

### 中文乱码

源文件、存档、IDE 显示和终端显示要分开排查。文件读写已指定 UTF-8，IDEA 的 Properties 文件也应按 UTF-8 查看，避免将乱码另存覆盖原数据。

### null、空字符串和字符串 null

getProperty 找不到键返回 null；assigneeId= 返回空字符串，转换成无处理人的 null；文字 "null" 是字符串，会在当前编号解析中失败。测试第二张工单用 getAssigneeId() != null 作为失败条件。

### 报 AssertionError 是不是业务代码坏了

先确认预期值正确、读取文件正确。故意将 1001L 改为 999L 就应该失败，这是测试练习。修复后保存并重新编译，不要捕获后忽略 AssertionError 来制造通过结果。

### throw 后面还执行吗

当前正常路径会中断；找到外层匹配的 catch 后执行处理代码，之后可以继续 catch 后的语句。当前文件 Demo 的成功输出放在 try 中，发生读取异常后不会继续执行那些成功语句。
