"""Manim scenes for the explainer video (Manim Community Edition 0.22).

Each scene reads the clip lengths in build/timing.json. A beat starts with
self.beat() and ends with self.done(), which waits until the line and a short
pause have played. The real start time of every beat is written to
build/marks/<scene>.json, and tools/assemble.py places the clips there, so the
voice stays in step with the picture even if an animation runs long.

Render one scene:  manim render -r 1920,1080 --fps 30 tools/video.py S1
"""
import json
from pathlib import Path

import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
TIMING = json.loads((BUILD / "timing.json").read_text(encoding="utf-8"))
GAP = 0.45  # pause after each line, in seconds

config.background_color = "#0e1014"
FONT = "CMU Serif"

C_MARK = "#F4D345"    # the 100,000 km mark
C_TODAY = "#5CD0B3"   # today's data
C_FUT = "#58C4DD"     # declared future observations; also "reached"
C_NOT = "#FF862F"     # not reached
C_UND = "#8F959E"     # undecided
C_STAR = "#FC6255"
C_SUN = "#E8C11C"
C_PLANET = "#83C167"
C_D = "#B189C6"       # planet d
C_DIM = "#A3A9B1"
C_FAINT = "#5B616A"


def T(s, size=34, color=WHITE, **kw):
    return Text(s, font=FONT, font_size=size, color=color, **kw)


def M(s, size=34, color=WHITE, **kw):
    return MarkupText(s, font=FONT, font_size=size, color=color, **kw)


R90 = "r<sub>90</sub>"


def glow(point, color, r=0.12, layers=4):
    g = VGroup()
    for i in range(layers, 0, -1):
        g.add(Dot(point, radius=r * (1 + 0.8 * i), color=color, fill_opacity=0.07))
    g.add(Dot(point, radius=r, color=color))
    return g


def note(s):
    """Small grey note in the top right corner (the bottom is kept free for subtitles)."""
    return T(s, 22, C_FAINT).to_corner(UR, buff=0.35)


def check(size=0.35, color=C_FUT):
    p = VMobject(color=color, stroke_width=6)
    p.set_points_as_corners([[-0.5, 0, 0], [-0.15, -0.38, 0], [0.55, 0.45, 0]])
    return p.scale(size / 0.9)


def cross(size=0.3, color=C_NOT):
    a = Line([-1, -1, 0], [1, 1, 0], color=color, stroke_width=6)
    b = Line([-1, 1, 0], [1, -1, 0], color=color, stroke_width=6)
    return VGroup(a, b).scale(size / 2)


def cloud(n, sx, sy, angle, seed, center=ORIGIN, radius=0.03, color=C_FUT, opacity=0.85):
    rng = np.random.default_rng(seed)
    pts = rng.normal(size=(n, 2)) * [sx, sy]
    c, s = np.cos(angle), np.sin(angle)
    pts = pts @ np.array([[c, s], [-s, c]])
    dots = VGroup(*[Dot([x, y, 0], radius=radius, color=color, fill_opacity=opacity) for x, y in pts])
    dots.shift(center)
    r90 = float(np.quantile(np.hypot(pts[:, 0], pts[:, 1]), 0.9))
    return dots, r90


class LogAxis(VGroup):
    """Log scale from 10^4 to 10^7 km with the paper's 13 test radii as ticks."""

    def __init__(self, x0=-5.4, x1=5.0, y=-1.3, **kw):
        super().__init__(**kw)
        self.x0, self.x1, self.y = x0, x1, y
        self.line = Line([x0 - 0.2, y, 0], [x1 + 0.2, y, 0], color=GREY_B, stroke_width=2)
        self.ticks = VGroup()
        for i in range(13):
            x = self.x(10 ** (4 + i * 0.25))
            h = 0.16 if i % 4 == 0 else 0.09
            self.ticks.add(Line([x, y - h, 0], [x, y + h, 0], color=GREY_B, stroke_width=2))
        names = {4: "10 thousand", 5: "100 thousand", 6: "1 million", 7: "10 million"}
        self.labels = VGroup(*[
            T(n, 24, C_DIM).move_to([self.x(10 ** e), y - 0.45, 0]) for e, n in names.items()
        ])
        self.unit = T("km", 24, C_DIM).next_to(self.line, RIGHT, buff=0.2)
        self.add(self.line, self.ticks, self.labels, self.unit)

    def x(self, v):
        return self.x0 + (np.log10(v) - 4) / 3 * (self.x1 - self.x0)

    def p(self, v, dy=0.0):
        return np.array([self.x(v), self.y + dy, 0])


def mark_on(ax, v=1e5, color=C_MARK, h=1.1, label=None, size=26):
    ln = Line(ax.p(v, -0.25), ax.p(v, h), color=color, stroke_width=4)
    g = VGroup(ln)
    if label:
        g.add(T(label, size, color).next_to(ln, UP, buff=0.12))
    return g


class Beats(Scene):
    SID = None

    def setup(self):
        self.lines = TIMING[self.SID]
        self.k = -1
        self.marks = []

    def beat(self):
        self.k += 1
        self.t0 = self.renderer.time
        self.marks.append(round(self.t0, 4))

    def done(self, extra=0.0):
        end = self.t0 + self.lines[self.k]["dur"] + GAP + extra
        rem = end - self.renderer.time
        if rem < -0.05:
            print(f"[{self.SID} line {self.lines[self.k]['id']}] picture runs {-rem:.2f} s past the line")
        if rem > 1 / 30:
            self.wait(rem)

    def tear_down(self):
        assert len(self.marks) == len(self.lines), (self.SID, len(self.marks), len(self.lines))
        out = BUILD / "marks"
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{self.SID}.json").write_text(
            json.dumps({"marks": self.marks, "end": round(self.renderer.time, 4)}), encoding="utf-8")

    def fade_all(self, run_time=0.6):
        mobs = [m for m in self.mobjects]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)
        for m in mobs:
            m.clear_updaters()


