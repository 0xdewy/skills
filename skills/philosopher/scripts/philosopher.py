#!/usr/bin/env python3
"""Search a philosopher's own writings. Texts download and index on first use."""
import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.request
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "catalog.json"
MIRROR = os.environ.get("PHILOSOPHER_MIRROR", "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt")
CACHE = Path(os.environ.get("PHILOSOPHER_CACHE") or
             Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "philosopher")
ORDINAL = "FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH"
TOP = re.compile(rf"(BOOK|Book|PART|Part|VOLUME|ESSAY|(THE )?({ORDINAL}) (BOOK|PART|ESSAY|SECTION|DIVISION))\b")
SUB = re.compile(r"(CHAPTER|CHAP\.|SECTION|SECT\.|LECTURE|LETTER)\b", re.I)
STOP = set("a an and are as at be but by do does for from had has have how i if in is it its me my "
           "not of on or our should so than that the their them then there these they this to was we "
           "were what when which who why will with would you your about say said think".split())
CHUNK = 1200


def die(msg):
    sys.exit(f"philosopher: {msg}")


def body(raw, work):
    """The philosopher's own text: no Gutenberg wrapper, no translator's introduction or notes."""
    text = raw.replace("\r", "")
    text = re.split(r"\*\*\* ?START OF TH[^\n]*\n", text, maxsplit=1)[-1]
    text, *footer = re.split(r"\*\*\* ?END OF TH", text, maxsplit=1)
    if not footer:
        die(f"download of {work['title']} is incomplete; run again")
    text = re.split(r"\nEnd of (the )?Project Gutenberg", text, maxsplit=1)[0]
    at = 0
    if start := work.get("start"):
        at = text.find(start)
        if at < 0:
            die(f"start marker {start!r} not found in {work['title']}")
        at = text.rfind("\n", 0, at) + 1
    if end := work.get("end"):
        hit = re.compile(rf"^[ \t]*{re.escape(end)}[ \t]*$", re.M).search(text, at)
        if not hit:
            die(f"end marker {end!r} not found in {work['title']}")
        text = text[:hit.start()]
    for _ in range(2):  # keep the headings directly above the opening, e.g. BOOK I / CHAPTER I
        above = text[:at].rstrip()
        cut = above.rfind("\n") + 1
        line = above[cut:].strip()
        alone = not above[:cut].strip() or above[:cut].endswith("\n\n")
        if not (alone and is_heading([line], line)) or line.strip(" .").upper() == work["title"].upper():
            break
        at = cut
    return text[at:]


def is_heading(lines, par):
    caps = len(lines) <= 3 and len(par) <= 200 and par.upper() == par and re.search(r"[A-Z]{2}", par)
    return bool(caps or (len(lines) == 1 and 0 < len(par) <= 80 and (SUB.match(par) or TOP.match(par))))


def pieces(par):
    """Split an overlong paragraph at sentence ends."""
    out = ""
    for sentence in re.split(r"(?<=[.?!;]) ", par):
        if out and len(out) + len(sentence) > CHUNK:
            yield out
            out = ""
        out = f"{out} {sentence}".strip()
    yield out


def chunks(text):
    """Yield (heading, passage): paragraphs packed to about CHUNK characters under one heading."""
    top = sub = buf = ""
    for par in re.split(r"\n\s*\n", text):
        lines = par.strip().splitlines()
        par = " ".join(" ".join(lines).split())
        if not par:
            continue
        heading = is_heading(lines, par)
        if heading or len(buf) + len(par) > CHUNK:
            if buf:
                yield " › ".join(filter(None, (top, sub))), buf
            buf = ""
        if heading:
            top, sub = (par, "") if TOP.match(par) else (top, par)
            continue
        for piece in pieces(par):
            if buf and len(buf) + len(piece) > CHUNK:
                yield " › ".join(filter(None, (top, sub))), buf
                buf = ""
            buf = f"{buf}\n\n{piece}".strip()
    if buf:
        yield " › ".join(filter(None, (top, sub))), buf


def load(path):
    return json.loads(Path(path).read_text())


def index(who, entry):
    """Open the philosopher's index, building it from the sources when missing or stale."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{who}.db"
    stamp = json.dumps([entry, Path(__file__).stat().st_mtime], sort_keys=True)  # rebuild on any change
    if path.exists():
        db = sqlite3.connect(path)
        try:
            if db.execute("select v from meta").fetchone()[0] == stamp:
                return db
        except sqlite3.Error:
            pass
        db.close()
    tmp = CACHE / f"{who}.{os.getpid()}.tmp"  # per process: parallel first searches must not share a build
    db = sqlite3.connect(tmp)
    db.execute("create table meta(v)")
    db.execute("create virtual table passages using fts5(work unindexed, heading unindexed, text, "
               "tokenize='porter unicode61 remove_diacritics 2')")
    for work in entry["works"]:
        url = MIRROR.format(id=work["id"])
        print(f"fetching {work['title']} …", file=sys.stderr)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "philosopher-skill"})
            raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8-sig")
        except OSError as err:
            die(f"cannot fetch {url}: {err}")
        db.executemany("insert into passages values (?,?,?)",
                       ((work["title"], h, t) for h, t in chunks(body(raw, work))))
    db.execute("insert into meta values (?)", (stamp,))
    db.commit()
    db.close()
    tmp.replace(path)
    return sqlite3.connect(path)


def show(entry, rows):
    by = {w["title"]: w for w in entry["works"]}
    for n, work, heading, text in rows:
        tr = by[work].get("translator")
        where = ", ".join(filter(None, (work, heading)))
        print(f"[#{n}] {where}" + (f" (tr. {tr})" if tr else "") + f"\n{text}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", default=CATALOG, help="catalog JSON (default: the bundled one)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="philosophers and their indexed works")
    s = sub.add_parser("search", help="passages most relevant to a query")
    s.add_argument("who")
    s.add_argument("query", nargs="+")
    s.add_argument("-n", type=int, default=5, help="passages to return (default 5)")
    r = sub.add_parser("read", help="one passage by number, with its neighbours")
    r.add_argument("who")
    r.add_argument("n", type=lambda v: int(v.lstrip("#")))
    r.add_argument("-c", type=int, default=1, help="passages of context each side (default 1)")
    args = ap.parse_args()
    catalog = load(args.catalog)

    if args.cmd == "list":
        for who, e in catalog.items():
            names = " / ".join((who, *e.get("aliases", [])))
            print(f"{names}: {e['name']} ({e['dates']}) — " + "; ".join(w["title"] for w in e["works"]))
            if e.get("note"):
                print(f"  note: {e['note']}")
        return
    who = next((k for k, e in catalog.items() if args.who.lower() in (k, *e.get("aliases", []))), None)
    entry = catalog.get(who) or die(f"unknown philosopher {args.who!r}; run `list`")
    db = index(who, entry)
    if args.cmd == "read":
        rows = db.execute("select rowid, work, heading, text from passages where rowid between ? and ?",
                          (args.n - args.c, args.n + args.c)).fetchall()
    else:
        words = [w for w in re.findall(r"\w+", " ".join(args.query).lower()) if w not in STOP]
        if not words:
            die("query has no searchable words")
        rows = db.execute("select rowid, work, heading, text from passages where passages match ? "
                          "order by bm25(passages) limit ?",
                          (" OR ".join(f'"{w}"' for w in words), args.n)).fetchall()
    if not rows:
        print("no passages found")
    show(entry, rows)


if __name__ == "__main__":
    main()
