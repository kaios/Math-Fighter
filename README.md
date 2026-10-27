# Math Fighter: Tournament of Numbers

An anime-style fighting game for kids where every punch, kick and block is
powered by a math question. Pick a fighter, choose a level from 1 (easy) to
5 (hardest), and battle through 4 stages to become the **Math Tournament
Champion**.

## The fighters

| Fighter | Math power | Special move |
|---|---|---|
| **Kai Blaze**, the Addition Ace | Addition (+) | Plus Blaster |
| **Luna Shade**, the Division Ninja | Division (÷) | Split Shuriken |
| **Dax Steel**, the Subtraction Knight | Subtraction (−) | Minus Slash |
| **Mira Nova**, the Multiplication Star | Multiplication (×) | Times Tornado |

When you attack, you answer a question in your own fighter's math. When the
CPU attacks, you answer a question in the *attacker's* math to block it. For
example, Kai attacks with addition but must answer subtraction to block Dax.

### Final boss: Ninja Ryu

**Ninja Ryu**, the Grand Master, waits on stage 4. His attacks use a random mix
of all four operations, and you get only **3 seconds** to block them (your own
attacks on him still give you 5 seconds).

## Stages

1. **Sakura Temple**: Kyoto Mountains, Japan (sunset, falling cherry blossoms)
2. **Neon Rooftop**: Downtown Number City (night skyline, blinking neon math signs)
3. **Magma Crater**: Mount Calculus Volcano (lava cracks, rising embers)
4. **Aurora Ice Palace**: The Frozen North Pole (northern lights, snow)

Your first opponent is picked at random by the CPU, and the next two are the
other fighters in random order. The final boss on stage 4 is **Ninja Ryu**.
You never fight the same opponent twice.

## How to play

* Non-stop math action: once a fight starts you never press SPACE or ENTER. You
  and the CPU take turns automatically (you attack, the CPU attacks, and so on),
  and rounds and stages follow on by themselves. You only type answers.
* On your turn, a question in your fighter's math appears and you have **5 seconds**.
  * Right answer: your attack hits.
  * Wrong or too slow: you miss.
* When the CPU attacks, a question in the **CPU fighter's** math appears and you have **5 seconds**.
  * Right answer: you **block**.
  * Right answer in under **2.5 seconds**: you block **and counter attack**!
    (Against Ninja Ryu: 3 seconds to block, under 1.5 seconds to counter.)
  * Wrong or too slow: you get hit.
* Type answers with the **number keys**. There is no ENTER: the answer is checked
  as soon as you have typed as many digits as the right answer has (the answer box
  shows one slot per digit). For 5 × 10 you must type 5 then 0. BACKSPACE fixes a
  digit before the last one.
* 8 hits and a fighter is knocked out. Each round lasts 99 seconds (when time runs out,
  the fighter who took fewer hits wins). Win 2 of 3 rounds to clear a stage.
* After a wrong answer the game always shows the right answer, so kids learn from it.
* Win all 4 stages, watch the credits, then play again at the next level up.

Other keys: **T** top 10 (on the title screen), **ESC/P** pause, **M** music on/off (sound effects stay on; the
choice is remembered), **F11** full screen. On a touch screen, an on-screen
number pad and a pause button appear automatically; tap **MUSIC** on the title
screen or the music line on the pause screen to switch music on or off.

Every stage has its own song (plus the title and champion screens), and each
song has an intro, verses and a chorus, so it runs for about a minute before
repeating.

### Score and the Top 10

| You did | Points |
|---|---|
| Right answer | 100, plus up to 100 more for answering fast |
| Counter attack (a fast block) | +100 |
| Won a round | +500 |
| Perfect round (won without getting hit) | +1000 more |

All points are multiplied by the level number (the bonus level counts as 6),
so harder levels score more. Your score is shown at the bottom left during
fights.

When a run ends (you win the tournament, or lose a match) with a score in
the top 10, you type a name of up to 10 characters (keyboard, or the
on-screen keys on a touch screen), and the Top 10 table shows where you
placed. See the table any time with **T** or the **TOP 10** button on the title
screen. Trying a stage again after a loss starts a fresh score. Scores are
kept in the save file.

### Difficulty levels

| Level | Add / Subtract | Multiply / Divide |
|---|---|---|
| 1 Rookie | numbers up to 5 | tables 1–3 |
| 2 Fighter | numbers up to 10 | tables up to 5 × 10 |
| 3 Warrior | two digits and one digit (e.g. 24 + 7) | up to 10 × 10 |
| 4 Master | two digits and two digits | up to 12 × 12 |
| 5 Legend | three digits and two digits | two digits × one digit (e.g. 17 × 6) |
| 6 BONUS | fractions (e.g. 1/4 + 1/2) | fractions (e.g. 2/3 × 3/4, 1/4 ÷ 1/2) |