class S1(Beats):
    SID = "s1"

    def construct(self):
        # Title card (no voice); its last frame is the poster.
        title = T("Where will Proxima b be", 60)
        title2 = T("when a probe arrives?", 60).next_to(title, DOWN, buff=0.3)
        sub = T("A plain-language guide to a 2026 research paper", 30, C_DIM).next_to(title2, DOWN, buff=0.6)
        VGroup(title, title2, sub).move_to(ORIGIN)
        self.play(FadeIn(VGroup(title, title2), shift=UP * 0.2), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)
        self.wait(1.6)
        self.play(FadeOut(VGroup(title, title2, sub)), run_time=0.6)

        # 1.1 nearest star
        self.beat()
        sun = glow(LEFT * 5.4 + UP * 0.3, C_SUN, 0.16)
        sun_l = T("Sun", 28, C_DIM).next_to(sun, DOWN, buff=0.3)
        prox = glow(RIGHT * 5.4 + UP * 0.3, C_STAR, 0.11)
        prox_l = T("Proxima Centauri", 28, C_DIM).next_to(prox, DOWN, buff=0.3)
        line = DashedLine(sun.get_right(), prox.get_left(), dash_length=0.12, color=GREY_B, stroke_width=2)
        dist = T("about 4.2 light-years", 34).next_to(line, UP, buff=0.35)
        nts = note("not to scale")
        self.play(FadeIn(sun, scale=0.5), FadeIn(sun_l), FadeIn(nts), run_time=0.8)
        self.play(Create(line), run_time=1.4)
        self.play(FadeIn(prox, scale=0.5), FadeIn(prox_l), Write(dist), run_time=1.2)
        self.done()

        # 1.2 planet b, about 11 days
        self.beat()
        center = UP * 0.4
        self.play(FadeOut(VGroup(sun, sun_l, line, dist, prox_l)), prox.animate.move_to(center).scale(1.6),
                  run_time=1.0)
        orbit = Ellipse(width=6.0, height=2.6, color=GREY_B, stroke_width=2).move_to(center)
        th = {"v": -PI / 2}
        planet = Dot(radius=0.09, color=C_PLANET)

        def move_planet(m, dt):
            th["v"] += 2 * PI * dt / 4.0
            m.move_to(center + np.array([3.0 * np.cos(th["v"]), 1.3 * np.sin(th["v"]), 0]))

        move_planet(planet, 0)
        planet.add_updater(move_planet)
        pl = T("Proxima b", 28, C_PLANET)
        pl.add_updater(lambda m: m.next_to(planet, UR, buff=0.08))
        per = T("one orbit: about 11 days", 30, C_DIM).move_to(UP * 2.6)
        self.play(Create(orbit), FadeIn(planet), FadeIn(pl), run_time=1.0)
        self.play(FadeIn(per), run_time=0.6)
        self.done()

        # 1.3 a small probe
        self.beat()
        probe = Triangle(color=WHITE, fill_opacity=1).scale(0.12).rotate(-PI / 2)
        probe.move_to(LEFT * 7.4 + DOWN * 0.9)
        path = DashedLine(LEFT * 7.4 + DOWN * 0.9, LEFT * 4.3 + DOWN * 0.9, dash_length=0.1,
                          color=GREY_B, stroke_width=2)
        probe_l = T("small probe", 28, C_DIM).move_to(LEFT * 5.2 + DOWN * 1.5)
        self.play(probe.animate.move_to(LEFT * 4.3 + DOWN * 0.9), Create(path), run_time=2.0, rate_func=smooth)
        self.play(FadeIn(probe_l), run_time=0.5)
        self.done()

        # 1.4 more than 20 years
        self.beat()
        trip = M(f"at 1/5 of the speed of light: <span foreground='{C_MARK}'>more than 20 years</span>", 32)
        trip.move_to(UP * 3.3)
        self.play(FadeOut(per), Write(trip), run_time=1.4)
        self.done()

        # 1.5 predict before launch
        self.beat()
        ghost_pt = center + np.array([3.0 * np.cos(2.35), 1.3 * np.sin(2.35), 0])
        ghost = Circle(radius=0.16, color=C_PLANET, stroke_width=3).move_to(ghost_pt)
        q = T("?", 40, C_PLANET).next_to(ghost, UP, buff=0.12)
        aim = DashedLine(probe.get_center(), ghost_pt, dash_length=0.12, color=C_MARK, stroke_width=3)
        txt = T("predicted before launch", 30, C_MARK).move_to(DOWN * 2.3 + LEFT * 1.0)
        self.play(Create(aim), FadeOut(pl), run_time=1.2)
        self.play(GrowFromCenter(ghost), FadeIn(q), run_time=0.8)
        self.play(FadeIn(txt, shift=UP * 0.1), run_time=0.6)
        self.done()

        # 1.6 the question
        self.beat()
        self.fade_all(0.7)
        q1 = T("How well can we know that position", 46)
        q2 = M(f"<span foreground='{C_MARK}'>before launch</span>?", 46).next_to(q1, DOWN, buff=0.3)
        self.play(Write(q1), run_time=1.6)
        self.play(FadeIn(q2, shift=UP * 0.1), run_time=0.7)
        self.done(extra=0.3)
        self.play(FadeOut(VGroup(q1, q2)), run_time=0.6)


class S2(Beats):
    SID = "s2"

    def construct(self):
        # 2.1 a sheet at right angles to the path
        self.beat()
        sheet = Polygon([0.9, -2.1, 0], [2.7, -1.2, 0], [2.7, 2.4, 0], [0.9, 1.5, 0],
                        color=GREY_B, stroke_width=2, fill_color=GREY_D, fill_opacity=0.35)
        hit = sheet.get_center()
        arrow = Arrow(LEFT * 6.2 + DOWN * 0.6, hit, buff=0.05, color=WHITE, stroke_width=4,
                      max_tip_length_to_length_ratio=0.05)
        probe_l = T("probe's path", 28, C_DIM).next_to(arrow.get_start(), UP, buff=0.25).shift(RIGHT * 1.0)
        planet = Dot(hit, radius=0.08, color=C_PLANET)
        right = T("at right angles to the path", 28, C_DIM).move_to(RIGHT * 3.6 + DOWN * 2.6)
        self.play(GrowArrow(arrow), FadeIn(probe_l), run_time=1.2)
        self.play(DrawBorderThenFill(sheet), FadeIn(planet), run_time=1.2)
        self.play(FadeIn(right), run_time=0.5)
        self.done()

        # 2.2 the target plane
        self.beat()
        name = T("target plane", 40, WHITE).move_to(RIGHT * 4.85 + UP * 3.3)
        beta = M("(the paper calls it the β plane)", 22, C_DIM).next_to(name, DOWN, buff=0.1)
        self.play(Write(name), FadeIn(beta), run_time=0.9)
        self.done()

        # 2.3 not one exact point
        self.beat()
        square = Square(side_length=5.4, color=GREY_B, stroke_width=2, fill_color=GREY_D,
                        fill_opacity=0.25).move_to(LEFT * 2.6 + DOWN * 0.15)
        self.play(FadeOut(VGroup(arrow, probe_l, right, beta)),
                  ReplacementTransform(sheet, square), planet.animate.move_to(square.get_center()),
                  name.animate.scale(0.75).next_to(square, UP, buff=0.2), run_time=1.2)
        q = T("?", 44, C_PLANET).next_to(planet, UR, buff=0.1)
        self.play(FadeIn(q), Indicate(planet, color=C_PLANET), run_time=1.0)
        self.done()

        # 2.4 a cloud of possible positions
        self.beat()
        c0 = square.get_center()
        dots, r90 = cloud(420, 0.95, 0.42, 0.5, seed=7, center=c0)
        self.play(FadeOut(q), FadeOut(planet), LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.004),
                  run_time=2.0)
        self.done()

        # 2.5 the smallest circle that holds 90%
        self.beat()
        circ = Circle(radius=r90, color=WHITE, stroke_width=4).move_to(c0)
        pct = T("90%", 30, WHITE).move_to(c0 + np.array([0, -r90 - 0.3, 0]))
        self.play(GrowFromCenter(circ), run_time=1.4)
        self.play(FadeIn(pct), run_time=0.5)
        self.done()

        # 2.6 r90
        self.beat()
        ang = 0.6
        rad = Line(c0, c0 + r90 * np.array([np.cos(ang), np.sin(ang), 0]), color=C_MARK, stroke_width=4)
        lab = M(R90, 40, C_MARK).move_to(c0 + (r90 + 0.5) * np.array([np.cos(ang), np.sin(ang), 0]))
        self.play(Create(rad), Write(lab), run_time=1.0)
        self.done()

        # 2.7 sharp and vague
        self.beat()
        grp = VGroup(dots, circ, rad)
        sharp = M(f"small {R90}: sharp prediction", 32, WHITE).move_to(RIGHT * 3.6 + UP * 0.6)
        vague = M(f"large {R90}: vague prediction", 32, WHITE).move_to(RIGHT * 3.6 + DOWN * 0.6)
        self.play(FadeOut(lab), FadeOut(pct), grp.animate.scale(0.4, about_point=c0), FadeIn(sharp), run_time=1.3)
        self.wait(0.6)
        self.play(grp.animate.scale(2.9, about_point=c0), sharp.animate.set_opacity(0.35), FadeIn(vague),
                  run_time=1.5)
        self.done()
        self.fade_all(0.6)


