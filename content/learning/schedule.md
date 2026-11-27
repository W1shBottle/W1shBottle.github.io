{
  "title": "Java 设备运维工单与轻量 AI 阶段学习计划",
  "description": "纯 Java 主线定稿：A1 后端闭环 → A2 工程交付 → B01–B09 轻量 AI → C01–C04 评估回归（可选 D01–D02）。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 20,
  "group": "start",
  "draft": false,
  "lastmod": "2026-11-27T00:00:00+08:00"
}

更新于 2026-11-27（纯 Java 主线定稿于 2026-11-25）。每天约 3 小时，按可验收的最小任务推进。

**唯一主线：A1（数据库与 HTTP 业务闭环）→ A2（认证授权、事务、并发与交付）→ B（Java AI 业务功能 B01–B09）→ C（效果评估与回归 C01–C04）→ 可选进阶 D（D01 MySQL 轻量 RAG / D02 外部 SOP 轻量 Skill）。**

## 定稿边界与克制原则

- **技术栈收口**：全部基于现有 **Java 21 / Spring Boot 4.1.2 / MyBatis 4.1.0 / MySQL 8.4** 轻量落地，**不引入 Kafka、Milvus、Neo4j，不做微调与本地推理部署**。
- **B 阶段定稿（B01–B09）**：在原有模型接入、结构校验、降级与调用记录（`B01–B07`）基础上，加入 **B08（Spring `@Async` + 自定义有界线程池的事务后异步触发、状态回写与同工单同版本幂等，联动 P03）** 和 **B09（直接采纳 / 修改后采纳 / 驳回接口与反馈差异日志，保留人工确认权与权限/版本校验）**。
- **C 阶段定稿（C01–C04）**：修订 **C02（效果评估）**，采用离线固定案例集（开发集/留出集分离）与 B09 交互反馈日志真实采纳率双口径统计，分开列示并写清真实分母。
- **可选进阶 D（不阻挡 A→B→C 结项）**：**D01（MySQL 全文/同设备过滤 Top 3 已解决工单轻量 RAG + 留出集对比回归）**、**D02（外部 Markdown/配置表排查 SOP 与分类口径动态拼装 + 回归对比）**。完整验收口径见[技能 To-do List 与验收记录](/learning/checklists/)。

## 当前进度与实测证据（2026-11-27）

- **A1 已跑通主流程**：真实 MySQL 跑通创建、派单（`assign`）、指定工程师解决（`resolve`）、原报障人验收关闭（`close`）四态闭环；已清理早期文件/控制台演示代码，统一为标准 Spring Boot 8 子包分层。
- **A2 当前正在收尾**：已亲手落地并实测 Spring Security + MySQL `app_user` 登录、`@PreAuthorize` 角色授权、`GET /api/db/tickets/{id}` 与 `GET /api/db/tickets/{id}/logs` 三角色归属隔离、`POST /api/db/tickets` 自动取登录人、`expectedVersion` 乐观锁（`409`）、`ticket_action_log` 审计表 + `@Transactional` 事务绑定与 H2 外键失败回滚测试（4 项全绿）。
- **验收口径**：主线 51 项中已正式验收保持 6 项（`J01–J06`），跟练待巩固 22 项，待学 23 项。
- **下一步**：收尾 A2 剩余小边界（`GET /api/db/tickets` 列表接口权限、SLF4J 日志与基础集成验证），随后正式进入 **B 阶段：Java AI 业务功能（B01–B09）**。

## 阶段与验收总表

| 阶段 | 核心内容 | 达标证据 | 当前状态 |
| --- | --- | --- | --- |
| 起步（J01–J10） | Java 语法、集合、异常、Git、Maven、JUnit | 口述边界判断、独立小改与可复现测试 | 6 项已验收，4 项沿途巩固 |
| A1 后端业务闭环（S/W） | MySQL 三表、SQL、JDBC、MyBatis 映射与四态闭环 | 真实 MySQL 跑通创建/派单/解决/关闭及 400/404/409 分支 | 主流程已跑通，跟练待巩固 |
| A2 工程与交付（E01–E10） | MySQL 登录、角色与资源归属、乐观锁、操作日志与事务回滚、SLF4J、测试与运行 | 多角色 `200/401/403/409` 实测、回滚测试通过、可复现启动与排错 | **当前阶段（收尾中）** |
| B Java AI 功能（B01–B09） | 模型 API、结构化校验、降级、用量记录、`@Async` 异步回写、人工采纳闭环 | 真实调用与模拟故障分开记录；事务回滚不误触发异步；过期建议 409 | 待开始 |
| C 效果评估与回归（C01–C04） | 固定案例集、双口径评估、延迟/token/成本记录、单因子回归 | 标注真实分母与失败归因，无真实调用不以 Mock 充当效果 | 待开始 |
| D 可选进阶（D01–D02） | MySQL Top 3 轻量 RAG、外部 SOP 轻量 Skill | 留出集对照与误召回/退化分析，不阻挡主线结项 | 按需 |

## 按阶段看网课与做练习

学习方式：遇到卡点再针对性看 1–2 集短视频并对照官方文档，看完立刻回到工单项目写最小变体并验证，不刷完大课再动手。

1. **事务与代理边界复盘**：若对 `@Transactional` 代理、异常回滚条件存疑，可对照 [Spring 事务官方文档](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html) 及黑马 JavaWeb [P101 事务管理](https://www.bilibili.com/video/BV1yGydYEE3H/?p=101) / [P102 Spring 事务](https://www.bilibili.com/video/BV1yGydYEE3H/?p=102) 核对自己的 `assign`/`resolve`/`close` 链路。
2. **A2 收尾（列表权限、SLF4J 与集成测试）**：结合 [Spring Security 官方文档](https://docs.spring.io/spring-security/reference/index.html) 与 [Spring Boot 测试文档](https://docs.spring.io/spring-boot/reference/testing/index.html) 补齐列表接口三角色权限过滤、结构化日志与关键回归测试。
3. **进入 B 阶段（模型调用与异步回写）**：先以虚构工单跑通 Java HTTP/SDK 调用与 JSON Schema 校验，再参考 [Spring 异步执行文档](https://docs.spring.io/spring-framework/reference/integration/scheduling.html) 配置自定义有界线程池与事务提交后事件触发（`B08`），最后完成人工采纳与反馈差异日志（`B09`）。

## 历史路线归档说明

2026-11-14 至 11-24 曾短暂规划“Python（Y）+ Redis（R）+ LangGraph / Python 只读 Agent（G）”双栈并行方案；2026-11-25 复盘工程复杂度与实习求职聚焦后，已正式收口为单一纯 Java / Spring Boot / MyBatis / MySQL 主线，上述旧分支已归档备查，不再作为当前执行计划。
