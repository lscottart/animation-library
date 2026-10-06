"""Stress harness for the animation skills (split text line reveal, list hover sliding fill, roll link hover).
The same behavioural checks grade any implementation: point a suite at a route and its selectors.
Needs the app served on :3020 (suites/run.py does that). Run: python suites/harness.py [split|list|roll|all] [baseline|tuned]"""
import json, sys, time, urllib.request
from io import BytesIO
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

BASE = "http://localhost:3020"
GPU = ["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"]
R = []


def check(name, ok, detail=""):
    R.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""), flush=True)


def lum(png):
    return float(np.asarray(Image.open(BytesIO(png)).convert("L"), dtype=float).mean())


# ---------------------------------------------------------------- split text
# Per frame from the first: is the hero's text plainly showing (visible, nothing moved yet)? And when does
# anything inside it first move? Text plainly showing before the reveal starts is the flash.
SPLIT_INIT = r"""
(() => {
  const W = window; W.__frames = []; W.__orig = {}; W.__errs = []; W.__cls = 0;
  try { new PerformanceObserver((l) => l.getEntries().forEach((e) => { if (!e.hadRecentInput) W.__cls += e.value; })).observe({ type: "layout-shift", buffered: true }); } catch (e) {}
  addEventListener("error", (e) => W.__errs.push(String(e.message)));
  const moved = (el) => [...el.querySelectorAll("*")].some((n) => { const t = getComputedStyle(n).transform; return t && t !== "none" && t !== "matrix(1, 0, 0, 1, 0, 0)"; });
  const shown = (el) => { const cs = getComputedStyle(el); return cs.visibility !== "hidden" && +cs.opacity > 0.01; };
  document.addEventListener("readystatechange", () => { if (document.readyState !== "interactive") return;
    for (const id of ["hero", "p1", "nested", "below"]) { const el = document.getElementById(id); if (el) W.__orig[id] = el.innerHTML; }
  });
  const tick = (t) => {
    const h = document.getElementById("hero");
    if (h) W.__frames.push({ t: Math.round(t), shown: shown(h), moved: moved(h) });
    if (t < 6000) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
})();
"""


