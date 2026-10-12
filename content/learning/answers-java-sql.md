{
  "title": "第 1 至 6 周自测答案与关键示例",
  "description": "第1—6周自测解释及Java、文件读写、建表和JDBC局部示例。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 110,
  "group": "answers",
  "draft": false
}
配合[第 1 至 6 周课程](/learning/java-sql/)使用。先保留自己的尝试、报错和预测结果，再读对应小节。Java 代码块多数是局部片段，不能直接作为独立文件运行；需要放进相应类，并由你补全 import、字段、getter、调用和边界处理。全部示例使用虚构数据。

每周过关不以“复制后运行成功”为标准：合上答案，改变一个输入，先预测结果，再独立解释或修改代码。环境和第三方依赖首次下载通常需要网络；这套材料不要求订阅任何 AI 服务。

## 第 1 周答案

**题 1：为什么构造器也要校验？** 创建对象也是输入数据的入口。如果构造器直接保存空标题，非法对象在第一次调用 `rename` 前已经存在。构造和修改应共用校验规则，保证任何正常完成的创建或修改都留下合法状态。

**题 2：两个变量指向同一对象会怎样？** `Ticket b = a` 复制引用，没有复制对象。通过 `b.rename("新标题")` 修改同一个对象后，`a.getTitle()` 也返回“新标题”。只有再次 `new Ticket(...)` 才创建另一张对象。

**题 3：为什么不用 static 字段？** `static` 字段属于类，所有实例共享。如果标题是 static，改第一张可能让第二张读取相同的新标题。每张工单自己的数据必须是实例字段。`main` 是 static，是因为程序入口不需要先创建 Demo 对象。

关键校验可以这样写在 Ticket 类内部。这里的 `normalizeTitle` 是私有静态工具方法：它只处理参数，不访问任何一张工单的字段，因此与“把 title 字段变成 static”不同。

```java
private long id;
private String title;

public Ticket(long id, String title) {
    if (id <= 0) {
        throw new IllegalArgumentException("编号必须大于0");
    }
    String validTitle = normalizeTitle(title);
    this.id = id;
    this.title = validTitle;
}

private static String normalizeTitle(String value) {
    if (value == null) {
        throw new IllegalArgumentException("标题不能为空");
    }
    String normalized = value.trim();
    if (normalized.isEmpty() || normalized.length() > 50) {
        throw new IllegalArgumentException("标题长度必须为1至50");
    }
    return normalized;
}

public void rename(String newTitle) {
    this.title = normalizeTitle(newTitle);
}
```

先算赋值右边：校验抛异常时，赋值还没有发生，旧标题保留。getter 由你补上。不要先 `this.title = newTitle` 再判断，否则异常发生后对象已经被非法输入污染。

下面放在 Demo 的 main 中检查失败修改。每个失败用例单独捕获异常，才能继续验证后面的用例。

```java
Ticket ticket = new Ticket(1L, "  投影仪无法开机  ");
try {
    ticket.rename("   ");
    throw new AssertionError("这里本应拒绝空标题");
} catch (IllegalArgumentException expected) {
    System.out.println(expected.getMessage());
}
System.out.println(ticket.getTitle()); // 投影仪无法开机
```

常见错误：`void Ticket(...)` 是普通方法，不是构造器；`title = title` 只给参数自身赋值；先 `trim` 再判断 null 会产生 NullPointerException；只判断 `isEmpty()` 无法排除全空格。检查 50 与 51 的边界，条件应为 `> 50`，不是 `>= 50`。

数组复习题：先约定空数组抛异常，再把第一个元素作为当前最大值，循环比较剩下的元素；不要把最大值初始设为 0，否则 `[-5,-2,-8]` 会错误返回 0。时间复杂度 O(n)，额外空间 O(1)。

## 第 2 周答案

**题 1：重复 Map.put 会怎样？** 相同键的新值会替换旧值。创建时应先检查 `containsKey(id)` 并拒绝重复，或使用 `putIfAbsent` 检查返回值。本阶段是单线程，先检查再放入足够；并发时不能直接推广这个结论。

