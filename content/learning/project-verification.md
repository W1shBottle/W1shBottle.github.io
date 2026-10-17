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

核对日期：2026-10-17。本页区分正式 JUnit、main Demo、用户自报和助手复核。第二周本轮验收已完成，当前进入第三周仓库接口与测试。

## 1. 环境与构建

编译目标为 Java 21。pom.xml 使用 JUnit Jupiter 5.14.4、maven-compiler-plugin 3.13.0、maven-surefire-plugin 3.5.5。所有源码已迁至 cn.wishbottle.opsticket 包，业务源码根为 src/main/java，测试、Demo 与练习源码根为 src/test/java。

命令行使用前配置 JDK 21 和 Maven，在项目根目录核对：

```powershell
java -version
javac -version
mvn -v
mvn clean package
```

若终端未配置 mvn，可在 IDEA Maven 面板执行 clean、package，或调用 IDEA 自带 Maven 的完整可执行路径；不要把“IDEA 有 Maven”理解成系统终端必然能执行 mvn。Maven Runner 的 JDK 也需核对，pom 的 release=21 不会替换运行 Maven 的 JDK。

本次学习中曾发现终端 Java 8 与 IDEA Java 21 不一致；通过当前 PowerShell 会话的 JAVA_HOME、PATH 临时切换，学习者确认 java、javac、Maven 均使用 21.0.8。此设置未永久写入系统环境，关闭终端后需重新核对。

用户报告 clean package 的 8 项旧测试通过、BUILD SUCCESS，包迁移后的构建及重启读取也已验证。package 会执行前面的编译和测试阶段，生成 target/ops-ticket-0.1.0-SNAPSHOT.jar；当前是普通 JAR，没有配置 java -jar 启动入口，也没有 Maven Wrapper。clean 清理 target 构建产物，不清理项目 data。

## 2. 当前正式 JUnit：10 项

```powershell
mvn test
```

2026-10-17 日结时，助手以当前 pom.xml 和 src 的隔离临时副本、JDK 21 与 Maven 离线运行 test：编译 6 个业务源码和 18 个测试/Demo/练习源码，**Tests run: 10, Failures: 0, Errors: 0, Skipped: 0，BUILD SUCCESS**。这次未改变原项目的 target、数据或 Git 暂存区。

| 测试类 | 场景 | 数量 |
| --- | --- | --- |
| TicketTest | 正常修改；拒绝 null；接受 50 字符；拒绝 51 字符；先 trim 再检查长度；拒绝空白；非法修改还检查原标题保留 | 6 |
| TicketFileStoreTest | 空列表往返；两张工单往返并核对编号、标题、状态、处理人 | 2 |
| InMemoryTicketRepositoryTest | 新增后按编号找到且数量正确；不存在的编号返回空 Optional | 2 |

前 8 项此前已有学习者自测和助手运行证据；仓库两个测试当前已在源码中完成，本次由助手复核通过，不能写成学习者已独立完成全部仓库边界验收。仓库更新、重复新增、null 和列表结构隔离等专项断言尚未编写。

JUnit 通过 @Test 调用测试方法，不需要 main。每个仓库测试自己 new 仓库，数据独立、不依赖运行顺序；orElseThrow 使意外查不到直接失败，isEmpty 检查不存在编号的预期结果。

文件测试使用 @TempDir。tempDir.resolve("tickets-empty.properties") 指向临时目录中的新路径，save 才创建文件；与 data 中已有文件只是同名，**不是同一个文件，不会读取或覆盖原存档**。JUnit 默认清理临时资源。

mvn test 不会自动执行 main Demo，不把临时检查或口头题计入 10 项；此前暂停的“坏存档第 9 个 JUnit”也没有突然完成，新增的两项来自仓库查询。

## 3. 运行普通 Demo 与路径

修改源码后先编译。下面 classpath 分隔符适用于 Windows PowerShell，须在项目根目录运行：

```powershell
mvn test-compile
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' cn.wishbottle.opsticket.TicketServiceDemo
java '-Dfile.encoding=UTF-8' -cp 'target/classes;target/test-classes' cn.wishbottle.opsticket.TicketLoadDemo
```

