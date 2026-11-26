"""Club Clocks logo set. A clock dial whose hour hand is a flagstick: the clock face meets the 18th green.

Writes: logo-mark.svg (round badge), logo.svg (badge + wordmark, dark ink), logo-light.svg (for dark
backgrounds), icon.svg (home-screen tile), favicon.svg (simplified for 16-32 px).
Lettering is Caladea Bold, the face the clocks print in, converted to outlines.
"""
import math, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

GREEN, BRASS, CREAM, RED, WHITE = "#1E4A3A", "#C2A458", "#F5F0E3", "#B8432F", "#FFFFFF"
FONT = TTFont(os.path.join(os.path.dirname(os.path.abspath(__file__)), "caladea.woff2"))
GS, CMAP, HMTX = FONT.getGlyphSet(), FONT.getBestCmap(), FONT["hmtx"]
UPM = FONT["head"].unitsPerEm
CAP = FONT["OS/2"].sCapHeight or 667


def text_path(s, x, y, cap_px, track=0.0):
    """Outline path for s with its baseline at y and caps cap_px tall; returns (d, width)."""
    k = cap_px / CAP
    pen = SVGPathPen(GS)
    cx = 0.0
    for ch in s:
        gname = CMAP[ord(ch)]
        tp = TransformPen(pen, (k, 0, 0, -k, x + cx, y))
        GS[gname].draw(tp)
        cx += HMTX[gname][0] * k + track * cap_px
    return pen.getCommands(), cx - track * cap_px


def dial(cx, cy, r, ticks=True, detail=True):
    """Cream dial, brass ring, flagstick hour hand at 12 with a red pennant, minute hand at 20 past."""
    ring = r * 0.12
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r - ring / 2:.2f}" fill="{CREAM}" stroke="{BRASS}" stroke-width="{ring:.2f}"/>']
    if ticks:
        for i in range(12):
            a = math.radians(i * 30)
            big = i % 3 == 0
            r0, r1 = r * (0.68 if big else 0.74), r * 0.82
            w = r * (0.055 if big else 0.032)
            if i == 0:
                continue                       # the pennant stands where 12 would be
            out.append(f'<line x1="{cx + r0 * math.sin(a):.2f}" y1="{cy - r0 * math.cos(a):.2f}" '
                       f'x2="{cx + r1 * math.sin(a):.2f}" y2="{cy - r1 * math.cos(a):.2f}" '
                       f'stroke="{GREEN}" stroke-width="{w:.2f}" stroke-linecap="round"/>')
    # minute hand towards 4 (twenty past), drawn first so the flagstick sits on top
    a = math.radians(120); L = r * 0.62; w = r * 0.075
    out.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + L * math.sin(a):.2f}" y2="{cy - L * math.cos(a):.2f}" '
               f'stroke="{GREEN}" stroke-width="{w:.2f}" stroke-linecap="round"/>')
    # flagstick hour hand straight up, pennant flying right
    top = cy - r * 0.70
    out.append(f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{top:.2f}" stroke="{GREEN}" stroke-width="{r * 0.07:.2f}" stroke-linecap="round"/>')
    pw, ph = r * 0.40, r * 0.30
    out.append(f'<path d="M{cx + r * 0.02:.2f} {top:.2f} L{cx + pw:.2f} {top + ph * 0.45:.2f} '
               f'L{cx + r * 0.02:.2f} {top + ph:.2f} Z" fill="{RED}" stroke="{RED}" stroke-width="{r * 0.02:.2f}" stroke-linejoin="round"/>')
    # golf ball hub
    hr = r * 0.13
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{hr:.2f}" fill="{WHITE}" stroke="{GREEN}" stroke-width="{r * 0.03:.2f}"/>')
    if detail:
        for dx, dy in ((-0.35, -0.3), (0.3, -0.35), (0.0, 0.05), (-0.3, 0.38), (0.35, 0.32)):
            out.append(f'<circle cx="{cx + dx * hr:.2f}" cy="{cy + dy * hr:.2f}" r="{hr * 0.13:.2f}" fill="{GREEN}" opacity=".35"/>')
    return "\n".join(out)


def badge(cx, cy, r, detail=True):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{GREEN}"/>\n' + dial(cx, cy, r * 0.80, detail=detail, ticks=True))


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{title}"><title>{title}</title>\n{body}\n</svg>\n')


def main(out):
    os.makedirs(out, exist_ok=True)
    # round badge
    open(f"{out}/logo-mark.svg", "w").write(svg(240, 240, badge(120, 120, 118), "Club Clocks"))
    # home-screen tile: full-bleed square (iOS rounds the corners itself), dial inside the maskable safe zone
    tile = f'<rect width="512" height="512" fill="{GREEN}"/>\n' + dial(256, 256, 190)
    open(f"{out}/icon.svg", "w").write(svg(512, 512, tile, "Club Clocks"))
    # favicon: rounded tile, fewer ticks so it reads at 16 px
    fav = f'<rect width="64" height="64" rx="14" fill="{GREEN}"/>\n' + dial(32, 32, 29.5, ticks=False, detail=False)
    open(f"{out}/favicon.svg", "w").write(svg(64, 64, fav, "Club Clocks"))
    # wordmark lockups
    for name, ink, sub in (("logo", GREEN, BRASS), ("logo-light", CREAM, BRASS)):
        d1, w1 = text_path("CLUB CLOCKS", 0, 0, 78, track=0.10)
        d2, w2 = text_path("BY AFTERNOON GOLF CLUB", 0, 0, 25, track=0.32)
        x0, H = 268, 240
        body = badge(120, 120, 118) + "\n"
        body += f'<path transform="translate({x0} 128)" fill="{ink}" d="{d1}"/>\n'
        body += f'<rect x="{x0}" y="150" width="{w1:.1f}" height="3" fill="{BRASS}"/>\n'
        body += f'<path transform="translate({x0 + (w1 - w2) / 2:.1f} 196)" fill="{sub}" d="{d2}"/>\n'
        W = int(x0 + max(w1, w2) + 12)
        open(f"{out}/{name}.svg", "w").write(svg(W, H, body, "Club Clocks by Afternoon Golf Club"))
    print("written to", out)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "out")
