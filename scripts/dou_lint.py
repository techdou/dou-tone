#!/usr/bin/env python3
"""Advisory Chinese prose checks. Matches need context; they never prove a defect."""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

Rule = tuple[re.Pattern[str], str]

# Avoid single-word bans: legitimate wording and technical terms need context.
WARN_RULES: tuple[Rule, ...] = tuple(
    (re.compile(pattern), message) for pattern, message in (
        (r"(?:在当今|在当前).{0,18}(?:时代|背景|环境)下",
         "背景是否有助于理解后文？有具体条件时保留，空泛铺垫再删。"),
        (r"随着.{0,18}(?:不断|持续)(?:发展|演变|变化)",
         "这项变化与后文有什么具体关系？已有关系时无需删除。"),
        (r"(?:值得注意的是|需要指出的是|毋庸置疑|不可否认的是?)",
         "领起语是否承担真实提醒、限定或转折？不要仅凭措辞替换。"),
        (r"(?:标志着|代表着).{0,24}(?:重要|关键)(?:一步|时刻|转折点)",
         "该判断是否有材料支持？保留有依据的评价，空泛时说明具体变化。"),
        (r"为.{1,24}奠定(?:了)?(?:坚实的?)?基础",
         "是否交代了具体后续条件？有实际含义时保留。"),
        (r"(?:彰显|凸显|体现)(?:了)?.{0,20}(?:重要性|意义|价值)",
         "评价是否增加信息并有依据？不要补造效果来替换。"),
        (r"(?:业内|行业|专家|观察者)(?:普遍)?(?:认为|指出|表示)",
         "附近是否有明确来源或归因？不能自行编造权威背书。"),
        (r"(?:很多|不少|部分)用户(?:认为|指出|表示|反馈)",
         "反馈是否来自所提供的材料？有证据时保留原归因与范围。"),
        (r"(?:有|相关|多项|大量)研究(?:均)?(?:表明|显示|指出)",
         "检查附近引文或已知来源；真实引用不因命中而删去。"),
        (r"(?:从而确保|进而体现|进一步彰显|反映了更深层次)",
         "因果或解释是否有材料支持？语义成立时保留。"),
        (r"尽管.{0,24}(?:挑战|困难).{0,24}(?:仍|依然|未来)",
         "是否写清实际困难和后续安排？真实转折与计划可以保留。"),
        (r"(?:未来可期|迈出(?:了)?(?:至关重要|重要|关键)的一步|开启(?:了)?(?:全新|新的?)篇章)",
         "结尾是否提供新信息或作者有依据的判断？无需强加总结。"),
        (r"(?:当然可以|这是一个(?:非常|很)?好的问题|你说得(?:完全)?正确|希望这对(?:你|您)有帮助|如需更多(?:信息|帮助).{0,8}(?:请)?(?:随时)?(?:告诉我|联系我))",
         "是否属于独立成稿中的聊天包装？邮件、引语与真实对话按用途保留。"),
        (r"(?:可能|或许|也许|在一定程度上|在某种程度上).{0,8}(?:可能|或许|也许|在一定程度上|在某种程度上)",
         "限定是否重复修饰同一判断？不同条件或对象不能一并删去。"),
        (r"(?:全面赋能|打造(?:全新)?生态|沉淀价值|形成强大合力)",
         "是否有具体对象、动作与作用？保留必要术语，空泛时回到材料。"),
        (r"(?:原因很简单[：:]|真正重要的是|真正的关键是|从更大的角度看)",
         "后文是否增加必要原因或判断？不要把有内容的引导句当作禁语。"),
    )
)


def read_text(name: str) -> str:
    if name == "-":
        return sys.stdin.read()
    try:
        return Path(name).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read UTF-8 file {name}: {exc}") from exc


