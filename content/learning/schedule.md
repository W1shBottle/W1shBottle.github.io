{
  "title": "Java工单与Python Agent阶段学习计划",
  "description": "Java工单与Python基础并行，逐步完成模型调用、只读Agent和安全联调。",
  "date": "2026-10-12T12:00:00+08:00",
  "weight": 20,
  "group": "start",
  "draft": false,
  "lastmod": "2026-11-15T00:00:00+08:00"
}

更新：2026-11-15。继续设备运维工单项目；不删除既有代码、不把Java整体改写为Python。每天约3小时、每周弹性安排；下列阶段和学习次数是拆分参考，不是完成期限。

**Java工单后端（A）与Python基础（Y）并行 → Python模型调用（B）→ 只读Agent（G）→ 知识检索与评测（C）→ 按条件与Java联调。** A/Y并行；B/G使用假数据即可提前练习。真正连接受限的用户工单数据前，Java端和服务间必须完成身份、资源范围和接口授权。评测从第一次模型调用开始。

## 当前进度与证据

截至2026-11-15：文件版Web已有查询和创建；数据库练习接口已有查询、创建及派单。学习者11月9日跟练创建POST并得到id=9；11月13日助手补充创建事务，隔离H2运行25项JUnit与17个Demo，不代表本人独立掌握或真实MySQL复测。11月15日学习者按指导完成派单链路，并在隔离H2用Apifox反馈成功派单和回查符合预期；失败分支本人练习、操作人认证授权、完整版本冲突、解决/验收、Python Agent与真实模型调用仍待完成。

2026-11-15学习者反馈：已经看过黑马Python+AI课程第1—119集，但很久没有写，需要少量复习。课程目录涵盖Python基础、函数/异常、HTTP、模型调用、Streamlit与会话管理；观看不等于已跟练、独立掌握或本工单项目已实现。

`/api/tickets`仍使用文件仓库；`/api/db/tickets`是数据库练习接口。派单HTTP成功路径已由学习者在隔离H2练习；本人失败分支和真实MySQL隔离集成仍待验证，也不把助手的隔离测试算为独立掌握。

## 项目要做成什么样

用户说：“查一下我的打印机工单，告诉我当前进度，并根据设备资料给出可参考的下一步。”

1. Java工单系统负责用户、工单、MySQL、业务校验和授权，提供明确的只读接口。
2. Python负责模型调用、工具选择、任务步骤、结果整合和引用；不直接执行任意SQL或更改工单。
3. 资料和工单无法确定时提示缺少信息；有多条结果就追问。模型回答标注工单编号、资料来源及限制。
4. 简单页面或HTTP工具展示问题、步骤和答案即可，不依赖复杂前端或真实设备。

首个实验只用自造假数据；Java和Python的HTTP联调放到双方各自能跑后。Java接口仍未有权限时，只能使用本机隔离演示数据，不能标榜“已保障用户权限”或接入真实敏感数据。

## 阶段与验收

| 阶段 | 亲手交付 | 达标证据 |
| --- | --- | --- |
| A Java工单业务 | 读懂现有事务与数据库创建；逐步完成派单、状态与必要鉴权 | 能独立画请求链并解释回滚；派单接口、失败分支及授权按实际结果记录 |
| Y Python复习与应用 | 课程已看到119集；选择字典/函数等少量复习，并用虚构工单写查询 | 恢复编码手感、能修改查询；基础不熟时再回看，不重刷整个课程 |
| R Redis核心与项目实践 | 学数据结构、过期、Python连接；逐步加虚构工单缓存和Agent会话记忆 | 自己解释命中/失效、回源与会话隔离，验证过期与Redis不可用的处理 |
| B Python模型调用 | 先用虚构数据请求一个模型，返回摘要和待补充信息；模拟错误 | 保存真实调用与模拟测试各一份证据，校验结构、超时与错误；没有API时仅标契约测试 |
| G Python只读Agent | 先对假数据接查询工具，完成查找→追问/详情→回答，记录步骤 | 真实模型发出工具调用、Python执行；无结果、坏参数、超时和步数限制可复现 |
| C 资料与评测 | 维护少量自编设备资料，检索并引用；用固定任务集改进 | 引用可定位；区分检索、工具、生成错误，记录真实样本数、耗时与用量 |
| L 安全联调 | Java提供经授权的只读工单接口，Python通过HTTP调用 | 隔离演示数据、真实身份与授权已验证；无权请求不能读取；超时/故障可解释 |


