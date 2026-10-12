{
  "title": "第7至13周 Web接口与登录权限",
  "description": "Spring MVC、MyBatis、工单闭环、页面、登录、CSRF与资源权限。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 50,
  "group": "course",
  "draft": false
}
这七周把你已经会写的 Java 业务和 SQL 接到浏览器上，做出能保存数据、走完工单流程、区分三种用户的 Web 版本。按每周约18小时安排，任务块可以交换到不同日期；遇到考试就顺延，验收没有通过时先补当前周。

先做题和实验，再打开[本阶段参考答案](/learning/answers-web-security/)。答案包含关键接线代码、请求示例和排错顺序，供你在没有 AI 陪读时继续推进；它不是一套已经替你写完的项目。

## 本阶段共同约定

- 主线使用 Java 21、Spring Boot 4.1 系列、MyBatis Starter 4.0 系列。2026年10月12日核对的版本为 Boot 4.1.1、MyBatis Starter 4.0.0；新建时选择兼容的正式补丁版本，记录在 `pom.xml` 和项目说明中。Java21在 Boot4.1.1 支持范围内；MyBatis Starter4.0 支持 Boot4.0及以上。[Boot系统要求](https://docs.spring.io/spring-boot/system-requirements.html)、[MyBatis兼容表](https://mybatis.org/spring-boot-starter/mybatis-spring-boot-autoconfigure/)
- 业务包名示例为 `com.example.opsticket`，启动类放在该包顶层。业务代码逐步分为 `controller`、`dto`、`service`、`mapper`、`model`、`security`、`exception`，不必第一天创建全部空目录。
- 数据库为 `ops_ticket_dev`。用户1 `reporter_a`、2 `engineer_a`、3 `admin_a`、4 `reporter_b`；设备1 `PJ-001`投影仪、2 `AC-001`空调、3 `PR-001`打印机。初始工单101为用户1报修设备1的OPEN单，102为用户1报修设备2且指派用户2的IN_PROGRESS单，103为用户4报修设备1的OPEN单。每次验收注明是否已重置这份样本。
- 第7至11周尚无真实登录，只在本机运行，配置 `server.address=127.0.0.1`。临时身份由服务器端本地配置选定，写请求也不接受 `reporterId`、`actorId`。第12周彻底替换为会话身份。临时身份不属于最终成品，不能算作权限已经完成。
- 请求与响应统一使用 JSON；框架登录例外，它使用表单编码。创建成功201，查询与状态操作成功200，状态操作返回新状态与版本；登录、退出成功204且无响应体。参数错误400、未登录401、无权访问403、资源不存在404、状态或版本冲突409，意外故障500。字段与边界统一查[数据与接口约定](/learning/contracts/)。
- 时间先统一使用 `LocalDateTime` 加数据库 `DATETIME`，明确解释为北京时间，响应示例 `2026-12-07T14:30:00`。数据库会话和应用部署时保持相同约定；该字符串没有时区，不能直接当全球通用时间。后续如改成UTC应一起调整存储、API和展示。

## 第7周 建立HTTP接口

目标窗口：2026年11月23日至29日。

**前置能力：** 能用 JDBC 创建与查询工单，知道 JSON 是文本格式，能运行 Maven 工程。若 `java -version` 与 IDEA、Maven 的 Java 版本不一致，先完成前阶段的环境统一。

**本周成果：** 一份能够启动的 Boot 工程和三个接口：创建工单、列表查询、按编号查询。创建之后可以再查询得到；本周可保留此前 JDBC 存储实现，第8周再换 MyBatis。

**先理解：** Controller 像接待窗口，把 HTTP 参数交给 Java 方法；Service 决定业务是否合法；存储层读写数据库。DTO 是“这次交接允许携带的字段清单”。例如创建请求只有标题、描述和设备编号，状态、报修人、版本号由服务端决定。依赖注入就是由 Spring 创建对象，再通过构造器把它需要的对象交给它，和你第3周手动传入存储实现的思路相通。

**灵活任务块：**

1. **环境与最小启动，约3小时。** 用 Spring Initializr 生成 Maven、Java21、Boot4.1正式版工程，只选 Spring Web 和 Validation；在新目录检查生成结构，再有选择地迁入已有项目，保留 Git 历史，不覆盖旧源码。先运行一个返回 `{"message":"ok"}` 的 `/api/ping`，观察启动日志中的端口。
2. **请求和DTO，约3小时。** 设计 `CreateTicketRequest(title, description, deviceId)` 和 `TicketView`。读懂 `@RestController`、`@RequestMapping`、`@PostMapping`、`@RequestBody`、`@PathVariable`，不要一口气背完所有注解。
3. **连接业务，约5小时。** Controller 通过构造器取得 Service，再接此前存储接口。创建时验证标题、设备存在且启用；服务器给出 OPEN、报修人1、版本0以及创建时间。GET详情不存在时返回404；暂时把列表限制在演示数据量内。
4. **HTTP实验，约4小时。** 保存 `requests.http` 或 PowerShell 请求脚本；分别发送合法JSON、坏JSON、空标题、未知设备、未知编号。记录请求路径、方法、请求体、状态码和响应体。参数注解的完整整理留到第10周，此时先保证业务校验有效。
5. **独立修改与复盘，约3小时。** 增加列表的 `status` 查询参数，把参数一路传到存储查询；画出“请求→DTO→Service→存储→响应”的箭头图，口述一次。完成一次只包含本周变化的提交。

**验收：** 用客户端创建“教学楼投影仪无信号”，拿响应里的编号查询，标题与设备一致；重启后仍存在。GET未知编号404，POST空标题400；请求体自带 `status=CLOSED` 不能生成关闭工单。能够指着代码指出状态和报修人到底在哪里赋值。

**自测：** 7.1 为什么不直接把数据库实体当创建请求？7.2 Controller里每次 `new TicketService(...)` 与构造器注入有什么区别？7.3 请求到达服务端但返回404、400、500，各应先检查哪一层？

卡住时先看端口与完整异常的第一条业务相关堆栈，再看类是否在启动类所在包的子包中。[Spring REST入门](https://spring.io/guides/gs/rest-service/)只读接收请求和返回对象部分。

## 第8周 用MyBatis连接数据库

目标窗口：2026年11月30日至12月6日。

**前置能力：** 第7周三条接口可用；能手写工单INSERT、按编号SELECT和设备关联查询。

**本周成果：** Web接口改由 MyBatis 访问 MySQL。请求地址和业务规则保持一致，JDBC练习代码保留在学习记录中，正式流程只维护一个存储实现。

**先理解：** JDBC需要你亲自准备SQL、绑定参数、执行并读取结果；MyBatis把这些重复步骤封装起来，但SQL仍由你写。Mapper接口定义“我需要怎样的数据”，注解或XML提供实际SQL。Mapper不自动知道某字段是否允许修改，也不替你决定谁能看工单。数据库行、创建请求、展示结果可以是三个不同类型。

**灵活任务块：**

1. **接入配置，约3小时。** 添加 `org.mybatis.spring.boot:mybatis-spring-boot-starter:4.0.0` 与 `com.mysql:mysql-connector-j`。先用 `dependency:tree`查看Boot实际管理的驱动版本，核对它与MySQL服务端兼容；仍用8.0练习时可延续前阶段明确支持8.0的Connector/J9.7.0，不无条件追最新版，也不替换原有数据库。其余Boot管理依赖不随意改版本。用环境变量设置URL、用户名和密码，不把密码提交到Git。[驱动9.7.0兼容说明](https://dev.mysql.com/doc/relnotes/connector-j/en/news-9-7-0.html)
2. **最小Mapper，约3小时。** 给 `TicketMapper` 加 `@Mapper`，先实现 `findById`；用 `#{id}` 绑定值。字段使用明确列名，配置下划线转驼峰，验证 `reporter_id` 能进入 `reporterId`。复杂关联展示用单独DTO并起明确别名。
3. **创建与查询，约5小时。** 实现INSERT与生成主键回填，再实现列表和按状态筛选；增加 `GET /api/devices`返回设备列表，可按启用状态筛选。若返回实体用可写 `id` 配合 `useGeneratedKeys`；本阶段不对不可变record硬套主键回填。运行已有HTTP请求，确认替换存储没有改变行为。
4. **最小设备维护与排错，约4小时。** 实现 `POST /api/devices`新增设备，以及 `PATCH /api/devices/{id}/enabled`启用或停用；设备编码唯一，不删除历史引用。用API和SQL交叉查验，再制造并修复一次映射错误，记录排错步骤；管理权限第13周接入。
5. **理解与复盘，约3小时。** 独立补一个按设备编号筛选；指出Controller为什么无需知道数据库密码、Service为什么不拼SQL、Mapper为什么不负责HTTP状态码。提交 `pom.xml`、配置示例和映射代码。

**验收：** 创建后响应含真实数据库主键；重启应用后可查询；`deviceId`、`reporterId`、可空 `assigneeId`、`version` 映射正确。设备新增201，停用200且原有工单仍能查到，停用设备不能新报修。输入带单引号的标题仍作为普通数据保存，不破坏SQL；不会用 `${title}` 拼接用户输入。提交内容不含密码。

**自测：** 8.1 `#{title}` 与 `${title}` 有何区别？8.2 返回了工单但 `reporterId` 为null，应从哪三处排查？8.3 Mapper是接口没有手写实现，为什么仍能被注入？

提示：先把SQL复制到SQL客户端用具体参数运行，SQL正确再查Java映射。仅阅读[MyBatis Starter快速接入](https://mybatis.org/spring-boot-starter/mybatis-spring-boot-autoconfigure/)和[参数与结果映射](https://mybatis.org/mybatis-3/sqlmap-xml.html)的相关小节。

## 第9周 实现业务流转和事务

目标窗口：2026年12月7日至13日。

**前置能力：** MyBatis创建、查询已通过；能解释一次数据库提交与回滚。

**本周成果：** `assign`、`resolve`、`accept`、`reject`四种操作，以及处理结果和操作日志。工单更新与对应记录必须一起成功或一起失败。

**先理解：** 状态不是随便填写的标签。例如只有OPEN可以派单，派单后是IN_PROGRESS；处理中提交说明变成RESOLVED；验收通过CLOSED，退回则回到IN_PROGRESS。一次操作可能改工单、插处理说明、写日志三张表，事务把它们作为一次整体提交。事务负责完整性，具体允许怎样跳转仍由你判断。

**灵活任务块：**

1. **规则表，约2小时。** 按项目说明写四行“当前状态→动作→目标状态→必需参数”。派单要求有效工程师编号；处理和退回要求非空说明；关闭不允许继续变更。请求路径统一为 `/api/tickets/{id}/动作名`。
2. **日志表与请求，约3小时。** 用 `ticket_action_log(id,ticket_id,actor_id,action,from_status,to_status,note,created_at)` 保存日志；`ticket_resolution` 保存每次工程师提交，退回后再次处理新增记录。请求含 `expectedVersion`，`assign`另含 `engineerId`，`resolve`另含 `content`，`reject`另含 `reason`；日志说明仍写入 `note`列。
3. **先做派单，约4小时。** Service检查对象存在、当前状态和工程师；Mapper的UPDATE带 `id`、预期状态、`expectedVersion`条件，成功时版本加1。检查影响行数，0行抛业务冲突。把更新和日志写入放进一个公开的 `@Transactional` Service方法。
4. **完成其他操作，约5小时。** 延续相同结构；resolve再保存处理结果，reject保留原处理人和历史处理说明。详情响应增加 `actionLogs`和 `resolutions`，按时间与id正序展示历史。暂时由本机服务端配置选择演示操作者，不从JSON取操作者。第12至13周接入真实身份和资源范围；本周不声称已经防越权。
5. **验证与复盘，约4小时。** 正常走完两条路径：直接验收；退回后再次处理再验收。在练习分支临时让日志插入前抛 `RuntimeException`，实际调用事务方法并查询数据库，确认状态和版本均未改变，再移除故障代码。总结事务注解生效条件。

**验收：** 两条路径都留下顺序正确的日志；重复派单、重复验收409，日志不多一条。没有 `POST /setStatus` 任意改状态接口。故障实验中，工单、版本、处理结果和日志一起回滚。第14周再用真正并发请求加固和验证条件更新。

**自测：** 9.1 已更新工单但写日志失败，为什么不能吞掉异常后返回“失败”？9.2 同类中 `this.assign(...)` 调用可能让事务失效，原因是什么？9.3 UPDATE返回0行时，为什么不能继续写“派单成功”日志？

提示：优先使用一个数据源，Mapper交给Spring管理，不手动开启另一个SqlSession。[Spring事务注解](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)、[MyBatis与Spring事务](https://mybatis.org/spring/transactions.html)。

## 第10周 校验参数和分页评论

目标窗口：2026年12月14日至20日。

**前置能力：** 四种状态操作和日志回滚已验收。

**本周成果：** 列表有稳定分页与筛选；详情可显示评论；错误返回固定的 `code` 与 `message`。用户能知道如何修正输入，开发者能从日志定位意外故障。

**先理解：** 校验分两类：标题为空这类“单看输入就能判断”的要求交给DTO校验；设备已停用、工单不允许再派单这类“需要数据库现状”的要求放Service。分页也不是从全部数据中随便截几条：先用一致条件计算总数，再用固定排序取当前页，权限接入后总数和列表都要带相同的可见范围。

**灵活任务块：**

1. **输入边界，约3小时。** 使用 `jakarta.validation` 的 `@NotBlank`、`@Size`、`@NotNull`、`@Positive`；Controller加 `@Valid`。明确标题1至50字符、描述1至2000、评论1至1000；trim去除首尾空白后检查，数据库列长也要容纳这些值。数字用包装类型以区分缺失与0。
2. **分页筛选，约4小时。** 定义 `page` 从1开始、`size`默认10且1至100；`offset=(page-1)*size`用long计算。支持 `status`、`deviceId`；排序固定 `created_at DESC,id DESC`。返回 `items,total,page,size`，不把客户端提供的排序字符串直接拼进SQL。
3. **评论，约3小时。** POST `/api/tickets/{id}/comments`保存非空内容，GET同一路径按时间和id正序分页读取。作者来自服务器身份；工单不存在404。本版本关闭工单仍允许评论，但评论不改变状态。
4. **错误与日志，约4小时。** `@RestControllerAdvice`处理校验、找不到、业务冲突；坏JSON和数字类型错误也应400。业务异常给可理解的信息，意外异常返回通用500并在服务器保留堆栈；日志不记录密码和会话Cookie。没有必要把所有异常都变成200。
5. **边界与复盘，约4小时。** 独立造至少12条工单，把size设5检查三页；验证空结果、越界页、负页码、超大size、未知状态和全空格评论。写出一张“请求输入→预期状态码→数据库变化”的记录表。

**验收：** 固定数据下翻页无重复遗漏；第4页空列表且total仍正确。`page=0`、`size=101`、`status=INVALID`均400；未知工单评论404；空评论400；合法评论201且工单状态不变。相同评论重复发送会新增两条，本周没有承诺所有POST天然幂等，页面下一周降低误点，状态操作则已有冲突保护。

**自测：** 10.1 只有 `@Size(max=50)` 能拒绝空标题吗？10.2 count查询漏掉筛选条件会导致什么现象？10.3 为什么“所有异常都返回200和一段提示”会给联调带来问题？

提示：校验注解无效先检查Validation依赖、`jakarta`导入及 `@Valid`，不要反复修改正则。[Spring MVC校验](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-validation.html)。

## 第11周 做一个能够演示的页面

目标窗口：2026年12月21日至27日。

**前置能力：** HTTP客户端已能走完整流程，分页和错误可预测。先修接口，再做页面。

**本周成果：** 简单列表、创建表单、详情、评论与操作按钮，以及最小设备管理表单；一个正常业务流程可以从页面完成。页面从Boot同一端口提供，第一版无需Vue、React或单独的前端构建工程。

**先理解：** HTML决定有哪些输入框和按钮，JavaScript负责点击后发请求、读取响应并修改页面。`fetch`返回Promise，可以用 `await`等待结果；HTTP400并不自动使fetch抛网络异常，必须检查 `response.ok`。同源指协议、主机、端口相同，用相对路径 `/api/tickets` 可避免把开发地址写死。[Fetch官方说明](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)

**灵活任务块：**

1. **静态页面，约2小时。** 在项目的 `src/main/resources/static` 中建立 `index.html` 和 `app.js`，从 `http://localhost:8080/`打开。先显示一个标题和按钮，确认浏览器能加载脚本；不通过双击HTML的 `file://`打开。[Boot静态资源说明](https://docs.spring.io/spring-boot/reference/web/servlet.html#web.servlet.spring-mvc.static-content)
2. **列表和详情，约4小时。** 用fetch获取第一页；用 `document.createElement` 和 `textContent`显示编号、标题、状态。点击一条加载详情、评论和日志。标题与评论是用户输入，用文本方式显示，不直接塞进 `innerHTML`。
3. **创建和流转，约5小时。** 表单提交时阻止默认刷新，把字段转换成JSON；成功后刷新列表，失败保留输入并显示提示。操作携带详情里的版本号；409提示刷新后重试，不自动覆盖。再用相同表单方法做设备新增及启停，页面保持简朴。演示角色此时仍是服务器临时身份，不设计能伪造身份的前端下拉框。
4. **失败反馈，约4小时。** 统一请求函数，处理JSON响应和204空响应；请求过程中禁用相关按钮，结束恢复。测试后端关闭、参数错误和重复点击。登录将在下周加入，此时预留401跳登录的处理即可。
5. **演示与表达，约3小时。** 做一段3分钟本地演示并写项目README：业务、已实现功能、启动方式、当前限制。写简历草稿，只写已完成的接口、SQL、事务与排错，不写尚未完成的登录或高并发。

**验收：** 页面可以创建、查看、评论并展示状态变化；设备可新增、停用，报修只能选择启用设备；错误信息可见且用户输入保留。把标题设为 `<b>测试</b>`，页面应显示这些文字而不是粗体标签。Network面板能找到请求JSON、响应状态和返回数据。状态操作200时用新版本刷新页面；下周登录退出会返回204，辅助函数应支持空响应。

**自测：** 11.1 fetch遇到500为什么可能仍进入正常返回分支？11.2 `textContent` 与 `innerHTML` 用于评论有什么差别？11.3 按钮被隐藏或禁用，是否就能阻止用户直接调用接口？

提示：页面无反应先开浏览器Console；请求失败再查Network的URL、方法、Content-Type和响应体。CSS到“能读、能点击”即可，余下时间用于业务演示。

## 第12周 登录退出与会话

目标窗口：2026年12月28日至2027年1月3日。

**前置能力：** 同源页面可用；能理解浏览器发送请求时会携带Cookie；能看懂Service构造器注入。

**本周成果：** 三类演示账号能登录与退出，API能识别会话用户；数据库保存密码哈希。客户端不再有改变当前用户编号的入口，服务器移除临时身份实现。

**先理解：** 认证回答“你是谁”，授权回答“你能做什么”。Session把登录身份留在服务器，浏览器持有会话Cookie；它不是把密码反复传给每个接口。密码哈希由框架编码器生成并匹配，不能通过每次重新encode后直接比较字符串。CSRF令牌帮助服务端验证修改请求的来源意图，它与登录身份是两回事。

**灵活任务块：**

1. **账号读取，约3小时。** 添加Spring Security依赖。建 `UserDetailsService`，用MyBatis按唯一username读取 `app_user(id,username,password_hash,role,enabled)`，返回框架的用户信息。`role`存REPORTER/ENGINEER/ADMIN；配置 `.roles(...)`时框架添加ROLE_前缀，不要重复添加。
2. **框架登录，约4小时。** 使用 `SecurityFilterChain` 和 `formLogin`，POST `/api/login`提交 `username/password`表单参数；成功204、凭据错误401。通过PasswordEncoder生成演示哈希，保存完整编码前缀；停用账号不能登录。不要自己写“仅authenticate然后返回成功”的Controller。
3. **CSRF与页面，约4小时。** 保留默认CSRF，GET `/api/csrf`允许匿名获取 `headerName/token`，响应不缓存。登录及其他POST带该请求头；登录成功和退出成功后重新获取令牌。参考答案提供同源fetch接线示例，先逐句解释再使用。
4. **身份与退出，约3小时。** GET `/api/me`只返回当前账号的id、username和role；从 `Authentication.getName()`回查用户，拒绝不存在或停用用户，绝不返回哈希。框架处理POST `/api/logout`并结束会话，成功204。修改工单的操作者来自这条服务器身份链。
5. **浏览器验收与复盘，约4小时。** 用普通窗口和无痕窗口建立两个独立会话。记录登录前后Cookie与/api/me变化、错误密码、停用账号、退出后再次查询以及缺失CSRF的结果。

**验收：** 未登录GET工单401；错误密码且CSRF正确时401；正确登录204，随后/api/me200；退出后GET工单401。已登录但缺失或错误CSRF的POST403，携带新令牌可通过认证继续业务校验。未登录POST也可能先因CSRF缺失返回403，这是安全过滤器先后顺序，不要为追求“所有情况都是401”关闭CSRF。

**自测：** 12.1 为什么 `authenticate` 返回成功不等于下一次请求已经登录？12.2 正确密码却收到403，先查什么？12.3 为什么登录成功后，首次创建工单可能因继续使用旧CSRF令牌失败？

本周理解主线即可，不扩展JWT、刷新令牌或单点登录。[表单登录](https://docs.spring.io/spring-security/reference/servlet/authentication/passwords/form.html)、[会话持久化](https://docs.spring.io/spring-security/reference/servlet/authentication/session-management.html)、[CSRF令牌端点](https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html#csrf-integration-mobile)。

## 第13周 限制资源范围和业务操作

目标窗口：2027年1月4日至10日。

**前置能力：** 登录退出已通过，包括两份独立会话；业务操作已经从会话获得actorId。

**本周成果：** 报修人只能查看自己的工单，工程师只能看分配给自己的工单；管理员查看全部并负责派单。权限同时覆盖列表、详情、评论、日志、处理结果和写操作。

**先理解：** “是工程师”只是角色条件，“这张工单分配给当前工程师”是数据条件。两个都满足才能处理。路径中的工单编号只是用户声称要访问的对象，服务器必须查出它，再核对归属。只限制列表仍可能让人直接改URL查看别人的详情。

**灵活任务块：**

1. **写权限矩阵，约2小时。** REPORTER可创建、查看自己的单、评论、验收或退回自己的待验收单；ENGINEER可查看与评论自己的任务、提交处理说明；ADMIN可查看与评论全部、派单和管理设备。管理员不替报修人验收，工程师不能把单指给自己。
2. **统一身份与规则，约4小时。** 将会话身份解析集中在一个 `CurrentUser`组件，将角色和资源判断集中到Service或专门Policy。每个入口调用同一规则，避免Controller之间复制后漏改；数据不允许时返回403，确实不存在返回404。
3. **读权限，约4小时。** 列表查询与count都带服务端生成的范围：报修人 `reporter_id=当前id`，工程师 `assignee_id=当前id`，管理员不限。详情、评论列表、日志和结果先检查工单可见性。前端传来的 `reporterId=别人` 不能扩大范围。
4. **写权限，约4小时。** 创建强制reporterId=本人，派单仅管理员；resolve同时检查工程师角色、assigneeId和IN_PROGRESS；accept/reject同时检查报修人角色、reporterId和RESOLVED。评论复用可见性判断。设备新增和启停限定ADMIN，设备读取供已登录用户使用。条件UPDATE继续包含状态与版本，涉及操作者的更新再加归属条件。
5. **越权实验与复盘，约4小时。** 用reporter_a读取103，应403；读取列表不含103。用reporter_b验收用户1的单、用另一工程师处理不属于他的单、用报修人调用assign，均403；客户端手填actorId不改变日志作者。整理权限矩阵及验证记录，提交本阶段版本。

**验收：** 每个“允许”至少测一次，每类“拒绝”至少测一次。成功登录但越权403；本人合法请求参数错误400；本人重复状态操作409。失败操作不改状态、不增加结果和日志。评论、日志、总数中都没有泄露其他人的工单信息；界面隐藏按钮只是体验，HTTP客户端绕过页面仍会被服务端拒绝。

**自测：** 13.1 `hasRole("ENGINEER")` 能否独自保证工程师只能处理自己的任务？13.2 为什么列表items过滤了，total却没有过滤，仍然是权限缺陷？13.3 用户在JSON里加 `reporterId=3` 或 `actorId=3`，服务端应如何处理？

提示：准备第二名工程师时使用新的虚构账号并保存同样格式的密码哈希；不要通过修改账号角色来冒充另一个会话。课程采用明确403展示越权错误；产品若选择把无权资源也返回404，应全局一致且测试说明。[Spring请求授权](https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html)。

## 进入下一阶段的门槛

你应能独立演示：报修人创建工单→管理员派单→工程师处理→报修人退回→工程师补充→报修人验收；能解释请求、SQL、事务、Session和权限在哪里生效。

保存三份证据：一张请求链路图，一组可重复执行的HTTP请求，一份包含失败场景的验收记录。第14周开始验证真正并发并补自动测试；没有通过第12至13周权限验收前，不把项目发布到公网。
