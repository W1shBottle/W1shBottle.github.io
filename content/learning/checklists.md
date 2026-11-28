{
  "title": "技能 To-do List 与验收记录",
  "description": "纯 Java 后端技能清单：A1 业务闭环、A2 工程交付、M1 Redis（R01–R04）、M2 RabbitMQ（M01–M04）与二期后置扩展（O01–O04）。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 90,
  "group": "tools",
  "draft": false,
  "lastmod": "2026-11-28T00:00:00+08:00"
}

更新：2026-11-28（方案与周号统一：全站统一使用第 1–17 周编号，将 **Redis（R01–R04）** 与 **RabbitMQ（M01–M04）** 纳入第 15–16 周主线，放弃 Spring AI，不再在 Java 侧编写大模型调用与离线评测；AI / Agent 方向留待二期以独立 Python 服务对接本项目，与微服务拆分概念一并列为后置扩展 `O01–O04`）。此前 11-25 草案中的 Java 侧 AI 条目（`B01–B09`、`C01–C04`、`D01–D02`）已移入历史归档，不再计入当前活跃看板分母。主线必修由 51 项调整为 **46 项**（另设 5 项按需/后置），原有 **6 项已验收（`J01–J06`）** 与 **22 项跟练中** 均保持不变，待学 18 项。

## 怎样看这份清单

- `[x]`：这一条明确的小练习或解释已有通过记录，不代表整门技术已经熟练。
- `[ ] 【已练习】`：接触过或在指导下做过，后续通过一个独立变体确认；不要求现在从头重写项目。
- `[ ] 【正在学】`：当前优先做。`[ ] 【已看课，待复习】`：看过相关课程但久未写，项目实践按实际情况记录；`[ ] 【待学】`：到对应阶段再做。`[ ] 【按需】` / `[ ] 【后置】`：按需或二期扩展，不计入主线分母。
- 勾选前能做到：**解释用途 → 自己改出一个小变体 → 预测并验证结果 → 能定位一个相关错误**。只看懂助手给的代码，不自动勾选。
- 网页和连续阅读版展示当前验收快照，不会因点击自动保存或同步个人进度。可下载自学包，在自己的Markdown中把 `[ ]` 改为 `[x]` 记录；已勾项只说明本项目作者已有相应证据，不代表每位读者都已完成。
- 每次只挑当前阶段 1—3 项；同类断言已明确跳过的练习不再补成欠账，不用完成率催进度。

## 技术栈一眼看清

| 所处位置 | 技术/工具 | 学到什么程度 | 当前状态 |
| --- | --- | --- | --- |
| 已有基础 | Java 21、IDEA | 对象/接口/集合/异常/IO，能调试自己的业务 | 已练习，具体证据见 J 项 |
| 已有工具 | Git、Maven、JUnit Jupiter | 管理变更、依赖、构建和有意义的测试 | 已练习；已清理早期文件版演示，保留 `TicketTest` 与数据库事务/HTTP 测试 |
| A1 | MySQL、SQL、JDBC → MyBatis | 四表关系、Mapper 映射、条件更新与四态闭环、联合索引 `EXPLAIN` | 真实 MySQL 已跑通创建/派单/解决/验收关闭四态闭环与标准 8 子包分层 |
| A1 | HTTP/JSON、Spring Boot、Spring MVC、依赖注入 | 从请求到数据库的完整分层调用链 | 数据库查询/创建/派单/解决/关闭/日志接口均已接通；列表隔离与接口收口进行中 |
| A2（当前） | Bean Validation、统一响应、Spring Security、OpenAPI | `@Valid` 参数合法、`Result<T>`、MySQL 登录认证、三角色资源归属、Swagger/Knife4j 文档 | 已实测 MySQL `app_user` 登录、`@PreAuthorize`、单条/日志三角色归属与创建自动绑登录人；列表分页、Controller 瘦身与 OpenAPI 文档收尾中 |
| A2（当前） | Spring 事务、`expectedVersion` 乐观锁、审计日志、SLF4J | 状态变更与 `ticket_action_log` 同事务、版本冲突 409、MDC `requestId` 链路日志 | 已实测三动作乐观锁 `409`、流水提交与 H2 外键失败回滚（4 项全绿）；SLF4J 与真实 MySQL 并发/回滚测试待补 |
| A2 | Tomcat、Fat JAR、Docker Compose、Linux 基础 | `spring-boot-maven-plugin`、内嵌 Tomcat 线程参数、一键编排与 Linux 排错 | 待学；补齐 Web 服务器与部署基础 |
| M1 | Redis（Spring Data Redis） | Cache-Aside（防穿透/雪崩/一致性）、JWT 登录态与黑名单、`X-Request-Id` 防重幂等、分布式锁对比 | 待学；第 15 周核心实战 |
| M2 | RabbitMQ（Spring AMQP） | `AFTER_COMMIT` 异步通知解耦、TTL + 死信队列（DLX）超时告警、Confirm + 手动 ACK + 消费幂等 | 待学；第 16 周核心实战 |
| 二期（后置） | 微服务概念 + Python（FastAPI + LangGraph）Agent | 架构拆分设计；独立 Python Agent 服务直接复用本项目 OpenAPI / JWT / Redis / RabbitMQ | 后置扩展，不阻挡当前纯 Java 主线 |

