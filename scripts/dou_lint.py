#!/usr/bin/env python3
"""Deterministic lint checks for dou-tone Chinese writing.

FAIL means the pattern is considered a confirmed writing problem in normal
finished copy. WARN means the pattern needs contextual review and must not be
removed mechanically.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

Rule = tuple[re.Pattern[str], str]

FAIL_RULES: tuple[Rule, ...] = (
    (re.compile(r"先保哪一个|保(?:重点|逻辑|意思|准确|清楚|自然|风格|质量|结构)"), "使用“遵循、保留、确保”等准确动词。"),
    (re.compile(r"(?:一个|这个)?(?:代码)?问题.{0,8}怎么走"), "改成能够说明真实处理过程的表达。"),
    (re.compile(r"(?:线索|结果|结论|内容).{0,8}(?:带回来|丢回来|交回来)"), "写清楚谁说明、提交或返回了什么。"),
    (re.compile(r"(?:先)?把(?:事实|证据).{0,8}(?:找出来|建立(?:起来)?)"), "改成查看、检查、确认等具体动作。"),
    (re.compile(r"(?:逻辑|流程).{0,6}跑(?:到|下去)"), "使用“执行”或具体说明调用关系。"),
    (re.compile(r"(?:问题|流程|事情|能力|价值).{0,6}落(?:下去|到|地)"), "说明具体实现、应用或处理动作。"),
    (re.compile(r"(?:吃下|吞下).{0,10}(?:对话|内容|信息|上下文)"), "改用读取、接收、包含等准确动词。"),
    (re.compile(r"(?:把)?(?:内容|信息|上下文).{0,8}(?:塞进|塞到|喂给)"), "改用写入、添加、提供等准确动词。"),
    (re.compile(r"跑测试"), "使用“运行测试”。"),
    (re.compile(r"(?:搞|弄)(?:顺|清楚|明白|好|完|懂|定|起来|下去)"), "说明具体动作和结果，不使用含义含糊的动作词。"),
    (re.compile(r"承接(?:需求|任务|工作|内容)"), "说明具体是处理、负责、实现还是接收。"),
    (re.compile(r"(?:赋能|撬动|抓手|闭环|沉淀价值|价值落地)"), "删除宣传黑话，直接说明具体作用。"),
    (re.compile(r"原因很简单[：:，,。]?"), "删除模板化领起语，直接说明具体原因。"),
    (re.compile(r"(?:真正重要的是|真正的关键是|这不仅仅?是|从更大的角度看)"), "删除没有增加信息的总结或升华表达。"),
    (re.compile(r"任务.{0,12}停在[“\"]?代码已经写出来"), "直接说明代码完成后还需要执行哪些检查。"),
    (re.compile(r"(?:当然可以|希望这对(?:你|您)有帮助|如需更多(?:信息|帮助).{0,8}(?:请)?(?:随时)?(?:告诉我|联系我))"), "删除成稿中的聊天残留。"),
)

WARN_RULES: tuple[Rule, ...] = (
    (re.compile(r"(?:在当今|在当前).{0,18}(?:时代|背景|环境)下"), "确认背景是否提供必要信息，否则直接进入具体内容。"),
    (re.compile(r"随着.{0,18}(?:不断|持续)(?:发展|演变|变化)"), "确认变化是否与后文存在具体关系。"),
    (re.compile(r"(?:值得注意的是|需要指出的是|毋庸置疑|不可否认的是?)"), "确认领起语是否承担真实限定或转折。"),
    (re.compile(r"(?:标志着|代表着).{0,24}(?:重要|关键)(?:一步|时刻|转折点)"), "改为材料已经确认的动作、变化或结果。"),
    (re.compile(r"为.{1,24}奠定(?:了)?(?:坚实的?)?基础"), "说明具体产生了什么后续条件或结果。"),
    (re.compile(r"(?:彰显|凸显|体现)(?:了)?.{0,20}(?:重要性|意义|价值)"), "确认重要性判断是否有材料支持。"),
    (re.compile(r"(?:业内|行业|专家|观察者)(?:普遍)?(?:认为|指出|表示)"), "给出明确来源；没有来源时删除模糊归因。"),
    (re.compile(r"(?:很多|不少|部分)用户(?:认为|指出|表示|反馈)"), "确认用户反馈是否有明确材料依据。"),
    (re.compile(r"(?:有|相关|多项|大量)研究(?:均)?(?:表明|显示|指出)"), "学术文本需要明确来源；其他文本避免模糊权威背书。"),
    (re.compile(r"(?:从而确保|进而体现|进一步彰显|反映了更深层次)"), "确认尾句是否有真实因果或材料依据。"),
    (re.compile(r"尽管.{0,24}(?:挑战|困难).{0,24}(?:仍|依然|未来)"), "直接说明已经确认的限制、结果或后续安排。"),
    (re.compile(r"(?:未来可期|迈出(?:了)?(?:至关重要|重要|关键)的一步|开启(?:了)?(?:全新|新的?)篇章)"), "删除通用乐观结尾，改写为具体结果或安排。"),
    (re.compile(r"(?:这是一个(?:非常|很)?好的问题|你说得(?:完全)?正确)"), "成稿中删除聊天式回应；对话回复中结合上下文判断。"),
    (re.compile(r"(?:可能|或许|也许|在一定程度上|在某种程度上).{0,8}(?:可能|或许|也许|在一定程度上|在某种程度上)"), "合并重复限定，保留一个符合事实状态的说法。"),
)


def read_text(name: str) -> str:
    if name == "-":
        return sys.stdin.read()
    try:
        return Path(name).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"file not found: {name}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"file is not valid UTF-8: {name}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read {name}: {exc}") from exc


def visible_lines(text: str) -> list[tuple[int, str]]:
    """Return visible prose while skipping fenced code and script/style blocks."""
    lines: list[tuple[int, str]] = []
    in_fence = False
    in_script = False
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.search(r"<(script|style)\b", raw, flags=re.IGNORECASE):
            in_script = True
        if in_script:
            if re.search(r"</(script|style)>", raw, flags=re.IGNORECASE):
                in_script = False
            continue
        clean = re.sub(r"<[^>]+>", " ", raw)
        clean = re.sub(r"`[^`]*`", " ", clean)
        clean = html.unescape(re.sub(r"\s+", " ", clean)).strip()
        if clean:
            lines.append((number, clean))
    return lines


def scan(text: str, rules: tuple[Rule, ...]) -> list[tuple[int, str, str]]:
    out: list[tuple[int, str, str]] = []
    for line_no, line in visible_lines(text):
        for pattern, message in rules:
            if pattern.search(line):
                out.append((line_no, line, message))
    return out


def self_test() -> int:
    bad = "\n".join(
        (
            "模型不知道先保哪一个。",
            "一个代码问题平时可以怎么走。",
            "Explorer 把线索带回来。",
            "先把事实找出来。",
            "这个流程怎么跑下去。",
            "让这个能力落下去。",
            "子 Agent 直接吃下整段上下文。",
            "把内容塞进提示词。",
            "让模型跑测试。",
            "先把这段流程搞顺。",
            "这个功能负责承接需求。",
            "这套方案可以赋能开发团队。",
            "原因很简单：它读取了错误的文件。",
            "真正重要的是，我们理解了工具的边界。",
            "任务不必停在“代码已经写出来”。",
            "当然可以，以下是修改后的正文。",
        )
    )
    good = "\n".join(
        (
            "模型必须先遵循事实准确这项要求。",
            "一个代码问题通常按调用关系定位。",
            "Explorer 说明查到的调用和配置。",
            "查看调用和配置，确认当前实现。",
            "这个流程由主 Agent 继续执行。",
            "实现这项能力。",
            "子 Agent 读取与任务有关的对话。",
            "把内容写入提示词。",
            "让模型运行测试。",
            "这个功能负责处理需求。",
            "产品支持批量处理和离线模式。",
        )
    )
    warn_bad = "\n".join(
        (
            "在当前复杂环境下，团队需要保持敏捷。",
            "随着人工智能技术的不断发展，工具越来越多。",
            "值得注意的是，这项功能已经发布。",
            "这标志着产品迈出了重要一步。",
            "这次更新为后续增长奠定了坚实的基础。",
            "这体现了自动化的重要性。",
            "业内普遍认为，这种方案更可靠。",
            "不少用户反馈，新的设计更自然。",
            "有研究表明，这种方法可以提高效率。",
            "这项改动进一步彰显了产品价值。",
            "尽管面临诸多挑战，团队未来仍将继续前进。",
            "产品完成升级，未来可期。",
            "这是一个很好的问题。",
            "这项政策可能在一定程度上或许会影响结果。",
        )
    )
    warning_good = "\n".join(
        (
            "2026 年 9 月接口升级后，旧版客户端无法继续登录。",
            "清华大学发布的报告显示，样本中的响应时间缩短了 12%。",
            "这项政策可能影响结果。",
        )
    )
    failures = scan(bad, FAIL_RULES)
    warnings = scan(warn_bad, WARN_RULES)
    failure_lines = {line_number for line_number, _, _ in failures}
    warning_lines = {line_number for line_number, _, _ in warnings}
    ok = (
        failure_lines == set(range(1, len(bad.splitlines()) + 1))
        and not scan(good, FAIL_RULES)
        and not scan(good, WARN_RULES)
        and warning_lines == set(range(1, len(warn_bad.splitlines()) + 1))
        and not scan(warning_good, WARN_RULES)
    )
    print("PASS  dou-tone lint self-test" if ok else "FAIL  dou-tone lint self-test")
    if not ok:
        for item in failures:
            print(f"      FAIL sample: {item}")
        for item in warnings:
            print(f"      WARN sample: {item}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Check UTF-8 text for known dou-tone writing issues.")
    parser.add_argument("files", nargs="*", help="UTF-8 files to scan, or - for stdin")
    parser.add_argument("--self-test", action="store_true", help="run deterministic rule self-tests")
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="return a non-zero status when contextual warnings are found",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.files:
        parser.error("provide one or more UTF-8 files, or use --self-test")

    failed = False
    warned = False
    read_error = False
    for name in args.files:
        try:
            text = read_text(name)
        except ValueError as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            read_error = True
            continue
        for line_no, line, message in scan(text, FAIL_RULES):
            print(f"FAIL  {name}:{line_no}: {line}\n      {message}")
            failed = True
        for line_no, line, message in scan(text, WARN_RULES):
            print(f"WARN  {name}:{line_no}: {line}\n      {message}")
            warned = True

    if read_error:
        return 2
    if not failed and not warned:
        print("PASS  no known dou-tone issues")
    elif not failed:
        print("PASS  no confirmed failures; review warnings")
    if failed or (warned and args.fail_on_warn):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