def visible_lines(text: str) -> list[tuple[int, str]]:
    """Lightweight prose extraction, preserving source line numbers, not a parser."""
    raw_lines = text.splitlines()
    start = 0
    if raw_lines and raw_lines[0].strip() == "---":
        for index in range(1, len(raw_lines)):
            if raw_lines[index].strip() in ("---", "..."):
                start = index + 1
                break
    fence_char = ""
    fence_length = 0
    prose: list[str] = []
    for number, raw in enumerate(raw_lines, start=1):
        if number <= start:
            prose.append("")
            continue
        if fence_char:
            if re.fullmatch(r" {0,3}" + re.escape(fence_char) + "{" +
                            str(fence_length) + r",}\s*", raw):
                fence_char = ""
            prose.append("")
            continue
        opener = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", raw)
        if opener and not (opener[1][0] == "`" and "`" in opener[2]):
            fence_char, fence_length = opener[1][0], len(opener[1])
            prose.append("")
            continue
        prose.append(re.sub(r"(`+).*?\1", " ", raw))
    # Protect code before interpreting HTML-like strings as markup.
    hidden = re.compile(
        r"<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)",
        re.IGNORECASE | re.DOTALL,
    )
    visible = hidden.sub(lambda match: "\n" * match.group().count("\n"),
                         "\n".join(prose))
    lines: list[tuple[int, str]] = []
    for number, raw in enumerate(visible.splitlines(), start=1):
        clean = re.sub(r"<[^>]+>", " ", raw)
        clean = html.unescape(re.sub(r"\s+", " ", clean)).strip()
        if clean:
            lines.append((number, clean))
    return lines


def scan(text: str, rules: tuple[Rule, ...] = WARN_RULES) -> list[tuple[int, str, str]]:
    return [
        (number, line, message)
        for number, line in visible_lines(text)
        for pattern, message in rules
        if pattern.search(line)
    ]


# Heuristics locate passages to review; these thresholds are not writing quotas.
BULLET_RE = re.compile(r"^(?:[-*+•·]|\d{1,3}[.、)])\s+")
BOLD_COLON_RE = re.compile(r"^\*\*[^*\n]{1,40}(?:[:：]\s*\*\*|\*\*\s*[:：])")
NON_PROSE_RE = re.compile(r"^(?:#{1,6}\s|[|>])")


def structural_checks(text: str) -> list[tuple[int, str, str]]:
    """Find structural hints without joining unrelated blocks or rewriting text."""
    lines = visible_lines(text)
    out: list[tuple[int, str, str]] = []
    for number, line in lines:
        if BOLD_COLON_RE.match(line):
            out.append((number, line,
                        "加粗冒号段首是否只在包装要点？字段、定义与指定格式可以保留。"))

    run: list[tuple[int, str]] = []

    def flush_bullets() -> None:
        if len(run) >= 4:
            out.append((run[0][0], run[0][1][:60],
                        f"连续 {len(run)} 条长列表项：检查是否属于连贯论述；"
                        "独立并列信息、步骤、规格和用户指定列表可以保留。"))
        run.clear()

    for number, line in lines:
        bullet = BULLET_RE.match(line)
        if bullet and len(line[bullet.end():]) >= 12:
            if run and number != run[-1][0] + 1:
                flush_bullets()
            run.append((number, line))
        else:
            flush_bullets()
    flush_bullets()

    paragraph: list[tuple[int, str]] = []

    def flush_paragraph() -> None:
        if not paragraph:
            return
        joined = "\n".join(line for _, line in paragraph)
        short: list[tuple[int, str]] = []

        def flush_short() -> None:
            if len(short) >= 3:
                out.append((short[0][0], " ".join(s for _, s in short)[:60],
                            "同段连续短句：检查是否缺少句间关系；"
                            "有意节奏和独立判断可以保留，不为合并补造因果。"))
            short.clear()

        for match in re.finditer(r"[^。！？]*[。！？]", joined):
            sentence = match[0].strip()
            body = re.sub(r"\s+", "", sentence[:-1])
            if 0 < len(body) < 15:
                offset = match.start() + len(match[0]) - len(match[0].lstrip())
                number = paragraph[joined[:offset].count("\n")][0]
                short.append((number, sentence))
            else:
                flush_short()
        flush_short()
        paragraph.clear()

    for number, line in lines:
        if BULLET_RE.match(line) or NON_PROSE_RE.match(line):
            flush_paragraph()
            continue
        if paragraph and number != paragraph[-1][0] + 1:
            flush_paragraph()
        paragraph.append((number, line))
    flush_paragraph()
    return out


