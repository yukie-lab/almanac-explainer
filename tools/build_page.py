"""Build index.html from tools/page.html: draw the figures, write the video transcript, fill the placeholders.

Usage: python tools/build_page.py
Reads tools/page.html, tools/narration.json and assets/video/chapters.json. Writes index.html at the site root.
Every figure has its English and Japanese labels side by side; the page shows one language at a time.
The numbers in the figures are the paper's (Maeda 2026, v0.4); the drawings in Figures 1 to 3 are illustrations.
"""
import html
import json
import math
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
W = 640  # width of every figure in SVG units


def esc(s):
    return html.escape(s, quote=True)


def sub90(s):
    """Write r₉₀ with a real subscript in HTML text."""
    return s.replace("r₉₀", "r<sub>90</sub>")


def r90(rest="", d=3.5):
    """r₉₀ inside SVG text, followed by the rest of the label on the normal baseline."""
    return f'r<tspan dy="{d}" font-size="78%">90</tspan><tspan dy="{-d}">{rest}</tspan>'


def t2(x, y, en, ja, cls="", anchor="start"):
    """One label in two languages: two text elements at the same place."""
    a = "" if anchor == "start" else f' text-anchor="{anchor}"'
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}"{a}{c} data-l="en" lang="en">{en}</text>'
            f'<text x="{x:.1f}" y="{y:.1f}"{a}{c} data-l="ja" lang="ja">{ja}</text>')


def tip(en, ja):
    """Hover text. site.js swaps it when the language changes."""
    return f'<title data-en="{esc(en)}" data-ja="{esc(ja)}">{esc(en)}</title>'


def figure(num, h, body, cap_en, cap_ja, aria_en, aria_ja):
    return (f'<figure class="fig">\n<div class="fig-scroll"><svg viewBox="0 0 {W} {h}" role="img" '
            f'aria-label="{esc(aria_en)}" data-aria-en="{esc(aria_en)}" data-aria-ja="{esc(aria_ja)}">'
            f'{body}</svg></div>\n<figcaption><span data-l="en" lang="en"><span class="fignum">Figure {num}.</span>'
            f'{sub90(cap_en)}</span><span data-l="ja" lang="ja"><span class="fignum">図 {num}</span>'
            f'{sub90(cap_ja)}</span></figcaption>\n</figure>')


def fig_trip():
    """Figure 1: the trip from the Sun to Proxima, not to scale."""
    y, sx, px = 104, 52, 540
    s = []
    # distance bar above the path
    s.append(f'<path class="dim" d="M{sx},{y - 50} v-8 M{sx},{y - 54} H{px} M{px},{y - 50} v-8"/>')
    s.append(t2((sx + px) / 2, y - 62, "about 4.2 light-years", "約 4.2 光年", "ink", "middle"))
    # the probe's path, broken in the middle (not to scale)
    bx = 330
    s.append(f'<path class="path" d="M{sx + 16},{y} H{bx - 8} M{bx + 8},{y} H{px - 58}"/>')
    s.append(f'<path class="dim" d="M{bx - 11},{y + 9} l6,-18 M{bx + 5},{y + 9} l6,-18"/>')
    s.append(f'<path class="ink-fill" d="M{px - 66},{y - 6} l12,6 l-12,6 z"/>')
    s.append(f'<path class="ink-fill" d="M164,{y - 7} l15,7 l-15,7 z"/>')
    s.append(t2(171, y - 16, "probe", "探査機", "", "middle"))
    s.append(t2(bx, y + 36, "more than 20 years at 0.2c, more than 40 years at 0.1c",
                "0.2c で 20 年以上、0.1c で 40 年以上", "", "middle"))
    # the Sun
    s.append(f'<circle class="sun" cx="{sx}" cy="{y}" r="11"/>')
    s.append(t2(sx, y + 34, "Sun", "太陽", "ink", "middle"))
    # Proxima, the orbit of b, and the planet
    s.append(f'<circle class="orbit" cx="{px}" cy="{y}" r="44"/>')
    s.append(f'<circle class="star" cx="{px}" cy="{y}" r="9"/>')
    a = math.radians(-145)
    bxp, byp = px + 44 * math.cos(a), y + 44 * math.sin(a)
    s.append(f'<circle class="planet dot" cx="{bxp:.1f}" cy="{byp:.1f}" r="5.5"/>')
    s.append(t2(bxp - 10, byp - 8, "Proxima b", "プロキシマ b", "ink", "end"))
    s.append(t2(px, y + 66, "Proxima Centauri", "プロキシマ・ケンタウリ", "ink", "middle"))
    s.append(t2(px, y + 84, "one orbit of b: about 11.2 days", "b の一周: 約 11.2 日", "small", "middle"))
    return figure(
        1, 204, "".join(s),
        "The trip, not to scale. During the trip, the planet goes around its star hundreds of times or more. "
        "The speeds 0.2c and 0.1c are the paper's assumptions.",
        "旅の様子(縮尺は正しくありません)。旅の間に、惑星は星の周りを数百回以上回ります。"
        "0.2c と 0.1c の速さは、論文の仮定です。",
        "Diagram: a probe flies from the Sun to Proxima Centauri, about 4.2 light-years away. "
        "The planet Proxima b goes around the star once in about 11.2 days.",
        "図: 探査機が太陽から約 4.2 光年のプロキシマ・ケンタウリへ飛ぶ。惑星プロキシマ b は約 11.2 日で星を一周する。")


