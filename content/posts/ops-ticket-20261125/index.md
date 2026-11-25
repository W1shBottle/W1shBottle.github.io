---
title: "设备运维工单开发 — 17 Spring Security 数据库登录与接口角色授权"
description: "承接数据库派单练习，接入 Spring Security，从内存账号过渡到 MySQL app_user 表认证，完成方法级角色授权、CSRF 排错与 401/403/404 分层验证。"
date: 2026-11-25T00:00:00+08:00
draft: false
tags: ["Java", "设备运维工单", "Spring Boot", "Spring Security", "MyBatis", "MySQL", "学习笔记"]
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 17
chapter_title: "Spring Security 数据库登录与接口角色授权"
---

> 接续[上一篇：创建事务、仓库分层与数据库派单](/posts/ops-ticket-20261115/)。这篇合并整理上一篇之后尚未归档的认证与授权学习（含 26 日凌晨的收尾验证）：从引入 Spring Security 默认登录起步，经历密码哈希、内存账号配置，最终切到 MySQL `app_user` 表登录，并给派单接口补上角色限制与 CSRF 排错。

## 1 为什么紧接着补认证与授权

上一篇做完数据库派单时，SQL 里的 `EXISTS` 只检查了**被派单的人**是不是已启用的工程师，却没有检查**发起派单的人**是谁、有没有管理员权限。

接入 `spring-boot-starter-security` 之后，请求在进入 Controller 之前会先经过两道关：

| 关卡 | 解决什么问题 | 没通过时的典型状态码 |
| --- | --- | --- |
| **身份认证（Authentication）** | 确认“你是谁”（账号密码或会话是否有效） | `401 Unauthorized` |
| **角色授权（Authorization）** | 确认“你能不能调这个接口”（角色是否满足规则） | `403 Forbidden` |

在 `DatabaseTicketController.findSummary()` 中注入 `Authentication authentication` 后，用断点可以看到 `authentication.getName()` 取出当前登录用户名，`authentication.getAuthorities()` 取出当前用户拥有的权限条目（例如密码认证产生的 `FACTOR_PASSWORD`，以及角色对应的 `ROLE_ADMIN`、`ROLE_REPORTER`）。

## 2 方法级角色检查：`@EnableMethodSecurity` 与 `@PreAuthorize`

为了让角色规则直接贴在具体接口方法上，需要两处配合：

1. 在启动类 `OpsTicketApplication` 上加 `@EnableMethodSecurity`，开启方法级权限检查。
2. 在 Controller 方法上加 `@PreAuthorize(...)`：

~~~java
@GetMapping("/api/db/tickets/{id}")
@PreAuthorize("hasAnyRole('ADMIN', 'REPORTER')")
public TicketSummary findSummary(
        @PathVariable(name = "id") long id,
        Authentication authentication
) { ... }
~~~

这里经历了从单角色到多角色的两次验证：
- 先写 `@PreAuthorize("hasRole('ADMIN')")`：默认临时账号 `user` 密码正确，但没有 `ADMIN` 角色，Apifox 返回 `403`；给它配置 `ADMIN` 角色后，权限集合出现 `ROLE_ADMIN`，再次查询返回 `200`。
- 改成 `hasAnyRole('ADMIN', 'REPORTER')` 后，管理员和报修人两个角色都能查询，工程师角色则仍会被拦成 `403`。

## 3 密码哈希与内存账号：`PasswordEncoder` 与 `UserDetailsService`

数据库不能存明文密码。我先通过 `PasswordEncodingDemo` 练习了 `PasswordEncoder` 接口及其实现类 `BCryptPasswordEncoder`：
- `encode(原密码)`：生成以 `$2a$10$...` 开头、自带盐值的 BCrypt 哈希字符串；
- `matches(输入密码, 已保存哈希)`：把输入明文按同样算法和盐重新计算后比对，返回 `true` 或 `false`。

随后在 `cn.wishbottle.opsticket.config` 包下建立 `DemoSecurityConfig`（最初误放到 `src/test/java` 下，发现正常运行加载不到后移回了 `src/main/java`），先用内存账号 `demo-admin`、`demo-reporter` 跑通了角色区分。这一步理清了三个核心类型：

