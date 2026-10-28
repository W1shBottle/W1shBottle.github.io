"""Sync the Java project's four Markdown documents into the blog.

Usage: python scripts/sync_project_docs.py --project-root <JavaProject directory>
Project files remain the source of truth. Only public links, environment-specific
wording and publication-workflow details are adapted; behavior is not rewritten.
"""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

PAGES = [
    ("README.md", "project-docs", "设备运维工单项目文档", "当前控制台与 SQL 进度、Java＋AI 路线和运行入口。", 160),
    ("docs/requirements.md", "project-requirements", "工单项目需求与开发计划", "最小业务闭环、阶段验收与后续 AI、Agent 任务。", 170),
    ("docs/design.md", "project-design", "工单项目设计与数据约定", "现有类与存档设计，以及待实施的数据库、Web 和 AI 边界。", 180),
    ("docs/verification.md", "project-verification", "工单项目运行与验收", "实际运行证据、后端验收与模型效果评估标准。", 190),
]
LINKS = {
    "docs/requirements.md": "/learning/project-requirements/",
    "docs/design.md": "/learning/project-design/",
    "docs/verification.md": "/learning/project-verification/",
    "../README.md": "/learning/project-docs/",
    "requirements.md": "/learning/project-requirements/",
    "design.md": "/learning/project-design/",
    "verification.md": "/learning/project-verification/",
    "../Java学习/实习训练/README.md": "/learning/start/",
    "../Java学习/实习训练/离线自学包/01_20周弹性日程.md": "/learning/schedule/",
    "../Java学习/实习训练/学习进度.md": "/learning/#progress",
}
PRIVATE_PATH = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[/\\]|file://")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def public_body(raw, source):
    # The native page title already supplies the first heading.
    body = re.sub(r"\A# [^\n]+\n+", "", raw)
    for old, new in LINKS.items():
        body = body.replace("](" + old + ")", "](" + new + ")")
        body = body.replace("](" + old + "#", "](" + new + "#")

    if source == "README.md":
        # Local siblings are not shipped with the website; use stable public pages.
        body = re.sub(
            r"(?m)^本地学习入口：[^\n]*(?:\n|$)",
            "学习入口：[路线说明](/learning/start/) · [阶段计划](/learning/schedule/) · "
            "[技能清单](/learning/checklists/) · [实际学习进度](/learning/#progress)。"
            "本组项目文档记录实现与验收，课程材料记录后续学习安排。\n",
            body,
        )
        body = body.replace(
            "A1/A2 对应第一份需求中的两个后端阶段；B/C 对应第二份需求中的 AI 与验证阶段。",
            "A1/A2 分别完成最小业务与基础工程；B/C 分别完成 AI 接入与效果验证。",
        )
        body = "> 本组文档对应项目当前实现，与[总体规划](/learning/project/)配合阅读。后续功能以各页的实现状态为准。\n\n" + body

    # Local migration reports contain account/backup locations. Publish the
    # verified behavior and boundaries, while retaining private restore details locally.
    if source == "README.md":
        body = re.sub(
            r"(?s)### 本机 MySQL 环境（2026-10-28）.*?(?=### 存档位置)",
            "### MySQL 与 JDBC 环境（2026-10-28）\n\n"
            "当前学习环境为 MySQL 8.4.13 LTS 与 Connector/J 26.10.0。"
            "在 IDEA 重新加载 Maven 依赖；数据库地址、账号和密码按自己的本机环境配置。"
            "升级前已有备份，助手完成恢复、数据一致性与真实 JDBC 验证；"
            "安装路径、账号材料和回退操作保留在本地，不公开。\n\n"
            "学习者随后完成独立 JDBC 查询 Demo；正式控制台仍使用文件仓库，"
            "Java 更新事务待亲手实现。详见[运行与验收](/learning/project-verification/)。\n\n",
            body,
        )
    if source == "docs/verification.md":
        body = re.sub(
            r"(?s)## 10\. 2026-10-28 MySQL 升级验收.*?(?=## 11\.|\Z)",
            "## 10. 2026-10-28 MySQL 升级验收\n\n"
            "助手完成 MySQL 8.0.44 → 8.4.13 和 Connector/J 9.7.0 → 26.10.0 的环境维护。"
            "先备份全部旧库，为 MyISAM 补充锁表备份；独立端口恢复后，再冻结旧库写入、"
            "最终备份并切换服务。原账号认证和旧数据目录保留；旧服务停止，新服务自动启动，重启验证通过。\n\n"
            "五个业务库共70张表、958行，逐表比较完整行内容哈希、结构、引擎、排序规则、"
            "自增值及业务存储对象，切换前后均一致。结构比较只标准化外键引用列名的大小写显示。"
            "旧项目所需的认证及非唯一索引外键兼容选项予以保留，新项目仍应采用默认认证和规范外键。\n\n"
            "助手用新驱动在临时和正式端口验证参数查询、中文、版本条件更新、回滚及FK/CHECK约束；"
            "测试修改均回滚，临时数据库账号删除。Java21运行原有17项JUnit全部通过，"
            "不计为学习者新增JDBC测试。其他旧项目未全部完成端到端验收。\n\n"
            "备份和账号材料只保存在受限本地目录，不随博客发布。旧版本回退点不包含升级后的新增数据，"
            "不能不经评估直接切回，也不能用8.0打开8.4的数据目录。正式工单业务仍使用文件仓库，"
            "独立查询Demo的学习证据见下一节。\n\n",
            body,
        )

    # Keep the verification facts, without publishing private installation/report paths.
    body = body.replace("用 `D:/JDK` 的 Java 21 和 IDEA 自带 Maven", "使用已配置的 Java 21 和 IDEA 自带 Maven")
    body = body.replace("显式选 D:/JDK", "显式选择 JDK 21")
    body = body.replace("（例如当前机器的 D:\\work\\JavaProject）", "（即包含 src 的 JavaProject 目录）")
    body = re.sub(r"，报告在本地忽略目录 `\.qa/[^`]+`", "，核验记录保留在本地", body)
    body = body.replace("本次路线文档修订尚未提交。", "此次路线调整仅更新文档与课程，业务实现未提前推进。")

    if PRIVATE_PATH.search(body):
        raise ValueError("Remove machine-specific paths before publication: " + source)
    if "本次未发布" in body or ".qa/plan-refresh" in body:
        raise ValueError("Local publication state remains: " + source)
    if body.count("```") % 2:
        raise ValueError("Unclosed code fence: " + source)
    for target in MARKDOWN_LINK.findall(body):
        parsed = urlsplit(target)
        if parsed.scheme not in ("", "http", "https", "mailto"):
            raise ValueError("Non-public link in " + source + ": " + target)
        if not parsed.scheme and not target.startswith(("/", "#")):
            raise ValueError("Unmapped local link in " + source + ": " + target)
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    destination = Path(__file__).resolve().parents[1] / "content" / "learning"
    prepared = []
    for source, slug, title, description, weight in PAGES:
        raw = (args.project_root / source).read_text(encoding="utf-8-sig")
        body = public_body(raw, source)
        date = re.search(r"核对日期：(\d{4}-\d{2}-\d{2})", body)
        if not date:
            raise ValueError("Missing document review date: " + source)
        path = destination / (slug + ".md")
        existing = {}
        if path.exists():
            existing, _ = json.JSONDecoder().raw_decode(path.read_text(encoding="utf-8-sig").lstrip())
        metadata = {
            "title": title, "description": description,
            "date": existing.get("date", date[1] + "T00:00:00+08:00"),
            "lastmod": date[1] + "T00:00:00+08:00",
            "weight": weight, "group": "project-docs", "draft": False,
        }
        prepared.append((path, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n\n" + body))
    # Prepare and validate every page before writing any output.
    for path, content in prepared:
        path.write_text(content, encoding="utf-8", newline="\n")
        print(path.name)


if __name__ == "__main__":
    main()
