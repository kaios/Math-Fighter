"""Procedural anime-style fighter sprites.

Each fighter is a jointed rig (torso, head, two-bone arms and legs) drawn
with outlined, cel-shaded shapes. Poses are small dicts of joint values and
animations ease between them every frame, so motion is perfectly smooth at
any frame rate or screen size. Legs use inverse kinematics so feet stay
planted on the ground.
"""

import math

import pygame

from .draw import Pen, darker, fill_circle, lighter, mix

# ----------------------------------------------------------------------------
# Poses. Angles in degrees: 0 = hanging straight down, positive = forward.
#   x      lunge offset (px)        hy        hip height
#   torso  body lean                head      extra head tilt
#   saf/eaf front shoulder/elbow    sab/eab   back shoulder/elbow
#   ffx/ffy front foot target       fbx/fby   back foot target
# ----------------------------------------------------------------------------

STANCE = dict(x=0, hy=106, torso=8, head=-2, saf=40, eaf=110, sab=20, eab=120,
              ffx=30, ffy=0, fbx=-42, fby=0)


def P(**kw):
    p = dict(STANCE)
    p.update(kw)
    return p


POSES = {
    "stance": P(),
    "idle_b": P(hy=101, torso=10, saf=44, eaf=106, sab=23, eab=116),
    "stand": P(hy=118, torso=0, head=0, saf=8, eaf=12, sab=4, eab=16, ffx=12, fbx=-12),
    "walk1": P(hy=104, ffx=46, fbx=-22, ffy=0, fby=10),
    "walk2": P(hy=106, ffx=8, fbx=-52, ffy=10, fby=0),
    "punch_wind": P(x=-8, hy=102, torso=0, saf=12, eaf=135, sab=30, eab=110, ffx=32, fbx=-44),
    "punch": P(x=140, hy=100, torso=20, head=-6, saf=70, eaf=2, sab=-35, eab=120, ffx=58, fbx=-62),
    "punch2": P(x=145, hy=100, torso=18, head=-6, saf=-10, eaf=125, sab=72, eab=0, ffx=55, fbx=-58),
    "kick_wind": P(x=30, hy=110, torso=-6, ffx=40, ffy=58, fbx=-22),
    "kick": P(x=100, hy=114, torso=-24, head=10, saf=30, eaf=100, sab=-25, eab=90,
              ffx=128, ffy=92, fbx=-26),
    "special_wind": P(x=-15, hy=98, torso=-10, saf=-40, eaf=100, sab=-50, eab=100, ffx=42, fbx=-56),
    "special": P(x=20, hy=96, torso=15, head=-8, saf=78, eaf=5, sab=74, eab=12, ffx=62, fbx=-70),
    "upper_wind": P(x=45, hy=86, torso=26, saf=10, eaf=120, sab=30, eab=110, ffx=38, fbx=-52),
    "uppercut": P(x=130, hy=122, torso=-8, head=-12, saf=165, eaf=12, sab=-20, eab=100,
                  ffx=34, ffy=34, fbx=-24),
    "charge_a": P(x=-10, hy=92, torso=10, head=4, saf=-15, eaf=100, sab=-25, eab=95, ffx=48, fbx=-62),
    "charge_b": P(x=-10, hy=89, torso=12, head=6, saf=-19, eaf=106, sab=-29, eab=100, ffx=48, fbx=-62),
    "hit": P(x=-55, hy=104, torso=-24, head=-22, saf=-20, eaf=40, sab=-45, eab=30,
             ffx=18, ffy=12, fbx=-55),
    "block": P(x=-12, hy=100, torso=-4, head=8, saf=70, eaf=122, sab=80, eab=115, ffx=26, fbx=-50),
    "dodge": P(x=-75, hy=100, torso=-32, head=-10, saf=10, eaf=110, sab=0, eab=120, ffx=12, fbx=-46),
    "fall": P(x=-130, hy=72, torso=-62, head=-15, saf=130, eaf=10, sab=150, eab=20,
              ffx=40, ffy=55, fbx=10, fby=34),
    "down": P(x=-150, hy=18, torso=-80, head=-4, saf=-18, eaf=12, sab=175, eab=-15,
              ffx=108, ffy=12, fbx=96, fby=18),
    "victory": P(hy=114, torso=0, head=-8, saf=145, eaf=28, sab=-40, eab=95, ffx=22, fbx=-28),
    "victory_b": P(hy=116, torso=-2, head=-12, saf=150, eaf=22, sab=-40, eab=95, ffx=22, fbx=-28),
    "victory_v": P(hy=114, torso=0, head=-10, saf=160, eaf=12, sab=198, eab=-12, ffx=20, fbx=-26),
    "victory_v2": P(hy=117, torso=-2, head=-14, saf=166, eaf=6, sab=192, eab=-6, ffx=20, fbx=-26),
    "victory_cross": P(hy=114, torso=0, head=4, saf=62, eaf=132, sab=55, eab=128, ffx=20, fbx=-30),
    "victory_cross2": P(hy=115, torso=-2, head=8, saf=64, eaf=130, sab=57, eab=126, ffx=20, fbx=-30),
}