| 类型 | 作用 | 类比项目里的工单仓库 |
| --- | --- | --- |
| `UserDetails` | 装单个用户的用户名、密码哈希、角色和启用状态 | 单条工单对象 |
| `UserDetailsService` | 接口，规定“按用户名查用户”：`loadUserByUsername(username)` | `TicketRepository` 接口 |
| `InMemoryUserDetailsManager` | Spring 自带的内存实现类，从内存查账号 | `InMemoryTicketRepository` |

## 4 查清 MySQL `app_user` 表与占位密码陷阱

内存账号重启即失，也和业务表脱节，接下来要把用户来源切到 MySQL 的 `app_user` 表。

我先在 IDEA 右侧 Database 面板配置好本机 `ops_ticket_dev` 数据源，在 Query Console 中执行 `SELECT` 核对当前 4 条记录：`reporter_a`、`engineer_a`、`admin_a`、`reporter_b` 均已启用，但 `password_hash` 列全部是初始化脚本留下的占位字符串 `NOT_A_LOGIN_HASH`。

这里纠正了一个容易想当然的理解：为什么把 `NOT_A_LOGIN_HASH` 交给 `BCryptPasswordEncoder.matches()` 一定会失败？不是因为程序“看得懂这是占位文本”，而是因为 **`matches()` 不是明文字符串 `equals()` 对比**——它要求已保存值必须符合 BCrypt 哈希格式。哪怕登录时故意输入密码 `"NOT_A_LOGIN_HASH"`，`matches()` 也会直接返回 `false`。

## 5 编写 `AppUser`、`UserMapper` 与 `DatabaseUserDetailsService`

把数据库查用户拆成三块逐步实现，过程中暴露并修正了几处细节问题：

1. **`AppUser`（`dto` 包）**：承接 `app_user` 查出的一行 5 列数据。
   - **修正记录**：初版漏写了字段的 `private`、把 `BIGINT` 的 `id` 写成了 `int`，还把 `password_hash` 直接照抄成带下划线的字段名和 `getPassword_hash` / `getpasswordHash`。项目开启了 `mybatis.configuration.map-underscore-to-camel-case=true`，MyBatis 会按 JavaBean 规范找驼峰方法 `setPasswordHash(...)`，且 Java 区分大小写；全部修正为 `private long id` 与 `passwordHash` / `getPasswordHash()` / `setPasswordHash(...)` 后才通过核对。
2. **`UserMapper`（`mapper` 包）**：按用户名查单条记录。
   - **修正记录**：初版 `WHERE` 条件误写成 `user_name`（表里实际列名是 `username`），返回类型也误写成 `String`；修正为 `WHERE username = #{username}` 且返回 `AppUser`。
3. **`DatabaseUserDetailsService`（`config` 包）**：自己实现 `UserDetailsService` 接口，通过构造器注入 `UserMapper`：

~~~java
@Service
public class DatabaseUserDetailsService implements UserDetailsService {

    private final UserMapper userMapper;

    public DatabaseUserDetailsService(UserMapper userMapper) {
        this.userMapper = userMapper;
    }

    @Override
    public UserDetails loadUserByUsername(String username) {
        AppUser appUser = userMapper.findByUsername(username);
        if (appUser == null) {
            throw new UsernameNotFoundException("用户不存在：" + username);
        }
        return User.withUsername(appUser.getUsername())
                .password(appUser.getPasswordHash())
                .roles(appUser.getRole())
                .disabled(!appUser.isEnabled())
                .build();
    }
}
~~~

这一步有两个关键点：
- **`UserMapper` 和 `AppUser` 的关系**：`UserMapper` 负责发 SQL 去 MySQL 查一行数据；MyBatis 自动 `new AppUser()` 并调用各 setter 装入 5 列，作为 `findByUsername()` 的返回值交回给 `DatabaseUserDetailsService`。
- **不能二次加密**：数据库里存的本来就是 BCrypt 哈希，放进 `.password(...)` 时绝不能再套一层 `encoder.encode(...)`，否则会变成双重哈希，任何明文密码都无法匹配。

