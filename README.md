# WishBottle's Blog

这是我的个人博客源码仓库，使用 **Hugo** + [Typo](https://github.com/tomfran/typo) 主题搭建，定制蓝色配色、圆角卡片和玻璃质感导航。

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
hugo new posts/my-post.md
```

然后编辑 `content/posts/my-post.md`，写完把 `draft: true` 改为 `false`。

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

定制样式位于 `assets/css/apple.css`，招聘样式位于 `assets/css/jobs.css`。支持深浅色切换、手机布局与减少动态效果。字体优先使用本机苹方，未安装时使用系统字体；没有分发苹方字体文件。

主题保存在 `themes/typo-blue`，保留 MIT 许可证；站点模板覆盖位于 `layouts/`。文章原有地址和图片保持兼容。

## 目录结构（简要）

- `content/`：文章与页面内容
- `static/`：静态资源（favicon、图片等）
- `layouts/`：自定义模板覆盖（可选）
- `i18n/`：界面文字翻译（可选）
- `hugo.yaml`：站点配置
