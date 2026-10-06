"""Release suite for /animations:wipe-button. Chromium, Firefox, WebKit.
Run with the dev or prod server on BASE:  python suites/wipe_extra.py [base-url]"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
ROUTE = "/tuned/wipe"
R = []


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)



# Panel tops relative to the button's padding box (the panels sit inside the 1.5px border), the panel height,
# and the label colour.
STATE = r"""() => {
window.__wipe = (sel) => {
  const el = document.querySelector(sel);
  const [a, b] = el.querySelectorAll('span[aria-hidden="true"]');
  const top = el.getBoundingClientRect().top + el.clientTop;
  return [a.getBoundingClientRect().top - top, b.getBoundingClientRect().top - top, a.getBoundingClientRect().height, getComputedStyle(el.querySelector('span:not([aria-hidden])')).color];
};
}"""

# Per frame: both panels' tops relative to the button's top, the button height, the label colour.
REC = r"""
(sel) => {
  window.__rec = []; window.__on = true;
  const t0 = performance.now();
  const f = () => {
    const [a, b, h, c] = window.__wipe(sel);
    window.__rec.push([performance.now() - t0, a, b, h, c]);
    if (window.__on) requestAnimationFrame(f);
  };
  requestAnimationFrame(f);
}
"""
STOP = "(() => { window.__on = false; return window.__rec; })()"
INK = "rgb(23, 25, 26)"
PAPER = "rgb(255, 255, 255)"


def center(pg, sel):
    b = pg.locator(sel).bounding_box()
    return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, b


def monotonic(vals, sign, h):
    """Every step moves with the fill (sign -1 = up), allowing 0.6px jitter. A jump against the flow is
    allowed only when the panel was fully outside before it (a re-park of a hidden panel)."""
    bad = []
    for i in range(1, len(vals)):
        d = (vals[i] - vals[i - 1]) * -sign  # positive = against the flow
        if d > 0.6 and not abs(vals[i - 1]) >= h - 1:
            bad.append((i, round(vals[i - 1], 1), round(vals[i], 1)))
    return bad


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
        pg.evaluate(STATE)
        pg.wait_for_timeout(900)
        pg.mouse.move(1200, 860)

        check(f"[{engine}] server HTML has the label and the parked panels", "Log In" in html and "translateY(101%)" in html and "translateY(-101%)" in html)
        names = pg.get_by_role("link", name="Log In", exact=True).count()
        it = pg.evaluate("document.querySelector('#login').innerText")
        check(f"[{engine}] one accessible name; innerText is the label", names == 1 and it.strip() == "Log In", json.dumps(it))
        btn = pg.evaluate("[document.querySelector('#btn').tagName, document.querySelector('#btn').type]")
        check(f"[{engine}] without href it's a real <button> with its type", btn == ["BUTTON", "submit"], json.dumps(btn))

        # rest
        rest = pg.evaluate("window.__wipe('#login')")
        check(f"[{engine}] at rest: filled, the spare panel parked below, white label", abs(rest[0]) < 1 and rest[1] >= rest[2] - 1 and rest[3] == PAPER, json.dumps(rest))

        # hover in: the fill leaves upward
        x, y, bb = center(pg, "#login")
        pg.evaluate(REC, "#login")
        pg.mouse.move(x, y)
        pg.wait_for_timeout(450)
        rec = pg.evaluate(STOP)
        h = rec[0][3]
        a = [r[1] for r in rec]
        moving = [r[0] for r in rec if -h * 1.01 + 0.5 < r[1] < -0.5]
        span = (max(moving) - min(moving)) if moving else 0
        check(f"[{engine}] hover: the fill leaves upward, never back down", not monotonic(a, -1, h) and a[-1] <= -h + 1, f"end {a[-1]:.1f} / h {h:.1f}")
        check(f"[{engine}] hover: done in the measured time (<= 300 ms)", 0 < span <= 300, f"{span:.0f} ms in motion")
        check(f"[{engine}] hover: the label ends ink", rec[-1][4] == INK, rec[-1][4])

        # leave: the fill comes back in from below
        pg.evaluate(REC, "#login")
        pg.mouse.move(1200, 860)
        pg.wait_for_timeout(450)
        rec = pg.evaluate(STOP)
        moved = [r[1] for r in rec] if abs(rec[-1][1]) < 1 else [r[2] for r in rec]
        start_below = moved[0] > h * 0.5  # clearly from below; the first frame may already be one step in
        check(f"[{engine}] leave: the fill comes back from below and settles", not monotonic(moved, -1, h) and start_below and abs(moved[-1]) < 1, f"from {moved[0]:.1f} to {moved[-1]:.1f}")
        check(f"[{engine}] leave: the label ends white", rec[-1][4] == PAPER, rec[-1][4])

        # the race: in and out every 70 ms; no panel may ever move against the flow while visible
        pg.evaluate(REC, "#login")
        for k in range(7):
            pg.mouse.move(x, y) if k % 2 == 0 else pg.mouse.move(1200, 860)
            pg.wait_for_timeout(70)
        pg.mouse.move(1200, 860)
        pg.wait_for_timeout(600)
        rec = pg.evaluate(STOP)
        bad = monotonic([r[1] for r in rec], -1, h) + monotonic([r[2] for r in rec], -1, h)
        final = rec[-1]
        covered_end = abs(final[1]) < 1 or abs(final[2]) < 1
        check(f"[{engine}] race: 7 quick in/outs, nothing reverses or snaps while visible", not bad, json.dumps(bad[:3]))
        check(f"[{engine}] race: it settles covered after the pointer leaves", covered_end and final[4] == PAPER, json.dumps([round(final[1], 1), round(final[2], 1), final[4]]))

        # direction down, clear at rest
        x2, y2, _ = center(pg, "#down")
        pg.mouse.move(1200, 860)
        pg.evaluate(REC, "#down")
        pg.mouse.move(x2, y2)
        pg.wait_for_timeout(650)
        pg.mouse.move(1200, 860)
        pg.wait_for_timeout(600)
        rec = pg.evaluate(STOP)
        h2 = rec[0][3]
        bad = monotonic([r[1] for r in rec], 1, h2) + monotonic([r[2] for r in rec], 1, h2)
        gone = rec[-1][1] >= h2 - 1 or rec[-1][1] <= -h2 + 1
        check(f"[{engine}] direction down: fills from the top, leaves through the bottom", not bad and gone, json.dumps(bad[:3]))

        # keyboard: Tab to it clears it; Tab away covers it again
        pg.evaluate("document.activeElement && document.activeElement.blur()")
        pg.keyboard.press("Shift")
        pg.evaluate("document.querySelector('#login').focus()")
        pg.wait_for_timeout(400)
        foc = pg.evaluate("[document.activeElement.id, (() => { const s = window.__wipe('#login'); return Math.min(Math.abs(s[0]), Math.abs(s[1])); })()]")
        pg.keyboard.press("Shift")
        pg.evaluate("document.querySelector('#after').focus()")
        pg.wait_for_timeout(400)
        back = pg.evaluate("(() => { const s = window.__wipe('#login'); return Math.min(Math.abs(s[0]), Math.abs(s[1])); })()")
        check(f"[{engine}] keyboard focus clears it, Tab away refills it", foc[0] == "login" and foc[1] >= h - 1 and back < 1, json.dumps([foc, back]))

        # a mouse click focuses the link but must not hold it clear once the pointer leaves
        pg.mouse.click(x, y)
        pg.mouse.move(1200, 860)
        pg.wait_for_timeout(450)
        after = pg.evaluate("(() => { const s = window.__wipe('#login'); return Math.min(Math.abs(s[0]), Math.abs(s[1])); })()")
        check(f"[{engine}] after a mouse click and leave, it's filled again", after < 1, f"{after:.1f}")

        # font size: inherits from its parent
        big = pg.evaluate("[getComputedStyle(document.querySelector('#big')).fontSize, document.querySelector('#big').getBoundingClientRect().height]")
        check(f"[{engine}] inherits the parent's size", big[0] == "44px" and big[1] > 70, json.dumps(big))
        check(f"[{engine}] no console errors", not errs, json.dumps(errs[:2]))
        ctx.close()

        # touch: a tap must leave nothing half-wiped
        if engine != "firefox":  # Playwright's Firefox has no touch emulation
            tctx = b.new_context(viewport={"width": 430, "height": 900}, has_touch=True, is_mobile=engine == "chromium")
            tp = tctx.new_page()
            tp.goto(BASE + ROUTE, wait_until="load")
            tp.wait_for_timeout(700)
            tx, ty, _ = center(tp, "#login")
            tp.touchscreen.tap(tx, ty)
            tp.wait_for_timeout(500)
            tp.evaluate(STATE)
            st = tp.evaluate("[(() => { const s = window.__wipe('#login'); return Math.min(Math.abs(s[0]), Math.abs(s[1])); })(), window.__wipe('#login')[3]]")
            check(f"[{engine}] touch: a tap leaves it filled, nothing stuck", st[0] < 1 and st[1] == PAPER, json.dumps(st))
            tctx.close()

        # reduced motion: state changes in one step, no frames in between
        rctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        rp = rctx.new_page()
        rp.goto(BASE + ROUTE, wait_until="load")
        rp.evaluate(STATE)
        rp.wait_for_timeout(700)
        rp.mouse.move(1200, 860)
        rx, ry, _ = center(rp, "#login")
        rp.evaluate(REC, "#login")
        rp.mouse.move(rx, ry)
        rp.wait_for_timeout(300)
        rec = rp.evaluate(STOP)
        mid = [r for r in rec if -rec[0][3] * 1.01 + 0.5 < r[1] < -0.5]
        check(f"[{engine}] reduced motion: no in-between frames", not mid and rec[-1][1] <= -rec[0][3] + 1, f"{len(mid)} in-between frames")
        rctx.close()
        b.close()

print(f"\n{sum(R)}/{len(R)} passed", flush=True)