删掉 `DemoSecurityConfig` 中的内存 `userDetailsService` Bean、仅保留 `passwordEncoder()` Bean（供 Spring Security 登录时调用 `matches()` 核对密码）后重启应用：用昨天的旧内存账号 `demo-admin` 请求 `GET /api/db/tickets/1` 返回 `401`，证明登录已真正切换到 MySQL。

随后我用 `PasswordEncodingDemo` 生成一串本地练习密码对应的真实 BCrypt 哈希，通过带 `WHERE` 条件的 `UPDATE` 写入 `admin_a` 和 `engineer_a` 两行。**没有重启 Java 程序**，直接用 Apifox 访问 `GET /api/db/tickets/1`，三组账号一次跑通：
- `admin_a` → **`200`**（数据库实时查到最新哈希，且拥有 `ADMIN` 角色）；
- `engineer_a` → **`403`**（认证通过，但 `findSummary` 只允许 `ADMIN` / `REPORTER`）；
- `reporter_a` → **`401`**（`password_hash` 仍是 `NOT_A_LOGIN_HASH`）。

## 6 派单接口角色限制与 CSRF 排错

给 `POST /api/db/tickets/{id}/assign` 加上 `@PreAuthorize("hasRole('ADMIN')")` 后，我用 `admin_a` 向不存在的 `999` 号工单发派单请求，本以为会得到 `404`，结果连续收到 **`401`**。

排查后发现两个叠加原因：
1. **Spring Security 默认 CSRF 防护**：`GET` 是只读请求不查 CSRF，但 `POST` 会修改数据；默认的 `CsrfFilter` 排在 `BasicAuthenticationFilter` 之前，Apifox 走 Basic Auth 没带 CSRF Token，在未认证状态就被拦截并转成 `401`。
2. **排查与验证**：在 `DemoSecurityConfig` 新增 `SecurityFilterChain` Bean（配置 `anyRequest().authenticated()`、`httpBasic`，并临时关闭 CSRF——注释写明仅限当前 Basic Auth 接口练习阶段，后续接入浏览器 Session 登录前必须恢复）。改完后通过 Debug 在 `DatabaseUserDetailsService.loadUserByUsername()` 打断点并重启生效，确认查到的 `AppUser` 字段与 `Authorization: Basic ...` 请求头均无误，再次发送 `POST /api/db/tickets/999/assign`：
   - **`admin_a` → `404`**（穿过安全层进入 `assign()`，顺手亲验了工单不存在的 `404` 分支）；
   - **`engineer_a` → `403`**（身份认证通过，但在进入 `assign()` 查数据库之前就被角色授权拦截）。

这次对比把整条请求链的执行顺序钉死了：
> **① 身份认证（失败 `401`） → ② 角色授权（失败 `403`） → ③ 业务查库与校验（`404` / `409` / `200`）**

## 7 这次完成到哪里与下一步

- **本次亲手完成并验证**：完成 `AppUser`、`UserMapper`、`DatabaseUserDetailsService`、`DemoSecurityConfig`（`PasswordEncoder` + `SecurityFilterChain`）及 `findSummary`/`assign` 的 `@PreAuthorize`；实测 MySQL 账号 `GET` 的 `200 / 403 / 401` 与 `POST /assign` 的 `404 / 403`。
- **同步规划定稿**：同日已将学习主线收口为纯 Java / Spring Boot / MyBatis / MySQL（`A1 → A2 → B01–B09 → C01–C04`，可选 `D01–D02`），原 Python / Redis / Agent 草案条目已归档，既有验收勾选保持不变。
- **尚未完成的边界**：其余接口（列表、创建等）尚未补齐 `@PreAuthorize` 与资源归属授权（如报修人只能看自己的工单）；浏览器 Session 登录、注销与恢复 CSRF 仍待后续实践；`assign` 的 `409`（重复派单/非工程师）失败分支与 `expectedVersion` 乐观锁尚未由本人复验和补齐。
- **下一步**：亲手复验 `POST /api/db/tickets/{id}/assign` 的 `409` 失败分支并解释受影响行数，再给派单补上 `expectedVersion` 乐观锁校验。

继续查看[学习进度](/learning/#progress)、[技能清单](/learning/checklists/)和[项目设计](/learning/project-design/)。