## J：已有 Java 与工具基础

下面勾选项只对应学习记录中已经验证的具体行为，其余随项目自然巩固。

- [x] **J01 引用与对象**：能解释 `Ticket alias = first` 是共享对象引用；重新 `new` 后引用可以指向另一对象。证据：已口述判断。
- [x] **J02 static**：能解释静态字段由同一个类的对象共享，为什么会出现第二张工单的数据覆盖第一张的观察结果。证据：已口述判断。
- [x] **J03 Map 的键**：知道相同 key 的 put 会覆盖，能解释新增前检查重复编号的原因。证据：已口述判断。
- [x] **J04 编号算法**：能解释已有 1/2/5 时下一个编号应为 6，而不是 size()+1。证据：已口述；仅适用于当前内存练习，数据库不能照搬。
- [x] **J05 相对路径**：知道相同字符串可能因工作目录不同指向不同文件，并会检查工作目录。证据：已口述排查思路。
- [x] **J06 Git 本地提交**：已执行 status/add/commit/log，产生可见提交。后续仍需学习分支和冲突；不代表 Git 全部掌握。
- [ ] **J07【已练习】对象规则与接口**：读 Ticket、TicketRepository、两种实现和 Service；独立讲清 private/构造器/this/enum、long 与 Long、implements/Override、接口多态和构造器注入。完成一个业务规则的小改即可，不重写整套类。
- [ ] **J08【已练习】集合、泛型与空结果**：已练List/Map/Set、引用与Optional；ResponseEntity<ErrorResponse>已结合数组类比讲解。继续独立说明响应体类型，并完成一种筛选、解释顺序与空结果。
- [ ] **J09【已练习】异常和文件 IO**：读 FileStore/文件仓库；能解释 throw/throws/catch、受检与运行时异常、cause、Reader/Writer、UTF-8、try-with-resources。自己定位一次字段错误，不能把写文件失败当事务已回滚。
- [ ] **J10【已练习】构建、调试和测试**：用 pom/现有测试解释 main 与 @Test、断言和 @TempDir、test/package 的区别；独立下断点看调用链，改坏一处规则后关键测试应失败，恢复后通过。无需追加同质 assertEquals。

J07—J10作为沿途巩固项，不要求全部重新验收后才继续当前Web/数据库接线任务；只在新任务暴露具体缺口时补练。

## S：当前 SQL 与数据库基础（A0 / A1 前半）

阅读项目 `sql/01_schema.sql`—`06_transactions.sql`；SQL 文件已保存不等于每条都执行通过，真实记录以 SELECT 为准。

