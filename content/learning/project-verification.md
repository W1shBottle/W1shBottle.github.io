{
  "title": "工单项目运行与验收",
  "description": "实际运行证据、后端验收与模型效果评估标准。",
  "date": "2026-10-21T00:00:00+08:00",
  "lastmod": "2026-10-30T00:00:00+08:00",
  "weight": 190,
  "group": "project-docs",
  "draft": false
}

[返回项目首页](/learning/project-docs/) · [需求](/learning/project-requirements/) · [设计](/learning/project-design/)

核对日期：2026-10-30。本页区分历史测试、学习者反馈、助手请求验证与待验收内容；第10节记录10月28日环境升级，第11—12节为JDBC，第13节为Web入门。

## 1. 环境与构建

编译目标为 Java 21。现已加入Spring Boot 4.1.2父POM与Web MVC Starter，JUnit版本通过属性保留为5.14.4。pom.xml 使用 JUnit Jupiter 5.14.4、maven-compiler-plugin 3.13.0、maven-surefire-plugin 3.5.5、maven-jar-plugin 3.4.1。所有源码已迁至 cn.wishbottle.opsticket 包，业务源码根为 src/main/java，测试、Demo 与练习源码根为 src/test/java。

命令行使用前配置 JDK 21 和 Maven，在项目根目录核对：

```powershell
java -version
javac -version
mvn -v
mvn clean package
java -jar target/ops-ticket-0.1.0-SNAPSHOT.jar
```

若终端未配置 mvn，可在 IDEA Maven 面板执行 clean、package，或调用 IDEA 自带 Maven 的完整可执行路径；不要把“IDEA 有 Maven”理解成系统终端必然能执行 mvn。Maven Runner 的 JDK 也需核对，pom 的 release=21 不会替换运行 Maven 的 JDK。

本次学习中曾发现终端 Java 8 与 IDEA Java 21 不一致；通过当前 PowerShell 会话的 JAVA_HOME、PATH 临时切换，学习者确认 java、javac、Maven 均使用 21.0.8。此设置未永久写入系统环境，关闭终端后需重新核对。

package 会执行编译和测试，生成 target/ops-ticket-0.1.0-SNAPSHOT.jar；已配置 ConsoleApp 入口。学习者报告 java -jar 能显示菜单和已有工单，助手已检查 JAR Manifest 中的入口和类文件。项目没有 Maven Wrapper。clean 清理 target，不清理 data。

控制台存档为 data/tickets-app.properties，相对于运行时工作目录；需在项目根目录启动并保证 data 存在。首次无文件可空仓库启动，保存时创建文件，但不会自动创建父目录。

## 2. 当前正式 JUnit：17 项

```powershell
mvn test
```

2026-10-21，助手在项目目录使用 JDK 21.0.8 和 Maven 执行离线 package：测试源码重新编译，共 22 个测试/Demo/练习源文件；**Tests run: 17, Failures: 0, Errors: 0, Skipped: 0，BUILD SUCCESS**。生成项目 target 下的报告和 JAR，未改写项目 data 存档。

| 测试类 | 场景 | 数量 |
| --- | --- | --- |
| TicketTest | 正常修改、拒绝 null、50/51 字符边界、trim 后计长、拒绝空白；失败保留原标题 | 6 |
| TicketFileStoreTest | 空列表往返、两张工单四字段往返 | 2 |
| InMemoryTicketRepositoryTest | 新增查询、不存在查询、重复编号拒绝、更新替换、未知编号拒绝、add(null) 拒绝、返回列表结构隔离 | 7 |
| TicketServiceTest | 创建使用注入仓库并接续编号、修改标题 | 2 |

update(null) 已作为理解了的重复练习跳过，没有该项正式测试，不计入数量。Service 改名测试在共享对象引用下不能单独证明调用了 update；文件重新加载演示补充检查了结果确实持久化。17 项通过不代表所有文件错误、所有菜单分支或写入失败均有自动测试。

JUnit 通过 @Test 调用测试方法，不需要 main。每个仓库测试自己创建仓库，不依赖顺序；orElseThrow 在意外查不到时直接失败，isEmpty 检查预期的不存在。