def fig_cloud():
    """Figure 2: the target plane, the cloud of predicted positions, and r90 (an illustration)."""
    s = []
    # side view: the probe's path meets the sheet at right angles
    cy = 150
    s.append(f'<path class="dim" d="M18,{cy} H138"/>')
    s.append(f'<path class="ink-fill" d="M138,{cy - 6} l12,6 l-12,6 z"/>')
    s.append(t2(78, cy - 14, "probe's path", "探査機の進む向き", "", "middle"))
    s.append(f'<path class="sheet" d="M166,58 L206,88 L206,244 L166,214 Z"/>')
    s.append(f'<circle class="planet dot" cx="186" cy="{cy}" r="5"/>')
    s.append(t2(186, 268, "target plane", "的の面", "ink", "middle"))
    s.append(t2(186, 285, "(β plane)", "(β 面)", "small", "middle"))
    # face-on view of the sheet
    px, py, pw = 230, 18, 266
    cx, cyy = px + pw / 2, py + pw / 2
    s.append(f'<rect class="panel" x="{px}" y="{py}" width="{pw}" height="{pw}" rx="8"/>')
    s.append(t2(px + 12, py + 22, "seen face-on", "正面から見る", "small"))
    rng = random.Random(7)
    th = math.radians(-28)
    pts = []
    for _ in range(460):
        u, v = rng.gauss(0, 1.0), rng.gauss(0, 0.5)
        pts.append((u * math.cos(th) - v * math.sin(th), u * math.sin(th) + v * math.cos(th)))
    dist = sorted(math.hypot(a, b) for a, b in pts)
    q90 = dist[int(0.9 * len(dist))]
    k = 86 / q90  # the 90% circle gets a radius of 86 units
    rr = q90 * k
    for a, b in pts:
        x, y = cx + a * k, cyy + b * k
        if px + 6 < x < px + pw - 6 and py + 30 < y < py + pw - 6:
            s.append(f'<circle class="pt" cx="{x:.1f}" cy="{y:.1f}" r="1.8"/>')
    s.append(f'<circle class="circle90" cx="{cx}" cy="{cyy}" r="{rr:.1f}"/>')
    # the radius, at right angles to the long side of the cloud
    va = th + math.pi / 2
    ex, ey = cx + rr * math.cos(va), cyy + rr * math.sin(va)
    s.append(f'<path class="radius" d="M{cx},{cyy} L{ex:.1f},{ey:.1f}"/>')
    s.append(f'<circle class="ink-fill" cx="{cx}" cy="{cyy}" r="2.5"/>')
    mx, my = (cx + ex) / 2, (cyy + ey) / 2
    s.append(t2(mx + 10, my + 6, r90(), r90(), "ink big halo"))
    # labels on the right, with leader lines
    lx = px + pw + 14
    p_cloud = (cx + 40 * math.cos(th), cyy + 40 * math.sin(th))
    s.append(f'<path class="leader" d="M{lx - 4},{py + 66} L{p_cloud[0]:.1f},{p_cloud[1]:.1f}"/>')
    s.append(t2(lx, py + 62, "predicted", "予測した", "ink"))
    s.append(t2(lx, py + 80, "positions (a cloud)", "位置(雲)", "ink"))
    ang = math.radians(28)
    p_c = (cx + rr * math.cos(ang), cyy + rr * math.sin(ang))
    s.append(f'<path class="leader" d="M{lx - 4},{py + 196} L{p_c[0]:.1f},{p_c[1]:.1f}"/>')
    s.append(t2(lx, py + 192, "circle that holds", "雲の 90% を", "ink"))
    s.append(t2(lx, py + 210, "90% of the cloud", "含む円", "ink"))
    s.append(t2(lx, py + 236, r90(" = its radius"), r90(" = その半径"), ""))
    return figure(
        2, 300, "".join(s),
        "The prediction is a cloud of possible positions on the target plane. r₉₀ is the radius of the smallest "
        "circle that holds 90% of the cloud. A small r₉₀ means a sharp prediction. This is an illustration, "
        "not data from the paper.",
        "予測は、的の面の上の、ありうる位置の雲です。r₉₀ は、雲の 90% を含む最も小さい円の半径です。"
        "r₉₀ が小さいほど、予測は鋭くなります。これは説明のための絵で、論文のデータではありません。",
        "Illustration: the probe's path meets a flat sheet, the target plane, at right angles. On the sheet, "
        "the predicted positions of the planet make a cloud. A circle holds 90% of the cloud; its radius is r90.",
        "説明の図: 探査機の進む向きと直角に、平らな板(的の面)がある。板の上で、予測した惑星の位置が雲になる。"
        "雲の 90% を含む円の半径が r90。")


