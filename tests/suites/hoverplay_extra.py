"""Release suite for /animations:hover-play. Chromium, Firefox, WebKit.
Run with the dev or prod server on BASE:  python suites/hoverplay_extra.py [base-url]"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
ROUTE = "/tuned/hoverplay"
R = []


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


V = "(cls) => { const w = document.querySelector('.' + cls); const v = w.querySelector('video'); const bar = w.querySelector('div[aria-hidden]');" \
    " return { muted: v.muted, paused: v.paused, t: Math.round(v.currentTime * 1000) / 1000, bar: new DOMMatrixReadOnly(getComputedStyle(bar).transform).a }; }"
RAF = "(() => { const raf = window.requestAnimationFrame.bind(window); window.__rafs = 0; window.requestAnimationFrame = (cb) => { window.__rafs++; return raf(cb); }; })()"


def center(pg, sel):
    b = pg.locator(sel).bounding_box()
    return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2


with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)  # default autoplay policy: hover is not a gesture, so it must be muted
        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        ctx.add_init_script(RAF)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:160]))
        html = pg.request.get(BASE + ROUTE).text().lower()
        check(f"[{engine}] server HTML: inline, poster, both sources", all(k in html for k in ["playsinline", 'poster="/tuned/clip.jpg"', 'type="video/webm"', 'type="video/mp4"']))
        pg.goto(BASE + ROUTE, wait_until="load")
        pg.wait_for_timeout(1200)
        pg.mouse.move(1200, 880)
        s = pg.evaluate(V, "v1")
        check(f"[{engine}] at rest: paused at the start, muted", s["paused"] and s["t"] == 0 and s["muted"], json.dumps(s))

        x, y = center(pg, ".v1")
        pg.mouse.move(x, y)
        pg.wait_for_timeout(1500)
        s1 = pg.evaluate(V, "v1")
        check(f"[{engine}] hover: it plays, and the hairline grows", not s1["paused"] and s1["t"] > 0.3 and s1["bar"] > 0.05, json.dumps(s1))

        pg.mouse.move(x, y + 400)
        pg.wait_for_timeout(250)
        s2 = pg.evaluate(V, "v1")
        pg.wait_for_timeout(700)
        s3 = pg.evaluate(V, "v1")
        check(f"[{engine}] leave: it pauses and holds the frame it reached", s2["paused"] and s2["t"] > 0.3 and s3["t"] == s2["t"] and abs(s3["bar"] - s2["bar"]) < 0.001, json.dumps([s2, s3]))

        n = pg.evaluate("new Promise((res) => { const a = window.__rafs; setTimeout(() => res(window.__rafs - a), 1000); })")
        check(f"[{engine}] paused: no animation frames requested", n == 0, f"{n} frames")

        pg.mouse.move(x, y)
        pg.wait_for_timeout(200)
        s4 = pg.evaluate(V, "v1")
        check(f"[{engine}] hover again: it resumes from where it was, not from the start", not s4["paused"] and s4["t"] >= s3["t"] - 0.05, json.dumps([s3["t"], s4["t"]]))
        pg.mouse.move(x, y + 400)
        pg.wait_for_timeout(300)

        pg.keyboard.press("Shift")
        pg.evaluate("document.querySelector('#card1').focus()")
        pg.wait_for_timeout(900)
        k1 = pg.evaluate(V, "v1")
        pg.keyboard.press("Shift")
        pg.evaluate("document.querySelector('#card1').blur()")
        pg.wait_for_timeout(300)
        k2 = pg.evaluate(V, "v1")
        check(f"[{engine}] keyboard: focusing the card's link plays it, leaving pauses it", not k1["paused"] and k2["paused"], json.dumps([k1["paused"], k2["paused"]]))

        x2, y2 = center(pg, ".v2")
        pg.mouse.move(x2, y2)
        pg.wait_for_timeout(1300)
        tc = pg.evaluate("document.querySelector('.v2 span').textContent")
        check(f"[{engine}] the optional timecode counts", tc in ("00:01", "00:02"), tc)
        pg.mouse.move(x2, y2 + 400)
        check(f"[{engine}] no console errors", not errs, json.dumps(errs[:2]))
        ctx.close()

        # touch: plays while most of it is on screen, pauses when scrolled away
        if engine != "firefox":
            tctx = b.new_context(viewport={"width": 480, "height": 900}, has_touch=True, is_mobile=engine == "chromium")
            tp = tctx.new_page()
            tp.goto(BASE + ROUTE, wait_until="load")
            tp.wait_for_timeout(1500)
            t1 = tp.evaluate(V, "v1")
            tp.evaluate("window.scrollTo(0, 1600)")
            tp.wait_for_timeout(900)
            t2 = tp.evaluate(V, "v1")
            t3 = tp.evaluate(V, "v3")
            check(f"[{engine}] touch: plays in view, pauses out of view, the next one plays", not t1["paused"] and t2["paused"] and not t3["paused"], json.dumps([t1["paused"], t2["paused"], t3["paused"]]))
            tctx.close()

        # reduced motion: never plays by itself
        rctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        rp = rctx.new_page()
        rp.goto(BASE + ROUTE, wait_until="load")
        rp.wait_for_timeout(900)
        rx, ry = center(rp, ".v1")
        rp.mouse.move(rx, ry)
        rp.wait_for_timeout(1000)
        check(f"[{engine}] reduced motion: hover doesn't play it", rp.evaluate(V, "v1")["paused"])
        rctx.close()
        b.close()

print(f"\n{sum(R)}/{len(R)} passed", flush=True)
