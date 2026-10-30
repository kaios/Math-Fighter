"""The main menu, the setup screens (math settings, practice, daily challenge)
and the progress screen."""

from datetime import date

import pygame

from . import progress
from .battle import Actor
from .characters import ROSTER
from .config import BONUS_LEVEL, DAILY_QUESTIONS, GOLD, H, MAX_LEVEL, W, WHITE
from .draw import darker
from .mathq import DISPLAY, OPS, OP_NAMES
from .scenes import CONFIRM, Difficulty, HighScores, HowTo, Scene, Title, starfield_bg
from .ui import panel, portrait, text

MUTED = (190, 190, 215)
BAR = (96, 165, 250)
BAR_TRACK = (45, 45, 75)


class MainMenu(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.bg = starfield_bg((20, 12, 60), (90, 35, 95))
        self.sel = 0
        self.items = [("TOURNAMENT", self.tournament), ("DAILY CHALLENGE", self.daily), ("PRACTICE", self.practice),
                      ("MY PROGRESS", self.progress), ("TOP 10", self.top10), ("MATH SETTINGS", self.settings)]
        self.rects = [pygame.Rect(70, 138 + i * 86, 470, 74) for i in range(len(self.items))]
        self.actor = Actor(game.player, 900, -1, 1.0)
        game.audio.play_music("menu")

    def tournament(self):
        g = self.game
        g.goto(HowTo(g) if not g.seen_howto else Difficulty(g))

    def daily(self):
        g = self.game
        g.goto(Options(g, "DAILY CHALLENGE", ("level", "fighter"), "START", lambda: start_drill(g, "daily")))

    def practice(self):
        g = self.game
        g.goto(Options(g, "PRACTICE", ("ops", "level", "fighter"), "START", lambda: start_drill(g, "practice")))

    def progress(self):
        self.game.goto(ProgressScreen(self.game))

    def top10(self):
        g = self.game
        g.goto(HighScores(g, then=lambda: MainMenu(g)))

    def settings(self):
        g = self.game
        g.goto(Options(g, "MATH SETTINGS", ("ops",), "DONE", lambda: g.goto(MainMenu(g))))

    def describe(self):
        g = self.game
        i = self.sel
        if i == 0:
            return ["Fight through 4 stages and beat", "the final boss, Ninja Ryu!",
                    "Answer attacks in under 2 seconds", "for a special move."]
        if i == 1:
            st = progress.daily_status(g.save, g.today())
            theme = progress.daily_theme(g.today(), g.allowed_ops)
            name = "All four mixed" if theme == "mix" else OP_NAMES[theme]
            done = f"Today's score: {st['today']:,}" if st["today"] is not None else "Not played yet today"
            return [f"{DAILY_QUESTIONS} timed questions, new every day.", f"Today's theme: {name}", done,
                    f"Daily streak: {st['streak']}"]
        if i == 2:
            return ["No timer and no health bars.", "Questions you miss come back",
                    "later, so you can get them right.", "Stop any time."]
        if i == 3:
            answered, right = progress.totals(g.save)
            pct = f" ({100 * right // answered}% right)" if answered else ""
            return ["Your personal bests, and how", "you are doing in each kind of math.",
                    f"Answered so far: {answered:,}{pct}"]
        if i == 4:
            return ["The ten best tournament scores", "on this device."]
        on = ", ".join(OP_NAMES[op] for op in g.allowed_ops)
        return ["For parents: choose which kinds", "of math the game asks.", "Now on:", on]

    def handle(self, ev):
        g = self.game
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.items)
                g.audio.play("select")
            elif ev.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.items)
                g.audio.play("select")
            elif ev.key in CONFIRM:
                self.activate()
            elif ev.key == pygame.K_ESCAPE:
                g.goto(Title(g))
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(ev.pos):
                    self.sel = i
                    self.activate()
                    break

    def activate(self):
        self.game.audio.play("confirm")
        self.items[self.sel][1]()

    def update(self, dt):
        super().update(dt)
        self.actor.update(dt)

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        text(surf, "MATH FIGHTER", 92, GOLD, center=(W // 2, 66), outline=(120, 30, 20), ow=6)
        for i, ((label, _), r) in enumerate(zip(self.items, self.rects)):
            on = i == self.sel
            col = (205, 80, 70) if on else (45, 35, 90)
            rr = r.inflate(14, 8) if on else r
            panel(surf, rr, col, 235, GOLD if on else (140, 140, 175), 16, 4 if on else 2)
            text(surf, label, 46, WHITE, center=rr.center, ow=3)
        panel(surf, (590, 138, 620, 150), (10, 10, 30), 205, (140, 140, 175), 16, 2)
        for i, line in enumerate(self.describe()):
            text(surf, line, 32, WHITE, midleft=(616, 164 + i * 33), ow=2)
        self.actor.draw(surf, 660)
        text(surf, "UP / DOWN to choose,  ENTER to go", 28, MUTED, center=(W // 2, H - 22), ow=2)


def start_drill(game, mode):
    from .drill import Drill
    game.store()
    game.goto(Drill(game, mode))


class Options(Scene):
    """Rows of choices with a button at the bottom. rows: any of ops, level, fighter."""
    ROW_H = {"ops": 150, "level": 112, "fighter": 150}

    def __init__(self, game, title, rows, button, on_go):
        super().__init__(game)
        self.title, self.rows, self.button, self.on_go = title, rows, button, on_go
        self.bg = starfield_bg((16, 18, 60), (70, 30, 90))
        self.top_level = BONUS_LEVEL if game.bonus_unlocked else MAX_LEVEL
        self.row = 0
        self.cursor = {"ops": 0, "level": game.level - 1, "fighter": ROSTER.index(game.player)
                       if game.player in ROSTER else 0}
        self.hit = {}
        y = 130
        self.row_y = {}
        for row in rows:
            self.row_y[row] = y
            n = {"ops": 4, "level": self.top_level, "fighter": 4}[row]
            bw = 180 if n == 4 else 130
            gap = 18
            x0 = 300
            h = self.ROW_H[row] - 26
            self.hit[row] = [pygame.Rect(x0 + i * (bw + gap), y, bw, h) for i in range(n)]
            y += self.ROW_H[row]
        self.go_rect = pygame.Rect(W // 2 - 170, max(y + 8, 500), 340, 76)

    def rows_all(self):
        return list(self.rows) + ["go"]

    def choose(self, row, i):
        g = self.game
        self.cursor[row] = i
        if row == "ops":
            g.toggle_op(OPS[i])
        elif row == "level":
            g.set_level(i + 1)
        else:
            g.player = ROSTER[i]
        g.audio.play("select")

    def handle(self, ev):
        g = self.game
        rows = self.rows_all()
        if ev.type == pygame.KEYDOWN:
            cur = rows[self.row]
            if ev.key in (pygame.K_UP, pygame.K_w):
                self.row = (self.row - 1) % len(rows)
                g.audio.play("select")
            elif ev.key in (pygame.K_DOWN, pygame.K_s):
                self.row = (self.row + 1) % len(rows)
                g.audio.play("select")
            elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d) and cur != "go":
                step = -1 if ev.key in (pygame.K_LEFT, pygame.K_a) else 1
                i = (self.cursor[cur] + step) % len(self.hit[cur])
                if cur == "ops":
                    self.cursor[cur] = i
                    g.audio.play("select")
                else:
                    self.choose(cur, i)
            elif ev.key == pygame.K_SPACE and cur == "ops":
                self.choose("ops", self.cursor["ops"])
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                g.audio.play("confirm")
                self.on_go()
            elif ev.key == pygame.K_ESCAPE:
                g.goto(MainMenu(g))
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.go_rect.collidepoint(ev.pos):
                g.audio.play("confirm")
                self.on_go()
                return
            for row, rects in self.hit.items():
                for i, r in enumerate(rects):
                    if r.collidepoint(ev.pos):
                        self.row = rows.index(row)
                        self.choose(row, i)
                        return

    def draw(self, surf):
        g = self.game
        surf.blit(self.bg, (0, 0))
        text(surf, self.title, 80, GOLD, center=(W // 2, 62), ow=5)
        current = self.rows_all()[self.row]
        labels = {"ops": "MATH", "level": "LEVEL", "fighter": "FIGHTER"}
        for row in self.rows:
            active = row == current
            r0 = self.hit[row][0]
            text(surf, labels[row], 44, GOLD if active else WHITE, midright=(270, r0.centery), ow=3)
            for i, r in enumerate(self.hit[row]):
                cursor = active and i == self.cursor[row]
                if row == "ops":
                    self.draw_op(surf, r, OPS[i], cursor)
                elif row == "level":
                    self.draw_level(surf, r, i + 1, cursor)
                else:
                    self.draw_fighter(surf, r, ROSTER[i], cursor)
        if "ops" in self.rows and self.button == "DONE":
            text(surf, "Tournament questions, practice and the daily challenge only use the math that is ON.",
                 28, MUTED, center=(W // 2, 300), ow=2)
            text(surf, "If a fighter's math is off, that fighter asks one of the others instead.", 28, MUTED,
                 center=(W // 2, 336), ow=2)
        if "fighter" in self.rows and "ops" not in self.rows:
            today = g.today()
            st = progress.daily_status(g.save, today)
            theme = progress.daily_theme(today, g.allowed_ops)
            name = "All four mixed" if theme == "mix" else OP_NAMES[theme]
            text(surf, f"Today: {name}   -   {DAILY_QUESTIONS} questions   -   Best: {st['best']:,}", 34, WHITE,
                 center=(W // 2, 430), ow=2)
        on = current == "go"
        panel(surf, self.go_rect, (60, 170, 95) if on else (40, 110, 70), 240, GOLD if on else WHITE, 16, 4 if on else 2)
        text(surf, self.button, 50, WHITE, center=self.go_rect.center, ow=3)
        hint = "UP / DOWN: row    LEFT / RIGHT: choose    ENTER: " + self.button.lower()
        if "ops" in self.rows:
            hint = "UP / DOWN: row    LEFT / RIGHT: move    SPACE: on / off    ENTER: " + self.button.lower()
        text(surf, hint, 28, MUTED, center=(W // 2, H - 26), ow=2)

    def draw_op(self, surf, r, op, cursor):
        on = op in self.game.allowed_ops
        panel(surf, r, (60, 130, 200) if on else (50, 50, 65), 235, GOLD if cursor else (150, 150, 175), 14,
              4 if cursor else 2)
        text(surf, DISPLAY[op], 72, WHITE if on else (130, 130, 145), center=(r.centerx, r.y + 42), ow=3)
        text(surf, OP_NAMES[op], 26, WHITE if on else (150, 150, 165), center=(r.centerx, r.y + 88), ow=2)
        text(surf, "ON" if on else "OFF", 24, WHITE if on else (150, 150, 165), center=(r.centerx, r.y + 110), ow=2)

    def draw_level(self, surf, r, lv, cursor):
        on = self.game.level == lv
        panel(surf, r, (205, 80, 70) if on else (45, 35, 90), 235, GOLD if cursor or on else (150, 150, 175), 14,
              4 if cursor else 2)
        label = "FRAC" if lv == BONUS_LEVEL else str(lv)
        text(surf, label, 54 if lv < BONUS_LEVEL else 38, WHITE, center=r.center, ow=3)

    def draw_fighter(self, surf, r, fd, cursor):
        on = self.game.player is fd
        panel(surf, r, darker(fd.theme, 0.7) if on else (45, 35, 75), 235, GOLD if cursor or on else (150, 150, 175), 14,
              4 if cursor else 2)
        surf.blit(portrait(fd, 90), (r.centerx - 45, r.y + 4))
        text(surf, fd.name.split()[0], 26, WHITE, center=(r.centerx, r.bottom - 14), ow=2)


class ProgressScreen(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.bg = starfield_bg((14, 18, 54), (50, 30, 80))
        d = game.save
        self.ops = progress.op_stats(d)
        self.bests = progress.bests(d)
        self.week = progress.recent_days(d, game.today())
        self.answered, self.right = progress.totals(d)
        self.weak = progress.weakest_op(d)
        self.daily = progress.daily_status(d, game.today())

    def handle(self, ev):
        g = self.game
        if (ev.type == pygame.KEYDOWN and (ev.key in CONFIRM or ev.key == pygame.K_ESCAPE)) or \
                (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1):
            g.audio.play("confirm")
            g.goto(MainMenu(g))

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        text(surf, "MY PROGRESS", 78, GOLD, center=(W // 2, 52), ow=5)
        self.draw_ops(surf, pygame.Rect(40, 100, 640, 300))
        self.draw_bests(surf, pygame.Rect(696, 100, 544, 300))
        self.draw_week(surf, pygame.Rect(40, 414, 640, 256))
        self.draw_summary(surf, pygame.Rect(696, 414, 544, 256))
        text(surf, "Press ENTER to go back", 26, MUTED, center=(W // 2, H - 22), ow=2)

    def draw_ops(self, surf, r):
        panel(surf, r, (10, 10, 30), 215, (140, 140, 175), 14, 2)
        text(surf, "SHARE OF ANSWERS RIGHT", 34, WHITE, midleft=(r.x + 22, r.y + 30), ow=2)
        for i, (op, n, ok, avg) in enumerate(self.ops):
            y = r.y + 72 + i * 56
            text(surf, DISPLAY[op], 48, WHITE, center=(r.x + 40, y + 8), ow=3)
            text(surf, OP_NAMES[op], 28, WHITE, midleft=(r.x + 70, y - 8), ow=2)
            track = pygame.Rect(r.x + 70, y + 12, 380, 12)
            pygame.draw.rect(surf, BAR_TRACK, track, border_radius=6)
            if n:
                w = max(12, int(track.w * ok / n))
                pygame.draw.rect(surf, BAR, (track.x, track.y, w, track.h), border_radius=6)
                text(surf, f"{100 * ok // n}%", 40, WHITE, midright=(r.right - 18, y - 2), ow=2)
                detail = f"{n:,} answered" + (f", {avg:0.1f}s" if avg is not None else "")
                text(surf, detail, 22, MUTED, midright=(r.right - 18, y + 22), ow=1)
            else:
                text(surf, "Not tried yet", 26, MUTED, midright=(r.right - 18, y + 8), ow=2)

    def draw_bests(self, surf, r):
        b = self.bests
        panel(surf, r, (10, 10, 30), 215, (140, 140, 175), 14, 2)
        text(surf, "PERSONAL BESTS", 34, WHITE, midleft=(r.x + 22, r.y + 30), ow=2)
        scores = b.get("scores", {})
        rows = [("Top score", f"{max(scores.values()):,}" if scores else "-"),
                ("Most right in a row", str(b.get("streak", 0)) if b.get("streak") else "-"),
                ("Fastest right answer", f"{b['fastest']:0.2f}s" if "fastest" in b else "-"),
                ("Daily challenge score", f"{b['daily']:,}" if b.get("daily") else "-"),
                ("Longest daily streak", f"{b['day_streak']} days" if b.get("day_streak") else "-"),
                ("Special moves landed", f"{b.get('specials', 0):,}"),
                ("Tournaments won", f"{b.get('wins', 0):,}")]
        for i, (label, val) in enumerate(rows):
            y = r.y + 74 + i * 32
            text(surf, label, 28, MUTED, midleft=(r.x + 22, y), ow=2)
            text(surf, val, 32, WHITE, midright=(r.right - 22, y), ow=2)

    def draw_week(self, surf, r):
        panel(surf, r, (10, 10, 30), 215, (140, 140, 175), 14, 2)
        text(surf, "QUESTIONS ANSWERED, LAST 7 DAYS", 34, WHITE, midleft=(r.x + 22, r.y + 30), ow=2)
        top = max(1, max(n for _, n, _ in self.week))
        base = r.bottom - 42
        tall = 130
        pygame.draw.line(surf, (110, 110, 140), (r.x + 22, base), (r.right - 22, base), 1)
        slot = (r.w - 44) / 7
        for i, (day, n, _) in enumerate(self.week):
            cx = int(r.x + 22 + slot * (i + 0.5))
            h = int(tall * n / top)
            if n:
                pygame.draw.rect(surf, BAR, (cx - 15, base - h, 30, h + 1), border_top_left_radius=4,
                                 border_top_right_radius=4)
                text(surf, str(n), 26, WHITE, center=(cx, base - h - 14), ow=2)
            text(surf, date.fromisoformat(day).strftime("%a"), 24, MUTED, center=(cx, base + 18), ow=1)

    def draw_summary(self, surf, r):
        panel(surf, r, (10, 10, 30), 215, (140, 140, 175), 14, 2)
        text(surf, "SO FAR", 34, WHITE, midleft=(r.x + 22, r.y + 30), ow=2)
        pct = f"{100 * self.right // self.answered}%" if self.answered else "-"
        text(surf, f"{self.answered:,}", 72, WHITE, midleft=(r.x + 22, r.y + 88), ow=3)
        text(surf, "questions answered", 26, MUTED, midleft=(r.x + 22, r.y + 128), ow=2)
        text(surf, pct, 72, WHITE, midleft=(r.x + 300, r.y + 88), ow=3)
        text(surf, "right", 26, MUTED, midleft=(r.x + 300, r.y + 128), ow=2)
        text(surf, f"Daily streak: {self.daily['streak']}", 30, WHITE, midleft=(r.x + 22, r.y + 170), ow=2)
        tip = f"Good next step: practise {OP_NAMES[self.weak].lower()}" if self.weak else "Keep going to get a practice tip!"
        text(surf, tip, 30, (160, 220, 255), midleft=(r.x + 22, r.y + 210), ow=2)
