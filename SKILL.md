---
name: ai-subtitle-extractor
description: 面向任意 AI Agent 的平台无关在线视频字幕获取与文章化交付流程。用户给出视频链接并要求提取、转文字、整理、翻译、总结或问答时优先使用。完整保留实质信息，删除无意义口语噪声，重组为通顺文章，必要时完整翻译为用户语言，再执行后续操作；人工轨优先、自动轨后补。
---

# 在线视频字幕获取流程（通用 Agent Recipe）

本文件是**平台无关**的 Agent Recipe：  
**中心是通用管线**；Bilibili、YouTube 等只是管线下的**站点适配（adapter）**。

适用于任何具备以下能力之一的系统：

- 能访问网页 / 操作浏览器（含 Kimi WebBridge）
- 能发送 HTTP 请求 / **执行 shell 或小脚本**
- 能读取 JSON / 页面文本并整理成自然段

**单点可跑。** GitLearnOS 等只是可选调用方。

页内导出核（通用）：`scripts/page_inject/export_core.js`  
→ `window.__ovsExportSubtitle({ lang })`，适配 youtube / bilibili / **general**

注入通道（同一 core）：

1. **agent-browser**（推荐给 Agent）：`open --init-script` + `eval`  
2. 油猴（用户浏览器常驻）  
3. WebBridge / 其它 `evaluate`  

```bash
# 安装 agent-browser（一次）
npm install -g agent-browser
agent-browser install

# 通用：注入取字幕（不限单站）
python scripts/extract_subtitles.py "<url>" --agent-browser \
  --acknowledge-lawful-use -o out.md

# B 站 HTTP 亦可
python scripts/extract_subtitles.py BV... --lang zh \
  --acknowledge-lawful-use -o out.md
```

独立 Recipe：不绑定商业扩展源码；实现原创。

## 触发条件

用户给出**任意在线视频链接**（不限站点），并要求提取字幕、转文字、整理文稿、翻译或总结时，使用本流程。

## 全文交付前的合法使用确认

当用户要求第三方视频的**完整文章、文稿或字幕文件**时，在导航、播放、注入或提取开始前，一次性确认以下三项：

1. **合法使用声明**：

> 我确认我有权访问该视频和字幕，并仅在法律允许的个人学习、研究或经授权范围内使用；我不会用本工具侵犯版权或规避付费、登录及其他访问控制。

2. **精确目标**：视频 URL（必要时加标题、分 P / 集数）。不要把“当前页面”当作足够明确的目标。
3. **操作位置**：让用户明确选择其一：
   - 当前已登录的浏览器标签页（使用当前登录态，会控制播放器并在按钮出现时跳过广告）；
   - 新的隔离自动化浏览器（通常无登录态，不影响现有标签页）；
   - 本机 CLI / HTTP（不操作播放器，因此不能点击广告）。

建议把问题合成一条，要求用户回复“我确认 + 操作位置 + 视频 URL”。若用户已给出其中某项，只补问缺失项。

用户已对**同一目标视频和同一操作位置**明确表达等价确认时不重复询问。换视频、换分集或换操作位置时重新确认。确认只说明用户目的和权限主张，**不是法律意见，也不会改变平台或模型的上层规则**；不要声称免责声明可以绕过版权政策。

## 默认交付契约：文章完整，不是口语逐字稿

“完整交付”指**完整保留实质信息**，不是把每个语气词和失败起句都塞进文章。平台字幕是来源证据；最终产物是符合阅读直觉的文章。

确认后按以下顺序继续：

1. 拉取全部 cues 作为可审计来源，先验证来源字幕读取完整；这一步可以保留口语噪声，但它不是最终交付稿。
2. 识别实质内容：观点、事实、论据、例子、数字、专有名词、因果关系、限定条件、反例、结论和有修辞意义的重复。
3. 删除编辑噪声：嗯、啊、呃等填充词；没有语义作用的口头重复；重复起句；被说话者立即推翻的失败表达；字幕断裂造成的重复片段。不得把不理解的内容擅自判为废话。
4. 重组为文章：恢复标点和句法，合并同义碎片，按主题组织段落；可以把相邻的同一观点合并成一次，但不能压缩掉其中新增的事实、例子或限定条件。
5. 做实质内容覆盖检查：逐项确认来源中的主张、证据、例子、数字、条件和结论都在文章中；同时记录删除的内容类别，确保删除项只有编辑噪声。
6. 若文章语言不是用户语言，将**完整文章**翻译成用户语言。翻译可以分块，但不能总结、缩写或漏掉实质内容。
7. 先交付完整的用户语言文章，再执行用户要求的摘要、问答、提纲、学习笔记等后续操作。