- [ ] **S01【实操通过，解释与变体继续复盘】条件组合**：2026-10-28已提交“打印机＋OPEN＋处理人为空”的SQL与正确结果（id=3）。本项还包含解释WHERE/AND/LIKE/IS NULL、引号、ORDER BY及预测改条件后的结果，暂不把这些全部勾为已掌握；在下一项JOIN筛选中验收，不重抄成功语句。
- [ ] **S02【已练习】表设计与约束**：画 device/app_user/ticket/ticket_action_log 关系；解释主键、自增、外键、唯一、NOT NULL、CHECK 和 NULL。能指出外键不检查 ENGINEER 角色、CHECK 不代替合法状态迁移。
- [ ] **S03【已练习，独立解释待巩固】多表查询**：JOIN/LEFT/RIGHT和别名已讲解；OPEN筛选得到打印机且处理人NULL，用户已反馈通过。继续在后续功能解释每个ON及NULL保留，不重抄整套查询。
- [ ] **S04【已练习】统计和分页**：COUNT为2/1，LEFT JOIN用COUNT(t.id)统计工单，HAVING=0筛出无工单设备；稳定分页、同筛选总数及偏移后空页已有反馈。下一业务变体验证独立解释，暂不标成全部熟练。
- [ ] **S05【已练习】事务与影响行数**：已练COMMIT/ROLLBACK、CHECK失败不自动撤销前一语句、条件更新及双连接version竞争；反馈A=1/B=0。Java条件更新、提交与模拟故障回滚已跟练；数据库状态流已接入乐观锁与操作日志事务，独立复盘继续巩固。
- [ ] **S06【待学】索引与 EXPLAIN 实测**：为 `ticket` 和 `ticket_action_log` 设计高频查询联合索引（如 `(reporter_id, status, created_at)`、`(assignee_id, status, created_at)`），造 1—5 万条测试数据执行 `EXPLAIN`，对比优化前后 `type/key/rows` 并保留真实样本与记录。

## W：把 SQL 接成后端业务（A1）

先一个请求，再逐步完成闭环；以下未来文件只在轮到任务时创建。

- [ ] **W01【查询与更新事务已跟练】JDBC**：Connection/PreparedStatement/ResultSet、参数绑定、wasNull与资源关闭；JdbcTicketUpdateDemo已实现版本查询、影响行数检查、提交/回滚与方法提取，用户反馈通过、助手核对源码。没有新增JDBC自动测试；独立改写与完整业务接库仍待验收。
- [ ] **W02【已跟练，继续验收】数据库生成 ID 与映射**：学习者跟写数据库 POST 并取得自增 id=9；独立解释主键回填和 add/create 差别，再逐步补映射字段。
- [ ] **W03【已跟练，继续验收】HTTP 和 JSON**：文件版GET/POST已有200/201/400/404证据；用断点观察setter/getter、缺字段与错误JSON。学习者反馈重启恢复及统一错误响应通过；数据库版四态接口均已通过 Apifox 实测，独立解释继续验收。
- [ ] **W04【已跟练，继续验收】Spring Boot/MVC 与依赖注入**：已有Bean与构造器注入、请求DTO和RestControllerAdvice；文件版及数据库查询/创建/流转 HTTP 已接通；独立解释对象/调用链、权限与分层边界继续验收。
- [ ] **W05【已跟练，继续验收】MyBatis**：`TicketMapper`、`UserMapper`、`TicketActionLogMapper` 已落地参数绑定、下划线转驼峰映射、创建主键回填、带 `expectedVersion` 条件更新的 `assign`/`resolve`/`close` 及审计日志插入，并在真实 MySQL 跑通全链路；补充动态条件分页 SQL 与真实 MySQL 隔离集成测试继续验收。
- [ ] **W06【已跟练，继续验收】分层与核心状态流**：已在真实 MySQL 跑通创建、派单（`assign`）、指定工程师解决（`resolve`）、原报障人验收关闭（`close`）四态闭环与 `ticket_action_log` 操作审计，并按 `controller/service/repository/mapper/domain/dto/config/exception` 规范分包（清理与分包由助手协助）；列表权限收尾、Controller 瘦身与独立变体继续验收。

## E：能运行、能交付的工程能力（A2）

收口纯 Java 后端的工程规范、接口文档、测试与部署能力，为接入 Redis / RabbitMQ 与可靠交付打牢基础。

