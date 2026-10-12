{
  "title": "第7至13周自测答案与关键实现提示",
  "description": "第7—13周接口、MyBatis、事务、浏览器请求与安全配置参考。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 120,
  "group": "answers",
  "draft": false
}
对应[Web与权限课程](/learning/web-security/)。先完成自己的解答，再逐项对照；答案不要求逐字背诵。能把解释用于一个新例子，比记住术语更重要。

下列代码分为可以单独运行的最小示例和必须嵌入项目的局部示例，均明确标注。业务类、Mapper与Service应由你按课程逐步完成；本资料不是一个已构建、已联调的完整应用，也不替代你运行验收。

## 第7周答案和最小接口

**7.1 创建请求为何不直接用数据库实体？** 数据库实体含id、reporterId、assigneeId、status、version等服务端字段，客户端没有修改它们的权利。专门的DTO只接收本次操作允许传入的字段，Service再构造合法对象。即便JSON附带 `status=CLOSED`，也不能把它复制成最终状态；可拒绝未知字段或忽略未知字段，业务结果都不能被它改变。

**7.2 手动new与构造器注入的区别？** 手动new本身没有错，第3周就是这样组装对象的。但在Controller里到处new，会把业务和存储实现选择散落到多个入口，且自己new的Service通常不受Spring事务代理管理。构造器注入让对象依赖显式可见，由容器统一组装，也便于测试时传入替身。它不会自动让业务逻辑正确。

**7.3 404、400、500分别先查什么？** 404先核对URL、HTTP方法、Controller映射以及资源编号；400先看JSON格式、字段类型、约束和请求Content-Type；500先看服务器异常堆栈与导致失败的数据库或业务调用。连接被拒绝甚至没有HTTP响应时，应先查进程和端口，不能归类为500。

### Boot工程依赖参考