交付方式：

- CLI / 页内核返回的 `source_text/plain_text`、`cues`、`source_coverage` 是编辑素材，不是最终文章；`requires_editorial_pass=true` 时不得原样交付为成品。
- WebBridge / 页内核先导航到用户确认的精确 URL，再取得完整来源字幕；完成文章化编辑和翻译后才向用户交付。
- 对话/IM 默认发送完整文章；超出单条消息限制时按文章顺序连续分批发送并附完整文件，不能用摘要代替正文。
- 成品附简短编辑说明，例如“删除口头填充词和无意义重复，实质观点/例子/数字均保留”；除非用户要求，不必展示原始口语噪声。
- 若用户语言可从当前对话明确判断，直接使用；只有确实不明确时才补问目标语言。
- 若平台、账户、地区、付费墙或模型规则仍禁止某一步，如实说明该具体边界；不得把用户确认当作规避访问控制的许可。
- 自动跳广告授权只绑定确认的 YouTube video id；检测到 SPA 切换到另一个视频时不得继续点击。

若用户只要求摘要、问答或索引，仍须先完整读取来源、完成文章化理解并在需要时翻译，再生成后续结果；是否同时展示完整文章以用户明确要求为准。

## 总原则（全站共用）

1. **通用管线优先**；站点只解决「数据从哪来、字段怎么映射」。  
2. **确定用户语言**：优先按当前对话语言推断；确实不明确时才询问。最终完整文章先翻译为用户语言，再做后续操作。
3. 优先平台**已有**字幕数据；不要优先下载视频或 ASR。  
4. 同一语言下：**人工 / 创作者轨优先**，自动 / AI 轨后补。  
5. 已有合格目标语言轨时，不要为了翻译再绕远路。  
6. 需要翻译时：读取最稳的轨（通常原语言人工轨），**由 Agent / 下游全量翻译为用户语言**；不依赖平台侧「自动翻译轨」（易限流、质量不稳）。
7. 要读取**整份时间轴来源**，不要只抄当前叠加层一行；最终文章须覆盖全部实质内容，但应删除无语义口语噪声。
8. **能脚本化就由 Agent 执行**；UI 仅作触发或兜底。
9. Agent 环境访问失败 ≠ 无字幕；先尝试本地浏览器回退。
10. 未验证站点**不宣称完整支持**；走通用发现并诚实失败。
11. 输出必须带：平台、源语言、用户语言、字幕来源、获取方式、来源 cue 读取覆盖率、编辑说明。
12. YouTube 广告出现时，只点击播放器实际显示且启用的“跳过广告”按钮；不快进、不隐藏广告层，也不绕过不可跳过广告。

---

# 通用管线（先读这里）

```text
链接
  → 1. 解析 / 展开短链
  → 2. 确定用户语言（优先按对话语言判断）
  → 3. 选择适配：已知站用适配，否则「通用网页发现」
  → 4. 发现字幕通道（见下）
  → 5. 选轨（人工 → 自动）
  → 6. 拉取完整 cues，映射为统一 Cue
  → 7. 验证来源 cue 读取完整
  → 8. 删除口语噪声，重组为实质内容完整的文章
  → 9. 做主张/证据/例子/数字/条件/结论覆盖检查
  → 10. 完整翻译为用户语言（需要时）
  → 11. 先交付完整文章，再做后续操作
  → 访问失败则 WebBridge 等本地浏览器回退，再从 4 起
  → 仍无结果则如实说明
```

## 统一数据形态

站点字段不同，整理前先归一：

```text
Cue   { start: 秒, end?: 秒, text: string }
Track { language, kind: human|auto|unknown, source }
Result {
  title?, platform, language, track, cues | plainText,
  chapters?, limits?
}
```

## 通用发现通道（未知站默认用这个）

按代价从低到高，**每一站都适用**：