**题 2：为什么不从 1 开始？** 文件里已经有旧编号，重新从 1 开始可能覆盖或与旧记录冲突。读取全部记录后，空集合用 1，否则用现有最大 id 加 1。这仅用于单进程练习；数据库阶段改成 AUTO_INCREMENT，后期并发不能用 `MAX(id)+1`。

**题 3：明明保存却找不到，查什么？** 先打印保存和读取的绝对路径，判断工作目录是否不同；再检查写入是否真正完成、异常是否被吞掉，且保存成功提示是否放在实际写入成功之后。`src` 是代码目录，不自动等于运行的工作目录。

状态与派单的最小实现。字段名和方法名放在 Ticket 中，getter 自行补全。

```java
public enum TicketStatus {
    OPEN, IN_PROGRESS, RESOLVED, CLOSED
}
```

```java
private TicketStatus status = TicketStatus.OPEN;
private Long assigneeId; // null表示还没有处理人

public void assign(long engineerId) {
    if (engineerId <= 0) {
        throw new IllegalArgumentException("工程师编号必须大于0");
    }
    if (status != TicketStatus.OPEN) {
        throw new IllegalStateException("只有待派单工单可以派单");
    }
    assigneeId = engineerId;
    status = TicketStatus.IN_PROGRESS;
}
```

这里还没有用户库，所以只能校验编号正数，不能证明这个编号真的是启用的工程师。进入 Service 和数据库后增加相应检查。不要将 `assign` 当作任意修改处理人的 setter。

普通循环筛选示例，`tickets` 是已有 List。返回新列表，不删除原列表里的其他状态。

```java
List<Ticket> openTickets = new ArrayList<>();
for (Ticket ticket : tickets) {
    if (ticket.getStatus() == TicketStatus.OPEN) {
        openTickets.add(ticket);
    }
}
```

文件先只练一张，再写循环。以下代码需要 `java.nio.file.*`、`java.nio.charset.StandardCharsets`、`java.io.*`、`java.util.Properties`；放入声明了 `throws IOException` 的方法中，或由调用处处理 IOException。

```java
Path path = Paths.get("data", "tickets.properties");
Files.createDirectories(path.toAbsolutePath().getParent());
System.out.println(path.toAbsolutePath());

Properties data = new Properties();
data.setProperty("count", "1");
data.setProperty("ticket.0.id", Long.toString(ticket.getId()));
data.setProperty("ticket.0.title", ticket.getTitle());
data.setProperty("ticket.0.status", ticket.getStatus().name());
data.setProperty("ticket.0.assigneeId",
    ticket.getAssigneeId() == null ? "" : ticket.getAssigneeId().toString());

try (Writer writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
    data.store(writer, "ops-ticket training data");
}
System.out.println("保存成功");
```

读取先保存到临时 Properties 和临时集合。只有全部通过校验，才替换程序原来的集合。不要读到一半报错，却把旧集合清空了。

```java
Properties loaded = new Properties();
try (Reader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
    loaded.load(reader);
}
String rawId = loaded.getProperty("ticket.0.id");
long id = Long.parseLong(rawId);
String title = loaded.getProperty("ticket.0.title");
TicketStatus status = TicketStatus.valueOf(
    loaded.getProperty("ticket.0.status"));
String rawAssignee = loaded.getProperty("ticket.0.assigneeId");
if (rawAssignee == null) {
    throw new IllegalArgumentException("第0条缺少assigneeId字段");
}
Long assignee = rawAssignee.isEmpty() ? null : Long.valueOf(rawAssignee);
```

接着把这些值交给专门的恢复入口，不用“创建后反复派单”来恢复旧状态。一个可对照的核心片段：