class S3(Beats):
    SID = "s3"

    def construct(self):
        # 3.1
        self.beat()
        q = T("How small is small enough?", 46).move_to(UP * 2.6)
        self.play(Write(q), run_time=1.0)
        self.done()

        # 3.2 100,000 km
        self.beat()
        big = T("100,000 km", 80, C_MARK).move_to(UP * 0.9)
        src = T("one published requirement (Eubanks et al. 2026)", 28, C_DIM).next_to(big, DOWN, buff=0.35)
        self.play(FadeIn(big, scale=0.8), run_time=1.0)
        self.play(FadeIn(src), run_time=0.6)
        self.done()

        # 3.3 a quarter of the Earth-Moon distance
        self.beat()
        y = -1.2
        earth = glow([-5.0, y, 0], "#3B82F6", 0.17, 3)
        moon = glow([5.0, y, 0], GREY_B, 0.07, 2)
        e_l = T("Earth", 26, C_DIM).next_to(earth, DOWN, buff=0.25)
        m_l = T("Moon", 26, C_DIM).next_to(moon, DOWN, buff=0.25)
        em = Line([-5.0, y, 0], [5.0, y, 0], color=GREY_B, stroke_width=2)
        em_l = T("384,400 km", 26, C_DIM).next_to(em, DOWN, buff=0.25)
        frac = 100000 / 384400
        seg = Line([-5.0, y, 0], [-5.0 + 10.0 * frac, y, 0], color=C_MARK, stroke_width=8)
        seg_l = T("100,000 km: about 1/4", 28, C_MARK).next_to(seg, UP, buff=0.3)
        self.play(FadeOut(src), big.animate.scale(0.6).move_to(UP * 1.6), FadeIn(earth), FadeIn(moon),
                  FadeIn(e_l), FadeIn(m_l), Create(em), FadeIn(em_l), run_time=1.2)
        self.play(Create(seg), FadeIn(seg_l), run_time=1.0)
        self.done()

        # 3.4 one mark, not the only requirement
        self.beat()
        one = M(f"<span foreground='{C_MARK}'>one mark</span>, not the only possible requirement", 34)
        one.move_to(UP * 1.6)
        self.play(FadeOut(VGroup(earth, moon, e_l, m_l, em, em_l, seg, seg_l)),
                  ReplacementTransform(big, one), run_time=1.2)
        self.done()

        # 3.5 thirteen test radii
        self.beat()
        ax = LogAxis(y=-0.6)
        m = mark_on(ax, 1e5, h=0.9, label="mark")
        lab = M("13 test radii <i>R</i>, from 10,000 km to 10 million km", 30, WHITE).move_to(DOWN * 2.2)
        self.play(FadeOut(q), one.animate.move_to(UP * 2.6), Create(ax.line), run_time=0.8)
        self.play(LaggedStart(*[Create(t) for t in ax.ticks], lag_ratio=0.12), FadeIn(ax.labels),
                  FadeIn(ax.unit), run_time=1.6)
        self.play(Create(m[0]), FadeIn(m[1]), FadeIn(lab), run_time=0.8)
        self.done()
        self.fade_all(0.6)