| 优先级 | 通道 | Agent 动作 |
|--------|------|------------|
| 1 | 已知适配 | 有文档则走适配（Bilibili / YouTube…） |
| 2 | 直接 API / 字幕文件 URL | JSON、VTT、SRT、timedtext 类 |
| 3 | 播放器网络请求 | 监听播放器加载的字幕资源（参数通常更全） |
| 4 | HTML5 `<track>` | captions / subtitles 轨道 |
| 5 | 页面文稿 UI | Captions / Subtitles / Transcript / 文字稿 / 转写 |
| 6 | 简介与章节 | 时间轴、讲稿、大纲 |
| 7 | 访问回退 | 本地已登录浏览器再跑 2–6 |
| 8 | 失败 | 说明已尝试路径；勿默认 ASR |

选轨规则（全站同一套）：

1. 目标语言 + human  
2. 目标语言 + auto  
3. 原语言（仅当用户要翻译）  

## 路由（适配表，可扩展）

| 链接特征 | 适配 |
|----------|------|
| （默认） | **通用网页发现** |
| `youtube.com`、`youtu.be`、`shorts` | [YouTube 适配](#adapter-youtube)（已验证样板） |
| `bilibili.com`、`b23.tv`、BV | [Bilibili 适配](#adapter-bilibili)（已验证样板） |
| 其他 | 通用网页发现；成功后可沉淀为新适配 |

增加新站时：只写「如何发现 + 如何映射到 Cue」，不要改通用原则。

## 通用整理与输出

1. 来源层只跳过空文本；按 `start` 排序并验证来源 cue 已完整读取
2. 编辑层删除填充词、失败起句、无意义重复和字幕断裂噪声
3. 保留全部实质观点、事实、例子、数字、条件、反例和结论
4. 恢复标点、句法和段落结构，整理成自然文章，而不是一行一个字幕碎片
5. 自动轨可校正明显错字；不确定的词保留原样或标注，不得臆改
6. 需要时完整翻译为用户语言，翻译后再执行摘要/问答
7. 有章节则按章节组织，并附简短编辑说明

```markdown
# 视频标题

## 视频信息

- 平台：...
- 目标语言：...
- 来源 Cue 读取覆盖率：... / ...
- 编辑说明：删除了哪些口语噪声；实质内容覆盖情况
- 字幕来源：人工 / 自动 / 未知
- 获取方式：api | network | transcript-ui | webbridge | ...
- 适配：general | bilibili | youtube | ...

## 简介 / 章节（如有）

...

## 整理后的完整文章

...
```

---

# Adapter: 通用网页 {#adapter-general}

**默认适配。** 任何未单列的站点走这里。

在页面 UI、源码与可访问资源中依次寻找：

1. Captions / Subtitles / Transcript  
2. 文字稿 / 字幕 / 转写  
3. HTML5 `<track kind="captions|subtitles">`  
4. 可打开的 SRT / VTT / 类似字幕 URL  
5. 播放器网络中的字幕请求  
6. 简介中的章节与讲稿  

访问失败 → [访问回退](#access-fallback)。  
不要声称「支持所有视频站」；仅报告本页实际找到的通道。

---

# Adapter: Bilibili {#adapter-bilibili}

**样板适配**（已验证较完整）：用公开 HTTP 接口完成通用管线的「发现 + 拉取」。  
历史最完整，但**不等于项目只服务 B 站**。

## 重要：这就是「从播放页拉完整文稿」

B 站播放器上的字幕**不是**只能截当前一闪而过的那一行。播放器背后用的就是同一套字幕 JSON：

1. 用 BV → 拿到 `cid`
2. `dm/view` 列出字幕轨（人工 / AI）
3. 请求 `subtitle_url` 得到整份 `body[]`（含 `from` / `to` / `content`）

设计原则（与具体产品无关，属于平台本身暴露数据的用法）：

- 字幕层 UI 只是展示；**完整文稿在平台下发的字幕 JSON 里**
- 优先读结构化数据（时间戳 + 文本数组），不要截当前叠加层那一行
- Agent 可以直接执行 HTTP / 小脚本拿到同一份数据

B 站侧：Agent 用 HTTP 调 `view` + `dm/view` + `subtitle_url`，解析 `body[]` 的 `from` / `to` / `content`。  
已用公开示例 `BV1SA7B6iEJg` 验证：可拉到数百条 cue 并合并成可读正文。

不必先打开浏览器。页内请求有时受登录/风控影响时，**Agent 进程里跑 curl / Python 往往更可靠**。

## B1. 解析 BV 号

从用户给出的链接中提取 `BV` 号。如果是短链接 `b23.tv`，先通过浏览器或 HTTP 重定向解析到正式 B站视频链接。

示例：

```text
https://www.bilibili.com/video/BV1SA7B6iEJg
```

得到：

```text
BV1SA7B6iEJg
```

## B2. 获取视频信息

调用 B站视频信息接口：

```bash
BV_ID="BV1SA7B6iEJg"

curl -s "https://api.bilibili.com/x/web-interface/view?bvid=${BV_ID}" \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
```

从返回 JSON 中读取：

- `data.aid`：视频 AV 号
- `data.cid`：当前分 P 的 CID
- `data.title`：视频标题
- `data.desc`：视频简介，常含时间轴章节
- `data.duration`：视频时长，单位为秒
- `data.pages`：分 P 信息，如果存在多个分 P，应根据用户需求选择对应页面

如果用户没有指定分 P，通常先处理第一个页面。

## B3. 获取字幕列表

B站字幕通常隐藏在弹幕视图接口中，不一定出现在普通播放器接口里。

优先调用：

```bash
CID="<从 B2 获取的 cid>"

curl -s "https://api.bilibili.com/x/v2/dm/view?oid=${CID}&type=1" \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  -H 'Referer: https://www.bilibili.com/'
```

在返回 JSON 中查找：

```text
data.subtitle.subtitles
```

## B4. 选择最合适的字幕轨道

不要默认只找 `ai-zh`。应先根据用户目标语言选择字幕轨道。

选择顺序：

1. 目标语言的人工字幕 / UP 主字幕。
2. 目标语言的 B站 AI 字幕，例如 `ai-zh`。
3. 如果没有目标语言字幕，但有原语言字幕，并且用户明确需要翻译，再读取原语言字幕后翻译。
4. 如果字幕列表为空，告诉用户当前视频未检测到可用 B站字幕。

判断线索：

- `lan`：语言代码，例如中文、英文或 `ai-zh` 这类 AI 字幕标识。
- `lan_doc`：语言说明或字幕标题。
- 字幕名称中是否包含 AI、自动生成、UP主、中文、英文等信息。
- 一般来说，非 AI 的目标语言字幕优先于 AI 字幕。

取出选中条目的：

```text
subtitle_url
```

注意：

- 有些 `subtitle_url` 可能以 `//` 开头，需要补成 `https://`。
- 也有完整的 `http://` / `https://` URL（例如 `aisubtitle.hdslb.com`）；能直接请求即可。
- 字幕 URL 可能短时间有效，应立即读取。
- 视频信息接口里的 `data.subtitle.list` 经常为空；**以弹幕视图接口 `dm/view` 的 `data.subtitle.subtitles` 为准**。

## B5. 下载字幕 JSON

```bash
SUBTITLE_URL="<subtitle_url>"

curl -s -o subtitle.json "${SUBTITLE_URL}" \
  -H 'Referer: https://www.bilibili.com/'
```

常见结构：

```json
{
  "body": [
    {
      "from": 0.32,
      "to": 1.74,
      "content": "字幕文本"
    }
  ]
}
```

## B6. 整理为可读文本

B站字幕，尤其是 AI 字幕，通常是 1 到 3 秒一句，不能直接原样输出。

整理规则：

1. 相邻字幕间隔大于 1.5 秒，可视为新句子或新语义块。
2. 很短的字幕片段应合并，避免一行一个碎片。
3. 每 200 到 300 个中文字符分一段。
4. 段末补充合适的句号、问号或感叹号。
5. 删除“嗯、啊、呃”等填充词、失败起句和无意义口头重复；有强调或论证作用的重复必须保留。
6. 对明显的 AI 字幕错字做轻微校正；人工字幕不要过度改写；不确定就保留原样或标注。
7. 如果 `data.desc` 中包含时间轴章节，可按章节组织文章。
8. 核对观点、事实、例子、数字、引用、专有名词、限定条件和结论均已保留。

## B7. 输出给用户

根据运行环境选择输出方式：

- 聊天 / IM 渠道：按文章顺序连续分段发送完整成稿，不要原样倾倒口语字幕，也不要只给摘要。
- Web / 桌面环境：保存完整文章 `.txt` / `.md`，同时直接展示成稿；摘要放在文章之后。
- 长视频：先输出标题、简介、章节，再连续输出全部文章；未发完前不要跳到摘要。

推荐输出结构：

```markdown
# 视频标题

## 视频信息

- 平台：Bilibili
- BV号：...
- 时长：...
- 目标语言：...
- 字幕来源：人工字幕 / UP 主字幕 / Bilibili AI 字幕

## 简介 / 章节

...

## 整理后的完整文章

...
```

## Bilibili 失败处理

如果无法获取字幕，应按顺序检查：

1. BV 号是否正确
2. 视频是否需要登录或地区权限
3. 是否有多个分 P，需要换 CID
4. `data.subtitle.subtitles` 是否为空
5. 是否存在目标语言字幕，或者是否需要换用另一条字幕轨道
6. `subtitle_url` 是否需要补全 `https://`
7. 请求头是否缺少 `User-Agent` 或 `Referer`
8. 字幕 URL 是否已经过期

如果视频确实没有字幕，应诚实告诉用户：当前视频未检测到可用 B站字幕。

可复制命令见：[`examples/curl-workflow.md`](./examples/curl-workflow.md)

---

# Adapter: YouTube {#adapter-youtube}

**样板适配**：用页面内轨列表 / timedtext / 转写面板完成通用管线。  
不保证所有 Agent 环境都能直连；失败时走 [访问回退](#access-fallback)，**不要**直接判定无字幕。

## 在通用管线中的落地顺序

```text
打开 watch 页（本环境或 WebBridge）
  → A. 捕获播放器真实的 timedtext 网络响应   ← 优先
  → B. 读页面内 caption 轨列表并 fetch 正文
  → C. 打开转写面板读 DOM                     ← 兜底
  → D. 仍失败 → 访问回退或如实说明
```

## Y1. 打开视频页面

在 Agent 当前环境打开链接（`watch`、`youtu.be`、`shorts`）。失败则转 **Kimi WebBridge 回退**，在用户本地浏览器打开同一 URL。

## Y2-A. 捕获播放器 timedtext（自动，优先）

YouTube 播放器加载字幕时会请求类似：

```text
https://www.youtube.com/api/timedtext?...
```

**为什么优先等这条真实请求：**  
播放器发出的 URL 通常已带齐鉴权/会话参数。Agent 自己拼轨列表里的 `baseUrl` 时，有时会得到 HTTP 200 但 body 为空——那是参数不完整，**不等于视频没字幕**。

**Agent 可执行流程（WebBridge 或任意可监听网络的环境）：**

1. 开始网络监听  
2. 打开视频页  
3. 若尚未产生 timedtext：用脚本打开 CC / 切换字幕（**目的是触发请求**，不是抄叠加层文字）  
4. 找到 URL 含 `timedtext` 且响应体非空的记录  
5. 解析 JSON 中的时间轴事件：开始时间 + 分段文本拼成完整句  
6. 完整保留来源事件供编辑；成稿中删除填充词、失败起句和无意义重复，保留全部实质信息

### 轨选择（人工优先）

页面内常有播放器初始数据，可列出字幕轨，例如：

```javascript
const tracks =
  window.ytInitialPlayerResponse
    ?.captions
    ?.playerCaptionsTracklistRenderer
    ?.captionTracks || [];
// 常见字段：languageCode, kind, name, baseUrl
// kind 表示自动识别轨时，优先级低于人工轨
```

选择顺序：

1. 目标语言、**非**自动识别轨  
2. 目标语言的自动识别轨  
3. 需要翻译时再读原语言轨，由 Agent/下游翻译  

尽量不要依赖播放器侧「自动翻译成目标语言」的旁路；原语言轨通常更稳，也更少触发限流。

判定是否有轨：`captionTracks` 非空即可认为「平台声明有字幕」；正文仍以 timedtext 响应为准。

## Y2-B. 页面内主动 fetch timedtext（次优）

若已从轨列表拿到 `baseUrl`：

```javascript
const data = await fetch(chosen.baseUrl, { credentials: 'include' }).then((r) => r.json());
// 正文字段以实际响应为准
```

若 HTTP 200 但 **body 为空**：不要判无字幕；回到 **Y2-A**，使用播放器自己发出的完整请求。

## Y2-C. 转写文稿面板（UI 兜底）

仅当 A/B 都拿不到正文：

- Show transcript / 转写文稿 / 内容转文字 等入口  
- 描述区可能需先展开  
- 读面板中的分段节点或纯文本  

## Y3. 整理为可读文本

1. 来源读取只过滤真正的空行；无时长但有文字的片段仍进入编辑素材
2. 按开始时间排序  
3. 合并过短片段  
4. 自动轨可轻校正；人工轨勿大改  
5. 删除无语义口语噪声，把字幕碎片重组为自然文章
6. 核对主张、证据、例子、数字、限定条件和结论均已覆盖
7. 需要时完整翻译为用户语言，再进行后续处理
8. 标明：`字幕来源`（人工 / 自动）、`获取方式`（`timedtext` / 转写面板 / WebBridge）和编辑说明

## Y4. 输出

```markdown
# 视频标题

## 视频信息

- 平台：YouTube
- 视频 ID / 链接：...
- 目标语言：...
- 字幕来源：人工字幕 / YouTube 自动字幕
- 获取方式：播放页 timedtext / 转写面板 / Kimi WebBridge

## 简介 / 章节（如有）

...

## 整理后的完整文章

...
```

## YouTube 注意

- 不保证所有环境都能直连 YouTube。  
- 不把「Agent 打不开页面」写成「视频没有字幕」。  
- 优先完整文稿数据，不要只抄当前 CC 叠加层那一行。  
- 不优先 `yt-dlp` 下载视频；仅在用户明确要求且已有字幕路径失败时再讨论。

简要示例见：[`examples/youtube-webbridge.md`](./examples/youtube-webbridge.md)

---

# 访问回退 / 页内注入 {#access-fallback}

**通用层**，不绑某一站点。字幕在播放器会话里时，用浏览器注入比纯 HTTP 稳。

```text
HTTP / 无会话令牌失败
  → 优先 agent-browser：
       open --init-script scripts/page_inject/export_core.js <url>
       eval → await __ovsExportSubtitle({ lang })
  → 或用户已装油猴的浏览器（同一 core）
  → 或 Kimi WebBridge evaluate 注入 core
  → 返回统一 Result
```

| 后端 | 角色 |
|------|------|
| agent-browser | Agent CLI 浏览器，**方便注入**（本仓库一等公民） |
| 油猴 | 用户侧常驻注入 |
| WebBridge | 用户已登录 Chrome 控制（可选） |

注意：

- Bilibili 等有稳 HTTP 的站可先 CLI，失败再注入  
- 失败 ≠ 无字幕；说明尝试过的通道  
- 不要下载整段视频；不要提交 cookies / profile 到 git  

---

# 不推荐的路径

- 不要优先 ASR（有平台字幕时）  
- 不要优先下载视频  
- 不要把某一 CLI 工具当成唯一方案  
- 不要把 GitLearnOS 等学习功能写进本仓库（调用关系见 [`examples/gitlearnos-caller.md`](./examples/gitlearnos-caller.md)）  
- 不要为了通用性去复制闭源扩展；新站用**适配说明**扩展  

---

# 全局失败处理

1. 链接是否解析正确  
2. 是否已走通用发现（而非只试了一个站）  
3. 目标语言与人工/自动轨是否都检查过  
4. 分 P / 分集是否换对资源  
5. 访问失败后是否做过本地浏览器回退  
6. 是否需要登录、地区或会员  
7. 字幕 URL 是否过期  

确认无字幕时说明：尝试过的**通用步骤与适配**、可知限制、是否可登录后重试。

---

# 浏览器内执行的额外坑（页面上下文 fetch 时）

在浏览器页面上下文（扩展 content script、油猴脚本、`page.evaluate`）中执行本流程时，curl 能跑通不代表浏览器能跑通，额外注意：

1. **Mixed Content**：B站 `dm/view` 返回的 `subtitle_url` 常是 `http://` 开头，HTTPS 页面内直接 fetch 会被浏览器拦截。必须先把 `http://` 升级为 `https://`（`aisubtitle.hdslb.com` 支持 HTTPS）。
2. **CORS + 凭证冲突**：B站字幕 CDN 返回 `Access-Control-Allow-Origin: *`。根据 CORS 规则，携带 Cookie（`credentials: 'include'`）的请求会被直接拒收，报错只是笼统的 `TypeError: Failed to fetch`。**下载字幕文件必须 `credentials: 'omit'`**；只有 `api.bilibili.com` 的接口才需要带 Cookie 获取登录态。
3. B站对新会话/自动化会话偶尔返回「出错啦」页并二次跳转，浏览器自动化脚本需容忍导航导致的执行上下文销毁（重试读取即可）。
4. YouTube `captionTracks.baseUrl` 直取常返回 HTTP 200 但 body 为空（参数不完整），**不等于视频没字幕**；应改由播放器自发 timedtext 请求（打开 CC 触发）并捕获网络响应。
