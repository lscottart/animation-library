"""Release suite for /animations:parallax-image. Chromium, Firefox, WebKit.
Run with the dev or prod server on BASE:  python suites/parallax_extra.py [base-url]"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3020"
ROUTE = "/tuned/parallax"
R = []


def check(n, ok, d=""):
    R.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""), flush=True)


# For frame k: the frame's box, the moving layer's box (transform included), and how much the layer covers.
GEOM = r"""(k) => {
  const media = document.querySelectorAll('.parallax-image__media')[k];
  const layer = media.parentElement, frame = layer.parentElement;
  const f = frame.getBoundingClientRect(), l = layer.getBoundingClientRect();
  return { ft: f.top, fb: f.bottom, fl: f.left, fr: f.right, fh: f.height, lt: l.top, lb: l.bottom, ll: l.left, lr: l.right, scale: l.width / f.width,
           covers: l.top <= f.top + 0.6 && l.bottom >= f.bottom - 0.6 && l.left <= f.left + 0.6 && l.right >= f.right - 0.6 };
}"""


def frame_top(pg, k):
    return pg.evaluate(f"document.querySelectorAll('.parallax-image__media')[{k}].parentElement.parentElement.getBoundingClientRect().top + scrollY")


def at(pg, y, settle=120):
    pg.evaluate(f"window.scrollTo(0, {y})")
    pg.wait_for_timeout(settle)


with sync_playwright() as p:
    for engine in ["chromium", "firefox", "webkit"]:
        b = getattr(p, engine).launch(headless=True)
        for reduced in (False, True):
            ctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce" if reduced else "no-preference")
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:160]))
            pg.goto(BASE + ROUTE, wait_until="load")
            pg.wait_for_timeout(900)
            vh = 900
            tag = f"[{engine}{' reduced' if reduced else ''}]"

            # drift: sample the frame from entering at the bottom to leaving at the top
            t0 = frame_top(pg, 0)
            fh = pg.evaluate(GEOM, 0)["fh"]
            ys = [t0 - vh + fh * 0.1 + i * (vh + fh * 0.8) / 7 for i in range(8)]
            offs, cover = [], True
            for y in ys:
                at(pg, y)
                g = pg.evaluate(GEOM, 0)
                offs.append(g["lt"] - g["ft"])
                cover = cover and g["covers"]
            if not reduced:
                mono = all(offs[i + 1] >= offs[i] - 0.3 for i in range(len(offs) - 1))
                check(f"{tag} drift: the picture moves down through its frame as you scroll, steadily", mono and offs[-1] - offs[0] > fh * 0.08, json.dumps([round(o, 1) for o in offs]))
            else:
                check(f"{tag} drift: no movement", max(offs) - min(offs) < 0.5, json.dumps([round(o, 1) for o in offs]))
            check(f"{tag} drift: the picture always covers the frame (no edge shows)", cover)

            # zoom: 1.45 entering, 1 by the time the frame's centre reaches 55% of the screen
            t1 = frame_top(pg, 1)
            fh1 = pg.evaluate(GEOM, 1)["fh"]
            ys = [t1 - vh + 5, t1 - vh + (vh * 0.45 + fh1 / 2) * 0.5, t1 - vh * 0.55 + fh1 / 2 + 5, t1 - vh * 0.55 + fh1 / 2 + 200]
            sc, cover = [], True
            for y in ys:
                at(pg, y, 1100)  # scrub smooths over 0.6s
                g = pg.evaluate(GEOM, 1)
                sc.append(g["scale"])
                cover = cover and g["covers"]
            if not reduced:
                check(f"{tag} zoom: 1.45 entering, down to 1 at mid-screen, and it stays 1", sc[0] > 1.4 and 1.05 < sc[1] < 1.4 and abs(sc[2] - 1) < 0.01 and abs(sc[3] - 1) < 0.01, json.dumps([round(v, 3) for v in sc]))
            else:
                check(f"{tag} zoom: stays at 1", all(abs(v - 1) < 0.005 for v in sc), json.dumps([round(v, 3) for v in sc]))
            check(f"{tag} zoom: the picture always covers the frame", cover)
            img = pg.evaluate("(() => { const i = document.querySelectorAll('.parallax-image__media')[1].querySelector('img'); const cs = getComputedStyle(i); return [cs.objectFit, i.getBoundingClientRect().width > 0]; })()")
            check(f"{tag} next/image with fill works inside", img == ["cover", True], json.dumps(img))

            # settle: 1.12 before it enters, 1 after, once
            t2 = frame_top(pg, 2)
            at(pg, t2 - vh * 1.6, 300)
            before = pg.evaluate(GEOM, 2)["scale"]
            at(pg, t2 - vh * 0.5, 2400)
            after = pg.evaluate(GEOM, 2)["scale"]
            at(pg, t2 - vh * 1.6, 300)
            at(pg, t2 - vh * 0.5, 400)
            again = pg.evaluate(GEOM, 2)["scale"]
            if not reduced:
                check(f"{tag} settle: 1.12 before, eases to 1 on entry, doesn't replay", abs(before - 1.12) < 0.01 and abs(after - 1) < 0.005 and abs(again - 1) < 0.005, json.dumps([round(before, 3), round(after, 3), round(again, 3)]))
            else:
                check(f"{tag} settle: stays at 1", abs(before - 1) < 0.005 and abs(after - 1) < 0.005, json.dumps([round(before, 3), round(after, 3)]))
            check(f"{tag} no console errors", not errs, json.dumps(errs[:2]))
            ctx.close()
        b.close()

print(f"\n{sum(R)}/{len(R)} passed", flush=True)