class S4(Beats):
    SID = "s4"

    def construct(self):
        # 4.1 two kinds of data
        self.beat()
        card_g = VGroup(RoundedRectangle(corner_radius=0.15, width=5.8, height=0.85, color=GREY_B, stroke_width=2),
                        T("Gaia DR3", 32)).move_to([-3.4, 2.9, 0])
        card_r = VGroup(RoundedRectangle(corner_radius=0.15, width=5.8, height=0.85, color=GREY_B, stroke_width=2),
                        T("Radial velocities", 32)).move_to([3.4, 2.9, 0])
        self.play(FadeIn(card_g, shift=DOWN * 0.2), FadeIn(card_r, shift=DOWN * 0.2), run_time=1.0)
        self.done()

        # 4.2 Gaia: position, distance, motion on the sky
        self.beat()
        sky = Rectangle(width=5.8, height=3.6, color=C_FAINT, stroke_width=1.5).move_to([-3.4, 0.4, 0])
        rng = np.random.default_rng(3)
        field = VGroup(*[
            Dot(sky.get_center() + np.array([rng.uniform(-2.8, 2.8), rng.uniform(-1.7, 1.7), 0]),
                radius=rng.uniform(0.012, 0.03), color=WHITE, fill_opacity=rng.uniform(0.3, 0.8))
            for _ in range(70)])
        star = glow(sky.get_center() + LEFT * 1.8 + DOWN * 0.6, C_STAR, 0.07, 3)
        trail = TracedPath(star.get_center, stroke_color=C_STAR, stroke_width=3, stroke_opacity=0.8)
        g_l = T("position, distance, motion on the sky", 24, C_DIM).next_to(sky, DOWN, buff=0.2)
        self.add(trail)
        self.play(FadeIn(sky), FadeIn(field), FadeIn(star), FadeIn(g_l), run_time=0.8)
        self.play(star.animate.shift(RIGHT * 3.4 + UP * 1.2), run_time=3.2, rate_func=linear)
        self.done()

        # 4.3 radial velocities
        self.beat()
        box = Rectangle(width=5.8, height=3.6, color=C_FAINT, stroke_width=1.5).move_to([3.4, 0.4, 0])
        x0, x1, yc = 1.0, 5.8, 0.4
        base = DashedLine([x0, yc, 0], [x1, yc, 0], dash_length=0.08, color=C_FAINT, stroke_width=1.5)
        curve = ParametricFunction(lambda t: np.array([t, yc + 1.05 * np.sin(2 * PI * (t - x0) / 1.6), 0]),
                                   t_range=[x0, x1], color=WHITE, stroke_width=3)
        away = T("away from us", 22, "#F08A7E").move_to([x1 - 0.9, yc + 1.45, 0])
        toward = T("toward us", 22, "#7EB6F0").move_to([x1 - 0.9, yc - 1.45, 0])
        r_l = T("speed toward and away from us", 24, C_DIM).next_to(box, DOWN, buff=0.2)
        self.play(FadeIn(box), Create(base), FadeIn(r_l), run_time=0.6)
        self.play(Create(curve), FadeIn(away), FadeIn(toward), run_time=3.0, rate_func=linear)
        self.done()

        # 4.4 the model: the star's path with a small pull from Alpha Cen A and B
        self.beat()
        self.remove(trail)
        self.fade_all(0.6)
        title = T("The model", 36).move_to(UP * 3.2)
        nts = note("not to scale")
        path = ParametricFunction(lambda t: np.array([t - 0.6, -0.6 + 0.00875 * ((t + 5.5) ** 2 - 30.25), 0]),
                                  t_range=[-5.5, 0.0], color=C_FAINT, stroke_width=3)
        star = glow(path.get_start(), C_STAR, 0.1, 3)
        ac = VGroup(glow([-4.6, 2.3, 0], "#FFE7A0", 0.08, 3), glow([-4.35, 2.15, 0], "#FFD27A", 0.06, 3))
        ac_l = T("Alpha Centauri A and B", 24, C_DIM).next_to(ac, RIGHT, buff=0.25)
        self.play(FadeIn(title), FadeIn(nts), FadeIn(ac), FadeIn(ac_l), FadeIn(star), run_time=0.8)
        pull = Arrow(path.point_from_proportion(0.5), path.point_from_proportion(0.5) + np.array([-0.5, 0.75, 0]),
                     buff=0.1, color="#FFE7A0", stroke_width=3, max_tip_length_to_length_ratio=0.25)
        self.play(Create(path), MoveAlongPath(star, path), run_time=3.0, rate_func=smooth)
        self.play(GrowArrow(pull), run_time=0.6)
        self.done()

        # 4.5 the planet on its orbit
        self.beat()
        sc = star.get_center()
        a, b = 2.3, 1.5
        foc = np.sqrt(a * a - b * b)
        orbit = Ellipse(width=2 * a, height=2 * b, color=GREY_B, stroke_width=2).move_to(sc + RIGHT * foc)
        th = {"v": 0.0}
        planet = Dot(radius=0.08, color=C_PLANET)

        def on_orbit(m, dt):
            th["v"] += 2 * PI * dt / 3.0
            p = np.array([a * np.cos(th["v"]), b * np.sin(th["v"]), 0])
            m.move_to(orbit.get_center() + rotate_vector(p, orbit_angle["v"]))

        orbit_angle = {"v": 0.0}
        on_orbit(planet, 0)
        planet.add_updater(on_orbit)
        b_l = T("planet b", 24, C_PLANET)
        b_l.add_updater(lambda m: m.next_to(planet, UR, buff=0.05))
        self.play(FadeOut(pull), Create(orbit), FadeIn(planet), FadeIn(b_l), run_time=1.0)
        self.done()

        # 4.6 planet d and general relativity slowly turn the orbit of b
        self.beat()
        d_orbit = Circle(radius=0.85, color=C_D, stroke_width=2).move_to(sc)
        d_orbit = DashedVMobject(d_orbit, num_dashes=30)
        dpl = Dot(sc + 0.85 * np.array([-0.707, 0.707, 0]), radius=0.06, color=C_D)
        d_l = T("planet d", 24, C_D).next_to(dpl, UL, buff=0.08)
        turn = T("planet d and general relativity slowly turn the orbit of b", 28, WHITE).move_to(DOWN * 2.45)
        self.play(Create(d_orbit), FadeIn(dpl), FadeIn(d_l), FadeIn(turn), FadeOut(ac), FadeOut(ac_l), run_time=1.0)
        vt = ValueTracker(0)

        def follow(m):
            m.move_to(sc + rotate_vector(RIGHT * foc, vt.get_value()))
            m.rotate(vt.get_value() - follow.last)
            follow.last = vt.get_value()

        follow.last = 0.0
        orbit.add_updater(follow)
        planet.remove_updater(on_orbit)

        def on_orbit2(m, dt):
            th["v"] += 2 * PI * dt / 3.0
            p = np.array([a * np.cos(th["v"]), b * np.sin(th["v"]), 0])
            m.move_to(sc + rotate_vector(RIGHT * foc + p, vt.get_value()))

        planet.add_updater(on_orbit2)
        self.play(vt.animate.set_value(PI / 5), run_time=3.0, rate_func=smooth)
        orbit.clear_updaters()
        self.done()

        # 4.7 leaving out planet d moves the position by 36,000-212,000 km
        self.beat()
        planet.clear_updaters()
        b_l.clear_updaters()
        self.play(FadeOut(turn), FadeOut(b_l), run_time=0.4)
        p_with = planet.get_center()
        p_wo = p_with + np.array([0.75, 0.45, 0])
        wo = Dot(p_wo, radius=0.08, color=WHITE)
        with_l = T("with d", 24, C_PLANET).next_to(planet, LEFT, buff=0.15)
        wo_l = T("without d", 24, WHITE).next_to(wo, RIGHT, buff=0.15)
        br = DoubleArrow(p_with, p_wo, buff=0.1, color=C_MARK, stroke_width=3, tip_length=0.15)
        shift = T("leave out planet d: the position moves 36,000 to 212,000 km", 28, WHITE).move_to(DOWN * 2.45)
        self.play(FadeIn(with_l), TransformFromCopy(planet, wo), run_time=1.0)
        self.play(GrowFromCenter(br), FadeIn(wo_l), FadeIn(shift), run_time=1.0)
        self.done()

        # 4.8 about the size of the mark; included for future observations
        self.beat()
        same = M(f"about the size of the <span foreground='{C_MARK}'>mark</span>: "
                 "the model for future observations includes it", 28).move_to(DOWN * 2.45)
        self.play(ReplacementTransform(shift, same), run_time=1.0)
        self.done()
        self.fade_all(0.6)


