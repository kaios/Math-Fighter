"""The fight itself: rounds, math questions, attacks, blocks, counters and KOs."""

import math
import random

import pygame

from .config import (ANSWER_TIME, BOSS_ANSWER_TIME, COUNTER_WINDOW, CPU_HOME_X, GOLD, GREEN, GROUND_Y,
                     H, MAX_HITS, PLAYER_HOME_X, RED, ROUND_TIME, ROUNDS_TO_WIN, TURN_PAUSE, W, WHITE)
from .draw import fill_circle, lighter
from .effects import Effects, Projectile
from .mathq import DISPLAY, OP_NAMES, QuestionMaker
from .sprite import VICTORY, Animator, Rig
from .stages import STAGES
from .ui import Keypad, font, panel, portrait, text

SCALE = 1.05
ATTACK_MOVES = ["punch", "kick", "combo", "special"]
EXPR = {"punch": "angry", "kick": "angry", "combo": "angry", "special": "angry", "uppercut": "angry",
        "charge": "angry", "block": "angry", "hit": "hurt", "ko": "ko", "victory": "happy",
        "victory_loop": "happy"}
BUSY_OK = ("idle", "charge", "victory_loop", "walk")


class Actor:
    def __init__(self, fd, x, facing, scale=SCALE):
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

    def play(self, name):
        self.anim.play(name)

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
        sw = int(160 * self.scale)
        sh = pygame.Surface((sw, sw // 6), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
        surf.blit(sh, (hx - sw // 2, ground - sw // 12))
        self.rig.draw(surf, self.x, ground, self.facing, self.scale, self.anim.pose, self.t, self.flash,
                      self.expr, self.wind)
        hip = self.rig.points["hip"][0]
        if self._hip is not None and self._dt > 0:
            v = (hip - self._hip) / self._dt * self.facing
            target = max(-30.0, min(30.0, v * 0.04))
            self.wind += (target - self.wind) * min(1.0, self._dt * 8)
        self._hip = hip


class Battle:
    PAUSE_RECT = pygame.Rect(W - 70, 120, 56, 56)

    def __init__(self, game):
        self.game = game
        self.level = game.level
        self.stage_no = game.stage
        self.stage = STAGES[game.stage]()
        self.p = Actor(game.player, PLAYER_HOME_X, 1)
        self.c = Actor(game.opponents[game.stage], CPU_HOME_X, -1)
        # Attacking asks your own fighter's math, defending asks the attacker's.
        self.qm_attack = QuestionMaker(self.p.fd.op, game.level)
        self.qm_defend = QuestionMaker(self.c.fd.op, game.level)
        self.fx = Effects()
        self.keypad = Keypad()
        self.round = 1
        self.wins = [0, 0]
        self.paused = False
        self.disp_hp = [float(MAX_HITS), float(MAX_HITS)]
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
        # Blocking the final boss gives less time, and the counter window shrinks with it.
        boss = mode == "defend" and self.c.fd.boss
        self.q_time = BOSS_ANSWER_TIME if boss else ANSWER_TIME
        self.counter_window = COUNTER_WINDOW * self.q_time / ANSWER_TIME
        self.q_left = self.q_time
        self.last_tick = int(self.q_time)
        self.result = None
        (self.p if mode == "attack" else self.c).play("charge")
        self.set_state("question")
        self.game.audio.play("select")

    def submit(self, timeout=False):
        q = self.q
        correct = (not timeout) and self.typed != "" and int(self.typed) == q.answer
        elapsed = self.q_time - self.q_left
        st = self.game.stats
        st["asked"] += 1
        if correct:
            st["correct"] += 1
            st["best"] = min(st["best"], elapsed)
        self.result = {"correct": correct, "q": q, "timeout": timeout, "t": 0.0, "typed": self.typed}
        self.game.audio.play("correct" if correct else "wrong")

        if self.mode == "attack":
            att, dfd = self.p, self.c
            outcome = "hit" if correct else "miss"
            counter = False
        else:
            att, dfd = self.c, self.p
            outcome = "block" if correct else "hit"
            counter = correct and elapsed <= self.counter_window
        move = random.choice(ATTACK_MOVES)
        self.exchange = {"att": att, "dfd": dfd, "outcome": outcome, "counter": counter,
                         "counter_t": None, "counter_phase": False, "dodged": False, "ko": None}
        att.play(move)
        self.set_state("action")

    # ------------------------------------------------------------- impacts --
    def damage(self, victim, attacker, label, big=False):
        victim.hits += 1
        victim.flash = 1.0
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
        self.fx.text(label, x, y - 90, color, font(64), 1.0)

    def impact(self, final):
        ex = self.exchange
        att, dfd = ex["att"], ex["dfd"]
        x, y = dfd.point("chest")
        x -= 20 * dfd.facing
        if ex["outcome"] == "hit":
            if final:
                self.damage(dfd, att, "HIT!" if dfd is self.c else "OUCH!", big=True)
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
                self.fx.text("MISS!", x, y - 90, (200, 200, 220), font(64))
        else:  # block
            dfd.play("block")
            self.fx.block_spark(x - 25 * dfd.facing, y - 20)
            self.game.audio.play("block")
            if final:
                self.fx.text("BLOCK!", x, y - 90, (120, 200, 255), font(64))
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
            passes = ex["outcome"] == "miss"
            if passes:
                self.impact(False)
            self.fx.projectiles.append(Projectile(
                hx, hy, tx, actor.facing, actor.fd.theme, DISPLAY[self.q.op], font(56),
                lambda: self.impact(True), passes))
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
                elif ev.key == pygame.K_m:
                    g.audio.toggle()
                return
            if self.state == "question":
                if ev.unicode and ev.unicode.isdigit():
                    self.type_digit(ev.unicode)
                elif ev.key == pygame.K_BACKSPACE:
                    self.typed = self.typed[:-1]
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.paused:
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
        if len(self.typed) >= len(str(self.q.answer)):
            self.submit()

    # ------------------------------------------------------------- update --
    def update(self, dt):
        if self.paused:
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
        self.set_state("round_end")

    # --------------------------------------------------------------- draw --
    def draw(self, surf):
        ox, oy = self.fx.offset()
        self.stage.draw(surf, ox, oy)
        shaking = ox or oy
        layer = pygame.Surface((W, H), pygame.SRCALPHA) if shaking else surf
        # the defender is drawn first so attacks appear in front
        order = [self.c, self.p]
        if self.exchange and self.state == "action":
            order = [self.exchange["dfd"], self.exchange["att"]]
            if self.exchange["counter_phase"]:
                order.reverse()
        for a in order:
            a.draw(layer)
        self.fx.draw(layer)
        self.stage.draw_front(layer)
        if shaking:
            surf.blit(layer, (ox, oy))
        self.draw_hud(surf)
        if self.state == "question":
            self.draw_question(surf)
        elif self.result and self.result["t"] < 1.6:
            self.draw_result(surf)
        self.fx.draw_top(surf)
        self.draw_banner(surf)
        if self.paused:
            panel(surf, (W // 2 - 300, H // 2 - 160, 600, 320), (10, 10, 30), 230)
            text(surf, "PAUSED", 90, GOLD, center=(W // 2, H // 2 - 90))
            text(surf, "ENTER / tap  -  Resume", 40, center=(W // 2, H // 2 - 10))
            text(surf, "M  -  Sound on/off", 40, center=(W // 2, H // 2 + 40))
            text(surf, "Q  -  Quit to title", 40, center=(W // 2, H // 2 + 90))

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
        text(surf, f"STAGE {self.stage_no + 1}: {self.stage.name.upper()}   LEVEL {self.level}", 26,
             (230, 230, 240), center=(W // 2, H - 18))
        # pause button (touch)
        if g.touch:
            panel(surf, self.PAUSE_RECT, (30, 30, 60), 200, WHITE, 10, 2)
            pygame.draw.rect(surf, WHITE, (W - 53, 133, 8, 30))
            pygame.draw.rect(surf, WHITE, (W - 39, 133, 8, 30))

    def draw_question(self, surf):
        g = self.game
        attack = self.mode == "attack"
        cx, top = W // 2, 128
        rect = pygame.Rect(cx - 300, top, 600, 186)
        border = (255, 200, 60) if attack else (90, 170, 255)
        panel(surf, rect, (15, 10, 35), 225, border, 20, 4)
        if attack:
            head = f"ATTACK with {DISPLAY[self.p.fd.op]} !"
        else:
            head = f"DEFEND!  Block the {OP_NAMES[self.q.op].upper()} attack!"
        text(surf, head, 38, border, center=(cx, top + 26))
        text(surf, self.q.text, 88, WHITE, center=(cx, top + 82), ow=4)
        box = pygame.Rect(cx - 110, top + 118, 220, 50)
        pygame.draw.rect(surf, (250, 250, 255), box, border_radius=10)
        pygame.draw.rect(surf, border, box, 3, border_radius=10)
        # One slot per digit of the answer; the answer is checked when they are full.
        slots = self.typed + "_" * (len(str(self.q.answer)) - len(self.typed))
        text(surf, " ".join(slots), 60, (20, 20, 40), center=box.center, ow=0)
        # timer bar
        k = max(0.0, self.q_left / self.q_time)
        bar = pygame.Rect(rect.x + 20, rect.bottom - 18, int((rect.w - 40) * k), 10)
        col = GREEN if k > 0.5 else (255, 200, 40) if k > 0.25 else RED
        pygame.draw.rect(surf, (50, 40, 60), (rect.x + 20, rect.bottom - 18, rect.w - 40, 10), border_radius=5)
        pygame.draw.rect(surf, col, bar, border_radius=5)
        text(surf, f"{self.q_left:0.1f}s", 34, col, midright=(rect.right - 18, box.centery))
        if not attack and self.q_left >= self.q_time - self.counter_window:
            text(surf, "FAST = COUNTER!", 26, (255, 160, 220), midleft=(rect.x + 16, box.centery))
        if g.touch:
            self.keypad.draw(surf, 1 / 60)

    def draw_result(self, surf):
        """Compact strip after answering, so the action below stays visible.
        A wrong answer always shows the right one, so kids learn from it."""
        res = self.result
        q = res["q"]
        rect = pygame.Rect(W // 2 - 330, 128, 660, 72)
        if res["correct"]:
            panel(surf, rect, (10, 40, 20), 220, GREEN, 18, 3)
            text(surf, f"CORRECT!   {q.a} {DISPLAY[q.op]} {q.b} = {q.answer}", 52, GREEN, center=rect.center, ow=4)
        else:
            msg = "TIME'S UP!" if res["timeout"] else "OOPS!"
            panel(surf, rect, (50, 10, 20), 220, RED, 18, 3)
            text(surf, f"{msg}   {q.a} {DISPLAY[q.op]} {q.b} = {q.answer}", 52, (255, 130, 130),
                 center=rect.center, ow=4)

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
                msg, col = "YOU WIN THE ROUND!", GREEN
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
