"""
YouTube 路径端到端测试（待测试项）：mock captionTracks + 路由拦截 timedtext，
不需要真实访问 YouTube。覆盖：
  1. captionTracks -> baseUrl(fmt=json3) -> 解析上报（人工 + asr 两条轨）
  2. aAppend 碎片事件被过滤（回归）
  3. baseUrl 返回空 body 时自动打开 CC、走嗅探路径，且不上报假轨道
  4. 广告出现且官方 skip 按钮可用时自动点击；非广告状态不误点
运行：python3 tests/test_youtube.py   （无需本地 http server）
"""
import copy
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
USERJS = str(ROOT / "dist" / "universal-subtitle-extractor.user.js")
PAGE_CORE = str(ROOT.parent / "scripts" / "page_inject" / "export_core.js")
JSON3 = json.loads((ROOT / "tests" / "site" / "youtube-json3.json").read_text(encoding="utf-8"))
JSON3_ASR = copy.deepcopy(JSON3)
JSON3_ASR["events"][0]["segs"] = [{"utf8": "Auto hello"}, {"utf8": "world"}]

TIMEDTEXT = "https://www.youtube.com/api/timedtext"
CAPTION_TRACKS = [
    {"baseUrl": TIMEDTEXT + "?v=test1234567&lang=en",
     "name": {"simpleText": "English"}, "languageCode": "en"},
    {"baseUrl": TIMEDTEXT + "?v=test1234567&lang=en&kind=asr",
     "name": {"simpleText": "English (auto-generated)"}, "languageCode": "en", "kind": "asr"},
]

PAGE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Mock - YouTube</title></head>
<body>
<div id="movie_player"></div>
<button class="ytp-subtitles-button" aria-pressed="false"
        onclick="window.__ccClicked=(window.__ccClicked||0)+1">CC</button>
