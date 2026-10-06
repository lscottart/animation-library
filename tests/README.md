# Tests

The release suites for the twelve skills, and the fixture pages they drive. They're Playwright scripts in Python that measure the motion in the page, frame by frame, across Chromium, Firefox and WebKit.

## Run them

1. Make a fresh Next.js app (`npx create-next-app@latest`), then apply the skills you want to test to it, word for word. For the Pages Router, import each skill's CSS in `pages/_app.tsx`, as the skills say.
2. Copy the fixtures in: `fixtures/app/tuned/` → `app/tuned/` (or rewrite them as `pages/tuned/*.tsx`), and `fixtures/public/tuned/` → `public/tuned/`.
3. Install the test tools: `pip install playwright numpy pillow`, then `playwright install`.
4. Run the suites against the app, in dev or after `next build`:

```bash
APP_ROOT=/path/to/your-app python suites/run.py dev  "cursor_extra.py" "focusdim_extra.py"
APP_ROOT=/path/to/your-app python suites/run.py prod "numroll_extra.py"
```

`run.py` serves the app on port 3020, runs each suite, and stops the server. Each suite prints `PASS`/`FAIL` per check and a total.

| Skill | Suites |
|---|---|
| split-text-line-reveal | `harness.py split tuned`, `split_react.py`, `split_start.py`, `split_dynamic.py`, `split_edge.py`, `mask_check.py` |
| list-hover-sliding-fill | `harness.py list tuned`, `list_extra.py` |
| roll-link-hover | `harness.py roll tuned`, `roll_extra.py` |
| wipe-button | `wipe_extra.py` |
| note-minimap | `minimap_extra.py` |
| cursor-label | `cursor_extra.py` |
| parallax-image | `parallax_extra.py` |
| scroll-color-fill | `colorfill_extra.py` |
| travelling-indicator | `travel_extra.py` |
| focus-dim | `focusdim_extra.py` |
| number-roll | `numroll_extra.py` |
| hover-play | `hoverplay_extra.py` |

## Notes from the rig

- In Firefox, a scripted `.focus()` after a mouse click doesn't count as keyboard focus. The keyboard checks press real Tab keys in Chromium and Firefox. In WebKit, where Tab skips links, they use a key press followed by a scripted focus.
- The Pages Router's dev server hides `body` until its CSS is injected. Checks on the first frames only judge frames that were painted.
- Playwright's desktop browsers allow unmuted autoplay, so hover-play's `muted` requirement is only measurable under mobile emulation.