def suite_split(route, line_sel, churn_route, server_route=None):
    print(f"\n=== split text: {route}", flush=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, channel="chromium", args=GPU)
        if server_route:
            pg = b.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
            pg.goto(BASE + server_route, wait_until="load"); pg.wait_for_timeout(2500)
            ok = not errs and pg.evaluate("!!document.getElementById('hero')")
            check("works from a Server Component page (the App Router default)", ok, "; ".join(errs[:1]))
            pg.close()
        ctx = b.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_init_script(SPLIT_INIT)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        pg.goto(BASE + route, wait_until="commit"); pg.wait_for_timeout(4500)
        fr = pg.evaluate("window.__frames")
        first_move = next((f["t"] for f in fr if f["moved"]), None)
        flash = [f for f in fr if f["shown"] and not f["moved"] and (first_move is None or f["t"] < first_move)]
        check("no flash: the text never shows plainly before its reveal", len(flash) == 0, f"{len(flash)} frames ({(flash[-1]['t'] - flash[0]['t']) if flash else 0} ms) shown unsplit before the reveal")
        nested = pg.evaluate(f"document.querySelectorAll('{line_sel} {line_sel}').length")
        check("split once (StrictMode mounts twice in dev)", nested == 0, f"{nested} lines nested inside lines")
        done = pg.evaluate("(() => { const h = document.getElementById('hero'); return [...h.querySelectorAll('*')].every((n) => { const t = getComputedStyle(n).transform; return !t || t === 'none' || t === 'matrix(1, 0, 0, 1, 0, 0)'; }); })()")
        check("the hero's reveal completes", done)
        cls = pg.evaluate("window.__cls")
        check("splitting causes no layout shift (CLS)", cls < 0.001, f"CLS {cls:.4f}")
        same = pg.evaluate("document.getElementById('hero').innerHTML === window.__orig.hero")
        check("after the reveal the text is its original DOM again (reverted)", same)
        # the layout after a resize matches the same text unsplit
        pg.set_viewport_size({"width": 720, "height": 800}); pg.wait_for_timeout(900)
        lay = pg.evaluate("""(() => { const out = {}; for (const id of ['hero', 'p1', 'nested']) { const el = document.getElementById(id);
            const ref = el.cloneNode(false); ref.innerHTML = window.__orig[id]; ref.removeAttribute('id');
            Object.assign(ref.style, { position: 'absolute', visibility: 'hidden', left: '0', top: '0', width: el.getBoundingClientRect().width + 'px' });
            el.parentElement.appendChild(ref); out[id] = [Math.round(el.getBoundingClientRect().height), Math.round(ref.getBoundingClientRect().height), el.scrollWidth > el.clientWidth + 1]; ref.remove(); } return out; })()""")
        bad = {k: v for k, v in lay.items() if abs(v[0] - v[1]) > 1 or v[2]}
        check("after a resize the text wraps exactly like the unsplit text", not bad, json.dumps(lay))
        pg.set_viewport_size({"width": 1280, "height": 800}); pg.wait_for_timeout(500)
        links = pg.evaluate("[...document.querySelectorAll('#nested a')].map((a) => a.textContent)")
        check("a link inside the text survives whole", links == ["a link that spans words"], json.dumps(links))
        below_before = pg.evaluate("(() => { const el = document.getElementById('below'); const r = el.getBoundingClientRect(); return { top: Math.round(r.top), shownPlain: getComputedStyle(el).visibility !== 'hidden' && ![...el.querySelectorAll('*')].some((n) => getComputedStyle(n).transform !== 'none') } })()")
        pg.evaluate("document.getElementById('below').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(2600)
        below_after = pg.evaluate("document.getElementById('below').innerHTML === window.__orig.below || [...document.getElementById('below').querySelectorAll('*')].every((n) => ['none', 'matrix(1, 0, 0, 1, 0, 0)'].includes(getComputedStyle(n).transform))")
        check("below the fold it waits, then reveals when scrolled to", below_before["top"] > 800 and not below_before["shownPlain"] and below_after, json.dumps(below_before))
        check("no page errors", not errs and not pg.evaluate("window.__errs.length"), "; ".join(errs[:2]))
        ctx.close()
        # descenders at the end of the reveal: the masked state just before the revert must match the plain text
        pg2 = ctx.new_page() if False else None
        dpg = b.new_page(viewport={"width": 1280, "height": 800})
        dpg.goto(BASE + route, wait_until="load")
        try:
            dpg.wait_for_function(f"window.__gsap && document.querySelector('#hero {line_sel}')", timeout=8000)
            dpg.evaluate(f"(() => {{ const ls = document.querySelectorAll('#hero {line_sel}'); const tw = window.__gsap.getTweensOf(ls); tw.forEach((t) => {{ t.pause(); t.progress(0.9999); }}); }})()")
            dpg.wait_for_timeout(200)
            box = dpg.locator("#hero").bounding_box()
            clip = {"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"] + 30}
            a = np.asarray(Image.open(BytesIO(dpg.screenshot(clip=clip))).convert("L"), dtype=float)
            dpg.evaluate(f"(() => {{ const ls = document.querySelectorAll('#hero {line_sel}'); window.__gsap.getTweensOf(ls).forEach((t) => t.progress(1)); }})()")
            dpg.wait_for_timeout(300)
            c = np.asarray(Image.open(BytesIO(dpg.screenshot(clip=clip))).convert("L"), dtype=float)
            diff = np.abs(a - c); frac = float((diff > 40).mean())
            check("descenders aren't cut by the masks (the last masked frame matches the plain text)", frac < 0.0005, f"{frac * 100:.3f}% of pixels differ")
        except Exception as ex:
            check("descenders aren't cut by the masks (the last masked frame matches the plain text)", False, f"couldn't seek the tween: {str(ex)[:80]}")
        dpg.close()
        # reduced motion: the text is simply there
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
        ctx.add_init_script(SPLIT_INIT)
        pg = ctx.new_page(); pg.goto(BASE + route, wait_until="commit"); pg.wait_for_timeout(2500)
        fr = pg.evaluate("window.__frames")
        moved = [f for f in fr if f["moved"]]
        check("reduced motion: no movement, the text is just there", not moved and fr and fr[-1]["shown"], f"{len(moved)} frames with motion")
        ctx.close()
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, java_script_enabled=False)
        pg = ctx.new_page(); pg.goto(BASE + route, wait_until="load"); pg.wait_for_timeout(500)
        vis = pg.evaluate("getComputedStyle(document.getElementById('hero')).visibility") if False else pg.locator("#hero").is_visible()
        check("with JavaScript off the text is visible", vis)
        ctx.close()
        # a web font that arrives late: the lines must be the final font's lines
        ctx = b.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_init_script(SPLIT_INIT)
        def slow(route_):
            time.sleep(1.2); route_.continue_()
        ctx.route("**/*.woff2", slow)
        pg = ctx.new_page(); pg.goto(BASE + route, wait_until="commit"); pg.wait_for_timeout(5000)
        lay = pg.evaluate("""(() => { const out = {}; for (const id of ['hero', 'p1']) { const el = document.getElementById(id);
            const ref = el.cloneNode(false); ref.innerHTML = window.__orig[id]; ref.removeAttribute('id');
            Object.assign(ref.style, { position: 'absolute', visibility: 'hidden', left: '0', top: '0', width: el.getBoundingClientRect().width + 'px' });
            el.parentElement.appendChild(ref); out[id] = [Math.round(el.getBoundingClientRect().height), Math.round(ref.getBoundingClientRect().height)]; ref.remove(); } return out; })()""")
        bad = {k: v for k, v in lay.items() if abs(v[0] - v[1]) > 1}
        check("a late web font: the lines are the final font's lines", not bad, json.dumps(lay))
        ctx.unroute_all(behavior="ignoreErrors"); ctx.close()
        # churn: remount below-the-fold copies ten times; scroll triggers must not pile up
        ctx = b.new_context(viewport={"width": 1280, "height": 800})
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(BASE + churn_route, wait_until="load"); pg.wait_for_timeout(2500)
        base = pg.evaluate("window.__ST ? window.__ST.getAll().length : -1")
        for _ in range(10):
            pg.click("#remount"); pg.wait_for_timeout(250)
        pg.wait_for_timeout(2500)
        after = pg.evaluate("window.__ST ? window.__ST.getAll().length : -1")
        pg.click("#toggle"); pg.wait_for_timeout(1500)
        gone = pg.evaluate("window.__ST ? window.__ST.getAll().length : -1")
        nested = pg.evaluate(f"document.querySelectorAll('{line_sel} {line_sel}').length")
        check("ten remounts don't pile up scroll triggers, and unmounting frees them", after == base and gone == 0 and nested == 0 and not errs, f"live triggers: {base} at start, {after} after 10 remounts, {gone} after unmount; nested lines {nested}; errors {errs[:1]}")
        ctx.close(); b.close()