class S5(Beats):
    SID = "s5"

    def construct(self):
        # 5.1
        self.beat()
        title = T("A fair test", 44).move_to(UP * 3.1)
        self.play(Write(title), run_time=0.8)
        self.done()

        # 5.2 rules fixed before each computation
        self.beat()
        names = ["rules written\nand fixed", "computation", "results"]
        boxes = VGroup()
        for i, n in enumerate(names):
            r = RoundedRectangle(corner_radius=0.15, width=3.4, height=1.3, color=GREY_B, stroke_width=2)
            boxes.add(VGroup(r, T(n, 28)).move_to([-4.4 + 4.4 * i, 0.6, 0]))
        arrows = VGroup(*[Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.1, color=C_DIM,
                                stroke_width=3) for i in range(2)])
        lock = VGroup(RoundedRectangle(corner_radius=0.05, width=0.42, height=0.34, color=C_MARK,
                                       fill_opacity=1, stroke_width=0),
                      Arc(radius=0.14, start_angle=0, angle=PI, color=C_MARK, stroke_width=5).shift(UP * 0.17))
        lock.next_to(boxes[0], UP, buff=0.2)
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.2) for b in boxes], lag_ratio=0.3),
                  LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.5), run_time=2.0)
        self.play(FadeIn(lock, scale=0.6), run_time=0.5)
        self.done()

        # 5.3 eight versions of the model
        self.beat()
        self.play(FadeOut(VGroup(boxes, arrows, lock)), run_time=0.5)
        rs = [0.52, 0.62, 0.47, 0.71, 0.58, 0.66, 0.5, 0.75]
        panels = VGroup()
        circles = VGroup()
        for i in range(8):
            cx, cy = -4.65 + 3.1 * (i % 4), 1.3 - 2.25 * (i // 4)
            sq = Square(side_length=2.0, color=C_FAINT, stroke_width=1.5).move_to([cx, cy, 0])
            d, r90 = cloud(36, rs[i] * 0.55, rs[i] * 0.33, 0.3 + 0.4 * i, seed=20 + i, center=[cx, cy, 0],
                           radius=0.022)
            c = Circle(radius=rs[i], color=WHITE, stroke_width=2.5).move_to([cx, cy, 0])
            panels.add(VGroup(sq, d))
            circles.add(c)
        lab8 = T("8 versions of the model", 30, C_DIM).move_to(UP * 2.65)
        self.play(FadeOut(title), FadeIn(lab8),
                  LaggedStart(*[FadeIn(p) for p in panels], lag_ratio=0.1), run_time=1.2)
        self.play(LaggedStart(*[Create(c) for c in circles], lag_ratio=0.08), run_time=0.8)
        self.done()

        # 5.4 different choices about the planet, the star, and the orientation
        self.beat()
        ch = T("planet: 2 choices  ×  star: 2 choices  ×  orientation: 2 choices  =  8", 28)
        ch.move_to(DOWN * 2.45)
        self.play(FadeIn(ch, shift=UP * 0.1), run_time=0.8)
        self.done()

        def test_circles(R):
            return VGroup(*[DashedVMobject(Circle(radius=R, color=C_MARK, stroke_width=3), num_dashes=24)
                            .move_to(p[0].get_center()) for p in panels])

        def verdicts(R):
            g = VGroup()
            for i, p in enumerate(panels):
                mk = check() if rs[i] <= R else cross()
                g.add(mk.move_to(p[0].get_corner(UR) + np.array([-0.28, -0.28, 0])))
            return g

        def tag(text, color):
            return VGroup(RoundedRectangle(corner_radius=0.12, width=3.6, height=0.7, color=color,
                                           fill_opacity=0.18, stroke_width=2), T(text, 30, color)).move_to(DOWN * 2.45)

        # 5.5 reached: inside in all eight
        self.beat()
        tc = test_circles(0.86)
        v = verdicts(0.86)
        rlab = M("test radius <i>R</i>", 26, C_MARK).move_to(UP * 2.65 + RIGHT * 3.6)
        t1 = tag("reached", C_FUT)
        self.play(FadeOut(ch), LaggedStart(*[Create(c) for c in tc], lag_ratio=0.06), FadeIn(rlab), run_time=1.2)
        self.play(LaggedStart(*[FadeIn(x, scale=0.5) for x in v], lag_ratio=0.06), run_time=0.8)
        self.play(FadeIn(t1), run_time=0.5)
        self.done()

        # 5.6 not reached: outside in all eight
        self.beat()
        tc2 = test_circles(0.36)
        v2 = verdicts(0.36)
        t2 = tag("not reached", C_NOT)
        self.play(Transform(tc, tc2), FadeOut(v), FadeOut(t1), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(x, scale=0.5) for x in v2], lag_ratio=0.06), FadeIn(t2), run_time=0.8)
        self.done()

        # 5.7 undecided: the versions disagree
        self.beat()
        tc3 = test_circles(0.6)
        v3 = verdicts(0.6)
        t3 = tag("undecided", C_UND)
        self.play(Transform(tc, tc3), FadeOut(v2), FadeOut(t2), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(x, scale=0.5) for x in v3], lag_ratio=0.06), FadeIn(t3), run_time=0.8)
        self.done()

        # 5.8 undecided never means no
        self.beat()
        neq = M(f"<span foreground='{C_UND}'>undecided</span>  ≠  <span foreground='{C_NOT}'>not reached</span>", 34)
        neq.move_to(DOWN * 2.45)
        self.play(ReplacementTransform(t3, neq), run_time=0.8)
        self.done(extra=0.2)
        self.fade_all(0.6)