文件测试使用 @TempDir。tempDir.resolve("tickets-empty.properties") 指向临时目录中的新路径，由 save 创建文件；它与 data 中已有文件只是同名，**不是同一个文件，不会读取或覆盖原存档**。JUnit 默认清理临时资源。

mvn test 不执行 main Demo，不把临时检查和口头题累计为 JUnit。此前未完成的坏存档 JUnit 仍未计入。

## 3. 运行普通 Demo 与路径

修改源码后先编译。下面 classpath 分隔符适用于 Windows PowerShell，须在项目根目录运行：

```powershell
mvn test-compile
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' cn.wishbottle.opsticket.TicketServiceDemo
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' cn.wishbottle.opsticket.TicketLoadDemo
```

包迁移后必须使用完整类名。IDEA 中可打开移动后的类，从 main 旁重新运行，核对 Working directory；不要设为 data，否则路径可能变为 data/data。用 path.toAbsolutePath() 比较保存和读取实际位置，同样的相对路径不保证在不同工作目录中指向同一个文件。

普通 Demo 可使用上面的类路径；JUnit 测试类没有 main，交给 Maven/IDEA 测试引擎运行。已完成练习残留的 TODO 和占位注释在本次规范检查中清理，验收仍以实际代码和行为为准。

| Demo / 入口 | 文件影响或检查范围 |
| --- | --- |
| ConsoleApp | 正式菜单，写 data/tickets-app.properties；成功变更后自动保存 |
| TicketAutoSaveDemo | 每次向 data/tickets-auto-demo.properties 新增一张工单，改名并派单 |
| TicketAutoLoadDemo | 只恢复并打印自动保存演示的存档 |
| TicketRepositorySwitchDemo | 使用新建的系统临时目录，运行两种仓库共用流程并重新加载；不写项目 data |
| ArrayPractice | 最大值、次数统计、双循环和 Map 两数之和；仅内存练习 |
| TicketServiceDemo | 只操作内存；派单、列表引用和自动编号边界 |
| TicketFileDemo | 生成或覆盖 data/tickets.properties 的两张示例工单 |
| TicketLoadDemo | 只读取正常两张工单；恢复服务、检查字段和查询输出 |
| TicketEmptyDemo | 生成或覆盖 data/tickets-empty.properties，再读取检查空列表 |
| TicketStartupDemo | 只读取；正常、缺文件与坏文件三个启动分支 |
| TicketLoadFailureDemo | 只读取缺少第二张标题的副本，核对完整异常消息 |
| TicketInvalidNumberDemo | 只读取 ticket.1.id=abc 的副本 |
| TicketInvalidStatusDemo | 只读取 ticket.1.status=DONE 的副本 |
| TicketRestartSaveDemo | 生成或覆盖 data/tickets-restart.properties |
| TicketRestartLoadDemo | 只读重启存档，编号 4 仅在内存，不保存 |

保存 Demo 会覆盖指定练习文件，需保留现有内容时先复制到隔离练习目录并建立 data；不要为文档验收重复覆盖原始数据。

## 4. 第二周已完成的功能验收

### 自动编号与失败后数据不变

TicketServiceDemo 已补 main 断言，学习者报告通过，教学中也已核对：

- 现有 1001、1002 时 create 得到 1003，返回对象与服务中对象相同，数量变为 3。
- 空服务得到编号 1、数量 1；原服务继续创建得到 1004、数量 4。
- 空白标题抛 IllegalArgumentException，服务数量保持不变。

编号取最大已有值加 1，不取集合大小加 1。标题先由构造器校验，通过才 add。原有演示还保留派单后状态、重复派单不改变原处理人、清空结果列表不清空服务、修改列表元素会反映到原对象等内容。

### 启动分支

TicketStartupDemo 当前路径已恢复为 data/tickets.properties。学习者分别测试并报告：

