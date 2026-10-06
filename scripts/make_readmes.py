"""Write README.md and components/<skill>/README.md from one table, so the gallery, the folders and the skills agree.
  python scripts/make_readmes.py"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "https://github.com/lscottart/animation-library"

UI = "`components/ui/` (or `src/components/ui/`)"
SKILLS = [
    dict(slug="split-text-line-reveal", name="Split text line reveal",
         line="Each line of a heading rises out of its own mask, staggered, then hands the text back to React.",
         about="Each line of a heading or paragraph rises out of its own mask, staggered, with GSAP's SplitText. It works in Server Components, starts from the very bottom of its rise even on a busy page, and hands the text back to React when it lands, so links and updates inside keep working.",
         example="the hero heading on app/page.tsx", needs="`gsap` 3.13 or later and `@gsap/react`.",
         files=[("SplitReveal.tsx", UI), ("globals.css", "appended to your global stylesheet"), ("layout-head.tsx", "inside `<head>` in the root layout (`pages/_document.tsx` in the Pages Router)")],
         suites="`harness.py split tuned`, `split_react.py`, `split_start.py`, `split_dynamic.py`, `split_edge.py`, `mask_check.py`",
         caption="A project page's opening statement, revealed line by line."),
    dict(slug="list-hover-sliding-fill", name="List hover sliding fill",
         line="A link list whose hover fill slides from row to row like one bar.",
         about="A link list whose hover fill slides from row to row like one bar, after the Obys DES project index. Pure CSS and a Server Component; works with or without Tailwind, and is keyboard and touch safe.",
         example="the project index on the home page", needs="Nothing.",
         files=[("SlidingFillList.tsx", UI), ("SlidingFillList.css", UI + "; in the Pages Router, import it in `pages/_app.tsx`")],
         suites="`harness.py list tuned`, `list_extra.py`", caption="The house index."),
    dict(slug="roll-link-hover", name="Roll link hover",
         line="Letters roll up one line in a 15 ms wave, a dimmer copy rising behind.",
         about="On hover a link's letters roll up one line in a 15 ms left-to-right wave while a dimmer copy rises from below. Pure CSS, server-rendered text, one accessible name, any length.",
         example="the header links", needs="Nothing.",
         files=[("RollLink.tsx", UI), ("RollLink.css", UI + "; in the Pages Router, import it in `pages/_app.tsx`")],
         suites="`harness.py roll tuned`, `roll_extra.py`", caption="A menu at display size."),
    dict(slug="wipe-button", name="Wipe button",
         line="The fill only travels one way: out the top on hover, back in from the bottom.",
         about="The des.obys.agency \"Log In\" button: hover sends the fill out the top, leaving brings it back in from the bottom, and the label crossfades in step. Timing measured frame by frame from a capture (out 221 ms, back 207 ms). Two panels, so it never reverses, however fast you come and go.",
         example="the Book a call button in the footer", needs="`gsap`.",
         files=[("WipeButton.tsx", UI)], suites="`wipe_extra.py`", caption="In, out, and straight back in."),
    dict(slug="note-minimap", name="Note minimap",
         line="A rail of section cards that follows your reading on a soft spring.",
         about="A vertical rail of section cards (thumbnail and title) at the page edge that follows your reading on a soft, underdamped spring, with a viewfinder on the current section. Click a card to glide there. It sleeps when nothing moves.",
         example="the case-study pages in app/work/[slug]/page.tsx", needs="Nothing.",
         files=[("NoteMinimap.tsx", UI), ("NoteMinimap.css", UI + "; in the Pages Router, import it in `pages/_app.tsx`")],
         suites="`minimap_extra.py`", caption="Reading down a note, then a click back to The plan."),
    dict(slug="cursor-label", name="Cursor label",
         line="A word like (View) rolls in at the cursor and trails it a step behind.",
         about="A word like \"(View)\" rolls into a one-line window at the cursor over anything marked `data-cursor-label`, trails the pointer on a soft lag, and rolls out when it leaves. One component for every target; white with a difference blend, so it reads on photos and on paper.",
         example="the project grid: (View project)", needs="`gsap`.",
         files=[("CursorLabel.tsx", UI + ", mounted once in the layout")], suites="`cursor_extra.py`", caption="(View project) across a grid."),
    dict(slug="parallax-image", name="Parallax image",
         line="A picture moves inside a still frame: drift, zoom or settle.",
         about="A photograph moves inside a still frame as the frame crosses the screen, in one of three variants: drift; zoom (1.45 to 1, measured on Telha Clarke); settle (1.12 to 1 over 1.8 s, measured on OH Architecture). Wraps any `img`, `next/image` or `video`, and the picture always covers its frame.",
         example="the project hero images, drift", needs="`gsap` and `@gsap/react`.",
         files=[("ParallaxImage.tsx", UI)], suites="`parallax_extra.py`", caption="Drift, zoom and settle on one page."),
    dict(slug="scroll-color-fill", name="Scroll color fill",
         line="A statement fills from grey to ink, character by character, as you scroll.",
         about="A statement fills from grey to ink, character by character, at the reader's own scroll pace. The characters are split in React on the server, so the sentence is in the HTML, nothing rewrites the DOM, and accents, emoji and flags fill as one piece.",
         example="the studio statement on the about page", needs="`gsap` and `@gsap/react`.",
         files=[("ScrollColorFill.tsx", UI), ("ScrollColorFill.css", UI + "; in the Pages Router, import it in `pages/_app.tsx`")],
         suites="`colorfill_extra.py`", caption="The studio statement."),
    dict(slug="travelling-indicator", name="Travelling indicator",
         line="One highlight travels between items and resizes to each.",
         about="One highlight travels between a nav's items, a set of filters or a toolbar's buttons and resizes to each, instead of every item owning its own hover. An ink block with the text inverting inside it, a hairline underline, or one tooltip that slides between buttons. Right on first paint, keyboard aware.",
         example="the header nav, block", needs="`gsap`.",
         files=[("TravellingIndicator.tsx", UI), ("TravellingIndicator.css", UI + "; in the Pages Router, import it in `pages/_app.tsx`")],
         suites="`travel_extra.py`", caption="The menu block and the image tools."),
    dict(slug="focus-dim", name="Focus dim",
         line="Point at one item and its siblings step back. CSS only.",
         about="Hover or keyboard-focus one item in a group and its siblings step back to a quarter opacity and grey. The group never flashes when the pointer crosses the gap between two items. Pure CSS with `:has()`, a Server Component, no JavaScript.",
         example="the project grid on the home page", needs="Nothing. `:has()` needs Chrome 105, Safari 15.4 or Firefox 121.",
         files=[("FocusDim.tsx", UI), ("FocusDim.css", UI + "; in the Pages Router, import it in `pages/_app.tsx`")],
         suites="`focusdim_extra.py`", caption="Four houses."),
    dict(slug="number-roll", name="Number roll",
         line="Digits roll to a new value, right-most first; symbols stay put.",
         about="Digits roll to a new value like a counter, right-most first, while colons, commas and letters stay put. The value is real text in the page once; the rolling strips are generated content. CSS transitions, no library.",
         example="the local time in the footer", needs="Nothing.",
         files=[("NumberRoll.tsx", UI), ("NumberRoll.css", UI + "; in the Pages Router, import it in `pages/_app.tsx`")],
         suites="`numroll_extra.py`", caption="Last light at each house."),
    dict(slug="hover-play", name="Hover play",
         line="A video card plays on hover and holds its frame when you leave.",
         about="A video card holds its poster until you point at it, then plays; leave and it pauses on the frame it reached, with a hairline along the bottom showing where the loop is. Keyboard focus plays it too, and on touch screens it plays while it's mostly in view. Costs nothing while paused.",
         example="the project grid: each card's walkthrough clip", needs="Nothing.",
         files=[("HoverVideo.tsx", UI)], suites="`hoverplay_extra.py`", caption="Three studies from the shader lab."),
]


def component_readme(s):
    rows = "\n".join(f"| `{f}` | {where} |" for f, where in s["files"])
    return f"""# {s['name']}

