"""Release suite for /animations:number-roll. Chromium, Firefox, WebKit.
Run with the dev or prod server on BASE:  python suites/numroll_extra.py [base-url]"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
ROUTE = "/tuned/numroll"
R = []


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


# For each digit column: the digit its strip shows (translateY / 1em, negated), and the real digit it should show.
COLS = r"""(cls) => {
  const root = document.querySelector('.' + cls);
  const fs = parseFloat(getComputedStyle(root).fontSize);
  return [...root.querySelectorAll('.number-roll__col')].map((c) => {
    const m = new DOMMatrixReadOnly(getComputedStyle(c, '::before').transform);
    return { shown: Math.round((-m.m42 / fs) * 100) / 100, want: +getComputedStyle(c).getPropertyValue('--d') };
  });
}"""
TEXT = "(cls) => document.querySelector('.' + cls).innerText"
# The glyph box of a column's (invisible) sizing digit and of a plain "0" in the same line: equal when the baselines match.
BASELINE = r"""(cls) => {
  const root = document.querySelector('.' + cls);
  const box = (n) => { const r = document.createRange(); r.selectNodeContents(n); const b = r.getBoundingClientRect(); return [b.top, b.bottom]; };
  return { digit: box(root.querySelector('.number-roll__ghost')), text: box(root.parentElement.querySelector('.ref')) };
}"""


def landed(cols):
    return all(abs(c["shown"] - c["want"]) < 0.02 for c in cols)


with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)
        for reduced in (False, True):
            ctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce" if reduced else "no-preference")
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:160]))
            tag = f"[{engine}{' reduced' if reduced else ''}]"
            if not reduced:
                html = pg.request.get(BASE + ROUTE).text()
                check(f"{tag} server HTML: the value is in the page as text", "4:38 PM" in html and "1,284" in html)
            pg.goto(BASE + ROUTE, wait_until="load")

            # the number on screen at load never shows another value
            # (only painted frames count: the Pages Router's dev server hides the body until its CSS is injected)
            early = []
            for _ in range(10):
                if pg.evaluate("document.querySelector('.t-top').getClientRects().length > 0"):
                    early.append(landed(pg.evaluate(COLS, "t-top")))
                pg.wait_for_timeout(60)
            if not reduced:
                check(f"{tag} on screen at load: shows its value, no roll", len(early) >= 5 and all(early), f"{len(early)} painted samples")
                t = pg.evaluate(TEXT, "t-top")
                check(f"{tag} the text is the value, once (no digit strips in innerText or copy)", t == "4:38 PM", json.dumps(t))
                aria = pg.locator(".t-top").aria_snapshot()
                check(f"{tag} screen readers get the value once", aria.strip() == "- text: 4:38 PM", json.dumps(aria))
                w0 = pg.locator(".t-top").bounding_box()["width"]
                bl = pg.evaluate(BASELINE, "t-top")
                off = max(abs(bl["digit"][0] - bl["text"][0]), abs(bl["digit"][1] - bl["text"][1]))
                check(f"{tag} the digits sit on the same baseline as the text beside them", off < 0.5, f"off by {off:.2f}px at 96px")

            # off screen at load: waits at zero, rolls in when seen, right-most digit first
            if not reduced:
                below = pg.evaluate(COLS, "t-below")
                check(f"{tag} off screen at load: it waits at zero", all(c["shown"] == 0 for c in below), json.dumps(below))
            pg.evaluate("document.querySelector('.t-below').scrollIntoView({ block: 'center' })")
            pg.wait_for_timeout(260)
            mid = pg.evaluate(COLS, "t-below")
            pg.wait_for_timeout(1800)
            end = pg.evaluate(COLS, "t-below")
            if not reduced:
                # 1,284: by now the right-most digit (4) is further along its way than the left-most (1)
                right_lead = (mid[-1]["shown"] / mid[-1]["want"]) > (mid[0]["shown"] / mid[0]["want"]) + 0.05
                check(f"{tag} seen: it rolls up, right-most digit first, and lands exactly", right_lead and landed(end), json.dumps([mid[0], mid[-1]]))
            else:
                check(f"{tag} reduced motion: it shows the value, no roll", landed(mid) and landed(end), json.dumps(mid))

            # a new value rolls (and under reduced motion it just changes)
            pg.evaluate("window.scrollTo(0, 0)")
            pg.wait_for_timeout(300)
            pg.click("#next")
            pg.wait_for_timeout(120)
            m = pg.evaluate(COLS, "t-top")
            pg.wait_for_timeout(1700)
            e = pg.evaluate(COLS, "t-top")
            t = pg.evaluate(TEXT, "t-top")
            if not reduced:
                moving = not landed(m)
                check(f"{tag} a new value rolls to the new digits", moving and landed(e) and t == "5:14 PM", f"{t}, in motion at 120ms: {moving}")
                w1 = pg.locator(".t-top").bounding_box()["width"]
                check(f"{tag} the width holds as the digits change (tabular)", abs(w1 - w0) < 0.5, f"{w0:.1f} -> {w1:.1f}")
                pg.click("#grow")
                pg.wait_for_timeout(1700)
                g = pg.evaluate(COLS, "t-len")
                check(f"{tag} a longer value adds a column and lands", len(g) == 2 and landed(g) and pg.evaluate(TEXT, "t-len") == "10", json.dumps(g))
            else:
                check(f"{tag} reduced motion: a new value changes at once", landed(m) and t == "5:14 PM")
            check(f"{tag} no console errors", not errs, json.dumps(errs[:2]))
            ctx.close()
        b.close()

print(f"\n{sum(R)}/{len(R)} passed", flush=True)