VICTORY = {
    "kai": ("victory", "victory_b"),
    "mira": ("victory_v", "victory_v2"),
    "luna": ("victory_cross", "victory_cross2"),
    "dax": ("victory_cross", "victory_cross2"),
}


def smooth(t):
    return t * t * (3 - 2 * t)


def ease_out(t):
    return 1 - (1 - t) ** 3


# Animation = (frames, loop, next_anim). Frame = (pose, seconds, event, ease)
def _a(frames, loop=False, nxt="idle"):
    out = []
    for f in frames:
        pose, dur = f[0], f[1]
        event = f[2] if len(f) > 2 else None
        ease = f[3] if len(f) > 3 else smooth
        out.append((pose, dur, event, ease))
    return out, loop, nxt


ANIMS = {
    "idle": _a([("idle_b", 0.6), ("stance", 0.6)], loop=True),
    "walk": _a([("walk1", 0.22), ("walk2", 0.22)], loop=True),
    "stand": _a([("stand", 0.3)], nxt=None),
    "charge": _a([("charge_a", 0.25), ("charge_b", 0.25)], loop=True),
    "punch": _a([("punch_wind", 0.13), ("punch", 0.08, "hit", ease_out), ("punch", 0.22),
                 ("stance", 0.28)]),
    "kick": _a([("kick_wind", 0.15), ("kick", 0.09, "hit", ease_out), ("kick", 0.24),
                ("stance", 0.32)]),
    "combo": _a([("punch_wind", 0.1), ("punch", 0.07, "jab", ease_out), ("punch_wind", 0.09),
                 ("punch2", 0.07, "jab", ease_out), ("kick_wind", 0.11),
                 ("kick", 0.08, "hit", ease_out), ("kick", 0.22), ("stance", 0.3)]),
    "special": _a([("special_wind", 0.28), ("special", 0.1, "fire", ease_out), ("special", 0.45),
                   ("stance", 0.3)]),
    "uppercut": _a([("upper_wind", 0.1), ("uppercut", 0.1, "hit", ease_out), ("uppercut", 0.25),
                    ("stance", 0.3)]),
    "hit": _a([("hit", 0.07, None, ease_out), ("hit", 0.22), ("stance", 0.3)]),
    "block": _a([("block", 0.07, None, ease_out), ("block", 0.35), ("stance", 0.25)]),
    "dodge": _a([("dodge", 0.12, None, ease_out), ("dodge", 0.3), ("stance", 0.3)]),
    "ko": _a([("hit", 0.08, None, ease_out), ("fall", 0.35), ("down", 0.3, "land", ease_out)],
             nxt=None),
}


class Animator:
    def __init__(self, victory=("victory", "victory_b")):
        self.pose = dict(STANCE)
        self.anims = dict(ANIMS)
        self.anims["victory"] = _a([("stance", 0.15), (victory[0], 0.35), (victory[1], 0.5),
                                    (victory[0], 0.5)], nxt="victory_loop")
        self.anims["victory_loop"] = _a([(victory[1], 0.5), (victory[0], 0.5)], loop=True)
        self.name = None
        self.play("idle")

    def play(self, name):
        self.name = name
        self.frames, self.loop, self.nxt = self.anims[name]
        self.i, self.t = 0, 0.0
        self.start = dict(self.pose)

    @property
    def done(self):
        return self.i >= len(self.frames)

    def update(self, dt):
        events = []
        while dt > 0 and not self.done:
            pose_name, dur, event, ease = self.frames[self.i]
            step = min(dt, dur - self.t)
            self.t += step
            dt -= step
            k = ease(min(1.0, self.t / dur)) if dur > 0 else 1.0
            target = POSES[pose_name]
            self.pose = {key: self.start[key] + (target[key] - self.start[key]) * k
                         for key in target}
            if self.t >= dur - 1e-9:
                if event:
                    events.append(event)
                self.start = dict(target)
                self.i += 1
                self.t = 0.0
                if self.done:
                    if self.loop:
                        self.i = 0
                    elif self.nxt:
                        self.play(self.nxt)
                    else:
                        break
            if step <= 0:
                break
        return events