## 接下来的六个学习单元

每单元可拆成多次；根据遗忘程度调整复习量，不要求先学完所有Python语法再做项目。Java与Python并行，下面是建议先后，不是固定工期。

| 顺序 | Java项目任务 | Python / Agent任务 | 可观察的结果 |
| --- | --- | --- | --- |
| 1 | 读DatabaseTicketRepository.create，理解请求链和回滚 | 少量回看P52字典、P58函数，用已有环境和虚构工单练一次查询 | 能根据编号返回工单或查无结果；忘记了就随时回看与提问 |
| 2 | 回顾派单Controller、Service、Repository和Mapper，画出调用链 | 把查询整理成 `find_ticket(ticket_id)` 只读工具，处理缺失与非法输入 | 普通查询和无结果可复现，不访问真实工单 |
| 3 | 在隔离环境练习派单失败分支，解释400/404/409 | 复用已有模型调用代码或环境；必要时回看已看过的P98，用假工单生成摘要 | 真调用、模拟结果或未配置分别标记，API失败可解释 |
| 4 | 继续设计派单权限与版本冲突，保留真实库数据 | 看工具调用视频，接入受限工具：模型请求→程序校验执行→结果反馈 | 有模型发起的工具调用和最终答案，限制次数与超时 |
| 5 | 继续补授权和错误处理 | 并行学Redis基础；后续分别练设备缓存和会话记忆 | 先弄懂TTL和数据结构，初版Agent仍可使用内存 |
| 6 | 完成联调所需的认证与资源授权 | 需要HTTP时补FastAPI；再做资料检索与评测 | 假数据先行，真实工单须具备可信身份与授权 |

**下一次亲手做：** 先用已看过的Python课程少量复习字典和函数，再用2—3条虚构工单写find_ticket查询和查无结果；根据实际卡点回看对应章节。随后复用或按需要搭建模型客户端，让模型请求只读工具、程序执行并回传结果。Java线先在隔离环境练习派单失败分支，继续理解创建事务与影响行数，不接入真实敏感数据。

## 按阶段看网课与做练习

学习方式：每次只安排当前任务相关的1—2集，给出视频链接、分P、时长和要留意的问题；看完由学习者反馈、提问，再回到现有工单项目独立做小练习。下面时长约数仅为视频播放时长，不含暂停和练习；不要求从头看完大课。看过、跟练和能独立完成分开记录。以下是依据公开简介和选集目录筛选，当前环境受B站访问限制，未逐段播放；若选集顺序或时长变化，以标题为准。配套付费服务不作为学习前提，安装与API版本以官方文档和本机环境为准。