| 输入 | 预期与已报告结果 |
| --- | --- |
| 正常两张存档 | 恢复后打印启动完成，数量 2 |
| 确认不存在的文件 | 提示缺文件，继续启动，数量 0 |
| 已有坏存档 | 提示错误并 return，不打印启动完成 |

NoSuchFileException 是 IOException 的子类，catch 放前面。后两个失败分支是 I/O 失败与内容错误；缺文件不能和所有读取错误一起当成正常空数据。该 Demo 不调用 save，也不保证错误时进程返回非零退出码；检查输出和控制流，不能只看“程序结束”。

### 精确定位坏字段与业务错误

缺字段、非法数字与非法状态已有专用 Demo，对异常消息进行精确比较；正常返回或 IOException 会转为 AssertionError，不能误判通过。其他场景在坏存档副本上通过 Startup Demo 逐个验证，测后恢复正常读取路径。

| 测试修改 | 预期错误消息或关键部分 | 证据 |
| --- | --- | --- |
| 删除 ticket.1.title 整行 | 存档缺少必要字段：ticket.1.title | 专用 Demo 与用户通过反馈 |
| ticket.1.id=abc | 存档字段格式错误：ticket.1.id，应为整数，实际值：abc | 专用 Demo 与用户通过反馈 |
| ticket.1.status=DONE | 存档状态不合法：ticket.1.status，实际值：DONE | 专用 Demo 与用户通过反馈 |
| count=abc | 存档字段格式错误：count，应为整数，实际值：abc | 用户报告启动验收通过 |
| count=-1 | 存档字段不合法：count，不能为负数，实际值：-1 | 用户报告启动验收通过 |
| 删除 count 键 | 存档缺少必要字段：count | 用户报告启动验收通过 |
| ticket.1.id=0 | 存档记录不合法：ticket.1，原因：工单编号必须大于0 | 用户报告启动验收通过 |
| ticket.1.title= | 存档记录不合法：ticket.1，原因：工单标题不能为空 | 用户报告启动验收通过 |
| OPEN 工单的 assigneeId=20 | 存档记录不合法：ticket.1，原因：待派单工单不能有处理人 | 用户报告启动验收通过 |

每个场景应从正常副本开始只改一项，避免前面的错误遮住本次目标。缺键与空值不同；assigneeId= 是合法未派单状态，字符串 "null" 则不能当数字解析。parseLongProperty 同时用于工单编号和非空处理人编号；本轮专用非法数字 Demo 测的是工单编号，不扩张为全部数字边界已覆盖。

转换失败与恢复失败的包装异常保留 cause，便于追查原始原因。第二条恢复失败时不会正常返回第一条的局部结果，也不会回到出错位置继续。

### 空列表

TicketEmptyDemo 已验证保存 count=0 再读回非 null、isEmpty 的列表；文件不存在和零字节空文件不是这个场景。正式 JUnit 中也有临时目录空列表往返测试。

## 5. 完整重启与坏存档保护

在项目根目录分两次执行，保存端结束后再运行读取端：

```powershell
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' cn.wishbottle.opsticket.TicketRestartSaveDemo
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' cn.wishbottle.opsticket.TicketRestartLoadDemo
```

两端已有用户通过反馈；教学中对代码和读取运行作过核对。验收内容：

| 检查点 | 结果 |
| --- | --- |
| 保存端编号和数量 | 1、2、3，共三张 |
| 第一张特殊字符 | Java 字面量 `"A=B\\C"` 对应的标题往返后仍为 `A=B\C` |
| 第二张派单 | 标题空调不制冷、IN_PROGRESS、处理人 20 |
| 第三张 | 标题打印机卡纸、OPEN、处理人 null |
| 重启后筛选 | 创建第四张之前，OPEN 仍为编号 1、3 |
| 恢复后继续创建 | 新编号 4、总数 4，返回对象与服务中对象相同 |
| 原存档 | 读取端不保存，仍是原来三张 |

预期输出分别为“阶段一通过：已保存3张工单”和“阶段二通过：数据恢复正确，新工单编号为4”。重复执行读取端仍从三张开始，编号 4 不会自动写回文件。

