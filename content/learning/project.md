{
  "title": "设备运维工单平台项目说明",
  "description": "同一个纯 Java / Spring Boot / MyBatis / MySQL 工单项目：A1 业务闭环、A2 工程化、B 轻量 AI、C 效果评估与 D 可选进阶。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 15,
  "group": "start",
  "draft": false,
  "lastmod": "2026-11-27T00:00:00+08:00"
}

> 本页说明项目整体路线；具体代码现状与验收记录请配合[项目文档](/learning/project-docs/)和[学习时间线](/learning/#progress)阅读。计划中的能力不代表已经实现或掌握。

更新于 2026-11-27。项目统一采用 **Java 21 / Spring Boot 4.1.2 / MyBatis 4.1.0 / MySQL 8.4**，先交付可靠后端业务与工程保护，再在同一工程内轻量落地 AI 业务功能与效果评估，不引入 Kafka、Milvus、Neo4j、微调或本地推理部署。

## 当前实测进展（2026-11-27）

- **A1 核心业务**：已在真实 MySQL 跑通创建、派单（`assign`）、解决（`resolve`）、验收关闭（`close`）四态闭环，完成早期控制台/文件版旧代码清理并整理为标准 Spring Boot 8 子包分层。
- **A2 工程化（当前阶段）**：已实测 Spring Security + MySQL `app_user` 登录、`@PreAuthorize` 角色授权、`GET` 单条与日志的三角色归属隔离、`POST` 创建自动取登录人、`expectedVersion` 乐观锁（`409`）、`ticket_action_log` 审计表 + `@Transactional` 事务绑定与 H2 外键失败回滚测试（4 项全绿）。当前收尾列表权限、SLF4J 日志与基础验证后进入 B 阶段。
- **B / C / D**：尚未开始编码，按计划逐步推进。

## 目标与阶段

**A1（数据库与 HTTP 闭环）→ A2（认证授权、事务、并发与交付）→ B（Java AI 业务功能 B01–B09）→ C（效果评估与回归 C01–C04）→ 可选进阶 D（D01 MySQL 轻量 RAG / D02 外部 SOP 轻量 Skill）。**

| 阶段 | 亲手交付 | 达标证据 |
| --- | --- | --- |
| A1 后端业务闭环 | MySQL 建表、MyBatis 映射、创建/查询/派单/解决/关闭四态接口与规范分层 | 真实 MySQL 跑通四态流转与 400/404/409 分支，能独立画出调用链 |
| A2 工程与交付（当前） | MySQL 登录认证、三角色资源归属、乐观锁、操作日志与 `@Transactional` 回滚、SLF4J 日志与核心测试 | 多角色 `200/401/403/409` 实测、事务回滚测试通过、可复现启动与排错 |
| B Java AI 功能（B01–B09） | Java 模型客户端、结构化校验、超时降级、`@Async` 事务后异步回写、人工采纳/修改/驳回反馈闭环 | 真实模型调用与故障降级分开记录；事务回滚不误触发异步；过期建议被 `expectedVersion` 返回 409 |
| C 效果评估与回归（C01–C04） | 12–20 条固定案例（开发/留出集分离）、B09 真实采纳率统计、延迟/token/成本与单因子回归 | 两类指标分开列示真实分母，保留失败样本与回归前后对比 |
| D 可选进阶（D01–D02） | MySQL 全文/同设备 Top 3 轻量检索（轻量 RAG）、外部 Markdown/配置表排查 SOP（轻量 Skill） | 留出集有无检索对比与误召回分析；改外部规则无需改 Java 业务代码并做回归 |

## 第一版业务边界

设备来自虚构园区/实验室记录，无真实硬件连接。只保留三种角色：

| 角色 | 首版职责 | 不可越过的边界 |
| --- | --- | --- |
| REPORTER 报修人 | 选启用设备、创建、查自己的工单与日志、验收关闭 | 不能冒充别人报修、查询别人记录或自行派单 |
| ENGINEER 工程师 | 查分给自己的工单与日志、提交处理结果 | 不能处理别人名下工单或代报修人验收 |
| ADMIN 管理员 | 查询全部工单与日志、给 OPEN 工单指定启用工程师 | 不能随意跳状态或代报修人验收 |

流程为 `OPEN → IN_PROGRESS → RESOLVED → CLOSED`。首版不做验收退回、评论、公开注册、全套设备/用户后台、统计大屏。数据库包含 `device`、`app_user`、`ticket` 与 `ticket_action_log` 四张表；状态更新与写审计日志在同一 `@Transactional` 事务内执行，状态变更通过前置状态与 `expectedVersion` 乐观锁保护。

具体实现与验收细节见[项目文档](/learning/project-docs/)、[需求](/learning/project-requirements/)、[设计](/learning/project-design/)、[验收](/learning/project-verification/)。

## Java 轻量 AI 功能边界（B 阶段）

在现有 Spring Boot 项目中用 Java HTTP 客户端或官方 SDK 接入真实模型提供方：

1. 对工单生成结构化的 `summary` / `category` / `missingInformation` 建议，程序严格校验字段类型、枚举与长度。
2. 模型网络调用严格放在数据库写事务外，设置连接/读取超时与重试上限；关闭 AI 或模型故障时工单核心流程完全不受影响。
3. 使用 Spring `@Async` + 自定义有界线程池在工单写事务**提交后**异步触发分析并回写状态（`PENDING` / `DONE` / `FAILED`），做好同工单同版本幂等。
4. 提供**直接采纳 / 修改后采纳 / 驳回**接口并记录反馈差异日志；任何写回均重新校验 Java 角色权限、前置状态与 `expectedVersion`。

## 技术与学习方式

沿用 **Java 21 / Spring Boot 4.1.2 / MyBatis 4.1.0 / MySQL 8.4.13**。将“AI 辅助编程”和“项目内 AI 业务功能”严格分开记录；每次约 3 小时按最小可验证任务推进，完整阶段安排见[阶段学习计划](/learning/schedule/)。

## 求职匹配与信息边界

简历与面试只写实际运行验证过的功能、真实分母下的指标与个人独立贡献，不编造未测出的并发规模或提升比例；每次投递按目标岗位的学历、毕业届别、城市、出勤天数与连续实习月数逐项核对。

官方技术参考：[结构化输出仍需校验](https://docs.spring.io/spring-ai/reference/api/structured-output/converters.html) · [工具调用由应用控制执行](https://docs.spring.io/spring-ai/reference/api/tools.html)。
