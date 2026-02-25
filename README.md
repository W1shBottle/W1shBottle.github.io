# WishBottle's Blog

这是我的个人博客源码仓库，使用 **Hugo** + **PaperMod** 主题搭建。

- 站点地址：<https://wishbottle.cn/>
- GitHub Pages：<https://w1shbottle.github.io/>

## 本地预览

> 需要已安装 Hugo（建议 extended 版本）

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

- push 到默认分支后自动部署

## 目录结构（简要）

- `content/`：文章与页面内容
- `static/`：静态资源（favicon、图片等）
- `layouts/`：自定义模板覆盖（可选）
- `i18n/`：界面文字翻译（可选）
- `hugo.yaml`：站点配置