最后，学习者复制重启存档为 tickets-restart-invalid.properties，分别制造第三张与第二张编号重复、第三张状态 DONE，使用 Startup Demo 验证停止启动。**用户报告两个场景的运行前后 Get-FileHash 比较均为 True，并已恢复正常路径。** 比较基线是在造好坏数据之后记录，每个场景各取一次。

这项证据说明读取失败没有修改这两个坏存档副本，不证明写入中途断电或异常时文件也安全。当前 save 直接覆盖文件，尚无原子替换和备份机制。

## 6. 第三周验收与下一步

第二周集合、文件、启动边界和重启验收结论保持有效。第三周已接入仓库接口、控制台、自动保存、关键词查询、可执行 JAR；代码提交为 682b3c7（完成仓库接口接入、文件自动保存与控制台交互）。文档随后由学习者提交为 ecc0f14；当时尚未提交的规范整理后来已进入 8a3bfbe，此次路线调整仅更新文档与课程，业务实现未提前推进。

| 验收事项 | 证据与范围 |
| --- | --- |
| Maven 构建 | 2026-10-21 助手执行离线 package，17 项正式测试全部通过 |
| 同一业务流程切换仓库 | 学习者反馈正常；助手单独编译运行 TicketRepositorySwitchDemo，内存/文件实现均创建编号 1、改名、派单为 IN_PROGRESS/20 |
| 新文件仓库恢复 | 同一 Demo 创建新仓库后得到相同最终字段、数量 1；这是同一进程内重新加载，不是独立进程重启 |
| 控制台创建、改名、派单和重启 | 学习者报告保存及重启后数据正常，助手核对源码路径和调用顺序 |
| 非法数字、重复派单、空白关键词 | 学习者报告提示后能返回菜单；助手核对异常捕获顺序和校验 |
| 坏存档启动 | 学习者报告提示并退出、正常路径已改回；当前坏存档样本 tickets-app-invalid.properties 的 count=abc 已提交 |
| 可执行 JAR | 学习者报告菜单及已有数据正常；助手检查 Manifest 和入口类 |
| Lambda 与两数之和 | 口头解释每次遍历对象正确；双循环和 Map 版源码已核对，学习者报告样例输出 [0, 1]；不计入 JUnit |

手动复现仓库切换：

```powershell
mvn test-compile
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' cn.wishbottle.opsticket.TicketRepositorySwitchDemo
```

预期三次打印的工单字段一致：编号 1、标题“投影仪无法开机”、IN_PROGRESS、处理人 20；恢复数量 1。临时目录由 Files.createTempDirectory 创建，该 Demo 没有自动清理逻辑，与 JUnit 的 @TempDir 生命周期不同。

尚未覆盖：文件写入失败的自动故障测试、原子替换、多进程并发安全，以及全部业务/菜单路径的自动测试。当前保存失败提示后退出，不回滚内存；通过的恢复演示不能证明抗写入中断。

以上是 2026-10-21 的第三周快照。规范整理后已提交 8a3bfbe；截至 2026-10-26 已进入 SQL 三表与条件查询，当前任务以第 9 节为准。

### 2026-10-21 日结规范检查与复验

本次按学习者要求修正代码与结构，未补写新的业务流程或永久测试：

| 问题 | 处理 |
| --- | --- |
| 已完成的 TODO、占位注释、缩进和导入不统一 | 清理占位，保留有用说明；显式导入实际用到的类，统一空行与换行 |
| 编号字段可被类内误改、字段分散 | id 改为 final，实例字段集中在类顶部 |
| 改名不存在编号的提示不一致 | 补全“工单不存在：”后的编号；不改变异常类型 |
| 存档说明被早期重构误替成包名 | 后续保存使用 Ops ticket archive 注释，不改变存档键和读取协议 |
| 两份运行存档容易误入 Git | 只忽略控制台与自动保存演示的运行档，保留验收样本及所有现有文件 |
| 三份旧手工模块文件残留 | 确认活动 Maven 模块无引用后移入本地忽略目录备份；活动 IDEA 配置保持原样 |

