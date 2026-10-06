"""Build the README's GIFs (GitHub renders GIFs inline everywhere; a committed MP4 doesn't play in a README).
  media/<skill>.gif   cut from the skill's 4K60 stage capture to the moment it acts, with its own palette
  media/hero.gif      the launch film's 15 s loop, whole
  python scripts/make_previews.py <clips-dir> [skill ...]
  python scripts/make_previews.py --hero <loop.mp4>"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "media")

# skill: (capture name, start s, duration s, fps, colours)
CUTS = {
    "split-text-line-reveal": ("split", 0.0, 2.6, 24, 96),
    "list-hover-sliding-fill": ("list", 0.6, 4.4, 24, 96),
    "roll-link-hover": ("roll", 0.4, 4.0, 24, 96),
    "wipe-button": ("wipe", 0.5, 4.1, 24, 96),
    "note-minimap": ("minimap", 0.5, 6.2, 15, 128),
    "cursor-label": ("cursor", 0.6, 4.4, 24, 192),
    "parallax-image": ("parallax", 1.2, 5.0, 15, 128),
    "scroll-color-fill": ("fill", 0.4, 5.0, 24, 96),
    "travelling-indicator": ("travel", 0.4, 6.2, 24, 192),
    "focus-dim": ("focus", 0.6, 5.8, 24, 192),
    "number-roll": ("number", 1.0, 5.8, 24, 96),
    "hover-play": ("play", 0.5, 6.9, 24, 256),
}


def gif(src, dst, fps, width, colours, cut=()):
    vf = (f"fps={fps},scale={width}:-1:flags=lanczos,split[a][b];"
          f"[a]palettegen=max_colors={colours}:stats_mode=diff[p];"
          f"[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *cut, "-i", src, "-vf", vf, "-loop", "0", dst], check=True)
    print(f"{os.path.basename(dst):28s} {os.path.getsize(dst) / 1e6:.2f} MB", flush=True)


os.makedirs(OUT, exist_ok=True)
if sys.argv[1] == "--hero":
    # 960 px for a README column about 830 px wide; 20 fps and 128 colours keep the 15 s loop near 5 MB
    gif(sys.argv[2], os.path.join(OUT, "hero.gif"), 20, 960, 128)
    sys.exit()
CLIPS, ONLY = sys.argv[1], sys.argv[2:]
for skill, (cap, ss, dur, fps, colours) in CUTS.items():
    if ONLY and skill not in ONLY:
        continue
    width = 640 if cap in ("minimap", "parallax") else 800  # scrolled photographs carry the weight
    gif(os.path.join(CLIPS, f"{cap}.mp4"), os.path.join(OUT, f"{skill}.gif"), fps, width, colours,
        ("-ss", str(ss), "-t", str(dur)))