Subtraction never goes below zero and division always comes out even.

**Bonus level (fractions)** unlocks after you win the tournament on level 5
(Legend), and stays unlocked. Every answer is a fraction between 0 and 1 in
simplest form. Type the top number, then the bottom number: for 3/4 type 3
then 4 (the slash is already shown). Fraction questions give **8 seconds**
instead of 5, and blocking Ninja Ryu gives 4.8 seconds instead of 3.

## Version

The version number lives in `mathfighter/config.py` (`__version__`). The
.deb, Windows and Android builds all read it from there, and it is shown on
the title screen.

## Running it

Requires Python 3.8+ and pygame 2.

```bash
pip install -r requirements.txt
python3 main.py
```

There are no image or sound files. All characters, stages, sound effects and
music are generated by the code, so the game is easy to share and port. The
songs are composed on the first run and cached as .wav files next to the save
file (`~/.local/share/MathFighter` on Linux, `%APPDATA%\MathFighter` on Windows).

## Building

**Linux:** `./build_linux.sh` creates `dist/MathFighter`, a single executable.

**Debian / Ubuntu package:** `./build_deb.sh` creates
`dist/mathfighter_<version>_amd64.deb`. It contains the self-contained executable
(no Python or pygame needed on the target), a menu entry and an icon.
Install it with `sudo apt install ./dist/mathfighter_*_amd64.deb`, then
start it from the Games menu or by typing `mathfighter`. Remove it with
`sudo apt remove mathfighter`.

**Windows:** on Linux, `./build_windows_wine.sh` builds `dist/MathFighter-<version>.exe`
using Windows Python under Wine (it downloads Python into `~/.wine-mathfighter`
the first time). On a Windows PC with Python 3 installed, double-click
`build_windows.bat` instead; it creates `dist\MathFighter.exe`.

**Android (10 and newer):** use [Buildozer](https://buildozer.readthedocs.io) on Linux.
`buildozer.spec` is already set up (Android 10+ / API 29, targets API 35,
landscape, fullscreen, 64-bit and 32-bit ARM). `p4a-recipes/pygame` makes the
build use pygame 2.6.1, because the stock pygame 2.1.0 recipe no longer
compiles with the Python 3.14 that python-for-android ships.

```bash
sudo apt install -y git zip unzip openjdk-17-jdk autoconf libtool pkg-config \
     zlib1g-dev libncurses5-dev libncursesw5-dev cmake libffi-dev libssl-dev
python3 -m venv ~/.venvs/buildozer
~/.venvs/buildozer/bin/pip install buildozer cython setuptools
# Buildozer only notices the venv when VIRTUAL_ENV is set (activating it does that)
. ~/.venvs/buildozer/bin/activate
buildozer android debug   # first build downloads the Android SDK/NDK: slow, ~7 GB of disk
# APK ends up in bin/ ; install with:  adb install bin/*.apk
```

To install without adb, copy the APK to the phone, open it, and allow
"install unknown apps" when Android asks.

The game already runs at a fixed 1280×720 internal resolution scaled to any
screen, detects Android, and supports touch (number pad, tap
to pause, Android back button).

## Tests

```bash
python3 -m unittest discover -s tests
```

The tests check every question generator (correct, whole-number, non-negative
answers at all levels) and play complete headless games: a perfect player
wins the tournament and reaches the credits, a player who always answers wrong
gets Game Over, and a timeout counts as a hit.

## Project layout

```
main.py                 entry point
mathfighter/
  config.py             rules (5 s answers, 99 s rounds, 8 hits, best of 3) and credits name
  mathq.py              question generator for each operation and level
  characters.py         the four fighters + the final boss, Ninja Ryu
  sprite.py             procedural anime sprite rig, poses and animations
  draw.py               anti-aliased cel-shaded drawing helpers
  stages.py             the four arenas
  battle.py             the fight: rounds, questions, attacks, blocks, counters, KOs
  scenes.py             title, how-to, difficulty, select, versus, game over, champion,
                        name entry, top 10, credits
  effects.py            particles, hit sparks, projectiles, screen shake
  audio.py              synthesized sound effects and a composer for the songs
  ui.py                 text, panels, touch keypad
  save.py               save file: bonus unlock, music setting, top 10
  highscores.py         the top 10 score table
  game.py               main loop and tournament progression
```

## Credits

Created by Shawn Rapaz and Claude.