当前 Maven 目录和包结构本来正确：8 个正式源码、22 个测试/Demo/练习源码分属 main/test，不为整理强行拆多模块。

修正后助手在独立临时副本使用 JDK 21 与 Maven 离线 package，17 项 JUnit 全部通过，打包成功。另在隔离数据目录运行临时检查：

- 两种仓库共用 Demo 和新仓库恢复通过，三次工单字段一致，恢复数量 1。
- ArrayPractice 两个两数之和样例输出 [0, 1]，原最大值五项 main 检查通过。
- 实际运行新 JAR，创建、改名、派单、关键词查询成功；非法数字、重复派单、空关键词和不存在编号 999 均提示后继续菜单。
- 结束一个 JVM 后启动另一个，恢复最终标题、状态和处理人；只读查看未改变临时存档。
- 将临时存档 count 改为 abc，启动提示并退出，未进入菜单、未改写坏存档。
- 项目原有全部 properties 与 Git 暂存区的检查前后 SHA256 一致，原数据和暂存状态保留。

这些是助手日结临时复验，不是新增的正式 JUnit；正式数量仍为 17。检查不覆盖写入中断、并发保护或全部整数边界。

## 7. 历史验收记录

以下记录保留当时事实，不能用于替代当前 Maven/包结构运行说明：

- 2026-10-16 引入 Maven 前，4 个业务类与 8 个 Demo/练习类曾分别编译，7 个当时完成的 Demo 在 JDK 8 与 JDK 21 下输出一致，TicketEmptyDemo 当时仅有框架；11 个其他源码迁移前后 SHA256 一致。现在完整项目需要 JDK 21，测试依赖 JUnit。
- 当日 5 个 properties 迁入 data，4 个文件 Demo 改相对路径；隔离副本验证后原存档 SHA256 不变。后续又新增了本页所列的坏存档与重启验收文件。
- IDEA 模块修复曾通过实际 JPS 模块加载器确认源码根与项目根，用户关闭后再次解析并重新打开；之后又以 Maven 重新导入并迁入命名包，旧配置检查不是当前模块结构的唯一证据。
- 第一周补漏：数组最大值 main 的普通、全负、单元素、空数组、null 五项；标题练习的助手临时 8 项；static 共享字段口头解释。Map 次数统计的助手临时 7 项、早期 Set 查重临时 3 项分别通过，均不计入正式 JUnit。
- 10 月 16 日正式测试数量为 8；10 月 17 日新增仓库两项后为 10，当日助手在隔离副本使用 JDK 21 离线 test 全部通过。10 月 21 日增至 17；历史文章保留当时数量，不回写成已提前完成。

## 8. 常见问题

**重构预览是不是报错？** 普通 Refactoring Preview 列出待更新引用；Conflicts Detected 需要检查原因，不能一概忽略。移动测试类时保留 test 源码根，README 文本引用不必随类移动批量改成完整名称。

**方法一定要写 @Override 吗？** 注解不强制，但建议接口实现方法都写，用于编译期核对。缺少接口要求的方法与缺少注解是不同问题；当前普通实现类不能少实现 update。

**抛 AssertionError 是业务失败吗？** 它通常表示测试预期不成立，先核对数据和断言；故意改错预期让测试失败，是确认检查有效，不能捕获忽略来伪造通过。

**中文乱码怎么排查？** 源码、存档、IDE 与终端显示分别检查，文件读写已指定 UTF-8；不要把显示乱码另存覆盖正常文件。终端的 Git/包版本/Java 提示只是环境信息，不能替代实际的版本命令。

## 9. 2026-10-26 路线调整与分阶段验收

### 本次复核（事实，不等于独立掌握）

