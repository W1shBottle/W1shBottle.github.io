"""Build the public learning reader and ZIP from already-reviewed Hugo content.

Run locally: python scripts/build_learning_downloads.py
Requires the local Python packages markdown and beautifulsoup4. The resulting
static files are committed artifacts; site CI does not need these packages.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import html
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import zipfile

import markdown
from markdown.extensions.toc import slugify_unicode
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "learning"
OUTPUT = ROOT / "static" / "learning" / "downloads"
SITE = "https://wishbottle.cn"
ZIP_NAME = "java-internship-self-study.zip"
ZIP_URL = SITE + "/learning/downloads/" + ZIP_NAME
EXPECTED_CHAPTERS = 14
MARKDOWN_LINK = re.compile(r"(?P<before>\]\()(?P<url>[^\s)]+)(?P<after>\))")
PRIVATE_TEXT = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[/\\]|file://[^\s`<>\"']|续费|codex", re.I)


@dataclass
class Chapter:
    slug: str
    metadata: dict
    body: str
    soup: BeautifulSoup
    headings: list[tuple[str, str]]
    fragments: dict[str, str]

    @property
    def anchor(self) -> str:
        return "chapter-" + self.slug

    @property
    def title(self) -> str:
        return self.metadata["title"]


def assert_public(text: str, label: str) -> None:
    match = PRIVATE_TEXT.search(text)
    if match:
        raise ValueError(f"Private/context-specific text remains in {label}: {match.group()}")


def read_chapters() -> list[Chapter]:
    chapters = []
    for path in CONTENT.glob("*.md"):
        if path.name == "_index.md":
            continue
        raw = path.read_text(encoding="utf-8-sig").lstrip()
        metadata, end = json.JSONDecoder().raw_decode(raw)
        # Project implementation docs are separate from the 14-chapter course.
        if metadata.get("group") == "project-docs":
            continue
        if metadata.get("draft", False):
            continue
        if not metadata.get("title") or not isinstance(metadata.get("weight"), int):
            raise ValueError(f"Missing title/weight: {path.name}")
        if not re.fullmatch(r"[a-z0-9-]+", path.stem):
            raise ValueError(f"Unexpected public slug: {path.stem}")
        body = raw[end:].strip() + "\n"
        assert_public(body, path.name)
        if body.count("```") % 2:
            raise ValueError(f"Unclosed code fence: {path.name}")
        rendered = markdown.markdown(
            body, extensions=["tables", "fenced_code", "sane_lists", "toc"],
            extension_configs={"toc": {"slugify": slugify_unicode}},
        )
        soup = BeautifulSoup(rendered, "html.parser")
        headings, fragments = [], {}
        for heading in soup.find_all(re.compile(r"^h[1-6]$")):
            original = heading.get("id")
            if not original:
                raise ValueError(f"Missing heading anchor: {path.name}")
            anchor = "chapter-" + path.stem + "-" + original
            fragments[original] = anchor
            heading["id"] = anchor
            if heading.name == "h2":
                headings.append((anchor, heading.get_text(" ", strip=True)))
        for table in list(soup.find_all("table")):
            table.wrap(soup.new_tag("div", attrs={"class": "table-scroll", "tabindex": "0"}))
        for item in soup.find_all("li"):
            first = item.contents[0] if item.contents else None
            if isinstance(first, str) and first.startswith("[ ] "):
                first.replace_with("□ " + first[4:])
        chapters.append(Chapter(path.stem, metadata, body, soup, headings, fragments))
    chapters.sort(key=lambda item: (item.metadata["weight"], item.slug))
    if len(chapters) != EXPECTED_CHAPTERS:
        raise ValueError(f"Expected {EXPECTED_CHAPTERS} chapters; found {len(chapters)}")
    return chapters


def target_url(url: str, current: Chapter, chapters: dict[str, Chapter], *, for_html: bool) -> str:
    parsed = urlsplit(html.unescape(url))
    if parsed.scheme:
        if parsed.scheme not in ("https", "http", "mailto"):
            raise ValueError(f"Unsupported link scheme in {current.slug}: {url}")
        return url
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("#"):
        fragment = unquote(parsed.fragment)
        if fragment not in current.fragments:
            raise ValueError(f"Unknown local fragment in {current.slug}: {url}")
        return "#" + current.fragments[fragment] if for_html else url
    path = unquote(parsed.path)
    if path == "/learning/downloads/reader.html":
        return "#top" if for_html else "reader.html"
    if path == "/learning/downloads/" + ZIP_NAME:
        return ZIP_URL
    match = re.fullmatch(r"/learning/([a-z0-9-]+)/?", path)
    if match and match.group(1) in chapters:
        target = chapters[match.group(1)]
        if parsed.query:
            raise ValueError(f"Unexpected query on a course link: {url}")
        if parsed.fragment:
            fragment = unquote(parsed.fragment)
            if fragment not in target.fragments:
                raise ValueError(f"Unknown cross-chapter fragment: {url}")
            return "#" + target.fragments[fragment] if for_html else f"./{target.slug}.md#{parsed.fragment}"
        return "#" + target.anchor if for_html else f"./{target.slug}.md"
    if path.startswith("/"):
        return SITE + url
    raise ValueError(f"Unresolved relative link in {current.slug}: {url}")


STYLE = r"""
:root{color-scheme:light;--ink:#172c3b;--muted:#516575;--accent:#17665e;--paper:#fff;--line:#dce5e6;--bg:#f4f7f6}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:20px}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;font-size:16px;line-height:1.9}
a{color:var(--accent);text-underline-offset:4px}a:hover{color:#0a453e}a:focus-visible,summary:focus-visible,.table-scroll:focus-visible{outline:3px solid #369b89;outline-offset:4px}
.layout{max-width:1540px;margin:auto;display:grid;grid-template-columns:270px minmax(0,1fr);gap:40px;padding:32px}aside{position:sticky;top:24px;height:calc(100vh - 48px);overflow-y:auto;padding:12px 10px 24px 0;font-size:14px}
.brand{font-size:21px;font-weight:700;margin-bottom:4px}.sidebar-note{color:var(--muted);font-size:12px;line-height:1.7}.site-return{display:inline-block;margin:12px 0}
nav ul{padding:0;list-style:none;margin:20px 0}nav li{margin:0 0 7px}nav a{display:block;border-radius:7px;padding:6px 10px;text-decoration:none;line-height:1.6}nav a:hover{background:#e4efec}aside details{border-top:1px solid var(--line);padding-top:12px}summary{cursor:pointer;font-weight:600}
main{min-width:0;max-width:1120px}.hero{padding:36px 42px;background:var(--ink);border-radius:12px;color:#fff;margin-bottom:28px}.eyebrow{color:#9ce1cf;font-size:13px;letter-spacing:1px}.hero h1{margin:12px 0;font-size:clamp(27px,3vw,40px);line-height:1.3;border:0;color:#fff}.hero p{color:#dce7ea;margin:12px 0 20px;max-width:50em}.hero a{color:#b1eadb}
.meta{display:flex;flex-wrap:wrap;gap:10px}.meta span{background:#2c4552;color:#f1f7f8;padding:5px 12px;border-radius:6px;font-size:13px}.download{display:inline-block;margin-top:18px}
.chapter{background:var(--paper);padding:36px 42px;margin:0 0 28px;border:1px solid var(--line);border-radius:10px;scroll-margin-top:24px;min-width:0}.chapter-meta{display:flex;justify-content:space-between;gap:10px;color:var(--muted);font-size:12px;letter-spacing:.5px}
h1{font-size:28px;line-height:1.4;margin:18px 0 24px;color:var(--ink)}h2{font-size:22px;margin:36px 0 16px;padding-top:18px;border-top:1px solid var(--line);line-height:1.5}h3{font-size:18px;line-height:1.6;margin:26px 0 12px}p{margin:14px 0}strong{font-weight:700;color:#143e44}li{margin:5px 0}ul,ol{padding-left:1.7em}blockquote{margin:18px 0;padding:4px 20px;border-left:4px solid #86b5a9;background:#f2f8f6}
.table-scroll{overflow:auto;margin:20px 0;max-width:100%;border:1px solid var(--line);border-radius:7px}table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.75;min-width:550px}th,td{padding:11px 13px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left;overflow-wrap:anywhere}th{background:#eaf2ef;color:#1b4e48;font-weight:700}tbody tr:nth-child(even){background:#f9fbfa}tbody tr:last-child td{border-bottom:0}
code{font-family:Consolas,"Cascadia Code",monospace;font-size:.9em;background:#edf2f4;padding:2px 5px;border-radius:4px;overflow-wrap:anywhere}pre{background:#122938;color:#e6f0f4;border-radius:8px;padding:18px 20px;line-height:1.65;font-size:13px;overflow-x:auto;max-width:100%}pre code{color:inherit;background:none;padding:0;overflow-wrap:normal;white-space:pre}
.backtop{display:inline-block;margin-top:16px}.footer{padding:16px 0 30px;color:var(--muted);font-size:13px}.mobile-nav{display:none}
@media(max-width:1000px){.layout{grid-template-columns:220px minmax(0,1fr);gap:20px;padding:20px}.chapter,.hero{padding:28px}}
@media(max-width:760px){.layout{display:block;padding:14px}aside{position:static;height:auto;overflow:visible;padding:10px 6px 16px}.brand{font-size:19px}aside nav,aside details{display:none}.sidebar-note{font-size:13px}.hero,.chapter{padding:22px 18px;border-radius:8px}.hero h1{font-size:29px}h1{font-size:25px}h2{font-size:21px}.chapter-meta{font-size:11px}body{font-size:15px}pre{font-size:12px;padding:14px}th,td{padding:9px 11px}table{font-size:13px}.mobile-nav{display:block;margin-bottom:20px;padding:12px 18px;background:white;border:1px solid var(--line);border-radius:8px}.mobile-nav ul{list-style:none;padding:0;margin:12px 0}.mobile-nav li{padding:3px 0}.mobile-nav details{padding-top:12px;border-top:1px solid var(--line)}}
@media print{body{background:white;font-size:10pt;line-height:1.65}.layout{display:block;padding:0;max-width:none}aside,.mobile-nav,.chapter-meta,.backtop,.download{display:none!important}.hero{background:white;color:#172c3b;padding:0 0 20px;border-radius:0}.hero h1,.hero p,.eyebrow{color:#172c3b}.meta span{background:#eee;color:#172c3b}.chapter{padding:0;margin:0;border:0;border-radius:0;break-before:page}h1{font-size:20pt}h2{font-size:15pt;break-after:avoid}h3{break-after:avoid}tr{break-inside:avoid}.table-scroll{overflow:visible;border-radius:0}table{min-width:0;font-size:9pt}pre{white-space:pre-wrap;background:#f3f3f3;color:#111;font-size:8pt;overflow:visible;break-inside:auto}pre code{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#164d48;text-decoration:none}@page{size:A4;margin:16mm}}
"""


def build() -> dict:
    chapters = read_chapters()
    by_slug = {chapter.slug: chapter for chapter in chapters}
    chapter_nav, week_nav, sections, package_markdown = [], [], [], {}
    for index, chapter in enumerate(chapters, start=1):
        for anchor in chapter.soup.find_all("a", href=True):
            anchor["href"] = target_url(anchor["href"], chapter, by_slug, for_html=True)
            if anchor["href"].startswith(("http://", "https://")):
                anchor["rel"] = "noopener noreferrer"
        chapter_nav.append(f'<li><a href="#{chapter.anchor}">{html.escape(chapter.title)}</a></li>')
        if chapter.metadata.get("group") != "answers":
            for anchor, title in chapter.headings:
                if re.match(r"第\s*\d+\s*周", title):
                    week_nav.append(f'<li><a href="#{anchor}">{html.escape(title)}</a></li>')
        sections.append(
            f'<section id="{chapter.anchor}" class="chapter">'
            f'<div class="chapter-meta"><span>{index:02d} / {len(chapters)}</span>'
            f'<a href="#top">回到目录</a></div><h1>{html.escape(chapter.title)}</h1>'
            f'{chapter.soup}</section>'
        )
        def replace_link(match: re.Match) -> str:
            converted = target_url(match["url"], chapter, by_slug, for_html=False)
            return match["before"] + converted + match["after"]
        package_markdown[chapter.slug + ".md"] = (
            "# " + chapter.title + "\n\n" + MARKDOWN_LINK.sub(replace_link, chapter.body)
        )
    navigation, weeks = "".join(chapter_nav), "".join(week_nav)
    if len(week_nav) != 20:
        raise ValueError(f"Expected 20 distinct teaching weeks; found {len(week_nav)}")
    document = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="设备运维工单平台：20周Java项目主线、自测答案与2027春季投递计划，支持离线阅读。"><title>Java 实习自学计划 · WishBottle</title><style>{STYLE}</style></head>
<body id="top"><div class="layout"><aside><div class="brand">Java 实习自学计划</div><div class="sidebar-note">2028 届 · 2027 暑期目标<br>每周目标制 / 连续阅读版</div><a class="site-return" href="{SITE}/learning/">返回博客学习板块 ↗</a><nav aria-label="章节目录"><ul>{navigation}</ul></nav><details><summary>按学习周查找</summary><nav aria-label="周目录"><ul>{weeks}</ul></nav></details><p class="sidebar-note">Ctrl+F 查找 · Ctrl+P 打印<br>保存这一份 HTML 即可离线阅读<br>正文无需加载外部资源</p></aside>
<main><header class="hero"><div class="eyebrow">WISHBOTTLE / 学习板块</div><h1>Java 实习完整自学计划</h1><p>用设备运维工单平台学习 Java、数据库、接口、权限、测试与部署。每周完成一个具体成果，保留考试和复习的弹性。</p><div class="meta"><span>20 周项目主线</span><span>每周 15—18 小时</span><span>14 篇课程与参考资料</span><span>2027 春季投递安排</span></div><a class="download" href="{ZIP_URL}">下载完整自学包（HTML + Markdown）↗</a></header>
<details class="mobile-nav"><summary>打开课程目录</summary><nav aria-label="手机章节目录"><ul>{navigation}</ul></nav><details><summary>按学习周查找</summary><nav aria-label="手机周目录"><ul>{weeks}</ul></nav></details></details>
{''.join(sections)}<footer class="footer">编制日期：2026年10月12日。计划日期可顺延，以实际验收为准。<br>这是学习路线与局部参考示例，完整项目需随课程实现和验证。<br><a href="{SITE}/learning/">返回 WishBottle 学习板块 ↗</a> · <a href="#top">回到顶部</a></footer></main></div></body></html>'''
    assert_public(document, "reader.html")
    soup = BeautifulSoup(document, "html.parser")
    ids = [item["id"] for item in soup.find_all(id=True)]
    duplicates = [anchor for anchor, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate HTML anchors: {duplicates}")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.startswith("#") and href[1:] not in ids:
            raise ValueError(f"Missing HTML anchor: {href}")
        if not href.startswith(("#", "https://", "http://", "mailto:")):
            raise ValueError(f"Standalone reader depends on another local file: {href}")
    if soup.find_all(["script", "iframe", "img", "link", "audio", "video", "object", "embed", "form"]):
        raise ValueError("Reader contains active content or external resource elements")
    if re.search(r"@import|url\s*\(", STYLE, re.I):
        raise ValueError("Reader CSS contains external resources")
    filenames = set(package_markdown) | {"reader.html"}
    for filename, body in package_markdown.items():
        assert_public(body, filename)
        for match in MARKDOWN_LINK.finditer(body):
            url = urlsplit(match["url"])
            if not url.scheme and url.path:
                relative = unquote(url.path).removeprefix("./")
                if relative not in filenames:
                    raise ValueError(f"Broken ZIP Markdown link in {filename}: {match['url']}")
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, body in package_markdown.items():
            archive.writestr(filename, body.encode("utf-8"))
        archive.writestr("reader.html", document.encode("utf-8"))
    with zipfile.ZipFile(buffer) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(chapters) + 1:
            raise ValueError("ZIP CRC or file-count check failed")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "reader.html").write_text(document, encoding="utf-8")
    (OUTPUT / ZIP_NAME).write_bytes(buffer.getvalue())
    report = {
        "chapters": len(chapters), "week_links": len(week_nav),
        "html_anchors": len(ids), "code_blocks": len(soup.find_all("pre")),
        "tables": len(soup.find_all("table")), "archive_files": len(filenames),
        "html_bytes": len(document.encode("utf-8")), "zip_bytes": len(buffer.getvalue()),
        "broken_links": 0, "duplicate_anchors": 0, "external_resource_elements": 0,
        "private_context_matches": 0, "zip_crc": "passed",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    build()
