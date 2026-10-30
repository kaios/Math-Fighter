"""Keeps track of how a child is doing: per-operation stats, questions per day,
personal bests and the daily challenge. Plain data in the save file, with the
date always passed in so everything can be tested."""

from datetime import date, timedelta

from .mathq import OPS

KEEP_DAYS = 120
MILESTONES = (5, 10, 15, 20, 30, 40, 50, 75, 100)
# The daily challenge's theme rotates through these
THEMES = OPS + ("mix",)


def _p(data):
    p = data.get("progress")
    if not isinstance(p, dict):
        p = data["progress"] = {}
    for key in ("ops", "days", "bests", "daily", "scores"):
        if not isinstance(p.get(key), dict):
            p[key] = {}
    return p


def _trim(table):
    for key in sorted(table)[:-KEEP_DAYS]:
        del table[key]


def answered(data, op, correct, elapsed, day, streak, special=False):
    """Records one answer. streak is the run of correct answers including this
    one. Returns {"best_streak": bool, "milestone": n or None}."""
    p = _p(data)
    s = p["ops"].setdefault(op, {"n": 0, "ok": 0, "time": 0.0})
    d = p["days"].setdefault(day, {"n": 0, "ok": 0})
    s["n"] += 1
    d["n"] += 1
    _trim(p["days"])
    if not correct:
        return {}
    s["ok"] += 1
    d["ok"] += 1
    s["time"] += elapsed
    b = p["bests"]
    if elapsed < b.get("fastest", 1e9):
        b["fastest"] = round(elapsed, 2)
    if special:
        b["specials"] = b.get("specials", 0) + 1
    # a new best only counts as news after the first few answers ever
    new_best = streak > b.get("streak", 0)
    was_set = b.get("streak", 0) >= 5
    if new_best:
        b["streak"] = streak
    return {"best_streak": new_best and was_set, "milestone": streak if streak in MILESTONES else None}


def record_run(data, level, score):
    """A tournament run ended. True if it beat the best score for that level."""
    scores = _p(data)["scores"]
    key = str(level)
    new = score > scores.get(key, 0)
    if new:
        scores[key] = score
    return new


def tournament_won(data):
    b = _p(data)["bests"]
    b["wins"] = b.get("wins", 0) + 1


def op_stats(data):
    """[(op, answered, correct, average seconds or None)] for all four operations."""
    ops = _p(data)["ops"]
    rows = []
    for op in OPS:
        s = ops.get(op, {})
        n, ok = s.get("n", 0), s.get("ok", 0)
        rows.append((op, n, ok, s.get("time", 0.0) / ok if ok else None))
    return rows


def weakest_op(data, min_answers=5):
    """The operation to practise next: lowest share correct, once it has enough answers."""
    rows = [r for r in op_stats(data) if r[1] >= min_answers]
    if len(rows) < 2:
        return None
    return min(rows, key=lambda r: r[2] / r[1])[0]


def totals(data):
    rows = op_stats(data)
    return sum(r[1] for r in rows), sum(r[2] for r in rows)


def recent_days(data, day, count=7):
    """[(date, answered, correct)], oldest first, ending today."""
    today = date.fromisoformat(day)
    days = _p(data)["days"]
    out = []
    for i in range(count - 1, -1, -1):
        key = (today - timedelta(days=i)).isoformat()
        d = days.get(key, {})
        out.append((key, d.get("n", 0), d.get("ok", 0)))
    return out


def bests(data):
    p = _p(data)
    return dict(p["bests"], scores=dict(p["scores"]), day_streak=p["daily"].get("best_streak", 0),
                daily=p["daily"].get("best", 0))


def daily_theme(day, allowed):
    """Today's challenge theme: one operation, or everything mixed."""
    theme = THEMES[date.fromisoformat(day).toordinal() % len(THEMES)]
    return theme if theme in allowed else "mix"


def daily_status(data, day):
    """{"today": score or None, "streak": days in a row still alive, "best": best score}"""
    d = _p(data)["daily"]
    results = d.get("results", {})
    yesterday = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
    alive = d.get("last") in (day, yesterday)
    return {"today": results.get(day), "streak": d.get("streak", 0) if alive else 0, "best": d.get("best", 0)}


def daily_finish(data, day, score):
    """A daily challenge was finished. Replays can improve today's score, but
    only count once for the streak. Returns {"new_best", "new_today", "streak"}."""
    d = _p(data)["daily"]
    results = d.setdefault("results", {})
    yesterday = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
    if d.get("last") != day:
        d["streak"] = d.get("streak", 0) + 1 if d.get("last") == yesterday else 1
        d["last"] = day
    d["best_streak"] = max(d.get("best_streak", 0), d["streak"])
    new_today = score > results.get(day, -1)
    if new_today:
        results[day] = score
    _trim(results)
    new_best = score > d.get("best", 0)
    if new_best:
        d["best"] = score
    return {"new_best": new_best, "new_today": new_today, "streak": d["streak"]}
