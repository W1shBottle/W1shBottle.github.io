{
  "title": "工单项目运行与验收",
  "description": "编译运行步骤、预期输出、验收清单和常见问题。",
  "date": "2026-10-17T00:00:00+08:00",
  "lastmod": "2026-10-17T00:00:00+08:00",
  "weight": 190,
  "group": "project-docs",
  "draft": false
}

[返回项目首页](/learning/project-docs/) · [需求](/learning/project-requirements/) · [设计](/learning/project-design/)

核对日期：2026-10-17（凌晨）。本次学习归 2026-10-16，包含持续到次日凌晨的学习。本页区分现有源码、已有运行证据和待完成验收；本次日结整理不重复执行已通过的业务测试。

## 1. 环境与构建

当前为 Maven 项目，编译目标 Java 21。项目已配置 JUnit Jupiter 5.14.4、maven-compiler-plugin 3.13.0 和 maven-surefire-plugin 3.5.5。

命令行使用前配置 JDK 21、JAVA_HOME 和 Maven，并在项目根目录核对：

```powershell
java -version
javac -version
mvn -v
mvn test
```

重点检查 mvn -v 中实际使用的 Java，不要只看 IDEA 的项目 SDK。学习环境曾出现终端仍使用 JDK 8、IDEA 使用 JDK 21 的情况；已通过显式使用 JDK 21 和 IDEA 自带 Maven 运行测试，没有宣称系统 PATH 已统一。命令行尚未识别 mvn 时，可从 IDEA Maven 面板运行 test，并设置 Maven Runner 使用 JDK 21。

当前不再沿用早期“用 JDK 8 直接编译全部 Demo”的命令：测试源码已依赖 JUnit，部分练习使用较新的 Java API。项目没有 Maven Wrapper，也没有可直接 java -jar 启动的入口配置。

IDEA 加载 pom.xml 后，业务源码为 src/main/java，测试源码为 src/test/java；仍使用默认包。target/ 是 Maven 构建输出，已加入 .gitignore。

## 2. JUnit 自动测试

```powershell
mvn test
```

已有运行报告：Tests run: 8, Failures: 0, Errors: 0, Skipped: 0，BUILD SUCCESS。报告位于 target/surefire-reports。

| 测试类 | 场景 | 数量 |
| --- | --- | --- |
| TicketTest | 正常修改；拒绝 null 并保留原标题；接受 50 字符；拒绝 51 字符并保留原标题；先 trim 再检查长度；拒绝空白并保留原标题 | 6 |
| TicketFileStoreTest | 空列表保存读回；两张工单保存读回，逐项核对编号、标题、状态和处理人 | 2 |

学习者逐项运行并报告通过；助手核对源码并实际运行过 8 项测试。通过临时注释 rename 调用让测试失败，再恢复为通过，验证过断言确实检查实际行为。曾把期望值和自身比较的问题也已修正。

JUnit 文件测试使用 @TempDir。tempDir.resolve("tickets-empty.properties") 指向临时目录下的新文件路径；save 才创建文件。它只是与 data 中的文件同名，不会读取或覆盖 data/tickets-empty.properties。两张工单测试也在临时目录中写 tickets.properties。

mvn test 不会自动运行每个 Demo 的 main，也不包括助手的临时检查。坏存档的第 9 个 JUnit 测试曾被布置，但主线调整后暂停，当前没有这个测试方法。

## 3. 运行普通 Demo

修改源码后先编译，再运行；以下 classpath 分隔符适用于 Windows PowerShell：

```powershell
mvn test-compile
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' TicketServiceDemo
```

业务类输出到 target/classes，测试、Demo 与练习输出到 target/test-classes。普通 Demo 不调用 JUnit API，所以其 main 可使用上面的 classpath；不要照此直接调用没有 main 的 JUnit 测试类。

IDEA 也可直接运行对应 main。文件 Demo 的 Working directory 应为项目根目录，data 文件夹需存在；不要把工作目录设为 data，否则相对路径会变成 data/data。

TicketServiceDemo 已有运行证据覆盖首次派单、重复派单失败后原处理人保留、第二张工单不受影响、筛选结果列表独立但工单引用共享。findAll 的演示输出包括：

