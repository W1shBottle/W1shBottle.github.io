{
  "title": "第14至20周 自测答案与排错示例",
  "description": "并发、测试与交付的参考实验，深度性能和中间件按实际需要选学。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 130,
  "group": "answers",
  "draft": false,
  "lastmod": "2026-10-26T00:00:00+08:00"
}

> 2026-10-26说明：这是原教材的局部参考答案，周号和固定样本仅作索引。当前路线以[阶段日程](/learning/schedule/)和[数据接口约定](/learning/contracts/)为准；评论、退回、独立处理记录表、缓存与性能专题均不作为接AI门槛。未来依赖版本到接入时再核对，不能把示例代码视为当前实现或本人已掌握。


先完成[第14至20周课程](/learning/testing-delivery/)中的尝试，再核对答案。这里提供判断依据、局部实现和复现实验；包名、Java 方法签名及实际 jar 名称要与你自己的工程对应。读完以后关掉答案，用自己的工程重新做一次，才记为通过。

所有修改数据库的实验只在 `ops_ticket_test`、自己创建的新测试记录或专用恢复库中进行。测试账号不应拥有 `ops_ticket_dev` 的写权限。禁止为了重复实验清空开发库，或把删除 Docker 数据卷当成重置步骤。

## 第14周 并发与事务

### 14.1 先查询再无条件更新为什么出错

因为查询到的是某个时刻的结果，不是对未来修改的独占许可。下面是可能发生的顺序：

| 顺序 | 管理员请求 A | 管理员请求 B |
| --- | --- | --- |
| 1 | 查询到 OPEN、version=0 | |
| 2 | | 也查询到 OPEN、version=0 |
| 3 | 派给工程师甲并更新 | |
| 4 | | 无条件派给工程师乙，覆盖 A 的结果 |

`if (ticket.getStatus() == OPEN)` 只检查 Java 对象中那份旧值。修复要让数据库在实际修改时再次检查状态和期望版本：

```sql
UPDATE ticket
SET assignee_id = ?, status = 'IN_PROGRESS',
    version = version + 1, updated_at = CURRENT_TIMESTAMP
WHERE id = ? AND status = 'OPEN' AND version = ?;
```

三个 `?` 分别绑定处理人、工单编号、用户本次操作基于的版本。MyBatis 可改为命名参数，不能拼接用户输入到 SQL。只有返回影响行数 1 才代表修改成功。

可以先在两个 MySQL 客户端窗口验证。准备一张新的 OPEN 测试工单并记住编号与版本；A 开始事务后执行条件更新但暂不提交；B 开始事务并对同一旧版本执行条件更新，通常会等待；A 提交后 B 继续，条件已不满足，影响行数为 0。B 回滚结束实验。每次 `UPDATE` 后立即看客户端影响行数或执行 `SELECT ROW_COUNT()`。此实验直接操作数据库，只验证并发更新机制；应用权限和日志事务还要通过应用接口验证。

### 14.2 有事务为什么还要条件更新

事务用于让“修改工单、写日志”等操作形成一个整体；它不会自动替你决定“两位管理员谁的派单有效”。若 SQL 只按 id 更新，后来的事务仍可能在前者提交后覆盖处理人。条件更新把业务前提写进同一条 SQL，避免检查和修改之间的空隙。

版本号还能表达“你操作的是旧页面中的工单”。对 OPEN 派单来说状态条件已经能阻止第二次派单，保留版本条件则让后续其他修改也能沿用一致的冲突约定。本项目并不要求为此引入分布式锁。

局部 Service 结构如下，类名和调用方法需要对应自己的实现：

```java
@Transactional
public void assign(long ticketId, long engineerId, long expectedVersion,
                   CurrentUser actor) {
    requireAdmin(actor);
    requireEnabledEngineer(engineerId);
    requireTicketExists(ticketId);
    int changed = ticketMapper.assignIfOpen(
            ticketId, engineerId, expectedVersion);
    if (changed != 1) {
        throw new ConflictException("工单已变化，请刷新后重试");
    }
    actionLogMapper.insertAssign(ticketId, actor.id(), engineerId);
}
```