def bar(x, base, h, w, cls):
    """A bar anchored to the baseline, with rounded top corners."""
    top, r = base - h, 3
    return (f'<path class="{cls}" d="M{x},{base} V{top + r} Q{x},{top} {x + r},{top} H{x + w - r} '
            f'Q{x + w},{top} {x + w},{top + r} V{base} Z"/>')


def fig_rule():
    """Figure 3: the three answers of the decision rule (an illustration)."""
    s = []
    base, rline = 214, 128
    panels = [
        ("✓", "Reached", "届いた", "all 8 at or below R", "8 通りすべて R 以下", [44, 62, 38, 70, 55, 48, 66, 58]),
        ("✗", "Not reached", "届かない", "all 8 above R", "8 通りすべて R より大きい",
         [120, 142, 104, 150, 128, 112, 136, 124]),
        ("?", "Undecided", "判定不能", "the 8 versions disagree", "8 通りの答えが分かれる",
         [62, 112, 70, 134, 58, 76, 118, 66]),
    ]
    for i, (glyph, en, ja, rule_en, rule_ja, hs) in enumerate(panels):
        x0 = 8 + i * 214
        s.append(f'<rect class="panel" x="{x0}" y="6" width="198" height="222" rx="8"/>')
        s.append(f'<circle class="badge" cx="{x0 + 20}" cy="26" r="10"/>')
        s.append(f'<text class="badge-glyph" x="{x0 + 20}" y="30.5" text-anchor="middle">{glyph}</text>')
        s.append(t2(x0 + 37, 31, en, ja, "ink big bold"))
        s.append(t2(x0 + 12, 54, rule_en, rule_ja, "small"))
        for j, h in enumerate(hs):
            cls = "b-in" if base - h >= rline else "b-out"
            s.append(bar(x0 + 32 + j * 20, base, h, 12, cls))
        s.append(f'<path class="axis" d="M{x0 + 12},{base} H{x0 + 186}"/>')
        s.append(f'<path class="rline" d="M{x0 + 26},{rline} H{x0 + 192}"/>')
        s.append(f'<text class="ink" x="{x0 + 12}" y="{rline + 4}">R</text>')
    # legend
    ly = 250
    s.append(f'<rect class="b-in" x="8" y="{ly - 10}" width="12" height="12" rx="2"/>')
    s.append(t2(26, ly, r90(" at or below R"), r90(" が R 以下"), ""))
    s.append(f'<rect class="b-out" x="170" y="{ly - 10}" width="12" height="12" rx="2"/>')
    s.append(t2(188, ly, r90(" above R"), r90(" が R より大きい"), ""))
    s.append(t2(632, ly, "each bar: one of the 8 versions", "棒一本: 8 通りのモデルの一つ", "small", "end"))
    return figure(
        3, 262, "".join(s),
        "The decision rule. For one test radius R, one launch year, and one speed, each bar is r₉₀ in one of "
        "the eight versions of the model. Undecided never means “not reached”. This is an illustration, "
        "not data from the paper.",
        "決め方の決まり。一つの試しの半径 R・打ち上げの年・速さについて、棒の一本一本が、8 通りのモデルの一つでの "
        "r₉₀ です。判定不能は「届かない」という意味ではありません。これは説明のための絵で、論文のデータではありません。",
        "Illustration of three panels. Reached: all eight bars are at or below the line R. Not reached: all eight "
        "bars are above R. Undecided: some bars are below R and some are above.",
        "三つの枠の説明の図。届いた: 8 本の棒がすべて線 R 以下。届かない: 8 本すべて R より上。"
        "判定不能: R より下の棒と上の棒がある。")


