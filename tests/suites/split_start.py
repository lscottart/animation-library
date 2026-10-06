"""A load reveal must start from its first frame even when the main thread is blocked right after the split.
Measures how far into the motion the first moving frame already is, with 0 and 300 ms of blocking, and that
a delay is still honoured. Run: python suites/split_start.py [base-url]"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
R = []


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


# per frame: line 1's progress on its own clock, and the time since the split
SAMPLER = """(() => { const W = window; W.__s = []; W.__t0 = null;
  const tick = (t) => { const l = document.querySelector('#br .split-line');
    if (l && W.__t0 === null) W.__t0 = t;
    if (l && W.__gsap) { const tw = W.__gsap.getTweensOf(document.querySelectorAll('#br .split-line'))[0];
      if (tw) W.__s.push([t - W.__t0, Math.min(1, tw.time() / tw.vars.duration)]); }
    requestAnimationFrame(tick); };
  requestAnimationFrame(tick); })();"""


def first_frame(pg, query):
    pg.goto(BASE + "/tuned/split-busy" + query, wait_until="load")
    pg.wait_for_timeout(2600)
    s = pg.evaluate("window.__s")
    moving = [(t, p) for t, p in s if p > 0]
    return (moving[0][1] * 1000, moving[0][0]) if moving else (None, None)


with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_init_script(SAMPLER)
        pg = ctx.new_page()
        for busy in (0, 300):
            lost, _ = first_frame(pg, f"?busy={busy}")
            check(f"[{engine}] main thread blocked {busy} ms after the split: the first moving frame is at most a frame in",
                  lost is not None and lost < 34, f"first moving frame already {lost:.0f} ms into the motion" if lost is not None else "no motion")
        # a delay still holds: the first moving frame comes ~400 ms after the split, and starts near zero
        lost, at = first_frame(pg, "?busy=300&delay=0.4")
        check(f"[{engine}] with delay 0.4 and 300 ms blocked: waits the delay, then starts from its first frame",
              lost is not None and lost < 34 and at is not None and at >= 380, f"starts {at:.0f} ms after the split, {lost:.0f} ms into the motion" if lost is not None else "no motion")
        b.close()

print(f"{sum(R)}/{len(R)} passed")
