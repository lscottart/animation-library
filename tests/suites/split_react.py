"""After the reveal, React still owns the revealed text: Next links route client-side, handlers fire, updates land.
Run: python suites/split_react.py [base-url]"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
R = []


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)
        pg = b.new_page(viewport={"width": 1100, "height": 900})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:200]))
        pg.goto(BASE + "/tuned/split-react", wait_until="load")
        pg.wait_for_function("document.fonts.status === 'loaded'")
        pg.wait_for_timeout(2600)
        pg.evaluate("window.__mark = 'kept'")
        pg.click("#nextlink")
        pg.wait_for_url("**/tuned/roll", timeout=10000)
        pg.wait_for_timeout(300)
        mark = pg.evaluate("window.__mark || null")
        check(f"[{engine}] a Next <Link> inside the text routes client-side", mark == "kept", "page kept its JS state" if mark else "full page reload")
        pg.goto(BASE + "/tuned/split-react", wait_until="load")
        pg.wait_for_function("document.fonts.status === 'loaded'")
        pg.wait_for_timeout(2600)
        left = pg.evaluate("document.querySelectorAll('#links .split-line, #dyn .split-line, #struct .split-line').length")
        check(f"[{engine}] every reveal finished and reverted", left == 0, f"{left} split elements left")

        pg.click("#handler")
        pg.wait_for_timeout(200)
        check(f"[{engine}] a React onClick inside the text still fires", pg.text_content("#clicks") == "1", f"clicks shown: {pg.text_content('#clicks')}")

        pg.click("#inc")
        pg.click("#inc")
        pg.wait_for_timeout(200)
        dyn = pg.text_content("#dyn")
        check(f"[{engine}] state updates still reach the text", dyn.startswith("2 items") and dyn.rstrip().endswith("count 2."), json.dumps(dyn[:40] + "…" + dyn[-12:]))

        # keyboard: focus a link in unrevealed text (its first copy, if SplitText copied it); it scrolls in, reveals,
        # reverts, and focus has to still be on the link afterwards
        pg.goto(BASE + "/tuned/split-react", wait_until="load")
        pg.wait_for_function("document.fonts.status === 'loaded'")
        pg.wait_for_timeout(1500)
        copies = pg.evaluate("document.querySelectorAll('#spanning a.span-link').length")
        if engine == "webkit":  # WebKit's Tab skips links by default
            pg.evaluate("document.querySelector('#spanning a.span-link').focus()")
        else:
            for _ in range(15):
                pg.keyboard.press("Tab")
                if pg.evaluate("!!document.activeElement && document.activeElement.matches('a.span-link')"):
                    break
        pg.wait_for_timeout(3200)
        st = pg.evaluate("""(() => { const a = document.activeElement, box = document.querySelector('#spanning');
            return { onLink: !!a && a.matches('a.span-link') && box.contains(a), links: box.querySelectorAll('a.span-link').length,
                     ring: !!a && a.matches(':focus-visible'), splitLeft: box.querySelectorAll('.split-line').length }; })()""")
        check(f"[{engine}] keyboard focus survives the reveal (the link was in {copies} pieces while split)", st["onLink"] and st["links"] == 1 and st["splitLeft"] == 0, json.dumps(st))
        pg.goto(BASE + "/tuned/split-react", wait_until="load")
        pg.wait_for_function("document.fonts.status === 'loaded'")
        pg.wait_for_timeout(2600)

        pg.click("#toggle")
        pg.wait_for_timeout(300)
        st = pg.evaluate("document.querySelector('#struct') ? document.querySelector('#struct').textContent : null")
        em = pg.evaluate("!!document.querySelector('#struct em')")
        check(f"[{engine}] a structure change renders without a crash", st and "is on right" in st and em and not errs, json.dumps(st) + (" | " + errs[0] if errs else ""))

        b.close()

print(f"{sum(R)}/{len(R)} passed")
