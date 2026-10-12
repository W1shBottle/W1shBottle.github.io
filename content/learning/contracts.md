{
  "title": "设备工单的数据与接口约定",
  "description": "统一角色、工单状态、六张数据表、请求字段、响应与错误码。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 100,
  "group": "tools",
  "draft": false
}
这份约定在第4周以后逐步使用，避免不同阶段对字段和业务含义理解不同。第一周只实现Ticket编号与标题，不需要预先建全部表或接口。它描述计划中的最终约定，具体SQL和代码随课程完成。

## 角色与状态

角色固定为REPORTER、ENGINEER、ADMIN。REPORTER只能查看和操作自己的工单；ENGINEER只能查看和处理分配给自己的工单；ADMIN可看全部并维护设备、对待派单工单派单。演示系统不提供公开注册，不让前端自行指定当前身份。

```text
OPEN → IN_PROGRESS → RESOLVED → CLOSED
          ↑              │
          └── reject ────┘
```

assign由管理员触发；resolve由当前工程师触发；accept/reject由原报修人触发。关闭后第一版不再变更。所有状态变更都检查当前状态和权限，最终版本带期望版本以识别并发冲突。评论本身不变更工单状态。

## 字段约定

Java属性用驼峰，例如reporterId；SQL用下划线，例如reporter_id。编号用Java long/Long、MySQL BIGINT。还没分配的处理人用NULL，不用0冒充用户。标题trim后长度1—50；本课程Java长度按String.length计算，验收长短边界使用英文字母。

| 表 | 关键字段 | 约束与含义 |
| --- | --- | --- |
| app_user | id, username, password_hash, role, enabled | username唯一；role为三个角色之一；停用保留历史记录 |
| device | id, code, name, location, enabled | code唯一；停用后不再接受新报修；已有历史保留 |
| ticket | id, title, description, device_id, reporter_id, assignee_id, status, version, created_at, updated_at | device/reporter存在；assignee可空；创建状态OPEN、version=0 |
| ticket_comment | id, ticket_id, author_id, content, created_at | 有访问权限者评论；内容非空；身份取自会话 |
| ticket_action_log | id, ticket_id, actor_id, action, from_status, to_status, note, created_at | 记录关键状态操作；与状态更新同事务；创建的from_status可空 |
| ticket_resolution | id, ticket_id, engineer_id, content, created_at | 每次提交处理结果保存一条；验收退回后可以再次提交 |

先在`ops_ticket_dev`练习，自动测试使用独立的`ops_ticket_test`；恢复演练另建`ops_ticket_restore`。建表脚本分版本保存在项目中，不让自动测试连接自己仍需保留的开发数据。

## 全课程的基础样本

| 对象 | 编号与内容 |
| --- | --- |
| 用户 | 1 reporter_a、2 engineer_a、3 admin_a、4 reporter_b |
| 设备 | 1 PJ-001投影仪、2 AC-001空调、3 PR-001打印机 |
| 工单101 | device_id=1，reporter_id=1，assignee_id=NULL，status=OPEN，version=0 |
| 工单102 | device_id=2，reporter_id=1，assignee_id=2，status=IN_PROGRESS，version=0 |
| 工单103 | device_id=1，reporter_id=4，assignee_id=NULL，status=OPEN，version=0 |

这个样本应查询到3张工单：OPEN有2张，IN_PROGRESS有1张；设备1有2张、设备2有1张、设备3有0张。做聚合时是否显示0条设备，是INNER JOIN与LEFT JOIN练习的区别。

做权限实验可额外创建engineer_b，验证工程师之间不能互相操作。建表阶段的password_hash可以用明确的非登录占位值；第12周必须由PasswordEncoder生成演示密码的哈希后再验证登录。占位值不是可用密码，更不是加密实现。

各实验改变状态后，使用新的测试记录或专用测试库重新准备初始条件。不要依赖在开发库全表删除来重置实验。

## 请求与响应

| 请求 | 主要输入 | 成功结果 | 主要规则 |
| --- | --- | --- | --- |
| POST /api/tickets | title, description, deviceId | 201，返回工单id与初始状态 | reporter取当前用户；设备必须启用 |
| GET /api/tickets | page, size, status等 | 200，返回items与total | page从1起，size限制1—100；先限制可见范围再筛选 |
| GET /api/tickets/{id} | 路径编号 | 200，返回详情，含actionLogs与resolutions | 先检查资源是否存在及当前用户的访问范围 |
| POST /api/tickets/{id}/assign | engineerId, expectedVersion | 200，返回新状态与版本 | 管理员、OPEN、工程师存在且启用 |
| POST /api/tickets/{id}/resolve | content, expectedVersion | 200，返回新状态与版本 | 当前工程师、IN_PROGRESS、处理说明非空 |
| POST /api/tickets/{id}/accept | expectedVersion | 200，返回CLOSED与版本 | 原报修人、RESOLVED |
| POST /api/tickets/{id}/reject | reason, expectedVersion | 200，返回IN_PROGRESS与版本 | 原报修人、RESOLVED、退回原因非空 |
| POST /api/tickets/{id}/comments | content | 201，返回评论id | 有工单访问权、内容非空 |
| GET /api/tickets/{id}/comments | page, size | 200，分页返回评论 | 先检查工单访问权，再按时间和id正序读取 |
| GET /api/devices | 可选启用状态 | 200，设备列表 | 已登录用户可读；创建报修时只选择启用设备 |
| POST /api/devices | code, name, location | 201，返回设备id | 仅管理员；编码唯一、名称非空 |
| PATCH /api/devices/{id}/enabled | enabled | 200，返回设备状态 | 仅管理员；停用保留历史工单 |

时间显示采用明确时区，列表固定排序，例如created_at DESC, id DESC。创建时间相同也能保持相对顺序；分页时插入新数据仍可能使后续页移动，第一版接受这一限制并记录。

Web版创建请求的description去掉首尾空白后长度为1—2000；评论content为1—1000。标题、描述和评论的请求校验与页面提示保持一致。详情中的日志和处理记录同样受工单访问权限保护。

状态码约定：400输入格式或校验错误；401身份未认证；403无权限或CSRF校验失败；404资源不存在；409当前状态或版本冲突。访问别人工单在本教学项目按403处理；若选择统一404以隐藏资源存在性，须保持一致并调整对应测试。

CSRF校验可能先于认证失败处理：未登录GET受保护API通常401；缺失CSRF的POST可能先403。错误响应不能只靠状态码猜原因，应读取错误体和服务端日志。

## 认证方案

第12周使用Spring Security框架formLogin、Session Cookie和框架密码编码。静态页面与API同源，避免一开始引入跨域复杂度。登录请求使用表单字段username/password，携带有效CSRF token；登录成功由框架保存会话认证。登录和退出后按课程重新取得token。

API认证失败与禁止访问返回JSON错误；页面可以自行跳转登录页。后端不接受请求体传入的actorId或reporterId作为当前用户身份。前端隐藏按钮只能改善界面，不能替代服务端授权。

## 并发与事务

派单必须把“判断仍为OPEN且版本相同”和“写入新处理人”放进一次条件UPDATE；检查影响行数为1后写操作记录。受影响行为0表示条件已变化，应返回冲突，不把它当作正常完成。

同一事务覆盖工单更新与操作记录，提交结果才能一起可见。需要持久化处理说明时，处理记录同样参与事务。单独在Java里先查状态再无条件更新，会在并发时留下覆盖窗口；仅在一个JVM里synchronized也无法保护多个进程的数据库写入。

核心SQL与实现练习在各周参考答案中给出，所有实验只针对自己创建的练习数据。
