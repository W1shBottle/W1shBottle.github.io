# WishBottle's Blog

这是我的个人博客源码仓库，使用 **Hugo** + [Typo](https://github.com/tomfran/typo) 主题搭建，定制暖灰靛蓝配色、圆角卡片和半透明导航。

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

## 学习板块

`/learning/` 单独承载 Java 实习自学计划，顶部导航的“学习”进入。14 篇资料包括20周弹性日程、设备运维工单项目、第一课、三个阶段课程、春季投递安排、资料与排错、接口约定、验收模板和参考答案。课程属于学习材料，项目功能需学习者亲手实现与验收。

课程源码在 `content/learning/`，使用 JSON front matter：`weight` 控制阅读顺序，`group` 为 `start`、`course`、`tools` 或 `answers`。修改正文时维护站内 `/learning/<slug>/` 链接，保持已有网址稳定。模板位于 `layouts/learning/`，样式位于 `assets/css/learning.css`；课程同时进入全站搜索，日常笔记仍放 `content/posts/`。

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

首页展示杭州 Java 后端 / AI 开发的实习及校招岗位；`/jobs/` 提供全部岗位和企业、类型、方向筛选。

来源包括迪普科技、恒生电子、新华三、大华股份、同花顺的公开岗位列表，以及海康威视已核验的 Java 实习岗位详情。海康目前仅检查该固定岗位，不代表其全部招聘信息。

`scripts/update_jobs.py` 将公开信息保存到 `static/data/hangzhou-jobs.json`。Actions Cache 保存前次快照，页面每 10 分钟重新读取。失败来源保留最后成功核验时间，超过 72 小时未核验的岗位移除；成功返回空列表时清空该来源旧岗位。未披露的薪资、学历或发布日期不推断。

首页按北京时间日期选择至多 8 条推荐，并优先展示当日新收录岗位。每日组合可以包含重复岗位；企业没有新增时明确显示“今日暂无新收录”。首次接入来源建立基线，不将已有岗位计为当天新增。岗位发布时间、收录时间和核验时间分别记录。

```bash
python -m unittest discover -s scripts -p 'test_*.py'
node scripts/test_jobs_feed.cjs
python scripts/update_jobs.py
hugo --minify
```

## 外观

定制样式按用途划分，加载顺序由 `layouts/partials/head/css.html` 统一管理：

- `assets/css/tokens.css`：暖灰靛蓝配色、字体、内容宽度等公共变量。强调色使用 `--accent`，浅色背景使用 `--accent-soft`。
- `assets/css/site.css`：导航、文章、首页、归档、搜索、简介等公共布局与组件。
- `assets/css/jobs.css`：首页招聘卡片与完整岗位列表，仅相关页面加载。
- `assets/css/accessibility.css`：玻璃效果回退、减少动态效果与透明度等偏好，最后加载。

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
