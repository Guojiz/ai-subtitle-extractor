# 油猴 Userscript

由**通用页内核**生成，不是另一套逻辑：

```bash
python scripts/build_userscript.py
# → ai-subtitle-extractor.user.js
```

核文件：[`../scripts/page_inject/export_core.js`](../scripts/page_inject/export_core.js)

## 安装

1. Tampermonkey / Violentmonkey  
2. 导入 `ai-subtitle-extractor.user.js`（`@match *://*/*`，通用）  
3. 打开任意视频页 → 右下角导出 / 复制 / JSON  

每个目标视频首次导出时会显示当前操作位置和精确 URL，并要求确认自己有合法访问权、仅在法律允许的个人学习、研究或授权范围内使用。确认只对当前会话中的这个视频生效；换视频或换操作位置需要重新确认。确认不是法律意见，也不会绕过平台、付费或模型规则。

在 YouTube 上，脚本会在播放器实际出现官方“跳过广告”按钮时自动点击；不可跳过广告不会被快进或隐藏。

## Agent 更推荐 agent-browser

油猴适合人机常驻；Agent 批量注入请用：

```bash
npm install -g agent-browser && agent-browser install
python scripts/extract_subtitles.py "<url>" --agent-browser \
  --acknowledge-lawful-use -o transcript.md
```

见 [`../scripts/page_inject/README.md`](../scripts/page_inject/README.md)。

## API

```js
await window.__ovsExportSubtitle({ lang: 'zh' })
// adapter 可选: youtube | bilibili | general（默认 auto）
```

## 许可

MIT。与商业翻译扩展无关。  