`CurrentUser`、校验方法和 `ConflictException` 都是项目自己的类型或方法；`ConflictException` 可继承 `RuntimeException`。把它映射为 409。此处 `actor` 必须从服务器认证上下文取得，不能由客户端提交一个管理员编号冒充。状态和日志由同一个事务管理器管理、使用同一数据源参与事务。[Spring 声明式事务](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)

### 14.3 日志写失败后数据库应是什么样

整个业务事务应回滚：工单保持原状态、原处理人和原版本，没有这次派单日志。如果初始值为 OPEN、assignee_id 为 NULL、version 为 0，失败后仍应是这些值。

默认声明式事务对未被吞掉的运行时异常进行回滚；如果是检查型异常，要明确配置适当的回滚规则。不要捕获异常后只打印一句话、继续正常返回；不要让日志写入进入单独提交的事务。事务入口应由另一个组件调用 Spring 管理的 Service Bean，而不是 `new Service()`，也不是在同一个类内部依赖自调用来启动事务。

**诊断顺序：** 先确认调用的是 Spring Bean；再看异常是否逃离事务方法；再看两个 Mapper 是否用同一数据源；最后检查日志方法是否另开事务、更新是否自动提交。不要仅凭注解存在就认定事务一定生效。

## 第15周 自动测试

### 15.1 mock 成功能否证明数据库事务正确

不能。mock 返回的是你预设的行为，没有真实执行 SQL，也没有数据库锁、约束和提交过程。它可以证明 Service 遇到 Mapper 返回 0 时抛出冲突，却不能证明两个真实事务竞争时最终只成功一个。

最小 JUnit 示例只说明断言用法，不与项目类名绑定：

```java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class TitleRuleTest {
    private String normalizeTitle(String title) {
        if (title == null || title.isBlank()) {
            throw new IllegalArgumentException("标题不能为空");
        }
        return title.strip();
    }

    @Test
    void blankTitleIsRejected() {
        assertThrows(IllegalArgumentException.class,
                () -> normalizeTitle("   "));
    }

    @Test
    void surroundingSpacesAreRemoved() {
        assertEquals("投影仪无法开机", normalizeTitle(" 投影仪无法开机 "));
    }
}
```

在正式项目中，应直接测实际领域方法或 Service，避免把业务规则复制到测试类再测复制品。上面只适合第一次学习 JUnit 时运行，之后删除重复规则，用真实实现替换。

数据库集成测试至少实际调用 MyBatis 和 MySQL：创建测试用户、设备与 OPEN 工单；调用真实 Service；重新查询 `ticket` 和 `ticket_action_log`；核对状态、版本和日志。并发测试需要两条独立事务路径，测试前数据必须已经提交，不能被外层未提交的准备事务挡住。对每个等待和 Future 设置超时，失败时也释放门闩并关闭线程池。

### 15.2 测试自动回滚为什么会掩盖业务错误

假设 Service 忘写事务，但测试方法自己开了事务。Service 的数据库操作可能加入测试事务，测试结束时一起被回滚，于是你误以为业务本来就会回滚。真实 HTTP 请求没有这个测试外壳，可能只完成了工单修改而没写日志。

验证步骤要让业务事务独立承担责任：

1. 测试方法本身不加自动回滚事务；使用仅能访问 `ops_ticket_test` 的配置和账号。
2. 创建并提交一张新的 OPEN 工单，记录初始值。
3. 在测试配置中让“写操作记录”这一步抛出运行时异常，但工单 Mapper 和数据库连接仍真实工作。可以使用仅测试生效的日志写入组件，或对实际日志组件做故障注入；不替换工单 Mapper。
4. 调用 Spring 管理的派单 Service，断言确实抛出了预期异常。
5. 在业务调用结束后开启新的查询，核对工单与日志；不能只检查内存里的旧对象。
6. 清理这项测试创建的记录，不清空整个库。

