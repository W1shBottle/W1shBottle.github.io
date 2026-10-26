{
  "title": "设备工单的数据与接口约定",
  "description": "现有三表与计划中的动作日志、最小接口、权限和只读AI建议边界。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 100,
  "group": "tools",
  "draft": false,
  "lastmod": "2026-10-26T00:00:00+08:00"
}

2026-10-26 更新。这里区分当前数据与未来设计；项目内 `docs/design.md` 与实际 SQL 是实现依据。本文的接口均为计划，当前控制台尚无 HTTP、登录或 AI。保留 `cn.wishbottle.opsticket` 包名，不因新路线改项目主题。

## 当前样本和状态

`ops_ticket_dev` 已有 `device`、`app_user`、`ticket`；建表依据项目 `sql/01_schema.sql`。用户/设备实际编号为1至4、1至3：reporter_a=1、engineer_a=2、admin_a=3、reporter_b=4；投影仪=1且已停用，空调=2，打印机=3。学习记录确认工单1“空调不制冷”已派给2，状态IN_PROGRESS。之后的插入和查询以实际 SELECT 为准，不能假定打印机工单一定是2或已插入。

旧教材中的工单101/102/103是另设的教学样本，**不是当前库的现状**。需要时在隔离测试库创建，不覆盖开发数据来凑教材输出；自增编号允许有空洞。

## 第一版的角色与流程

```text
报修人创建 OPEN → 管理员派单 IN_PROGRESS → 指定工程师解决 RESOLVED → 原报修人验收 CLOSED
```

REPORTER看自己的工单；ENGINEER看分给自己的工单；ADMIN看全部。创建身份来自会话；不能由请求自报actorId或reporterId。派单必须目标用户存在、启用且为ENGINEER，设备须在创建时启用。FK只保证存在，CHECK只保证定义的行内约束，不自动实现上述权限与业务规则。

首版不做退回、评论、附件、任意状态设置、复杂设备后台或公开注册。三类演示账号和设备通过明确的初始化流程准备；密码占位 `NOT_A_LOGIN_HASH` 不可登录，登录阶段用Spring Security PasswordEncoder生成哈希。

## 表与字段

| 表/记录 | 当前或计划 | 用途 |
| --- | --- | --- |
| app_user | 已有SQL | id、username、password_hash、role、enabled |
| device | 已有SQL | id、code、name、location、enabled；停用保留历史 |
| ticket | 已有SQL | id、title、description、device_id、reporter_id、assignee_id、status、version、created_at、updated_at |
| ticket_action_log | A1计划新增 | 工单状态动作、操作者、前后状态、note、时间；resolve的处理说明写note，与状态同事务 |
| 创建请求去重信息 | A2在ticket_action_log补充 | CREATE动作使用request_key、request_hash，按(actor_id, action, request_key)唯一；保存对应ticket_id；非创建动作不要求request_key；当前尚无此实现 |
| ticket_comment / ticket_resolution | 延后 | 首版不必为评论或多轮处理新增表；已有教材案例仅供扩展参考 |

编号Java用long/Long、数据库BIGINT。数据库新增ID由AUTO_INCREMENT产生，不照搬文件仓库的maxId+1；创建命令与已持久化对象可分开建模，得到真实ID后再构造对象。不为了实现旧 `void add(Ticket)` 签名让数据库插入虚假编号；到接库时有意识地调整契约。

待派单处理人是SQL NULL，对应Java Long null，不是0。数据库目前允许description默认空字符串；Web创建要求trim后1—2000长度，这是未来应用规则，要与现有演示数据/迁移明确区分。标题沿用trim后1—50，Java当前按String.length计；补充字符/emoji与数据库字符长度的差异在Web校验任务中统一约定并测边界，不宣称天然一致。

开发库ops_ticket_dev，测试用独立ops_ticket_test，恢复演练用新库；测试账号不应写开发库。数据和脚本保留来源，DDL迁移不能当普通事务回滚演示。

## A 阶段最小接口（待实现）

