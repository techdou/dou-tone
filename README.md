# dou-tone

`dou-tone` 是一个面向个人长期使用的中文写作、改写与润色 Skill。它负责文字层的校对、润色、重写、整理成稿与文体适配，在不改变事实边界的前提下，让正式报告、科研材料、项目方案、教学文案、PPT 和个人内容更准确、自然、完整。

它不是通用问答 Skill，也不会仅因为内容涉及科研、项目、教学或文档就自动介入。纯事实问答、概念解释、资料检索、代码修改、忠实翻译、仅摘要或信息抽取，以及只生成文件格式而未要求文字改写时，不应使用 `dou-tone`。

## 适合处理

- 工作总结、汇报、建设方案、申请与调研材料
- 论文、开题报告、研究现状、实验分析与科研汇报
- AI / Agent / Web / 3D / 软件项目需求与技术方案
- 教案、说课稿、教学设计与课堂材料
- PPT 标题、页面文案与讲稿配套文字
- 博客、公众号、个人简介、GitHub 项目介绍与社交内容
- 日常草稿、口述和要点整理

## Agent 匹配

`SKILL.md` 的 `description` 同时定义正向触发和负向边界。

典型正向意图：

- 润色、校对、深度润色
- 改写、重写、重新整理
- 根据材料整理成稿
- 优化表达、改正式、改自然
- 用我的语气、减少 AI 套话

典型负向意图：

- 纯问答、解释、检索和论文解读
- 代码编写、调试和代码审查
- 忠实翻译
- 仅摘要、抽取、分类或核对信息
- 只创建 DOCX / PDF / PPTX 等文件而没有文字改写要求

Skill 激活后还会执行一次边界判断，避免宿主过度匹配。

## 改写级别

1. **L1 校对**：只修错别字、标点、明显语病和格式错误。
2. **L2 润色**：优化措辞、句式和衔接，不改观点、结构和详略比例；“润色”默认使用这一档。
3. **L3 深度润色**：允许调整句序、段落和局部结构，不增加新事实。
4. **L4 重写**：保留事实与核心意思，重新组织表达和结构。
5. **L5 成稿**：根据已有材料整理成可直接提交、汇报或发布的完整文本。

任何级别都不能通过润色制造新的事实、引用、经历、实验结果、产品能力或完成状态。

## 渐进加载

主 `SKILL.md` 只保存所有写作场景都需要的规则。具体文体规范放在 `references/`：

```text
references/
├── academic-writing.md
├── daily-writing.md
├── personal-writing.md
├── ppt-writing.md
├── project-writing.md
├── report-writing.md
└── teaching-writing.md
```

Agent 默认只读取一个主场景文件；真正的混合任务最多再读取一个辅助场景文件。例如：

- 科研汇报 PPT：`academic-writing.md` + `ppt-writing.md`
- 项目建设方案：`report-writing.md` + `project-writing.md`

不要一次性加载全部 references。

## 仓库结构

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
├── scripts/
│   └── dou_lint.py
├── evals/
│   └── matching.md
├── .github/
│   └── workflows/
│       └── validate-skill.yml
├── NOTICE.md
└── LICENSE
```

仓库根目录本身就是标准 Skill 目录，不再额外套一层 `skills/dou-tone/`。

## 使用示例

```text
使用 $dou-tone 润色这份工作总结，保持原结构和数字不变。
```

```text
使用 $dou-tone 按硕士论文语言深度润色这一节，不修改学术观点，不补造引用。
```

```text
使用 $dou-tone 把这些口述需求整理成给甲方看的项目需求说明，不展开低层实现细节。
```

```text
使用 $dou-tone 把这份教学设计改得更适合课堂表达，保留教学目标和知识点。
```

## lint

`dou_lint.py` 使用 FAIL / WARN 两级规则：FAIL 表示比较确定的语言问题，WARN 表示需要结合文体和上下文判断。

```bash
python scripts/dou_lint.py --self-test
python scripts/dou_lint.py draft.md
```

lint 只能检查已知文本模式，不能验证事实、引用、科学结论和业务状态，也不能替代完整通读。

## 验证

仓库 CI 会执行：

1. Agent Skills reference validator 校验根目录 Skill；
2. Python 脚本编译；
3. `dou_lint.py --self-test`。

Agent discovery 的人工回归样例位于 `evals/matching.md`。

## 来源与许可证

`dou-tone` 最初基于 `oil-oil/oil-tone` 的事实边界、自然表达与去 AI 味规则演化，并经过面向多文体写作、Agent 自动匹配、渐进加载和质量验证的独立重构。详细来源说明见 `NOTICE.md`。

项目按 MIT License 发布。