- 阅读 8 个业务类、22 个测试/Demo/练习类、pom、5 个 SQL 文件及现有文档；没有 JDBC/Boot/MyBatis/模型运行依赖。
- 使用已配置的 Java 21 和 IDEA 自带 Maven 执行 `mvn -o package`：重新编译 8 个生产源码和 22 个测试源码，**17 tests、0 failures、0 errors、0 skipped，BUILD SUCCESS**。未新增测试，不把重复构建累计为新能力。
- 本次没有连接/写入 MySQL，没有真实模型请求。表数据和 SQL 执行进度以学习者的聊天反馈为证；SQL 文件存在只能证明已保存语句。
- 本次只调整文档与课程；源码、pom、SQL、data、Git index 以核验哈希检查，核验记录保留在本地。
- 当前 shell 默认仍可能指向 Java 8；本次构建仅在该进程显式选择 JDK 21，不修改系统环境或 IDEA 配置。

### 同日SQL学习补充（日结证据）

- 学习者提交组合查询SQL及实际结果：标题含打印机、状态OPEN、assignee_id IS NULL，返回编号3、打印机卡纸、NULL、OPEN。这一条实操通过，不据此宣称所有SQL条件与排错已掌握。
- `sql/03_queries.sql` 已保存设备、报修人、处理人和完整关联查询；INNER/LEFT/RIGHT JOIN、表/列别名、结果集已讲解，尚未收到完整查询执行结果和独立OPEN筛选变体反馈。
- 下次先核对完整JOIN和三个ON，再自己加WHERE状态条件。Java仍使用文件仓库，没有数据库接入或Web/AI。
- 本次日结只核对文件与聊天证据，没有连接/写入MySQL，没有新增/重复运行Java测试；17项JUnit引用上面同日方案核对的既有结果。笔记见[MySQL三表关系、条件查询与JOIN入门](https://wishbottle.cn/posts/ops-ticket-20261026/)。

### A 后端的必要验收（全部仍待完成）

| 场景 | 预期与证据 |
| --- | --- |
| 正常闭环 | 真实 MySQL 创建→派单→解决→验收，重启查询仍一致；能讲请求链和四表职责 |
| 参数与身份 | 空标题、无效设备、停用工程师、错误角色、别人的工单、未登录分别拒绝；核对状态/日志未变化 |
| 状态与并发 | 错序操作、重复验收、两个相同期望版本的派单仅一方成功；另一方明确 409，无重复日志 |
| 创建重试 | 同 requestKey/同输入返回同 ticketId；不同输入 409；并发时不留下两张工单 |
| 事务 | 在隔离测试库故意令操作日志插入失败，证明工单状态也回滚；仅 Mock 通过不能证明 MySQL 事务 |
| 查询与部署 | 未分配处理人的 LEFT JOIN 不丢工单；分页排序稳定；可按 README 在另一个环境启动、看日志、重启恢复 |
| 独立能力 | 不复制答案改一个查询条件/状态规则，解释权限位置和事务边界；定位一个故意制造的映射或配置错误 |

### B/C 模型功能的验收（尚无配置或实测结果）

准备固定的 12—20 个虚构案例，分开发集和未用于改提示的留出集；包括清楚描述、模糊输入、缺型号/现象、无关内容、试图改变系统指令的文本。固定工单数据、模型与参数、提示版本；同一版本保留输入、预期规则、实际输出及判定理由。人工基线是自行整理摘要和分类，不预设 AI 一定更快或更好。

| 用例组 | 验收要求 |
| --- | --- |
| 内容质量 | 摘要不增添事实；分类在白名单中，信息不足可 UNKNOWN；待补充信息有用且不重复；人工按固定规则判定 |
| 权限/输入 | 无权工单不发模型请求；长输入有上限；指令注入文本不扩权、不更改业务状态 |
| 模型与网络故障 | 空响应、错误 JSON、缺字段、非法枚举、拒答、超时、429/5xx、失效密钥明确处理；业务接口仍可用 |
| 真实调用与替身 | 可用模拟服务器稳定造故障，但标记 Mock；至少用选定供应商跑固定真实案例并保存去敏结果，不能混称真实验证 |
| 指标 | 记录有效样本数、结构合法率、内容忠实/可用性、成功/失败延迟分布、调用次数、token与成本；小样本指标标出局限 |
| 改进 | 选择一个真实失败归因，修改提示/校验或业务上下文，重跑固定集和留出集；比较前后而非只挑成功截图 |

RAG 追加资料导入/更新、已知答案召回、引用真实性、无匹配与越权资料案例。Agent 追加工具参数错误、无结果、无权限、工具失败、重复调用、步数耗尽和上下文过期；写工具追加未确认/确认过期/版本改变/重复请求。没有引入这些能力时写“未实施”，不提前勾选。

阶段记录使用“未接触 / 已讲解 / 跟写或助手协助 / 独立修改 / 验收通过”。测试通过是工程证据，不自动证明学习者独立完成；已经明确跳过的重复断言不再作为欠作业。

## 10. 2026-10-28 MySQL 升级验收

助手完成 MySQL 8.0.44 → 8.4.13 和 Connector/J 9.7.0 → 26.10.0 的环境维护。先备份全部旧库，为 MyISAM 补充锁表备份；独立端口恢复后，再冻结旧库写入、最终备份并切换服务。原账号认证和旧数据目录保留；旧服务停止，新服务自动启动，重启验证通过。

五个业务库共70张表、958行，逐表比较完整行内容哈希、结构、引擎、排序规则、自增值及业务存储对象，切换前后均一致。结构比较只标准化外键引用列名的大小写显示。旧项目所需的认证及非唯一索引外键兼容选项予以保留，新项目仍应采用默认认证和规范外键。

助手用新驱动在临时和正式端口验证参数查询、中文、版本条件更新、回滚及FK/CHECK约束；测试修改均回滚，临时数据库账号删除。Java21运行原有17项JUnit全部通过，不计为学习者新增JDBC测试。其他旧项目未全部完成端到端验收。

备份和账号材料只保存在受限本地目录，不随博客发布。旧版本回退点不包含升级后的新增数据，不能不经评估直接切回，也不能用8.0打开8.4的数据目录。正式工单业务仍使用文件仓库，独立查询Demo的学习证据见下一节。

## 11. 2026-10-28 SQL 与 JDBC 学习日结

SQL文件：03_queries.sql包含JOIN、统计、HAVING、分页及版本实验；06_transactions.sql记录提交、回滚、CHECK失败与条件派单。两文件有重复事务片段，属于学习记录，不是可盲目整文件重跑的迁移脚本。当日记录工单3的version为1，旧version=0示例需先核对前置条件。

学习者反馈：JOIN筛选剩打印机；COUNT为2/1；HAVING=0剩投影仪；分页偏移后空结果但总数仍1；COMMIT/ROLLBACK结果符合预期；双连接A影响1行、B影响0行，保留A标题和version=1。独立修改与完整解释继续在后续任务验证。

JdbcTicketQueryDemo先后跟写连接、按编号/状态查询、修正statu列名、getLong+wasNull读取可空处理人、提取printTicketsByStatus。最新源码确认在同一Connection内依次查询OPEN/IN_PROGRESS，statement/resultSet由方法关闭，连接由main关闭；学习者报告运行成功。该Demo不是JUnit；本次日结只读核对，不重复查询或修改真实数据，不新增测试通过数量。

第10节中的17项JUnit及临时JDBC事务验证属于此前助手环境维护，不等于学习者已经完成Java更新事务。下一步由学习者亲手使用executeUpdate和显式rollback验证标题/版本恢复，再进入后续数据库接入。


## 12. 2026-10-29 JDBC 更新事务学习日结

本节运行证据来自学习者课堂反馈，助手核对最新源码；日结未重新运行Java程序或读写数据库。没有新增JUnit，17项原有测试保留10月28日的验收日期。

| 场景 | 学习者反馈与源码核对 |
| --- | --- |
| 更新后回滚、三阶段查询 | 影响1行；同一连接查到暂时修改；回滚后标题与版本恢复 |
| 旧版本重复更新 | 第一次1、第二次0；原演示已随后重构，不声称最新main仍运行两次更新 |
| 自动读取版本 | findTicketVersion已接入，反馈1/0与恢复正常 |
| 成功提交 | Java显示已提交，另一个MySQL终端查到新标题与增加后的版本 |
| 模拟后续失败 | 更新后、提交前主动抛异常，反馈catch回滚恢复；未实际写日志表 |
| 提取更新方法 | 经检查修正只定义未调用的问题；最新main已调用updateTitle，反馈回滚正常，simulateFailure已改回false |

当前false分支会提交练习标题并增加版本，不能为了日结重复运行；精确版本以实际查询为准，不再沿用旧快照的1。本次只整理笔记/文档，源码、SQL、data、pom和Git暂存区均保留。

HTTP请求/响应、GET、URL、JSON和200/404已经初步讲解；Network主文档的Request URL/Request Method/Status Code尚无反馈。下一次从这项观察继续，再接Spring Boot/MyBatis；不把计划中的接口当作已部署功能。


## 13. 2026-10-30 HTTP、Maven 与 Web 入门验收

| 场景 | 学习者证据 | 助手核对/边界 |
| --- | --- | --- |
| 浏览器Network | 发现页GET/304截图；首页HTML响应截图 | 首页截图未展示状态码，不补造200证据 |
| Maven配置 | 反馈添加父POM/Web Starter后测试通过 | 源码已核对；既有JUnit17项未增加，日结不重跑 |
| Boot启动与首页 | 日志截图显示Java21.0.8、Boot4.1.2、Tomcat8080，反馈根路径404 | 启动类与扫描范围正确；尚无首页处理方法 |
| Hello普通文本 | 反馈浏览器显示Hello, Ops Ticket! | 课堂实际GET：200、text/plain;charset=UTF-8、正文一致 |
| Hello固定Map | 进入JSON学习 | 课堂实际GET：200、application/json、message/project两字段一致 |
| Hello查询参数 | 反馈带name和不带name正常 | 最新源码正确；最后一次请求8080连接被拒绝，不能记为助手复跑通过 |
| 工单路径编号 | 未反馈3/10/abc运行结果 | 日结确认TicketController已写；预计数字回显、abc默认400，未实际请求验收 |

日结只读代码，不启动应用、不重跑Java/数据库实验，不修改源码、SQL、data、pom或Git暂存区。临时HTTP请求不构成Web自动测试；普通JAR仍为ConsoleApp入口，Web打包未完成。没有工单存在性、正数编号、权限或HTTP→数据库业务验证。

下一项：启动OpsTicketApplication，GET /api/tickets/3、/api/tickets/10、/api/tickets/abc，记录响应体和状态码。解释路径类型转换与业务校验的区别，再连接真实查询及不存在的404行为。无需重建已有类。


## 14. 2026-10-31 Bean、查询与 POST 验收

覆盖10月31日至11月1日凌晨课堂；与第13节历史结果分开。本次日结只读源码/存档和请求文件，不重新运行Java、数据库或写请求，现有17项JUnit未增加。

| 场景 | 证据 |
| --- | --- |
| 早期路径回显3/10/abc | 用户反馈对应编号和400；之后方法已改真实查询 |
| 详情1/999 | 助手课堂GET分别200（标题b、处理人20）和404 |
| 列表/关键词 | 助手GET查全部、b匹配、xyz空列表均200；空值与两个空格400 |
| 尾斜杠 | 默认无尾斜杠200、带斜杠404实测；后续源码显式配置两条列表/创建路径，未把未重测变体记为新验收 |
| 重复映射 | 源码发现两个同GET路径；删除旧方法后课堂GET恢复正常 |
| POST正常创建 | 用户截图201、id2、标题打印机卡纸、OPEN、null；课堂读取文件确认记录已保存 |
| POST空白标题 | 请求文件已追加；用户反馈400与前后数量不变均符合预期 |
| 重启查询 | 已安排并写好GET编号2，尚无本轮单独结果反馈 |
| 注释整理 | 助手给当时43文件加注释，校验代码/SQL/配置未变；后续DTO/POST是之后的课堂实现 |

下一项：先确认重启后编号 2 仍可查询，再用断点追踪 setTitle → Controller → Service；比较缺标题的 {} 与语法错误 JSON 的失败位置，区分参数转换和业务校验。