# ----------------------------------------------------------------------------
# Rig geometry
# ----------------------------------------------------------------------------

def _dir(deg):
    a = math.radians(deg)
    return math.sin(a), math.cos(a)


def _add(p, v, k=1.0):
    return p[0] + v[0] * k, p[1] + v[1] * k


def _ik(hip, target, a, b):
    dx, dy = target[0] - hip[0], target[1] - hip[1]
    d = math.hypot(dx, dy) or 0.001
    ux, uy = dx / d, dy / d
    dc = max(abs(a - b) + 1, min(a + b - 0.5, d))
    ankle = (hip[0] + ux * dc, hip[1] + uy * dc)
    ca = max(-1.0, min(1.0, (a * a + dc * dc - b * b) / (2 * a * dc)))
    ang = math.acos(ca)
    side = (uy, -ux)  # knees bend toward the front
    best = None
    for s in (ang, -ang):
        kx = hip[0] + a * (ux * math.cos(s) - uy * math.sin(s))
        ky = hip[1] + a * (ux * math.sin(s) + uy * math.cos(s))
        score = (kx - hip[0]) * side[0] + (ky - hip[1]) * side[1]
        if best is None or score > best[0]:
            best = (score, (kx, ky))
    return best[1], ankle


# Hair outlines in head space (unit = head radius, +x = facing direction).
HAIR = {
    "spiky": [(-0.95, 0.6), (-1.3, 0.38), (-1.02, 0.08), (-1.55, -0.32), (-1.02, -0.5),
              (-1.35, -1.05), (-0.62, -0.95), (-0.6, -1.6), (-0.12, -1.06), (0.25, -1.62),
              (0.46, -0.98), (1.0, -1.28), (0.86, -0.62), (1.34, -0.46), (0.98, -0.2),
              (1.02, 0.08), (0.74, -0.2), (0.56, 0.18), (0.38, -0.22), (0.16, 0.08),
              (-0.06, -0.28), (-0.36, -0.1), (-0.52, 0.32), (-0.7, 0.58)],
    "swept": [(-0.85, 0.62), (-1.2, 0.45), (-1.0, 0.2), (-1.62, 0.0), (-1.05, -0.3),
              (-1.65, -0.58), (-0.95, -0.78), (-1.32, -1.1), (-0.45, -1.06), (0.1, -1.2),
              (0.62, -1.12), (1.05, -0.75), (1.14, -0.34), (0.96, -0.12), (1.04, 0.32),
              (0.8, -0.04), (0.52, -0.28), (0.2, -0.34), (-0.2, -0.3), (-0.5, 0.25),
              (-0.62, 0.62)],
    "long": [(-0.98, 0.5), (-1.08, -0.2), (-0.85, -0.85), (-0.32, -1.14), (0.3, -1.14),
             (0.82, -0.86), (1.07, -0.35), (1.04, 0.1), (0.9, -0.02), (0.76, -0.12),
             (0.62, 0.0), (0.47, -0.12), (0.32, 0.0), (0.16, -0.14), (-0.1, -0.16),
             (-0.24, 0.12), (-0.18, 1.0), (-0.42, 1.08), (-0.6, 0.5), (-0.85, 0.55)],
    "twintails": [(-0.96, 0.45), (-1.07, -0.2), (-0.85, -0.85), (-0.32, -1.14), (0.3, -1.14),
                  (0.82, -0.86), (1.07, -0.35), (1.04, 0.05), (0.88, -0.1), (0.78, 0.1),
                  (0.62, -0.16), (0.44, 0.02), (0.28, -0.2), (0.08, -0.06), (-0.12, -0.22),
                  (-0.28, 0.1), (-0.3, 0.58), (-0.5, 0.66), (-0.62, 0.35), (-0.84, 0.5)],
}