包迁移后必须使用完整类名。IDEA 中可打开移动后的类，从 main 旁重新运行，核对 Working directory；不要设为 data，否则路径可能变为 data/data。用 path.toAbsolutePath() 比较保存和读取实际位置，同样的相对路径不保证在不同工作目录中指向同一个文件。

普通 Demo 可使用上面的类路径；JUnit 测试类没有 main，交给 Maven/IDEA 测试引擎运行。源码中的待清理 TODO 注释不代表已实现的代码仍为空，验收以实际代码和行为为准。

| Demo | 文件影响或检查范围 |
| --- | --- |
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

## 6. 第二周结论与第三周下一步

第二周本轮的集合、文件、启动边界、重启流程和理解验收完成。学习者正确解释了 Map 同键替换为何要防重、最大编号与 size 的区别、maxId 每次从 0 开始仍会遍历，以及工作目录如何影响相对路径。第一周此前的数组、标题和 static 补验收继续保留有效。

第三周当前已经完成 JDK/Maven 环境核对、构建、包迁移；创建了仓库接口、内存实现以及两个查询测试。尚未完成：

1. 重复 add 拒绝且保留原对象与数量。
2. update 已有编号能替换，更新不存在编号拒绝且不新增。
3. add/update 的 null 检查和失败后状态不变。
4. findAll 返回列表的结构隔离、插入顺序，以及元素共享引用的理解与必要测试。
5. 将仓库注入 Service，保持 create、查询、筛选和恢复行为；再安排后续存储实现。

当前 Service 与 Repository 各自有 Map，没有自动联动。文件异常仍以 main Demo 为主，不能把 10 项 JUnit 说成完整业务回归覆盖。

## 7. 历史验收记录

以下记录保留当时事实，不能用于替代当前 Maven/包结构运行说明：

- 2026-10-16 引入 Maven 前，4 个业务类与 8 个 Demo/练习类曾分别编译，7 个当时完成的 Demo 在 JDK 8 与 JDK 21 下输出一致，TicketEmptyDemo 当时仅有框架；11 个其他源码迁移前后 SHA256 一致。现在完整项目需要 JDK 21，测试依赖 JUnit。
- 当日 5 个 properties 迁入 data，4 个文件 Demo 改相对路径；隔离副本验证后原存档 SHA256 不变。后续又新增了本页所列的坏存档与重启验收文件。
- IDEA 模块修复曾通过实际 JPS 模块加载器确认源码根与项目根，用户关闭后再次解析并重新打开；之后又以 Maven 重新导入并迁入命名包，旧配置检查不是当前模块结构的唯一证据。
- 第一周补漏：数组最大值 main 的普通、全负、单元素、空数组、null 五项；标题练习的助手临时 8 项；static 共享字段口头解释。Map 次数统计的助手临时 7 项、早期 Set 查重临时 3 项分别通过，均不计入正式 JUnit。
- 10 月 16 日正式测试数量为 8；10 月 17 日新增仓库两项后为 10。历史文章保留当时数量，不回写成已提前完成。

## 8. 常见问题

**重构预览是不是报错？** 普通 Refactoring Preview 列出待更新引用；Conflicts Detected 需要检查原因，不能一概忽略。移动测试类时保留 test 源码根，README 文本引用不必随类移动批量改成完整名称。

**方法一定要写 @Override 吗？** 注解不强制，但建议接口实现方法都写，用于编译期核对。缺少接口要求的方法与缺少注解是不同问题；当前普通实现类不能少实现 update。

**抛 AssertionError 是业务失败吗？** 它通常表示测试预期不成立，先核对数据和断言；故意改错预期让测试失败，是确认检查有效，不能捕获忽略来伪造通过。

**中文乱码怎么排查？** 源码、存档、IDE 与终端显示分别检查，文件读写已指定 UTF-8；不要把显示乱码另存覆盖正常文件。终端的 Git/包版本/Java 提示只是环境信息，不能替代实际的版本命令。