class S6(Beats):
    SID = "s6"

    def construct(self):
        # 6.1
        self.beat()
        title = T("With today's data", 44).move_to(UP * 3.1)
        self.play(Write(title), run_time=0.9)
        self.done()

        # 6.2 r90 = 7.2-9.45 million km at the launch years on the list
        self.beat()
        ax = LogAxis(y=-0.9)
        band = Line(ax.p(7.2e6, 0.35), ax.p(9.45e6, 0.35), color=C_TODAY, stroke_width=16)
        b_l = M(f"{R90} = 7.2 to 9.45 million km", 30, C_TODAY).move_to(UP * 1.45 + RIGHT * 2.6)
        b_s = T("(launch years on the list, today's data)", 24, C_DIM).next_to(b_l, DOWN, buff=0.15)
        self.play(FadeIn(ax), run_time=0.8)
        self.play(Create(band), FadeIn(b_l), FadeIn(b_s), run_time=1.2)
        self.done()

        # 6.3 about the size of the orbit; 70-95 times the mark
        self.beat()
        m = mark_on(ax, 1e5, h=1.0, label="mark: 100,000 km")
        span = DoubleArrow(ax.p(1e5, 0.35), ax.p(7.2e6, 0.35), buff=0.05, color=WHITE, stroke_width=3,
                           tip_length=0.18)
        times = T("about 70 to 95 times the mark", 28).next_to(span, UP, buff=0.15).shift(RIGHT * 0.8)
        orb = T("about the size of the planet's orbit", 26, C_DIM).move_to(DOWN * 2.45)
        self.play(Create(m[0]), FadeIn(m[1]), run_time=0.8)
        self.play(GrowFromCenter(span), FadeIn(times), run_time=1.0)
        self.play(FadeIn(orb), run_time=0.5)
        self.done()

        # 6.4 no single better input reaches the mark
        self.beat()
        tryline = DashedLine(ax.p(7.0e6, 0.9), ax.p(1.2e5, 0.9), dash_length=0.12, color=C_DIM, stroke_width=3)
        x = cross(0.45).move_to(ax.p(9e5, 0.9))
        one = T("one better input alone: does not reach the mark", 28).move_to(DOWN * 2.45)
        self.play(FadeOut(orb), FadeOut(span), FadeOut(times), Create(tryline), run_time=1.0)
        self.play(FadeIn(x, scale=0.5), FadeIn(one), run_time=0.7)
        self.done()

        # 6.5 the orientation of the orbit is among the largest parts
        self.beat()
        self.play(FadeOut(VGroup(ax, band, b_l, b_s, m, tryline, x, one)), title.animate.set_opacity(0.0),
                  run_time=0.7)
        c = UP * 0.4
        st = glow(c, C_STAR, 0.1, 3)
        orbits = VGroup()
        for i, (ang, h) in enumerate([(0.35, 0.45), (0.95, 0.62), (1.5, 0.3), (2.05, 0.75), (2.6, 0.5), (3.0, 0.36)]):
            e = Ellipse(width=5.0, height=5.0 * h, color=C_TODAY if i == 0 else GREY_B,
                        stroke_width=2.5, stroke_opacity=0.9 if i == 0 else 0.45).move_to(c).rotate(ang)
            orbits.add(e)
        o_l = T("orientation of the orbit: how it is turned in space", 30).move_to(DOWN * 2.45)
        nts = note("illustration")
        self.play(FadeIn(st), FadeIn(nts), LaggedStart(*[Create(o) for o in orbits], lag_ratio=0.15),
                  run_time=2.0)
        self.play(FadeIn(o_l), Rotate(orbits, angle=0.5, about_point=c), run_time=1.6)
        self.done()

        # 6.6 radial velocities do not measure it
        self.beat()
        rv = T("radial velocities do not measure it", 30, C_DIM).move_to(DOWN * 2.45)
        self.play(ReplacementTransform(o_l, rv), run_time=0.8)
        self.done(extra=0.2)
        self.fade_all(0.6)


