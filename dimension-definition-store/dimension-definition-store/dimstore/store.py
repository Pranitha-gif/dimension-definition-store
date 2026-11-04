"""SQLite-backed, versioned store of dimension definitions."""
import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from .models import Dimension


class DimensionStore:
    def __init__(self, path: str = "dimensions.db"):
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS dimension_versions (
                   name TEXT NOT NULL,
                   version INTEGER NOT NULL,
                   definition TEXT NOT NULL,   -- JSON
                   change_note TEXT,
                   created_at TEXT NOT NULL,
                   PRIMARY KEY (name, version)
               )"""
        )
        self.conn.commit()

    def register(self, dim: Dimension, change_note: str = "") -> Dimension:
        """Validate and save. Identical re-registrations are no-ops;
        any change creates a new version."""
        dim.validate()
        latest = self.get(dim.name)
        body = dim.to_dict()
        body["version"] = None
        if latest:
            old = latest.to_dict()
            old["version"] = None
            if old == body:
                return latest
        version = (latest.version + 1) if latest else 1
        dim.version = version
        stored = dim.to_dict()
        self.conn.execute(
            "INSERT INTO dimension_versions VALUES (?, ?, ?, ?, ?)",
            (dim.name, version, json.dumps(stored), change_note,
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        self.conn.commit()
        return dim

    def get(self, name: str, version: Optional[int] = None) -> Optional[Dimension]:
        if version is None:
            row = self.conn.execute(
                "SELECT definition FROM dimension_versions WHERE name=? "
                "ORDER BY version DESC LIMIT 1", (name,)).fetchone()
        else:
            row = self.conn.execute(
                "SELECT definition FROM dimension_versions WHERE name=? AND version=?",
                (name, version)).fetchone()
        return Dimension.from_dict(json.loads(row[0])) if row else None

    def list_latest(self) -> List[Dimension]:
        names = [r[0] for r in self.conn.execute(
            "SELECT DISTINCT name FROM dimension_versions ORDER BY name")]
        return [self.get(n) for n in names]

    def history(self, name: str):
        return self.conn.execute(
            "SELECT version, change_note, created_at FROM dimension_versions "
            "WHERE name=? ORDER BY version", (name,)).fetchall()

    def search(self, text: str) -> List[Dimension]:
        t = text.lower()
        out = []
        for d in self.list_latest():
            hay = " ".join([d.name, d.description, d.grain, " ".join(d.tags),
                            " ".join(a.name + " " + a.description for a in d.attributes)])
            if t in hay.lower():
                out.append(d)
        return out

    def diff(self, name: str, v1: int, v2: int) -> List[str]:
        a, b = self.get(name, v1), self.get(name, v2)
        if not a or not b:
            raise KeyError(f"Version not found for '{name}'")
        changes = []
        for f in ("description", "grain", "source_table", "owner", "scd_type", "tags"):
            if getattr(a, f) != getattr(b, f):
                changes.append(f"{f}: {getattr(a, f)!r} -> {getattr(b, f)!r}")
        am = {x.name: x for x in a.attributes}
        bm = {x.name: x for x in b.attributes}
        for n in sorted(bm.keys() - am.keys()):
            changes.append(f"+ attribute {n} ({bm[n].data_type})")
        for n in sorted(am.keys() - bm.keys()):
            changes.append(f"- attribute {n}")
        for n in sorted(am.keys() & bm.keys()):
            if am[n] != bm[n]:
                changes.append(f"~ attribute {n}: {am[n]} -> {bm[n]}")
        return changes
