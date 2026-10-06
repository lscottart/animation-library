"""Extra stress for the sliding fill list, in Chromium, Firefox and WebKit. Run: python suites/list_extra.py"""
import json
from io import BytesIO
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
R = []
def check(n, ok, d=""):
    R.append(ok); print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)
lum = lambda png: float(np.asarray(Image.open(BytesIO(png)).convert("L"), dtype=float).mean())
SCALE = "(el) => { const t = getComputedStyle(el).transform; return t === 'none' ? 1 : +t.slice(7, -1).split(',')[3]; }"
with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)
        pg = b.new_page(viewport={"width": 1280, "height": 800})
        pg.goto("http://localhost:3020/tuned/list-coloured", wait_until="load"); pg.wait_for_timeout(800)
        rows = pg.locator("a.sfl-row")
        box = rows.nth(0).bounding_box(); clip = {"x": box["x"] + 4, "y": box["y"] + 4, "width": box["width"] - 8, "height": box["height"] - 8}
        before = lum(pg.screenshot(clip=clip)); rows.nth(0).hover(); pg.wait_for_timeout(800); after = lum(pg.screenshot(clip=clip))
        rows.nth(1).hover(); pg.wait_for_timeout(150)
        f0 = pg.locator("a.sfl-row .sfl-fill").nth(0); f1 = pg.locator("a.sfl-row .sfl-fill").nth(1)
        s0, s1 = f0.evaluate(SCALE), f1.evaluate(SCALE)
        check(f"[{engine}] hover fills solid, and moving down slides one bar", abs(after - before) > 60 and 0 < s0 < 1 and 0 < s1 < 1, f"luminance {before:.0f}->{after:.0f}, mid-slide scales {s0:.2f}/{s1:.2f}")
        pg.mouse.move(5, 5); pg.wait_for_timeout(700)
        pg.set_viewport_size({"width": 700, "height": 800}); pg.wait_for_timeout(400)
        lab = pg.evaluate("(() => { const r = document.querySelectorAll('a.sfl-row')[2]; const l = r.querySelector('.sfl-label'), i = r.querySelector('.sfl-icon'); const rr = r.getBoundingClientRect(), ir = i.getBoundingClientRect(); return { truncated: l.scrollWidth > l.clientWidth, iconInside: ir.right <= rr.right + 0.5 && ir.left >= rr.left, overflow: document.documentElement.scrollWidth - innerWidth }; })()")
        check(f"[{engine}] a long label truncates; the arrow stays in the row", lab["truncated"] and lab["iconInside"] and lab["overflow"] <= 0, json.dumps(lab))
        pg.set_viewport_size({"width": 1280, "height": 800}); pg.wait_for_timeout(300)
        if engine == "webkit":
            pg.locator("a.sfl-row").first.focus()  # Safari's Tab skips links unless a system setting is on; focus() is keyboard-style focus (it matches :focus-visible)
        else:
            pg.keyboard.press("Tab")
        pg.wait_for_timeout(800)
        fs = pg.evaluate("(() => { const a = document.activeElement; const f = a && a.querySelector('.sfl-fill'); if (!f) return null; const t = getComputedStyle(f).transform; return t === 'none' ? 1 : +t.slice(7, -1).split(',')[3]; })()")
        check(f"[{engine}] keyboard focus fills the row", fs is not None and fs > 0.95, f"{fs}")
        b.close()
        if engine != "firefox":  # Firefox has no touch emulation in Playwright
            b = getattr(p, engine).launch(headless=True)
            ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=3)
            pg = ctx.new_page(); pg.goto("http://localhost:3020/tuned/list-coloured", wait_until="load"); pg.wait_for_timeout(700)
            pg.locator("a.sfl-row").nth(0).tap(); pg.wait_for_timeout(900)
            s = pg.locator("a.sfl-row .sfl-fill").nth(0).evaluate(SCALE)
            check(f"[{engine}] touch: a tap leaves nothing filled", s < 0.05, f"{s}")
            b.close()
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(reduced_motion="reduce"); pg = ctx.new_page(); pg.goto("http://localhost:3020/tuned/list-coloured", wait_until="load")
    durs = pg.evaluate("['.sfl-row', '.sfl-fill', '.sfl-label', '.sfl-icon'].map((s) => getComputedStyle(document.querySelector(s)).transitionDuration)")
    check("reduced motion: every transition is instant", all(d.split(",")[0].strip() in ("1e-05s", "0.00001s", "0s") for d in durs), json.dumps(durs))
    ctx.close()
    ctx = b.new_context(forced_colors="active"); pg = ctx.new_page(); pg.goto("http://localhost:3020/tuned/list-coloured", wait_until="load")
    for _ in range(10):  # in dev, framework UI (Next's dev-tools button) can take the first Tab stop
        pg.keyboard.press("Tab"); pg.wait_for_timeout(150)
        if pg.evaluate("document.activeElement.matches('.sfl-row')"):
            break
    o = pg.evaluate("(() => { const a = document.activeElement, cs = getComputedStyle(a); return (a.matches('.sfl-row') ? '' : 'NOT A ROW: ' + a.tagName + ' ') + cs.outlineStyle + ' ' + cs.outlineWidth; })()")
    check("forced colours: focus gets an outline", o.startswith("solid") and not o.endswith(" 0px"), o)
    ctx.close()
    pg = b.new_page(); pg.goto("http://localhost:3020/tuned/list", wait_until="load")
    ext = pg.evaluate("[...document.querySelectorAll('a.sfl-row')].filter((a) => a.target === '_blank').map((a) => a.rel)")
    check("an off-site row opens in a new tab with rel=noopener noreferrer", ext == ["noopener noreferrer"], json.dumps(ext))
    b.close()
print(f"{sum(R)}/{len(R)} passed")
