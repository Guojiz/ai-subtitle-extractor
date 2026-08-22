#!/usr/bin/env python3
"""
Standalone CLI: online video URL → existing captions/transcript.

Part of the platform-agnostic Agent Recipe.
- Works alone from the command line (no GitLearnOS required).
- GitLearnOS / other apps are optional callers only.
- Stdlib only. Original code for this repository.

Examples:
  python scripts/extract_subtitles.py "https://www.bilibili.com/video/BVxxxxxxxx"
  python scripts/extract_subtitles.py BV1SA7B6iEJg --lang zh -o out.md
  python scripts/extract_subtitles.py "https://www.youtube.com/watch?v=..." --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python scripts/extract_subtitles.py` without installing a package.
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.agent_browser import (  # noqa: E402
    agent_browser_available,
    extract_with_agent_browser,
)
from lib.bilibili import extract_bilibili  # noqa: E402
from lib.detect import detect_adapter  # noqa: E402
from lib.general import extract_general  # noqa: E402
from lib.models import ExtractResult  # noqa: E402
from lib.youtube import extract_youtube  # noqa: E402


LAWFUL_USE_ATTESTATION = (
    "我确认我有权访问该视频和字幕，并仅在法律允许的个人学习、研究或经授权范围内使用；"
    "我不会用本工具侵犯版权或规避付费、登录及其他访问控制。"
)


def extract(
    url: str,
    *,
    lang: str = "",
    adapter: str = "auto",
    browser: bool = False,
    agent_browser: bool = False,
    headed: bool = False,
    acknowledge_lawful_use: bool = False,
) -> ExtractResult:
    """
    Access backends (generic):
      1) agent-browser inject (preferred when requested / installed for page sites)
      2) HTTP adapters (bilibili full, youtube best-effort)
      3) WebBridge browser fallback (--browser)
    """
    # Force agent-browser path (any site: inject page core)
    if agent_browser:
        return extract_with_agent_browser(
            url,
            prefer_lang=lang,
            headed=headed,
            acknowledge_lawful_use=acknowledge_lawful_use,
        )

    ad = adapter if adapter and adapter != "auto" else detect_adapter(url)

    if ad == "bilibili":
        return extract_bilibili(url, prefer_lang=lang)

    if ad == "youtube":
        result = extract_youtube(url, prefer_lang=lang, use_browser=False)
        if result.ok:
            return result
        # Only escalate when user asked for a browser backend
        if not browser:
            result.limits = list(result.limits or []) + [
                "HTTP timedtext often empty without player session tokens",
                "Retry with: --agent-browser   (recommended)",
                "Or:          --browser         (agent-browser if installed, else WebBridge)",
            ]
            return result
        if agent_browser_available():
            ab = extract_with_agent_browser(
                url,
                prefer_lang=lang,
                headed=headed,
                acknowledge_lawful_use=acknowledge_lawful_use,
            )
            if ab.ok:
                return ab
            # fall through to WebBridge with both errors
            wb = extract_youtube(
                url,
                prefer_lang=lang,
                use_browser=True,
                acknowledge_lawful_use=acknowledge_lawful_use,
            )
            if not wb.ok:
                wb.limits = list(wb.limits or []) + [
                    f"agent-browser also failed: {ab.error}"
                ]
            return wb
        return extract_youtube(
            url,
            prefer_lang=lang,
            use_browser=True,
            acknowledge_lawful_use=acknowledge_lawful_use,
        )

    # Unknown site: HTTP has no adapter; browser only if requested
    if browser and agent_browser_available():
        return extract_with_agent_browser(
            url,
            prefer_lang=lang,
            headed=headed,
            acknowledge_lawful_use=acknowledge_lawful_use,
        )
    gen = extract_general(url, prefer_lang=lang)
    if browser:
        gen.limits = list(gen.limits or []) + [
            "Install agent-browser for page inject: npm i -g agent-browser && agent-browser install",
            "python scripts/extract_subtitles.py <url> --agent-browser",
        ]
    return gen


def _should_escalate_to_page(result: ExtractResult) -> bool:
    err = (result.error or "").lower()
    return (
        "empty" in err
        or "no usable cues" in err
        or "timedtext" in err
        or "blocked" in err
        or "failed to fetch" in err
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Extract existing subtitles/transcripts from an online video URL. "
            "Standalone tool; no external learning app required."
        )
    )
    p.add_argument("url", help="Video URL, BV id, or YouTube id/URL")
    p.add_argument(
        "--lang",
        default="",
        help="Preferred language code or hint (e.g. zh, en)",
    )
    p.add_argument(
        "--adapter",
        default="auto",
        choices=["auto", "bilibili", "youtube", "general"],
        help="Force adapter (default: auto-detect)",
    )
    p.add_argument(
        "-o",
        "--output",
        default="",
        help="Write markdown (or JSON if --json) to this path",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of markdown",
    )
    p.add_argument(
        "--cues-json",
        default="",
        help="Optional path to write raw cue list JSON",
    )
    p.add_argument(
        "--browser",
        action="store_true",
        help=(
            "Escalate to a real browser when HTTP fails. Prefers agent-browser inject "
            "if installed; else Kimi WebBridge."
        ),
    )
    p.add_argument(
        "--agent-browser",
        action="store_true",
        help=(
            "Force vercel-labs agent-browser: open URL, inject page_inject/export_core.js, "
            "call window.__ovsExportSubtitle. Best for generic page injection."
        ),
    )
    p.add_argument(
        "--headed",
        action="store_true",
        help="Show browser window when using agent-browser",
    )
    p.add_argument(
        "--acknowledge-lawful-use",
        action="store_true",
        help="Confirm lawful access/use before extracting a full transcript",
    )
    args = p.parse_args(argv)

    acknowledged = args.acknowledge_lawful_use
    if not acknowledged:
        if sys.stdin.isatty():
            if args.agent_browser:
                surface = "新的 agent-browser 浏览器页面"
            elif args.browser:
                surface = "浏览器回退（agent-browser 或已连接的 WebBridge）"
            else:
                surface = "本机 CLI/HTTP（无播放器 UI，不会点击广告）"
            print(LAWFUL_USE_ATTESTATION, file=sys.stderr)
            print(f"操作位置：{surface}", file=sys.stderr)
            print(f"目标视频：{args.url}", file=sys.stderr)
            answer = input("输入“我确认”后继续，其他输入将取消：").strip()
            if answer != "我确认":
                print("已取消：未确认合法使用。", file=sys.stderr)
                return 2
            acknowledged = True
        else:
            print(
                "Full transcript export requires lawful-use acknowledgement. "
                "Review the notice and rerun with --acknowledge-lawful-use.",
                file=sys.stderr,
            )
            return 2

    try:
        result = extract(
            args.url,
            lang=args.lang,
            adapter=args.adapter,
            browser=args.browser,
            agent_browser=args.agent_browser,
            headed=args.headed,
            acknowledge_lawful_use=acknowledged,
        )
    except Exception as e:
        result = ExtractResult(
            ok=False,
            platform="unknown",
            adapter=args.adapter,
            url=args.url,
            error=str(e),
        )

    if args.json:
        payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    else:
        payload = result.to_markdown()

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
        print(f"Wrote {out}", file=sys.stderr)
    else:
        sys.stdout.write(payload)
        if not payload.endswith("\n"):
            sys.stdout.write("\n")

    if args.cues_json and result.cues:
        Path(args.cues_json).write_text(
            json.dumps([c.to_dict() for c in result.cues], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
