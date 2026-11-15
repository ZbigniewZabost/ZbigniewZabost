#!/usr/bin/env python3
"""Write the animated profile banners (light and dark), in the style of zbigniewzabost.github.io.

A slowly rotating dashed hexagon with a heartbeat line (the site's emblem), and a strip of
hexagon "skill badges" that light up one after another, like the site's career run.
SMIL animation only: no scripts, no external fonts, so it renders inside GitHub's <img>.
"""
import math, os

W, H = 900, 150
BRANCH = ['#3b7bff', '#8b5cf6', '#0ea5c6', '#f59e0b', '#f43f5e']
THEMES = {
    'light': dict(bg='#f5f6fa', ink='#121725', off='#cfd5e1', node='#ffffff'),
    'dark': dict(bg='#0a0d15', ink='#e7ebf4', off='#252e44', node='#0f1626'),
}


def hexpts(cx, cy, r):
    return ' '.join(f'{cx + r * math.cos(math.pi / 6 + i * math.pi / 3):.1f},{cy + r * math.sin(math.pi / 6 + i * math.pi / 3):.1f}' for i in range(6))


def banner(t):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Animated hexagon emblem and a strip of skill badges lighting up">',
           f'<rect width="{W}" height="{H}" rx="14" fill="{t["bg"]}"/>']
    # emblem
    cx, cy = 75, 75
    out.append(f'<g transform="translate({cx} {cy})"><g><polygon points="{hexpts(0, 0, 46)}" fill="none" stroke="{t["off"]}" stroke-width="2" stroke-dasharray="5 6"/>'
               f'<circle cx="0" cy="-46" r="4.5" fill="#3b7bff"/><circle cx="39.8" cy="23" r="4.5" fill="#f59e0b"/><circle cx="-39.8" cy="23" r="4.5" fill="#f43f5e"/>'
               '<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="14s" repeatCount="indefinite"/></g>'
               f'<g><polygon points="{hexpts(0, 0, 30)}" fill="{t["node"]}" stroke="{t["ink"]}" stroke-width="2"/>'
               '<animateTransform attributeName="transform" type="scale" values="1;1.07;1" dur="3.2s" repeatCount="indefinite"/></g>'
               '<polyline points="-19,3 -10,3 -5,-11 0,14 5,-5 10,3 19,3" fill="none" stroke="#0ea5c6" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="66" stroke-dashoffset="66">'
               '<animate attributeName="stroke-dashoffset" values="66;0;0;-66" keyTimes="0;.45;.7;1" dur="2.4s" repeatCount="indefinite"/></polyline></g>')
    # honeycomb strip: cells light up left to right, hold, then reset (8 s cycle)
    cols, rows, r = 17, 3, 19
    n, cycle = 0, 8.0
    for col in range(cols):
        for row in range(rows):
            x = 175 + col * 41 + (20.5 if row % 2 else 0)
            y = 33 + row * 42
            if x > W - 24:
                continue
            c = BRANCH[(col * 3 + row) % 5]
            start = (col * rows + row) / (cols * rows) * 0.55  # lights up during the first 55 % of the cycle
            kt = f'0;{start:.3f};{start + 0.03:.3f};0.92;1'
            out.append(f'<polygon points="{hexpts(x, y, r)}" fill="{t["node"]}" stroke="{t["off"]}" stroke-width="1.4" stroke-dasharray="3 3"/>'
                       f'<polygon points="{hexpts(x, y, r)}" fill="none" stroke="{c}" stroke-width="2" opacity="0">'
                       f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{kt}" dur="{cycle}s" repeatCount="indefinite"/></polygon>')
            n += 1
    out.append('</svg>')
    return ''.join(out), n


here = os.path.dirname(os.path.abspath(__file__))
for name, t in THEMES.items():
    svg, n = banner(t)
    open(os.path.join(here, f'banner-{name}.svg'), 'w').write(svg)
    print(f'banner-{name}.svg', len(svg) // 1024, 'KB,', n, 'cells')
