"""Release suite for /animations:travelling-indicator. Chromium, Firefox, WebKit.
Run with the dev or prod server on BASE:  python suites/travel_extra.py [base-url]"""
import json
import re
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
ROUTE = "/tuned/travel"
R = []
INK = "rgb(23, 25, 26)"
AWAY = (1200, 860)  # empty canvas, clear of every nav


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


# The block's visible box (from its clip-path insets) and each link's box, relative to the nav.
INSTALL = r"""() => {
  window.__nav = (wrap) => {
    const nav = document.querySelector(wrap + ' nav');
    const o = nav.getBoundingClientRect();
    const links = [...nav.querySelectorAll('.tn__row')[0].children].map((a) => { const r = a.getBoundingClientRect(); return { l: r.left - o.left, w: r.width, t: r.top - o.top, h: r.height, cur: a.getAttribute('aria-current') }; });
    const copy = [...nav.querySelectorAll('.tn__row')[1]?.children ?? []].map((a) => { const r = a.getBoundingClientRect(); return { l: r.left - o.left, t: r.top - o.top }; });
    const mark = nav.querySelector('.tn__block, .tn__line');
    const cs = getComputedStyle(mark);
    let box = null;
    if (mark.classList.contains('tn__block')) {
      const m = cs.clipPath.match(/inset\(([-\d.]+)px ([-\d.]+)px ([-\d.]+)px ([-\d.]+)px/);
      if (m) box = { l: +m[4], w: o.width - +m[4] - +m[2], t: +m[1] };
    } else {
      const r = mark.getBoundingClientRect();
      box = { l: r.left - o.left, w: r.width };
    }
    return { links, copy, box, opacity: +cs.opacity };
  };
  window.__rec = []; window.__on = false;
  window.__start = (wrap) => { window.__rec = []; window.__on = true; const f = () => { window.__rec.push(window.__nav(wrap)); if (window.__on) requestAnimationFrame(f); }; requestAnimationFrame(f); };
  window.__stop = () => { window.__on = false; return window.__rec; };
  window.__tip = () => { const t = document.querySelector('.tt__tip'); const o = document.querySelector('.tt').getBoundingClientRect(); const r = t.getBoundingClientRect(); return { x: r.left - o.left, w: r.width, op: +getComputedStyle(t).opacity, text: t.textContent }; };
}"""


def on(box, link, tol=1.0):
    return box is not None and abs(box["l"] - link["l"]) < tol and abs(box["w"] - link["w"]) < tol


def key_focus(pg, engine, sel):
    """Give sel keyboard focus. Chromium and Firefox: real Tab presses into it (Firefox gives a scripted focus the
    focus-visible state of the focus before it, so a script alone fails after a mouse click). WebKit's Tab skips links:
    a key press, then a scripted focus, which WebKit counts as keyboard."""
    if engine == "webkit":
        pg.keyboard.press("Shift")
        pg.evaluate(f"document.querySelector({sel!r}).focus()")
    else:
        pg.evaluate(f"document.querySelector({sel!r}).focus()")
        pg.keyboard.press("Shift+Tab")
        pg.keyboard.press("Tab")


def center(pg, sel):
    b = pg.locator(sel).bounding_box()
    return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2


