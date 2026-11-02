#!/usr/bin/env python3
"""Locate dou-tone review candidates; never rewrite or certify prose quality.

STYLE is a selected profile's explicit punctuation constraint. REVIEW is a
context-sensitive candidate, not a demonstrated defect. Markdown exclusions are
conservative and limited; this is not a full Markdown or scientific parser.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Issue:
    line: int
    level: str
    rule: str
    evidence: str
    message: str


PATTERNS = (
    ("chat-residue", r"当然可以|希望这对(?:你|您)有帮助", "检查是否为应移出成稿的聊天回应。"),
    ("vague-action", r"(?:搞|弄)(?:顺|清楚|明白|好|完|懂|定|起来)|(?:吃下|吞下).{0,10}(?:信息|上下文)", "结合文体检查动作是否具体，不能机械替换。"),
    ("generic-opening", r"在(?:当今|当前).{0,18}(?:时代|背景|环境)下|随着.{0,18}(?:不断|持续)发展", "检查背景是否提供独立信息。"),
    ("padded-claim", r"真正重要的是|这不仅仅?是|原因很简单|为.{1,20}奠定.{0,4}基础|未来可期", "核对是否空泛或重复；真实对比与结果应保留。"),
    ("attribution", r"(?:有|相关|多项|大量)研究(?:均)?(?:表明|显示)|(?:专家|业内|行业)(?:普遍)?(?:认为|指出)", "核对来源与归因，不能删掉归因后改成事实断言。"),
    ("stacked-hedges", r"(?:可能|或许|也许).{0,6}(?:可能|或许|也许)", "检查是否重复限定；保留实际不确定性。"),
)
RULES = tuple((name, re.compile(pattern), message) for name, pattern, message in PATTERNS)
BULLET = re.compile(r"^\s*[-*+•·]\s+")
NUMBERED = re.compile(r"^\s*(?:\d+[.、)]|[（(]\d+[）)])\s*")
HEADING = re.compile(r"^\s*#{1,6}\s+")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
LABEL = re.compile(r"^\s*(?:\*\*[^*\n]{1,30}(?:[：:]\*\*|\*\*[：:])|[^。！？：:]{1,16}[：:])")


def mask_inline(raw: str) -> str:
    """Protect common literal constructs; keep link labels available for review."""
    raw = re.sub(r"(`+).*?\1", " ", raw)
    raw = re.sub(r"\$\$.*?\$\$|(?<!\\)\$(?!\$).*?(?<!\\)\$|\\\(.*?\\\)|\\\[.*?\\\]", " ", raw)
    raw = re.sub(r"!\[[^\]]*\]\([^\n]*?\)", " ", raw)
    raw = re.sub(r"\[([^\]]+)\]\([^\n]*?\)", r"\1", raw)
    raw = re.sub(r"\[[^\]]+\]\[[^\]]*\]", " ", raw)
    raw = re.sub(r"https?://[^\s<>，。；！？“”]+|[A-Za-z]:[\\/][^\s]+", " ", raw)
    raw = re.sub(r"“[^”]*”|「[^」]*」|『[^』]*』", " ", raw)
    raw = re.sub(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?\s*[:：]\s*\d+(?:\.\d+)?(?![A-Za-z0-9_])", " ", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return html.unescape(raw).strip()


def visible_lines(text: str) -> list[tuple[int, str, str]]:
    """Return numbered prose and boundaries without joining protected blocks."""
    source = text.splitlines()
    table_rows: set[int] = set()
    for index, raw in enumerate(source):
        if TABLE_SEP.match(raw):
            table_rows.add(index)
            if index:
                table_rows.add(index - 1)
            cursor = index + 1
            while cursor < len(source) and source[cursor].strip() and "|" in source[cursor]:
                table_rows.add(cursor)
                cursor += 1
    out: list[tuple[int, str, str]] = []
    fence_char, fence_size = "", 0
    frontmatter = False
    math_end = ""
    html_end = ""
    for index, raw in enumerate(source):
        number, stripped = index + 1, raw.strip()
        boundary = (number, "", "boundary")
        if index == 0 and stripped == "---":
            frontmatter = True
            out.append(boundary)
            continue
        if frontmatter:
            if stripped in ("---", "..."):
                frontmatter = False
            out.append(boundary)
            continue
        match = FENCE.match(raw)
        if fence_char:
            if re.fullmatch(rf"\s{{0,3}}{re.escape(fence_char)}{{{fence_size},}}\s*", raw):
                fence_char = ""
            out.append(boundary)
            continue
        if match:
            fence_char, fence_size = match[1][0], len(match[1])
            out.append(boundary)
            continue
        if math_end:
            if math_end in stripped:
                math_end = ""
            out.append(boundary)
            continue
        if stripped.startswith(("$$", r"\[")):
            opener = "$$" if stripped.startswith("$$") else r"\["
            closer = "$$" if opener == "$$" else r"\]"
            if closer not in stripped[len(opener):]:
                math_end = closer
            out.append(boundary)
            continue
        if html_end:
            if html_end in stripped.lower():
                html_end = ""
            out.append(boundary)
            continue
        block = re.search(r"<(script|style|pre|code)\b", raw, re.I)
        if block:
            closer = "</" + block[1].lower() + ">"
            if closer not in raw.lower():
                html_end = closer
            out.append(boundary)
            continue
        if (index in table_rows or stripped.startswith((">", "|", "<!--"))
                or re.match(r"^\s*\[[^\]]+\]:", raw)
                or raw.startswith(("    ", "\t"))):
            out.append(boundary)
            continue
        if not stripped:
            out.append((number, "", "blank"))
            continue
        kind = "heading" if HEADING.match(raw) else "bullet" if BULLET.match(raw) else "numbered" if NUMBERED.match(raw) else "prose"
        clean = mask_inline(raw)
        out.append((number, clean, kind) if clean else boundary)
    return out


def lint(text: str, profile: str = "general") -> list[Issue]:
    if profile not in ("general", "academic", "handout"):
        raise ValueError(f"unknown profile: {profile}")
    issues: list[Issue] = []
    rows = visible_lines(text)
    paragraph: list[tuple[int, str]] = []
    bullets: list[tuple[int, str]] = []

    def add(line: int, rule: str, evidence: str, message: str, level: str = "REVIEW") -> None:
        issues.append(Issue(line, level, rule, evidence[:160], message))

    def flush_paragraph() -> None:
        if not paragraph:
            return
        joined = " ".join(value for _, value in paragraph)
        offsets: list[tuple[int, int]] = []
        offset = 0
        for line, value in paragraph:
            offsets.append((offset, line))
            offset += len(value) + 1
        short: list[tuple[int, str]] = []

        def flush_short() -> None:
            if len(short) >= 3:
                add(short[0][0], "short-run", " ".join(value for _, value in short), "连续短句需连读确认关系；不按字数强制合并。")
            short.clear()

        for match in re.finditer(r"[^。！？]+[。！？]", joined):
            sentence = match[0].strip()
            start = match.start() + len(match[0]) - len(match[0].lstrip())
            line = next(line for position, line in reversed(offsets) if position <= start)
            body = sentence.rstrip("。！？")
            if 0 < len(body) < 15:
                short.append((line, sentence))
            else:
                flush_short()
            if len(body) >= 160 or (len(body) >= 100 and body.count("，") >= 4):
                add(line, "long-sentence", sentence, "较长句是复核线索；检查主干、条件范围与判断重心，不按字数强制拆句。")
        flush_short()
        paragraph.clear()

    def flush_bullets() -> None:
        if len(bullets) >= 4:
            add(bullets[0][0], "bullet-run", bullets[0][1], f"连续 {len(bullets)} 项需判断功能；原理说明可成段，独立清单与必要步骤可保留。")
        bullets.clear()

    for number, clean, kind in rows:
        if kind == "prose":
            paragraph.append((number, clean))
        else:
            flush_paragraph()
        if kind == "bullet":
            bullets.append((number, clean))
        elif kind != "blank":
            flush_bullets()
        if kind in ("blank", "boundary", "heading"):
            continue
        for rule, pattern, message in RULES:
            if pattern.search(clean):
                add(number, rule, clean, message)
        if "—" in clean:
            add(number, "dash", clean, "确认不属于受保护内容后，改写讲义正文中的破折号并保留原有关系。" if profile == "handout" else "检查破折号是否承担必要功能，避免反复插叙。", "STYLE" if profile == "handout" else "REVIEW")
        if profile == "handout" and re.search(r"[：:]", clean):
            add(number, "colon", clean, "确认不属于受保护内容后，把讲义正文的冒号定义或说明写成完整句子。", "STYLE")
        elif LABEL.search(clean) or "：" in clean:
            add(number, "colon-leadin", clean, "检查是否标签式领起；必要定义、字段与指定格式可保留。")
    flush_paragraph()
    flush_bullets()
    return sorted(issues, key=lambda issue: (issue.line, issue.rule))


def self_test() -> int:
    # Keep positive and negative boundaries together, including known old false positives.
    cases = [
        ("handout punctuation", "阈值：0.5——用于判断。", "handout", {"colon", "dash"}, set()),
        ("protected existing heading", "## 文献题名：现象——解释", "handout", set(), {"colon", "dash"}),
        ("general punctuation is review", "阈值：0.5——用于判断。", "general", {"dash", "colon-leadin"}, {"colon"}),
        ("literal constructs", '---\ntitle: 示例——引文\n---\n“原文：标签——阈值”\n`mode: strict` $f:X\\to Y$ https://a.example/x:y\n> 原文：保留——\n```python\nx = "标签：定义——"\n```\n~~~text\n标签：定义——\n~~~\n$$\nf:X\\to Y\n$$\n| 字段 | 值 |\n| --- | --- |\n| 标签：值 | —— |\n', "handout", set(), {"colon", "dash", "short-run"}),
        ("unprefixed table", "字段 | 值\n--- | ---\n标签：定义 | ——\n", "handout", set(), {"colon", "dash"}),
        ("link target", "访问[资料](https://a.example/a:b)，并保留 `C:\\data:v2`。", "handout", set(), {"colon", "dash"}),
        ("math and names", "Macro-F1、MRLQ-EF 与 $a:b$ 保持原样。", "handout", set(), {"colon", "dash"}),
        ("ratio and time", "比例为3:1，时间为10:30。", "handout", set(), {"colon"}),
        ("valid terminology", "控制器使用闭环反馈，保留误差；研究[12]采用被动控制。", "academic", set(), {"attribution", "vague-action"}),
        ("attribution is review", "专家认为可能更稳健，来源尚待核实。", "academic", {"attribution"}, set()),
        ("short run", "模型预测。教师检查。教师纠错。", "handout", {"short-run"}, set()),
        ("no crossing headings", "模型预测。\n\n## 教师\n教师检查。\n\n教师纠错。", "handout", set(), {"short-run"}),
        ("no crossing code", "模型预测。\n```\nx=1\n```\n教师检查。教师纠错。", "handout", set(), {"short-run"}),
        ("numbered steps", "1. 读取数据。\n2. 训练模型。\n3. 保存权重。\n4. 评价结果。", "handout", set(), {"short-run", "bullet-run"}),
        ("bullets only review", "- 项目一\n\n- 项目二\n\n- 项目三\n\n- 项目四", "handout", {"bullet-run"}, set()),
        ("HTML block", '<pre>标签：定义——</pre>\n<script>\nconst x="内容：——";\n</script>', "handout", set(), {"colon", "dash"}),
        ("long sentence", "当" + "固定条件下，" * 24 + "模型输出预测。", "academic", {"long-sentence"}, set()),
    ]
    failed = []
    for name, source, profile, required, forbidden in cases:
        result = lint(source, profile)
        found = {issue.rule for issue in result}
        if not required <= found or forbidden & found:
            failed.append((name, sorted(found)))
        if profile != "handout" and any(issue.level == "STYLE" for issue in result):
            failed.append((name, "unexpected STYLE"))
    print(f"{'FAIL' if failed else 'PASS'}  dou-tone lint self-test ({len(cases)} cases)")
    for item in failed:
        print(item)
    return int(bool(failed))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="UTF-8 text/Markdown files, or - for stdin")
    parser.add_argument("--profile", choices=("general", "academic", "handout"), default="general")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--fail-on-warn", action="store_true", help="also return 1 for REVIEW candidates")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.files:
        parser.error("provide UTF-8 text files, - for stdin, or --self-test")
    results = []
    errors = []
    all_issues = []
    for name in args.files:
        try:
            text = sys.stdin.read() if name == "-" else Path(name).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append({"file": name, "error": str(exc)})
            continue
        issues = lint(text, args.profile)
        all_issues.extend(issues)
        results.append({"file": name, "issues": [asdict(issue) for issue in issues]})
    if args.as_json:
        print(json.dumps({"profile": args.profile, "results": results, "errors": errors, "scope": "pattern candidates only; no factual or quality certification"}, ensure_ascii=False, indent=2))
    else:
        for result in results:
            for issue in result["issues"]:
                print(f'{issue["level"]} {result["file"]}:{issue["line"]} [{issue["rule"]}] {issue["message"]}\n      {issue["evidence"]}')
        for error in errors:
            print(f'ERROR {error["file"]}: {error["error"]}', file=sys.stderr)
        if not all_issues and not errors:
            print("CHECKED  no known patterns found; factual and semantic review still required")
    if errors:
        return 2
    return int(any(issue.level == "STYLE" or args.fail_on_warn for issue in all_issues))


if __name__ == "__main__":
    raise SystemExit(main())