def self_test() -> int:
    # Verify boundaries and scanning behavior, not linguistic quality.
    tick = chr(96)
    natural = "\n".join((
        "我先搞清楚报错，再跑测试；修好后就告诉你。",
        "把事实找出来，才能判断这个问题怎么处理。",
        "控制器通过闭环反馈调整输出。",
        "王某等人的研究表明，结果仅适用于该样本[1]。",
        "这项政策可能影响结果，效果尚未测试。",
    ))
    protected = (
        "---\ntitle: 全面赋能\n---\n"
        f"{tick*4}markdown\n{tick*3}\n全面赋能\n{tick*3}\n{tick*4}\n"
        "~~~text\n全面赋能\n~~~\n"
        "<!-- 全面赋能 -->\n"
        "<script>全面赋能</script><p>普通正文</p>\n"
        "<style>\n全面赋能\n</style>\n"
        f"使用 {tick}全面赋能{tick} 作为示例字符串。\n"
        f"使用 {tick*2}包含 {tick}全面赋能{tick} 的示例{tick*2}。\n"
        "普通正文\n全面赋能开发团队。\n"
    )
    checks = {
        "natural wording and technical terms": not scan(natural),
        "review-worthy wording is reported": bool(scan("相关研究表明，产品未来可期。")),
        "protected regions and line numbers": [n for n, _, _ in scan(protected)] == [20],
        "prose after an HTML block stays visible": bool(
            scan("<script>ignored</script><p>全面赋能</p>")),
        "short fences do not close long fences": not scan(
            f"{tick*4}\n{tick*3}\n全面赋能\n{tick*3}\n{tick*4}"),
        "longer closing fences work": bool(scan("~~~\nignored\n~~~~\n全面赋能")),
        "unclosed code is protected": not scan(f"{tick*3}\n全面赋能"),
        "HTML examples in fences cannot hide following prose": bool(scan(
            f"{tick*3}html\n<script>\n{tick*3}\n全面赋能")),
        "inline HTML examples cannot hide following prose": bool(scan(
            f"使用 {tick}<script>{tick} 标签。\n全面赋能")),
        "structural hints are reported": len(structural_checks(
            "**方案：**说明内容。\n"
            "- 首先检查材料中的日期和负责人信息。\n"
            "- 然后核对正文中的数字与引用来源。\n"
            "- 再次查看各项工作的计划和完成状态。\n"
            "- 最后保留与材料一致的原有段落结构。\n"
            "先看输入。\n再查日志。\n最后复核。")) == 3,
        "short sentences do not cross paragraph boundaries": not structural_checks(
            "先看输入。\n\n再查日志。\n\n最后复核。"),
        "headings break short-sentence runs": not structural_checks(
            "先看输入。\n## 检查\n再查日志。\n## 复核\n最后复核。"),
        "code examples do not trigger structural hints": not structural_checks(
            f"{tick*3}\n**字段：**示例。\n先看输入。再查日志。最后复核。\n{tick*3}"),
        "bold text inside a paragraph is not a paragraph lead": not structural_checks(
            "需要核对 **字段：** 的名称，但不能根据格式推断文本质量。"),
        "separated lists are not one run": not structural_checks(
            "- 首先检查材料中的日期和负责人信息。\n"
            "- 然后核对正文中的数字与引用来源。\n\n"
            "- 再次查看各项工作的计划和完成状态。\n"
            "- 最后保留与材料一致的原有段落结构。"),
        "short-sentence locations retain source lines": any(
            number == 3 for number, _, _ in structural_checks(
                "# 标题\n\n先看输入。\n再查日志。\n最后复核。")),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        print("FAIL  dou-tone lint self-test: " + ", ".join(failed))
        return 1
    print(f"PASS  dou-tone lint self-test ({len(checks)} boundary checks)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Find Chinese prose worth contextual review.")
    parser.add_argument("files", nargs="*", help="UTF-8 files, or - for stdin")
    parser.add_argument("--self-test", action="store_true", help="check scanning boundaries")
    parser.add_argument("--fail-on-warn", action="store_true",
                        help="explicitly return 1 on a warning; not a quality verdict")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.files:
        parser.error("provide UTF-8 files, stdin (-), or --self-test")
    warned = read_error = False
    for name in args.files:
        try:
            text = read_text(name)
        except ValueError as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            read_error = True
            continue
        for number, line, message in scan(text):
            print(f"WARN  {name}:{number}: {line}\n      {message}")
            warned = True
        for number, line, message in structural_checks(text):
            print(f"STRUCT {name}:{number}: {line}\n      {message}")
            warned = True
    if read_error:
        return 2
    if not warned:
        print("INFO  no known patterns found; full contextual review is still needed")
    return 1 if warned and args.fail_on_warn else 0


if __name__ == "__main__":
    raise SystemExit(main())