with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)

        # no JavaScript: the server's CSS already marks the current page
        nctx = b.new_context(viewport={"width": 1280, "height": 900}, java_script_enabled=False)
        np_ = nctx.new_page()
        np_.goto(BASE + ROUTE, wait_until="load")
        bg = np_.evaluate("getComputedStyle(document.querySelector('#block nav a[aria-current=page]')).backgroundColor")
        check(f"[{engine}] before JavaScript: the current page is already highlighted", bg == INK, bg)
        nctx.close()

        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:160]))
        pg.goto(BASE + ROUTE, wait_until="load")
        pg.evaluate(INSTALL)
        pg.wait_for_timeout(900)

        nav = pg.get_by_role("navigation", name="Main")
        n = [nav.get_by_role("link", name=x, exact=True).count() for x in ["Houses", "Studio", "Contact"]]
        check(f"[{engine}] each link is in the accessibility tree once (the copy is hidden)", n == [1, 1, 1], json.dumps(n))

        s = pg.evaluate("window.__nav('#block')")
        check(f"[{engine}] at rest: the block sits on the current page", on(s["box"], s["links"][1]) and s["opacity"] > 0.99 and s["links"][1]["cur"] == "page", json.dumps(s["box"]))
        drift = max(max(abs(c["l"] - l["l"]), abs(c["t"] - l["t"])) for c, l in zip(s["copy"], s["links"]))
        check(f"[{engine}] the white copy lines up exactly with the real text", drift < 0.5, f"max offset {drift:.2f}px")

        # hover Process: the block travels there, steadily, and resizes
        px, py = center(pg, "#block nav .tn__row:first-child a:nth-child(3)")
        pg.mouse.move(*AWAY)
        pg.evaluate("window.__start('#block')")
        pg.mouse.move(px, py)
        pg.wait_for_timeout(800)
        rec = pg.evaluate("window.__stop()")
        xs = [r["box"]["l"] for r in rec if r["box"]]
        mono = all(xs[i + 1] >= xs[i] - 0.3 for i in range(len(xs) - 1))
        steps = len({round(x) for x in xs})
        check(f"[{engine}] hover: the block travels to the item and takes its width", on(rec[-1]["box"], rec[-1]["links"][2]) and mono and steps > 4, f"{steps} distinct positions")

        # leave: back to the current page
        pg.mouse.move(*AWAY)
        pg.wait_for_timeout(800)
        s = pg.evaluate("window.__nav('#block')")
        check(f"[{engine}] leave: it returns to the current page", on(s["box"], s["links"][1]))

        # click: the clicked item becomes current and keeps the block
        jx, jy = center(pg, "#block nav .tn__row:first-child a:nth-child(4)")
        pg.mouse.click(jx, jy)
        pg.mouse.move(*AWAY)
        pg.wait_for_timeout(800)
        s = pg.evaluate("window.__nav('#block')")
        check(f"[{engine}] click: that item becomes current and keeps the block", s["links"][3]["cur"] == "page" and on(s["box"], s["links"][3]))

        # keyboard: the block follows focus, and goes back when focus leaves the nav
        key_focus(pg, engine, "#block nav .tn__row a:nth-child(5)")
        pg.wait_for_timeout(700)
        s = pg.evaluate("window.__nav('#block')")
        k1 = on(s["box"], s["links"][4])
        pg.keyboard.press("Shift")
        pg.evaluate("document.querySelector('#after').focus()")
        pg.wait_for_timeout(700)
        s = pg.evaluate("window.__nav('#block')")
        check(f"[{engine}] keyboard: it follows focus, and returns when focus leaves", k1 and on(s["box"], s["links"][3]))

        # underline variant
        s = pg.evaluate("window.__nav('#under')")
        u0 = on(s["box"], s["links"][0])
        cx, cy = center(pg, "#under nav .tn__row a:nth-child(5)")
        pg.mouse.move(cx, cy)
        pg.wait_for_timeout(800)
        u1 = pg.evaluate("window.__nav('#under')")
        pg.mouse.move(*AWAY)
        pg.wait_for_timeout(800)
        u2 = pg.evaluate("window.__nav('#under')")
        check(f"[{engine}] underline: rests on the current item, travels on hover, returns", u0 and on(u1["box"], u1["links"][4]) and on(u2["box"], u2["links"][0]))

        # no current page: hidden at rest, appears in place on hover, fades on leave
        s0 = pg.evaluate("window.__nav('#none')")
        hx, hy = center(pg, "#none nav .tn__row a:nth-child(3)")
        pg.evaluate("window.__start('#none')")
        pg.mouse.move(hx, hy)
        pg.wait_for_timeout(700)
        rec = pg.evaluate("window.__stop()")
        first_seen = next((r for r in rec if r["opacity"] > 0.05), None)
        pg.mouse.move(*AWAY)
        pg.wait_for_timeout(700)
        s2 = pg.evaluate("window.__nav('#none')")
        check(f"[{engine}] nothing current: hidden at rest, appears on the item (no slide in), fades on leave",
              s0["opacity"] < 0.01 and first_seen is not None and on(first_seen["box"], first_seen["links"][2]) and s2["opacity"] < 0.01)

        # the tooltip: appears in place, then travels between buttons without fading, then hides
        btns = pg.locator(".tt__btn")
        b1 = btns.nth(0).bounding_box(); b3 = btns.nth(2).bounding_box()
        pg.mouse.move(b1["x"] + 24, b1["y"] + 24)
        pg.wait_for_timeout(500)
        t1 = pg.evaluate("window.__tip()")
        trace = []
        pg.mouse.move(b3["x"] + 24, b3["y"] + 24)
        for _ in range(20):
            trace.append(pg.evaluate("window.__tip()"))
            pg.wait_for_timeout(25)
        pg.wait_for_timeout(300)
        t3 = pg.evaluate("window.__tip()")
        o = pg.locator(".tt").bounding_box()
        centred = abs((t3["x"] + t3["w"] / 2) - (b3["x"] - o["x"] + b3["width"] / 2)) < 1.5
        steady = min(t["op"] for t in trace) > 0.95
        check(f"[{engine}] tooltip: shows the label, travels to the next button without fading, re-centres and resizes",
              t1["text"] == "Share" and t1["op"] > 0.99 and t3["text"] == "Add to collection" and centred and steady and t3["w"] > t1["w"] + 20,
              json.dumps({"min opacity in travel": round(min(t["op"] for t in trace), 2), "w": [round(t1["w"]), round(t3["w"])]}))
        pg.mouse.move(*AWAY)
        pg.wait_for_timeout(600)
        check(f"[{engine}] tooltip: hides when the pointer leaves the toolbar", pg.evaluate("window.__tip()")["op"] < 0.01)
        key_focus(pg, engine, ".tt__btn:nth-child(4)")  # the tip and the measuring twin come first
        pg.wait_for_timeout(700)
        tk = pg.evaluate("window.__tip()")
        check(f"[{engine}] tooltip: keyboard focus shows it", tk["text"] == "Download" and tk["op"] > 0.99, json.dumps(tk))
        check(f"[{engine}] no console errors", not errs, json.dumps(errs[:2]))
        ctx.close()

        # reduced motion: it jumps, no frames in between
        rctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        rp = rctx.new_page()
        rp.goto(BASE + ROUTE, wait_until="load")
        rp.evaluate(INSTALL)
        rp.wait_for_timeout(700)
        px, py = center(rp, "#block nav .tn__row:first-child a:nth-child(3)")
        rp.mouse.move(*AWAY)
        rp.evaluate("window.__start('#block')")
        rp.mouse.move(px, py)
        rp.wait_for_timeout(400)
        rec = rp.evaluate("window.__stop()")
        mids = [r for r in rec if r["box"] and not on(r["box"], r["links"][1]) and not on(r["box"], r["links"][2])]
        check(f"[{engine}] reduced motion: it jumps straight to the item", not mids and on(rec[-1]["box"], rec[-1]["links"][2]), f"{len(mids)} in-between frames")
        rctx.close()
        b.close()

print(f"\n{sum(R)}/{len(R)} passed", flush=True)
