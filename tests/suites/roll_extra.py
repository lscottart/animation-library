"""Cross-browser stress for the tuned roll link: Chromium, Firefox, WebKit.
Run with the dev or prod server on BASE:  python suites/roll_extra.py [base-url]"""
import json
import sys
from io import BytesIO

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
ROUTE = "/tuned/roll"
R = []


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


YS = "(ls) => ls.map((l) => { const t = getComputedStyle(l).transform; return t === 'none' ? 0 : +t.slice(7, -1).split(',')[5]; })"
EXPECTED = ["Ü", "b", "e", "r", " ", "c", "a", "f", "é", " ", "\U0001F469\U0001F3FD‍\U0001F4BB", " ", "\U0001F1E8\U0001F1ED"]
GHOST_OFF = ".roll-letter::after{visibility:hidden !important}"
UNCLIP = ".roll-window{overflow:visible !important}"


def shot(pg, sel):
    r = pg.evaluate(f"(() => {{ const b = document.querySelector('{sel}').getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; }})()")
    clip = {"x": max(r[0] - 4, 0), "y": max(r[1] - 24, 0), "width": r[2] + 8, "height": r[3] + 48}
    return np.asarray(Image.open(BytesIO(pg.screenshot(clip=clip))).convert("L"), dtype=float)


with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:160]))
        pg.goto(BASE + ROUTE, wait_until="load")
        pg.wait_for_timeout(900)

        exact = pg.get_by_role("link", name="About", exact=True).count()
        it = pg.evaluate("[...document.querySelectorAll('a.roll-link')].map((a) => a.innerText)")
        check(f"[{engine}] one accessible name; innerText is the label", exact == 1 and "About" in it and "Typography, glyphs" in it, json.dumps(it[:3]))

        letters = pg.evaluate("[...document.querySelectorAll('#emoji .roll-letter')].map((l) => l.textContent)")
        check(f"[{engine}] graphemes stay whole: decomposed accent, ZWJ emoji, flag", letters == EXPECTED, json.dumps(letters, ensure_ascii=True))

        # at rest, with the rolling copy hidden vs shown: no pixel of the copy may show
        a1 = shot(pg, "#nav a:nth-child(2)")
        pg.add_style_tag(content=GHOST_OFF)
        pg.wait_for_timeout(80)
        a2 = shot(pg, "#nav a:nth-child(2)")
        peek = float((np.abs(a1 - a2) > 30).mean())
        check(f"[{engine}] at rest the rolling copy is fully hidden", peek == 0.0, f"{peek * 100:.3f}% differ")

        # clipping: with the copy hidden, the windowed text must match the unclipped text exactly
        for sel, name in (("#desc", "descenders (Typography, glyphs)"), ("#emoji", "accent caps and emoji")):
            clipped = shot(pg, sel)
            pg.add_style_tag(content=UNCLIP)
            pg.wait_for_timeout(80)
            free = shot(pg, sel)
            pg.evaluate("document.querySelectorAll('style').forEach((s) => s.textContent.includes('overflow:visible !important') && s.remove())")
            pg.wait_for_timeout(80)
            cut = float((np.abs(clipped - free) > 40).mean())
            check(f"[{engine}] nothing clipped: {name}", cut == 0.0, f"{cut * 100:.3f}% differ")
        pg.evaluate("document.querySelectorAll('style').forEach((s) => s.textContent.includes('visibility:hidden !important') && s.remove())")

        # hover, then off
        about = pg.locator("#nav a").nth(1)
        about.hover()
        pg.wait_for_timeout(700)
        ys = about.locator(".roll-letter").evaluate_all(YS)
        check(f"[{engine}] hover rolls every letter exactly one line up", ys and all(abs(y + 38.4) < 0.6 for y in ys), json.dumps([round(y, 1) for y in ys]))
        emo = pg.locator("#emoji")
        emo.hover()
        pg.wait_for_timeout(900)
        ye = emo.locator(".roll-letter").evaluate_all(YS)
        check(f"[{engine}] the grapheme label rolls whole", ye and all(abs(y + 38.4) < 0.6 for y in ye), json.dumps([round(y, 1) for y in ye]))
        pg.mouse.move(1200, 880)
        pg.wait_for_timeout(900)
        back = about.locator(".roll-letter").evaluate_all(YS) + emo.locator(".roll-letter").evaluate_all(YS)
        check(f"[{engine}] moving off rolls it back", all(abs(y) < 0.01 for y in back), f"max |y| {max(abs(y) for y in back):.2f}")

        # keyboard: Tab in Chromium/Firefox; WebKit skips links on Tab by default, so focus() there
        if engine == "webkit":
            pg.evaluate("document.querySelector('#nav a').focus()")
        else:
            pg.keyboard.press("Tab")
        pg.wait_for_timeout(700)
        fy = pg.evaluate("(() => { const a = document.activeElement; if (!a || !a.matches('a.roll-link')) return null; return [...a.querySelectorAll('.roll-letter')].map((l) => { const t = getComputedStyle(l).transform; return t === 'none' ? 0 : +t.slice(7, -1).split(',')[5]; }); })()")
        check(f"[{engine}] keyboard focus rolls it", fy and all(abs(y + 38.4) < 0.6 for y in fy), json.dumps(fy))
        check(f"[{engine}] no errors, hydration included", not errs, "; ".join(errs[:2]))
        ctx.close()

        # reduced motion: no transform on hover, an underline instead
        ctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        pg = ctx.new_page()
        pg.goto(BASE + ROUTE, wait_until="load")
        pg.wait_for_timeout(600)
        a = pg.locator("#nav a").nth(1)
        a.hover()
        pg.wait_for_timeout(500)
        st = a.evaluate("(a) => ({ t: [...a.querySelectorAll('.roll-letter')].map((l) => getComputedStyle(l).transform), u: getComputedStyle(a).textDecorationLine })")
        check(f"[{engine}] reduced motion: no roll, underline on hover", all(t == "none" for t in st["t"]) and "underline" in st["u"], json.dumps(st))
        ctx.close()

        # touch: Firefox can't emulate a phone in Playwright, so Chromium and WebKit only
        if engine != "firefox":
            ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=3)
            pg = ctx.new_page()
            pg.goto(BASE + ROUTE, wait_until="load")
            pg.wait_for_timeout(700)
            hov = pg.evaluate("matchMedia('(hover: hover)').matches")
            t = pg.locator("a.roll-link").filter(has_text="Tap target").first
            t.tap()
            pg.wait_for_timeout(800)
            ty = t.locator(".roll-letter").evaluate_all(YS)
            check(f"[{engine}] touch: a tap leaves nothing rolled", all(abs(y) < 0.01 for y in ty), f"(hover: hover) = {hov}; max |y| {max(abs(y) for y in ty):.2f}")
            ctx.close()
        b.close()

print(f"{sum(R)}/{len(R)} passed")
