"""Release suite for /animations:cursor-label. Chromium, Firefox, WebKit.
Run with the dev or prod server on BASE:  python suites/cursor_extra.py [base-url]"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
ROUTE = "/tuned/cursor"
R = []


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


# The label's state: visible?, its x/y on screen, its text, and the roll (text translateY as a share of its height).
INSTALL = r"""() => {
  window.__lab = () => {
    const root = document.querySelector('[data-cursor-label-root]');
    const text = root.querySelector('span span');
    const m = new DOMMatrixReadOnly(getComputedStyle(root).transform);
    const t = new DOMMatrixReadOnly(getComputedStyle(text).transform);
    return { vis: getComputedStyle(root).visibility, x: m.m41, y: m.m42, text: text.textContent, roll: t.m42 / text.offsetHeight, blend: getComputedStyle(root).mixBlendMode };
  };
  window.__rec = []; window.__on = false;
  window.__start = () => { window.__rec = []; window.__on = true; const f = () => { window.__rec.push(window.__lab()); if (window.__on) requestAnimationFrame(f); }; requestAnimationFrame(f); };
  window.__stop = () => { window.__on = false; return window.__rec; };
}"""


def mid(pg, sel, fx=0.5, fy=0.5):
    b = pg.locator(sel).bounding_box()
    return b["x"] + b["width"] * fx, b["y"] + b["height"] * fy


def glide(pg, x0, y0, x1, y1, steps=10):
    for i in range(1, steps + 1):
        pg.mouse.move(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps)
        pg.wait_for_timeout(16)


with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:160]))
        html = pg.request.get(BASE + ROUTE).text()
        pg.goto(BASE + ROUTE, wait_until="load")
        pg.evaluate(INSTALL)
        pg.wait_for_timeout(800)

        check(f"[{engine}] server HTML: the label is there, hidden, out of the accessibility tree", "(View)" in html and "visibility:hidden" in html.replace(" ", "") and 'aria-hidden="true"' in html)

        # enter A: the label rolls in at the pointer and reads A's label
        ax, ay = mid(pg, "#a", 0.3, 0.4)
        pg.mouse.move(40, 860)
        glide(pg, 40, 860, ax, ay, 12)
        pg.wait_for_timeout(1600)
        s = pg.evaluate("window.__lab()")
        check(f"[{engine}] over A: shows A's label, rolled in", s["vis"] == "visible" and s["text"] == "(View house)" and abs(s["roll"]) < 0.02, json.dumps(s))
        check(f"[{engine}] it settles at the pointer plus the offset", abs(s["x"] - (ax + 18)) < 2 and abs(s["y"] - (ay - 10)) < 2, f"label at {s['x']:.1f},{s['y']:.1f}, pointer {ax:.0f},{ay:.0f}")
        check(f"[{engine}] blend: white with difference", s["blend"] == "difference")

        # the trail: one quick move, and the label lags behind, then catches up
        pg.mouse.move(ax + 160, ay + 40)
        pg.wait_for_timeout(50)
        lag = pg.evaluate("window.__lab()")
        pg.wait_for_timeout(1500)
        caught = pg.evaluate("window.__lab()")
        check(f"[{engine}] the label trails the pointer, then catches up", (ax + 160 + 18) - lag["x"] > 40 and abs(caught["x"] - (ax + 178)) < 2, f"behind by {(ax + 178) - lag['x']:.0f}px after 50ms")

        # direct jump A -> B: A's label leaves completely before B's rises from below
        pg.evaluate("window.__start()")
        bx, by = mid(pg, "#b", 0.5, 0.4)
        glide(pg, ax + 160, ay + 40, bx, by, 6)
        pg.wait_for_timeout(900)
        rec = pg.evaluate("window.__stop()")
        first_b = next((i for i, r in enumerate(rec) if r["text"] == "(View model)"), None)
        ok = first_b is not None and rec[first_b - 1]["roll"] <= -1.0 and rec[first_b]["roll"] >= 0.5 and abs(rec[-1]["roll"]) < 0.02
        check(f"[{engine}] A to B: the old label leaves before the new one rises in", ok, json.dumps([rec[first_b - 1]["roll"], rec[first_b]["roll"]] if first_b else "B never shown"))

        # touching items D -> E: no gap to cross, so this is the direct jump; the queue must still hold
        dx, dy = mid(pg, "#d", 0.7, 0.5)
        glide(pg, bx, by, dx, dy, 8)
        pg.wait_for_timeout(900)
        pg.evaluate("window.__start()")
        ex, ey = mid(pg, "#e", 0.3, 0.5)
        glide(pg, dx, dy, ex, ey, 4)
        pg.wait_for_timeout(900)
        rec = pg.evaluate("window.__stop()")
        first_e = next((i for i, r in enumerate(rec) if r["text"] == "(View photo)"), None)
        ok = first_e is not None and rec[first_e - 1]["roll"] <= -1.0 and rec[first_e]["roll"] >= 0.5 and abs(rec[-1]["roll"]) < 0.02
        check(f"[{engine}] touching items: the old label leaves before the new one rises in", ok, json.dumps([rec[first_e - 1]["roll"], rec[first_e]["roll"]] if first_e else "E never shown"))
        bx, by = ex, ey

        # leave to a plain area: it rolls out
        px, py = mid(pg, "#plain")
        glide(pg, bx, by, px, py, 8)
        pg.wait_for_timeout(600)
        s = pg.evaluate("window.__lab()")
        check(f"[{engine}] off any labelled item: it rolls out", s["roll"] <= -1.0, f"roll {s['roll']:.2f}")

        # catch back: leave A and come back mid-exit; no replay from below
        glide(pg, px, py, ax, ay, 8)
        pg.wait_for_timeout(900)
        pg.evaluate("window.__start()")
        pg.mouse.move(ax, ay + 300)  # out, onto the empty page
        pg.wait_for_timeout(110)
        pg.mouse.move(ax, ay)  # back before the exit finishes
        pg.wait_for_timeout(700)
        rec = pg.evaluate("window.__stop()")
        replay = max(r["roll"] for r in rec)
        check(f"[{engine}] back on the same item mid-exit: caught, not replayed", replay < 0.05 and abs(rec[-1]["roll"]) < 0.02 and rec[-1]["text"] == "(View house)", f"max roll {replay:.2f}")

        # scrolling the item out from under a still pointer retires the label
        pg.mouse.move(ax, ay)
        pg.wait_for_timeout(600)
        pg.mouse.wheel(0, 700)
        pg.wait_for_timeout(900)
        s = pg.evaluate("window.__lab()")
        check(f"[{engine}] scrolled away under a still pointer: it rolls out", s["roll"] <= -1.0, f"roll {s['roll']:.2f}")

        # the label never blocks the page: clicking through it still hits the link
        pg.evaluate("window.scrollTo(0, 0)")
        pg.wait_for_timeout(400)
        pg.mouse.move(ax, ay)
        pg.wait_for_timeout(700)
        lx = pg.evaluate("window.__lab()")
        pg.mouse.click(lx["x"] + 2, lx["y"] + 6)
        pg.wait_for_timeout(200)
        check(f"[{engine}] clicks pass through the label", pg.evaluate("location.hash") == "#a", pg.evaluate("location.hash"))
        check(f"[{engine}] no console errors", not errs, json.dumps(errs[:2]))
        ctx.close()

        # touch: no label
        if engine != "firefox":
            tctx = b.new_context(viewport={"width": 430, "height": 900}, has_touch=True, is_mobile=engine == "chromium")
            tp = tctx.new_page()
            tp.goto(BASE + ROUTE, wait_until="load")
            tp.evaluate(INSTALL)
            tp.wait_for_timeout(700)
            tx, ty = mid(tp, "#a")
            tp.touchscreen.tap(tx, ty)
            tp.wait_for_timeout(600)
            check(f"[{engine}] touch: no label", tp.evaluate("window.__lab()")["vis"] == "hidden")
            tctx.close()

        # reduced motion: no label
        rctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        rp = rctx.new_page()
        rp.goto(BASE + ROUTE, wait_until="load")
        rp.evaluate(INSTALL)
        rp.wait_for_timeout(700)
        rx, ry = mid(rp, "#a")
        glide(rp, 40, 860, rx, ry, 10)
        rp.wait_for_timeout(700)
        check(f"[{engine}] reduced motion: no label", rp.evaluate("window.__lab()")["vis"] == "hidden")
        rctx.close()
        b.close()

print(f"\n{sum(R)}/{len(R)} passed", flush=True)