- [ ] **E01【已跟练，继续验收】参数校验与统一响应**：已有 `ErrorResponse` 与 `GlobalExceptionHandler`；待接入 `spring-boot-starter-validation`（`@Valid`）、统一包装响应体 `Result<T>(code, message, data, requestId)`，并将 404/403/409 语义异常分类下沉到 Service 层。
- [ ] **E02【已跟练，继续验收】认证与登录态**：已完成 Spring Security 引入、`BCryptPasswordEncoder`、`DatabaseUserDetailsService`（MySQL `app_user` 表）、Basic Auth 实测（`200/403/401`）与 `POST` 的 CSRF 排错；下一步引入自定义 `LoginUser`（去掉 Controller 越层查 `UserMapper`）并升级为 JWT + Redis 登录态管理。
- [ ] **E03【已跟练，继续验收】角色与资源归属授权**：已完成 `GET` 单条工单与日志查询的三角色归属隔离、`POST` 创建自动取登录人、管理员派单、指定工程师解决与原报障人验收关闭实测；下一步收口 `/api/v1/tickets` 列表三角色隔离分页、补 `/api/v1/devices` 并清理无权限 `/api/db` 调试接口。
- [ ] **E04【已跟练，继续验收】业务事务与审计日志**：已亲手建出 `ticket_action_log` 表，在 `assign`/`resolve`/`close` 上用 `@Transactional` 绑定状态更新与写日志（实测 5 号工单 3 条流水提交），并亲手在隔离 H2 写出外键失败回滚测试（4 项全绿）；下一步补 `note` 处理说明列与真实 MySQL 隔离测试库回滚验证。
- [ ] **E05【已跟练，继续验收】乐观锁、防重幂等与并发冲突**：已在 `assign`/`resolve`/`close` 三条状态操作上亲手接入并实测 `expectedVersion` 乐观锁（旧版本返回 `409`、成功递增版本）；下一步结合 `X-Request-Id` 与数据库唯一约束/Redis 实现创建幂等防重，并补真实多线程并发竞争测试。
- [ ] **E06【待学】集成测试与并发测试**：保留现有 JUnit；基于真实 MySQL 隔离测试库补齐权限、事务回滚与多线程并发派单测试（验证并发竞争仅 1 次成功其余 409），区分单元/集成测试与 Mock/真实依赖。
- [ ] **E07【待学】SLF4J 规范日志与排错**：接入 SLF4J + `OncePerRequestFilter` 注入 MDC `requestId`，记录关键业务结果与异常链，严禁输出密码、Token 与密钥；沉淀一次完整的复现→根因→修复→回归排错记录。
- [ ] **E08【待学】Tomcat、Fat JAR 与 Docker/Linux 部署**：在 `pom.xml` 补齐 `spring-boot-maven-plugin` 打可执行 Fat JAR，显式配置内嵌 Tomcat 线程与连接队列参数；编写 `docker-compose.yml` 一键拉起 MySQL/Redis/RabbitMQ/应用，并在 Linux 环境下完成启动与日志/端口排错。
- [ ] **E09【待学】OpenAPI 接口文档与技术交付文档**：接入 SpringDoc OpenAPI 3 / Knife4j 自动生成在线接口文档，编写《系统架构与接口设计文档》（含 ER 图、四态图、错误码与微服务演进设计），规范 SQL 与 README。
- [ ] **E10【待学】Git 协作基本流程**：在练习分支完成一项修改，检查 diff，处理一次受控合并冲突；会区分工作区/暂存区/提交并保留有意义记录，不盲目回退未提交成果。

**A阶段总验收：** 标准 RESTful 工单闭环＋三角色权限/事务/乐观锁/索引验证＋OpenAPI 文档与可复现 Fat JAR 启动；本人能独立改一个完整小功能并解释设计。只完成勾选文档不能算验收。

## R：Redis 缓存、幂等与分布式基础（M1）

围绕设备运维工单真实读多写少、防重提交与登录态场景落地 Redis，打通主流 Java 后端高频中间件实践。

- [ ] **R01【待学】Redis 基础数据结构与 Spring 接入**：掌握 String/Hash/List/ZSet 与 TTL 过期策略；Docker 启动隔离 Redis 实例，通过 `Spring Data Redis` 完成读写、序列化与连接超时配置。
- [ ] **R02【待学】设备与工单 Cache-Aside 缓存**：查询设备与高频工单详情先查 Redis、未命中回源 MySQL 并回填缓存；落地空值缓存防穿透、随机 TTL 防雪崩、工单状态变更后删除缓存，能口述缓存与数据库一致性取舍及故障回落策略。
- [ ] **R03【待学】JWT 登录态、创建幂等防重与限流**：将 JWT 登录态/登出黑名单接入 Redis；利用 `SET key value NX EX` 拦截短时重复 `X-Request-Id` 报修请求（与 MySQL 唯一约束双保险），并为报修创建接口增加简易频控限流。
- [ ] **R04【待学】分布式锁对比与缓存压测验证**：结合派单/抢单场景理解 Redisson 分布式锁与数据库 `expectedVersion` 乐观锁的适用边界；使用 JMeter/Wrk 实测加 Redis 缓存前后的工单详情查询 QPS 与耗时对比并保留真实条件与数据。

