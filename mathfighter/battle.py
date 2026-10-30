"""The fight itself: rounds, math questions, attacks, blocks, counters and KOs."""

import math
import random

import pygame

from .config import (ANSWER_TIME, BONUS_LEVEL, BOSS_ANSWER_TIME, COUNTER_WINDOW, CPU_HOME_X,
                     FRACTION_ANSWER_TIME, GOLD, GREEN, GROUND_Y, H, MAX_HITS, PLAYER_HOME_X, RED,
                     ROUND_TIME, ROUNDS_TO_WIN, SPECIAL_DAMAGE, SPECIAL_WINDOW, SUPER_WINDOW, TURN_PAUSE,
                     W, WHITE)
from .draw import QUALITY, fill_circle, lighter, soft_shadow
from .effects import Effects
from .mathq import DISPLAY, OP_NAMES, QuestionMaker
from .specials import CutIn, make_special
from .sprite import VICTORY, Animator, Rig
from .stages import STAGES
from .ui import Keypad, panel, portrait, text

SCALE = 1.05
# Points (all multiplied by the level number, so harder levels score more)
PTS_CORRECT = 100        # plus up to PTS_SPEED more the faster you answer
PTS_SPEED = 100
PTS_COUNTER = 100
PTS_ROUND = 500
PTS_FLAWLESS = 1000      # won a round without getting hit
PTS_SPECIAL = 200        # landed a special move
PTS_SUPER = 400          # ...with a very fast answer
ATTACK_MOVES = ["punch", "kick", "combo"]
CPU_SPECIAL_CHANCE = 0.2     # how often the CPU uses its special (it only ever does 1 damage)
EXPR = {"punch": "angry", "kick": "angry", "combo": "angry", "uppercut": "angry",
        "special_kai": "angry", "special_luna": "angry", "special_dax": "angry", "special_mira": "angry",
        "special_ryu": "angry",
        "charge": "angry", "block": "angry", "hit": "hurt", "ko": "ko", "victory": "happy",
        "victory_loop": "happy"}
BUSY_OK = ("idle", "charge", "victory_loop", "walk")


