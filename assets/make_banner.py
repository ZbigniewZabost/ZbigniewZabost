#!/usr/bin/env python3
"""Write assets/banner.svg: the GitHub profile banner, in the style of the LinkedIn banner.

Navy gradient, dot grid, Montserrat Light title, Source Code Pro keyword chips, and latency
percentile bands (p50 / p90 / p99, unlabelled) along the bottom.

Two layers, because GitHub shows README images without web fonts:
  * static text layer (background, title, chips, location): rendered at 2x with the real fonts
    by ImageMagick + librsvg, embedded as a JPEG data URI
  * animated vector layer: the site's hexagon emblem rotating, the percentile bands scrolling
    seamlessly like a live dashboard, and a pulsing location dot (SMIL only, no scripts)

Needs ImageMagick with librsvg, Montserrat and Source Code Pro (all on the Fedora laptop).
Usage: python3 assets/make_banner.py
"""
import base64, math, os, subprocess, tempfile

W, H = 1200, 300
OUT = os.path.dirname(os.path.abspath(__file__))
BG_A, BG_B, GRID = '#0b1220', '#121b30', '#1b2740'
PANEL, SLATE, CHIP_INK = '#111a2e', '#2c3b58', '#c3cfe0'
LIGHT, TEAL, BLUE = '#e6ebf3', '#3fd0b0', '#5aa9f0'
SANS, MONO = 'Montserrat', 'Source Code Pro'

TITLE = 'Site Reliability · Platform · Systems'
ROWS = [['AI Agents for Ops', 'Kubernetes', 'AWS · Azure · GCP'],
        ['Terraform', 'CI/CD', 'Observability', 'Incident Response']]
LOCATION = 'Berlin'
X0 = 196                     # left edge of the text block, right of the emblem
CHIP_FONT, CHIP_H, CHIP_PAD, CHIP_GAP = 19, 36, 14, 10
EMBLEM = (104, 112)          # centre of the rotating hexagon
LOC_RIGHT, LOC_Y = 1150, 58  # "● Berlin", top right


def chip_w(s):
    return len(s) * CHIP_FONT * 0.6 + len(s) * 0.5 + 2 * CHIP_PAD   # Source Code Pro advance = 0.6em


def text(x, y, s, size, fill, family, weight=400, anchor='start', spacing=0.5):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing}">{s}</text>')


def static_layer():
    dots = ''.join(f'<circle cx="{x}" cy="{y}" r="1"/>' for x in range(12, W, 24) for y in range(12, H, 24))
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="0.4"><stop offset="0" stop-color="{BG_A}"/><stop offset="1" stop-color="{BG_B}"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="16" fill="url(#bg)"/>', f'<g fill="{GRID}" fill-opacity="0.8">{dots}</g>',
         text(X0, 98, TITLE, 46, LIGHT, SANS, weight=300, spacing=0.3)]
    y = 122
    for row in ROWS:
        x = X0
        for kw in row:
            w = chip_w(kw)
            p.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{CHIP_H}" rx="{CHIP_H / 2}" fill="{PANEL}" stroke="{SLATE}" stroke-width="1.6"/>')
            p.append(text(x + w / 2, y + CHIP_H / 2 + CHIP_FONT * 0.36, kw, CHIP_FONT, CHIP_INK, MONO, anchor='middle'))
            x += w + CHIP_GAP
        y += CHIP_H + 10
    p.append(text(LOC_RIGHT, LOC_Y + 6, LOCATION, 18, TEAL, MONO, anchor='end', spacing=1.0))
    p.append('</svg>')
    return ''.join(p)


def render_png(svg):
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, 'layer.svg'), os.path.join(d, 'layer.jpg')
        open(src, 'w').write(svg)
        # JPEG keeps the 2x text layer small; the layer is fully opaque, and the card clip rounds the corners
        subprocess.run(['magick', '-background', BG_A, '-density', '192', f'rsvg:{src}', '-flatten', '-strip',
                        '-sampling-factor', '4:4:4', '-quality', '90', dst], check=True)
        return open(dst, 'rb').read()


def periodic(n, seed, base, amps):
    """A seamless loop: sums of sines whose periods divide n, so the strip tiles without a seam."""
    return [base + sum(a * math.sin(2 * math.pi * k * i / n + seed * (k + 1)) for k, a in amps) for i in range(n + 1)]