<img src="../../media/{s['slug']}.gif" alt="{s['name']}: {s['caption']}" width="100%">

{s['about']}

## With Claude Code

```
/animations:{s['slug']} {s['example']}
```

The skill is [`skills/{s['slug']}.md`](../../skills/{s['slug']}.md). It checks your project first, writes these files where your project keeps components, uses the component where you ask, and runs its own checks.

## Without it

| File | Where it goes |
|---|---|
{rows}

Needs: {s['needs']}

The skill file explains the rest: the props, the values and why they were chosen, and the ways it breaks.

## Tested

{s['suites']} in [`tests/`](../../tests/), on three fresh projects (App Router with Tailwind v4 and v3, Pages Router without Tailwind), in dev and production, in Chromium, Firefox and WebKit.
"""


def cell(s):
    return (f'<td width="50%" valign="top">\n'
            f'<a href="components/{s["slug"]}"><img src="media/{s["slug"]}.gif" alt="{s["name"]}: {s["caption"]}" width="100%"></a>\n'
            f'<br><b><a href="components/{s["slug"]}">{s["name"]}</a></b>\n'
            f'<br>{s["line"]}\n'
            f'</td>')


def main_readme():
    rows = []
    for i in range(0, len(SKILLS), 2):
        rows.append("<tr>\n" + "\n".join(cell(s) for s in SKILLS[i:i + 2]) + "\n</tr>")
    grid = "<table>\n" + "\n".join(rows) + "\n</table>"
    return f"""<img src="media/hero.gif" alt="The animation library: twelve skills running, one after another" width="100%">