<script>
window.ytInitialPlayerResponse = %s;
</script>
</body></html>""" % json.dumps({
    "videoDetails": {"title": "Mock Video", "lengthSeconds": "42"},
    "captions": {"playerCaptionsTracklistRenderer": {"captionTracks": CAPTION_TRACKS}},
})


def make_ctx(p, timedtext_body):
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    ctx = browser.new_context()
    ctx.add_init_script(path=USERJS)

    def handler(route):
        url = route.request.url
        if "timedtext" in url:
            body = timedtext_body(url)
            route.fulfill(status=200, content_type="application/json", body=body)
        else:
            route.fulfill(status=200, content_type="text/html", body=PAGE_HTML)

    ctx.route("https://www.youtube.com/**", handler)
    return browser, ctx


def test_full_chain(p):
    def body(url):
        return json.dumps(JSON3_ASR if "kind=asr" in url else JSON3)

    browser, ctx = make_ctx(p, body)
    page = ctx.new_page()
    page.goto("https://www.youtube.com/watch?v=test1234567", wait_until="load")
    page.evaluate("window.__USE__.waitFor(2, 15000)")
    tracks = page.evaluate("window.__USE__.list()")
    yt = [t for t in tracks if t["site"] == "youtube" and t["source"] == "api"]
    assert len(yt) == 2, tracks
    assert sorted(t["isAI"] for t in yt) == [False, True], yt
    for t in yt:
        cues = page.evaluate("window.__USE__.get(%s).cues" % json.dumps(t["id"]))
        assert len(cues) == 3, cues  # aAppend 事件已过滤，否则是 4 条
        assert cues[0]["start"] == 0 and cues[0]["end"] == 1.5, cues[0]
    text = page.evaluate("window.__USE__.text()")
    assert "Hello world" in text, text
    meta = page.evaluate("window.__USE__.meta()")
    assert meta.get("site") == "youtube" and meta.get("title") == "Mock Video", meta
    assert page.evaluate("window.__ccClicked || 0") == 0  # 直取成功不应动 CC
    browser.close()
    print("YOUTUBE_FULL_CHAIN_OK", json.dumps(yt, ensure_ascii=False))


def test_empty_body_fallback(p):
    browser, ctx = make_ctx(p, lambda url: "")
    page = ctx.new_page()
    page.goto("https://www.youtube.com/watch?v=test1234567", wait_until="load")
    page.wait_for_function("() => (window.__ccClicked || 0) >= 1", timeout=15000)
    tracks = page.evaluate("window.__USE__.list()")
    assert not [t for t in tracks if t["source"] == "api"], tracks  # 空 body 不能上报假轨道
    browser.close()
    print("YOUTUBE_EMPTY_FALLBACK_OK (auto CC clicked)")


def test_skip_ad_button(p):
    browser, ctx = make_ctx(p, lambda url: json.dumps(JSON3))
    page = ctx.new_page()
    page.goto("https://www.youtube.com/watch?v=test1234567", wait_until="load")
    auth = page.evaluate(
        "window.__USE__.authorizeTarget(location.href, {acknowledgeLawfulUse:true})"
    )
    assert auth["ok"], auth

    # 相同按钮在非广告状态下不能被误点。
    page.evaluate("""() => {
      const player = document.querySelector('#movie_player');
      player.innerHTML = '<button class="ytp-skip-ad-button" aria-label="Skip ad" style="width:100px;height:30px" onclick="window.__adSkipped=(window.__adSkipped||0)+1">Skip ad</button>';
    }""")
    page.wait_for_timeout(1100)
    assert page.evaluate("window.__adSkipped || 0") == 0

    # 广告状态出现后，官方按钮应被自动点击一次。
    page.evaluate("document.querySelector('#movie_player').classList.add('ad-showing')")
    page.wait_for_function("() => (window.__adSkipped || 0) === 1", timeout=5000)

    # SPA 切换到别的视频后，原授权必须失效。
    page.evaluate("""() => {
      window.__adSkipped = 0;
      history.pushState({}, '', '/watch?v=other123456');
      document.querySelector('.ytp-skip-ad-button').setAttribute('aria-label', 'Skip ad');
    }""")
    page.wait_for_timeout(1100)
    assert page.evaluate("window.__adSkipped || 0") == 0
    browser.close()
    print("YOUTUBE_AD_SKIP_OK")


def test_page_core_acknowledged_download(p):
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    ctx = browser.new_context(accept_downloads=True)
    ctx.add_init_script(path=PAGE_CORE)

    def handler(route):
        if "timedtext" in route.request.url:
            route.fulfill(status=200, content_type="application/json", body=json.dumps(JSON3))
        else:
            route.fulfill(status=200, content_type="text/html", body=PAGE_HTML)

    ctx.route("https://www.youtube.com/**", handler)
    page = ctx.new_page()
    page.goto("https://www.youtube.com/watch?v=test1234567", wait_until="load")

    denied = page.evaluate("window.__ovsDownloadSubtitle({format: 'txt', targetUrl: location.href})")
    assert not denied["ok"] and denied["requires_acknowledgement"], denied
    mismatch = page.evaluate(
        "window.__ovsDownloadSubtitle({format:'txt', targetUrl:'https://www.youtube.com/watch?v=other123456', acknowledgeLawfulUse:true})"
    )
    assert not mismatch["ok"] and "does not match" in mismatch["error"], mismatch

    with page.expect_download(timeout=15000) as download_info:
        meta = page.evaluate(
            "window.__ovsDownloadSubtitle({format: 'txt', targetUrl: location.href, acknowledgeLawfulUse: true})"
        )
    text = Path(download_info.value.path()).read_text(encoding="utf-8")
    assert meta["ok"] and meta["cue_count"] == 3, meta
    assert "Hello world" in text, text
    assert meta["plain_text"] == text, meta
    assert meta["source_text"] == text, meta
    assert len(meta["cues"]) == 3, meta
    assert meta["source_coverage"]["complete"], meta
    assert meta["requires_editorial_pass"], meta
    browser.close()
    print("YOUTUBE_ACK_DOWNLOAD_OK", json.dumps(meta, ensure_ascii=False))


with sync_playwright() as p:
    test_full_chain(p)
    test_empty_body_fallback(p)
    test_skip_ad_button(p)
    test_page_core_acknowledged_download(p)
    print("YOUTUBE_ALL_OK")