def band_paths():
    n, top, bot = 120, 232, 292
    p99 = periodic(n, 1.3, 0.70, [(2, .07), (5, .04), (11, .02)])
    p90 = periodic(n, 2.1, 0.46, [(2, .05), (4, .03), (9, .015)])
    p50 = periodic(n, 0.7, 0.22, [(3, .03), (7, .015)])
    y = lambda v: bot - v * (bot - top)
    def line(vals, x0):
        return 'M ' + ' L '.join(f'{x0 + W * i / n:.1f},{y(v):.1f}' for i, v in enumerate(vals))
    def area(vals, x0):
        return line(vals, x0) + f' L {x0 + W:.1f},{bot} L {x0:.1f},{bot} Z'
    g = []
    for x0 in (0, W):   # two tiles; the group scrolls left by one tile per cycle
        g += [f'<path d="{area(p99, x0)}" fill="url(#blueArea)"/>', f'<path d="{line(p99, x0)}" fill="none" stroke="{BLUE}" stroke-width="1.6" stroke-opacity="0.85"/>',
              f'<path d="{area(p90, x0)}" fill="url(#tealArea)"/>', f'<path d="{line(p90, x0)}" fill="none" stroke="{TEAL}" stroke-width="1.2" stroke-opacity="0.5"/>',
              f'<path d="{line(p50, x0)}" fill="none" stroke="{TEAL}" stroke-width="2.2"/>']
    return ''.join(g)


def hexpts(r):
    return ' '.join(f'{r * math.cos(math.pi / 6 + i * math.pi / 3):.1f},{r * math.sin(math.pi / 6 + i * math.pi / 3):.1f}' for i in range(6))


def banner():
    png = base64.b64encode(render_png(static_layer())).decode()
    ex, ey = EMBLEM
    dot_x = LOC_RIGHT - len(LOCATION) * 18 * 0.6 - len(LOCATION) * 1.0 - 16
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Site Reliability, Platform, Systems. AI Agents for Ops, Kubernetes, AWS, Azure, GCP, Terraform, CI/CD, Observability, Incident Response. Berlin.">
<defs>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0.12" stop-color="#fff" stop-opacity="0"/><stop offset="0.38" stop-color="#fff" stop-opacity="1"/></linearGradient>
  <mask id="fadeMask"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
  <linearGradient id="tealArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TEAL}" stop-opacity="0.28"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></linearGradient>
  <linearGradient id="blueArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BLUE}" stop-opacity="0.22"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></linearGradient>
</defs>
<g clip-path="url(#card)">
  <image width="{W}" height="{H}" href="data:image/jpeg;base64,{png}" xlink:href="data:image/jpeg;base64,{png}"/>
  <g mask="url(#fadeMask)"><g>{band_paths()}<animateTransform attributeName="transform" type="translate" from="0 0" to="-{W} 0" dur="36s" repeatCount="indefinite"/></g></g>
  <g transform="translate({ex} {ey})">
    <g><polygon points="{hexpts(54)}" fill="none" stroke="{SLATE}" stroke-width="2" stroke-dasharray="6 7"/>
      <circle cx="0" cy="-54" r="5" fill="{BLUE}"/><circle cx="46.8" cy="27" r="5" fill="#f2b44c"/><circle cx="-46.8" cy="27" r="5" fill="#f43f5e"/>
      <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="14s" repeatCount="indefinite"/></g>
    <g><polygon points="{hexpts(34)}" fill="{PANEL}" stroke="{LIGHT}" stroke-width="2"/>
      <animateTransform attributeName="transform" type="scale" values="1;1.07;1" dur="3.2s" repeatCount="indefinite"/></g>
    <polyline points="-22,3 -12,3 -6,-13 0,16 6,-6 12,3 22,3" fill="none" stroke="{TEAL}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="76" stroke-dashoffset="76">
      <animate attributeName="stroke-dashoffset" values="76;0;0;-76" keyTimes="0;.45;.7;1" dur="2.4s" repeatCount="indefinite"/></polyline>
  </g>
  <circle cx="{dot_x:.1f}" cy="{LOC_Y}" r="5" fill="{TEAL}"/>
  <circle cx="{dot_x:.1f}" cy="{LOC_Y}" r="5" fill="none" stroke="{TEAL}" stroke-width="1.6">
    <animate attributeName="r" values="5;13" dur="2.4s" repeatCount="indefinite"/>
    <animate attributeName="stroke-opacity" values="0.7;0" dur="2.4s" repeatCount="indefinite"/></circle>
</g>
</svg>'''


svg = banner()
open(os.path.join(OUT, 'banner.svg'), 'w').write(svg)
print('banner.svg', len(svg) // 1024, 'KB')