```java
public static Ticket restore(long id, String title,
        TicketStatus status, Long assigneeId) {
    if (status == null) {
        throw new IllegalArgumentException("状态不能为空");
    }
    if (status == TicketStatus.OPEN && assigneeId != null) {
        throw new IllegalArgumentException("OPEN工单不能已有处理人");
    }
    if (status != TicketStatus.OPEN
            && (assigneeId == null || assigneeId <= 0)) {
        throw new IllegalArgumentException("非OPEN工单必须有正数处理人");
    }
    Ticket ticket = new Ticket(id, title);
    ticket.status = status;
    ticket.assigneeId = assigneeId;
    return ticket;
}
```

`restore` 仅用于存储恢复，不开放为用户操作入口。第 3 周拆包后继续收紧调用位置。新增字段时记得同时更新保存与恢复逻辑。

独立扩展：读取 `count`，校验为非负整数，用 `for (int i = 0; i < count; i++)` 生成前缀 `"ticket." + i + "."`。检查每个必填键存在、重复编号、非法数字和未知枚举。缺文件可以返回空集合；已有文件损坏必须报错，不可伪装成首次启动。写入会覆盖指定文件，本阶段只用自己的练习数据，并在试坏数据前复制备份；原子替换与并发写入不作为本周要求。

常见错误：字符串比较用 `==`；在 foreach 中直接删除原集合；读状态用中文“待派单”却保存英文 `OPEN`；漏存处理人；捕获所有异常后返回空列表。Properties 的 Reader/Writer 方式可明确使用 UTF-8，别混用其默认 ISO-8859-1 的字节流方法。[Properties 官方 API](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Properties.html)

## 第 3 周答案

**题 1：为什么不在业务方法里不断 new 文件仓库？** 这样业务被具体存储绑住，每次还可能重复加载或得到不同的内存状态。将 Repository 通过构造器传入，业务只调用约定接口，同一个对象的依赖清晰，也方便用内存实现做练习。

**题 2：换存储时什么变、什么不变？** 启动组装位置改实现，Repository 实现内部改变；标题规范、允许的状态迁移、用户看到的成功或失败含义应保留。若一个实现允许重复编号，另一个拒绝，就没有遵守统一约定。

**题 3：release 21 报错查什么？** 查看 `mvn -v` 输出里的 Java 版本与 Java home，并与 `java -version`、`javac -version`、IDEA Project SDK 及 Maven Runner JRE 比较。Maven 使用较旧 JDK 时，只把 pom 的 release 改为 21 无法让它编译 Java 21。

构造器传入依赖及改标题的关键代码：

```java
public class TicketService {
    private final TicketRepository repository;

    public TicketService(TicketRepository repository) {
        this.repository = java.util.Objects.requireNonNull(repository);
    }

    public void rename(long id, String title) {
        Ticket ticket = repository.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("工单不存在"));
        ticket.rename(title);
        repository.update(ticket);
    }
}
```

启动处 `new TicketService(new InMemoryTicketRepository())`。不要在 Service 中读键盘，也不要在 Repository 中决定哪些状态能派单。文件写入的 IOException 可以保留原因包装成存储失败异常，交互层显示失败；不能吞掉异常打印成功。内存版如果直接返回可变 Ticket，字段修改会提前反映在内存，这只是练习实现的限制；仍显式 update，后续用数据库事务处理多步修改的一致性。

最小 Maven pom 示例，文件位于项目根目录。它只承担 Java 编译，不包含 Spring 或测试框架；此时 `mvn package` 成功也不等于已验证业务行为。

```xml
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>ops-ticket</artifactId>
  <version>0.1.0</version>
  <properties>
    <maven.compiler.release>21</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.16.0</version>
      </plugin>
    </plugins>
  </build>
</project>
```

代码目录与包名对应：`src/main/java/com/example/opsticket/ConsoleApp.java` 的第一行是 `package com.example.opsticket;`。在项目根目录分别运行：

```powershell
mvn -v
mvn package
java -cp target/ops-ticket-0.1.0.jar com.example.opsticket.ConsoleApp
```