## M：RabbitMQ 异步解耦与死信延迟（M2）

围绕事件通知解耦与工单 SLA 超时升级场景落地 RabbitMQ，同时为二期独立 Python Agent 订阅工单事件预留标准消息通道。

- [ ] **M01【待学】RabbitMQ 核心模型与 Spring AMQP 接入**：理解 Producer/Exchange（Direct/Topic）/Queue/Binding/Consumer，通过 Docker 启动 RabbitMQ（含管理控制台）并接入 `spring-boot-starter-amqp` 跑通消息收发。
- [ ] **M02【待学】事务提交后异步通知解耦**：工单创建、派单、解决、关闭通过 `@TransactionalEventListener(phase = AFTER_COMMIT)` 发布事件到 RabbitMQ，验证事务回滚时不误发消息；消费者异步写入站内通知/模拟告警，并预留标准事件格式供后续服务订阅。
- [ ] **M03【待学】TTL 与死信队列（DLX）实现 SLA 超时告警**：新建工单发送带 TTL 的延迟消息，到期路由至死信交换机与死信队列；消费者回查工单状态，若仍为 `OPEN` 则写入超时升级日志并触发告警，已派单则直接 ACK 忽略。
- [ ] **M04【待学】消息可靠性投递与消费端幂等**：开启生产者 Publisher Confirm/Return 回调与消息持久化；消费者启用手动 ACK（`manual`）并基于 `messageId`（Redis 或去重表）实现消费幂等，验证重复投递不产生重复告警及异常重试超限落入死信表。

## P：沿途补充的基础与求职能力

全程与项目并行推进，持续补齐算法、八股原理与项目表达。

- [ ] **P01【已练习】数据结构与算法（力扣 Hot 100）**：已有数组/次数统计/两数之和；每日坚持 1—2 道力扣 Hot 100 高频题（哈希、链表、双指针、二叉树、二分、滑动窗口与常见 DP），兼练 ACM 输入输出模式。
- [ ] **P02【待学】Java 基础、集合与 JVM 查漏**：重点复盘 `HashMap`/`ConcurrentHashMap`、equals/hashCode、泛型注解、JVM 内存结构与垃圾回收基础，整理成自己的八股笔记。
- [ ] **P03【待学】JUC 并发、线程池与 Tomcat 模型**：掌握线程/锁、`synchronized`/`ReentrantLock`、自定义有界 `ThreadPoolExecutor` 7 参数与拒绝策略，结合本项目讲清 Tomcat BIO/NIO 线程模型与数据库乐观锁的边界。
- [ ] **P04【待学】计算机网络与操作系统基础**：围绕一次工单 HTTP 请求讲清 DNS、TCP 三次握手/四次挥手、HTTP/HTTPS、Cookie 与 JWT、超时；熟悉 Linux 进程、端口、内存与日志排错命令。
- [ ] **P05【按需】最小页面能力**：按需用简单 HTML/CSS/JS/fetch 展示登录、工单列表与操作，不要求投入大型前端框架，不阻挡后端交付。
- [ ] **P06【持续】AI 辅助编程与独立排错能力**：每次记录工具给了什么；坚持自己读调用链、手写小变体并实测验证、独立定位错误。
- [ ] **P07【待学】项目表达、八股笔记与实习投递**：用 5—8 分钟脱稿讲清业务、权限隔离、事务回滚、Redis/RabbitMQ 设计与至少一个真实故障排查；完成 MySQL/Redis/RabbitMQ/JUC/JVM 核心笔记并按节奏准备投递。

## O：二期扩展与后置规划（不计入主线完成率分母）

当前主线先交付扎实的纯 Java 后端；AI / Agent 能力统一采用市场主流 Python 栈在二期以独立服务形态推进：

- [ ] **O01【后置】微服务拆分设计与 Spring Cloud 概念**：不在当前阶段硬拆单体，但在架构文档中完成设备域/工单域/通知域/AI 域的拆分设计，理解 Nacos、Gateway、OpenFeign 与最终一致性。
- [ ] **O02【后置】Python FastAPI + LangGraph 独立 Agent 服务**：二期另起独立 `ops-agent-py` 服务，直接复用本项目的 OpenAPI 接口、JWT 权限、Redis 与 RabbitMQ。
- [ ] **O03【后置】Agent 受控工具调用、轻量 RAG 与人工采纳联调**：在 Python 侧落地受控只读 Tool Calling（带步数/超时护栏）与设备资料/历史工单检索引用，写回工单操作由人工确认并经 Java 接口校验权限与 `expectedVersion`。
- [ ] **O04【后置】MCP、多 Agent 与系统评测进阶**：在单 Agent 可靠联调后，按需扩展 MCP 协议、多 Agent 协作与系统评测。

