# WishBottle's Blog

这是我的个人博客源码仓库，使用 **Hugo** + [Typo](https://github.com/tomfran/typo) 主题搭建，提供 One Dark 深色主题与暖灰靛蓝浅色主题，搭配圆角卡片和半透明导航。

- 站点地址：<https://wishbottle.cn/>
- GitHub Pages：<https://w1shbottle.github.io/>

## 本地预览

> 使用 Hugo 0.156.0 extended；招聘同步与检查另外需要 Python 3.12 和 Node.js 24。

```bash
hugo version
hugo server -D
```

浏览器打开：`http://localhost:1313/`

## 写文章

新建文章（示例）：

```bash
hugo new content --kind posts posts/my-post
```

这会生成 `content/posts/my-post/index.md`，编辑摘要、标题、标签和正文，写完把 `draft: true` 改为 `false`。文章图片放在同一个目录，使用相对路径引用，例如 `![示意图](memory-layout.png)`。

新文章目录建议使用小写英文与连字符，例如 `java-file-io`；图片使用能说明内容的名称，例如 `student-menu.png`。历史文章目录、图片名和已发布地址保持原样，避免让已有链接失效。单独的 Markdown 页面也受 Hugo 支持，无需为了统一形式迁移已有文件。

需要公式的文章可在头部增加 `math: true`。文章目录和阅读时间由当前站点模板统一展示，不需要添加旧主题的 `ShowToc`、`TocOpen`、`ShowReadingTime` 配置。

## 系列文章标题

带有 learning_series、series_title、series_order 和 chapter_title 的文章，统一使用“系列名 — 两位序号 章节标题”。例如：

```yaml
title: "设备运维工单开发 — 03 多张工单存取与 Demo 自测"
learning_series: "ops-ticket"
series_title: "设备运维工单开发"
series_order: 3
chapter_title: "多张工单存取与 Demo 自测"
```

标题正文只写在 chapter_title，系列名只写在 series_title；序号使用数值。title 同步完整格式，便于 RSS 和社交分享显示一致。模板 post-title.html 统一首页、列表、归档、文章标题和系列内导航的视觉层次；post-title-text.html 生成页面与搜索索引的纯文本标题。搜索结果按索引的结构化字段渲染，不解析拼接后的标题，不使用 innerHTML 插入文章数据。

所有屏幕宽度统一为上下两层：系列名在顶部使用较小、较轻的次要文字，下面展示序号与章节标题；网页展示不再插入破折号。序号采用现有强调色与等宽数字，章节标题保留较高字重。首页、文章列表、系列页、归档、搜索和文章页共用这套层次。纯文本 title 继续用破折号分隔，便于 RSS、浏览器标签和社交分享阅读。没有系列字段的普通文章沿用原标题。

## 文章页系列折叠

`/posts/` 按最新文章日期排列，每个系列默认收起；展开后按文章日期从早到晚显示该系列全部文章。使用原生 `details` / `summary`，鼠标、键盘和关闭 JavaScript 的浏览器都能操作。普通文章仍单独展示，首页展示最近三篇文章，并为三个主要系列提供折叠入口；系列页同样默认折叠，标签、归档和搜索仍按文章列出。

新文章填写相同的 `learning_series` 即自动归入同组，`series_title` 作为组名。历史操作系统笔记暂不修改文章头部，使用 `data/wish.json` 对应集合的 `group_posts: true` 按标签归组。明确的 `learning_series` 优先；普通主题集合不会自动折叠，避免把不同项目的 Java 或 AI 文章混成一个系列。以后需要将其他历史集合视为系列时，显式设置 `group_posts`。

文章页先收集完整系列，不按单篇文章分页，以免展开时遗漏后续页面的章节；`paginationSize` 仍用于标签等普通列表。模板在 `layouts/posts/list.html`、`layouts/partials/post-series-list.html` 和 `layouts/partials/post-series.html`，基础样式位于 `site.css` 的 Article index 段落，新版材质、间距和动效由 `appearance.css` 与 `appearance.js` 补充。

## 学习板块

学习首页增加[每日学习时间线](https://wishbottle.cn/learning/#progress)。每次检查阶段成果或发布每日笔记时维护公开进度，详见[时间线维护说明](scripts/learning-progress.md)。数据位于 data/learning_progress.json，日期、笔记链接和重复记录由部署前检查校验。

`/learning/` 承载同一个 Java＋AI 工单项目的学习方案：A 后端业务与基础工程、B 一个 AI 功能、C 验证与改进。14 篇课程的 URL 保持不变；原周号仅作材料索引，`/learning/checklists/` 是55项技能清单，四份项目文档单独维护。当前为SQL条件查询，规划中的Web/AI功能不算已实现。网页清单是公开状态展示，个人勾选可在下载的Markdown中维护。

课程源码在 `content/learning/`，使用 JSON front matter：`weight` 控制阅读顺序，`group` 为 `start`、`course`、`tools` 或 `answers`。修改正文时维护站内 `/learning/<slug>/` 链接，保持已有网址稳定。模板位于 `layouts/learning/`，样式位于 `assets/css/learning.css`；课程同时进入全站搜索，日常笔记仍放 `content/posts/`。仅同步方案时不创建日记，时间线可用 `kind: plan-update` 并保留学习中状态。

更新课程后，从同一份公开正文重新生成离线下载，再构建博客：

```bash
python -m pip install markdown beautifulsoup4
python scripts/build_learning_downloads.py
hugo --minify
```

生成器只需要在编辑课程时运行；GitHub Actions 直接发布已提交的静态文件。下载产物在 `static/learning/downloads/`：`reader.html` 为不依赖网络资源的单页阅读版，`java-internship-self-study.zip` 包含14篇 Markdown 与阅读版。正文内的外部文档仍需联网访问，开发工具和依赖按阶段另行准备。不要将个人进度记录、本机路径、账号或私人聊天复制进公开课程或附件。

## 部署

本仓库通过 GitHub Actions 自动构建并部署到 GitHub Pages：

- push 到 `main` 后自动部署，也可在 Actions 中手动运行。
- 每小时第 17 分钟查询招聘来源并重新部署，GitHub 调度可能延迟。
- 自动任务运行于 GitHub，不需要本机开着。公开仓库长期没有活动时，GitHub 可能停用定时任务，需要在 Actions 中恢复。
- `public/`、`resources/`、缓存和本地检查文件不纳入版本控制；构建产物由 Actions 发布。

## 招聘信息

首页已移除招聘卡片；保留独立的 `/jobs/` 页面，提供杭州 Java 后端 / AI 开发的实习及校招岗位，以及企业、类型、方向筛选。

学历筛选只保留明确接受本科或本科及以上的岗位；本科可申请但硕士优先的岗位保留，硕士/博士起步、学历未注明/不限及专科起步的岗位不展示。规则同时用于来源同步、同步失败时保留的缓存和前端推荐/全部岗位列表，旧缓存不会绕过筛选。

来源包括迪普科技、恒生电子、新华三、大华股份、同花顺的公开岗位列表，以及海康威视已核验的 Java 实习岗位详情。海康目前仅检查该固定岗位，不代表其全部招聘信息。

`scripts/update_jobs.py` 将公开信息保存到 `static/data/hangzhou-jobs.json`。Actions Cache 保存前次快照，页面每 10 分钟重新读取。失败来源保留最后成功核验时间，超过 72 小时未核验的岗位移除；成功返回空列表时清空该来源旧岗位。未披露的薪资、学历或发布日期不推断。

招聘推荐组件仍保留按北京时间日期选择岗位的逻辑，目前未挂载到首页。首次接入来源建立基线，不将已有岗位计为当天新增。岗位发布时间、收录时间和核验时间分别记录。

```bash
python -m unittest discover -s scripts -p 'test_*.py'
node scripts/test_jobs_feed.cjs
python scripts/update_jobs.py
hugo --minify
```

## 每日开源发现

独立页面 `/discover/` 每天推荐 10 个 GitHub 项目；导航中的「发现」可直达，首页展示 3 个预览。页面支持 AI、开发工具、实用软件分类和本期搜索；关闭 JavaScript 时仍可阅读全部项目。排版沿用暖灰靛蓝样式，提供手机布局、深浅色和减少动态效果支持。

- `scripts/update_github_daily.py`：查询 GitHub REST Search API，过滤低于 1,000 Stars、超过 90 天未更新、已归档、Fork、私有或教程合集仓库。以仓库标签作为分类依据，按照 3 个 AI / 4 个开发工具 / 3 个实用软件选择；根据日期确定轮换顺序，尽量避开最近 7 天的项目、避免同一作者扎堆。候选不足时先放宽作者限制，再放宽历史去重；当期绝不重复，不足 10 个则不发布新一期。
- `data/github_daily.json`：已验证的首期快照，同时是本地预览与缓存失效时的回退数据。含实际日期、原始项目简介、Stars 总数及最近 14 期 ID 历史。简介按纯文本转义输出，不生成未经验证的功能介绍，也不冒充 GitHub 官方 Trending 或日增星数。
- `layouts/_default/discover.html`、`layouts/partials/github-card.html` 和 `layouts/partials/github-widget.html`：独立页面、共用项目卡片和首页预览；`assets/css/discover.css`、`assets/js/discover.js` 负责样式与筛选。

自动刷新复用 `.github/workflows/hugo.yml` 的每小时第 17 分钟任务，按北京时间 08:00 切日，通常在 **08:17 左右**生成新一期。同一天后续构建沿用本期，正常只发送 6 次搜索请求；失败后在后续任务重试。GitHub 的定时任务可能延迟或因仓库长期不活动暂停，**不保证准点**，必要时在 Actions 手动运行工作流。

工作流从 Actions Cache 恢复 `.cache/github-daily.json`，比较缓存和源码快照，保留较新的有效数据，再生成页面。生成成功才替换整期；限流、超时、响应不完整或无足够候选时保留上一期和原日期，页面提示尚未更新。缓存可能被 GitHub 清理，此时回退源码快照，最近 7 天去重记录也可能不完整；页面内容不会清空。抓取阶段使用 Actions 自动提供的 `GITHUB_TOKEN`，不需要新增付费服务、个人密钥或本机常驻任务；令牌不会进入网页。

手动刷新与检查（Python 标准库，无新增 pip 依赖）：

```bash
python -m unittest discover -s scripts -p 'test_*.py'
python scripts/update_github_daily.py
hugo --minify
```

只有明确想替换当天推荐时才用 `python scripts/update_github_daily.py --force`。本机未设置 `GITHUB_TOKEN` 时使用匿名 API，限流时仍保留已有快照。历史只用于避免重复，目前不提供往期全文归档。

阅读组织方式参考 [HelloGitHub](https://github.com/521xueweihan/HelloGitHub)，未转载其月刊内容。数据规则参见 [GitHub 搜索仓库文档](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories)和[定时工作流文档](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)。

## 外观

默认主题为 **One Dark**，配色参考 [JetBrains One Dark 插件](https://github.com/one-dark/jetbrains-one-dark-theme)：蓝灰背景、冷灰正文、蓝色链接，以及紫色关键字、绿色字符串和黄色类型名。页面仍使用现有阅读布局与轻微动效；小字、代码注释比编辑器原版更亮，以保证网页阅读对比度。

`assets/css/one-dark.css` 集中定义 One Dark 色板和 Chroma 语法色。新访客默认深色；已保存的 `wish-typo-theme=light/dark` 偏好继续生效，右上角可以切换。主题在页面正文绘制前确定，本地存储不可用时采用默认值，关闭 JavaScript 也有服务端默认配色。浅色仍保留原有外观。


定制样式按用途划分，加载顺序由 `layouts/partials/head/css.html` 统一管理：

- `assets/css/tokens.css`：暖灰靛蓝配色、字体、内容宽度等公共变量。强调色使用 `--accent`，浅色背景使用 `--accent-soft`。
- `assets/css/site.css`：导航、文章、首页、归档、搜索、简介等公共布局与组件。
- `assets/css/jobs.css`：独立招聘页面的样式，仅 `/jobs/` 加载。
- `assets/css/appearance.css`：暖白灰紫视觉、响应式首页、系列卡片、学习页信息顺序和文章侧边目录。
- `assets/js/appearance.js`：导航滑动、系列展开、主题切换、章节高亮、阅读进度和返回顶部；兼容减少动态效果偏好。
- `assets/css/one-dark.css`：One Dark 色板、深色组件细节，以及 Java、SQL 等代码块的语法颜色。
- `assets/css/accessibility.css`：玻璃效果回退、减少动态效果与透明度等偏好，最后加载。

首页的文章和系列条目从内容与集合数据生成；学习页优先展示已归档的时间线，课程与日程放在后面。电脑端文章目录跟随阅读位置高亮，手机端默认折叠；关闭 JavaScript 时文章和原生折叠目录仍可阅读。深浅色偏好继续保存到原有的 `wish-typo-theme` 键。

导航胶囊使用 [Lens / design-systems](https://github.com/ruiqichenbiec/design-systems) 的 Spring 计算器，按博客阅读场景降低运动幅度。原始 MIT 许可保存在 `static/licenses/lens.txt`，站点在页头提供许可链接。

支持深浅色切换和手机布局。字体优先使用本机苹方，未安装时使用系统字体；没有分发苹方字体文件。修改简介外观时编辑 `site.css` 中的 `.about-profile`、`.about-avatar`、`.about-bio`，无需在正文中写 CSS。

简介页的 `summary` 单独保留既有 RSS 摘要及其内联样式，让不加载站点 CSS 的订阅阅读器仍按原样显示。正文中的布局使用上述 CSS 类；以后修改简介首段时，也应检查这份摘要是否需要同步。

主题保存在 `themes/typo-blue`，保留 MIT 许可证；站点模板覆盖位于 `layouts/`。文章原有地址和图片保持兼容。

## 目录结构

```text
.
├── .github/workflows/hugo.yml  # 自动同步、检查、构建和发布
├── archetypes/                # 新内容模板
│   ├── default.md             # 普通页面模板
│   └── posts/index.md         # 带独立目录的文章模板
├── assets/
│   ├── css/                   # 按职责划分的站点样式
│   └── js/                    # 招聘展示与筛选逻辑
├── content/
│   ├── posts/                 # 文章和对应图片
│   └── *.md                   # 简介、归档、搜索、系列等页面
├── data/wish.json             # 学习系列配置
├── layouts/                  # 站点模板，覆盖主题同名模板
├── scripts/                  # 招聘同步脚本和相关检查
├── static/                   # 原样复制的图标、头像、CNAME 和招聘快照
├── themes/typo-blue/          # 第三方主题，保留上游文件和许可证
├── .gitignore
├── hugo.yaml                 # 站点配置，paginationSize 控制列表分页
└── README.md
```

`assets/` 中的样式与脚本经过 Hugo 处理，`static/` 中的文件直接复制，二者用途不同。构建时出现的 `public/`、`resources/` 是可再生成的输出和缓存，已忽略，不放文章源码，也不手工修改。

当前页面文字由站点模板提供，没有使用翻译表。旧 PaperMod 主题不再作为依赖。第三方 Typo 主题的说明、示例和许可证保留在主题目录；网站定制集中放在根目录的 `assets/` 与 `layouts/`，便于以后核对上游版本。