最后一条用于尚无外部运行依赖的第 3 周程序；第 6 周加 JDBC 后可先用 IDEA 带依赖运行，第 7 周用 Spring Boot 的打包方式。若项目有 Maven Wrapper，Windows 对应命令为 `./mvnw.cmd package`。首次构建会下载工具或插件，准备完整后 `mvn -o package` 才可能成功。[Maven 入门](https://maven.apache.org/guides/getting-started/maven-in-five-minutes.html)；[Compiler Plugin 版本与要求](https://maven.apache.org/plugins/maven-compiler-plugin/plugin-info.html)。

关键词筛选可先按原样匹配：校验关键词非 null，`trim` 后为空返回全部或报错，选一种并写进说明；对每张工单用 `getTitle().contains(keyword)`，加入新列表。两数之和的 Map 解法：遍历到 x 时先查 `target - x` 是否已出现，找到才返回两下标，然后再放入 x，避免同一个下标使用两次；`[3,3]`、目标 6 是必要边界。

常见错误：默认包里的类没有随目录加 package；`Optional.get()` 查不到会抛异常；仅新建接口但业务仍引用具体类；手改文件后程序还使用启动前的旧缓存；把文件写失败当作成功。Git 提交先看 diff，提交自己本次修改的源文件和配置，不提交 `target`、数据库密码或机器专属路径。

## 第 4 周答案

**题 1：为什么不用 = NULL？** NULL 表示缺失或未知值，与它用普通等号比较得不到“相等为真”。筛选缺失值用 `IS NULL`，有值用 `IS NOT NULL`。SQL NULL 不等于字符串 `'NULL'`，也不等于数字 0。

**题 2：改设备名为什么不用改工单编号？** 工单保存稳定的 device_id，关联时读取设备当前名称。同一设备改名仍是同一设备，id 不变。若未来有“保留报修当时名称”的业务需求，再专门设计快照字段。

**题 3：外键能否保证处理人是工程师？** 不能。外键仅保证编号引用的用户存在；角色和启用状态还需 Service 校验。用户 1 即使存在，也只是 REPORTER。

以下是三张表的参考结构。仅在自己的空练习库首次运行；重复执行 CREATE TABLE 已存在报错是正常提示，不要为了图省事删除整个数据库。把自己写的版本与它逐列对照。

```sql
CREATE DATABASE IF NOT EXISTS ops_ticket_dev
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE ops_ticket_dev;

CREATE TABLE app_user (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(16) NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT ck_user_role CHECK (role IN ('REPORTER','ENGINEER','ADMIN'))
) ENGINE=InnoDB;

CREATE TABLE device (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(64) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  location VARCHAR(200) NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE ticket (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(50) NOT NULL,
  description VARCHAR(2000) NOT NULL DEFAULT '',
  device_id BIGINT NOT NULL,
  reporter_id BIGINT NOT NULL,
  assignee_id BIGINT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_ticket_device FOREIGN KEY (device_id) REFERENCES device(id),
  CONSTRAINT fk_ticket_reporter FOREIGN KEY (reporter_id) REFERENCES app_user(id),
  CONSTRAINT fk_ticket_assignee FOREIGN KEY (assignee_id) REFERENCES app_user(id),
  CONSTRAINT ck_ticket_title CHECK (CHAR_LENGTH(TRIM(title)) BETWEEN 1 AND 50),
  CONSTRAINT ck_ticket_status CHECK (
    status IN ('OPEN','IN_PROGRESS','RESOLVED','CLOSED')),
  CONSTRAINT ck_ticket_assignment CHECK (
    (status = 'OPEN' AND assignee_id IS NULL) OR
    (status IN ('IN_PROGRESS','RESOLVED','CLOSED') AND assignee_id IS NOT NULL)),
  CONSTRAINT ck_ticket_version CHECK (version >= 0)
) ENGINE=InnoDB;
```

本结构使用 MySQL 8.0.16 及以上执行的 CHECK 约束；先执行 `SELECT VERSION()`，确认服务端为 MySQL 8.0.16 及以上或 8.4，再练习这些 SQL。客户端版本不能代表服务端版本。Java 的 `trim` 与 `String.length` 是应用层标题规则，数据库这条 CHECK 只做基本补充，不声称两种字符处理完全等价。

种子数据只插入一次。占位哈希不能用于第 12 周的正式登录演示；到时由 PasswordEncoder 生成并更新，且不返回到前端。

```sql
INSERT INTO app_user (id,username,password_hash,role,enabled) VALUES
 (1,'reporter_a','NOT_A_LOGIN_HASH','REPORTER',TRUE),
 (2,'engineer_a','NOT_A_LOGIN_HASH','ENGINEER',TRUE),
 (3,'admin_a','NOT_A_LOGIN_HASH','ADMIN',TRUE),
 (4,'reporter_b','NOT_A_LOGIN_HASH','REPORTER',TRUE);

INSERT INTO device (id,code,name,location,enabled) VALUES
 (1,'PJ-001','投影仪','A101',TRUE),
 (2,'AC-001','空调','A102',TRUE),
 (3,'PR-001','打印机','办公室',TRUE);

INSERT INTO ticket
 (id,title,description,device_id,reporter_id,assignee_id,status,version,created_at,updated_at)
VALUES
 (101,'投影仪无法开机','按电源键无响应',1,1,NULL,'OPEN',0,
  '2026-11-02 09:00:00','2026-11-02 09:00:00'),
 (102,'空调不制冷','运行十分钟仍无冷风',2,1,2,'IN_PROGRESS',0,
  '2026-11-02 10:00:00','2026-11-02 10:00:00'),
 (103,'投影画面闪烁','更换输入源仍闪烁',1,4,NULL,'OPEN',0,
  '2026-11-02 11:00:00','2026-11-02 11:00:00');
```

基础 SQL 参考。更新前的 SELECT 是帮助自己确认范围，不能替代事务或并发保护。

```sql
SELECT id,title FROM ticket WHERE status='OPEN' ORDER BY id;
SELECT id,title FROM ticket WHERE reporter_id=1 ORDER BY id;
SELECT id,title FROM ticket WHERE assignee_id IS NULL ORDER BY id;
SELECT id,title FROM ticket WHERE title LIKE '%投影%' ORDER BY id;

SELECT id,name,location FROM device WHERE id=1;
UPDATE device SET location='A103' WHERE id=1;
UPDATE device SET enabled=FALSE WHERE id=1;
SELECT id,device_id FROM ticket WHERE device_id=1;
```

验收后为了后续创建演示，重新启用设备 1：`UPDATE device SET enabled=TRUE WHERE id=1;`。练习删除另建一台没有工单引用的设备，并按确定的 id 删除；被工单引用的设备应保留记录并停用，外键不应改为级联删除工单。

常见错误：先插工单再插用户与设备；用中文顿号代替逗号；列名拼错；漏写 WHERE 修改了所有行；把布尔值、NULL 和字符串混用。`Duplicate entry` 先找冲突的唯一键；`Cannot add or update a child row` 先检查引用编号是否存在。数据库规范读 [MySQL 建表](https://dev.mysql.com/doc/refman/8.4/en/creating-tables.html)，遇到错误按错误信息查相应小节。

## 第 5 周答案

**题 1：INNER JOIN 处理人为什么丢行？** 未派单工单的 assignee_id 是 NULL，没有匹配用户。INNER JOIN 只保留匹配成功的行，因此 101、103 被过滤掉。LEFT JOIN 保留工单，处理人相关列为 NULL。

**题 2：为什么不 COUNT(*)？** 打印机没有工单，LEFT JOIN 仍保留一行，COUNT(*) 得到 1；COUNT(t.id) 只数非空工单编号，得到 0。统计前还要检查其他关联是否把工单复制成多行。

**题 3：失败后为什么显式回滚？** 某条 SQL 失败通常不代表前面所有成功语句都已回滚；仍可能保留在未提交事务里。业务要求全成功或全失败时，异常路径主动 ROLLBACK，正常路径才 COMMIT，并释放连接。不要在失败后继续提交部分结果。

关联列表：

```sql
SELECT t.id,t.title,d.name AS device_name,
       r.username AS reporter_name,
       a.username AS assignee_name,t.status
FROM ticket t
JOIN device d ON d.id=t.device_id
JOIN app_user r ON r.id=t.reporter_id
LEFT JOIN app_user a ON a.id=t.assignee_id
ORDER BY t.id;
```

初始结果依次为：101 投影仪 reporter_a 无处理人 OPEN；102 空调 reporter_a engineer_a IN_PROGRESS；103 投影仪 reporter_b 无处理人 OPEN。

```sql
SELECT status,COUNT(*) AS total
FROM ticket GROUP BY status ORDER BY status;

SELECT d.id,d.name,COUNT(t.id) AS ticket_count
FROM device d
LEFT JOIN ticket t ON t.device_id=d.id
GROUP BY d.id,d.name
ORDER BY d.id;

SELECT id,title FROM ticket
ORDER BY created_at DESC,id DESC LIMIT 2 OFFSET 0;
SELECT id,title FROM ticket
ORDER BY created_at DESC,id DESC LIMIT 2 OFFSET 2;
```

状态统计只输出实际出现的状态，当前没有 RESOLVED、CLOSED 行，不代表错误。设备统计为 1 投影仪 2，2 空调 1，3 打印机 0。如果只统计 OPEN 且仍要求保留零工单设备，把 `t.status='OPEN'` 放在 LEFT JOIN 的 ON 条件内，而不是 WHERE 中。

事务实验在同一数据库连接逐条执行，先记下设备 1 当前位置；ROLLBACK 后恢复该原值，不必与教材初始值完全相同。

```sql
SELECT location FROM device WHERE id=1;
START TRANSACTION;
UPDATE device SET location='临时位置' WHERE id=1;
SELECT location FROM device WHERE id=1; -- 当前连接看到临时位置
ROLLBACK;
SELECT location FROM device WHERE id=1; -- 恢复实验前的位置

START TRANSACTION;
UPDATE device SET location='新教室' WHERE id=1;
COMMIT;
```

第二连接使用普通自动提交模式做查询，不提前开启长事务，分别观察第一连接提交前后。否则第二连接可能因事务隔离下的旧快照继续看到旧结果。此处只验证最小提交/回滚，不一次混入所有隔离级别。

```sql
EXPLAIN SELECT id,title,created_at FROM ticket
WHERE reporter_id=1
ORDER BY created_at DESC,id DESC LIMIT 20;

CREATE INDEX idx_ticket_reporter_created_id
  ON ticket(reporter_id,created_at,id);

EXPLAIN SELECT id,title,created_at FROM ticket
WHERE reporter_id=1
ORDER BY created_at DESC,id DESC LIMIT 20;
```

索引只创建一次。EXPLAIN 的 `possible_keys` 是候选，`key` 是实际选择，`rows` 是估算；不能把估算行数当成真实测量耗时。小表无明显差异是可接受结果，第 18 周用相同数据规模与条件做更完整性能实验。

常见错误：两个 app_user 没有起别名；JOIN 漏掉 ON 导致结果数量异常；将处理人条件放 WHERE 意外排掉未派单行；`GROUP BY` 只分组一列却随意查询不确定的其他列；认为建好索引一定快；事务开始后忘记结束。参考 [JOIN](https://dev.mysql.com/doc/refman/8.4/en/join.html)及[事务语句](https://dev.mysql.com/doc/refman/8.4/en/commit.html)。

## 第 6 周答案

**题 1：为什么不拼标题到 SQL？** 标题可能包含单引号等字符，拼接会改变 SQL 结构或制造注入风险。固定语句使用占位符绑定值，让输入作为数据处理。参数绑定不替代标题业务校验，也不能自动保证权限。

**题 2：为什么退出后数据库数据还在？** 已提交数据由数据库持久化管理，不只存在 Java 进程内存中。Map 只在进程内；第 2 周能恢复是因为额外写了文件。不要把 `commit` 与 Java 对象仍在混为一谈。

**题 3：200 和 JSON 是否够了？** 还要核对响应内容、id、字段、当前身份与可见范围是否符合请求。200 只表达服务端报告成功，不自动证明业务实现正确；比如错误返回了另一张工单也仍可能带 200。

第 6 周独立 JDBC 练习在 pom 的 project 内添加 dependencies。示例固定 Connector/J 9.7.0，便于兼容既有 MySQL 8.0 与 8.4；进入 Spring Boot 后优先使用该 Boot BOM 管理的驱动，并核对数据库兼容范围。此版本为学习基线，不要求永远锁死。[9.7.0 官方发布说明](https://dev.mysql.com/doc/relnotes/connector-j/en/news-9-7-0.html)明确支持 MySQL Server 8.0 及以上；[官方 Maven 坐标](https://dev.mysql.com/doc/connector-j/en/connector-j-installing-maven.html)为下列 groupId 与 artifactId。

```xml
<dependencies>
  <dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
    <version>9.7.0</version>
  </dependency>
</dependencies>
```

在 IDEA 运行配置中设置 `OPS_DB_URL`、`OPS_DB_USERNAME`、`OPS_DB_PASSWORD`。URL 的基础形式为 `jdbc:mysql://localhost:3306/ops_ticket_dev`，主机、端口以你的实际环境为准。不要把真实密码写到源码或提交到 Git。连接设置不通时按具体认证与连接错误排查，不先复制一串关闭安全检查的参数。

最小连接与查询示例可放入 `JdbcTicketDemo.main`，声明 `throws SQLException` 用于观察首个实验错误。实际交互入口再增加清晰错误处理。`requiredEnv` 帮助在缺配置时立即指出变量名。

```java
private static String requiredEnv(String key) {
    String value = System.getenv(key);
    if (value == null || value.isBlank()) {
        throw new IllegalStateException("缺少环境变量：" + key);
    }
    return value;
}

private static Connection openConnection() throws SQLException {
    return DriverManager.getConnection(
        requiredEnv("OPS_DB_URL"),
        requiredEnv("OPS_DB_USERNAME"),
        requiredEnv("OPS_DB_PASSWORD"));
}
```

```java
try (Connection connection = openConnection();
     PreparedStatement statement = connection.prepareStatement("SELECT 1");
     ResultSet result = statement.executeQuery()) {
    if (result.next()) {
        System.out.println(result.getInt(1)); // 1
    }
}
```

需要导入 `java.sql.Connection`、`DriverManager`、`PreparedStatement`、`ResultSet`、`SQLException`，或学习阶段使用 `import java.sql.*;`。添加依赖后让 Maven 同步完成，不同时手动粘贴多份驱动 JAR。

创建方法核心示例如下。`normalizedTitle` 表示已经用第 1 周规则处理过的标题；方法调用者还应检查描述长度、用户与设备是否启用。这里展示参数绑定和生成编号，不是完整 Service。

```java
static long insertTicket(String normalizedTitle, String description,
        long deviceId, long reporterId) throws SQLException {
    String sql = "INSERT INTO ticket "
        + "(title,description,device_id,reporter_id,status,version) "
        + "VALUES (?,?,?,?, 'OPEN',0)";
    try (Connection connection = openConnection();
         PreparedStatement statement = connection.prepareStatement(
             sql, Statement.RETURN_GENERATED_KEYS)) {
        statement.setString(1, normalizedTitle);
        statement.setString(2, description);
        statement.setLong(3, deviceId);
        statement.setLong(4, reporterId);
        if (statement.executeUpdate() != 1) {
            throw new SQLException("创建工单受影响行数不是1");
        }
        try (ResultSet keys = statement.getGeneratedKeys()) {
            if (!keys.next()) {
                throw new SQLException("没有取得生成的工单编号");
            }
            return keys.getLong(1);
        }
    }
}
```

此单语句演示使用新 JDBC 连接默认的自动提交。插入已提交却在读取生成键时异常，不应简单认为数据库一定没有新增；先按实际数据库状态排查，不要盲目重复提交。多步业务在第 9 周显式放入事务。数据库自增编号可能有空洞，不把它当连续计数器。

按编号查询时先绑定编号再执行，处理 ResultSet 的关键部分：

```java
String sql = "SELECT id,title,assignee_id,status FROM ticket WHERE id=?";
try (Connection connection = openConnection();
     PreparedStatement statement = connection.prepareStatement(sql)) {
    statement.setLong(1, 101L);
    try (ResultSet result = statement.executeQuery()) {
        if (result.next()) {
            Long assignee = result.getObject("assignee_id", Long.class);
            TicketStatus status = TicketStatus.valueOf(result.getString("status"));
            System.out.println(result.getLong("id") + " | "
                + result.getString("title") + " | " + assignee + " | " + status);
        } else {
            System.out.println("工单不存在");
        }
    }
}
```

`getLong` 返回基本类型，SQL NULL 时要配合 `wasNull()`；这里用 `getObject(..., Long.class)` 保留 null。参数从 1 编号，不是从 0。`executeQuery` 用于返回结果集的查询；`executeUpdate` 用于插入、更新、删除，返回受影响行数。驱动基本用法可查 [DriverManager 官方示例](https://dev.mysql.com/doc/connector-j/en/connector-j-usagenotes-connect-drivermanager.html)。

把一次请求与响应画成文字也合格：

```text
浏览器
  → GET /api/tickets/101
后端：检查身份和数据范围 → 查询数据库 → 组织响应
  → HTTP 200
  → Content-Type: application/json
  → {"id":101,"title":"投影仪无法开机","status":"OPEN"}
浏览器读取 JSON 并显示标题
```

这里是第 7 周将要实现的草图，第 6 周不声称已经有 HTTP 服务。JSON 属性名和字符串用双引号；数字可以不加引号。读取用 GET，创建用 POST；请求地址不是数据库连接 URL。[HTTP 概览](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview)

| 报错或现象 | 先检查 |
| --- | --- |
| No suitable driver | Maven 依赖是否下载、IDEA 是否刷新、运行 classpath 是否带驱动、URL 是否以 jdbc:mysql 开头 |
| Communications link failure | 服务是否在运行，主机与端口是否正确；同配置的数据库客户端能否连接 |
| Access denied | 账号、密码、允许连接的主机与该库权限；不要把 SQL 语法当成原因 |
| No operations allowed after connection closed | 是否离开了 try 块后才使用连接或 ResultSet |
| Before start of result set | 读取列前有没有先执行 result.next() |
| Parameter index out of range | 占位符数量与 setXxx 下标是否对应，下标从 1 开始 |
| 中文乱码 | 源码、终端显示、表字符集、连接与实际存储逐层确认；不要用重复转码掩盖问题 |
| 查不到刚插入的记录 | 是否同一数据库、同一编号，事务是否提交；打印库名和编号，不要打印密码 |

最后独立小改：写 `SELECT id,title,status FROM ticket WHERE status=? ORDER BY id`，绑定 `TicketStatus.OPEN.name()`，循环读取所有行。能够不照抄完成这一小改，并解释每一层数据流，才是准备好进入 Spring Boot 的证据。

## 示例核验范围

提取第 1 周局部逻辑、补充测试壳后，用现有 JDK 8 编译运行，14 项检查通过。其他 SQL、JDBC 片段为教学参考，未连接数据库运行；这不是已经验收的完整项目。
