# 华为云码道（CodeArts）使用提示词清单 — QuorumPilot

> 用途：解决华为智能体创新赛（西北赛区）「码道深度使用 **25 分**」卡点。
> 官方评分细则逐字：「码道在开发全流程的覆盖度（**环境搭建、代码生成、调试排错、文档生成**等）」＋「Prompt 设计质量与工具使用效率」＋「使用证明材料的完整性与真实性」。
> 本清单严格按这四项编排，并针对 QuorumPilot 的**真实符号**设计（`verify.py` 的 `verify_claim()` / `verify_claims()`、`arbitrate.py` 的 `arbitrate()`）。
> **每条执行一次 → 截图一次**，全部放入 `codearts_proof/`。

---

## 操作方式

1. 登录华为云码道：`https://developer.huaweicloud.com/codeartsco.html`，打开 QuorumPilot 工程。
2. **逐条复制下面「提示词」框内原文**粘贴发送。
3. 每条保存 3 张图：① 对话与 Prompt 原文 ② 码道回答/生成代码 ③ 本地执行结果终端。
4. 保留码道 IDE 插件的**操作日志与记录**（官方明确列为证明材料）。
5. 💡 中部赛区（PayPilot）的提示词可**在同一场码道会话中连做**，切换工程目录即可，两组截图分别归档。

---

## A. 环境搭建

### A1 — 一键安装与环境自检

**提示词：**
```
这是我的项目 QuorumPilot（多智能体交易评审团，纯 Python 标准库、零第三方依赖）。
结构（真实模块名）：quorumpilot/ 下有 agents.py（4 位专家智能体）、brain.py（LLM/
离线双引擎）、verify.py（确定性验证器）、arbitrate.py（纯算术仲裁器）、market.py、
ingest.py、receipts.py、cli.py、mcp_server.py、agent.py；
根目录有 eval.py、app.py、web.py、test_web.py。

请生成两个文件：
1) scripts/setup.sh —— 一键环境搭建：检测 Python >= 3.9、创建虚拟环境、安装
   requirements.txt、打印自检结果。
2) scripts/doctor.py —— 环境自检：Python 版本、必需模块可导入性、eval.py 可执行性，
   每项以 PASS/FAIL 打印并以退出码反映结果。

约束：只使用 Python 标准库；Windows 与 Linux 均可运行（Windows 用 python 命令）。
输出完整文件内容。
```

**截图**：对话 + 脚本 + 跑 `python scripts/doctor.py` 的终端输出。

---

## B. 代码生成

### B1 — 为验证器新增一类可校验论断

**提示词：**
```
阅读 quorumpilot/verify.py，重点是 verify_claim(claim, ...) 与
verify_claims(claims, ...)（逐条核对智能体论断是否可被引证）。

请新增一类可校验论断「时序类论断（temporal claim）」：
- 需求：支持论断引用时间窗口事实（例如「过去 30 天内该商户交易次数 > 5」），
  verify_claim 需要能校验 claim 中引用的时间字段是否落在事实快照的有效窗口内。
- 若 claim 引用的时间字段超出快照窗口，判定为不可证明（unprovable），与其他
  不可证明论断一样在进入仲裁前被丢弃。
- 必须保持现有 verify_claims 的批处理语义与返回结构不变。

约束：纯标准库；**不得让验证逻辑依赖任何 LLM 输出**；给出完整改动代码，以及追加
到 eval.py 的新断言（要求 `python eval.py` 仍全绿并说明断言数变化）。
```

**截图**：对话 + 生成代码 + `python eval.py` 新结果。

### B2 — 增加第五位专家智能体

**提示词：**
```
阅读 quorumpilot/agents.py（4 位专家智能体的定义）与 quorumpilot/arbitrate.py 的
arbitrate(snap, m, ...) 函数。

需求：增加第五位专家智能体「合规视角（compliance）」，它提出的论断同样必须引用
事实字段并经过 verify_claims 校验，不可证明者被丢弃；仲裁器在汇总时需把这位专家
的幸存论断计入，且仍保持 PROCEED / PROCEED_WITH_CAUTION / REJECT 三种裁决语义不变。

约束：纯标准库；**仲裁器必须保持纯算术、不使用任何模型**；给出完整改动代码与新增
断言；说明这对现有 137 条断言的影响。
```

**截图**：对话 + 生成代码 + 终端结果。

---

## C. 调试排错

### C1 — 定位并修复一个真实缺陷

**提示词：**
```
问题：在 quorumpilot/verify.py 的 verify_claims 批处理中，当同一位专家提出两条
指向同一事实字段但结论相反的论断时，目前的丢弃行为不稳定——有时两条都被丢弃，
有时都被保留。

请：
1) 定位导致该不稳定行为的具体代码位置（给出行号与原因）；
2) 给出明确的冲突消解语义（建议：同一专家对同一字段的相反论断应**同时丢弃**，
   因为无法判定哪一条为真），并说明为何这比"保留其一"更符合本项目"不可证明即
   丢弃"的设计哲学；
3) 给出修复后的完整代码片段；
4) 给出一条回归断言锁死该行为。
```

**截图**：对话 + 定位与修复代码 + 修复后终端输出。

### C2 — 解释与优化

**提示词：**
```
这是 quorumpilot/arbitrate.py 的全文（粘贴）。请：① 逐步解释 arbitrate() 如何把
幸存论断汇总为 PROCEED / PROCEED_WITH_CAUTION / REJECT 三种裁决；② 说明它为何是
"纯算术、不使用模型"的，以及这带来什么保证；③ 给出异常处理、日志、可读性方面的
具体优化建议。
```

**截图**：对话 + 解释与建议。

---

## D. 文档生成

### D1 — 架构与 API 文档

**提示词：**
```
阅读 quorumpilot/ 全部模块、app.py、web.py、docs/ 目录。
请生成：① 一份中文架构说明（模块依赖图 + 数据流 + "智能体提议 / 验证器定证据 /
仲裁器定决策"权力分离设计）；② 一份 API 与 MCP 服务器使用文档（端点、请求响应
示例、错误码）。输出 Markdown，可直接放进 readme/ 目录。
```

**截图**：对话 + 生成的 Markdown。

### D2 — 部署运行说明

**提示词：**
```
阅读 app.py、web.py、DEPLOY.md。
请生成部署运行说明文档：环境依赖清单、一键安装脚本、本地启动步骤（含 Web 界面与
MCP 服务器）、健康检查端点、常见问题排查。输出 Markdown，要求按文档可完整复现运行。
```

**截图**：对话 + 生成的文档。

---

## 交付自检（打包前确认）

- [ ] A 组 ≥1 条（含脚本与执行输出截图）
- [ ] B 组 ≥2 条（含生成代码与 `python eval.py` 结果截图）
- [ ] C 组 ≥1 条（含定位过程与修复后结果截图）
- [ ] D 组 ≥2 条（含生成的 Markdown）
- [ ] 码道 IDE 插件**操作日志/记录**已导出
- [ ] 图片命名可读（如 `codearts_proof/B1_verify_temporal_01.png`）
- [ ] 所有截图为**真实操作记录**，不做任何合成或伪造