# ---------------------------------------------------------------- sliding fill list
def suite_list(route, row_sel, fill_sel, text_sel, coloured_route=None):
    print(f"\n=== list hover sliding fill: {route}", flush=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, channel="chromium", args=GPU)
        for label, r in [("on the page", route)] + ([("on a coloured section", coloured_route)] if coloured_route else []):
            ctx = b.new_context(viewport={"width": 1280, "height": 800})
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(BASE + r, wait_until="load"); pg.wait_for_timeout(1200)
            rows = pg.locator(row_sel)
            box = rows.nth(0).bounding_box()
            clip = {"x": box["x"] + 4, "y": box["y"] + 4, "width": box["width"] - 8, "height": box["height"] - 8}
            before = lum(pg.screenshot(clip=clip))
            rows.nth(0).hover(); pg.wait_for_timeout(800)
            after = lum(pg.screenshot(clip=clip))
            check(f"{label}: hovering fills the row solid", abs(after - before) > 60, f"row luminance {before:.0f} -> {after:.0f}")
            # the slide: leaving row 1 for row 2, row 1 collapses toward its bottom while row 2 grows from its top
            rows.nth(1).hover(); pg.wait_for_timeout(150)
            st = pg.evaluate(f"""[0, 1].map((i) => {{ const f = document.querySelectorAll('{row_sel}')[i].querySelector('{fill_sel}'); const cs = getComputedStyle(f);
                return {{ origin: cs.transformOrigin, t: cs.transform, scale: cs.scale }}; }})""")
            def sy(s):
                if s["scale"] and s["scale"] != "none":
                    parts = s["scale"].split(); return float(parts[-1])
                if s["t"].startswith("matrix("):
                    return float(s["t"][7:-1].split(",")[3])
                return 1.0
            o0, o1 = st[0]["origin"].split()[1], st[1]["origin"].split()[1]
            h = box["height"]
            slide = abs(float(o0.rstrip("px")) - h) < 2 and abs(float(o1.rstrip("px"))) < 2 and 0 < sy(st[0]) < 1 and 0 < sy(st[1]) < 1
            check(f"{label}: moving down, one bar slides (row 1 shrinks to its bottom as row 2 grows from its top)", slide, json.dumps(st))
            pg.mouse.move(5, 5); pg.wait_for_timeout(800)
            # keyboard: focus fills the row too
            pg.keyboard.press("Tab")
            for _ in range(6):
                if pg.evaluate(f"document.activeElement?.matches('{row_sel}')"):
                    break
                pg.keyboard.press("Tab")
            pg.wait_for_timeout(800)
            focused = pg.evaluate(f"document.activeElement?.matches('{row_sel}')")
            fs = pg.evaluate(f"(() => {{ const a = document.activeElement; const f = a?.querySelector('{fill_sel}'); if (!f) return null; const cs = getComputedStyle(f); return cs.scale !== 'none' ? cs.scale : cs.transform; }})()")
            fval = 0.0
            if fs:
                fval = float(fs.split()[-1]) if not fs.startswith("matrix") else float(fs[7:-1].split(",")[3])
            check(f"{label}: keyboard focus fills the row too", focused and fval > 0.95, f"focused {focused}, fill {fs}")
            check(f"{label}: no page errors", not errs, "; ".join(errs[:2]))
            ctx.close()
        # touch: a tap must not leave a row stuck filled
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=3)
        pg = ctx.new_page(); pg.goto(BASE + (coloured_route or route), wait_until="load"); pg.wait_for_timeout(1000)
        rows = pg.locator(row_sel)
        rows.nth(0).tap(); pg.wait_for_timeout(900)
        fs = pg.evaluate(f"(() => {{ const f = document.querySelectorAll('{row_sel}')[0]?.querySelector('{fill_sel}'); if (!f) return null; const cs = getComputedStyle(f); return cs.scale !== 'none' ? cs.scale : cs.transform; }})()")
        stuck = fs not in (None, "none") and (float(fs.split()[-1]) if not fs.startswith("matrix") else float(fs[7:-1].split(",")[3])) > 0.05
        check("touch: a tap doesn't leave the row stuck filled", not stuck, f"fill after tap: {fs}")
        ctx.close(); b.close()


