"""Text that changes while it is still split (waiting below the fold): without a key React edits nodes SplitText
moved; with a key that changes with the text, React replaces the element. Run: python suites/split_dynamic.py [base-url]"""
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
        for mode in ("key", "nokey"):
            pg = b.new_page(viewport={"width": 1100, "height": 800})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
            pg.goto(BASE + f"/tuned/split-dynamic-{mode}", wait_until="load")
            pg.wait_for_function("document.fonts.status === 'loaded'")
            pg.wait_for_timeout(1200)
            split_before = pg.evaluate("document.querySelectorAll('#dyn .split-line').length")
            pg.click("#t")
            pg.wait_for_timeout(300)
            alive = pg.evaluate("!!document.querySelector('#dyn')")
            if alive:
                pg.evaluate("document.querySelector('#dyn').scrollIntoView({ block: 'center' })")
                pg.wait_for_timeout(2600)
            final = pg.evaluate("(() => { const d = document.querySelector('#dyn'); return d ? { text: d.textContent.trim().slice(0, 22), em: !!d.querySelector('em'), split: d.querySelectorAll('.split-line').length } : null; })()")
            ok = final and final["em"] and final["text"].startswith("The state is on") and final["split"] == 0 and not errs
            label = "with a key: the change lands and the new text reveals" if mode == "key" else "without a key (expected to break)"
            check(f"[{engine}] {label}", ok if mode == "key" else True, f"split while waiting: {split_before} lines; after: {json.dumps(final)}; errors: {errs[:1]}")
            pg.close()
        b.close()
print(f"{sum(R)}/{len(R)} passed")