def fig_phase():
    """Figure 4: launch times over one orbit, and one example from the paper (2045, 0.2c)."""
    s = []
    # left: 24 launch times over one orbit
    ox, oy, orr = 150, 140, 92
    s.append(t2(ox, 18, "24 launch times over one orbit", "一周にわたる 24 の打ち上げ時刻", "ink bold", "middle"))
    s.append(f'<circle class="orbit" cx="{ox}" cy="{oy}" r="{orr}"/>')
    s.append(f'<circle class="star" cx="{ox}" cy="{oy}" r="8"/>')
    for k in range(24):
        a = math.radians(-90 + 15 * k)
        x, y = ox + orr * math.cos(a), oy + orr * math.sin(a)
        if k == 0:
            s.append(f'<circle class="planet dot" cx="{x:.1f}" cy="{y:.1f}" r="6.5"/>')
        else:
            s.append(f'<circle class="tick" cx="{x:.1f}" cy="{y:.1f}" r="2.6"/>')
    # a small arrow along the orbit, showing the direction of motion
    a1, a2, ra = math.radians(-80), math.radians(-40), orr + 14
    p1 = (ox + ra * math.cos(a1), oy + ra * math.sin(a1))
    p2 = (ox + ra * math.cos(a2), oy + ra * math.sin(a2))
    s.append(f'<path class="dim" d="M{p1[0]:.1f},{p1[1]:.1f} A{ra},{ra} 0 0 1 {p2[0]:.1f},{p2[1]:.1f}"/>')
    tx, ty = -math.sin(a2), math.cos(a2)  # direction of motion at the arrow's end
    nx, ny = math.cos(a2), math.sin(a2)
    hx, hy = p2[0] + 7 * tx, p2[1] + 7 * ty
    s.append(f'<path class="ink-fill" d="M{hx:.1f},{hy:.1f} L{p2[0] - 4 * nx:.1f},{p2[1] - 4 * ny:.1f} '
             f'L{p2[0] + 4 * nx:.1f},{p2[1] + 4 * ny:.1f} Z"/>')
    s.append(t2(ox, 262, "the planet's place at arrival, for launch", "打ち上げを約 0.47 日ずつずらしたときの、", "", "middle"))
    s.append(t2(ox, 280, "times about 0.47 days apart", "着いたときの惑星の位置", "", "middle"))
    s.append(t2(ox, 297, "one orbit: about 11.2 days", "一周: 約 11.2 日", "small", "middle"))
    # right: the example, circles to scale
    cx, cy, u = 470, 140, 0.70 / 1000  # SVG units per km
    r_lo, r_hi, r_mark = 83079.5 * u, 144155 * u, 100000 * u
    s.append(t2(cx, 18, "one example: launch in 2045 at 0.2c", "一つの例: 2045 年に 0.2c で打ち上げ", "ink bold", "middle"))
    s.append(f'<path class="ring" d="M{cx - r_hi:.1f},{cy} a{r_hi:.1f},{r_hi:.1f} 0 1 0 {2 * r_hi:.1f},0 '
             f'a{r_hi:.1f},{r_hi:.1f} 0 1 0 {-2 * r_hi:.1f},0 Z M{cx - r_lo:.1f},{cy} '
             f'a{r_lo:.1f},{r_lo:.1f} 0 1 0 {2 * r_lo:.1f},0 a{r_lo:.1f},{r_lo:.1f} 0 1 0 {-2 * r_lo:.1f},0 Z"/>')
    for r in (r_lo, r_hi):
        s.append(f'<circle class="ring-edge" cx="{cx}" cy="{cy}" r="{r:.1f}"/>')
    s.append(f'<circle class="mark-line" cx="{cx}" cy="{cy}" r="{r_mark:.1f}"/>')
    s.append(f'<circle class="ink-fill" cx="{cx}" cy="{cy}" r="2.5"/>')
    # a two-headed arrow across the ring
    a = math.radians(-45)
    ux, uy = math.cos(a), math.sin(a)
    q1 = (cx + (r_lo + 2) * ux, cy + (r_lo + 2) * uy)
    q2 = (cx + (r_hi - 2) * ux, cy + (r_hi - 2) * uy)
    s.append(f'<path class="arrow" d="M{q1[0]:.1f},{q1[1]:.1f} L{q2[0]:.1f},{q2[1]:.1f}"/>')
    for (qx, qy), sgn in ((q1, -1), (q2, 1)):
        bx_, by_ = qx - sgn * 7 * ux, qy - sgn * 7 * uy
        s.append(f'<path class="ink-fill" d="M{qx:.1f},{qy:.1f} L{bx_ - 3.5 * uy:.1f},{by_ + 3.5 * ux:.1f} '
                 f'L{bx_ + 3.5 * uy:.1f},{by_ - 3.5 * ux:.1f} Z"/>')
    # legend under the circles
    lx = cx - 118
    s.append(f'<path class="mark-line" d="M{lx},{258} h22"/>')
    s.append(t2(lx + 30, 262, "mark: 100,000 km", "目安: 10 万 km", "ink"))
    s.append(f'<rect class="ring" x="{lx}" y="{270}" width="22" height="12" rx="2"/>')
    s.append(f'<rect class="ring-edge" x="{lx}" y="{270}" width="22" height="12" rx="2"/>')
    s.append(t2(lx + 30, 280, "largest " + r90(" of the 8 versions:"), "8 通りで最も大きい " + r90(":"), "ink"))
    s.append(t2(lx + 30, 299, "about 83,000 to 144,000 km", "約 8 万 3 千〜14 万 4 千 km", "ink"))
    return figure(
        4, 308, "".join(s),
        "Left: the paper moves each launch across one orbit of the planet, in 24 steps. Right: one example from "
        "the paper, one of the six settings, with launch in 2045 at 0.2c. As the launch time moves, the largest "
        "r₉₀ of the eight versions moves between about 83,000 and 144,000 km. So at some launch times all eight "
        "versions are inside the 100,000 km mark, and at other times they are not. The circles on the right are "
        "to scale; the left part is a diagram.",
        "左: 論文は、それぞれの打ち上げを、惑星の一周にわたって 24 段階でずらします。右: 論文の一つの例で、6 つの設定の"
        "一つ、2045 年に 0.2c で打ち上げる場合です。打ち上げの時刻が動くと、8 通りの中で最も大きい r₉₀ は、約 8 万 "
        "3 千 km から 14 万 4 千 km の間を動きます。そのため、8 通りすべてが 10 万 km の目安の内側に入る時刻もあれば、"
        "入らない時刻もあります。右の円は縮尺どおりで、左は模式図です。",
        "Left: an orbit with 24 marks, the planet's places at arrival for 24 launch times. Right: a dashed circle "
        "for the 100,000 km mark lies between two circles of 83,000 and 144,000 km.",
        "左: 24 の印のある軌道。24 の打ち上げ時刻での、着いたときの惑星の位置。右: 10 万 km の目安の破線の円が、"
        "8 万 3 千 km と 14 万 4 千 km の二つの円の間にある。")


