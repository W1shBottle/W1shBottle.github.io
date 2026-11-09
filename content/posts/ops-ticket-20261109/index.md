---
title: "设备运维工单开发 — 15 数据库创建 POST 与自增主键"
description: "从 CreateDatabaseTicketRequest、DatabaseTicketCommandService 到 POST /api/db/tickets，验证 @Options 自增主键、回查 Ticket、201 响应，以及外键和标题约束错误如何转成 400。"
date: 2026-11-09T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Spring Boot", "MyBatis", "MySQL", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 15
chapter_title: "数据库创建 POST 与自增主键"
---

> 接续 [上一篇 多列对象映射与只读数据库分层](/posts/ops-ticket-20261108/)。上一篇已经把只读查询分层和写入组件准备好；今天把 `POST /api/db/tickets` 接通，验证 `@Options` 自增主键、回查 `Ticket`、201 JSON，以及外键/标题约束错误如何变成 400。数据库派单 UPDATE 还没做，留到明天。

## 1 今天的目标

昨天结束时，数据库写入只到 `DatabaseTicketRepository.create`：

```text
TicketInsert
→ ticketMapper.insertTicket
→ 影响行数
→ insert.getId()
→ findById
```

但它没有 HTTP 入口，也没有命令 Service 和请求 DTO。今天要补的是：

```text
POST /api/db/tickets
→ CreateDatabaseTicketRequest
→ DatabaseTicketCommandService
→ TicketWriteRepository.create
→ INSERT
→ 自增主键
→ 回查 Ticket
→ 201 JSON
```

## 2 请求 DTO：三个字段缺一不可

文件版创建只提交 `title`，数据库版还需要 `deviceId` 和 `reporterId`：

```java
public class CreateDatabaseTicketRequest {

    private String title;
    private long deviceId;
    private long reporterId;

    // getter / setter
}
```

原因在表结构：

```sql
CREATE TABLE ticket (
    ...
    device_id BIGINT NOT NULL,
    reporter_id BIGINT NOT NULL,
    ...
    CONSTRAINT fk_ticket_device
        FOREIGN KEY (device_id) REFERENCES device(id),
    CONSTRAINT fk_ticket_reporter
        FOREIGN KEY (reporter_id) REFERENCES app_user(id)
);
```

`device_id`、`reporter_id` 都是 `NOT NULL` 外键，创建时必须提供。

请求 JSON：

```json
{ "title": "打印机缺纸", "deviceId": 3, "reporterId": 4 }
```

Jackson 通过 setter 填入字段。`long` 缺字段时是 `0`，正好用 `<= 0` 判断不合法。

## 3 命令服务：校验后委托

```java
@Service
public class DatabaseTicketCommandService {

    private final TicketWriteRepository ticketWriteRepository;

    public DatabaseTicketCommandService(
            TicketWriteRepository ticketWriteRepository
    ) {
        this.ticketWriteRepository = ticketWriteRepository;
    }

    public Ticket create(String title, long deviceId, long reporterId) {
        if (title == null) {
            throw new IllegalArgumentException("工单标题不能为null");
        }

        String trimmed = title.trim();
        if (trimmed.isEmpty()) {
            throw new IllegalArgumentException("工单标题不能为空");
        }
        if (trimmed.length() > 50) {
            throw new IllegalArgumentException("工单标题不能超过50");
        }

        if (deviceId <= 0) {
            throw new IllegalArgumentException("设备编号必须大于0");
        }
        if (reporterId <= 0) {
            throw new IllegalArgumentException("报障人编号必须大于0");
        }

        return ticketWriteRepository.create(trimmed, deviceId, reporterId);
    }
}
```

- 命令服务不写 SQL，只负责校验和委托；
- `trimmed` 和数据库 `CHECK (CHAR_LENGTH(TRIM(title)) BETWEEN 1 AND 50)` 保持一致；
- 校验失败抛 `IllegalArgumentException`，Controller 转 400。

## 4 Controller：POST 与 201

```java
@PostMapping({"/api/db/tickets", "/api/db/tickets/"})
@ResponseStatus(HttpStatus.CREATED)
public Ticket create(@RequestBody CreateDatabaseTicketRequest request) {
    try {
        return databaseTicketCommandService.create(
                request.getTitle(),
                request.getDeviceId(),
                request.getReporterId()
        );
    } catch (IllegalArgumentException e) {
        throw new ResponseStatusException(
                HttpStatus.BAD_REQUEST,
                e.getMessage(),
                e
        );
    }
}
```

- `@RequestBody`：JSON → DTO；
- `@ResponseStatus(HttpStatus.CREATED)`：成功返回 201，不是 200；
- `IllegalArgumentException` → 400；
- 返回领域 `Ticket`，Jackson 读取 getter 生成 JSON。

## 5 INSERT 的两个输出

`DatabaseTicketRepository.create` 的核心：

```java
int affectedRows = ticketMapper.insertTicket(insert);

if (affectedRows != 1) {
    throw new IllegalStateException(
            "创建工单失败，影响行数：" + affectedRows
    );
}

if (insert.getId() == null) {
    throw new IllegalStateException(
            "创建工单成功，但没有取得自增主键"
    );
}

return findById(insert.getId())
        .orElseThrow(() -> new IllegalStateException(
                "创建后读取工单失败：" + insert.getId()
        ));
```

这里有两个输出，必须分清：

