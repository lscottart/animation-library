"""Release suite for /animations:focus-dim. Chromium, Firefox, WebKit.
Run with the dev or prod server on BASE:  python suites/focusdim_extra.py [base-url]"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
ROUTE = "/tuned/focusdim"
R = []


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


OPS = "(sel) => [...document.querySelectorAll(sel)].map((e) => [Math.round(+getComputedStyle(e).opacity * 100) / 100, getComputedStyle(e).filter])"


def center(pg, sel):
    b = pg.locator(sel).bounding_box()
    return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2


with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:160]))
        html = pg.request.get(BASE + ROUTE).text()
        check(f"[{engine}] server HTML: the group class and its settings are there", 'class="focus-dim"' in html and "--fd-dim:0.25" in html.replace(" ", ""))
        pg.goto(BASE + ROUTE, wait_until="load")
        pg.wait_for_timeout(600)
        pg.mouse.move(1200, 860)
        pg.wait_for_timeout(300)
        rest = pg.evaluate(OPS, "[id^=t-]")
        check(f"[{engine}] at rest nothing is dimmed", all(o == 1 for o, _ in rest), json.dumps(rest))

        bx, by = center(pg, "#t-b")
        pg.mouse.move(bx, by)
        pg.wait_for_timeout(800)
        s = pg.evaluate(OPS, "[id^=t-]")
        check(f"[{engine}] hover one: the others step back (0.25, grey), it stays full",
              s[1][0] == 1 and all(abs(o - 0.25) < 0.02 and "grayscale(1)" in f for i, (o, f) in enumerate(s) if i != 1), json.dumps(s))

        # cross the 24px gap from b to c, pausing in it: the group must not flash back to full
        gx = pg.locator("#t-b").bounding_box()
        gap_x = gx["x"] + gx["width"] + 12
        trace = []
        pg.mouse.move(gap_x, by)
        pg.wait_for_timeout(40)
        trace.append(pg.evaluate("+getComputedStyle(document.querySelector('#t-a')).opacity"))
        cx, cy = center(pg, "#t-c")
        pg.mouse.move(cx, cy)
        for _ in range(20):
            trace.append(pg.evaluate("+getComputedStyle(document.querySelector('#t-a')).opacity"))
            pg.wait_for_timeout(16)
        pg.wait_for_timeout(700)
        s = pg.evaluate(OPS, "[id^=t-]")
        check(f"[{engine}] crossing the gap between two items doesn't flash the group", max(trace) < 0.4 and s[2][0] == 1 and s[1][0] < 0.3, f"a peaked at {max(trace):.2f}")

        pg.mouse.move(1200, 860)
        pg.wait_for_timeout(900)
        check(f"[{engine}] leave: everything comes back", all(o == 1 for o, _ in pg.evaluate(OPS, "[id^=t-]")))

        lx, ly = center(pg, "#n-1 a")
        pg.mouse.move(lx, ly)
        pg.wait_for_timeout(800)
        s = pg.evaluate(OPS, "[id^=n-]")
        check(f"[{engine}] options: 0.4 and no grey on the list", s[1][0] == 1 and abs(s[0][0] - 0.4) < 0.02 and s[0][1] == "none", json.dumps(s))
        pg.mouse.move(1200, 860)
        pg.wait_for_timeout(900)

        pg.keyboard.press("Shift")
        pg.evaluate("document.querySelector('#n-2 a').focus()")
        pg.wait_for_timeout(800)
        k = pg.evaluate(OPS, "[id^=n-]")
        pg.keyboard.press("Shift")
        pg.evaluate("document.querySelector('#after').focus()")
        pg.wait_for_timeout(900)
        k2 = pg.evaluate(OPS, "[id^=n-]")
        check(f"[{engine}] keyboard focus dims the others, and moving on brings them back", k[2][0] == 1 and k[0][0] < 0.45 and all(o == 1 for o, _ in k2), json.dumps([k, k2]))
        check(f"[{engine}] no console errors", not errs, json.dumps(errs[:2]))
        ctx.close()

        if engine != "firefox":
            tctx = b.new_context(viewport={"width": 430, "height": 900}, has_touch=True, is_mobile=engine == "chromium")
            tp = tctx.new_page()
            tp.goto(BASE + ROUTE, wait_until="load")
            tp.wait_for_timeout(600)
            tx, ty = center(tp, "#t-b")
            tp.touchscreen.tap(tx, ty)
            tp.wait_for_timeout(800)
            s = tp.evaluate(OPS, "[id^=t-]")
            check(f"[{engine}] touch: a tap leaves nothing dimmed", all(o == 1 for o, _ in s), json.dumps(s))
            tctx.close()

        rctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        rp = rctx.new_page()
        rp.goto(BASE + ROUTE, wait_until="load")
        rp.wait_for_timeout(600)
        bx, by = center(rp, "#t-b")
        rp.mouse.move(bx, by)
        rp.wait_for_timeout(60)
        s = rp.evaluate(OPS, "[id^=t-]")
        check(f"[{engine}] reduced motion: it dims at once, no fade", abs(s[0][0] - 0.25) < 0.02, json.dumps(s))
        rctx.close()
        b.close()

print(f"\n{sum(R)}/{len(R)} passed", flush=True)