## 今天只看这一小段

1. **第 14 周（A2 收口与规范化，当前优先）**：收口 `/api/v1/tickets` 列表三角色权限与动态分页、补 `/api/v1/devices` 与联合索引 `EXPLAIN`；瘦身 Controller（`@Valid`、`LoginUser`、`Result<T>`），接入 OpenAPI 3 / Knife4j、SLF4J + MDC 与 Fat JAR / Tomcat 参数配置。
2. **第 15—16 周（M1 Redis + M2 RabbitMQ）**：依次完成 JWT + Redis、Cache-Aside 缓存、幂等防重，以及 RabbitMQ `AFTER_COMMIT` 异步通知、TTL + 死信队列 SLA 超时告警、Confirm + 手动 ACK + 消费幂等。
3. **第 17 周（并发验证、Docker 部署与压测）**：补真实 MySQL 多线程并发派单测试、Docker Compose 一键编排与缓存压测对比；全程并行每日力扣 Hot 100 与核心八股整理。

不因更新计划更改任何已有验收勾选。

## 每周记录

```text
第__周，实际日期：____至____，实际投入：__小时
本周目标：
本周完成的任务：
独立完成的代码/SQL：
参考答案后完成的部分：
仍不能解释的概念：
正常输入与运行结果：
至少一个边界输入与结果：
Git提交编号或本地版本备份：
本周一个错误及原因：
验收：通过 / 需补课 / 顺延
下周第一个小任务：
```

## 阶段进度与能力证据

2026-11-28 定稿按统一第 1–17 周的纯 Java 后端主线 **起步（J）→ A1（S/W）→ A2（E）→ M1 Redis（R）→ M2 RabbitMQ（M）→ 贯穿（P）** 执行，二期独立 Python Agent 与微服务拆分概念列为后置扩展（`O01–O04`）；不用日历替你勾完成。每项填写“项目有没有实现”和“本人如何证明理解”两列。看过、跟写、独立完成和运行验证分别记录，AI 生成不自动计入掌握。

| 阶段检查 | 项目实现证据 | 本人能力证据 | 当前结论 |
| --- | --- | --- | --- |
| A0 SQL/JDBC | JOIN筛选、统计/分页、SQL事务/版本竞争、JDBC查询/更新回滚已有跟练反馈 | 独立解释与新业务变体继续巩固 | 已切入正式 Spring Boot + MyBatis 项目 |
| A1 数据库/HTTP 闭环 | 真实 MySQL 已跑通创建、派单、解决、验收关闭四态闭环，清理早期文件代码并完成标准 8 子包分层 | 已实测 4 号/5 号工单全链路与 400/404/409 分支，独立变体继续验收 | 主流程已跑通，进入 A2 工程化 |
| A2 工程规范与交付（当前） | 已落地 MySQL `app_user` 登录、`@PreAuthorize`、单条/日志三角色归属隔离、创建自动绑登录人、`expectedVersion` 乐观锁、`ticket_action_log` + `@Transactional` 与 H2 外键回滚测试（4 项全绿） | 已实测多角色 `200/401/403/409`、修复 `findLogs` 角色比对 bug 并手写外键回滚测试 | 当前第 14 周，收尾列表分页、Controller 瘦身、OpenAPI、SLF4J 与 Fat JAR |
| M1 Redis 缓存与幂等（R01–R04） | Spring Data Redis、JWT+Redis、Cache-Aside 缓存、创建幂等防重与压测 | 解释穿透/雪崩/一致性、分布式锁 vs 乐观锁并实测压测对比 | 第 15 周主攻 |
| M2 RabbitMQ 异步与死信（M01–M04） | `AFTER_COMMIT` 异步通知、TTL+DLX 超时告警、Confirm+手动 ACK+消费幂等 | 验证事务回滚不误发、超时告警与重复消息幂等去重 | 第 16 周主攻 |
| O 二期后置扩展（O01–O04） | 微服务拆分设计；独立 Python（FastAPI + LangGraph）Agent 服务对接本项目 | 不阻挡纯 Java 后端交付，后续双栈拓展 | 后置扩展 |