| 请求 | 输入与成功结果 | 核心规则 |
| --- | --- | --- |
| POST /api/tickets | title、description、deviceId；A2加入requestKey；首次201返回ticketId；同键同内容重试200返回原ticketId，最新状态/版本从GET详情取得 | 当前报修人；启用设备；同一人的同键同内容返回原ticketId，可查详情取最新状态；不同内容409 |
| GET /api/tickets | status、keyword、deviceId、page、size；items/total | 先限制当前用户可见范围，再一致筛选与计数；稳定排序 |
| GET /api/tickets/{id} | 详情和必要动作记录 | 角色与归属限制同列表 |
| POST /api/tickets/{id}/assign | engineerId、expectedVersion | ADMIN、OPEN、启用ENGINEER；成功IN_PROGRESS |
| POST /api/tickets/{id}/resolve | content、expectedVersion | 当前处理人、IN_PROGRESS；非空处理说明；成功RESOLVED |
| POST /api/tickets/{id}/accept | expectedVersion | 原报修人、RESOLVED；成功CLOSED |
| GET /api/devices | 可报修设备列表 | 已登录；创建时服务端再次检查是否启用 |
| GET /api/users/engineers | 启用工程师的最小id/name列表 | 仅管理员派单需要；不返回密码或整张用户表 |

列表page从1开始，size默认10、限制1—100；排序created_at DESC,id DESC。第一版采用普通分页，记录并发新增导致后页移动的限制。时间统一记录本地业务时区Asia/Shanghai；LocalDateTime本身无时区，部署须保持约定。

状态码：校验400，未认证401，禁止访问403，资源不存在404，状态/旧版本/请求键冲突409，意外故障500。缺CSRF的写请求可能先403，权限测试应带有效认证和CSRF再验证越权，不能把所有403都当授权正确。

## A2 工程规则

Session Cookie + Spring Security，同源最小页面；formLogin使用username/password表单及有效CSRF token，不先引入JWT。使用框架密码编码，不自己写加密；页面隐藏按钮不替代授权。

状态变化使用带id、预期状态、版本和适当归属条件的UPDATE，检查影响行数；成功后同事务写动作记录。任何日志写失败都须回滚状态/版本。0行不是成功，不能继续插成功日志。创建去重在ticket_action_log用(actor_id, action, request_key)唯一约束和request_hash；创建工单与CREATE日志同事务。同键同内容返回原ticketId，不同内容409；唯一冲突后按事务失败处理并在正确事务边界重读。派单/解决/验收不建通用幂等框架，重复或旧版本返回409且不追加日志。确切迁移和重读实现到A2任务学习。

外部模型调用不在业务数据库事务里执行，不拿着锁等待模型。日志带requestId与错误原因，避免记录密码、Cookie、API key和完整敏感描述。

## B 阶段 AI 契约（待实现）

`POST /api/tickets/{id}/ai-assistance` 由路径id定位当前用户有权访问的已有工单，服务端读取description和必要设备信息，不接收客户端自报身份或整张工单，输出受约束的 `summary`、`category`、`missingInformation`；category限定DISPLAY/PRINTING/HVAC/OTHER/UNKNOWN。输入/输出限长；仅整理描述和提出补充信息，不生成维修操作指令，不调用派单/解决/验收写接口。

Java先按已有详情规则校验当前用户对工单的访问权，再读取真实description；负责上下文限长、结构解析和枚举/字段验证。模型给出正确JSON也可能语义错误，必须由用户审阅；人工后续操作仍走原业务校验。超时、限流、无效JSON、缺字段时返回可理解的建议不可用提示，保留原输入，人工业务仍可继续。模型功能可用配置关闭。

待配置：提供方、API端点、模型名、环境变量key、单次超时、最大输入/输出与调用预算、费用币种/价格依据。未填之前只做本地契约和故障测试，标记真实模型未验证。

## 可选 RAG / Agent 边界

RAG资料导入须有来源、版本和访问范围；检索结果给可定位引用，无依据时明确不足。工具Agent第一步只读：允许的查询函数复用Service授权，不暴露任意SQL执行，身份不取模型参数；限制调用数量、步骤、总时长和上下文，异常有明确停止路径。

以后若增加写工具，先展示动作参数和必要确认；执行时再次校验权限、参数、状态、版本和重复请求。模型输出、检索文档和聊天内容均不是授权凭证。第一版不要求RAG、Agent框架或多Agent。

## 首版建议的使用边界

B首版只展示/复制参考，不提供直接回写按钮。现有rename只在控制台，不能视为已有HTTP修改接口；以后若加入人工采纳改标题，须单独定义报修人归属、允许状态、expectedVersion和日志同事务的HTTP接口，再实施并验收。
