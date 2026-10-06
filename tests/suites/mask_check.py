"""For each split element on a page: before its reveal nothing may peek out of the masks (progress 0), and the last
masked frame must match the plain text after the revert (no cut descenders). Run: python suites/mask_check.py <route> <id,id,...>"""
import sys
from io import BytesIO
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

route, ids = sys.argv[1], sys.argv[2].split(",")
ok_all = True
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="chromium", args=["--use-angle=d3d11", "--enable-gpu"])
    for i in ids:
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.goto("http://localhost:3020" + route + f"?only={i}", wait_until="load")
        pg.wait_for_function(f"window.__gsap && document.querySelector('#{i} .split-line')", timeout=10000)
        # take control only once the component has started its reveal, or its deferred play() would undo the seek
        pg.wait_for_function(f"window.__gsap.getTweensOf(document.querySelectorAll('#{i} .split-line')).some((t) => !t.paused())", timeout=10000)
        pg.evaluate(f"document.getElementById('{i}').scrollIntoView({{ block: 'center' }})")
        seek = lambda v: pg.evaluate(f"window.__gsap.getTweensOf(document.querySelectorAll('#{i} .split-line')).forEach((t) => {{ t.pause(); t.progress({v}); }})")
        seek(0); pg.wait_for_timeout(150)
        box = pg.locator(f"#{i}").bounding_box()
        clip = {"x": box["x"], "y": box["y"] - 20, "width": box["width"], "height": box["height"] + 50}
        start = np.asarray(Image.open(BytesIO(pg.screenshot(clip=clip))).convert("L"), dtype=float)
        ink0 = float((start < 128).mean())
        seek(0.9999); pg.wait_for_timeout(150)
        a = np.asarray(Image.open(BytesIO(pg.screenshot(clip=clip))).convert("L"), dtype=float)
        seek(1); pg.wait_for_timeout(250)
        c = np.asarray(Image.open(BytesIO(pg.screenshot(clip=clip))).convert("L"), dtype=float)
        cut = float((np.abs(a - c) > 40).mean())
        ok = ink0 < 0.0002 and cut < 0.0005
        ok_all &= ok
        print(("PASS " if ok else "FAIL ") + f"{i}: ink peeking before the reveal {ink0 * 100:.3f}%, pixels cut at the end {cut * 100:.3f}%", flush=True)
        pg.close()
    b.close()
print("ALL PASS" if ok_all else "SOME FAIL")
