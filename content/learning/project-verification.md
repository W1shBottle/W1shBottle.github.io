{
  "title": "工单项目运行与验收",
  "description": "编译运行步骤、预期输出、验收清单和常见问题。",
  "date": "2026-10-13T00:00:00+08:00",
  "lastmod": "2026-10-13T00:00:00+08:00",
  "weight": 190,
  "group": "project-docs",
  "draft": false
}

[返回项目首页](/learning/project-docs/) · [需求](/learning/project-requirements/) · [设计](/learning/project-design/)

核对日期：2026-10-13。

## 1. 环境和编译

当前没有第三方依赖。需要安装 JDK，命令行能够找到 java 和 javac。本次验证环境为 Windows PowerShell、Temurin JDK 8（1.8.0_472）。后续计划在 Maven 阶段统一 JDK 21。

在项目根目录打开终端，检查：

```powershell
java -version
javac -version
```

编译全部源文件：

```powershell
New-Item -ItemType Directory -Force -Path out | Out-Null
$sourceFiles = (Get-ChildItem -LiteralPath .\src -Filter '*.java').FullName
javac -encoding UTF-8 -d out $sourceFiles
```

编译应无错误。若失败，先修复错误再运行，避免误跑上次编译留下的旧 class。每次修改源码后重新编译。

IDEA 运行时选择对应类的 main；文件 Demo 的 Working directory 应设为项目根目录（即包含 src 的 JavaProject 目录），两个 Demo 要一致。

## 2. 工单服务演示

```powershell
java '-Dfile.encoding=UTF-8' -cp out TicketServiceDemo
```

预期输出：

```text
IN_PROGRESS, 20
状态必须是OPEN
IN_PROGRESS, 20
OPEN, null
清空前：1
结果列表：0
重新查询：1
重新查询标题：打印机卡纸
是否同一对象：true
```

它验证了首次派单、重复派单失败后原数据保留、另一张工单不受影响、结果列表独立以及列表元素引用共享。

## 3. 单张工单文件演示

TicketFileDemo 会覆盖工作目录中的 ticket-demo.properties。已有需要保留的记录时，先复制备份，或在单独的练习目录运行。它保存的是代码里构造的示例工单，不是服务集合。

确认可覆盖示例文件后，在项目根目录先运行：

```powershell
java '-Dfile.encoding=UTF-8' -cp out TicketFileDemo
```

预期包含：

```text
1001
投影仪无信号
IN_PROGRESS
处理人：[20]
保存成功：<工作目录>\ticket-demo.properties
```

随后读取：

```powershell
java '-Dfile.encoding=UTF-8' -cp out TicketLoadDemo
```

预期包含：

```text
读取文件：<工作目录>\ticket-demo.properties
编号：1001
标题：投影仪无信号
状态：IN_PROGRESS
处理人：20
```

这些结果从恢复后的 Ticket 对象 getter 取得，证明该单张工单的编号、标题、状态和处理人已恢复。

## 4. 验收清单

下面区分已运行的当前 Demo 和应补充为自动化测试的场景。没有把所有清单项都算作本次通过。

| 场景 | 预期 | 本次文档整理验证 |
| --- | --- | --- |
| 编译所有 src/*.java | 编译成功 | 通过 |
| 派单给 20 后再次派给 30 | 第二次失败，仍为 IN_PROGRESS / 20 | TicketServiceDemo 通过 |
| 清空筛选结果后重新查询 | 服务里的待处理工单仍存在 | TicketServiceDemo 通过 |
| 修改筛选结果中的工单 | 服务查询得到修改后的同一对象 | TicketServiceDemo 通过 |
| 保存后读回中文、状态与处理人 | 中文一致，IN_PROGRESS，处理人 20 | 两个文件 Demo 在临时目录运行通过 |
| 标题 null、空白、50/51 长度边界 | 非法值拒绝，合法值接受；失败不改旧值 | 需整理为可重复自动化测试 |
| 添加 null、重复编号 | 拒绝且不覆盖原记录 | 需整理为可重复自动化测试 |
| 查询不存在编号、无匹配状态、null 状态 | 分别为 null、空列表、异常 | 需整理为可重复自动化测试 |
| 派给 0 或负数 | 拒绝且保持原状态和处理人 | 需整理为可重复自动化测试 |
| 完整加载多张工单 | 数量、编号、标题、状态、处理人一致 | 功能待实现 |
| 恢复入口的合法与非法参数 | 检查状态和处理人组合，沿用编号、标题校验 | 助手临时程序 21 项检查通过 |
| 文件缺字段、非法枚举或非法编号 | 当前代码会抛出异常，不返回合法工单 | 已有检查逻辑；尚未逐项验证坏文件加载路径 |
| 多条存档中重复编号及加载失败保护 | 报告错误，不污染服务或覆盖原存档 | 功能待实现 |
| 首次运行没有存档 | 按约定初始化空服务 | 功能待实现；当前 Demo 打印读取失败 |

文件保存演示在独立临时目录中验证，未覆盖项目现有的示例存档。随后对象恢复阶段重新编译全部源码，运行项目现有存档读取，读取前后哈希一致；21 项恢复检查在助手创建的临时程序中完成。当前仓库主要依靠 main 演示，没有 JUnit 测试套件；这些 Demo 不能代替完整的回归测试。

## 5. 常见问题

### 找不到文件

先看 TicketLoadDemo 打印的绝对路径。检查是否先运行保存 Demo，以及保存和读取时的工作目录是否一致。

### 中文乱码

先区分源文件、存档内容、IDE 显示和终端显示。当前文件读写代码已经显式使用 UTF-8。IDEA 的 Properties 文件编码也应按 UTF-8 查看；不要在乱码状态下另存覆盖原文件。终端字体或编码问题需要单独排查，修改项目路径不会替代文件编码设置。

### 读到 null 或空处理人

getProperty 缺少对应键时返回 null；文件中 assigneeId= 表示键存在但值为空字符串。二者含义不同。当前 Demo 拒绝缺字段，将空处理人转为 null，再由 Ticket.restore 检查其是否符合工单状态。

### 异常后仍继续执行了后面的代码

throw 会中断当前执行路径；如果外层 catch 捕获了异常，程序可以继续执行 catch 后面的代码。两个文件 Demo 在 IOException 的 catch 中写了 return，所以读写失败时不会继续打印成功结果。
