{
  "title": "学习",
  "description": "基于 Java / Spring Boot / MyBatis / MySQL / Redis / RabbitMQ 的设备运维工单后端路线：A1 → A2 → M1 Redis → M2 RabbitMQ，二期独立 Python Agent 后置。",
  "date": "2026-10-12T12:00:00+08:00",
  "lastmod": "2026-11-28T00:00:00+08:00",
  "draft": false
}

以现有 **Java 21 / Spring Boot / MyBatis / MySQL / Redis / RabbitMQ** 设备运维工单系统作为纯 Java 后端主线（**A1 业务闭环 → A2 工程规范与交付 → M1 Redis 缓存与幂等 → M2 RabbitMQ 异步解耦与死信队列**）：先把权限、事务、乐观锁、索引、缓存、消息队列、接口文档与部署压测彻底打透，不采用 Spring AI；AI / Agent 能力留待二期直接以独立 **Python（FastAPI + LangGraph）** 服务对接本项目的 OpenAPI、JWT、Redis 与 RabbitMQ。

此前 11-25 草案中的 Java 侧 AI 条目（`B01–B09`、`C01–C04`、`D01–D02`）已归档暂不执行，既有全部验收勾选（`J01–J06`）与跟练记录保持不变。

下一次继续 **第 14 周（A2 工程规范收口）**：`/api/v1/tickets` 路径收口、下线调试读接口与列表三角色隔离已实测通过；下一步通过 MyBatis XML 实现 `GET /api/v1/tickets` 的 `status`/`keyword`/`page`/`size` 动态筛选与 `PageResult<T>` 分页，随后推进 `/api/v1/devices`、联合索引 `EXPLAIN`、Controller 瘦身与 OpenAPI/SLF4J。

[技能清单](/learning/checklists/) · [第 1–17 周学习计划](/learning/schedule/) · [11 月 28 日接口路径收口与列表三角色隔离](/posts/ops-ticket-20261128/) · [项目文档](/learning/project-docs/) · [连续阅读版](/learning/downloads/reader.html) · [下载自学包](/learning/downloads/java-internship-self-study.zip)
