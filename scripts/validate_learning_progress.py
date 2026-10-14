"""Validate public learning progress records before building the blog."""
import argparse
import json
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def validate(as_of=None):
    raw = (ROOT / "data/learning_progress.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    assert data["version"] == 1, "Unsupported progress schema"
    updated = date.fromisoformat(data["updated"])
    cutoff = date.fromisoformat(as_of) if as_of else datetime.now(timezone(timedelta(hours=8))).date()
    assert updated <= cutoff, "Future learning records are not allowed"
    assert data["current_project"] in data["projects"], "Unknown current project"
    assert any(e["project"] == data["current_project"] and e["date"] == data["updated"] for e in data["entries"]), "Current project needs a latest-day record"
    assert isinstance(data["stage"], str) and data["stage"].strip()
    entries = data["entries"]
    assert entries, "Progress needs at least one record"
    seen = set()
    for entry in entries:
        day = date.fromisoformat(entry["date"])
        assert day <= updated, "Record date exceeds update date"
        assert entry["project"] in data["projects"], "Unknown project"
        key = (entry["date"], entry["project"])
        assert key not in seen, "Duplicate date/project record"
        seen.add(key)
        for field in ("title", "summary", "verification", "next"):
            assert isinstance(entry[field], str) and entry[field].strip(), "Empty " + field
        assert entry["status"] in ("reviewed", "in-progress")
        note = entry.get("note")
        if entry["status"] == "reviewed":
            assert note, "Reviewed records should link to their daily note"
        if note:
            assert re.fullmatch(r"/posts/[a-z0-9-]+/", note), "Invalid daily note URL"
            source = ROOT / "content" / note.strip("/") / "index.md"
            assert source.is_file(), "Missing daily note: " + note
            assert not re.search(r"(?m)^draft:\s*true\s*$", source.read_text(encoding="utf-8")), "Linked note is a draft"
    assert max(entry["date"] for entry in entries) == data["updated"], "Update date should match latest record"
    assert not re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[/\\]|file://", raw), "Remove local paths from public records"
    print("Learning progress OK: " + str(len(entries)) + " records")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", help="Confirmed publication date YYYY-MM-DD; defaults to UTC+08:00 today")
    validate(parser.parse_args().as_of)