# Animation library

Twelve motion skills for [Claude Code](https://claude.com/claude-code). Each one builds a single animation into a Next.js project in one pass: it reads your project first, writes the component where your project keeps components, uses it where you ask, and then runs its own checks.

They're the motion details I reach for on studio sites. None of them is a template. Each is a small primitive that fits many places, and each was applied word for word to three fresh projects and tested in dev and production, in Chromium, Firefox and WebKit, before it was published.

## The skills

{grid}

Every one works with the App Router or the Pages Router, with or without Tailwind, and respects `prefers-reduced-motion`. Click a preview for its files and notes.

## Install

```bash
git clone {REPO}.git
mkdir -p ~/.claude/commands/animations
cp animation-library/skills/*.md ~/.claude/commands/animations/
```

To keep them in one project, copy them into that project's `.claude/commands/animations/` instead. Then, inside a Next.js project, run one and say where it goes:

```
/animations:split-text-line-reveal the hero heading on app/page.tsx
/animations:focus-dim the project grid on the home page
/animations:number-roll the local time in the footer
```

With no instructions, each skill builds a small demo of itself. The skills were tuned on Claude Opus 5.5 at maximum effort and their frontmatter asks for it (`model: claude-opus-5-5`, `effort: max`); edit those two lines to run them on something else.

Not using Claude Code? [`components/`](components/) has the source of every animation, the same code the skills write, with a note in each folder on where the files go.

## How they're tested

A skill ships only when its code, applied verbatim to projects nobody prepared for it, passes every cell of this matrix:

| | Chromium 153 | Firefox 155 | WebKit 26.6 |
|---|---|---|---|
| App Router + Tailwind v4 | dev, production | dev, production | dev, production |
| App Router + Tailwind v3 | dev, production | dev, production | dev, production |
| Pages Router + `src/`, no Tailwind | dev, production | dev, production | dev, production |

Next.js 16.3.8, React 19.2.8, GSAP 3.15, Playwright 1.63. In each cell: a type check, lint, a production build, and the skill's own suite, which measures the motion frame by frame (where the fill is mid-slide, which digit rolls first, whether a paused video still asks for frames).

Then each mechanic a skill claims is broken on purpose, and its check has to fail. Those results, with their numbers, are each skill's "Failure patterns to avoid"; anything that couldn't be measured is labelled as a guard. The suites and fixture pages are in [`tests/`](tests/).

## The repository

```
skills/        the twelve Claude Code skills (copy these into your commands folder)
components/    each animation's source, with a note on where it goes
tests/         the suites, their fixture pages and the runner
media/         the previews
scripts/       rebuilds the previews and these READMEs
```

## License

[MIT](LICENSE). Use them in client work.

Made by Lukas Scott, a designer and developer building websites for architecture studios. [@lscott_art](https://x.com/lscott_art)
"""


for s in SKILLS:
    assert os.path.exists(os.path.join(HERE, "skills", f"{s['slug']}.md")), s["slug"]
    for f, _ in s["files"]:
        assert os.path.exists(os.path.join(HERE, "components", s["slug"], f)), (s["slug"], f)
    open(os.path.join(HERE, "components", s["slug"], "README.md"), "w", encoding="utf-8", newline="\n").write(component_readme(s))
open(os.path.join(HERE, "README.md"), "w", encoding="utf-8", newline="\n").write(main_readme())
print("wrote README.md and", len(SKILLS), "component READMEs")
