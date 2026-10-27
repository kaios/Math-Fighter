"""Top 10 score table, kept in the save file."""

MAX_ENTRIES = 10
NAME_LEN = 10


def table(data):
    """The saved scores, best first. Ignores anything malformed."""
    rows = [r for r in data.get("scores", []) if isinstance(r, dict) and isinstance(r.get("score"), int)]
    return sorted(rows, key=lambda r: -r["score"])[:MAX_ENTRIES]


def qualifies(data, score):
    rows = table(data)
    return score > 0 and (len(rows) < MAX_ENTRIES or score > rows[-1]["score"])


def add(data, name, score, level, fighter):
    """Adds a score and returns its place in the table (0 = top), or None
    if it didn't make the top 10. Ties keep the older score ahead."""
    name = (name.strip() or "PLAYER")[:NAME_LEN]
    entry = {"name": name, "score": score, "level": level, "fighter": fighter}
    rows = table(data)
    place = next((i for i, r in enumerate(rows) if score > r["score"]), len(rows))
    rows.insert(place, entry)
    data["scores"] = rows[:MAX_ENTRIES]
    return place if place < MAX_ENTRIES else None
