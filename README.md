# WishBottle

我的个人博客源码，使用 Hugo + Typo 主题。

**[访问博客 → wishbottle.cn](https://wishbottle.cn/)**

## 本地运行

需要 **Hugo 0.156.0 extended**。

```bash
hugo server -D
```

打开 `http://localhost:1313/`。正式构建使用 `hugo --minify`。

## 维护入口

- `content/posts/`：文章与配图；新建文章用 `hugo new content --kind posts posts/my-post`。
- `content/learning/`：学习计划与课程；进度更新见[维护说明](scripts/learning-progress.md)。
- `assets/`、`layouts/`：样式、交互和页面模板。
- `data/`、`scripts/`：站点数据、生成与校验脚本。
- `hugo.yaml`：站点配置；`static/`：图标、字体等静态文件。

写作约定：公开文章不出现任课老师姓名，引用教学资料时使用“课程课件”等通用表述。

期末复习系列按专题维护，一篇只写一个专题，可按篇幅拆为同专题上下篇；未学完时更新已有专题文章。以知识点、适用条件、解法、伪代码、例题、复杂度和易错点为主，不写日记、聊天回顾或大量思考过程；与Java项目笔记和进度分开。

## 发布

推送到 `main` 后，GitHub Actions 自动检查、构建并发布到 GitHub Pages。流程见 [hugo.yml](.github/workflows/hugo.yml)；脚本检查环境为 Python 3.12、Node.js 24。

## 第三方素材

[Typo](themes/typo-blue/LICENSE) · [JetBrains Mono](static/licenses/jetbrains-mono.txt) · [Lens](static/licenses/lens.txt)
