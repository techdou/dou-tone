# dou-tone

按豆哥文风审阅、润色、改写中文及中英混排正文，保持专业、准确、自然、连贯。完整执行规则见 [SKILL.md](SKILL.md)。

支持文字审阅、L1–L4 改写及根据材料成稿。纯概念问答、检索解读、研究设计、事实核验、代码修改、忠实翻译、信息提取和仅排版转格式不单独触发；混合任务只处理写作部分。DOCX、PDF 和 PPTX 的制作由可用的文件能力负责。

## 安装与更新

仓库根目录就是技能目录，选择宿主支持的一个位置，避免重复注册。

```bash
# 多宿主共享路径
git clone https://github.com/douxl-lab/dou-tone.git ~/.agents/skills/dou-tone

# 或安装到 Claude Code 路径
git clone https://github.com/douxl-lab/dou-tone.git ~/.claude/skills/dou-tone
```

已有 Git 检出应先保存本地改动，再执行 `git pull --ff-only`。遇到分叉时先合并，不覆盖本地修改。上述命令用于本地宿主；ChatGPT 中的技能安装由其技能管理入口完成。

## 使用

```text
使用 $dou-tone 按 L2 润色这段论文，保留术语、数值、全部引用和必要限定。
使用 $dou-tone 把这些知识点整理成学生可独立阅读的讲义，不增加实验事实。
使用 $dou-tone 审阅这份讲义的文风，只给建议，不修改文件。
使用 $dou-tone 分别整理讲义正文和一页 PPT 文案，按各自用途表达。
```

“润色”默认 L2；L1 只校对，L3 可调整局部结构，L4 可重写，L5 根据材料组织成稿。用户的具体范围与限制优先，材料足够时无需额外选择档位。

## 学术与讲义规则

学术材料保留概念、公式、引用、实验条件和主张强度，不能通过润色制造显著性、因果或创新结论。讲义面向学生独立阅读，以连贯自然段解释概念和机制；可改写正文不使用破折号、冒号或标签式段首，原文引语、代码、公式和固定格式按原样保留。

相关碎句按真实关系组织，多层条件和长定语按意义拆分，不设置句长、段落句数或列表数量配额。原理说明、实验步骤与 PPT 页面分别处理，必要步骤保留编号。

| 用途 | 按需读取 |
| --- | --- |
| 论文、开题、科研汇报 | [academic-writing.md](references/academic-writing.md) |
| 学生讲义、教材、教程正文 | [handout-writing.md](references/handout-writing.md) |
| 教案、说课、教师活动 | [teaching-writing.md](references/teaching-writing.md) |
| PPT 标题、页面与配套文字 | [ppt-writing.md](references/ppt-writing.md) |
| 报告、方案与申请 | [report-writing.md](references/report-writing.md) |
| 技术方案、需求与部署说明 | [project-writing.md](references/project-writing.md) |
| 日常短说明 | [daily-writing.md](references/daily-writing.md) |
| 博客、公众号和个人介绍 | [personal-writing.md](references/personal-writing.md) |
| 作者声音校准与模板化表达 | [humanizer-lessons.md](references/humanizer-lessons.md) |
| 已定位的具体表达问题 | [humanizer-patterns.md](references/humanizer-patterns.md) |

默认读取当前交付物的一个主参考，必要时补辅助内容；不一次加载全部文件。与专业或文件技能协作时只形成一份成稿，不重复启动重写流程。

## 可选检查

从仓库根目录可运行以下命令；其他目录请使用脚本和输入文件的绝对路径。

```bash
python3 scripts/dou_lint.py --self-test
python3 scripts/dou_lint.py --profile handout draft.md
python3 scripts/dou_lint.py --profile academic --json draft.md
python3 evals/check_routing.py --self-test
```

脚本只读取 UTF-8 文本或 Markdown，不直接读取 DOCX/PDF。STYLE 是讲义标点约束候选，REVIEW 是需结合语义复核的线索；不自动改稿、不核验事实，不证明全文质量或作者身份。退出码 0 表示未命中所选失败条件，1 表示 STYLE 命中或启用 `--fail-on-warn` 后的 REVIEW 命中，2 表示读取错误。短稿可直接人工终检。

## 验证与维护

[路由检查说明](evals/matching.md) 区分元数据判断与实际工作流，[routing.json](evals/routing.json) 包含 24 条正向、间接、反向、混合与维护请求，[writing.md](evals/writing.md) 提供写作场景。独立执行者只接收请求与必要元数据，不接收预期答案。已有判断结果可运行：

```bash
python3 evals/check_routing.py decisions.json
```

该比较器核对标签完整性与一致性，不代表宿主真实自动调用率；scope 与具体工作流仍须人工复核。CI 检查技能格式、Python 编译、文本检查器和路由比较器自检，不将未执行的用例计为通过。

本仓库为 [techdou/dou-tone](https://github.com/techdou/dou-tone) 的 fork，保留已有 Humanizer 参考与来源说明，并独立维护学术、讲义与 Agent 调用规则。MIT 许可与具体来源见 [NOTICE.md](NOTICE.md) 和 [LICENSE](LICENSE)。
