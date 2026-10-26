"""Tiny synthesizer: all sound effects and music are generated at startup,
so the game ships without any audio files. Fails silently with no sound card."""

import math
import random
import threading
from array import array

import pygame

RATE = 22050


def _env(i, n, attack=0.005, release=0.6):
    t = i / RATE
    a = min(1.0, t / attack) if attack > 0 else 1.0
    r = max(0.0, 1 - (i / n) ** (1 / max(0.05, release)))
    return a * r


def _tone(freqs, dur, wave="square", vol=0.5, slide=0.0, noise=0.0, release=0.6):
    n = int(RATE * dur)
    out = [0.0] * n
    rnd = random.Random(7)
    for f0 in freqs:
        ph = 0.0
        for i in range(n):
            f = f0 * (1 + slide * i / n)
            ph += f / RATE
            x = ph % 1.0
            if wave == "square":
                v = 1.0 if x < 0.5 else -1.0
            elif wave == "saw":
                v = 2 * x - 1
            elif wave == "tri":
                v = 4 * abs(x - 0.5) - 1
            else:
                v = math.sin(ph * math.tau)
            out[i] += v * vol / len(freqs) * _env(i, n, release=release)
    if noise:
        for i in range(n):
            out[i] += rnd.uniform(-1, 1) * noise * _env(i, n, 0.001, 0.3)
    return out


def _mix_into(buf, samples, start, vol=1.0):
    end = min(len(buf), start + len(samples))
    for i in range(start, end):
        buf[i] += samples[i - start] * vol


class Audio:
    def __init__(self):
        self.ok = False
        self.sounds = {}
        self.music = {}
        self.channel = None
        self.want = None
        self.enabled = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(RATE, -16, 1, 512)
            self.freq, _, self.chans = pygame.mixer.get_init()
            self.ok = True
        except Exception:
            return
        self._make_sfx()
        threading.Thread(target=self._make_music, daemon=True).start()

    def _to_sound(self, samples):
        data = array("h")
        reps = self.chans
        step = RATE / self.freq
        n = int(len(samples) / step)
        for i in range(n):
            v = int(max(-1.0, min(1.0, samples[int(i * step)])) * 32000)
            for _ in range(reps):
                data.append(v)
        return pygame.mixer.Sound(buffer=data.tobytes())

    def _make_sfx(self):
        defs = {
            "hit": _tone([90], 0.22, "sine", 0.9, -0.6, noise=0.7, release=0.4),
            "bighit": _tone([70, 55], 0.45, "sine", 1.0, -0.7, noise=0.8, release=0.5),
            "block": _tone([880, 1320], 0.18, "tri", 0.5, -0.1, noise=0.2, release=0.3),
            "whoosh": _tone([200], 0.25, "sine", 0.05, 1.0, noise=0.35, release=0.8),
            "correct": _tone([660], 0.09, "square", 0.3) + _tone([990], 0.16, "square", 0.3),
            "wrong": _tone([220], 0.14, "saw", 0.35, -0.2) + _tone([160], 0.22, "saw", 0.35, -0.2),
            "tick": _tone([1200], 0.04, "square", 0.18, release=0.2),
            "select": _tone([520], 0.06, "square", 0.25, release=0.3),
            "confirm": _tone([520, 780], 0.08, "square", 0.3) + _tone([780, 1040], 0.18, "square", 0.3),
            "fire": _tone([300], 0.35, "saw", 0.3, 1.5, noise=0.15, release=0.7),
            "ko": _tone([110, 82], 0.9, "saw", 0.6, -0.6, noise=0.3, release=0.8),
            "fight": _tone([392, 494, 587], 0.12, "square", 0.35) + _tone([523, 659, 784], 0.35, "square", 0.35),
        }
        for k, v in defs.items():
            self.sounds[k] = self._to_sound(v)

    def _make_music(self):
        songs = {
            # key: (bpm, root midi, progression of chord roots, scale)
            "menu": (118, 60, [0, 9, 5, 7], [0, 2, 4, 7, 9]),  # first: the title needs it
            0: (112, 57, [0, 5, 3, 7], [0, 2, 4, 7, 9]),     # Sakura: pentatonic
            1: (128, 52, [0, 0, 8, 10], [0, 3, 5, 7, 10]),   # Neon: minor
            2: (140, 50, [0, 1, 0, 10], [0, 1, 4, 5, 7]),    # Magma: phrygian-ish
            3: (100, 55, [0, 8, 3, 10], [0, 2, 3, 7, 9]),    # Aurora
        }
        for key, (bpm, root, prog, scale) in songs.items():
            try:
                self.music[key] = self._to_sound(self._song(bpm, root, prog, scale, key))
            except Exception:
                pass

    def _song(self, bpm, root, prog, scale, seed):
        rnd = random.Random(str(seed))
        beat = 60 / bpm
        eighth = beat / 2
        bars = len(prog) * 2
        total = int(RATE * beat * 4 * bars)
        buf = [0.0] * total

        def hz(m):
            return 440 * 2 ** ((m - 69) / 12)

        cache = {}

        def note(m, dur, wave, vol):
            k = (m, dur, wave)
            if k not in cache:
                cache[k] = _tone([hz(m)], dur, wave, 1.0, release=0.5)
            return cache[k], vol

        kick = _tone([60], 0.15, "sine", 1.0, -0.5, release=0.3)
        snare = _tone([200], 0.12, "tri", 0.2, noise=0.6, release=0.3)
        hat = _tone([8000], 0.03, "sine", 0.0, noise=0.25, release=0.2)
        melody = [rnd.choice(scale) + 12 * rnd.choice([0, 0, 1]) for _ in range(16)]
        for bar in range(bars):
            ch = prog[(bar // 2) % len(prog)]
            for step in range(8):
                pos = int(RATE * (bar * 4 * beat + step * eighth))
                b, v = note(root - 12 + ch + (12 if step % 2 else 0), eighth * 0.9, "tri", 0.32)
                _mix_into(buf, b, pos, v)
                a, v = note(root + ch + [0, 4, 7, 12][step % 4] - (1 if scale[2] == 3 and step % 4 == 1 else 0),
                            eighth * 0.6, "square", 0.07)
                _mix_into(buf, a, pos, v)
                if step % 4 == 0:
                    _mix_into(buf, kick, pos, 0.5)
                if step % 4 == 2:
                    _mix_into(buf, snare, pos, 0.35)
                _mix_into(buf, hat, pos, 0.3)
                if bar % 2 == 1 or step % 2 == 0:
                    m = melody[(bar * 8 + step) % 16]
                    if (bar * 8 + step) % 3 != 2:
                        s, v = note(root + 12 + m, eighth * 0.85, "square", 0.09)
                        _mix_into(buf, s, pos, v)
        return buf

    def play(self, name):
        if self.ok and self.enabled and name in self.sounds:
            self.sounds[name].play()

    def play_music(self, key):
        """Music is generated in the background; it starts as soon as it is ready."""
        if self.want == key and self.channel:
            return
        self.stop_music()
        self.want = key

    def stop_music(self):
        self.want = None
        if self.channel:
            self.channel.fadeout(400)
            self.channel = None

    def update(self):
        if self.ok and self.enabled and self.want is not None and self.channel is None:
            snd = self.music.get(self.want)
            if snd:
                self.channel = snd.play(loops=-1, fade_ms=500)
                if self.channel:
                    self.channel.set_volume(0.5)

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            pygame.mixer.stop()
            self.channel = None
        elif self.want is not None:
            self.channel = None
        return self.enabled