在生成的Boot4.1工程里检查依赖。Web MVC使用 `spring-boot-starter-webmvc`，Validation使用 `spring-boot-starter-validation`；第12周才加 `spring-boot-starter-security`。这些依赖使用 `org.springframework.boot` groupId，版本跟随Boot父POM。Boot4官方已把旧 `spring-boot-starter-web` 标为由webmvc替代，不把旧教程整份POM复制过来。[Boot依赖与Starter](https://docs.spring.io/spring-boot/reference/using/build-systems.html)

Boot主类位于顶层包，以下是**可放进已生成Boot工程的完整最小Controller**，业务接口仍需自己实现。文件名为 `PingController.java`，位于 `com.example.opsticket.controller` 包。

```java
package com.example.opsticket.controller;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PingController {
    @GetMapping("/api/ping")
    public Map<String, String> ping() {
        return Map.of("message", "ok");
    }
}
```

进入包含 `pom.xml` 与 `mvnw.cmd` 的工程根目录后运行：

```powershell
.\mvnw.cmd -v
.\mvnw.cmd spring-boot:run
```

第一个命令显示Java21；第二个应保持运行，另开终端发送请求。退出用原终端Ctrl+C。依赖首次下载需要网络，后续离线构建还要求插件与依赖已缓存。

以下请求用于**第7至11周本地尚未登录的开发阶段**；第12周后使用后文Session与CSRF方法，不能继续发送匿名写请求。

```powershell
$ticketBody = @{
    title = '教学楼投影仪无信号'
    description = '通电后指示灯亮，但无法显示输入画面'
    deviceId = 1
} | ConvertTo-Json

$createdTicket = Invoke-RestMethod -Uri 'http://localhost:8080/api/tickets' -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($ticketBody))
$createdTicket
Invoke-RestMethod -Uri ('http://localhost:8080/api/tickets/' + $createdTicket.id)
```

POST应201，响应至少含新id、title、deviceId、status和version；客户端取得的新id再用于下一次请求，不假定永远是104。

**排错顺序：** 端口8080被占用时先查占用进程，或明确改 `server.port=8081`并同步请求地址；找不到Controller时查包层级；返回JSON为空时查getter或DTO定义；不要加一堆 `@ComponentScan` 来掩盖目录错误。

## 第8周答案和Mapper

**8.1 `#{}`与`${}`的区别？** `#{title}`把内容作为绑定参数，单引号只是内容；`${title}`先把文本拼入SQL，改变SQL结构的风险由此产生。值用 `#{}`。列名和排序方向不能当普通值绑定，应在服务端白名单中选择固定SQL，本项目直接固定排序即可。

**8.2 `reporterId`为什么为null？** 先查SELECT是否选出 `reporter_id`且源数据非null；再查列名到属性名的映射或别名；最后查Java属性名、setter、类型是否一致。不是每个null都意味着数据库没数据。`assigneeId`初始允许null，应使用 `Long`，避免把“尚未派单”和编号0混在一起。

**8.3 接口为何能注入？** MyBatis与Spring集成会扫描标记的Mapper，为接口生成代理对象，方法调用由代理定位映射SQL并执行。你不必手写实现类，但必须保证映射名、参数名、SQL和结果类型一致。具体扫描方式参见[MyBatis Starter说明](https://mybatis.org/spring-boot-starter/mybatis-spring-boot-autoconfigure/)。

### 配置与版本

以下为 `application.properties` **局部配置**，URL、账号与密码从环境读取；在IDEA的运行配置里填写 `OPS_DB_URL`、`OPS_DB_USERNAME`、`OPS_DB_PASSWORD`，不要把实际密码写进共享截图或Git。URL示例为 `jdbc:mysql://localhost:3306/ops_ticket_dev?connectionTimeZone=Asia/Shanghai`，实际端口以你的数据库为准。

```properties
server.address=127.0.0.1
spring.datasource.url=${OPS_DB_URL}
spring.datasource.username=${OPS_DB_USERNAME}
spring.datasource.password=${OPS_DB_PASSWORD}
mybatis.configuration.map-underscore-to-camel-case=true
mybatis.mapper-locations=classpath:mapper/*.xml
```

若全用注解SQL，可以先不设mapper-locations。注解与XML可按方法混用，但同一方法不要定义两份SQL。

```powershell
.\mvnw.cmd dependency:tree '-Dincludes=com.mysql:mysql-connector-j'
```

核对这条命令显示的实际驱动。沿用MySQL8.0时，Connector/J9.7.0官方说明支持8.0及以上；必要时在该依赖显式固定9.7.0，并把原因写入README。采用新驱动前查看其服务端要求，不把驱动版本和MySQL服务端版本当成必须相同的数字。独立8.4部署环境仍单独验收。[Connector/J9.7.0发布说明](https://dev.mysql.com/doc/relnotes/connector-j/en/news-9-7-0.html)

### Mapper局部示例

前置：你已编写普通JavaBean `TicketRow`，具有数据库字段对应属性、无参构造器、getter/setter；其中id用 `Long`且可以回填。下面是**接口中的两个方法**，不是完整Mapper文件。注解来自 `org.apache.ibatis.annotations`，`TicketRow`来自你自己的model包。

```java
@Select("""
    SELECT id, title, description, device_id, reporter_id,
           assignee_id, status, version, created_at, updated_at
    FROM ticket
    WHERE id = #{id}
    """)
TicketRow findById(@Param("id") long id);

@Insert("""
    INSERT INTO ticket
      (title, description, device_id, reporter_id, assignee_id,
       status, version, created_at, updated_at)
    VALUES
      (#{title}, #{description}, #{deviceId}, #{reporterId}, NULL,
       'OPEN', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)
@Options(useGeneratedKeys = true, keyProperty = "id")
int insert(TicketRow ticket);
```

Service先填写经过校验的title、description、deviceId以及服务器身份的reporterId，调用insert之后从 `ticket.getId()`读取生成编号，再查详情返回。不要把SQL的受影响行数当工单id；返回1只说明插入了一行。[MyBatis生成键与参数映射](https://mybatis.org/mybatis-3/sqlmap-xml.html)

**常见排错：** `Invalid bound statement`查Mapper XML的namespace是否是接口完整类名、id是否等于方法名、XML是否打包进resources；`Parameter ... not found`查 `@Param` 名与SQL一致；`Access denied`查账号、密码、主机与授权；`Communications link failure`先查数据库服务与端口；`Unknown database`查URL库名；这些问题不能靠换成root账号一概解决。

### 最小设备接口提示

`GET /api/devices?enabled=true`供报修表单选择启用设备；管理员查看全部时可省略enabled条件。`POST /api/devices`只接收code、name、location，trim后检查code与name非空，数据库以唯一约束保证code不重复，成功返回201与id。`PATCH /api/devices/{id}/enabled`只接收布尔enabled，用 `Boolean`配合 `@NotNull`区分缺失与false。

下面是**绑定参数的SQL逻辑**，转成MyBatis时把问号改成相应 `#{属性名}`；列表应明确字段，启用条件按是否传入选择。

```sql
SELECT id, code, name, location, enabled FROM device ORDER BY id;
INSERT INTO device (code, name, location, enabled) VALUES (?, ?, ?, TRUE);
UPDATE device SET enabled = ? WHERE id = ?;
```

PATCH先查设备是否存在，不存在404；已经是目标状态可直接返回200和当前数据，不把“重复停用”当工单状态冲突。停用只改enabled，历史工单的device_id不变。创建工单时重新检查设备是否启用，不能仅依赖页面下拉框。重复编码映射409并提示换一个code，其他数据库异常不能一概说成“编码重复”。第13周将两个写接口限制ADMIN，读接口供已登录用户使用。

## 第9周答案和事务边界

**9.1 为什么不能吞异常？** 事务方法如果捕获运行时异常后正常返回，框架可能把它视为一次成功调用并提交已做的修改。应让异常越过事务方法，由外层异常处理映射为HTTP错误；或明确标记回滚，但初学阶段采用前一种。不要 `catch(Exception)` 后只打印一行并返回false。

**9.2 `this.assign`有什么问题？** Spring常通过代理在方法前后开始和结束事务。同一个对象内部直接调用自己，绕过外部代理，注解可能不生效。把事务边界放在Controller通过注入对象调用的公开Service方法上；不要new这个Service，不把事务写在只会内部调用的小工具方法上。[Spring事务代理说明](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)

**9.3 为什么0行不能继续记成功日志？** WHERE条件未匹配意味着工单已变更、状态不对或不存在。没有成功修改，就没有派单成功这一业务事实。先区分不存在404、无权403，再把状态或版本不匹配作为409；抛异常使本次事务不产生成功记录。

### 业务规则答案

| 操作 | 操作者 | 原状态 | 新状态 | 必填内容 |
| --- | --- | --- | --- | --- |
| assign | ADMIN | OPEN | IN_PROGRESS | engineerId、expectedVersion |
| resolve | 本单ENGINEER | IN_PROGRESS | RESOLVED | content、expectedVersion |
| accept | 本单REPORTER | RESOLVED | CLOSED | expectedVersion |
| reject | 本单REPORTER | RESOLVED | IN_PROGRESS | reason、expectedVersion |

权限在第13周正式接入，此表从一开始就作为最终目标。退回不清除assigneeId；再次处理新增resolution，旧记录保留。关闭后可评论但不能继续变更状态，这是本项目选择的业务规则。

下面是**Mapper方法局部示例**。影响行数检查和事务必须在Service完成。

```java
@Update("""
    UPDATE ticket
    SET assignee_id = #{engineerId}, status = 'IN_PROGRESS',
        version = version + 1, updated_at = CURRENT_TIMESTAMP
    WHERE id = #{id} AND status = 'OPEN' AND version = #{expectedVersion}
    """)
int assign(@Param("id") long id,
           @Param("engineerId") long engineerId,
           @Param("expectedVersion") long expectedVersion);
```

下面是**Service方法的实现次序，不是可直接编译的完整类**。其中 `currentUser`、`permission`、Mapper、DTO和业务异常由你按相应周次定义；第9周使用服务器本地身份，第13周换为会话与权限实现。

```text
公开的@Transactional方法 assign(id, command)
  1. 取服务器当前操作者，检查其为ADMIN
  2. 查工单，不存在则404
  3. 查目标工程师，要求存在、启用、角色为ENGINEER
  4. 校验OPEN与expectedVersion
  5. 执行带状态和版本条件的UPDATE
  6. 影响行数不是1则抛ConflictException（继承RuntimeException）
  7. INSERT ticket_action_log
       (ticket_id,actor_id,action,from_status,to_status,note,created_at)
       写入(id,操作者id,'ASSIGN','OPEN','IN_PROGRESS',说明,当前时间)
  8. 正常结束提交；异常越过方法时回滚
```

`resolve`同一事务内更新工单、插入 `ticket_resolution`、写日志；accept/reject更新和写日志。MyBatis使用Spring管理的同一DataSource和事务，别在某个Mapper旁边额外 `DriverManager.getConnection`另开连接。[MyBatis事务说明](https://mybatis.org/spring/transactions.html)

**回滚实验的证据：** 先记录工单的status/version与日志、结果条数；使更新之后且日志插入之前出现运行时异常；调用真实HTTP接口；再用新的SQL连接查询，前后完全一致才算通过。仅看到500，或仅靠Mock对象证明“抛了异常”，都不能证明数据库回滚。

## 第10周答案和分页校验

**10.1 `@Size`能否拒绝空标题？** 不能单独完成。`@Size(max=50)`允许长度0，也通常把null视为有效；用 `@NotBlank`拒绝null、空字符串与纯空白，再加 `@Size(max=50)`限制上限。必须有Validation依赖并触发校验。

**10.2 count漏条件会怎样？** items可能只有2条符合条件的工单，total却显示12，于是页面出现多余页码；接入权限后还可能泄露别人的工单数量。列表与count复用相同WHERE条件，仅排序与LIMIT有所不同。

**10.3 为什么不能所有错误都200？** 浏览器请求工具、监控和调用方都依赖状态码区分成功与失败。200会使失败看起来像成功，页面可能清空用户输入或刷新列表，排错也更困难。状态码负责大类，code/message负责具体含义。

### DTO最小示例

以下是**完整DTO类**，依赖Boot Validation starter，文件名 `CreateTicketRequest.java`。Java21支持record；它自动保存构造参数并提供 `title()` 等访问方法，适合短小的请求类型。不会record时可用普通类写相同字段和getter，不影响业务设计。

```java
package com.example.opsticket.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

public record CreateTicketRequest(
        @NotBlank @Size(max = 50) String title,
        @NotBlank @Size(max = 2000) String description,
        @NotNull @Positive Long deviceId) {
    public CreateTicketRequest {
        title = title == null ? null : title.trim();
        description = description == null ? null : description.trim();
    }
}
```

Controller方法参数应为 `@Valid @RequestBody CreateTicketRequest request`；两个注解分别来自 `jakarta.validation.Valid` 和 `org.springframework.web.bind.annotation.RequestBody`。带 `@Size`的长度采用Java字符串长度规则，数据库和应用校验不要各自假定不同“字符数”。[Spring MVC校验](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-validation.html)

分页先采用显式校验也完全可以：

```java
// Controller收到page与size后，交给Service前执行的局部代码。
if (page < 1 || size < 1 || size > 100) {
    throw new IllegalArgumentException("page至少为1，size必须在1到100之间");
}
long offset = ((long) page - 1) * size;
```

注意先把page转long再乘，别等int已经溢出之后才转。请求 `page=abc` 会在类型转换阶段失败，也应映射400。

### XML分页片段

以下是**Mapper XML中的局部SQL片段**，假定Mapper方法有 `@Param("status")`、`@Param("deviceId")`、`@Param("offset")`、`@Param("size")`，status先在Java侧校验为允许的枚举值或null。第13周要把权限范围也加入这一公用where。

```xml
<sql id="ticketFilters">
  <where>
    <if test="status != null">
      AND status = #{status}
    </if>
    <if test="deviceId != null">
      AND device_id = #{deviceId}
    </if>
  </where>
</sql>

<select id="count" resultType="long">
  SELECT COUNT(*) FROM ticket
  <include refid="ticketFilters"/>
</select>

<select id="findPage" resultType="com.example.opsticket.model.TicketRow">
  SELECT id, title, description, device_id, reporter_id, assignee_id,
         status, version, created_at, updated_at
  FROM ticket
  <include refid="ticketFilters"/>
  ORDER BY created_at DESC, id DESC
  LIMIT #{size} OFFSET #{offset}
</select>
```

固定样本、固定筛选条件下，total=12、size=5时三页数量为5、5、2，第4页0。实时新增删除时offset分页可能移动边界，这不是固定排序就能彻底解决的问题；本阶段先记录这个限制，暂不引入游标分页。

**异常处理清单：** DTO校验失败 `MethodArgumentNotValidException`；直接方法参数约束可能是 `HandlerMethodValidationException`；坏JSON `HttpMessageNotReadableException`；查询参数类型不符 `MethodArgumentTypeMismatchException`。这些转400；你的NotFoundException转404，ConflictException转409。进入第12周后，安全过滤器的401/403用Security处理器输出，不能指望MVC的Advice包办所有过滤器异常。

业务异常可以用 `{ "code":"TICKET_CONFLICT", "message":"工单状态已变化，请刷新后重试" }`。意外异常不要把SQL语句、密码、数据库地址或完整堆栈原样返回页面。

## 第11周答案和页面请求

**11.1 fetch为何没有因500抛异常？** fetch主要用拒绝Promise表示网络等请求失败；拿到HTTP500响应仍属于收到了响应。代码必须主动看 `response.ok` 或 `response.status`。[Fetch用法](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)

**11.2 评论为什么用textContent？** textContent把 `<b>` 当普通文字；innerHTML让浏览器把它解释成HTML，用户输入可能改变页面甚至执行不应执行的内容。本项目评论就是纯文本，直接用textContent最符合需求。

**11.3 隐藏按钮能否保护接口？** 不能。用户能用HTTP客户端发送相同请求，甚至编辑浏览器里的页面。按钮控制只为了让人不误操作，服务端仍要验证身份、角色、归属、状态与版本。

以下是**第11周app.js的局部辅助函数**，供未接登录时使用；第12周应由后文带CSRF的函数替代。

```javascript
async function requestJson(url, method = "GET", data) {
  const headers = { Accept: "application/json" };
  const options = { method, headers, credentials: "same-origin" };
  if (data !== undefined) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(data);
  }
  const response = await fetch(url, options);
  const text = await response.text();
  let result = null;
  if (text) {
    try { result = JSON.parse(text); }
    catch { throw new Error("服务器返回格式异常，请检查Network响应"); }
  }
  if (!response.ok) {
    throw new Error(result?.message ?? `请求失败：${response.status}`);
  }
  return result;
}
```

先读文本并判断是否为空，因而204不会直接执行 `response.json()`。页面事件处理应 `try/catch/finally`：try发请求并更新页面，catch展示消息，finally恢复按钮。禁用按钮能降低双击概率，但仍须保留后端条件更新。

在HTML放 `<ul id="tickets"></ul>` 后，可用下面的**列表渲染片段**。假定接口返回 `{items,total,page,size}`。

```javascript
const page = await requestJson("/api/tickets?page=1&size=10");
const list = document.getElementById("tickets");
list.replaceChildren();
for (const ticket of page.items) {
  const item = document.createElement("li");
  item.textContent = `${ticket.id} ${ticket.title} ${ticket.status}`;
  list.append(item);
}
```

若直接使用顶层await，脚本标签要写 `<script type="module" src="/app.js"></script>`；也可把片段包进async函数再调用。数字输入框的value是字符串，提交deviceId前转换并检查，如 `Number(input.value)` 及 `Number.isInteger`。

**排错记录示例：** “页面提示JSON解析失败→第12周退出接口的Network响应显示204空体→代码无条件response.json→改为先检查空响应→退出成功且页面跳回登录”。这是可供练习的排错场景；只有你实际遇到并记录后，才把它作为个人经历用于面试。

## 第12周答案和Session登录接线

**12.1 authenticate成功为何不代表下一次也登录？** authenticate只完成本次凭据验证并返回认证对象。认证上下文还必须通过框架机制保存，下次请求才能从会话恢复。主线使用框架formLogin，由过滤器执行认证、会话处理和上下文保存；不要自写仅调用AuthenticationManager的“假登录成功”接口。[认证持久化](https://docs.spring.io/spring-security/reference/servlet/authentication/session-management.html)

**12.2 正确密码却403先查什么？** 查看请求是否包含当前会话对应的CSRF头，Cookie是否随请求发送，登录参数是否用表单编码而非JSON。缺少CSRF可能在验证密码之前被拒绝，所以改密码、删除Security依赖都不是对应修复。

**12.3 登录后旧CSRF为何失效？** 框架会在成功登录和退出时清除旧令牌；浏览器应重新GET `/api/csrf`并使用新的返回值。这也是为什么不能把令牌永久写死在JavaScript中。[CSRF令牌生命周期](https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html)

### 账号读取的连接点

前置：编写 `AppUserRow`普通JavaBean，属性为id、username、passwordHash、role、enabled；`enabled`用boolean并提供 `isEnabled()`。`AppUserMapper.findByUsername`采用 `#{username}`，返回用户行或null：

```sql
SELECT id, username, password_hash, role, enabled
FROM app_user
WHERE username = ?;
```

这里的问号表示绑定参数；MyBatis实际映射写 `#{username}`。`username`有唯一约束。下面是**放入配置类的局部Bean方法**，需要导入你自己的Mapper，以及框架的Bean、UserDetailsService、UsernameNotFoundException、User：

```java
@Bean
UserDetailsService userDetailsService(AppUserMapper users) {
    return username -> {
        AppUserRow row = users.findByUsername(username);
        if (row == null) {
            throw new UsernameNotFoundException("账号或密码错误");
        }
        return User.withUsername(row.getUsername())
                .password(row.getPasswordHash())
                .roles(row.getRole())
                .disabled(!row.isEnabled())
                .build();
    };
}
```

`User`为 `org.springframework.security.core.userdetails.User`，不要导入自己的同名用户实体。数据库role只允许REPORTER、ENGINEER、ADMIN；`UserDetailsService`负责读取，PasswordEncoder负责核对密码，调用顺序由框架认证提供器组织。[UserDetailsService](https://docs.spring.io/spring-security/reference/servlet/authentication/passwords/user-details-service.html)、[认证提供器](https://docs.spring.io/spring-security/reference/servlet/authentication/passwords/dao-authentication-provider.html)

### Security配置模板

这是**一个完整配置类模板**，前提是已加入Security依赖、上面的UserDetailsService Bean已由另一个配置类提供，并且登录页、CSRF端点及业务Controller存在。它只完成认证接线；第13周Service里的数据权限仍需自己写。若项目已有SecurityFilterChain，要修改现有配置，不叠加第二份不明顺序的配置。

```java
package com.example.opsticket.security;

import java.io.IOException;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.factory.PasswordEncoderFactories;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.csrf.CsrfException;

@Configuration
public class SecurityConfig {
    @Bean
    PasswordEncoder passwordEncoder() {
        return PasswordEncoderFactories.createDelegatingPasswordEncoder();
    }

    @Bean
    SecurityFilterChain securityFilterChain(
            HttpSecurity http, UserDetailsService users,
            PasswordEncoder passwords) throws Exception {
        var provider = new DaoAuthenticationProvider(users);
        provider.setPasswordEncoder(passwords);
        http.authenticationProvider(provider);
        http.csrf(Customizer.withDefaults());
        http.requestCache(cache -> cache.disable());
        http.authorizeHttpRequests(auth -> auth
                .requestMatchers("/", "/index.html", "/login.html",
                        "/app.js", "/auth.js", "/style.css", "/favicon.ico",
                        "/api/csrf", "/error").permitAll()
                .requestMatchers("/api/**").authenticated()
                .anyRequest().denyAll());
        http.formLogin(form -> form
                .loginPage("/login.html")
                .loginProcessingUrl("/api/login")
                .successHandler((request, response, auth) -> response.setStatus(204))
                .failureHandler((request, response, error) -> writeError(response, 401,
                        "{\"code\":\"LOGIN_FAILED\",\"message\":\"账号或密码错误\"}"))
                .permitAll());
        http.logout(logout -> logout
                .logoutUrl("/api/logout")
                .deleteCookies("JSESSIONID")
                .logoutSuccessHandler((request, response, auth) -> response.setStatus(204))
                .permitAll());
        http.exceptionHandling(errors -> errors
                .authenticationEntryPoint((request, response, error) ->
                        writeError(response, 401,
                                "{\"code\":\"UNAUTHENTICATED\",\"message\":\"请先登录\"}"))
                .accessDeniedHandler((request, response, error) -> {
                    String body = error instanceof CsrfException
                            ? "{\"code\":\"CSRF_INVALID\",\"message\":\"请求令牌失效，请刷新页面\"}"
                            : "{\"code\":\"FORBIDDEN\",\"message\":\"没有操作权限\"}";
                    writeError(response, 403, body);
                }));
        return http.build();
    }

    private static void writeError(HttpServletResponse response, int status,
                                   String fixedJson) throws IOException {
        response.setStatus(status);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(fixedJson);
    }
}
```

该例只写固定JSON常量，没有拼接用户内容；动态对象应交给JSON序列化器。Boot4的JSON包与旧教程可能不同，不为一个错误响应照搬旧ObjectMapper依赖。`DaoAuthenticationProvider(UserDetailsService)`构造器及 `setPasswordEncoder`已按当前API核对。[认证提供器API](https://docs.spring.io/spring-security/reference/api/java/org/springframework/security/authentication/dao/DaoAuthenticationProvider.html)

框架处理POST `/api/login`与POST `/api/logout`，不要再为这两个地址写同名Controller。第13周如增加HTTP级角色匹配，应放在 `/api/**` 的宽泛规则前面；具体工单归属仍在Service检查。

### CSRF端点模板

以下是**完整Controller模板**，继续使用默认会话CSRF存储，并通过参数取得框架已经处理的令牌，不自行替换令牌编码方式。

```java
package com.example.opsticket.controller;

import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CsrfController {
    public record TokenView(String headerName, String token) { }

    @GetMapping("/api/csrf")
    public ResponseEntity<TokenView> token(CsrfToken csrf) {
        var view = new TokenView(csrf.getHeaderName(), csrf.getToken());
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(view);
    }
}
```

### 同源页面的登录与写请求

以下是**auth.js辅助函数示例**，登录页面需要自行提供输入框，并在提交事件中调用login；它替代第11周没有CSRF的写请求方法。令牌只存在内存里，页面每次加载可重新获取。Cookie由浏览器管理，不尝试用JavaScript读取HttpOnly会话Cookie。

```javascript
let csrfInfo;

async function readResponse(response) {
  const text = await response.text();
  let data = null;
  if (text) {
    try { data = JSON.parse(text); }
    catch { throw new Error(`响应格式异常：${response.status}`); }
  }
  if (!response.ok) {
    const error = new Error(data?.message ?? `请求失败：${response.status}`);
    error.status = response.status;
    error.code = data?.code;
    throw error;
  }
  return data;
}

async function refreshCsrf() {
  const response = await fetch("/api/csrf", {
    credentials: "same-origin", cache: "no-store"
  });
  csrfInfo = await readResponse(response);
}

async function login(username, password) {
  await refreshCsrf();
  const response = await fetch("/api/login", {
    method: "POST",
    credentials: "same-origin",
    headers: { [csrfInfo.headerName]: csrfInfo.token },
    body: new URLSearchParams({ username, password })
  });
  await readResponse(response);
  await refreshCsrf();
}

async function apiJson(url, method = "GET", data) {
  const headers = { Accept: "application/json" };
  const options = { method, credentials: "same-origin", headers };
  const modifies = !["GET", "HEAD", "OPTIONS"].includes(method.toUpperCase());
  if (modifies) {
    if (!csrfInfo) await refreshCsrf();
    headers[csrfInfo.headerName] = csrfInfo.token;
  }
  if (data !== undefined) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(data);
  }
  return readResponse(await fetch(url, options));
}

async function logout() {
  await apiJson("/api/logout", "POST");
  csrfInfo = undefined;
  await refreshCsrf();
}
```

登录成功后可跳回主页；新页面重新调用refreshCsrf即可。页面遇401提示重新登录；遇403区分 `CSRF_INVALID` 与业务无权；遇409提示数据已变更。不要对失败POST无限自动重发，避免重复创建和评论。CORS不在本阶段引入，也不添加允许任意来源携带凭据的配置。

### 密码和当前用户

生成演示密码哈希时，在已有依赖的本地Java练习或测试中调用 `PasswordEncoderFactories.createDelegatingPasswordEncoder().encode(演示密码)`，把返回的完整字符串存入password_hash，列长建议255。实际校验用 `matches(原始密码,数据库哈希)`；两次encode结果不同是正常现象。演示账号只用于学习库，密码不复用个人真实账号。[密码存储说明](https://docs.spring.io/spring-security/reference/features/authentication/password-storage.html)

`/api/me`和Service的身份解析遵循同一条链：Controller接收框架的Authentication→取 `getName()`→MyBatis查当前账号→检查存在且enabled→得到id与固定role。返回前专门构造 `{id,username,role}`，不返回AppUserRow整个对象。第一版禁止更改username，并在每次业务请求回查账号是否启用，避免把登录时的资料永久视作最新。

这一做法使停用账号在业务层被拒绝，但“登录会话立即被集中注销”属于另一项功能，不能声称已经实现。角色和权限最终以本次服务端解析结果为准。

**最短人工验收顺序：** 匿名GET工单401→GET令牌200→带令牌和正确表单密码登录204→重新GET令牌200→GET当前用户200→带令牌创建201→不带令牌创建403→带令牌退出204→GET工单401。登录和退出后CSRF可能建立新的匿名会话；存在Cookie本身并不代表已登录。

**常见排错：** 登录302通常是没有配置JSON/204成功处理；登录200但响应是HTML可能是fetch跟随了跳转；一直401查password_hash前缀、UserDetailsService、enabled、Cookie；GET成功POST403查CSRF；IDE报 `javax.servlet` 找不到，当前代码应使用 `jakarta.servlet`；不要为修一个包名降级整套框架。

## 第13周答案和权限条件

**13.1 工程师角色够不够？** 不够。同为ENGINEER的两个人也不能处理对方的任务；必须再比较数据库中的assigneeId和服务器当前用户id，且状态须为IN_PROGRESS、版本匹配。报修人验收同理。

**13.2 total为何也要过滤？** total是对数据库内容的统计，也会透露“有多少我看不到的记录”，并使分页不准确。列表、count、导出、统计、评论、日志都属于数据出口，应遵循同一可见范围。

**13.3 JSON伪造身份怎么处理？** 创建DTO里没有reporterId，操作DTO里没有actorId；忽略或拒绝这些额外字段，不让它们参与身份决定。真正的reporterId、日志actorId来自会话绑定账号。URL里传来的id也只是目标工单编号，不是访问许可。

### 权限矩阵参考

| 功能 | REPORTER | ENGINEER | ADMIN |
| --- | --- | --- | --- |
| 创建 | 仅以本人身份创建 | 不允许 | 不允许 |
| 列表与详情 | 本人报修单 | 分配给本人 | 全部 |
| 评论与日志读取 | 可见工单 | 可见工单 | 全部 |
| 发评论 | 可见工单 | 可见工单 | 全部 |
| 派单 | 不允许 | 不允许 | OPEN单 |
| 提交处理 | 不允许 | 本人IN_PROGRESS单 | 不允许 |
| 验收或退回 | 本人RESOLVED单 | 不允许 | 不允许 |
| 设备新增与停用 | 不允许 | 不允许 | 允许 |

设备启用列表可供已登录用户查看，以便选择报修设备；停用设备不允许新报修，但历史工单仍显示原设备信息。管理员“权限多”不代表跳过既定流程。

下面是**可见性判断局部逻辑**，假定actor为服务器解析的当前用户，ticket为数据库工单，二者id类型按示例为long与可空Long，role为字符串：

```java
boolean visible = switch (actor.role()) {
    case "ADMIN" -> true;
    case "REPORTER" -> ticket.getReporterId() == actor.id();
    case "ENGINEER" -> java.util.Objects.equals(ticket.getAssigneeId(), actor.id());
    default -> false;
};
if (!visible) {
    throw new ForbiddenException("没有访问这张工单的权限");
}
```

这里 `ForbiddenException`是你自己定义并由Advice映射403的运行时异常；不要让它落入通用500处理。比较两个Long对象时不能直接用 `==`判断数值；示例reporterId与long比较会拆箱，但仍要求数据库非空约束，实际代码也可统一使用Objects.equals。

列表不能“先查全量再用Java删除不可见的几条”，那样分页和total容易错误。把服务端构造的范围一起传给Mapper。下面是**加入第10周公用WHERE的XML片段**，role与currentUserId必须是服务器计算结果，不能绑定前端同名查询参数：

```xml
<choose>
  <when test="role == 'ADMIN'">
    AND 1 = 1
  </when>
  <when test="role == 'REPORTER'">
    AND reporter_id = #{currentUserId}
  </when>
  <when test="role == 'ENGINEER'">
    AND assignee_id = #{currentUserId}
  </when>
  <otherwise>
    AND 1 = 0
  </otherwise>
</choose>
```

没有角色的请求应在更前面被拒绝；默认零行仍是防止意外扩大范围的最后一道约束。添加带表别名的JOIN后，相应列都加同样别名，避免同名列歧义。

resolve的更新除状态和版本外还带 `AND assignee_id=#{currentUserId}`；accept/reject带 `AND reporter_id=#{currentUserId}`。角色检查不能省略，例如ADMIN不能仅因恰巧某字段等于自己的id就代为验收。

### 本周独立验收用例

在原始样本上用不同会话完成：

| 请求 | 会话 | 预期 |
| --- | --- | --- |
| GET `/api/tickets/101` | reporter_a | 200 |
| GET `/api/tickets/103` | reporter_a | 403 |
| GET `/api/tickets?page=1&size=10` | reporter_a | 只有101和102，total=2 |
| GET `/api/tickets?page=1&size=10` | engineer_a | 只有102，total=1 |
| GET `/api/tickets/103/comments` | reporter_a | 403，不能只因“评论为空”返回200 |
| POST `/api/tickets/101/assign` | reporter_a | CSRF有效时403 |
| POST `/api/tickets/101/assign` | admin_a | 工程师2且版本正确时200，返回新状态和版本 |
| POST `/api/tickets/102/resolve` | 第二名工程师 | CSRF有效时403，无数据变化 |
| POST `/api/tickets/102/resolve` | engineer_a | content与版本正确时200，返回新状态和版本 |
| POST `/api/tickets/102/accept` | reporter_b | CSRF有效时403 |
| POST `/api/tickets/102/accept` | reporter_a | 当前版本正确时200，再次操作409 |

版本必须从当前详情响应读取，不能一直用初始0。核对日志actorId分别为3、2、1，不能由请求体伪造。测试403时必须先使CSRF正确，否则测试到的是令牌拒绝，不能证明资源权限有效。

权限拒绝、状态冲突和数据库回滚都应有可观察证据；到第15周再把这些用例转换成自动测试。能在不看参考答案时独立增加一个“仅本人可读取”的子资源接口，才算理解了这周的核心。
