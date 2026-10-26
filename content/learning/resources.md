{
  "title": "资料索引与排错手册",
  "description": "按阶段查官方资料、选择兼容版本，定位Java、SQL、Web和AI调用问题。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 80,
  "group": "tools",
  "draft": false,
  "lastmod": "2026-10-26T00:00:00+08:00"
}

这份索引用来在自学时快速找到当前任务需要的材料。一次只打开当前主题的章节，优先用项目中的小实验验证理解。原资料入口整理于2026年10月12日，路线于2026年10月26日调整；外部网站内容和版本可能继续更新，正文练习不依赖付费课程。

## 按阶段选择资料

| 编号 | 资料 | 什么时候读什么 |
| --- | --- | --- |
| R01 | [Dev.java 学习入口](https://dev.java/learn/) | 第1—3周读对象、集合、异常；第14周再读线程主题。英文概念先与本包中文解释对照 |
| R02 | [Pro Git 中文版](https://git-scm.com/book/zh/v2) | 第1周看起步与Git基础；先学status、diff、add、commit、log，后面再学分支 |
| R03 | [Maven 入门](https://maven.apache.org/guides/getting-started/index.html) | 第3周看pom、标准目录、compile/test/package；不先研究自定义插件 |
| R04 | [MySQL 教程](https://dev.mysql.com/doc/refman/8.0/en/tutorial.html) | 第4—5周看连接、建表、查询、多表与聚合；完成自己的SQL而不是通读整本手册 |
| R05 | [Connector/J 兼容说明](https://dev.mysql.com/doc/connector-j/en/connector-j-versions.html) | 第6周连接前核对JDK、数据库服务端与驱动版本，不把动态最新驱动当作旧服务器必然兼容 |
| R06 | [Spring REST 入门](https://spring.io/guides/gs/rest-service/) | 第7周观察请求参数如何变成JSON响应，再改成工单接口 |
| R07 | [Spring Boot 系统要求](https://docs.spring.io/spring-boot/system-requirements.html) | 创建Web项目时核对正式版本、Java和构建工具要求 |
| R08 | [MyBatis Spring Boot Starter](https://mybatis.org/spring-boot-starter/mybatis-spring-boot-autoconfigure/) | 第8周看兼容表、Mapper、配置与XML示例 |
| R09 | [Spring Security 用户名密码认证](https://docs.spring.io/spring-security/reference/servlet/authentication/passwords/index.html) | 第12周理解框架认证、UserDetailsService和密码编码 |
| R10 | [Spring Security CSRF](https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html) | 第12周按页面形态处理token，并理解登录后刷新token |
| R11 | [Spring Boot 测试](https://docs.spring.io/spring-boot/reference/testing/index.html) | 第15周使用当前Boot版本配套的测试组件，确认测试职责 |
| R12 | [Docker Compose 入门](https://docs.docker.com/compose/gettingstarted/) | 第17周再学服务、网络、数据卷；容器化之前先让jar能启动 |
| R13 | [Hello 算法](https://www.hello-algo.com/) | 每周基础时间阅读对应数据结构，选择Java示例；不必追求一次读完 |

资料网站提供阅读入口。需要离线时，使用网站自身提供的下载入口或浏览器保存所需页面；保留出处，不把下载材料当作自己原创内容。此包已包含中文任务解释和自测答案，但没有内嵌第三方整本书或视频。

## 环境清单

| 阶段 | 必须具备 | 先怎样确认 |
| --- | --- | --- |
| 第1周 | JDK、编辑器或IDE | 编译运行一个只有main的类；不要用运行README判断Java环境 |
| 第3周 | Java21、Git、Maven | `java -version`、`javac -version`、`git --version`、`mvn -v`，Java路径一致 |
| 第4周 | 可连接的MySQL练习库 | 客户端能执行`SELECT VERSION();`；能创建和查询自己练习库的表 |
| 第7周 | Web项目依赖和空闲端口 | 先启动最小接口，再接数据库与页面 |
| 第12周 | 三角色演示账号 | 密码由框架编码；测试账号只用于本地练习 |
| 第17周 | 可运行jar的环境 | 本机/本地Linux均可；Docker与云主机不是第一阶段前置条件 |

工具下载从[Temurin JDK](https://adoptium.net/temurin/releases/)、[Maven](https://maven.apache.org/download.cgi)、[Git](https://git-scm.com/downloads)与[MySQL](https://dev.mysql.com/downloads/)各自入口选择。已有可用工具先复用，不重复安装多个版本。教学不要求购买IDE；是否支持某个便捷界面不会改变Java命令行构建的原理。

IDEA中的项目SDK、终端PATH和Maven使用的Java可能不同。终端显示Java8而项目配置写Java21时，先找到实际安装路径，并让本项目明确使用Java21。确认配置后重开终端再检查，不要仅修改语言级别就认为JDK已经切换。

## 固定版本的方法

在项目README记录Java、Maven、Spring Boot、MyBatis Starter、MySQL服务端和Connector/J版本。沿用Java21和当前MySQL8.0.44；进入Web时按[MyBatis兼容表](https://mybatis.org/spring-boot-starter/mybatis-spring-boot-autoconfigure/)选择匹配的Boot/Starter正式版本，不把旧教材补丁号当作当前安装情况。只使用正式版本，学习期间不因“出现新版本”频繁升级。

Spring Boot管理的依赖优先跟随其依赖管理清单。若使用本机MySQL8.0练习，仍须核对被选中的驱动能否连接8.0；使用较新驱动不能自动推导为旧服务端兼容。课程JDBC阶段若指定驱动版本，按该阶段说明核对；进入Web阶段再检查实际依赖树。升级另建练习环境，不直接替换其他项目的数据库。

## 排错顺序

先记下“在哪一步失败”：编辑/编译、程序启动、收到请求、执行SQL、浏览器展示。按层检查比同时改很多配置有效。

| 现象 | 优先检查 | 最小验证 |
| --- | --- | --- |
| 没有Java Class创建选项 | src是否被识别为源码目录；项目SDK是否设置 | 在源码目录新建普通类，确认能够编译 |
| 找不到或无法加载主类 | 类名、包名、编译输出目录、classpath | 先运行只有main的TicketDemo |
| `release version 21 not supported` | Maven实际使用的JDK | 对比`java -version`与`mvn -v`中的Java版本 |
| `UnsupportedClassVersionError` | 编译版本高于运行版本 | 用同一个Java21编译、运行 |
| Maven无法下载依赖 | 网络、仓库响应、版本是否存在、错误日志 | 先重试一个最小项目；不要随意复制来历不明的仓库配置 |
| 文件找不到 | 运行工作目录与实际Path | 打印`path.toAbsolutePath()`，确认目标文件 |
| 中文乱码 | 源文件、读写流、终端的编码 | UTF-8写一行再UTF-8读回，分开判断文件与显示问题 |
| 加载后数据翻倍 | 是否向同一列表重复追加 | 用两条记录连续加载两次，观察列表长度 |
| 数据库连接被拒绝 | 服务是否启动、主机、端口、网络 | 数据库客户端用相同主机端口连接 |
| Access denied | 用户名、密码、来源主机及权限 | 用同一账户在客户端连接，不在日志打印密码 |
| 表或列不存在 | 当前数据库、建表脚本、命名 | `SELECT DATABASE();`与`SHOW CREATE TABLE ticket;` |
| MyBatis查到但字段为空 | 列名与属性映射、构造方式、getter | 只查id和title两列，确认resultMap或映射策略 |
| Mapper重复注册 | 扫描范围、多个配置、重复Bean | 保留一种明确的扫描方式，阅读启动错误中的Bean名 |
| 404 | 请求路径、方法、Controller扫描包 | 对照启动映射和最小GET接口 |
| 400 | JSON格式、Content-Type、字段类型与校验 | 发送文档中的最小合法JSON |
| 401 | 是否登录、Cookie是否随请求发送 | 查看登录响应和下一次请求的Cookie |
| 403 | 权限是否允许、CSRF是否缺失/过期 | GET与POST分开试；检查token与Cookie，不直接关闭防护 |
| 页面能看到按钮但接口拒绝 | 前端展示不代表服务端授权 | 在HTTP客户端复现，按用户身份检查规则 |
| 事务没有回滚 | 调用是否经Spring代理、是否吞掉异常、多个写操作是否共用事务 | 在日志写入前故意抛运行时异常，仅在练习库检查两处均未提交 |
| 两次派单都成功 | SQL是否含状态/版本条件，是否检查影响行数 | 从相同初始版本分别发送请求并检查最终记录 |
| 端口占用 | 旧程序仍在运行或配置冲突 | 找到自己的旧实例正常停止，或给练习实例换端口 |
| 关闭程序后数据没了 | 是否仍在用内存实现或容器临时层 | 确认实际连接的库与持久化位置，重启前后查询同一库 |

不要用删除数据库、删除数据卷、关闭权限校验或把所有异常忽略作为通用修复手段。先保留复现证据，确认错误原因后只修改必要部分。

## 看答案后仍不理解

把解释拆成三句话：输入是什么、这一行改变了什么、输出或异常是什么。用两个不同的输入手工执行一遍。比如构造器调用校验方法，是让创建与修改遵守相同规则；`private`本身不会判断数值范围。

每次看完参考代码，关闭它并改变一项需求：标题上限、筛选条件、状态操作或查询字段。能根据变化调整实现，才算从复制过渡到理解。

## AI接入时才需要的资料与排错

先读所选提供方的官方API文档，核对请求协议、模型名、结构化输出支持、错误码、用量字段与计费；目前提供方未选择，key/端点/预算仍待配置。Java客户端先查[JDK21 HttpClient](https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/java/net/http/HttpClient.html)，不必先安装Agent框架。

概念参考：[结构化输出与校验](https://docs.spring.io/spring-ai/reference/api/structured-output/converters.html)、[应用端工具执行](https://docs.spring.io/spring-ai/reference/api/tools.html)。这些链接用于理解，并不代表项目已安装Spring AI。

| 现象 | 先检查 | 验证边界 |
| --- | --- | --- |
| 模型401/403 | key是否配置、端点与账号模型权限；不打印key | 记录错误类别，人工业务继续 |
| 429/5xx/超时 | 额度、限流、服务状态、总超时与重试次数 | 用本地替身验错误分支，真API另记结果 |
| 返回非JSON或缺字段 | 提供方协议、输出schema、Java解析与校验 | 原始失败脱敏留样，不把文本直接写库 |
| 看似正确但事实不符 | 输入事实、模糊信息、prompt版本 | 纳入固定评估集，不用一次成功掩盖错误 |
| 用量/费用缺失 | 提供方是否返回用量、价格和币种来源 | 标未知或有依据估算，不能填0当免费 |
| Agent查到别人数据 | 工具是否真正复用Service授权、会话身份和范围 | 先关闭工具入口并修权限，模型提示词不能代替鉴权 |