```text
全部工单数：2
结果列表数：0
服务中的工单数：2
```

## 4. 正常文件存取与恢复服务

TicketFileDemo 会创建两张固定示例工单并覆盖 data/tickets.properties；需要保留已有数据时先备份，或在隔离练习目录运行并建立 data。TicketLoadDemo 使用相同路径，只读取文件。

```powershell
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' TicketFileDemo
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' TicketLoadDemo
```

正常读取当前预期：

```text
读取文件：<项目根目录>/data/tickets.properties
服务中的工单数：2
IN_PROGRESS
1
测试通过：两张工单的所有字段都正确
读回数量：2
1001 | 投影仪无信号 | IN_PROGRESS | 20
1002 | 打印机卡纸 | OPEN | null
```

新增的三项输出来自恢复后的 TicketService：全部数量 2、编号 1001 的状态 IN_PROGRESS、OPEN 数量 1。助手另外检查过 OPEN 对象的编号是 1002；当前 Demo 没有单独打印这条筛选结果的编号。

原来的字段断言仍检查返回列表中的两张工单。用户曾故意把预期 1001L 改成 999L，确认 AssertionError，再恢复正确预期。当前服务查询结果是打印值，尚未全部变成自动断言；不能把输出正确说成已建立完整服务回归测试。

TicketLoadDemo 先取得完整列表，再创建新服务并逐张 add。读取抛异常就不会执行恢复步骤。IOException 和 IllegalArgumentException 当前会打印后结束，不保证非零退出码，不能仅凭进程正常退出认定验收通过。

## 5. 坏文件、空列表和重复编号

### 缺少第二张标题

```powershell
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' TicketLoadFailureDemo
```

Demo 读取 data/tickets-invalid.properties。该副本保留 count=2，删除 ticket.1.title 整行；清空值测试的是空标题，含义不同。

只有捕获 IllegalArgumentException 且消息等于“存档缺少必要字段”，才打印“测试通过：缺少标题的存档被正确拒绝”。正常返回、其他内容错误或 IOException 都用 AssertionError 判定失败。AssertionError 不会被现有两个 catch 捕获。

用户已经验证坏文件通过、改读正常文件会失败，并恢复路径。助手在目录整理期间重跑通过，还在隔离目录确认正常文件、缺文件和 count=abc 不会误判为这项测试通过。count=abc 在这里只验证“异常原因不匹配”，不等于完整的数量边界测试。

### 空列表

```powershell
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' TicketEmptyDemo
```

当前已完成：保存空列表到 data/tickets-empty.properties，读回后检查非 null 且 isEmpty()，成功打印“测试通过：空列表保存和读取正常”。IOException 会转换为 AssertionError。运行会覆盖该空列表存档。

有效空列表文件包含 count=0；零字节文件缺少 count，不是同一种输入。这个场景也已在 JUnit 临时目录中验证。

### 重复编号

loadAll 在循环外创建 Set<Long>，读取编号后 contains 检查，随后 add 记录。最初只有 contains，导致集合一直为空；补 add 后助手临时检查以下三项通过：

| 存档编号 | 结果 |
| --- | --- |
| 1001、1002 | 恢复两张工单 |
| count=0 | 返回空列表 |
| 1001、1001 | 抛 IllegalArgumentException，消息包含重复编号 1001 |

这三项临时检查不计入正式 8 项 JUnit，用户原存档未用于破坏性实验。

## 6. 第一、二周补验收与剩余任务