class S7(Beats):
    SID = "s7"

    def construct(self):
        # 7.1
        self.beat()
        title = T("Possible future observations", 44).move_to(UP * 3.1)
        self.play(Write(title), run_time=1.0)
        self.done()

        # 7.2 an assumption, not a forecast
        self.beat()
        asm = VGroup(RoundedRectangle(corner_radius=0.12, width=6.8, height=0.7, color=C_MARK, stroke_width=2),
                     T("quality: an assumption, not a forecast", 28, C_MARK)).move_to(UP * 2.2)
        self.play(FadeIn(asm, shift=DOWN * 0.1), run_time=0.7)
        self.done()

        # 7.3 the four kinds of declared observations
        self.beat()

        def card(text, icon, pos):
            r = RoundedRectangle(corner_radius=0.15, width=6.5, height=1.5, color=GREY_B, stroke_width=2)
            icon.move_to(r.get_left() + RIGHT * 0.7)
            t = T(text, 25).next_to(r.get_left(), RIGHT, buff=1.4)
            return VGroup(r, t, icon).move_to(pos)

        ic1 = VGroup(glow(ORIGIN, C_STAR, 0.07, 2), Dot(RIGHT * 0.38 + UP * 0.12, radius=0.05, color=C_PLANET),
                     Circle(radius=0.14, color=C_PLANET, stroke_width=2).move_to(RIGHT * 0.38 + UP * 0.12))
        ic2 = VGroup(*[Dot([0.18 * i, 0.18 * j, 0], radius=0.025, color=WHITE) for i in range(-2, 3)
                       for j in range(-2, 3)])
        ic3 = ParametricFunction(lambda t: np.array([t, 0.18 * np.sin(2 * PI * t / 0.45), 0]),
                                 t_range=[-0.45, 0.45], color=WHITE, stroke_width=3)
        ic4 = Arrow(RIGHT * 0.35, LEFT * 0.35, buff=0, color=WHITE, stroke_width=4,
                    max_tip_length_to_length_ratio=0.35)
        cards = VGroup(
            card("pictures that show the planet\napart from its star", ic1, [-3.45, 0.75, 0]),
            card("more precise Gaia data", ic2, [3.45, 0.75, 0]),
            card("more radial velocities", ic3, [-3.45, -1.0, 0]),
            card("a more precise speed of\nthe star toward us", ic4, [3.45, -1.0, 0]),
        )
        for i, cd in enumerate(cards):
            self.play(FadeIn(cd, shift=UP * 0.15), run_time=0.6)
            self.wait([1.4, 0.6, 0.6, 0.2][i])
        self.done()

        # 7.4 the planet's orbit is fast: a few days change the place a lot
        self.beat()
        self.play(FadeOut(VGroup(cards, asm)), title.animate.set_opacity(0.0), run_time=0.6)
        c = UP * 0.3
        R = 2.2
        st = glow(c, C_STAR, 0.1, 3)
        orbit = Circle(radius=R, color=GREY_B, stroke_width=2).move_to(c)
        th = {"v": PI * 0.85}
        planet = Dot(radius=0.09, color=C_PLANET)

        def run(m, dt):
            th["v"] -= 2 * PI * dt / 2.5
            m.move_to(c + R * np.array([np.cos(th["v"]), np.sin(th["v"]), 0]))

        run(planet, 0)
        planet.add_updater(run)
        per = T("one orbit: about 11 days", 28, C_DIM).move_to(UP * 3.2)
        self.play(FadeIn(st), Create(orbit), FadeIn(planet), FadeIn(per), run_time=1.0)
        self.wait(2.6)
        planet.remove_updater(run)
        a0 = PI * 0.3
        a1 = a0 - 2 * PI * 3 / 11.2
        self.play(planet.animate.move_to(c + R * np.array([np.cos(a0), np.sin(a0), 0])), run_time=0.6)
        p0 = planet.copy().set_color(WHITE)
        l0 = T("arrival", 24).next_to(p0, UL, buff=0.1)
        arc = Arc(radius=R + 0.35, start_angle=a0, angle=a1 - a0, color=C_MARK, stroke_width=4).move_arc_center_to(c)
        arc.add_tip(tip_length=0.18)
        l1 = T("3 days later", 24, C_MARK).move_to(c + (R + 1.35) * np.array([np.cos((a0 + a1) / 2),
                                                                             np.sin((a0 + a1) / 2), 0]))
        self.add(p0)
        self.play(FadeIn(l0), Create(arc), FadeIn(l1),
                  planet.animate.move_to(c + R * np.array([np.cos(a1), np.sin(a1), 0])), run_time=1.6)
        self.done()

        # 7.5 24 launch times over one orbit
        self.beat()
        ticks = VGroup()
        for k in range(24):
            a = PI / 2 - 2 * PI * k / 24
            ticks.add(Line(c + (R - 0.16) * np.array([np.cos(a), np.sin(a), 0]),
                           c + (R + 0.16) * np.array([np.cos(a), np.sin(a), 0]), color=WHITE, stroke_width=3))
        t24 = T("24 launch times over one orbit", 30).move_to(DOWN * 2.45 + LEFT * 0.0)
        rule = T("the rule must hold at all 24", 26, C_DIM).move_to(UP * 3.2)
        self.play(FadeOut(VGroup(p0, l0, arc, l1)), ReplacementTransform(per, rule),
                  LaggedStart(*[Create(t) for t in ticks], lag_ratio=0.06), run_time=1.6)
        self.play(FadeIn(t24), run_time=0.5)
        self.done()

        # 7.6 smallest test radius with a definite earliest launch year
        self.beat()
        orbit_grp = VGroup(st, orbit, planet, ticks)
        self.play(FadeOut(VGroup(t24, rule)), orbit_grp.animate.scale(0.32).move_to([5.5, 2.75, 0]), run_time=0.9)
        ax = LogAxis(y=-0.9)
        m = mark_on(ax, 1e5, h=0.75, label="mark", size=24)
        f1 = VGroup(Dot(ax.p(3.16e5, 0.35), radius=0.11, color=C_FUT),
                    T("316,000 km", 26, C_FUT).move_to(ax.p(3.16e5, 1.55)),
                    T("at 1/5 c", 24, C_DIM).move_to(ax.p(3.16e5, 1.15)))
        f2 = VGroup(Dot(ax.p(5.62e5, 0.35), radius=0.11, color=C_FUT, fill_opacity=0.6),
                    T("562,000 km", 26, C_FUT).move_to(ax.p(5.62e5, 0.75) + RIGHT * 1.35),
                    T("at 1/10 c", 24, C_DIM).move_to(ax.p(5.62e5, 0.35) + RIGHT * 1.35))
        head = T("smallest test radius with a definite earliest launch year", 30).move_to(UP * 2.15 + LEFT * 0.8)
        sub = T("(the rule holds at all 24 launch times)", 24, C_DIM).next_to(head, DOWN, buff=0.12)
        self.play(FadeIn(ax), Create(m[0]), FadeIn(m[1]), run_time=0.9)
        self.play(FadeIn(head), FadeIn(sub), run_time=0.8)
        self.play(GrowFromCenter(f1[0]), FadeIn(f1[1:]), run_time=0.8)
        self.wait(1.6)
        self.play(GrowFromCenter(f2[0]), FadeIn(f2[1:]), run_time=0.8)
        self.done()

        # 7.7 at 100,000 km, no definite year over the orbit
        self.beat()
        und = VGroup(RoundedRectangle(corner_radius=0.12, width=8.6, height=0.7, color=C_UND, fill_opacity=0.15,
                                      stroke_width=2),
                     T("at 100,000 km: no definite earliest year over the orbit", 26, WHITE)).move_to(DOWN * 2.45)
        self.play(FadeIn(und), Indicate(m[0], color=C_UND, scale_factor=1.0), run_time=1.2)
        self.done()

        # 7.8 one example: the largest r90 moves between about 83,000 and 144,000 km
        self.beat()
        self.play(FadeOut(VGroup(ax, m, f1, f2, head, sub, und)),
                  orbit_grp.animate.scale(1 / 0.32 * 0.75).move_to([-4.2, 0.2, 0]), run_time=0.9)
        cc = np.array([2.6, 0.2, 0])
        u = 1.45 / 100000  # scene units per km
        mark_c = DashedVMobject(Circle(radius=1e5 * u, color=C_MARK, stroke_width=4), num_dashes=40).move_to(cc)
        mark_l = T("mark: 100,000 km", 24, C_MARK).move_to(cc + np.array([0, 2.5, 0]))
        vt = ValueTracker(83079.5)
        rc = always_redraw(lambda: Circle(radius=vt.get_value() * u, color=WHITE, stroke_width=3).move_to(cc))
        lo = M(f"largest {R90}: 83,000 to 144,000 km", 26).move_to(DOWN * 2.45 + RIGHT * 2.3)
        ex = T("one example from the paper: launch in 2045 at 1/5 c", 22, C_DIM).move_to(UP * 3.3 + RIGHT * 2.0)
        hl = Dot(radius=0.07, color=C_MARK)
        cen = st.get_center()
        rr = orbit.width / 2

        def at_tick(k):
            a = PI / 2 - 2 * PI * k / 24
            return cen + rr * np.array([np.cos(a), np.sin(a), 0])

        hl.move_to(at_tick(0))
        self.play(Create(mark_c), FadeIn(mark_l), FadeIn(rc), FadeIn(ex), FadeIn(hl), run_time=1.0)
        self.play(FadeIn(lo), run_time=0.5)
        k = ValueTracker(0)
        hl.add_updater(lambda m_: m_.move_to(at_tick(k.get_value())))
        # Only the two end values come from the paper; the path between them is drawn for illustration.
        self.play(k.animate.set_value(12), vt.animate.set_value(144155.0), run_time=3.2, rate_func=smooth)
        self.play(k.animate.set_value(24), vt.animate.set_value(83079.5), run_time=3.2, rate_func=smooth)
        hl.clear_updaters()
        self.done()

        # 7.9 the six settings checked over the orbit
        self.beat()
        six = VGroup(
            T("the 6 settings checked over the orbit combine", 30),
            VGroup(T("pictures of the planet", 28, C_FUT), T("+  much more precise Gaia data", 28, C_FUT),
                   T("+  much more precise speeds of the star toward us", 28, C_FUT)
                   ).arrange(DOWN, buff=0.2, aligned_edge=LEFT),
        ).arrange(DOWN, buff=0.45).move_to(DOWN * 0.2)
        self.play(FadeOut(VGroup(mark_c, mark_l, rc, lo, ex, hl, orbit_grp)), run_time=0.7)
        self.play(FadeIn(six[0]), run_time=0.6)
        self.play(FadeIn(six[1], shift=UP * 0.1), run_time=0.8)
        self.done()

        # 7.10 at one launch time per year they reach 100,000 km at 1/5 c
        self.beat()

        def mini_orbit(pos, nt):
            o = Circle(radius=0.9, color=GREY_B, stroke_width=2)
            ts = VGroup()
            for j in range(nt):
                a = PI / 2 - 2 * PI * j / nt
                ts.add(Line(0.75 * np.array([np.cos(a), np.sin(a), 0]), 1.05 * np.array([np.cos(a), np.sin(a), 0]),
                            color=WHITE, stroke_width=3))
            return VGroup(o, ts, glow(ORIGIN, C_STAR, 0.05, 2)).move_to(pos)

        left = mini_orbit([-3.6, 0.9, 0], 1)
        right = mini_orbit([3.6, 0.9, 0], 24)
        l_t = VGroup(T("one launch time per year", 26), T("100,000 km reached at 1/5 c", 26, C_FUT)) \
            .arrange(DOWN, buff=0.15).next_to(left, DOWN, buff=0.35)
        r_t = VGroup(T("24 launch times over one orbit", 26), T("no definite year at 100,000 km", 26, C_UND)) \
            .arrange(DOWN, buff=0.15).next_to(right, DOWN, buff=0.35)
        self.play(FadeOut(six), run_time=0.5)
        self.play(FadeIn(left), FadeIn(l_t), run_time=0.9)
        self.wait(1.2)
        self.play(FadeIn(right), FadeIn(r_t), run_time=0.9)
        self.done()

        # 7.11 without pictures of the planet: not below 10 million km
        self.beat()
        self.play(FadeOut(VGroup(left, right, l_t, r_t)), run_time=0.5)
        ax = LogAxis(y=-0.9)
        m = mark_on(ax, 1e5, h=0.75, label="mark", size=24)
        no = VGroup(Line(ax.p(1e7, -0.2), ax.p(1e7, 0.9), color=C_UND, stroke_width=6),
                    T("without pictures of the planet:", 26, C_UND).move_to(ax.p(1e7, 1.85) + LEFT * 1.6),
                    T("not below 10 million km", 26, C_UND).move_to(ax.p(1e7, 1.4) + LEFT * 1.6))
        self.play(FadeIn(ax), FadeIn(m), run_time=0.8)
        self.play(Create(no[0]), FadeIn(no[1:]), run_time=0.9)
        self.done(extra=0.2)
        self.fade_all(0.6)


