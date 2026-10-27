# Deriv · Rise of AI Agents — 提交包（QuorumPilot · Collaborative Systems 轨）

> **赛事**：Deriv「The Rise of AI Agents Hackathon」，lablab.ai 平台，Dubai AI Week 期间，线下决赛在 Deriv 迪拜办公室（仅邀请）。
> **截止**：作品提交 **2026-11-02（End of Day）**（Internshala/Luma 赛事页口径；lablab 官方页自身仍标 TBA——以平台邮件为准，按 11-02 倒排最稳）。
> **资格**（官方页逐字）："Everyone is welcome to participate, regardless of previous AI or coding experience!" / "Join solo or with a team." / **未列任何禁赛国家**。规则唯二硬性：**original + MIT**（均满足）。
> **奖金真相**（官方页逐字，防注水）：Gemini 轨 = **GCP 额度非现金**（$25k/$15k/$10k）；Vultr 轨 = **现金+额度**（$5k+$1k / $3k+$1k / $1k+$1k）。总池 $60k+。派奖最长 90 天。Vultr 现金提现有国别渠道风险，主价值按 GCP 额度计。

## 一、平台表单字段（复制即填）

| 字段 | 内容 |
|---|---|
| Project Title | **QuorumPilot** |
| Short Description | A multi-agent risk-review system for trading. Four specialist agents review a proposed trade — but a deterministic verifier decides which of their claims *count*, and a pure-arithmetic arbiter decides the verdict. No model touches the final number. |
| Long Description | 见下方「长描述」全文 |
| Track / Category | **Collaborative Systems**（多智能体协同） |
| Technology Tags | `multi-agent` `deterministic-verifier` `cited-evidence` `python-stdlib` `offline` `mcp` `finance-risk` |
| Public GitHub Repository | **`https://gitee.com/ZhiYIlang/quorumpilot-deriv`**（**本届主链·窗口内新建**：2026-10-26 00:35 京创建 → 公开匿名可见，**47 文件**（10-26 09:0x 增补 README 实测行 + 两支演示视频），MIT · README 明示 **137 passed, 0 failed**（2026-10-26 干净克隆实测 exit 0））＋ 配套仓 **`https://gitee.com/ZhiYIlang/tradeguard-deriv`**（2026-10-26 00:36 京创建 → 公开匿名可见，12 文件，16/16 断言 exit 0）。两仓创建日期均落在 Deriv 窗口 **2026-10-26 ~ 11-02** 内，满足 lablab「项目须在窗口内构建」的创建日期证明。旧链 `gitee.com/ZhiYIlang/quorumpilot`（2026-10-14 建，窗口外）**保留不删**——MINMAX/Open Agent/苏客松仍登记该链接 |
| Demo Application Platform | Python stdlib HTTP server（`web.py`，零依赖） |
| Application URL | **https://clauseguard-ai.app.workbuddy.host/**（00:3x 上线实测：title="QuorumPilot - live quorum demo" / /healthz 200 "Pod alive" / /api/demo/reckless 200；原 MatchLens 内容已被覆盖——用户确认未注册 MatchLens，该线关闭） |
| Cover Image | `quorumpilot/DERIV_COVER.png`（39,343 B · 1920×1080 · 代码渲染自真实幻灯片，非 AI 生图） |
| Video Presentation | `quorumpilot/deriv_demo.mp4`（1,043,175 B ≈ 1018.8 KB · **76.0s**@30fps · 2281 帧 · RENDER_EXIT=0；21.5s 快剪版 `quorumpilot_demo.mp4` 288,152 B 同仓备用） |
| Slide Presentation | `quorumpilot/DERIV_SLIDES.html`（8 页，浏览器打印为 PDF） |

### 长描述（Long Description，可直接粘）

> Most trading "AI" stops at a confident sentence. QuorumPilot is a pre-trade
> risk-review committee: four specialist agents (analyst, skeptic, risk,
> compliance) each examine a proposed trade and state their case — but an
> agent's word is not evidence. A deterministic verifier re-resolves every
> citation against the computed fact bundle; anything unprovable loses its
> voting weight entirely. The verdict is then decided by a pure-arithmetic
> arbiter. No model touches the final number.
>
> The result is a system that cannot be talked out of its own arithmetic: an
> agent that fabricates three confident claims has all of them dropped, and
> the verdict is byte-identical to the honest run (covered by the offline
> assertion suite: 137 assertions, including a "lying agent" adversarial
> case). Every verdict ships with a receipt: the full arbitration transcript,
> each breach with its measured number, and the fit-the-rules position size
> when the proposal is too big.
>
> Built for the Collaborative Systems track: the specialists coordinate
> through a shared, verifiable fact bundle rather than chatroom consensus,
> and the whole quorum is exposed as a real MCP server (protocol 2025-11-25)
> so any MCP host can call the reviewer before a trade executes. Zero
> third-party dependencies — Python standard library only; the offline
> brain is the default, an LLM is optional and can never override the
> arithmetic.

## 二、资产实测清单（宣称=实测）

