# AI Subtitle Extractor

[English](./README.md)

<p align="center">
  <a href="https://guojiz.github.io/"><img alt="官网" src="https://img.shields.io/badge/官网-guojiz.github.io-111111?style=flat-square"></a>
  <a href="https://github.com/Guojiz/Sponsors"><img alt="赞助" src="https://img.shields.io/badge/赞助-支持-111111?style=flat-square"></a>
</p>

<p align="center">
  <a href="https://guojiz.github.io/"><strong>作者官网</strong></a>
  · <a href="https://x.com/guojizh">X</a>
  · <a href="https://space.bilibili.com/3493114115263006">哔哩哔哩</a>
  · <a href="https://youtube.com/@guojizh">YouTube</a>
  · <a href="https://github.com/Guojiz/Sponsors">赞助</a>
</p>


**把任意在线视频链接变成干净文稿——读平台已有的字幕。人工轨优先，自动轨后补。不下载视频，不跑 ASR。**

本仓库的核心是 [`SKILL.md`](./SKILL.md) 里的 Recipe：一套通用管线，YouTube 和 Bilibili 是已验证的样板适配。其他站点走通用发现，不声称完整支持。

```text
视频链接
  → 用户确认：合法使用 + 精确视频 + 操作位置
  → 识别站点（或通用发现）
  → 先问目标语言——要翻译就译成用户想要的语言
  → 发现字幕通道（API / timedtext / VTT·SRT / 转写面板 / <track>）
  → 人工轨优先 → 整份时间轴 cues → 可读正文
  → 返回：正文 + 平台 + 语言 + 字幕来源 + 获取方式
  → 访问失败：回退到用户本地浏览器
  → 确实无字幕：如实说明（之后才考虑 ASR）
```

## 验证状态

只声称实际跑通过的。

| 组件 | 状态 |
|---|---|
| YouTube 适配 | ✅ 真实 watch 页实测（经 WebBridge） |
| Bilibili 适配 | ✅ 真实视频实测（完整 SRT/文本导出） |
| 通用嗅探（fetch/XHR hook、`textTracks`、`<track>`） | ✅ 测试套件 + 真实 YouTube 页 |
| WebBridge `evaluate` 注入（主路径） | ✅ 已实测 |
| Playwright `add_init_script` 注入 | ✅ 已实测（全部测试套件） |
| MV3 扩展形态 | ✅ B站实测 |
| 油猴安装形态 | ⚠️ 未单独实测 |
| `scripts/` 的 agent-browser 后端 | ⚠️ 未实测 |
| 确认后直接下载全文（模型只收元数据） | ✅ Chromium mock 实测 |
| YouTube 目标级自动点击“跳过广告” | ✅ Chromium mock 实测；真实广告待验证 |
| 其他站点 | 仅通用发现，不声称支持 |

## 快速开始（已实测主路径）

通过 WebBridge 之类的桥驱动用户真实浏览器（带登录态），用户侧零安装：

```text
1. 先取得用户对“合法使用 + 精确视频 URL + 操作位置”的确认
2. node universal/build.js   → dist/universal-subtitle-extractor.user.js
3. navigate → 已确认的视频页
4. evaluate → 注入 .user.js 全文（重复注入有守卫）
5. evaluate → 把播放器控制绑定到该视频，再等待字幕：
```

```javascript
(async () => {
  const videoUrl = location.href; // 必须等于用户确认的精确 URL
  const auth = window.__USE__.authorizeTarget(videoUrl, {
    acknowledgeLawfulUse: true
  });
  if (!auth.ok) return auth;
  await window.__USE__.waitFor(1, 20000);
  return window.__USE__.download('txt', null, null, {
    targetUrl: videoUrl,
    acknowledgeLawfulUse: true
  });
})()
```

这条路径直接生成下载文件，返回给 Agent 的只有文件名、cue 数量等元数据。自动跳广告也只对该 video id 生效；YouTube SPA 切换到其他视频后不再点击。

## 仓库地图

| 路径 | 内容 |
|---|---|
| [`SKILL.md`](./SKILL.md) | **Recipe（核心资产）**：管线 → 适配 → 回退 → 输出契约 |
| [`universal/`](./universal/) | 可运行的通用提取器（`window.__USE__` API），含测试 |
| [`scripts/`](./scripts/) | 参考 CLI + 页内核（`__ovsExportSubtitle`） |
| [`examples/`](./examples/) | 适配示例：YouTube + 浏览器回退、Bilibili curl |

## 贡献

欢迎站点适配：遵守通用管线与 `Cue` 模型，用公开示例，如实标注「已验证 / 实验性」。见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 官网与其它推广

这个仓库可以没有独立产品站。对外入口是作者官网、本 GitHub 仓库，以及下面这些项目。

| | |
| --- | --- |
| **项目页** | https://guojiz.github.io/ai-subtitle-extractor/ |
| **作者官网** | https://guojiz.github.io/ |
| **X** | https://x.com/guojizh |
| **哔哩哔哩** | https://space.bilibili.com/3493114115263006 |
| **YouTube** | https://youtube.com/@guojizh |
| **赞助** | https://github.com/Guojiz/Sponsors |

### 其它开源项目

- [GitLearnOS](https://guojiz.github.io/gitlearnos/) — 学习者拥有的 Git 记忆
- [Word Snap](https://guojiz.github.io/word-snap/) — 双语单词匹配
- [AI Subtitle Extractor](https://github.com/Guojiz/ai-subtitle-extractor)
- [Design Master](https://github.com/Guojiz/design-master)
- [AI Video Studio](https://github.com/Guojiz/comfyui-minimax-h3-studio)
- [llm-provider-compat](https://github.com/Guojiz/llm-provider-compat)
- [Claude Desktop Tweak Models](https://github.com/Guojiz/claude-desktop-tweak-models)
- 全部项目：[github.com/Guojiz](https://github.com/Guojiz)

## 许可

MIT，见 [LICENSE](./LICENSE)。
