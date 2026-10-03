# dou-tone

面向个人长期使用的中文写作技能：让文字自然、易读、通顺、清楚，保留事实、作者声音和不同文体的用途。入口与完整规则见 [SKILL.md](SKILL.md)。

支持校对、润色、重写、文体转换和基于材料成稿。纯问答、检索、代码修改、忠实翻译、仅信息抽取及文件转换不会单独触发；混合任务只处理写作部分。PPT 文案可以润色，文件制作由 `ppt-studio` 负责。

## 安装与更新

仓库根目录就是标准技能目录；选择宿主支持的 skills 路径安装一次，避免在多个可发现目录重复注册。

```bash
# 多宿主共享路径
git clone https://github.com/techdou/dou-tone.git ~/.agents/skills/dou-tone

# 或安装到 Claude Code 路径
git clone https://github.com/techdou/dou-tone.git ~/.claude/skills/dou-tone
```

以上命令用于目标目录不存在时。若目录已是 Git 检出，确认本地改动已保存后执行 `git pull --ff-only`；出现分叉时先合并，不覆盖改动。只有文件副本的安装应先备份，再从维护仓库同步，不直接在非 Git 目录运行 `git pull`。

## 使用

```text
使用 $dou-tone 润色这份工作总结，保留原结构、数字和完成状态。
使用 $dou-tone 把这些材料整理成公众号文章，沿用我的语气，不添加亲身经历。
使用 $dou-tone 优化这一页 PPT 的标题与正文，保留科研术语和数据。
```

改写幅度使用 L1 校对、L2 润色、L3 深度润色、L4 重写、L5 成稿；“润色”默认 L2。用户的具体限制优先，不需要额外选择档位。

## 场景参考

简单短稿直接处理；按用途读取所需参考，不一次加载全部文件。

| 用途 | 参考 |
|---|---|
| 日常短说明、沟通 | [daily-writing.md](references/daily-writing.md) |
| 工作报告、方案、申请 | [report-writing.md](references/report-writing.md) |
| 论文、开题、科研汇报 | [academic-writing.md](references/academic-writing.md) |
| 需求、技术方案、README | [project-writing.md](references/project-writing.md) |
| 教案、说课、课堂材料 | [teaching-writing.md](references/teaching-writing.md) |
| PPT 标题、正文、讲稿 | [ppt-writing.md](references/ppt-writing.md) |
| 公众号、博客、个人介绍 | [personal-writing.md](references/personal-writing.md) |
| 去 AI 味、作者语气校准 | [humanizer-lessons.md](references/humanizer-lessons.md) |

主场景与辅助参考只按实际需要组合。Humanizer 的编辑经验沉淀在本技能内，不另设重复入口。

## 可选检查

检查脚本只提供上下文复核提示，不自动改文，不把自然口语判为失败，也不能核验事实或检测作者身份。`WARN` 定位词句，`STRUCT` 定位加粗冒号段首、连续长列表项和连续短句；后两项使用数量或长度阈值辅助定位，不表示必须按阈值改稿。列表、字段、步骤和有意修辞应按用途保留。

```bash
python3 scripts/dou_lint.py --self-test
python3 scripts/dou_lint.py draft.md
```

默认 `WARN` 或 `STRUCT` 命中均返回 0；成功读取且无命中只表示“未发现已知模式”，不代表质量已通过。读取错误返回 2。为兼容既有手动流程保留 `--fail-on-warn`，显式使用时任一类命中返回 1；它只是提醒信号，不是客观质量判定，不作为默认交付门槛。

## 维护与来源

[evaluations](evals/matching.md) 包含触发边界和行为验收用例，供人工或独立评估使用；未执行的用例不能算作已验证。现有 CI 校验技能格式、Python 编译和脚本自测。

本技能独立维护，选择性吸收 [oil-oil/oil-tone](https://github.com/oil-oil/oil-tone) 与 Humanizer 的编辑经验，不自动同步、安装上游或固定模型与工具接口。核验提交、吸收范围与 MIT 许可见 [NOTICE.md](NOTICE.md) 和 [LICENSE](LICENSE)。