| 项目 | 当前证据与限制 |
| --- | --- |
| 数组最大值 | ArrayPractice.main 的普通、全负数、单元素、空数组、null 五项通过；失败提示已引用各自实际值 |
| 独立标题校验 | TitleValidationPractice 已实现；助手临时验证 8 个边界输入通过，学习者没有在类中编写完整自测 |
| static 共享字段 | 学习者正确解释第二个对象会覆盖类共享 id/title，第一周这轮补验收完成 |
| 数字出现次数 | countOccurrences 经修正使用数组元素作键、getOrDefault 加 put、LinkedHashMap 保序；助手 7 项临时检查通过，未加入 main 或 JUnit |
| 列表恢复到服务 | 最新 TicketLoadDemo 经助手运行通过，恢复数量、状态和 OPEN 编号符合预期 |
| 自动接续编号 | create(String title) 仅布置，源码未实现、未验收 |
| 异常 count 全部边界 | 代码已有缺失、解析失败和负数分支，完整专项验收未完成 |
| 首次无文件初始化 | 未实现；目前只报告读取失败 |
| 精确错误上下文 | 重复编号已有编号消息，其他错误尚未统一指出记录和字段 |
| 完整重启流程 | 未完成创建、派单、保存、退出、重启、筛选、新编号 4 的整体验收 |
| 写入中途失败保护 | 未实现原子替换或备份 |

第一周补验收已完成，第二周仍未完整完成。Maven 原定第三周，本次提前学习了 Maven 和 JUnit；保留工具与已有测试，继续补第二周。下一课先实现 create(String title)，并验证空服务从 1 开始、恢复 1001/1002 后新建为 1003、再次新建为 1004，以及非法标题不改变记录数。

## 7. 历史迁移验收

以下是 2026-10-16 引入 Maven 之前的记录，保留当时事实，不代表当前编译环境或文件状态：

- 源码目录整理时，4 个业务类和 8 个 Demo/练习类可分别编译，7 个当时已完成 Demo 在 JDK 8 与 JDK 21 下输出一致；TicketEmptyDemo 当时仅有可编译框架。11 个其他 Java 文件迁移前后 SHA256 一致，原 properties 内容未改变。
- data 整理时，5 个 properties 全部迁入 data，4 个文件 Demo 修改相对路径。保存验证使用隔离副本，原存档迁移前后 SHA256 一致，根目录无遗留 properties。记录在 .qa/data-layout-20261016/verification.json。
- IDEA 模块修复时，先前根据手工替换变量判断配置正确的结论不足。之后实际调用已安装 IDEA 的 JPS 模块加载器，验证只有一个 ops-ticket 模块、项目根与业务/测试源码根正确；用户关闭项目后再次解析通过。记录在 .qa/idea-module-repair-20261016/model-after-close.txt。用户随后截图显示目录已恢复。
- 之后完成 TicketEmptyDemo，并引入 pom.xml、JUnit 和新的练习类。当前运行方法、测试数量与完成状态以本页前述章节为准。

更早的对象恢复 21 项助手临时检查、单张文件提取阶段的数字与缺文件检查仍是历史证据，不计入当前 8 项 JUnit，也不代替新的多记录边界验收。

## 8. 常见问题

### main Demo 与 JUnit 有什么区别

main 由程序入口执行，需要自己组织检查和错误报告；JUnit 通过 @Test 发现并执行测试，提供 assertEquals、assertThrows 等断言和结果汇总。源码位于 test/java 不代表 main 会被 Maven 自动执行。

### catch 下面为什么一片报错

检查外层是否缺少 try，以及 for、try、方法和类的右括号是否分别闭合。catch 不能直接跟在 for 后面。

### 找不到文件

查看读取端打印的绝对路径，核对工作目录、data 子目录和文件名 tickets 的复数 s。保存和读取都从项目根目录运行，旧 ticket-demo.properties 不是当前默认文件。

### 中文乱码

源文件、存档、IDE 显示和终端显示分别排查。文件读写已指定 UTF-8，IDEA Properties 文件也应按 UTF-8 查看，避免将乱码另存覆盖原数据。

### null、空字符串和字符串 null

getProperty 找不到键返回 null；assigneeId= 返回空字符串，转换成无处理人的 null；文字 "null" 是字符串，在当前编号解析中会失败。

### 报 AssertionError 是不是业务代码坏了

先确认预期值和文件正确。故意将 1001L 改成 999L 应当失败；修复后保存并重新编译。不能捕获后忽略 AssertionError 来制造通过结果。

### 抛异常后还能拿到局部结果吗

当前正常执行路径中断，转到匹配的 catch。loadAll 在循环全部成功后才 return；第二张工单解析失败时，调用方拿不到局部列表中的第一张。现有成功输出都位于 try 中，不会在读取异常后继续执行。
