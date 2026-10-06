"""Edge cases for the split reveal: every case reveals and ends as its original DOM; a resize mid-reveal and before a
below-the-fold reveal both end with exact wrapping; the motion follows power4.out over 1 s. Run: python suites/split_edge.py"""
import json
from playwright.sync_api import sync_playwright
BASE = "http://localhost:3020/tuned/split-edge"
ORIG = """(() => { const W = window; W.__orig = {}; document.addEventListener("readystatechange", () => document.readyState === "interactive" && document.querySelectorAll("[data-split-reveal]").forEach((el) => (W.__orig[el.id] = el.innerHTML))); })();"""
LAY = """(ids) => ids.map((id) => { const el = document.getElementById(id); const ref = el.cloneNode(false); ref.innerHTML = window.__orig[id]; ref.removeAttribute("id");
  Object.assign(ref.style, { position: "absolute", visibility: "hidden", left: "0", top: "0", width: el.getBoundingClientRect().width + "px" }); el.parentElement.appendChild(ref);
  const r = [id, Math.round(el.getBoundingClientRect().height), Math.round(ref.getBoundingClientRect().height), el.innerHTML === window.__orig[id]]; ref.remove(); return r; })"""
R = []
def check(n, ok, d=""):
    R.append(ok); print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)
IDS = ["br", "emoji", "longword", "center", "rtl", "li", "empty"]
for engine in ["chromium", "firefox", "webkit"]:
    with sync_playwright() as p:
        try:
            b = getattr(p, engine).launch(headless=True)
        except Exception as e:
            check(f"[{engine}] launches", False, str(e)[:80]); continue
        ctx = b.new_context(viewport={"width": 1280, "height": 800}); ctx.add_init_script(ORIG)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
        pg.goto(BASE, wait_until="load"); pg.wait_for_timeout(3500)
        lay = pg.evaluate(LAY, IDS)
        bad = [r for r in lay if not r[3] or abs(r[1] - r[2]) > 1]
        check(f"[{engine}] br, emoji, long word, centred, RTL, li and empty all reveal and end as plain text", not bad and not errs, json.dumps(bad or errs)[:300])
        # resize before the below-the-fold paragraph is revealed: it must re-split at the new width, then land as plain text
        pg.set_viewport_size({"width": 700, "height": 800}); pg.wait_for_timeout(600)
        pg.evaluate("document.getElementById('later').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(2800)
        lay = pg.evaluate(LAY, ["later"])
        check(f"[{engine}] resized before its reveal: re-splits, reveals, ends exact", lay[0][3] and abs(lay[0][1] - lay[0][2]) <= 1, json.dumps(lay))
        ctx.close()
        # resize in the middle of a reveal
        ctx = b.new_context(viewport={"width": 1280, "height": 800}); ctx.add_init_script(ORIG)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
        pg.goto(BASE, wait_until="load")
        pg.wait_for_function("document.querySelector('#br .split-line')", timeout=8000); pg.wait_for_timeout(250)
        pg.set_viewport_size({"width": 620, "height": 800}); pg.wait_for_timeout(3000)
        lay = pg.evaluate(LAY, ["br", "center", "longword"])
        bad = [r for r in lay if not r[3] or abs(r[1] - r[2]) > 1]
        check(f"[{engine}] resized mid-reveal: every block still ends as exact plain text", not bad and not errs, json.dumps(bad or errs)[:300])
        ctx.close(); b.close()
# the motion: per frame, line 1's offset against its own clock (the staggered tween's progress x its total duration / one line's duration). The shape must be power4.out,
# progress must advance 1/1000 per ms (1 s). GSAP's powerN is exponent N+1, so power4.out is offset = T(1-p)^5, and the first painted frame may only lose a frame's worth of time
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="chromium")
    pg = b.new_page(viewport={"width": 1280, "height": 800})
    pg.add_init_script("""(() => { const W = window; W.__s = []; const tick = (t) => { const l = document.querySelector('#br .split-line');
      if (l && W.__gsap) { const tw = W.__gsap.getTweensOf(document.querySelectorAll('#br .split-line'))[0]; const m = getComputedStyle(l).transform;
        if (tw) W.__s.push([t, m === 'none' ? 0 : +m.slice(7, -1).split(',')[5], Math.min(1, tw.progress() * tw.duration() / tw.vars.duration), tw.vars.ease]); } requestAnimationFrame(tick); }; requestAnimationFrame(tick); })();""")
    pg.goto(BASE, wait_until="load"); pg.wait_for_timeout(2500)
    smp = pg.evaluate("window.__s"); b.close()
    import statistics
    T = statistics.median(y / (1 - pr) ** 5 for _, y, pr, _ in smp if 0 < pr < 0.85)  # the start offset, read off the curve
    expectT = 50.39 + 2 * 0.3 * 48  # #br: line height (48px x 1.05) + 2 x 0.3em of room
    shape = max(abs(y - T * (1 - pr) ** 5) for _, y, pr, _ in smp if 0 < pr < 1) / T  # GSAP's power4 is the quint: 1 - (1 - u)^5
    run = [(t, pr) for t, _, pr, _ in smp if 0 < pr < 1]
    rate = (run[-1][1] - run[1][1]) / (run[-1][0] - run[1][0]) * 1000 if len(run) > 3 else 0
    lost = run[0][1] * 1000 if run else 999
    check("the motion: power4.out shape, 1 s, offset = line + 0.6em, at most a frame lost at the start", shape < 0.01 and abs(T - expectT) < 1.5 and 0.97 < rate < 1.03 and lost < 45,
          f"start offset {T:.1f}px (expected {expectT:.1f}), shape error {shape * 100:.2f}% of travel, progress rate {rate:.3f}/s, first frame already {lost:.0f} ms in, ease {smp[0][3]}")
print(f"{sum(R)}/{len(R)} passed")
