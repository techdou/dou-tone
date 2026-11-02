# Agent 路由检查

用 `routing.json` 的请求测试文字表达处理是否适用。`expected_apply` 指是否应用本 Skill 的表达工作流，不等于宿主是否加载了 Skill；显式提及维护对象或纯问答时，两者可以不同。场景字段用于人工核对参考选择，不设无上下文的绝对优先级。

## 元数据判断

只向独立执行者提供当前 `name`、`description` 和请求，不提供预期标签、完整正文或其他执行者的答案。要求返回 JSON 数组，每项包含 `id`、布尔 `apply` 及一句 `scope`。记录实际元数据版本，再使用 `python3 "<skill_dir>/evals/check_routing.py" "<decisions.json>"` 对比标签；人工检查混合任务的 scope 是否只包含写作部分。

这是元数据判断检查，不是宿主真实自动调用率。不得用字符串命中、脚本自检或执行者自报结果替代真实调用轨迹，也不得宣称模型或版本间的普遍准确率。

## 实际工作流

将具体原稿与真实写作请求交给独立执行者，只给 Skill 路径，不给预期答案或诊断。可从 `writing.md` 选择原始材料；其他材料作为保留样本，避免只在同一案例上反复调参。

分别核对是否读取正确参考、是否遵守编辑范围、是否保留独立信息和受保护内容，以及是否交付用户需要的文本或诊断。事实漂移、术语错配、擅自写回文件和把讲义规则套在其他交付物上均为失败。

## 维护方式

先确定实际问题出在元数据匹配、参考路由、执行还是输出，再修改对应层。缺少真实调用轨迹时如实记录验证边界；不为了通过现有样例堆叠关键词或强改已合格文本。

规范与方法依据为 [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills)、[插件 Skill 工作流边界](https://developers.openai.com/plugins/build/skills) 和 [Skill Evals](https://developers.openai.com/blog/eval-skills)。区分格式校验、元数据判断和实际工作流验证，不互相代替。
