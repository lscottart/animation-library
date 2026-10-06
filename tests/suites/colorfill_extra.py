"""Release suite for /animations:scroll-color-fill. Chromium, Firefox, WebKit.
Run with the dev or prod server on BASE:  python suites/colorfill_extra.py [base-url]"""
import json
import re
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
ROUTE = "/tuned/colorfill"
R = []
LONG = "Before we draw anything, we stand on the land at dusk, mark where the last sun falls, and design every room to answer it."
EXPECTED = ["Ü", "b", "e", "r", "c", "a", "f", "e\u0301", "\U0001F469\U0001F3FD‍\U0001F4BB", "\U0001F1E8\U0001F1ED"]
FROM = (180, 182, 184)
TO = (23, 25, 26)


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


def fill(rgb):
    """0 = the from colour, 1 = the to colour, by red channel."""
    r = int(re.findall(r"\d+", rgb)[0])
    return (FROM[0] - r) / (FROM[0] - TO[0])


COLORS = "(k) => [...document.querySelectorAll('.scf')[k].querySelectorAll('.scf__ch')].map((c) => getComputedStyle(c).color)"


def top_of(pg, k):
    return pg.evaluate(f"document.querySelectorAll('.scf')[{k}].getBoundingClientRect().top + scrollY")


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
                plain = re.sub(r"<[^>]+>", "", html).replace("&#x27;", "'").replace("&amp;", "&")
                check(f"{tag} server HTML: the whole sentence is there", LONG in plain)
            pg.goto(BASE + ROUTE, wait_until="load")
            pg.wait_for_timeout(900)

            if not reduced:
                txt = pg.evaluate("[document.querySelectorAll('.scf')[0].textContent, document.querySelectorAll('.scf')[0].innerText]")
                check(f"{tag} the text reads as the sentence (textContent and innerText)", txt[0] == LONG and txt[1].replace("\n", " ") == LONG, json.dumps(txt[1][:60]))
                g = pg.evaluate("[...document.querySelectorAll('.scf')[1].querySelectorAll('.scf__ch')].map((c) => c.textContent)")
                check(f"{tag} graphemes stay whole: decomposed accent, ZWJ emoji, flag", g == EXPECTED, json.dumps(g, ensure_ascii=True))
                broken = pg.evaluate("[...document.querySelectorAll('.scf__word')].filter((w) => new Set([...w.querySelectorAll('.scf__ch')].map((c) => Math.round(c.getBoundingClientRect().top))).size > 1).length")
                check(f"{tag} no word breaks across two lines", broken == 0, f"{broken} broken words")

            t = top_of(pg, 0)
            h = pg.evaluate("document.querySelectorAll('.scf')[0].getBoundingClientRect().height")
            # before the band (its top below 78% of the screen), mid-band, after the band (its bottom above 42%)
            pg.evaluate(f"window.scrollTo(0, {t - 900 * 0.95})")
            pg.wait_for_timeout(700)
            before = [fill(c) for c in pg.evaluate(COLORS, 0)]
            mid_y = t - 900 * 0.78 + (900 * 0.78 - 900 * 0.42 + h) * 0.5
            pg.evaluate(f"window.scrollTo(0, {mid_y})")
            pg.wait_for_timeout(900)
            mid = [fill(c) for c in pg.evaluate(COLORS, 0)]
            pg.evaluate(f"window.scrollTo(0, {t + h - 900 * 0.42 + 120})")
            pg.wait_for_timeout(900)
            after = [fill(c) for c in pg.evaluate(COLORS, 0)]
            pg.evaluate(f"window.scrollTo(0, {mid_y})")
            pg.wait_for_timeout(900)
            back = [fill(c) for c in pg.evaluate(COLORS, 0)]
            if not reduced:
                check(f"{tag} before the band: every character is grey", max(before) < 0.02, f"max fill {max(before):.2f}")
                order = all(mid[i] >= mid[i + 1] - 0.02 for i in range(len(mid) - 1))
                check(f"{tag} mid-band: filled in reading order, part way", order and mid[0] > 0.95 and mid[-1] < 0.05, f"first {mid[0]:.2f}, last {mid[-1]:.2f}")
                check(f"{tag} after the band: every character is ink", min(after) > 0.98, f"min fill {min(after):.2f}")
                check(f"{tag} scrolling back unfills it", abs(sum(back) - sum(mid)) / len(mid) < 0.05, f"{sum(back) / len(back):.2f} vs {sum(mid) / len(mid):.2f}")
            else:
                check(f"{tag} no fill: ink at every scroll position", min(before + mid + after) > 0.98, f"min {min(before + mid + after):.2f}")

            if not reduced:
                # the text changes at runtime: React keeps owning the spans, and the fill works on the new text
                pg.click("#swap")
                pg.wait_for_timeout(300)
                t3 = top_of(pg, 2)
                txt = pg.evaluate("document.querySelectorAll('.scf')[2].textContent")
                pg.evaluate(f"window.scrollTo(0, {t3 - 900 * 0.95})")
                pg.wait_for_timeout(700)
                b3 = [fill(c) for c in pg.evaluate(COLORS, 2)]
                pg.evaluate(f"window.scrollTo(0, {t3 + 400})")
                pg.wait_for_timeout(900)
                a3 = [fill(c) for c in pg.evaluate(COLORS, 2)]
                check(f"{tag} new text at runtime: rendered, and it still fills", txt == "The text changed, and it still fills." and max(b3) < 0.02 and min(a3) > 0.98, f"{txt[:30]}... before {max(b3):.2f} after {min(a3):.2f}")
            check(f"{tag} no console errors", not errs, json.dumps(errs[:2]))
            ctx.close()
        b.close()

print(f"\n{sum(R)}/{len(R)} passed", flush=True)