FACE = ([(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(160, 385, 15)]
        + [(0.93, 0.52), (0.72, 0.84), (0.42, 1.02), (0.1, 0.98), (-0.35, 0.8), (-0.75, 0.55)])


class Rig:
    def __init__(self, fd):
        self.fd = fd
        self.style = fd.key.replace("shadow_", "")
        h = fd.height
        fem = fd.female
        self.h = h
        self.L = dict(thigh=62 * h, shin=62 * h, torso=(83 if fem else 88) * h, neck=9 * h,
                      uarm=(47 if fem else 50) * h, farm=(45 if fem else 48) * h)
        self.R = 37 * (0.97 if fem else 1.0) * (1 + (h - 1) * 0.5)
        self.points = {}
        s, f = self.style, fd
        skin = f.skin
        self.col = {
            "uarm": {"mira": skin}.get(s, f.top),
            "farm": {"kai": skin, "luna": f.top2, "mira": f.top2}.get(s, f.top),
            "fist": {"kai": f.top2, "dax": f.boots, "luna": f.top2, "mira": f.top2}[s],
            "thigh": {"mira": skin}.get(s, f.pants),
            "shin": {"mira": f.boots}.get(s, f.pants),
            "boot": {"luna": f.top2}.get(s, f.boots),
        }

    # -- geometry -------------------------------------------------------------
    def solve(self, p):
        L, h = self.L, self.h
        hip = (p["x"], -p["hy"] * h)
        t = p["torso"]
        up = (math.sin(math.radians(t)), -math.cos(math.radians(t)))
        fwd = (-up[1], up[0])
        neck = _add(hip, up, L["torso"])
        J = {"hip": hip, "neck": neck, "up": up, "fwd": fwd, "t": t}
        for side, sx in (("f", 5), ("b", -5)):
            hj = _add(hip, fwd, sx)
            foot = (p["x"] + p["f%sx" % side] * h, -p["f%sy" % side] * h)
            knee, ankle = _ik(hj, foot, L["thigh"], L["shin"])
            J["hip_" + side], J["knee_" + side], J["ankle_" + side] = hj, knee, ankle
            sh = _add(_add(neck, up, -9 * h), fwd, 6 if side == "f" else -4)
            sa = t + p["sa" + side]
            elbow = _add(sh, _dir(sa), L["uarm"])
            hand = _add(elbow, _dir(sa + p["ea" + side]), L["farm"])
            J["sh_" + side], J["elbow_" + side], J["hand_" + side] = sh, elbow, hand
        neck_top = _add(neck, up, L["neck"])
        ht = t + p["head"]
        hu = (math.sin(math.radians(ht)), -math.cos(math.radians(ht)))
        J["neck_top"] = neck_top
        J["ht"] = ht
        J["head"] = _add(neck_top, hu, self.R * 0.95)
        return J

    # -- drawing --------------------------------------------------------------
    def draw(self, surf, ox, oy, facing, scale, pose, t=0.0, flash=0.0, expr="normal", wind=0.0):
        J = self.solve(pose)
        fd, R = self.fd, self.R

        def S(p):
            return (ox + p[0] * scale * facing, oy + p[1] * scale)

        hc = J["head"]
        ca, sa = math.cos(math.radians(J["ht"])), math.sin(math.radians(J["ht"]))

        def HL(x, y):  # head space -> rig space
            x, y = x * R, y * R
            return (hc[0] + x * ca - y * sa, hc[1] + x * sa + y * ca)

        def H(x, y):
            return S(HL(x, y))

        pen = Pen(surf, ol=max(1.4, 2.3 * scale), flash=flash)
        sc = scale
        self.points = {k: S(J[k]) for k in ("hand_f", "hand_b", "head", "neck", "hip",
                                            "ankle_f")}
        self.points["chest"] = S(_add(J["hip"], J["up"], self.L["torso"] * 0.6))

        # ---- back layer: hair, scarves, sashes --------------------------------
        self._back_layer(pen, S, HL, J, t, wind, sc)

        # ---- back leg & arm ---------------------------------------------------
        self._leg(pen, S, J, "b", sc, back=True)
        self._arm(pen, S, J, "b", sc, back=True)

        # ---- torso ------------------------------------------------------------
        self._torso(pen, S, J, sc)

        # ---- front leg, skirt -------------------------------------------------
        self._leg(pen, S, J, "f", sc)
        if self.style == "mira":
            hip, up, fw = J["hip"], J["up"], J["fwd"]
            skirt = [_add(_add(hip, up, 20), fw, 15), _add(_add(hip, up, 20), fw, -15),
                     _add(_add(hip, up, -26), fw, -27), _add(_add(hip, up, -30), fw, -10),
                     _add(_add(hip, up, -27), fw, 6), _add(_add(hip, up, -31), fw, 22),
                     _add(_add(hip, up, -24), fw, 30)]
            pen.poly([S(q) for q in skirt], fd.pants)
            pen.poly([S(_add(_add(hip, up, 20), fw, 15)), S(_add(_add(hip, up, 20), fw, -15)),
                      S(_add(_add(hip, up, 13), fw, -16)), S(_add(_add(hip, up, 13), fw, 16))],
                     fd.accent)

        # ---- head ---------------------------------------------------------
        self._head(pen, S, H, HL, J, sc, expr, t)

        # ---- front arm ------------------------------------------------------
        self._arm(pen, S, J, "f", sc)
        return J

    def _limb_r(self, part):
        fem = self.fd.female
        return {"uarm": (10.0, 8.2) if not fem else (8.2, 6.8),
                "farm": (8.8, 7.2) if not fem else (7.0, 6.0),
                "thigh": (14.5, 11.0) if not fem else (13.0, 9.0),
                "shin": (10.5, 8.0) if not fem else (9.0, 6.8)}[part]

    def _arm(self, pen, S, J, side, sc, back=False):
        col = self.col
        k = 0.86 if back else 1.0
        sh, el, ha = J["sh_" + side], J["elbow_" + side], J["hand_" + side]
        r1, r2 = self._limb_r("uarm")
        r3, r4 = self._limb_r("farm")
        c_u, c_f, c_h = (darker(col[x], k) if back else col[x] for x in ("uarm", "farm", "fist"))
        pen.chain([(S(sh), S(el), r1 * sc, r2 * sc, c_u),
                   (S(el), S(ha), r3 * sc, r4 * sc, c_f)])
        if self.style == "kai":  # sleeve cuff
            pen.capsule(S(_lerp(sh, el, 0.75)), S(el), r2 * sc * 1.15, r2 * sc * 1.1,
                        darker(self.fd.top, k), shade=False)
        if self.style in ("luna", "dax"):
            pen.capsule(S(_lerp(el, ha, 0.45)), S(_lerp(el, ha, 0.92)), r4 * sc * 1.15,
                        r4 * sc * 1.15, darker(self.fd.accent if self.style == "luna"
                                               else self.fd.top2, k), shade=False)
        pen.circle(S(ha), (10.5 if not self.fd.female else 8.5) * sc, c_h)

    def _leg(self, pen, S, J, side, sc, back=False):
        col = self.col
        k = 0.86 if back else 1.0
        hp, kn, an = J["hip_" + side], J["knee_" + side], J["ankle_" + side]
        r1, r2 = self._limb_r("thigh")
        r3, r4 = self._limb_r("shin")
        ct, cs, cb = (darker(col[x], k) if back else col[x] for x in ("thigh", "shin", "boot"))
        # foot
        dx, dy = an[0] - kn[0], an[1] - kn[1]
        d = math.hypot(dx, dy) or 1
        dx, dy = dx / d, dy / d
        fx, fy = dy, -dx
        foot = [_add(_add(an, (fx, fy), -7), (dx, dy), -3), _add(_add(an, (fx, fy), -8), (dx, dy), 9),
                _add(_add(an, (fx, fy), 21), (dx, dy), 9), _add(_add(an, (fx, fy), 22), (dx, dy), 4),
                _add(_add(an, (fx, fy), 6), (dx, dy), -5)]
        pen.chain([(S(hp), S(kn), r1 * sc, r2 * sc, ct), (S(kn), S(an), r3 * sc, r4 * sc, cs)])
        pen.poly([S(q) for q in foot], cb)
        if self.style in ("dax", "mira", "luna"):
            top = _lerp(kn, an, 0.15 if self.style == "mira" else 0.45)
            pen.capsule(S(top), S(an), r4 * sc * 1.12, r4 * sc * 1.05, cb)
        elif self.style == "kai":  # gi pant cuff
            pen.capsule(S(_lerp(kn, an, 0.7)), S(an), r4 * sc * 1.25, r4 * sc * 1.35,
                        darker(ct, 0.92), shade=False)

    def _torso(self, pen, S, J, sc):
        fd, s = self.fd, self.style
        hip, neck, up, fw = J["hip"], J["neck"], J["up"], J["fwd"]
        fem = fd.female
        tl = self.L["torso"]

        wk = 1.12 if fem else 1.22

        def at(u, f):
            return S(_add(_add(hip, up, u * tl), fw, f * wk))

        if fem:
            body = [at(1.0, 11), at(0.8, 19), at(0.62, 17), at(0.4, 11), at(0.15, 15), at(0.0, 17),
                    at(-0.12, 13), at(-0.12, -13), at(0.0, -17), at(0.15, -14), at(0.4, -11),
                    at(0.75, -15), at(1.0, -12)]
        else:
            body = [at(1.0, 14), at(0.84, 21), at(0.55, 16), at(0.3, 13), at(0.0, 16),
                    at(-0.12, 14), at(-0.12, -14), at(0.0, -16), at(0.3, -13), at(0.6, -17),
                    at(0.86, -20), at(1.0, -15)]
        # neck behind torso top
        nt = J["neck_top"]
        pen.chain([(S(neck), S(_add(nt, up, 4)), 7.5 * sc, 7.0 * sc, darker(fd.skin, 0.9))],
                  shade=False)
        pen.poly(body, fd.top)
        # cel shade on the back half
        shade = [at(0.95, -2), at(0.6, -3), at(0.2, -2), at(-0.08, -4), at(-0.1, -12),
                 at(0.0, -15), at(0.3, -12), at(0.6, -15), at(0.86, -18), at(0.98, -13)]
        pen.poly(shade, darker(fd.top, 0.82), outline=False)

        if s == "kai":
            pen.poly([at(1.02, 9), at(1.02, -3), at(0.62, 6)], fd.skin, outline=False)
            pen.poly([at(1.02, 10), at(0.62, 6), at(0.58, 9), at(1.0, 14)], fd.top2, outline=False)
            pen.poly([at(0.3, 14), at(0.3, -14), at(0.18, -14), at(0.18, 14)], (30, 28, 34))
            pen.ribbon([at(0.24, 12), at(0.1, 18), at(-0.05, 15)], [6 * sc, 5 * sc, 3 * sc],
                       (30, 28, 34))
        elif s == "dax":
            pen.poly([at(0.95, 12), at(0.85, 19), at(0.55, 15), at(0.5, 3), at(0.95, 2)],
                     fd.top2)
            pen.poly([at(0.3, 13), at(0.3, -13), at(0.2, -13), at(0.2, 13)], darker(fd.top2, 0.6))
            pen.ribbon([S(_add(neck, up, -2)), at(1.04, 0), S(_add(_add(neck, up, -2), fw, 14))],
                       [11 * sc, 12 * sc, 10 * sc], fd.accent)
        elif s == "luna":
            pen.poly([at(0.98, 10), at(0.8, 17), at(0.5, 9), at(0.5, -4), at(0.98, -3)], fd.top2)
            pen.poly([at(0.33, 12), at(0.33, -12), at(0.18, -14), at(0.18, 14)], fd.accent)
            pen.poly([at(1.04, 10), at(1.04, -11), at(0.92, -12), at(0.92, 12)], darker(fd.top2))
        elif s == "mira":
            pen.poly([at(1.02, 11), at(0.86, 18), at(0.82, 6), at(0.9, -2), at(1.02, -10)], fd.top2)
            pen.circle(at(0.8, 9), 4.5 * sc, fd.accent)

    def _back_layer(self, pen, S, HL, J, t, wind, sc):
        fd, s, R = self.fd, self.style, self.R

        def chain(anchor, base, seg, n, amp, phase, spd=3.0, head=True):
            if head:
                base -= J["ht"] * 0.9
            pts = [anchor]
            p = anchor
            for i in range(1, n + 1):
                k = i / n
                ang = base + amp * math.sin(t * spd + phase - i * 0.6) * k + wind * k
                p = (p[0] - math.sin(math.radians(ang)) * seg, p[1] + math.cos(math.radians(ang)) * seg)
                pts.append(p)
            return [S(q) for q in pts]

        if s == "kai":
            a = HL(-0.95, -0.36)
            for ph, base in ((0.0, 72), (1.3, 92)):
                pts = chain(a, base, 8 * self.h, 5, 18, ph, 6.0)
                pen.ribbon(pts, [6 * sc, 7 * sc, 6 * sc, 5 * sc, 4 * sc, 2 * sc], fd.accent)
        elif s == "dax":
            a = _add(J["neck"], J["fwd"], -8)
            pts = chain(a, 62, 12 * self.h, 6, 14, 0.0, 4.0, head=False)
            pen.ribbon(pts, [w * sc for w in (12, 13, 13, 12, 11, 10, 7)], darker(fd.accent, 0.88))
        elif s == "luna":
            a = HL(-0.45, -0.35)
            pts = chain(a, 10, 0.78 * R, 6, 7, 0.0, 2.2)
            ws = [w * R * sc for w in (1.75, 1.6, 1.45, 1.25, 1.0, 0.65, 0.12)]
            pen.ribbon(pts, ws, darker(fd.hair, 0.82))
            sash = _add(_add(J["hip"], J["up"], 0.25 * self.L["torso"]), J["fwd"], -12)
            for ph, base in ((0.0, 60), (1.7, 80)):
                pts = chain(sash, base, 10 * self.h, 5, 16, ph, 5.0, head=False)
                pen.ribbon(pts, [w * sc for w in (7, 8, 8, 7, 5, 2)], fd.accent)
        elif s == "mira":
            for anchor, base, ph, k in (((-0.2, -0.95), 34, 1.1, 0.85), ((-0.62, -0.72), 20, 0.0, 1.0)):
                a = HL(*anchor)
                pts = chain(a, base, 0.62 * R, 6, 13, ph, 3.4)
                ws = [w * R * sc for w in (0.42, 0.66, 0.74, 0.68, 0.54, 0.34, 0.06)]
                pen.ribbon(pts, ws, darker(fd.hair, 0.86 * k + 0.1))

    def _head(self, pen, S, H, HL, J, sc, expr, t):
        fd, s = self.fd, self.style
        fem = fd.female
        # face
        pen.poly([H(x, y) for x, y in FACE], fd.skin)
        # jaw shadow under the hair line / neck side
        pen.poly([H(-0.75, 0.55), H(-0.35, 0.8), H(0.0, 0.92), H(-0.1, 0.6), H(-0.6, 0.35)],
                 darker(fd.skin, 0.9), outline=False)
        # ear
        pen.poly([H(-0.42 + 0.12 * math.cos(a), 0.3 + 0.2 * math.sin(a))
                  for a in [i * math.pi / 6 for i in range(12)]], fd.skin)
        self._eyes(pen, H, expr, t)
        # nose & mouth
        pen.poly([H(0.86, 0.38), H(0.94, 0.5), H(0.84, 0.52)], darker(fd.skin, 0.75), outline=False)
        self._mouth(pen, H, expr)
        if fem and not fd.shadow:
            for cx in (0.18, 0.72):
                pts = [H(cx + 0.13 * math.cos(a), 0.58 + 0.06 * math.sin(a))
                       for a in [i * math.pi / 6 for i in range(12)]]
                pen.poly(pts, mix(fd.skin, (255, 110, 130), 0.35), outline=False)
        # hair
        hair = HAIR[fd.hair_style]
        pen.poly([H(x, y) for x, y in hair], fd.hair)
        shine = [H(0.8 * math.cos(math.radians(a)), 0.8 * math.sin(math.radians(a)))
                 for a in range(215, 300, 12)]
        shine += [H(0.62 * math.cos(math.radians(a)), 0.62 * math.sin(math.radians(a)))
                  for a in range(295, 210, -12)]
        pen.poly(shine, lighter(fd.hair, 0.4), outline=False)
        if s == "kai":
            band = [H(-1.04, -0.5), H(-0.3, -0.82), H(0.5, -0.78), H(1.02, -0.42),
                    H(1.04, -0.2), H(0.5, -0.54), H(-0.3, -0.58), H(-1.04, -0.26)]
            pen.poly(band, fd.accent)
            pen.circle(H(0.35, -0.62), 0.11 * self.R * sc, (240, 240, 245))
        elif s == "mira":
            for x, y in ((-0.2, -0.95), (-0.62, -0.72)):
                self._star(pen, H(x, y), 0.26 * self.R * sc, fd.accent, t)
        elif s == "luna":
            pen.poly([H(-0.8, -0.82), H(-0.45, -1.02), H(-0.38, -0.86), H(-0.72, -0.66)],
                     fd.accent)

    def _star(self, pen, c, r, color, t):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5 + t * 0.6
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
        pen.poly(pts, color)

    def _ellipse(self, H, cx, cy, rx, ry, n=16):
        return [H(cx + rx * math.cos(a), cy + ry * math.sin(a))
                for a in [i * 2 * math.pi / n for i in range(n)]]

    def _eyes(self, pen, H, expr, t):
        fd = self.fd
        fem = fd.female
        ink = pen.ink
        w, h = (0.2, 0.3) if fem else (0.18, 0.24)
        # blink every few seconds
        blink = (t % 3.7) < 0.12 and expr == "normal"
        for cx, kw in ((0.2, 1.0), (0.7, 0.72)):
            cy = 0.24
            ew = w * kw
            if expr in ("hurt", "ko"):
                pts = [H(cx - ew, cy - 0.1), H(cx + ew * 0.6, cy), H(cx - ew, cy + 0.1)]
                if cx > 0.5:
                    pts = [H(cx + ew, cy - 0.1), H(cx - ew * 0.6, cy), H(cx + ew, cy + 0.1)]
                pygame_lines(pen, pts, 0.05 * self.R)
                continue
            if expr == "happy" or blink:
                k = -1 if expr == "happy" else 1
                pts = [H(cx - ew, cy + 0.02 * k), H(cx, cy - 0.07 * k), H(cx + ew, cy + 0.02 * k)]
                pygame_lines(pen, pts, 0.05 * self.R)
                continue
            if fd.shadow:
                pen.poly(self._ellipse(H, cx, cy, ew, h * 0.7), (255, 40, 60), outline=True)
                pen.poly(self._ellipse(H, cx, cy, ew * 0.45, h * 0.35), (255, 230, 230),
                         outline=False)
                continue
            pen.poly(self._ellipse(H, cx, cy, ew, h), (255, 255, 255), outline=False)
            ix = cx + ew * 0.18
            pen.poly(self._ellipse(H, ix, cy + h * 0.1, ew * 0.72, h * 0.8), darker(fd.eyes, 0.7),
                     outline=False)
            pen.poly(self._ellipse(H, ix, cy + h * 0.25, ew * 0.6, h * 0.55), fd.eyes, outline=False)
            pen.poly(self._ellipse(H, ix, cy + h * 0.12, ew * 0.3, h * 0.38), (20, 15, 30),
                     outline=False)
            pen.poly(self._ellipse(H, ix - ew * 0.25, cy - h * 0.25, ew * 0.22, h * 0.18, 10),
                     (255, 255, 255), outline=False)
            pen.poly(self._ellipse(H, ix + ew * 0.25, cy + h * 0.45, ew * 0.12, h * 0.09, 8),
                     (255, 255, 255), outline=False)
            # upper lash
            lash = [H(cx + ew * 1.1 * math.cos(a), cy + h * 1.05 * math.sin(a))
                    for a in [math.radians(d) for d in range(195, 350, 15)]]
            th = 0.09 if fem else 0.07
            lash += [H(cx + ew * 0.95 * math.cos(a), cy + (h - th) * math.sin(a))
                     for a in [math.radians(d) for d in range(345, 190, -15)]]
            if fem:
                lash.insert(len(lash) // 2, H(cx + ew * 1.35, cy - h * 0.55))
            pen.poly(lash, ink, outline=False)
        # brows
        angry = expr in ("angry",)
        for cx, kw in ((0.2, 1.0), (0.7, 0.72)):
            ew = w * kw
            y0 = 0.24 - h - 0.12
            tilt = 0.1 if angry else -0.02
            if cx < 0.5:
                pts = [H(cx - ew, y0 - tilt * 0.3), H(cx + ew, y0 + tilt)]
            else:
                pts = [H(cx - ew, y0 + tilt), H(cx + ew, y0 - tilt * 0.3)]
            pygame_lines(pen, pts, (0.035 if fem else 0.05) * self.R, darker(fd.hair, 0.55))

    def _mouth(self, pen, H, expr):
        if expr in ("angry", "hurt", "ko"):
            pts = [H(0.42, 0.68), H(0.66, 0.66), H(0.62, 0.82), H(0.48, 0.84)]
            pen.poly(pts, (110, 30, 40))
            pen.poly([H(0.47, 0.8), H(0.6, 0.79), H(0.58, 0.83), H(0.49, 0.84)], (230, 90, 100),
                     outline=False)
        elif expr == "happy":
            pts = [H(0.38, 0.66), H(0.7, 0.64), H(0.6, 0.82), H(0.46, 0.82)]
            pen.poly(pts, (150, 40, 50))
        else:
            pygame_lines(pen, [H(0.46, 0.72), H(0.62, 0.71)], 0.03 * self.R)


def _lerp(a, b, k):
    return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k


def pygame_lines(pen, pts, width, color=None):
    w = max(1, int(round(width * pen.ol / 2.3 * 2)))
    color = color or pen.ink
    ip = [(int(round(x)), int(round(y))) for x, y in pts]
    pygame.draw.lines(pen.surf, color, False, ip, w)
    for q in (ip[0], ip[-1]):
        fill_circle(pen.surf, q, w / 2, color)