# ---------------------------------------------------------------- roll link
def suite_roll(route, link_sel, letter_sel, long_text, tap_text, copies=2, ghost_hide_css=None, window_sel=None):
    print(f"\n=== roll link hover: {route}", flush=True)
    html = urllib.request.urlopen(BASE + route).read().decode("utf8")
    import re
    anchors = re.findall(r"<a[^>]*>(.*?)</a>", html, re.S)
    texts = [re.sub(r"<[^>]+>", "", a).replace("&nbsp;", " ").replace("\xa0", " ") for a in anchors]
    check("the server HTML carries each link's text (no empty links before hydration)", any("About" in t for t in texts) and any(long_text.split()[0] in t for t in texts), json.dumps(texts[:3]))
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, channel="chromium", args=GPU)
        ctx = b.new_context(viewport={"width": 1280, "height": 800})
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        pg.goto(BASE + route, wait_until="load"); pg.wait_for_timeout(1200)
        exact = pg.get_by_role("link", name="About", exact=True).count()
        names = pg.evaluate(f"[...document.querySelectorAll('{link_sel}')].slice(0, 2).map((a) => a.innerText.replace(/\\s+/g, ' '))")
        check("screen readers hear the label once ('About', not 'AboutAbout')", exact == 1, f"exact-name matches {exact}; innerText {json.dumps(names)}")
        it = pg.evaluate(f"[...document.querySelectorAll('{link_sel}')].find((x) => x.textContent.includes('About')).innerText")
        check("copied text and innerText read the label ('About', not one letter per line)", it == "About", json.dumps(it))
        # rest: the second copy is fully hidden below the window
        if ghost_hide_css:
            ab = pg.locator(link_sel).filter(has_text="About").first.bounding_box()
            clip = {"x": ab["x"] - 2, "y": ab["y"] - 2, "width": ab["width"] + 4, "height": ab["height"] + 4}
            with_ghost = np.asarray(Image.open(BytesIO(pg.screenshot(clip=clip))).convert("L"), dtype=float)
            pg.add_style_tag(content=ghost_hide_css); pg.wait_for_timeout(100)
            no_ghost = np.asarray(Image.open(BytesIO(pg.screenshot(clip=clip))).convert("L"), dtype=float)
            pg.evaluate("document.querySelectorAll('style').forEach((st) => st.textContent.includes('roll-ghost-test') && st.remove())")
            peek = float((np.abs(with_ghost - no_ghost) > 30).mean())
            check("at rest no part of the rolling copy shows", peek == 0.0, f"{peek * 100:.3f}% of pixels differ with the copy hidden")
            # clipping: a label full of descenders must keep clear of the window's bottom edge
            wb = pg.evaluate(f"(() => {{ const w = document.querySelector('#desc {window_sel}'); const r = w.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }})()")
            win = np.asarray(Image.open(BytesIO(pg.screenshot(clip={"x": wb[0], "y": wb[1], "width": wb[2], "height": wb[3]}))).convert("L"), dtype=float)
            edge_ink = float((win[-1:, :] < 128).mean())
            check("descenders aren't clipped by the window (no ink on its bottom edge)", edge_ink < 0.01, f"{edge_ink * 100:.1f}% of the bottom row is ink")
        else:
            rest = pg.evaluate(f"""(() => {{ const a = [...document.querySelectorAll('{link_sel}')].find((x) => x.textContent.includes('About')); const ls = a.querySelectorAll('{letter_sel}');
                const win = ls[0].parentElement.parentElement.getBoundingClientRect(); const half = ls.length / 2; const ghost = ls[half].getBoundingClientRect();
                return {{ winBottom: win.bottom, ghostTop: ghost.top }}; }})()""")
            check("at rest the second copy sits wholly below the window", rest["ghostTop"] >= rest["winBottom"] - 0.5, json.dumps(rest))
        link = pg.locator(link_sel).filter(has_text="About").first
        link.hover(); pg.wait_for_timeout(700)
        rolled = pg.evaluate(f"""(() => {{ const a = [...document.querySelectorAll('{link_sel}')].find((x) => x.textContent.includes('About')); const ls = [...a.querySelectorAll('{letter_sel}')];
            return ls.map((l) => {{ const t = getComputedStyle(l).transform; return t === 'none' ? 0 : +t.slice(7, -1).split(',')[5]; }}); }})()""")
        check("hovering rolls every letter up one line", rolled and all(v < -1 for v in rolled), json.dumps([round(v, 1) for v in rolled]))
        delays = pg.evaluate(f"""(() => {{ const a = [...document.querySelectorAll('{link_sel}')].find((x) => x.textContent.replace(/\\s/g, '').includes('{long_text.replace(' ', '')[:12]}'));
            const ls = [...a.querySelectorAll('{letter_sel}')]; const n = ls.length / {copies}; return ls.slice(0, n).map((l) => parseFloat(getComputedStyle(l).transitionDelay) * 1000); }})()""")
        mono = all(b2 > a2 for a2, b2 in zip(delays, delays[1:]))
        check(f"the wave reaches every letter of a {len(long_text)}-character label", mono, f"delays (ms) at letters 1, 20, 21, last: {[round(delays[i]) for i in (0, 19, 20, -1)] if len(delays) > 20 else delays}")
        pg.mouse.move(5, 5); pg.wait_for_timeout(700)
        pg.keyboard.press("Tab"); pg.wait_for_timeout(700)
        foc = pg.evaluate(f"""(() => {{ const a = document.activeElement; if (!a || !a.matches('{link_sel}')) return null; const l = a.querySelector('{letter_sel}'); const t = getComputedStyle(l).transform; return t === 'none' ? 0 : +t.slice(7, -1).split(',')[5]; }})()""")
        check("keyboard focus rolls it too", foc is not None and foc < -1, f"first letter y {foc}")
        check("no page errors (hydration included)", not errs, "; ".join(errs[:2]))
        ctx.close()
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
        pg = ctx.new_page(); pg.goto(BASE + route, wait_until="load"); pg.wait_for_timeout(800)
        dur = pg.evaluate(f"getComputedStyle(document.querySelector('{link_sel} {letter_sel}')).transitionDuration")
        check("reduced motion: no rolling motion", dur in ("0s", "0.001s", "1e-05s") or dur.startswith("0s"), f"transition {dur}")
        ctx.close()
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=3)
        pg = ctx.new_page(); pg.goto(BASE + route, wait_until="load"); pg.wait_for_timeout(800)
        pg.locator(link_sel).filter(has_text=tap_text).first.tap(); pg.wait_for_timeout(800)
        y = pg.evaluate(f"""(() => {{ const a = [...document.querySelectorAll('{link_sel}')].find((x) => x.textContent.replace(/\u00a0/g, ' ').includes('{tap_text}')); const t = getComputedStyle(a.querySelector('{letter_sel}')).transform; return t === 'none' ? 0 : +t.slice(7, -1).split(',')[5]; }})()""")
        check("touch: a tap doesn't leave the label stuck rolled", abs(y) < 0.5, f"first letter y after tap {y}")
        ctx.close(); b.close()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    impl = sys.argv[2] if len(sys.argv) > 2 else "baseline"
    if impl == "baseline":
        if which in ("split", "all"):
            suite_split("/baseline/split-client", ".copy-line", "/baseline/split-churn", "/baseline/split")
        if which in ("list", "all"):
            suite_list("/baseline/list", "ul a", ":scope > span:first-child", "span:nth-child(2)", "/baseline/list-css")
        if which in ("roll", "all"):
            suite_roll("/baseline/roll", "a.roll-link", ".roll-letter", "A much longer link label of thirty characters", "Tap target")
    else:
        if which in ("split", "all"):
            suite_split("/tuned/split-client", ".split-line", "/tuned/split-churn", "/tuned/split")
        if which in ("list", "all"):
            suite_list("/tuned/list", "a.sfl-row", ".sfl-fill", ".sfl-label", "/tuned/list-coloured")
        if which in ("roll", "all"):
            suite_roll("/tuned/roll", "a.roll-link", ".roll-letter", "A much longer link label of thirty characters", "Tap target", copies=1, ghost_hide_css=".roll-letter::after{visibility:hidden !important} /* roll-ghost-test */", window_sel=".roll-window")
    print(f"\n{sum(ok for _, ok in R)}/{len(R)} passed", flush=True)
