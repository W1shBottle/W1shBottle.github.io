"""Sync the Java project's four Markdown documents into the blog.

Usage: python scripts/sync_project_docs.py --project-root <JavaProject directory>
The project files are the source of truth; generated blog pages may be overwritten.
"""
import argparse
import json
from pathlib import Path
import re

PAGES = [
    ("README.md", "project-docs", "设备运维工单项目文档", "项目当前能力、代码结构和运行入口。", 160),
    ("docs/requirements.md", "project-requirements", "工单项目需求与开发计划", "业务规则、已实现功能、待办事项与开发里程碑。", 170),
    ("docs/design.md", "project-design", "工单项目设计与数据约定", "类的职责、方法契约、状态规则与 Properties 存档格式。", 180),
    ("docs/verification.md", "project-verification", "工单项目运行与验收", "编译运行步骤、预期输出、验收清单和常见问题。", 190),
]
LINKS = {
    "docs/requirements.md": "/learning/project-requirements/",
    "docs/design.md": "/learning/project-design/",
    "docs/verification.md": "/learning/project-verification/",
    "../README.md": "/learning/project-docs/",
    "requirements.md": "/learning/project-requirements/",
    "design.md": "/learning/project-design/",
    "verification.md": "/learning/project-verification/",
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    destination = Path(__file__).resolve().parents[1] / "content" / "learning"
    prepared = []
    for source, slug, title, description, weight in PAGES:
        raw = (args.project_root / source).read_text(encoding="utf-8-sig")
        # The native page title already supplies the first heading.
        body = re.sub(r"\A# [^\n]+\n+", "", raw)
        for old, new in LINKS.items():
            body = body.replace("](" + old + ")", "](" + new + ")")
        body = body.replace(
            "（例如当前机器的 D:\\work\\JavaProject）", "（即包含 src 的 JavaProject 目录）"
        )
        if re.search(r"(?<![A-Za-z0-9_])[A-Za-z]:[/\\]|file://", body):
            raise ValueError("Remove machine-specific paths before publication: " + source)
        date = re.search(r"核对日期：(\d{4}-\d{2}-\d{2})", body)
        if not date:
            raise ValueError("Missing document review date: " + source)
        metadata = {
            "title": title, "description": description,
            "date": date[1] + "T00:00:00+08:00",
            "lastmod": date[1] + "T00:00:00+08:00",
            "weight": weight, "group": "project-docs", "draft": False,
        }
        if source == "README.md":
            body = "> 本组文档对应项目当前实现，与[总体规划](/learning/project/)配合阅读。后续功能以各页的实现状态为准。\n\n" + body
        prepared.append((destination / (slug + ".md"), json.dumps(metadata, ensure_ascii=False, indent=2) + "\n\n" + body))
    for path, content in prepared:
        path.write_text(content, encoding="utf-8", newline="\n")
        print(path.name)

if __name__ == "__main__":
    main()
