"""Release suite for /animations:note-minimap. Chromium, Firefox, WebKit.
Run with the dev or prod server on BASE:  python suites/minimap_extra.py [base-url]"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
ROUTE = "/tuned/minimap"
R = []


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


GEOM = r"""() => {
  const rail = document.querySelector('.nm').getBoundingClientRect();
  const finder = document.querySelector('.nm__finder').getBoundingClientRect();
  const cards = [...document.querySelectorAll('.nm__card')].map((c) => { const r = c.getBoundingClientRect(); return r.top + r.height / 2; });
  const cur = [...document.querySelectorAll('.nm__hit')].findIndex((b) => b.getAttribute('aria-current') === 'location');
  return { railMid: rail.top + rail.height / 2, finderMid: finder.top + finder.height / 2, cards, cur };
}"""
SHIFT = "() => new DOMMatrixReadOnly(getComputedStyle(document.querySelector('.nm__strip')).transform).m42"


def framed(g, i):
    """The viewfinder sits on card i, and the rail's centre (the reading position) lies between card i and the
    next: the strip glides continuously through a section, it doesn't jump card to card."""
    c = g["cards"]
    nxt = c[i + 1] if i + 1 < len(c) else c[i]
    return g["cur"] == i and abs(g["finderMid"] - c[i]) < 1.5 and c[i] - 1.5 <= g["railMid"] <= nxt + 1.5


def scroll_to_section(pg, i, smooth=False):
    # put the reading line (40% down) a little inside section i
    pg.evaluate(f"""() => {{ const h = document.querySelector('#s{i} h2'); const top = h.getBoundingClientRect().top + scrollY - 0.4 * innerHeight + 30;
      window.scrollTo({{ top, behavior: '{'smooth' if smooth else 'auto'}' }}); }}""")


with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        # count animation frames requested by the page, to prove the loop really sleeps
        ctx.add_init_script("(() => { const raf = window.requestAnimationFrame.bind(window); window.__rafs = 0; window.requestAnimationFrame = (cb) => { window.__rafs++; return raf(cb); }; })()")
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:160]))
        pg.goto(BASE + ROUTE, wait_until="load")
        pg.wait_for_timeout(1500)

        names = pg.evaluate("[...document.querySelectorAll('.nm__hit')].map((b) => b.getAttribute('aria-label'))")
        check(f"[{engine}] five cards for six sections, named 'Go to …'", len(names) == 5 and names[0] == "Go to Harlan House" and names[4] == "Go to Quarry House", json.dumps(names))
        imgs = pg.evaluate("[...document.querySelectorAll('.nm__card')].map((c) => !!c.querySelector('img'))")
        check(f"[{engine}] the section without a thumbnail gets a title-only card", imgs == [True, True, False, True, True], json.dumps(imgs))

        g = pg.evaluate(GEOM)
        check(f"[{engine}] at the top: card 1 is current and framed, the rail on the reading position", framed(g, 0), json.dumps(g))

        # jump the page to section 3 and watch the strip: it should overshoot a little, then settle on card 3
        target_shift = None
        scroll_to_section(pg, 3)
        trace = []
        for _ in range(120):
            trace.append(pg.evaluate(SHIFT))
            pg.wait_for_timeout(25)
        g = pg.evaluate(GEOM)
        final = trace[-1]
        start = trace[0]
        overshoot = max((final - t) if final < start else (t - final) for t in trace)
        check(f"[{engine}] scrolled into section 3: card 3 current and framed, the rail on the reading position", framed(g, 2), json.dumps(g))
        check(f"[{engine}] the strip overshoots a little, then settles (the soft spring)", 0.5 < overshoot < 30, f"overshoot {overshoot:.1f}px")

        # once settled, the loop sleeps: nothing writes to the strip
        n = pg.evaluate("""() => new Promise((res) => { const a = window.__rafs; setTimeout(() => res(window.__rafs - a), 1000); })""")
        check(f"[{engine}] settled: the loop sleeps (no animation frames for a second)", n == 0, f"{n} frames requested")

        # click card 5: the page glides there and the heading lands on the reading line
        pg.locator(".nm__hit").nth(4).click()
        pg.wait_for_timeout(2400)
        off = pg.evaluate("document.querySelector('#s5 h2').getBoundingClientRect().top - 0.4 * innerHeight")
        g = pg.evaluate(GEOM)
        check(f"[{engine}] click a card: the page goes there", abs(off + 8) < 40 and g["cur"] == 4, f"heading {off:.0f}px from the reading line, current {g['cur']}")

        # keyboard: focus card 2 and press Enter
        pg.locator(".nm__hit").nth(1).focus()
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(2400)
        off = pg.evaluate("document.querySelector('#s2 h2').getBoundingClientRect().top - 0.4 * innerHeight")
        check(f"[{engine}] keyboard: Enter on a card goes there", abs(off + 8) < 40, f"{off:.0f}px")
        check(f"[{engine}] no console errors", not errs, json.dumps(errs[:2]))
        ctx.close()

        # narrow screens: hidden, and its loop doesn't run
        nctx = b.new_context(viewport={"width": 800, "height": 900})
        np_ = nctx.new_page()
        np_.goto(BASE + ROUTE, wait_until="load")
        np_.wait_for_timeout(900)
        disp = np_.evaluate("getComputedStyle(document.querySelector('.nm')).display")
        before = np_.evaluate("document.querySelector('.nm__strip').style.transform")
        np_.evaluate("window.scrollTo(0, 2400)")
        np_.wait_for_timeout(600)
        after = np_.evaluate("document.querySelector('.nm__strip').style.transform")
        check(f"[{engine}] under 900px: hidden, and the loop never runs", disp == "none" and before == after == "", json.dumps([disp, before, after]))
        nctx.close()

        # reduced motion: no spring, it lands exactly
        rctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        rp = rctx.new_page()
        rp.goto(BASE + ROUTE, wait_until="load")
        rp.wait_for_timeout(1200)
        scroll_to_section(rp, 4)
        trace = []
        for _ in range(40):
            trace.append(rp.evaluate(SHIFT))
            rp.wait_for_timeout(25)
        g = rp.evaluate(GEOM)
        spread = max(trace[3:]) - min(trace[3:])
        check(f"[{engine}] reduced motion: it snaps, no spring", spread < 0.5 and framed(g, 3), f"spread {spread:.2f}px after the first frames; {json.dumps(g)}")
        rctx.close()
        b.close()

print(f"\n{sum(R)}/{len(R)} passed", flush=True)