步骤 3 没有执行真实日志 SQL，也能检查真实工单更新是否被异常回滚；若要验证数据库约束引起的失败，可在测试专用日志写入路径中故意写入违反已有非空约束的值。两种方式都必须在测试环境隔离，不能加一个对外的“故障开关”接口。

可用下面的查询核对。`:id` 是说明中的参数占位符，实际通过 PreparedStatement、Mapper 参数或数据库客户端变量绑定，不能直接把这段冒号语法当普通 MySQL SQL 执行。

```sql
SELECT status, assignee_id, version FROM ticket WHERE id = :id;
SELECT COUNT(*) FROM ticket_action_log
WHERE ticket_id = :id AND action = 'ASSIGN';
```

真实端口的接口测试运行在服务端线程中，测试方法自动回滚不会自动覆盖服务器事务，因此数据清理也要单独安排。[Spring Boot 应用测试](https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html)

### 15.3 怎样确认 403 是权限拒绝

先分清请求：普通 GET 查询不要求 CSRF token，所以越权读取的 GET 测试主要确认已登录、账号角色正确、工单存在且属于另一个报修人。写入接口如 POST，需要同时提供有效登录身份和有效 CSRF token，再验证角色或资源权限。

例如使用 Spring Security 的 MockMvc 测试辅助时，局部示例为：

```java
mockMvc.perform(post("/api/tickets/{id}/resolve", ticketId)
        .with(user(actualOtherEngineerPrincipal))
        .with(csrf())
        .contentType(MediaType.APPLICATION_JSON)
        .content("{\"content\":\"已更换线缆\",\"expectedVersion\":0}"))
    .andExpect(status().isForbidden());
```