def fig_scale():
    """Figure 5: all results on one log scale (the paper's numbers)."""
    x0, dec = 24, 196  # x of 10^4 km, and units per factor of ten

    def X(v):
        return x0 + (math.log10(v) - 4) * dec

    s = []
    top, axis_y = 56, 336
    # legend
    s.append(f'<circle class="fast dot" cx="{x0 + 6}" cy="14" r="6"/>')
    s.append(t2(x0 + 18, 18, "0.2c (one fifth of the speed of light)", "0.2c(光の速さの 5 分の 1)", "ink"))
    s.append(f'<circle class="slow dot" cx="{x0 + 296}" cy="14" r="6"/>')
    s.append(t2(x0 + 308, 18, "0.1c (one tenth)", "0.1c(10 分の 1)", "ink"))
    # reference lines: the mark and the Earth-Moon distance
    xm, xe = X(1e5), X(384400)
    s.append(f'<path class="mark-line" d="M{xm:.1f},{top - 8} V{axis_y}"/>')
    s.append(t2(xm - 6, top - 10, "mark: 100,000 km", "目安: 10 万 km", "ink", "end"))
    s.append(f'<path class="moon-line" d="M{xe:.1f},{top - 8} V{axis_y}"/>')
    s.append(t2(xe + 6, top - 10, "Earth to Moon: 384,400 km", "地球から月: 38 万 4400 km", "", "start"))

    def dot(x, y, cls, en, ja):
        return (f'<g>{tip(en, ja)}<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="13"/>'
                f'<circle class="{cls} dot" cx="{x:.1f}" cy="{y:.1f}" r="6.5"/></g>')

    # row 1: today's data
    y = 84
    s.append(t2(x0, y, "Today's data: " + r90(" at the launch years on the list"),
                "今のデータ: リストの打ち上げの年での " + r90(), "ink bold halo"))
    a, b = X(7.2e6), X(9.45e6)
    s.append(f'<g>{tip("Today’s data: r90 is 7.2 to 9.45 million km (both speeds, all eight versions)", "今のデータ: r90 は 720 万〜945 万 km(二つの速さ、8 通りすべて)")}'
             f'<rect class="hit" x="{a - 6:.1f}" y="{y + 6}" width="{b - a + 12:.1f}" height="26"/>'
             f'<rect class="today" x="{a:.1f}" y="{y + 14}" width="{b - a:.1f}" height="10" rx="5"/></g>')
    s.append(t2(a - 8, y + 23, "7.2 to 9.45 million km (both speeds)", "720 万〜945 万 km(二つの速さ)", "halo", "end"))
    # row 2: future observations, one launch time per year
    y = 148
    s.append(t2(x0, y, "With future observations, one launch time per year (six settings)",
                "将来の観測あり、各年に一つの打ち上げ時刻(6 つの設定)", "ink bold halo"))
    s.append(dot(X(1e5), y + 20, "fast", "0.2c, one launch time per year: 100,000 km",
                 "0.2c、各年に一つの打ち上げ時刻: 10 万 km"))
    s.append(dot(X(316000), y + 20, "slow", "0.1c, one launch time per year: 316,000 km",
                 "0.1c、各年に一つの打ち上げ時刻: 31 万 6 千 km"))
    s.append(t2(X(1e5) - 12, y + 24, "100,000 km", "10 万 km", "halo", "end"))
    s.append(t2(X(316000) + 12, y + 24, "316,000 km", "31 万 6 千 km", "halo"))
    # row 3: future observations, 24 launch times over one orbit
    y = 214
    s.append(t2(x0, y, "With future observations, 24 launch times over one orbit (six settings)",
                "将来の観測あり、一周にわたる 24 の打ち上げ時刻(6 つの設定)", "ink bold halo"))
    xq = X(1e5)
    s.append(f'<g>{tip("At 100,000 km, no setting gives a definite earliest launch year over the orbit (both speeds)", "10 万 km では、一周を通して、届く最も早い打ち上げ年がはっきり決まる設定は無い(二つの速さ)")}'
             f'<circle class="hit" cx="{xq:.1f}" cy="{y + 20}" r="13"/>'
             f'<circle class="undec" cx="{xq:.1f}" cy="{y + 20}" r="7.5"/>'
             f'<text class="ink small" x="{xq:.1f}" y="{y + 24}" text-anchor="middle">?</text></g>')
    s.append(t2(xq - 14, y + 24, "no definite year", "年は決まらない", "halo", "end"))
    s.append(dot(X(316000), y + 20, "fast", "0.2c, 24 launch times over one orbit: 316,000 km",
                 "0.2c、一周にわたる 24 の打ち上げ時刻: 31 万 6 千 km"))
    s.append(dot(X(562000), y + 20, "slow", "0.1c, 24 launch times over one orbit: 562,000 km",
                 "0.1c、一周にわたる 24 の打ち上げ時刻: 56 万 2 千 km"))
    s.append(t2(X(316000), y + 44, "316,000 km", "31 万 6 千 km", "halo", "middle"))
    s.append(t2(X(562000) + 12, y + 24, "562,000 km", "56 万 2 千 km", "halo"))
    # row 4: without pictures of the planet
    y = 290
    s.append(t2(x0, y, "Without pictures of the planet (all combinations on the list)",
                "惑星の撮像なし(リストの全ての組み合わせ)", "ink bold halo"))
    s.append(dot(X(1e7), y + 13, "fast", "0.2c, without pictures of the planet: 10 million km",
                 "0.2c、惑星の撮像なし: 1000 万 km"))
    s.append(dot(X(1e7), y + 29, "slow", "0.1c, without pictures of the planet: 10 million km",
                 "0.1c、惑星の撮像なし: 1000 万 km"))
    s.append(t2(X(1e7) - 14, y + 25, "10 million km (both speeds)", "1000 万 km(二つの速さ)", "halo", "end"))
    # the axis, with the 13 test radii as small ticks
    s.append(f'<path class="axis" d="M{x0},{axis_y} H{X(1e7):.1f}"/>')
    for e in range(13):
        v = 10 ** (4 + e / 4)
        L = 7 if e % 4 == 0 else 4
        s.append(f'<path class="axis" d="M{X(v):.1f},{axis_y} v{L}"/>')
    labels = [(1e4, "10,000 km", "1 万 km", "start"), (1e5, "100,000 km", "10 万 km", "middle"),
              (1e6, "1 million km", "100 万 km", "middle"), (1e7, "10 million km", "1000 万 km", "end")]
    for v, en, ja, anc in labels:
        s.append(t2(X(v), axis_y + 22, en, ja, "", anc))
    s.append(t2(X(1e5 * 10 ** 0.5), axis_y + 42, "Each main step is 10 times the step before.",
                "目盛りが一つ進むと 10 倍になります。", "small", "middle"))
    return figure(
        5, 386, "".join(s),
        "All results on one scale. The gray bar is r₉₀ with today's data. The dots are the smallest test radius "
        "with a definite earliest launch year, for each speed. The small ticks on the scale are the 13 test radii. "
        "Numbers from the paper.",
        "全ての結果を一本の目盛りで。灰色の棒は、今のデータでの r₉₀ です。点は、速さごとの、届く最も早い打ち上げ年が"
        "はっきり決まる最も小さい試しの半径です。目盛りの小さい刻みは、13 の試しの半径です。数は論文のものです。",
        "Chart on a scale from 10,000 to 10 million km. Today's data: r90 is 7.2 to 9.45 million km. "
        "With future observations, one launch time per year: 100,000 km at 0.2c and 316,000 km at 0.1c. "
        "Over one orbit: 316,000 km at 0.2c and 562,000 km at 0.1c; at 100,000 km no setting gives a definite year. "
        "Without pictures of the planet: 10 million km at both speeds. The table below has the same numbers.",
        "1 万 km から 1000 万 km の目盛りの図。今のデータ: r90 は 720 万〜945 万 km。将来の観測あり、各年に一つの時刻: "
        "0.2c で 10 万 km、0.1c で 31 万 6 千 km。一周を通して: 0.2c で 31 万 6 千 km、0.1c で 56 万 2 千 km。"
        "10 万 km ではどの設定も年が決まらない。惑星の撮像なし: 二つの速さとも 1000 万 km。下の表に同じ数がある。")