1. **现在：Java事务，先看一集。** 黑马JavaWeb [P101「事务管理-介绍与操作」](https://www.bilibili.com/video/BV1yGydYEE3H/?p=101)约20分钟；接着看 [P102「Spring事务管理-介绍」](https://www.bilibili.com/video/BV1yGydYEE3H/?p=102)约16分钟。看后对照 `DatabaseTicketRepository.create`，画POST→Service→Repository→Mapper→MySQL调用链，说出出错时为什么需要回滚；结合[Spring事务官方说明](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)核对代理和异常规则。先理解，不操作真实业务数据。
2. **现在少量复习：Python字典和函数。** 学习者已看过[黑马Python+AI课程](https://www.bilibili.com/video/BV1sHU9BmEne/)前119集，但很久没有写。可以先回看 [P52「字典介绍」](https://www.bilibili.com/video/BV1sHU9BmEne/?p=52)约20分钟、[P58「函数定义」](https://www.bilibili.com/video/BV1sHU9BmEne/?p=58)约13分钟，分次观看；P37列表、P59参数与返回值、P86异常、P112 JSON按实际卡点再查。用2—3条虚构工单写 `find_ticket(ticket_id)`，能返回结果和查无结果即可。若已有课程代码或可用环境，优先复用；虚拟环境在需要隔离依赖时参考[官方venv文档](https://docs.python.org/zh-cn/3/library/venv.html)，不要求重装Python。模型调用P98也已看过，做摘要时需要再回看。
3. **可与Python复习并行：Redis基础（R01）。** 选择黑马Redis课的 [P4「认识Redis」](https://www.bilibili.com/video/BV1cr4y1671t/?p=4)约7分钟、[P9「通用命令」](https://www.bilibili.com/video/BV1cr4y1671t/?p=9)约12分钟、[P10「String类型」](https://www.bilibili.com/video/BV1cr4y1671t/?p=10)约13分钟；分次再看 [P12 Hash](https://www.bilibili.com/video/BV1cr4y1671t/?p=12)约12分钟、[P13 List](https://www.bilibili.com/video/BV1cr4y1671t/?p=13)约15分钟。学完在隔离环境用假数据练 `SET/GET/EXPIRE/TTL`、`HSET/HGETALL`、`RPUSH/LRANGE`，预测并观察过期。课程录于2022年，基础概念仍可参考；安装、客户端和版本以届时官方文档为准，不照搬Linux安装到Windows，也不需要现在安装。
4. **准备连接服务时：Python访问Redis（R02）。** 看 [Python操作Redis P9](https://www.bilibili.com/video/BV16vFPevEt6/?p=9)约15分钟，随后参照[Redis官方redis-py入门](https://redis.io/docs/latest/develop/clients/redis-py/)完成假数据读写、过期、连接超时和错误处理；理解返回bytes与字符串的区别。服务暂不可用时记录错误，不把模拟结果算成真实连接。
5. **有Java查询后：工单缓存（R03）。** 看黑马Redis课的 [P35「什么是缓存」](https://www.bilibili.com/video/BV1cr4y1671t/?p=35)约10分钟、[P36「添加商户缓存」](https://www.bilibili.com/video/BV1cr4y1671t/?p=36)约14分钟，再看 [P38「缓存更新策略」](https://www.bilibili.com/video/BV1cr4y1671t/?p=38)约26分钟。模仿思路给隔离的虚构设备查询加缓存：先读Redis，未命中读MySQL并设置TTL；更新MySQL后删除对应缓存；Redis故障回落数据库。按[官方Cache-Aside说明](https://redis.io/docs/latest/develop/use-cases/cache-aside/)说明并发时可能出现短暂不一致，TTL只是兜底，不声称强一致。真实私有工单需先认证授权，不能用公共缓存键绕过权限。
6. **完成假数据Agent后：会话记忆（R04）。** 用Python的 `redis-py` 将虚构对话按session分开存入List、限制长度并设置TTL，验证对话顺序、会话隔离、过期和Redis不可用时的短暂内存降级或明确错误；这只是上下文记忆练习，不等于永久保存或已具备身份授权。初版模型调用和只读Agent可以先用内存完成，不必等Redis。
7. **后续需要HTTP和Agent时。** FastAPI先看 [P3「第一个程序」](https://www.bilibili.com/video/BV1rgd3B6ErE/?p=3)约19分钟，再按需看[P7路径参数](https://www.bilibili.com/video/BV1rgd3B6ErE/?p=7)和[P11请求体](https://www.bilibili.com/video/BV1rgd3B6ErE/?p=11)，只做假工单查询接口。模型调用已在课程中看过，结合已有代码按需回顾；工具调用可参考LangChain课的 [P6「模型调用」](https://www.bilibili.com/video/BV15jug6yEyM/?p=6)、[P13「结构化输出」](https://www.bilibili.com/video/BV15jug6yEyM/?p=13)、[P14「工具调用」](https://www.bilibili.com/video/BV15jug6yEyM/?p=14)；框架版本变化时查[官方Agent文档](https://docs.langchain.com/oss/python/langchain/agents)，不为了看课一次装完全部依赖。

Redis先掌握上述基础和两个实际场景；集群、分布式锁、消息队列、底层源码与性能调优等在具体岗位或项目需要时再扩展，不与首个Agent串行绑定。

## Python复习与衔接Agent

已看过课程第1—119集，距上次编码较久；先复习实际要用到的字典、列表、函数与异常，在假工单查询里恢复手感。别为凑时长重复看变量、循环等基础，遗忘时再查对应章节或直接提问。

用现有代码或环境回顾模型请求/响应和JSON，然后做一个查询工具，让模型通过工具调用获取虚构工单。Python项目中的独立实践、真实调用和课程观看分开记录。FastAPI、依赖隔离等在实际需要时补，不阻挡第一个只读Agent。

## B/G：先做可运行的小Agent

1. Python内存里构造假工单，写 `find_ticket(ticket_id)` 和 `list_tickets(status)`，正常、无数据、非法参数均能处理。
2. 调用一个模型API：先让它理解用户问题并输出摘要，再让它实际请求一个工具；由Python按工具名/参数调用函数，把结果送回模型。
3. 加入有限步数、超时、失败提示和过程记录。先做一个Agent、一两个只读工具；LangChain可辅助模型/工具集成，LangGraph在确需多步状态时引入。
4. 对话歧义时追问，能展示实际工具调用记录和任务结果。模型输出不是数据库事实，也不自动获得业务权限。

先用假数据不要求真实用户登录；这只是学习原型，不宣传为有权限的业务系统。模型服务能看到发送给它的内容，因此只用虚构样本，key从环境变量获取，不写入代码或日志。

## 与Java联调和权限边界

Python先调用本机、隔离数据上的只读接口，记录HTTP状态、超时及错误，不先做写入。真实多用户场景必须先有Java认证和资源归属校验，以及服务间身份传递；服务端从可信会话或明确设计的服务凭据取得身份，不能信任模型生成的userId。认证缺失时只做假数据实验，不对公网开放开发接口。

需要时再由Java请求Python提供的Agent接口；两个进程带来启动、配置、依赖版本、超时、日志和联调成本，先分别调通，再连接。工具禁止模型拼任意SQL、执行系统命令或任意URL；写工具留到人工确认、重新鉴权、状态和幂等均能验证后。

## 知识检索与评测

准备10—20条自编虚构维护资料，记录资料ID、版本、设备范围、段落。先做关键词检索并给出处，语义效果不足时再试Embedding与向量库；查无依据就说明不足。资料本身不授予权限。

从约12—20条正常、模糊、无结果和错误输入开始，逐步扩展约30条Agent任务，区分开发集与留出集。分别记录检索命中、工具选择和参数、任务完成、引用依据、失败原因、延迟和真实用量/费用；缺费用写未知。先定判断标准，再比较修改前后，不能只保留成功截图。

## 后续按需与求职

Java基础、SQL、Git和常见数据结构继续训练；Redis基础及缓存、会话练习是计划内主线，基础可以与Python复习并行，缓存和会话跟随项目逐步实现。MCP、SubAgent、模型路由、微服务和模型训练在单Agent可靠后按岗位补。Python项目要能独立开发和调试，不能只列框架名。Java方向岗位与Python Agent方向分别对照岗位真实要求；查看届别、到岗天数和实习期，不保证录用。

参考：[Python官方教程](https://docs.python.org/zh-cn/3/tutorial/) · [FastAPI入门](https://fastapi.tiangolo.com/zh/tutorial/first-steps/) · [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents) · [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview)。具体依赖版本在实际接入时确认兼容，不为了追新重装现有Java环境。