已有Java/Maven/文件仓库成果不要求重复做完；若某概念无法解释，只补对应小练习。跳过同质断言可以记录已理解，但不能将未执行的关键事务或压测验证写成通过。

## 历史归档（暂不执行）

2026-11-28 路线调整为**纯 Java 后端（含 Redis + RabbitMQ）**、二期独立 Python Agent 后，原 11-25 草案中的 Java 侧 AI 条目（`B01–B09`、`C01–C04`、`D01–D02`）及早期并行草案条目已归档保存（暂不执行），不再留在当前活跃清单与进度看板统计中。

## 两类AI使用记录

```text
AI辅助编程：
工具给了哪些提示/代码：
我逐行读懂了什么，哪里仍不懂：
关闭答案后独立改动：
测试/排错证据：

项目模型功能：
真实调用 / 模拟故障 / 尚未配置：
模型提供方与模型标识：
prompt/schema版本：
caseId、输入事实、预期范围、实际建议：
人工判定与失败原因：
端到端延迟、tokens、重试次数：
费用实际值或估算依据（未知就写未知）：
不使用AI的对照结果：
下一次只改哪一项及回归结果：
```

API key、密码、Cookie不进入笔记；案例用虚构数据或必要脱敏。约20个固定案例可作为起点，阈值先定再跑，不替换失败案例凑成绩。无真API时模型质量/费用仍待验证。

## 功能验收单

| 项目 | 填写内容 |
| --- | --- |
| 功能 | 例如管理员派单 |
| 前置数据 | 隔离库中自己创建的一张OPEN工单，记录真实id和version；管理员已登录 |
| 操作 | 给工程师2派单，带期望版本0 |
| 预期 | 一次成功；状态IN_PROGRESS；版本递增；操作日志一条 |
| 实际 | 自己填写响应、数据库记录或测试结果 |
| 异常场景 | 重复请求、错误角色、错误工程师、日志插入失败 |
| 独立小改 | 例如新增一个允许的筛选条件或补充参数校验 |
| 结论 | 通过或待修，写出原因 |

验收只在专用练习库进行。并发实验前记录初始状态，实验后检查结果；不要把前一次实验留下的数据当成新实验起点。

## 缺陷报告

```text
标题：在什么条件下出现什么错误
环境：Java / Boot / 数据库 / 浏览器版本
前置数据和用户角色：
最小复现步骤：1. ... 2. ... 3. ...
预期结果：
实际结果：
相关错误与日志：
已排除的原因：
根本原因：
修改了什么及为什么：
如何防止再次出现：回归用例/约束/校验
验证结果：
```

## 项目README清单

- [ ] 说明项目解决的问题、角色和核心流程。
- [ ] 列出实际使用的版本和所需工具。
- [ ] 有可复制的初始化、启动、测试命令及预期结果。
- [ ] 有配置示例，但没有真实密码或密钥。
- [ ] 有演示账号的本地初始化方式和虚构数据。
- [ ] 说明表结构、核心接口和错误处理。
- [ ] 说明权限边界、并发保护与事务一致性。
- [ ] 记录真实测试、排错和性能测量条件。
- [ ] 说明已知限制及尚未实现的扩展。
- [ ] AI写明真实/模拟验证、配置缺项、故障回退、质量与成本来源；未做Agent不写已实现。
- [ ] 能在新的练习环境依说明复现。

## 项目讲解提纲

用5—8分钟讲清：谁需要这个系统；一张工单如何流转；自己实现哪些模块；为什么这样组织代码；一次真实问题如何定位；如何证明权限和并发正确；当前版本的局限。

技术追问时不要背一整段宣传文字。先说具体场景，再说方案与验证；没有实际测量就不写吞吐量，没有真实用户就不写服务人数。

## 投递记录

| 日期 | 公司及岗位链接 | 是否接受本人届别 | 到岗时间与天数 | 连续月数 | 当前状态 | 反馈与下一步 |
| --- | --- | --- | --- | --- | --- | --- |
| 待填写 | 待填写 | 待核对 | 待核对 | 待核对 | 未投递 | 待填写 |

状态可用未投递、已投、笔试、面试、等待结果、录用、结束。每周选择一次统一更新，依据实际反馈改简历或补知识，不用每天反复刷新。