def clock(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def transcript(script, chapters):
    starts = {c["id"]: c["start"] for c in chapters["chapters"]}
    out = ['<ol class="chapters">']
    for sc in script["scenes"]:
        t = starts[sc["id"]]
        mm = clock(t)
        en = " ".join(line["en"] for line in sc["lines"])
        ja = "".join(line["ja"] for line in sc["lines"])
        out.append(
            f'<li><button type="button" data-seek="{t}" aria-label="Play from {mm}" data-aria-en="Play from {mm}" '
            f'data-aria-ja="{mm} から再生">{mm}</button>'
            f'<h3><span data-l="en" lang="en">{sub90(esc(sc["title"]))}</span>'
            f'<span data-l="ja" lang="ja">{sub90(esc(sc["title_ja"]))}</span></h3>\n'
            f'<p data-l="en" lang="en">{sub90(esc(en))}</p>\n<p data-l="ja" lang="ja">{sub90(esc(ja))}</p></li>')
    out.append("</ol>")
    return "\n".join(out)


def main():
    page = (HERE / "page.html").read_text(encoding="utf-8")
    script = json.loads((HERE / "narration.json").read_text(encoding="utf-8"))
    chapters = json.loads((ROOT / "assets" / "video" / "chapters.json").read_text(encoding="utf-8"))
    total = round(chapters["duration"])
    head, body = page.split("</head>", 1)
    body = sub90(body)
    fill = {
        "{{DURATION_EN}}": f"{total // 60} min {total % 60} s",
        "{{DURATION_JA}}": f"{total // 60} 分 {total % 60} 秒",
        "{{TRANSCRIPT}}": transcript(script, chapters),
        "{{FIG0}}": fig_trip(),
        "{{FIG1}}": fig_cloud(),
        "{{FIG2}}": fig_rule(),
        "{{FIG4}}": fig_phase(),
        "{{FIG3}}": fig_scale(),
    }
    for k, v in fill.items():
        assert k in body, k
        body = body.replace(k, v)
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", body)
    assert not left, left
    (ROOT / "index.html").write_text(head + "</head>" + body, encoding="utf-8")
    print(f"index.html {len(head + body) / 1000:.0f} kB")


if __name__ == "__main__":
    main()