class Actor:
    def __init__(self, fd, x, facing, scale=SCALE):
        self.rim = None        # stage light colour
        self.reflect = 0       # strength of the reflection on a shiny floor
        self.fd = fd
        self.scale = scale
        self.rig = Rig(fd)
        self.anim = Animator(VICTORY.get(self.rig.style, ("victory", "victory_b")))
        self.x = self.home = x
        self.facing = facing
        self.hits = 0
        self.flash = 0.0
        self.t = random.uniform(0, 10)
        self.wind = 0.0
        self._hip = None
        self._dt = 1 / 60
        self._buf = self._out = self._buf_size = self._buf_ss = None

    def play(self, name):
        self.anim.play(name)

    @property
    def special_anim(self):
        return "special_" + self.fd.key

    @property
    def expr(self):
        return EXPR.get(self.anim.name, "normal")

    @property
    def settled(self):
        return self.anim.name in BUSY_OK or (self.anim.name == "ko" and self.anim.done)

    def update(self, dt):
        self.t += dt
        self._dt = dt
        self.flash = max(0.0, self.flash - dt * 5)
        return self.anim.update(dt)

    def point(self, name):
        return self.rig.points.get(name, (self.x, GROUND_Y - 200))

    def draw(self, surf, ground=GROUND_Y):
        hx = self.x + self.anim.pose["x"] * self.scale * self.facing
        sw = int(210 * self.scale)
        sh = soft_shadow(sw, sw // 4)
        surf.blit(sh, (hx - sw // 2, ground - sw // 8))
        ss = QUALITY["ss"]
        if ss > 1:
            self._draw_smooth(surf, ground, hx, ss)
        else:
            self.rig.draw(surf, self.x, ground, self.facing, self.scale, self.anim.pose, self.t, self.flash,
                          self.expr, self.wind, self.rim)
        hip = self.rig.points["hip"][0]
        if self._hip is not None and self._dt > 0:
            v = (hip - self._hip) / self._dt * self.facing
            target = max(-30.0, min(30.0, v * 0.04))
            self.wind += (target - self.wind) * min(1.0, self._dt * 8)
        self._hip = hip


    def _draw_smooth(self, surf, ground, hx, ss):
        """Draws the fighter at a larger size into a buffer and scales it down."""
        w, h = int(500 * self.scale), int(480 * self.scale)
        left = int(hx - w / 2 + 40 * self.scale * self.facing)    # more room in front, for kicks
        top = int(ground - h + 40 * self.scale)
        size = (w, h)
        if self._buf is None or self._buf_size != size or self._buf_ss != ss:
            self._buf = pygame.Surface((int(w * ss), int(h * ss)), pygame.SRCALPHA)
            self._out = pygame.Surface(size, pygame.SRCALPHA)
            self._buf_size, self._buf_ss = size, ss
        self._buf.fill((0, 0, 0, 0))
        QUALITY["skip_aa"] = True
        self.rig.draw(self._buf, (self.x - left) * ss, (ground - top) * ss, self.facing, self.scale * ss,
                      self.anim.pose, self.t, self.flash, self.expr, self.wind, self.rim)
        QUALITY["skip_aa"] = False
        self.rig.points = {k: (x / ss + left, y / ss + top) for k, (x, y) in self.rig.points.items()}
        pygame.transform.smoothscale(self._buf, size, self._out)
        if self.reflect:
            depth = ground - top
            body = self._out.subsurface((0, 0, w, min(h, depth)))
            mirror = pygame.transform.flip(body, False, True)
            mirror = pygame.transform.smoothscale(mirror, (w, int(mirror.get_height() * 0.42)))
            mirror.set_alpha(self.reflect)
            surf.blit(mirror, (left, ground + 2))
        surf.blit(self._out, (left, top))


def draw_question_panel(surf, q, typed, head, border, q_left, q_time, hints=(), bar_marks=(), t=0.0):
    """The question box shared by fights, practice and the daily challenge.
    q_left=None means no time limit (practice)."""
    cx, top = W // 2, 128
    rect = pygame.Rect(cx - 300, top, 600, 186)
    panel(surf, rect, (15, 10, 35), 225, border, 20, 4)
    text(surf, head, 38, border, center=(cx, top + 26))
    text(surf, q.text, 88, WHITE, center=(cx, top + 82), ow=4)
    box = pygame.Rect(cx - 110, top + 118, 220, 50)
    pygame.draw.rect(surf, (250, 250, 255), box, border_radius=10)
    pygame.draw.rect(surf, border, box, 3, border_radius=10)
    # One slot per digit of the answer; the answer is checked when they are full.
    # A fraction shows its slash: 3/4 is typed 3 then 4.
    slots, i = [], 0
    for ch in str(q.answer):
        if ch == "/":
            slots.append("/")
        else:
            slots.append(typed[i] if i < len(typed) else "_")
            i += 1
    text(surf, " ".join(slots), 60, (20, 20, 40), center=box.center, ow=0)
    if q_left is not None:
        k = max(0.0, q_left / q_time)
        barw = rect.w - 40
        bar = pygame.Rect(rect.x + 20, rect.bottom - 18, int(barw * k), 10)
        col = GREEN if k > 0.5 else (255, 200, 40) if k > 0.25 else RED
        pygame.draw.rect(surf, (50, 40, 60), (rect.x + 20, rect.bottom - 18, barw, 10), border_radius=5)
        pygame.draw.rect(surf, col, bar, border_radius=5)
        for mark, mcol in bar_marks:      # e.g. where the special move runs out
            mx = rect.x + 20 + int(barw * (1 - mark / q_time))
            pygame.draw.rect(surf, mcol, (mx - 2, rect.bottom - 22, 4, 18), border_radius=2)
        text(surf, f"{q_left:0.1f}s", 34, col, midright=(rect.right - 18, box.centery))
    for i, (hint, hcol) in enumerate(hints):
        y = box.centery + (i * 2 - len(hints) + 1) * 13
        text(surf, hint, 26, hcol, midleft=(rect.x + 16, y))


def draw_result_strip(surf, res):
    """Compact strip after answering, so the action below stays visible.
    A wrong answer always shows the right one, so kids learn from it."""
    q = res["q"]
    rect = pygame.Rect(W // 2 - 330, 128, 660, 72)
    line = f"{q.a} {DISPLAY[q.op]} {q.b} = {q.answer}"
    if res["correct"]:
        panel(surf, rect, (10, 40, 20), 220, GREEN, 18, 3)
        text(surf, f"CORRECT!   {line}", 52, GREEN, center=rect.center, ow=4)
    else:
        msg = "TIME'S UP!" if res["timeout"] else "OOPS!"
        panel(surf, rect, (50, 10, 20), 220, RED, 18, 3)
        text(surf, f"{msg}   {line}", 52, (255, 130, 130), center=rect.center, ow=4)


def question_time(q, boss=False):
    """Fractions get more time. Blocking the final boss gives less."""
    t = FRACTION_ANSWER_TIME if q.is_fraction else ANSWER_TIME
    return t * BOSS_ANSWER_TIME / ANSWER_TIME if boss else t


def special_tier(elapsed, q_time):
    """How good a special move a correct answer earns: 0 none, 1 special, 2 super.
    The windows stretch with the time allowed, so fractions can earn them too."""
    k = q_time / ANSWER_TIME
    if elapsed <= SUPER_WINDOW * k:
        return 2
    return 1 if elapsed <= SPECIAL_WINDOW * k else 0


class Battle:
    PAUSE_RECT = pygame.Rect(W - 70, 120, 56, 56)
    # tap targets on the pause screen
    MUSIC_ROW = pygame.Rect(W // 2 - 280, H // 2 + 18, 560, 46)
    QUIT_ROW = pygame.Rect(W // 2 - 280, H // 2 + 68, 560, 46)

    def __init__(self, game):
        self.game = game
        self.level = game.level
        self.stage_no = game.stage
        self.stage = STAGES[game.stage]()
        self.p = Actor(game.player, PLAYER_HOME_X, 1)
        self.c = Actor(game.opponents[game.stage], CPU_HOME_X, -1)
        # Attacking asks your own fighter's math, defending asks the attacker's.
        self.qm_attack = QuestionMaker(self.p.fd.op, game.level, allowed=game.allowed_ops)
        self.qm_defend = QuestionMaker(self.c.fd.op, game.level, allowed=game.allowed_ops)
        for a in (self.p, self.c):
            a.rim, a.reflect = self.stage.rim, self.stage.reflect
        self.fx = Effects()
        self.keypad = Keypad()
        self.round = 1
        self.wins = [0, 0]
        self.paused = False
        self.disp_hp = [float(MAX_HITS), float(MAX_HITS)]
        self.score_pop = None     # (points, seconds shown) for the "+250" next to the score
        self.cutin = None         # special move banner (the fight freezes while it shows)
        self.hitstop = 0.0        # tiny freeze when a hit lands, so it feels heavy
        game.audio.play_music(self.stage.music_key)
        self.start_round(first=True)

    # ---------------------------------------------------------------- flow --
    def start_round(self, first=False):
        for a in (self.p, self.c):
            a.hits = 0
            a.x = a.home - 420 * a.facing if first else a.home
            a.play("walk" if first else "idle")
        self.time = float(ROUND_TIME)
        self.state, self.state_t = "intro", 0.0
        self.walk_in = first
        self.q = None
        self.result = None
        self.exchange = None
        # The player and the CPU take turns attacking, with no button to press.
        self.next_mode = "attack"
        self.wait = 0.0
        self.slowmo = 0.0
        self.announced_fight = False
        self.disp_hp = [float(MAX_HITS), float(MAX_HITS)]

    def set_state(self, s):
        self.state, self.state_t = s, 0.0

    def ask(self, mode):
        self.q = (self.qm_attack if mode == "attack" else self.qm_defend).next()
        self.mode = mode
        self.typed = ""
        self.q_time = question_time(self.q, boss=mode == "defend" and self.c.fd.boss)
        self.counter_window = COUNTER_WINDOW * self.q_time / ANSWER_TIME
        self.q_left = self.q_time
        self.last_tick = int(self.q_time)
        self.result = None
        (self.p if mode == "attack" else self.c).play("charge")
        self.set_state("question")
        self.game.audio.play("select")

    def submit(self, timeout=False):
        q = self.q
        correct = (not timeout) and self.typed == q.digits
        elapsed = self.q_time - self.q_left
        st = self.game.stats
        st["asked"] += 1
        if correct:
            st["correct"] += 1
            st["best"] = min(st["best"], elapsed)
        tier = special_tier(elapsed, self.q_time) if correct and self.mode == "attack" else 0
        self.announce(self.game.answered(q.op, correct, elapsed, tier > 0))
        self.result = {"correct": correct, "q": q, "timeout": timeout, "t": 0.0, "typed": self.typed}
        self.game.audio.play("correct" if correct else "wrong")

        if self.mode == "attack":
            att, dfd = self.p, self.c
            outcome = "hit" if correct else "miss"
            counter = False
            move = att.special_anim if tier else random.choice(ATTACK_MOVES)
            if tier:
                self.cutin = CutIn(att.fd, tier, 1)
                self.game.audio.play("super" if tier == 2 else "special")
        else:
            att, dfd = self.c, self.p
            outcome = "block" if correct else "hit"
            counter = correct and elapsed <= self.counter_window
            cpu_special = random.random() < CPU_SPECIAL_CHANCE or (att.fd.boss and random.random() < 0.3)
            move = att.special_anim if cpu_special else random.choice(ATTACK_MOVES)
            if att.fd.boss and cpu_special:
                self.cutin = CutIn(att.fd, 1, -1)
                self.game.audio.play("special")
        if correct:
            self.add_points(PTS_CORRECT + int(PTS_SPEED * self.q_left / self.q_time)
                            + (PTS_COUNTER if counter else 0)
                            + {0: 0, 1: PTS_SPECIAL, 2: PTS_SUPER}[tier])
        self.exchange = {"att": att, "dfd": dfd, "outcome": outcome, "counter": counter, "tier": tier,
                         "power": SPECIAL_DAMAGE if tier else 1,
                         "counter_t": None, "counter_phase": False, "dodged": False, "ko": None}
        att.play(move)
        self.set_state("action")

    def announce(self, events):
        """New personal bests and streak milestones, as they happen."""
        x, y = self.p.home, GROUND_Y - 340
        if events.get("best_streak"):
            self.fx.text("NEW BEST STREAK!", x, y, (255, 240, 120), 44, 1.4)
        elif events.get("milestone"):
            self.fx.text(f"{events['milestone']} IN A ROW!", x, y, (255, 240, 120), 44, 1.2)

    def add_points(self, pts):
        pts *= self.level
        self.game.score += pts
        self.score_pop = [pts, 0.0]

    # ------------------------------------------------------------- impacts --
    def damage(self, victim, attacker, label, big=False, amount=1):
        victim.hits = min(MAX_HITS, victim.hits + amount)
        victim.flash = 1.0
        self.hitstop = 0.07 * amount
        x, y = victim.point("chest")
        x -= 20 * victim.facing
        if victim.hits >= MAX_HITS:
            victim.play("ko")
            self.exchange["ko"] = victim
            self.fx.hit_spark(x, y, (255, 240, 140), True)
            self.fx.shake(22, 0.5)
            self.fx.screen_flash((255, 255, 255), 0.8)
            self.game.audio.play("ko")
            self.slowmo = 1.2
        else:
            victim.play("hit")
            self.fx.hit_spark(x, y, (255, 230, 120) if victim is self.c else (255, 120, 100), big)
            self.fx.shake(14 if big else 10, 0.3)
            self.game.audio.play("bighit" if big else "hit")
        color = GOLD if victim is self.c else RED
        self.fx.text(label, x, y - 90, color, 64, 1.0)

    def impact(self, final):
        ex = self.exchange
        att, dfd = ex["att"], ex["dfd"]
        x, y = dfd.point("chest")
        x -= 20 * dfd.facing
        if ex["outcome"] == "hit":
            if final:
                label = "HIT!" if dfd is self.c else "OUCH!"
                if ex["tier"]:
                    label = f"SPECIAL! -{ex['power']}"
                self.damage(dfd, att, label, big=True, amount=ex["power"])
            else:
                dfd.play("hit")
                dfd.flash = 0.6
                self.fx.hit_spark(x, y)
                self.game.audio.play("hit")
        elif ex["outcome"] == "miss":
            if not ex["dodged"]:
                dfd.play("dodge")
                ex["dodged"] = True
                self.game.audio.play("whoosh")
            if final:
                self.fx.text("MISS!", x, y - 90, (200, 200, 220), 64)
        else:  # block
            dfd.play("block")
            self.fx.block_spark(x - 25 * dfd.facing, y - 20)
            self.game.audio.play("block")
            if final:
                self.fx.text("BLOCK!", x, y - 90, (120, 200, 255), 64)
                if ex["counter"]:
                    ex["counter_t"] = 0.4

    def on_event(self, actor, e):
        ex = self.exchange
        if not ex:
            return
        if e in ("hit", "jab"):
            if actor is ex["att"] and not ex["counter_phase"]:
                self.impact(e == "hit")
            elif actor is ex["dfd"] and ex["counter_phase"] and e == "hit":
                self.damage(ex["att"], actor, "COUNTER!", big=True)
        elif e == "fire":
            hx, hy = actor.point("hand_f")
            target = ex["dfd"]
            tx = target.point("chest")[0] - 30 * target.facing
            self.game.audio.play("fire")
            self.fx.projectiles.append(make_special(actor.fd.key, hx, hy, tx, actor.facing, actor.fd.theme,
                                                    max(1, ex["tier"]), lambda: self.impact(True)))
        elif e == "land":
            x = actor.point("hip")[0]
            for i in range(14):
                self.fx.aura(x + random.uniform(-80, 80), GROUND_Y - 10, (200, 190, 170), 10)
            self.fx.shake(8, 0.2)
            self.game.audio.play("hit")

    # -------------------------------------------------------------- input --
    def handle(self, ev):
        g = self.game
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_ESCAPE, pygame.K_p):
                self.paused = not self.paused
                return
            if self.paused:
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.paused = False
                elif ev.key == pygame.K_q:
                    g.to_title()
                return
            if self.state == "question":
                if ev.unicode and ev.unicode.isdigit():
                    self.type_digit(ev.unicode)
                elif ev.key == pygame.K_BACKSPACE:
                    self.typed = self.typed[:-1]
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.paused:
                if self.MUSIC_ROW.collidepoint(ev.pos):
                    g.toggle_music()
                elif self.QUIT_ROW.collidepoint(ev.pos):
                    g.to_title()
                else:
                    self.paused = False
                return
            if g.touch and self.PAUSE_RECT.collidepoint(ev.pos):
                self.paused = True
            elif self.state == "question":
                k = self.keypad.hit(ev.pos)
                if k == "DEL":
                    self.typed = self.typed[:-1]
                elif k:
                    self.type_digit(k)

    def type_digit(self, d):
        """The answer is checked as soon as it has as many digits as the
        right answer, so there is no ENTER to press."""
        self.typed += d
        if len(self.typed) >= len(self.q.digits):
            self.submit()

    # ------------------------------------------------------------- update --
    def update(self, dt):
        if self.paused:
            return
        if self.cutin:
            self.stage.update(dt)
            self.cutin.update(dt)
            if self.cutin.done:
                self.cutin = None
            return
        if self.hitstop > 0:
            self.hitstop -= dt
            self.fx.update(dt)
            return
        if self.slowmo > 0:
            self.slowmo -= dt
            dt *= 0.35
        self.state_t += dt
        self.stage.update(dt)
        for a in (self.p, self.c):
            for e in a.update(dt):
                self.on_event(a, e)
            if a.fd.boss and random.random() < 0.5:
                x, y = a.point("hip")
                self.fx.aura(x, y + 40, (130, 70, 210), 70)
        self.fx.update(dt)
        if self.result:
            self.result["t"] += dt
        if self.score_pop:
            self.score_pop[1] += dt
        for i, a in enumerate((self.p, self.c)):
            target = MAX_HITS - a.hits
            if self.disp_hp[i] > target:
                self.disp_hp[i] = max(target, self.disp_hp[i] - dt * 2.5)
            else:
                self.disp_hp[i] = target

        s = self.state
        fighting = s in ("neutral", "question", "action")
        if fighting:
            self.time = max(0.0, self.time - dt)

        if s == "intro":
            if self.walk_in:
                k = min(1.0, self.state_t / 1.2)
                for a in (self.p, self.c):
                    a.x = a.home - 420 * a.facing * (1 - k)
                if k >= 1 and self.p.anim.name == "walk":
                    for a in (self.p, self.c):
                        a.play("idle")
            if self.state_t > 1.4 and not self.announced_fight:
                self.announced_fight = True
                self.game.audio.play("fight")
            if self.state_t > 2.3:
                self.ask("attack")
        elif s == "neutral":
            if self.time <= 0:
                self.set_state("timeup")
                self.game.audio.play("ko")
            else:
                self.wait -= dt
                if self.wait <= 0:
                    self.ask(self.next_mode)
        elif s == "question":
            self.q_left -= dt
            sec = int(math.ceil(self.q_left))
            if sec < self.last_tick and sec <= 3:
                self.game.audio.play("tick")
            self.last_tick = sec
            charger = self.p if self.mode == "attack" else self.c
            if random.random() < 0.7:
                x, y = charger.point("hip")
                self.fx.aura(x, y + 60, lighter(charger.fd.theme, 0.3), 55)
            if self.q_left <= 0:
                self.q_left = 0
                self.submit(timeout=True)
        elif s == "action":
            ex = self.exchange
            if ex["counter_t"] is not None:
                ex["counter_t"] -= dt
                if ex["counter_t"] <= 0:
                    ex["counter_t"] = None
                    ex["counter_phase"] = True
                    ex["dfd"].play("uppercut")
                    self.game.audio.play("whoosh")
            done = (self.state_t > 0.6 and self.p.settled and self.c.settled and not self.fx.projectiles
                    and ex["counter_t"] is None)
            if done:
                if ex["ko"] is not None:
                    self.set_state("ko")
                else:
                    self.next_mode = "defend" if self.mode == "attack" else "attack"
                    self.wait = TURN_PAUSE
                    self.set_state("neutral")
        elif s in ("ko", "timeup"):
            if self.state_t > 2.0:
                self.end_round()
        elif s == "round_end":
            if self.state_t > 3.0:
                if max(self.wins) >= ROUNDS_TO_WIN:
                    self.set_state("match_end")
                    won = self.wins[0] >= ROUNDS_TO_WIN
                    self.game.audio.play("confirm" if won else "wrong")
                else:
                    self.round += 1
                    self.start_round()
        elif s == "match_end":
            if self.state_t > 3.0:
                self.game.match_over(self.wins[0] >= ROUNDS_TO_WIN)

    def end_round(self):
        self.game.store()
        ph, ch = self.p.hits, self.c.hits
        if ph < ch:
            self.round_winner = 0
        elif ch < ph:
            self.round_winner = 1
        else:
            self.round_winner = None if self.round < 5 else 0
        if self.round_winner is not None:
            self.wins[self.round_winner] += 1
            w = (self.p, self.c)[self.round_winner]
            w.play("victory")
            self.game.audio.play("confirm" if self.round_winner == 0 else "wrong")
            if self.round_winner == 0:
                self.add_points(PTS_ROUND + (PTS_FLAWLESS if ph == 0 else 0))
        self.set_state("round_end")

    # --------------------------------------------------------------- draw --
    def draw(self, surf):
        self.stage.draw(surf)
        # the defender is drawn first so attacks appear in front
        order = [self.c, self.p]
        if self.exchange and self.state == "action":
            order = [self.exchange["dfd"], self.exchange["att"]]
            if self.exchange["counter_phase"]:
                order.reverse()
        for a in order:
            a.draw(surf)
        self.fx.draw(surf)
        self.stage.draw_front(surf)
        ox, oy = self.fx.offset()
        if ox or oy:
            surf.scroll(int(ox), int(oy))
        if self.cutin:
            self.cutin.draw(surf)
        self.draw_hud(surf)
        if self.state == "question":
            self.draw_question(surf)
        elif self.result and self.result["t"] < 1.6:
            draw_result_strip(surf, self.result)
        self.fx.draw_top(surf)
        self.draw_banner(surf)
        if self.paused:
            panel(surf, (W // 2 - 300, H // 2 - 160, 600, 320), (10, 10, 30), 230)
            text(surf, "PAUSED", 90, GOLD, center=(W // 2, H // 2 - 90))
            music = "ON" if self.game.audio.music_on else "OFF"
            text(surf, "ENTER / tap  -  Resume", 40, center=(W // 2, H // 2 - 10))
            text(surf, f"M  -  Music: {music}  (sounds stay on)", 40, center=self.MUSIC_ROW.center)
            text(surf, "Q  -  Quit to title", 40, center=self.QUIT_ROW.center)

    def draw_hud(self, surf):
        g = self.game
        for i, a in enumerate((self.p, self.c)):
            left = i == 0
            px = 20 if left else W - 110
            pr = portrait(a.fd, 90)
            panel(surf, (px - 4, 14, 98, 98), a.fd.theme, 255, WHITE, 12, 3)
            surf.blit(pr if left else pygame.transform.flip(pr, True, False), (px, 18))
            bx = 124 if left else W - 124 - 440
            bw, bh = 440, 36
            panel(surf, (bx - 4, 26, bw + 8, bh + 8), (10, 5, 20), 230, WHITE, 8, 2)
            seg = (bw - 7 * 4) / MAX_HITS
            hp = MAX_HITS - a.hits
            disp = self.disp_hp[i]
            for k in range(MAX_HITS):
                idx = k if left else MAX_HITS - 1 - k
                sx = bx + idx * (seg + 4)
                r = pygame.Rect(int(sx), 30, int(seg), bh)
                if k < hp:
                    col = GREEN if hp > 4 else (255, 200, 40) if hp > 2 else RED
                    pygame.draw.rect(surf, col, r, border_radius=5)
                    pygame.draw.rect(surf, lighter(col, 0.5), (r.x, r.y, r.w, 9), border_radius=5)
                elif k < disp:
                    pygame.draw.rect(surf, (255, 240, 240), r, border_radius=5)
                else:
                    pygame.draw.rect(surf, (60, 30, 40), r, border_radius=5)
            name_anchor = {"topleft": (bx, 72)} if left else {"topright": (bx + bw, 72)}
            text(surf, a.fd.name.upper(), 34, WHITE, **name_anchor)
            for k in range(ROUNDS_TO_WIN):
                cx = (bx + bw - 20 - k * 34) if left else (bx + 20 + k * 34)
                won = self.wins[i] > k
                fill_circle(surf, (cx, 86), 13, (20, 10, 30))
                fill_circle(surf, (cx, 86), 10, GOLD if won else (70, 60, 80))
        # timer
        panel(surf, (W // 2 - 52, 12, 104, 84), (10, 5, 20), 230, GOLD, 14, 3)
        tcol = RED if self.time < 10 else WHITE
        text(surf, str(int(math.ceil(self.time))), 76, tcol, center=(W // 2, 56))
        label = "FINAL ROUND" if self.round >= 3 else f"ROUND {self.round}"
        text(surf, label, 30, GOLD, center=(W // 2, 112))
        text(surf, f"SCORE {g.score:,}", 34, GOLD, midleft=(20, H - 22), ow=3)
        if self.score_pop and self.score_pop[1] < 1.2:
            k = self.score_pop[1] / 1.2
            text(surf, f"+{self.score_pop[0]:,}", 32, (255, 255, 160),
                 midleft=(20, int(H - 58 - 30 * k)), ow=3)
        if g.streak >= 3:
            text(surf, f"{g.streak} IN A ROW", 28, (255, 255, 200), midleft=(250, H - 22), ow=3)
        lv = "BONUS LEVEL: FRACTIONS" if self.level >= BONUS_LEVEL else f"LEVEL {self.level}"
        text(surf, f"STAGE {self.stage_no + 1}: {self.stage.name.upper()}   {lv}", 26,
             (230, 230, 240), center=(W // 2, H - 18))
        # pause button (touch)
        if g.touch:
            panel(surf, self.PAUSE_RECT, (30, 30, 60), 200, WHITE, 10, 2)
            pygame.draw.rect(surf, WHITE, (W - 53, 133, 8, 30))
            pygame.draw.rect(surf, WHITE, (W - 39, 133, 8, 30))

    def draw_question(self, surf):
        attack = self.mode == "attack"
        border = (255, 200, 60) if attack else (90, 170, 255)
        hints, marks = [], []
        if self.q.is_fraction:
            hints.append(("SIMPLEST FORM", (150, 230, 255)))
        if attack:
            head = f"ATTACK with {DISPLAY[self.q.op]} !"
            k = self.q_time / ANSWER_TIME
            marks = [(SPECIAL_WINDOW * k, WHITE), (SUPER_WINDOW * k, GOLD)]
            elapsed = self.q_time - self.q_left
            if elapsed <= SUPER_WINDOW * k:
                hints.append(("SUPER SPECIAL!", (255, 225, 90)))
            elif elapsed <= SPECIAL_WINDOW * k:
                hints.append(("SPECIAL MOVE!", WHITE))
        else:
            head = f"DEFEND!  Block the {OP_NAMES[self.q.op].upper()} attack!"
            if self.q_left >= self.q_time - self.counter_window:
                hints.append(("FAST = COUNTER!", (255, 160, 220)))
        draw_question_panel(surf, self.q, self.typed, head, border, self.q_left, self.q_time, hints, marks)
        if self.game.touch:
            self.keypad.draw(surf, 1 / 60)

    def draw_banner(self, surf):
        s, t = self.state, self.state_t
        msg, col = None, GOLD
        if s == "intro":
            if t < 1.4:
                msg = "FINAL ROUND" if self.round >= 3 else f"ROUND {self.round}"
            elif t < 2.3:
                msg, col = "FIGHT!", RED
        elif s == "ko":
            msg, col = "K.O.!", RED
        elif s == "timeup":
            msg, col = "TIME!", GOLD
        elif s == "round_end":
            if self.round_winner is None:
                msg = "DRAW!"
            elif self.round_winner == 0:
                msg, col = ("PERFECT ROUND!" if self.p.hits == 0 else "YOU WIN THE ROUND!"), GREEN
            else:
                msg, col = f"{self.c.fd.name.upper()} WINS THE ROUND", RED
        elif s == "match_end":
            if self.wins[0] >= ROUNDS_TO_WIN:
                msg, col = "YOU WIN!", GOLD
            else:
                msg, col = "YOU LOSE...", RED
        if msg:
            k = min(1.0, t / 0.25)
            size = int(120 * (2 - k)) if len(msg) < 12 else int(80 * (2 - k))
            text(surf, msg, size, col, center=(W // 2, H // 2 - 20), ow=6)