class S8(Beats):
    SID = "s8"

    def construct(self):
        # 8.1
        self.beat()
        title = T("What the paper does not claim", 44).move_to(UP * 3.1)
        self.play(Write(title), run_time=1.0)
        self.done()

        def item(icon, l1, l2, y):
            icon.move_to([-5.3, y, 0])
            t1 = M(l1, 30).move_to([0.6, y + 0.25, 0]).align_to([-4.4, 0, 0], LEFT)
            t2 = M(l2, 24, C_DIM).next_to(t1, DOWN, buff=0.15, aligned_edge=LEFT)
            return VGroup(icon, t1, t2)

        # 8.2 calibration not verified
        self.beat()
        ic = VGroup(Circle(radius=0.38, color=WHITE, stroke_width=3), T("90%?", 20))
        it1 = item(ic, f"The {R90} values come from the model.",
                   "Their calibration has not been verified: no one has yet confirmed\n"
                   "that a 90% circle holds the true position 90% of the time.", 1.45)
        self.play(FadeIn(it1[0]), FadeIn(it1[1]), run_time=0.8)
        self.wait(1.8)
        self.play(FadeIn(it1[2]), run_time=0.8)
        self.done()

        # 8.3 performances are assumptions
        self.beat()
        ic2 = VGroup(RoundedRectangle(corner_radius=0.08, width=0.7, height=0.55, color=WHITE, stroke_width=3),
                     Circle(radius=0.14, color=WHITE, stroke_width=3))
        it2 = item(ic2, "Future instrument performances are assumptions.",
                   "The paper does not claim that the observations will be made.", -0.25)
        self.play(FadeIn(it2), run_time=0.9)
        self.done()

        # 8.4 no statement on missions or life
        self.beat()
        ic3 = cross(0.5, C_DIM)
        it3 = item(ic3, "Nothing about whether or when a mission is possible,",
                   "and nothing about life on the planet.", -1.75)
        self.play(FadeIn(it3), run_time=0.9)
        self.done(extra=0.2)
        self.fade_all(0.6)


class S9(Beats):
    SID = "s9"

    def construct(self):
        # 9.1 the size of the gap and which observations come closest
        self.beat()
        ax = LogAxis(y=-0.6)
        m = mark_on(ax, 1e5, h=0.75, label="mark", size=24)
        band = Line(ax.p(7.2e6, 0.35), ax.p(9.45e6, 0.35), color=C_TODAY, stroke_width=16)
        today = T("today", 26, C_TODAY).move_to(ax.p(8.2e6, 0.95))
        f1 = Dot(ax.p(3.16e5, 0.35), radius=0.11, color=C_FUT)
        f2 = Dot(ax.p(5.62e5, 0.35), radius=0.11, color=C_FUT, fill_opacity=0.6)
        fut = T("smallest values with declared future observations", 24, C_FUT).move_to(ax.p(4.2e5, 1.55))
        gap = DoubleArrow(ax.p(1e5, -1.1), ax.p(7.2e6, -1.1), buff=0.05, color=WHITE, stroke_width=3,
                          tip_length=0.18)
        head = T("a measure of the gap, not a mission plan", 36).move_to(UP * 2.6)
        self.play(FadeIn(ax), FadeIn(m), Create(band), FadeIn(today), run_time=1.0)
        self.play(FadeIn(f1), FadeIn(f2), FadeIn(fut), GrowFromCenter(gap), run_time=1.0)
        self.play(Write(head), run_time=1.2)
        self.done()

        # 9.2 open on Zenodo
        self.beat()
        z = VGroup(T("Paper, data, and scripts: open on Zenodo", 32),
                   T("doi.org/10.5281/zenodo.23501923", 30, C_FUT)).arrange(DOWN, buff=0.3).move_to(UP * 0.3)
        self.play(FadeOut(VGroup(ax, m, band, today, f1, f2, fut, gap)), head.animate.set_opacity(0.0),
                  run_time=0.6)
        self.play(FadeIn(z), run_time=0.8)
        self.done()

        # 9.3 credits
        self.beat()
        cr = VGroup(T("Made with the help of AI (Claude, by Anthropic)", 26, C_DIM),
                    T("Synthetic voice: Kokoro-82M  ·  Animation: Manim Community Edition", 26, C_DIM)) \
            .arrange(DOWN, buff=0.2).move_to(DOWN * 1.5)
        self.play(FadeIn(cr), run_time=0.8)
        self.done(extra=1.0)
        self.play(FadeOut(VGroup(z, cr)), run_time=0.8)