| 输出 | 来源 | 含义 |
| --- | --- | --- |
| 影响行数 `int` | `insertTicket` 返回值 | 插入了 1 行 |
| 自增主键 `Long` | `@Options` 回填 `insert.id` | 数据库生成的 id |

`@Options`：

```java
@Options(
        useGeneratedKeys = true,
        keyProperty = "id",
        keyColumn = "id"
)
int insertTicket(TicketInsert ticketInsert);
```

- `useGeneratedKeys = true`：让 JDBC 返回生成的主键；
- `keyProperty = "id"`：回填到 `TicketInsert.id`；
- `keyColumn = "id"`：数据库列名。

`TicketInsert.id` 必须是 `Long`，不能是 `long`，因为要用 `null` 表示「还没回填」。

## 6 回查 Ticket

```java
return findById(insert.getId())
        .orElseThrow(() -> new IllegalStateException(
                "创建后读取工单失败：" + insert.getId()
        ));
```

为什么不直接 `new Ticket(id, title)`？因为数据库还有默认值：

- `status = 'OPEN'`；
- `version = 0`；
- `created_at` / `updated_at`；
- `assignee_id = NULL`。

回查拿到的是数据库里的真实状态，同时验证这行确实能读出来。

`findById` 返回 `Optional<Ticket>`：

- 有值 → 返回；
- 空 → 抛 `IllegalStateException`。

`orElseThrow` 里的 lambda 是延迟创建异常，成功时不会 `new`。

## 7 实际请求结果

我写完后自己发了一次 POST，返回：

```json
{
  "id": 9,
  "title": "打印机缺纸",
  "assigneeId": null,
  "status": "OPEN"
}
```

一开始我看到 `id=9` 也疑惑：数据库里明明只有 1 和 3，为什么不是 4？

原因是 `AUTO_INCREMENT` 不是「行数 + 1」，而是只增不减的计数器：

1. 失败的 INSERT 也会消耗编号：InnoDB 在检查外键/CHECK 之前就分配了 id，失败后号码不还；
2. 删除行不会回退计数器；
3. 多次尝试或整份 `.http` 运行也会消耗。

所以 4 和 9 之间缺的 5、6、7、8 是「分配了但没落库」的号，不是数据丢失。

## 8 约束错误：数据库才知道的错误

命令服务能拦住：

- 空标题 / 超长标题；
- `deviceId <= 0` / `reporterId <= 0`。

但外键和 CHECK 只有数据库知道：

- 设备 999 不存在 → `fk_ticket_device`；
- 报障人 999 不存在 → `fk_ticket_reporter`；
- 标题违反 `ck_ticket_title`。

Spring 把 SQL 约束错误翻译成 `DataIntegrityViolationException`，在 `GlobalExceptionHandler` 里统一转 400：

```java
@ExceptionHandler(DataIntegrityViolationException.class)
@ResponseStatus(HttpStatus.BAD_REQUEST)
public ErrorResponse handleDataIntegrityViolation() {
    return new ErrorResponse(
            "创建失败：设备或报障人不存在，或标题不符合规则"
    );
}
```

这里不把底层 SQL 错误直接暴露给客户端，只给一句可读的提示。

## 9 验证矩阵

| 测试 | 结果 |
| --- | --- |
| 合法 POST | 201，`id=4`（助手验证） |
| GET 列表 | 200，包含新工单 |
| `deviceId=999` | 400，通用约束提示 |
| `reporterId=999` | 400，通用约束提示 |
| 空标题 | 400，`工单标题不能为空` |
| 缺 `title` | 400，`工单标题不能为null` |
| 51 字标题 | 400，`工单标题不能超过50` |
| `deviceId=0` | 400，`设备编号必须大于0` |
| 数据库行 | `id=4, device_id=3, reporter_id=4, status=OPEN, version=0` |

注意：这轮完整矩阵是助手运行验证；我自己只发了 `id=9` 那一次 POST。两者不能混为一谈。

## 10 自增计数器重置

为了让我下一次 POST 从 4 开始，我让助手删掉了测试行（id=4、9）并重置自增：

```sql
ALTER TABLE ticket AUTO_INCREMENT = 4;
```

有一个容易误判的点：

- `information_schema.TABLES.AUTO_INCREMENT` 和 `SHOW TABLE STATUS` 可能显示缓存值 10；
- `SHOW CREATE TABLE ticket` 才是实际表定义，显示 `AUTO_INCREMENT=4`。

临时表实验也确认了：设 10 → 插入得 10；删除后 `ALTER` 到 4 → 再插入得 4。

## 11 本次边界与下次接续

今天完成的是**数据库创建 POST**。还没做：

- 数据库派单 / 解决 / 验收（UPDATE 状态流）；
- 正式 `/api/tickets` 从文件仓库切到数据库仓库；
- Web 自动测试、事务边界、权限、并发和幂等。

下一次从数据库派单开始：

```text
POST /api/db/tickets/{id}/assign
→ AssignTicketRequest
→ DatabaseTicketCommandService.assign
→ TicketMapper.assignTicket
→ UPDATE ... WHERE id = ? AND status = 'OPEN'
→ 影响行数 0 / 1
→ 404 / 409
```

继续对照 [学习栏目](https://wishbottle.cn/learning/)、[项目设计](https://wishbottle.cn/learning/project-design/) 和 [运行验收](https://wishbottle.cn/learning/project-verification/) 阅读。