| 资产 | 路径 | 实测 |
|---|---|---|
| 封面图 | `DERIV_COVER.png` | 39,343 B · 1920×1080 · Edge headless 渲染 DERIV_SLIDES.html 第 1 页（真实 UI，禁 AI 生图合规） |
| 演示视频 | `deriv_demo.mp4` | 1,043,175 B（1018.8 KB）· 2281 帧 ≈ **76.0s**@30fps · `_videotool/ffmpeg.exe` 编码 · 2026-10-22 09:0x 帧级 spliced 修正（原版 eval 场景误显 "194 passed"，实测口径为 137；手术脚本 `_deriv_video_resplice/splice.py`，时长与原版逐帧一致） |
| 幻灯片 | `DERIV_SLIDES.html` | 8 页自包含 · 终端块为真实 demo 输出（REJECT score=-55 / 137 passed / MCP 2025-11-25）· `@media print` 可导出 PDF |
| 在线 demo | `web.py` | stdlib HTTP 服务 · `test_web.py` **15/15 PASS**（ reckless REJECT/-55/7  breaches/16 验 0 丢；clean PROCEED；marginal PROCEED_WITH_CAUTION；垃圾载荷不崩；400/404 契约）· 录屏 `docs/ui_demo_web.png` 106,644 B |
| 代码仓 | `gitee.com/ZhiYIlang/quorumpilot`（当前版，137 断言 eval 全绿；GitHub 镜像 10-17 旧版） | 公开 · MIT · 与本地逐字节一致（2026-10-23 匿名 clone 实测复现） |
| **Deriv 窗口内仓（2026-10-26 重建）** | `gitee.com/ZhiYIlang/quorumpilot-deriv`（主）＋ `gitee.com/ZhiYIlang/tradeguard-deriv`（配套） | 2026-10-26 00:35/00:36 京创建（窗口 10-26~11-02 内）· 匿名 API 复验 `private=False` · **47/12 文件**（10-26 09:0x 增补：README「137 passed, 0 failed」实测行 + `quorumpilot_demo.mp4` 21.5s + `deriv_demo.mp4` 76.0s，均 read-back sha256 逐字节一致）· 本地 eval 137/137、16/16 exit 0 · README 口径与本地一致（137/16） |
| Open Agent 版仓 | `gitee.com/ZhiYIlang/quorumpilot-openagent` | 2026-10-23 19:45 京创建（OA 窗口 10-22~27 内）· 公开 · 38 文件 · 窗内增量（Nemotron 后端 + explain 转写）· eval **194 passed, 0 failed** · GitHub 镜像 `Zhiyilang/quorumpilot-openagent`（shadow-ban，评委不可见） |

## 三、已完成的 AI 侧工作（本轮 10-21 夜）

1. 渲染 76.0s 演示视频成片（真实命令+真实输出捕获）。
2. 建 8 页幻灯片 `DERIV_SLIDES.html`（可打印 PDF）。
3. 渲染封面 `DERIV_COVER.png`（1920×1080，代码渲染真实界面）。
4. **新建零依赖在线 demo `web.py`**：三示例一键运行 + 可编辑 JSON + 实时裁决面板；满足平台 "Demo Application Platform + Application URL" 硬性要求。
5. 建 `test_web.py` 15 项契约断言，实跑 **15/15 PASS exit 0**。
6. 录 demo 界面截图 `docs/ui_demo_web.png`（Edge headless，真实运行态）。
7. 官方规则逐字取证（本文件头部）。

## 四、卡点（按依赖序）

1. **lablab 注册（用户，~5 分钟）**：https://lablab.ai/ai-hackathons/ai-agents-ai-week-hackathon → Sign up。注册后才有提交入口。
2. **Application URL（✅ 已解决 00:3x）**：用户确认未注册 MatchLens（官方注册 10-21 03:00 京截止已过）→ 发布槽 `clauseguard-ai.app.workbuddy.host` 已切换为 QuorumPilot demo（`web.py` 零依赖部署，verified: true）。实测：title="QuorumPilot - live quorum demo"、`/healthz` 200、`/api/demo/reckless` 200。MatchLens 两条 automation 已删。
3. **推送令牌（用户，~2 分钟）**：本轮新资产（`web.py`/`test_web.py`/`docs/ui_demo_web.png`/`DERIV_COVER.png`/`deriv_demo.mp4`/`DERIV_SLIDES.html`/本文件）尚未推送——需用户为 **`Zhiyilang`** 账号签发 repo 全权限 token（现持 074811 token 只能推 074811 账号，竞赛仓全在 Zhiyilang 名下）。
4. **quorumpilot-openagent 仓（10-23 07:59 后）**：Open Agent 注册完成后走 `_open_agent_rebuild.py --push` 建仓；幻灯片尾页已注明该依赖与 public mirror `quorumpilot` 的关系。
5. **视频上传**：若平台要求视频外链（YouTube Unlisted 等），76.0s 成片可直接传。

## 五、提交前检查单

- [ ] lablab 注册完成（用户）
- [x] Application URL 已定并 curl 核验（title="QuorumPilot - live quorum demo" / healthz 200 / demo 路由 200，00:3x 实测）
- [ ] 新资产已推送至 `Zhiyilang/quorumpilot`（token 到位后一条命令）
- [ ] 表单三件套（cover/video/slides）上传完毕
- [ ] 长描述粘贴核对 track=Collaborative Systems
- [ ] 提交后截图回传，登记管线

---
> 官方规则源：https://lablab.ai/ai-hackathons/ai-agents-ai-week-hackathon （2026-10-21 23:xx 实测抓取）· 提交指南 https://lablab.ai/delivering-your-hackathon-solution · 条款 https://lablab.ai/terms-of-use#16-participation-terms