`actualOtherEngineerPrincipal` 应是应用能识别用户编号的真实 `UserDetails` 实现，且是另一个 ENGINEER；只写 `user("name").roles("ENGINEER")` 可能没有项目需要的 id。测试预先创建状态为 IN_PROGRESS、版本为 0、分配给其他工程师的工单；请求按接口约定提供 `content` 和 `expectedVersion`，避免因请求字段错误先触发 400，无法检验权限。`user` 与 `csrf` 的静态方法来自 Spring Security Test 支持。[CSRF 测试说明](https://docs.spring.io/spring-security/reference/servlet/test/mockmvc/csrf.html)

再补一个对照：正确处理工程师、相同有效请求应成功。最后补缺少 CSRF token 被拒绝的独立用例。三个结果对应三条不同规则，不能混成一个用例。如果项目对不可见资源统一返回 404，就按既有接口契约断言 404，并检查不存在信息泄露，不要为了教材字面数字更改已经明确的策略。

**本周诊断：** 所有请求都 403 先看安全过滤链；只有部分身份失败再看数据权限；事务测试偶尔卡住先看准备数据是否提交、等待是否有超时；第二次跑失败先看测试主键或唯一用户名是否重复。

## 第16周 打包与交付

### 16.1 同一份 jar 为什么能连接不同地址

代码从配置读取数据库地址，地址不写死在 Java 类里。不同环境提供不同配置，同一业务代码就能使用相应数据库。示例使用标准 Spring 数据源属性：

```yaml
spring:
  datasource:
    url: ${SPRING_DATASOURCE_URL}
    username: ${SPRING_DATASOURCE_USERNAME}
    password: ${SPRING_DATASOURCE_PASSWORD}
```

也可以直接利用 Spring 对标准环境变量的映射；上面的显式占位符更方便初学者看出依赖。填写方式在本机按前期选择的配置方案保持一致，密码不要写入公开源码、终端截图或提交记录。改变地址并不会自动替你建表、搬数据或适配不同数据库产品。

### 16.2 只有点击 Run 的说明缺少什么

它没有解释新机器需要什么版本的 JDK、怎样准备数据库和表、配置从哪里来、依赖怎样构建、怎样测试、怎样从 jar 运行，以及失败时看哪里。按下面的最小目录核对 README：

```text
项目目标和业务规则
已验证的 Java / Boot / MyBatis / MySQL 版本
准备数据库和独立账号
填写外部配置
建表与演示数据
运行测试与构建
运行 jar、正常停止、查看日志
角色演示和主要接口
已知限制与排错
```

“在新目录复现”要从可交付的源码、脚本和配置样例开始，不能偷偷依赖原来 IDEA 里的本地设置。首次下载依赖需要网络；要离线演示，就提前确认依赖与 jar 已准备好。

### 16.3 没有实验能不能写高并发高性能

不能把未测量的能力写成已证实的结果。可以写已经实现的具体行为，例如：

> 使用状态与版本条件更新防止重复派单；在真实 MySQL 上验证两个相同期望版本的请求只成功一次，并通过事务保持工单修改与操作记录一致。

这是功能和一致性描述，不等于系统吞吐量结论。做过性能实验以后，写明测试环境、数据量、请求方式和结果，避免省略上下文。没有真实公司用户，就写个人学习项目，不能写“服务数万用户”。

**本周诊断：** IDEA 能跑而 jar 不行，优先比较 JDK、配置和打包产物；只有自己的电脑能跑，核查绝对路径与环境变量；新终端缺少配置，检查变量是否只在旧终端或 IDE 生效。

## 第17周 部署与恢复

### 17.1 容器运行为什么不代表数据库可用

“容器进程存在”只是一个状态。MySQL 可能还在初始化，也可能因目录权限、密码、端口或数据版本不匹配而无法服务。应用可能把 `localhost` 错当成另一个容器的地址，或者数据库还没就绪就尝试连接。

排查顺序：

1. `docker compose ps` 看容器状态与端口。
2. `docker compose logs --tail 100 db` 看数据库服务日志，`db` 改成自己的服务名。
3. 检查应用配置中的主机、端口、库名与账号；容器之间用数据库服务名和内部端口。
4. 使用实际配置尝试连接，区别连接拒绝、认证失败和找不到数据库。
5. 数据库可用后再看应用日志；必要时设置数据库健康检查与应用连接重试。

没有 Docker 时同样适用：先确认 MySQL 服务，再检查地址、认证、库表，最后查应用。不要反复重装所有工具来掩盖一个错误端口。

### 17.2 为什么还要实际恢复

文件可能为空、不完整、字符编码不正确，或依赖没有一起导出。你还可能没有恢复权限、选错目标库、漏掉关联数据。恢复测试让“有文件”变成“这份文件确实能重新形成可用数据”。

以下是按当前已实现表进行的恢复练习；新首版是用户、设备、工单、操作记录四张InnoDB表（当前学习库尚只有前三张），评论和独立处理记录表属于延后扩展，不覆盖已有库。示例假定备份由课程中不带 `--databases` 的命令生成，当前目录有 `backups` 子目录。

1. 停止向学习数据写入，记下源库每张表记录数及两条含中文的工单；备份完成后先确认文件非空。
2. 打开备份文本，确认没有 `CREATE DATABASE`、`USE ops_ticket_dev` 或其他切换到源库的语句。如果有，停止导入，回到课程备份命令重新生成，不要盲目改几个词继续。
3. 使用有建库权限的本地管理账号创建一个全新库，示例 SQL 如下。若库已存在，换一个新名称；不要删除同名库。

```sql
CREATE DATABASE ops_ticket_restore_20270201
CHARACTER SET utf8mb4;
```

4. 确认恢复账号只对这个恢复库有本次恢复所需权限。恢复 SQL 通常含建表和插入语句，可能包含 `DROP TABLE IF EXISTS`；因此目标必须是新空库，不能因为“名称看起来差不多”就复用旧库。
5. 在项目根目录运行下面的交互式客户端命令，账号名替换为实际恢复账号：

```powershell
mysql -u your_restore_user -p ops_ticket_restore_20270201
```

6. 进入 `mysql>` 后，先核对当前库为空，再从当前终端工作目录导入：

```sql
SELECT DATABASE();
SHOW TABLES;
SOURCE backups/ops_ticket_dev_20270201.sql;
SHOW TABLES;
```

`SOURCE` 是 mysql 客户端命令，文件路径指客户端机器上的文件。相对路径不可用时，改用自己确认过的绝对路径与正斜杠；不要把 Linux 的 `< file.sql` 重定向直接复制到 Windows PowerShell。

7. 比较当前已实现的 `app_user`、`device`、`ticket`、`ticket_action_log` 的行数；若以后实现评论和独立处理记录，再额外检查对应扩展表，检查中文标题、密码哈希和时间字段；用 JOIN 检查工单引用的用户和设备都存在。
8. 用临时外部配置把本机应用连接到恢复库，执行一次查询和登录演示。结束后恢复原配置，保留验证记录，不要求删除恢复库。

例如检查恢复库中的工单关联是否缺失：

```sql
SELECT t.id
FROM ticket t
LEFT JOIN device d ON d.id = t.device_id
LEFT JOIN app_user u ON u.id = t.reporter_id
WHERE d.id IS NULL OR u.id IS NULL;
```

结果应为空，但空结果只说明这两种关联未发现缺失，不代表所有恢复验证都通过。备份文件包含学习账号的密码哈希，也应作为私有文件保存。[MySQL 备份工具说明](https://dev.mysql.com/doc/refman/8.4/en/mysqldump.html)

### 17.3 停止容器与删除卷有什么区别

`docker compose stop` 停止运行，保留容器及持久化数据，之后可以再启动。数据库使用命名卷时，正常停止和启动不应使工单消失。删除承载 MySQL 数据的卷会删除其中数据，之后启动可能得到一个全新数据库。

不要用 `docker compose down -v` 演示“安全重启”；其中 `-v` 会删除 Compose 管理的相关卷。即使只执行不带 `-v` 的 `down`，也应事先知道数据到底存在命名卷、绑定目录还是容器可写层，不能凭命令名称判断数据一定保留。[Docker Compose down](https://docs.docker.com/reference/cli/docker/compose/down/)

**本周诊断：** 重启数据丢失先查持久化位置；恢复乱码先查导出和客户端字符集；导入权限不足就核对恢复账号权限，不要改成面向所有库的高权限账号后忘记收回；备份看似成功仍要检查退出结果和文件内容。

## 第18周 索引线程池与 JVM

### 18.1 使用索引就一定更快吗

不一定。索引可能只排除很少数据，还需要大量回表；表很小时扫描全表反而更简单；排序、返回字段、统计信息和缓存状态也会影响结果。`key` 有值只说明选择了某个访问路径，不能代替实际测量。

本项目的候选索引把相等条件 `reporter_id`、`status` 放前面，再按查询排序设计时间和 id 列。它适合特定查询，不保证对“按设备统计”也有帮助。优化记录可使用下面的模板，数值必须自己测量：

```text
数据量和分布：____条工单，OPEN约____%，指定报修人约____条
查询 SQL 和参数：____
环境与数据库版本：____
索引前执行计划及10次耗时：____
索引后执行计划及10次耗时：____
是否排除预热、是否相同返回结果：____
结论与局限：____
```

传统 EXPLAIN 的 `rows` 是估算；`EXPLAIN ANALYZE` 会执行支持的查询并提供实际执行信息，所以仅对自己理解成本的 SELECT 使用。没有明显差异时保留这个结论，同样体现测量能力。[MySQL EXPLAIN](https://dev.mysql.com/doc/refman/8.4/en/using-explain.html)

### 18.2 两线程两队列提交五项会怎样

在前两项任务都持续等待、尚未完成的前提下：任务 1、2 占用两个工作线程；任务 3、4 进入队列；任务 5 因线程与队列都满，被 `AbortPolicy` 拒绝并抛 `RejectedExecutionException`。

下面是一段独立 Java 21 实验，不接入工单业务。它使用门闩固定观察条件，不依赖“机器正好比较慢”。

```java
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

public class PoolDemo {
    public static void main(String[] args) throws InterruptedException {
        CountDownLatch release = new CountDownLatch(1);
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
                2, 2, 0, TimeUnit.SECONDS,
                new ArrayBlockingQueue<>(2),
                new ThreadPoolExecutor.AbortPolicy());
        try {
            for (int i = 1; i <= 5; i++) {
                final int taskId = i;
                try {
                    pool.execute(() -> {
                        try {
                            release.await();
                            System.out.println("完成任务 " + taskId);
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                        }
                    });
                } catch (RejectedExecutionException e) {
                    System.out.println("被拒绝的任务 " + taskId);
                }
            }
        } finally {
            release.countDown();
            pool.shutdown();
            if (!pool.awaitTermination(5, TimeUnit.SECONDS)) {
                pool.shutdownNow();
            }
        }
    }
}
```

预期第五项被拒绝，其余四项完成；四个完成信息之间的顺序不固定。这里使用 `execute`，若改成 `submit` 并在任务中抛异常，需要查看 `Future.get()` 的异常结果，不能只看提交方法有没有抛异常。线程池大小也必须考虑数据库连接和 CPU 等下游资源。[Java 21 线程池文档](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)

### 18.3 无限线程和永久 List 分别有什么风险

反复创建大量线程会增加线程栈、调度和系统资源开销，严重时无法再创建线程。把所有查询结果一直保存在某个长期存活的 List 中，会让这些对象仍可达，GC 无法回收，堆使用量持续增长。

GC 不是“内存不够时自动把没用的数据都猜出来删除”。程序还持有引用，GC 通常就必须认为对象可能被使用。数据库连接、文件等外部资源应按生命周期关闭，也不能等 GC 替你处理。应限制分页大小、缓存容量和线程数，并观察真实资源使用。

**本周诊断：** 索引没被选不代表索引创建失败，先看查询和数据分布；线程池程序一直不退出，先看任务是否结束、门闩是否放行、池是否关闭；内存升高不必立即调堆，先查是否无界集合或无界排队。

## 第19周 缓存与知识库

### 19.1 两个报修人能共用列表缓存吗

不能直接共用。列表结果受当前登录用户、角色、筛选条件和分页影响。若 A 的结果写入一个公共 key，B 读取它，就可能看见 A 的私有工单。鉴权也不能因为“有缓存”而跳过。

这也是本课程只推荐先缓存管理员统计的原因：范围比较明确，容易验证。若以后缓存私有列表，key 至少需要表达正确的用户与查询范围，例如下面只是结构示意：

```text
ticket:list:reporter:1:status:OPEN:device:all:page:1:size:20
```

还需要考虑角色变更、数据变更和失效策略。包含用户 id 只是必要设计的一部分，并不自动让整个缓存方案安全正确。

### 19.2 数字滞后什么时候是约定行为

如果功能明确允许“最多 30 秒陈旧”，页面显示更新时间，缓存过期后能重新加载，那么 10 秒前的数据可能符合约定。如果已超过约定窗口仍不更新，或者把旧数据用于必须立即准确的派单判断，就是错误。

本项目派单是否合法必须由数据库条件更新决定，不能从统计缓存判断。缓存统计只辅助展示。测试至少包含以下步骤：查询并记录初始数量 → 创建一张工单 → 在约定窗口内读取 → 过期后再读取并核对数据库。若采用主动失效，还应检查每一种会改变状态数量的操作是否触发失效。

缓存服务不可用时可回退数据库，但也要观察请求量是否在本机能承受的范围。个人项目先保证正确性，不用为了一个统计查询立即搭建复杂集群。

### 19.3 没接模型的知识库有什么价值

它仍能把常见故障整理成可查询资料，减少重复查找；可以验证文章维护、检索、分页、输入处理和来源展示。比如输入“投影 黑屏”，返回两条含关键词的条目并说明匹配依据，找不到就明确显示无结果。

自测数据至少包括：命中一条、命中多条、没有匹配、空白输入、停用文章不展示。不要把关键词匹配叫成语义检索，也不要把简单数据库搜索写成 RAG。以后接模型时才考虑检索结果怎样进入上下文、引用怎样验证和无依据时怎样回答。

**本周诊断：** 先核对原始 SQL 结果，再看缓存；先核对关键词规则，再谈模型；扩展导致主线不稳定时回到最后通过测试的版本，保留扩展代码与问题记录。

## 第20周 面试与独立修改

### 20.1 一分钟解释防止重复派单

参考表达，必须用自己的实现替换细节：

> 两个管理员可能同时读到工单处于 OPEN，直接按 id 更新会产生覆盖。我把工单 id、OPEN 状态和页面读到的版本一起放进 UPDATE 条件，成功后版本加一，并检查影响行数。只有一个请求更新一行，另一个返回零行时转成 409，提醒刷新。工单修改和操作记录在同一个事务里。我用两个独立请求携带同一初始版本验证，最终只派单一次，版本只加一，日志只有一条。

追问“为什么不用 Java 锁”时说明 JVM 内锁的范围；追问“日志失败怎么办”时说明回滚验证；追问“版本能防止所有重复提交吗”时说明这是本次派单的状态与并发策略，不等于所有接口都自动幂等。

### 20.2 没压测怎样回答并发能力

如实回答范围：

> 目前做了并发正确性验证，两个请求竞争同一张工单只成功一个，但没有完成系统容量压测，所以我不能给出吞吐量上限。我做过的查询实验是……。如果要测容量，我会先固定机器、数据量、请求比例和并发模型，观察响应时间、错误率、CPU、数据库连接与慢查询，再逐步增加负载。

不要把“两个请求的并发冲突测试”说成“支持高并发”。不了解的指标可以说还没测，再解释已经验证的部分。

### 20.3 新增设备筛选要改什么

先确认接口参数如 `deviceId` 的含义和可选性，再沿请求路径检查：

1. DTO 或请求参数接收设备编号；校验非法编号、分页大小等输入。
2. Service 仍从登录身份确定可见范围。设备过滤只是增加条件，不能替代报修人或处理人限制。
3. Mapper 的列表和总数查询都增加同样的设备条件，保持分页统计一致。
4. 索引是否需要调整，用实际查询决定；没有测量就先保留简单实现。
5. 增加接口测试，覆盖自己的设备工单、他人的同设备工单、无结果和不传参数；更新接口说明与页面。

报修人查询的核心意思应当是：

```sql
WHERE reporter_id = :currentUserId
  AND device_id = :deviceId
```

可选状态等条件继续用 AND 组合，不能误写成 `reporter_id = ... OR device_id = ...`，否则可能把同设备的他人工单泄露出来。这里的冒号仍是参数说明，MyBatis 实现时换成绑定参数。

用既有样本验证尤其直接：reporter_a 是用户 1，reporter_b 是用户 4；101 和 103 都关联设备 1，但报修人不同。用户 1 按设备 1 筛选时能看到 101，不应该因为设备相同就看到 103；管理员在合法权限下可以看见两者。

**本周诊断：** 讲不清就顺着一条真实请求解释；现场小改先画影响范围再动手；总数和列表不一致先查两个 SQL 条件；问题没做过就承认范围，不编测量结果。

## 自评分方法

每题给自己 0—2 分：0 分是答不出或结论错误，1 分是看答案后能解释，2 分是不看答案能解释并在项目中验证。每周 6 分满分，至少 4 分且关键验收通过再继续；14、15 周的并发和事务即使其他题得分高，也必须亲自验证。自评分帮助安排补课，不是招聘通过率预测。
