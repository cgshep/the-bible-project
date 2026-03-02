#!/usr/bin/env python3
"""
Static site generator for The Holy Bible.
Generates a beautiful, static HTML website with sidebar navigation
and multiple public-domain Bible translations.

URL structure:
  site/
    index.html                          (home / landing)
    style.css
    {version}/index.html                (version home — book grid)
    {version}/{book-slug}/index.html    (book — chapter grid)
    {version}/{book-slug}/{ch}.html     (chapter reading page)
"""

import json
import os
import re
import html as htmlmod

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = "site"

VERSIONS = [
    {"id": "kjv",     "file": "data/kjv.json",     "name": "King James Version",            "abbr": "KJV",     "year": "1769", "fmt": "aruljohn"},
    {"id": "asv",     "file": "data/asv.json",      "name": "American Standard Version",     "abbr": "ASV",     "year": "1901", "fmt": "scrollmapper"},
    {"id": "ylt",     "file": "data/ylt.json",      "name": "Young's Literal Translation",   "abbr": "YLT",     "year": "1898", "fmt": "scrollmapper"},
    {"id": "darby",   "file": "data/darby.json",    "name": "Darby Bible",                   "abbr": "Darby",   "year": "1889", "fmt": "scrollmapper"},
    {"id": "webster", "file": "data/webster.json",  "name": "Webster Bible",                 "abbr": "Webster", "year": "1833", "fmt": "scrollmapper"},
    {"id": "bbe",     "file": "data/bbe.json",      "name": "Bible in Basic English",        "abbr": "BBE",     "year": "1965", "fmt": "scrollmapper"},
    {"id": "drc",     "file": "data/drc.json",      "name": "Douay-Rheims Challoner",        "abbr": "DRC",     "year": "1752", "fmt": "scrollmapper"},
    {"id": "masonic", "file": "data/kjv.json",      "name": "Masonic Edition (KJV)",         "abbr": "Masonic", "year": "1769", "fmt": "aruljohn", "theme": "masonic"},
]

DEFAULT_VERSION = "kjv"

CANONICAL_ORDER = [
    "Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth",
    "1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles",
    "Ezra","Nehemiah","Esther","Job","Psalms","Proverbs","Ecclesiastes",
    "Song of Solomon","Isaiah","Jeremiah","Lamentations","Ezekiel","Daniel",
    "Hosea","Joel","Amos","Obadiah","Jonah","Micah","Nahum","Habakkuk",
    "Zephaniah","Haggai","Zechariah","Malachi",
    "Matthew","Mark","Luke","John","Acts","Romans",
    "1 Corinthians","2 Corinthians","Galatians","Ephesians","Philippians","Colossians",
    "1 Thessalonians","2 Thessalonians","1 Timothy","2 Timothy","Titus","Philemon",
    "Hebrews","James","1 Peter","2 Peter","1 John","2 John","3 John","Jude","Revelation"
]

OT_BOOKS = CANONICAL_ORDER[:39]
NT_BOOKS = CANONICAL_ORDER[39:]

# Map variant book names to canonical names
NAME_NORMALIZE = {
    "I Samuel": "1 Samuel", "II Samuel": "2 Samuel",
    "I Kings": "1 Kings", "II Kings": "2 Kings",
    "I Chronicles": "1 Chronicles", "II Chronicles": "2 Chronicles",
    "I Corinthians": "1 Corinthians", "II Corinthians": "2 Corinthians",
    "I Thessalonians": "1 Thessalonians", "II Thessalonians": "2 Thessalonians",
    "I Timothy": "1 Timothy", "II Timothy": "2 Timothy",
    "I Peter": "1 Peter", "II Peter": "2 Peter",
    "I John": "1 John", "II John": "2 John", "III John": "3 John",
    "Revelation of John": "Revelation",
}

# Short abbreviations for sidebar
BOOK_ABBR = {
    "Genesis": "Gen", "Exodus": "Exod", "Leviticus": "Lev", "Numbers": "Num",
    "Deuteronomy": "Deut", "Joshua": "Josh", "Judges": "Judg", "Ruth": "Ruth",
    "1 Samuel": "1 Sam", "2 Samuel": "2 Sam", "1 Kings": "1 Kgs", "2 Kings": "2 Kgs",
    "1 Chronicles": "1 Chr", "2 Chronicles": "2 Chr", "Ezra": "Ezra",
    "Nehemiah": "Neh", "Esther": "Esth", "Job": "Job", "Psalms": "Ps",
    "Proverbs": "Prov", "Ecclesiastes": "Eccl", "Song of Solomon": "Song",
    "Isaiah": "Isa", "Jeremiah": "Jer", "Lamentations": "Lam", "Ezekiel": "Ezek",
    "Daniel": "Dan", "Hosea": "Hos", "Joel": "Joel", "Amos": "Amos",
    "Obadiah": "Obad", "Jonah": "Jonah", "Micah": "Mic", "Nahum": "Nah",
    "Habakkuk": "Hab", "Zephaniah": "Zeph", "Haggai": "Hag", "Zechariah": "Zech",
    "Malachi": "Mal", "Matthew": "Matt", "Mark": "Mark", "Luke": "Luke",
    "John": "John", "Acts": "Acts", "Romans": "Rom",
    "1 Corinthians": "1 Cor", "2 Corinthians": "2 Cor",
    "Galatians": "Gal", "Ephesians": "Eph", "Philippians": "Phil",
    "Colossians": "Col", "1 Thessalonians": "1 Thess", "2 Thessalonians": "2 Thess",
    "1 Timothy": "1 Tim", "2 Timothy": "2 Tim", "Titus": "Titus",
    "Philemon": "Phlm", "Hebrews": "Heb", "James": "Jas",
    "1 Peter": "1 Pet", "2 Peter": "2 Pet",
    "1 John": "1 Jn", "2 John": "2 Jn", "3 John": "3 Jn",
    "Jude": "Jude", "Revelation": "Rev",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def esc(text):
    return htmlmod.escape(text, quote=True)

def load_version(ver_cfg):
    """Load a version JSON and normalize to a dict keyed by canonical book name."""
    with open(ver_cfg["file"]) as f:
        raw = json.load(f)

    if ver_cfg["fmt"] == "aruljohn":
        book_list = raw  # list of {book, chapters: [{chapter, verses:[{verse,text}]}]}
        name_key = "book"
    else:
        book_list = raw["books"]
        name_key = "name"

    books = {}
    for b in book_list:
        raw_name = b[name_key]
        canon_name = NAME_NORMALIZE.get(raw_name, raw_name)
        if canon_name not in set(CANONICAL_ORDER):
            continue  # skip apocryphal books
        chapters = []
        for ch in b["chapters"]:
            verses = []
            for v in ch["verses"]:
                verses.append({
                    "verse": str(v["verse"]),
                    "text": v["text"].strip(),
                })
            chapters.append({
                "chapter": str(ch["chapter"]),
                "verses": verses,
            })
        books[canon_name] = {"book": canon_name, "chapters": chapters}
    return books


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');

/* ── Reset ─────────────────────────────────────────────────────────────── */

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --parchment:  #faf6ed;
  --cream:      #f5f0e3;
  --sidebar-bg: #2c1810;
  --sidebar-fg: #d8cfc0;
  --sidebar-hi: #e8d5a0;
  --sidebar-w:  280px;
  --gold:       #b8860b;
  --gold-light: #d4a843;
  --gold-faint: #e8d5a0;
  --ink:        #2c1810;
  --ink-light:  #5a3e2b;
  --ink-faint:  #8b7355;
  --wine:       #722f37;
  --wine-dark:  #4a1c23;
  --white:      #fffdf7;
  --shadow:     rgba(44, 24, 16, .08);
}

html { font-size: 18px; scroll-behavior: smooth; }

body {
  font-family: 'Libre Baskerville', 'Georgia', 'Times New Roman', serif;
  background: var(--parchment);
  color: var(--ink);
  line-height: 1.8;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}

/* ── Layout shell ──────────────────────────────────────────────────────── */

.page-wrap {
  display: flex;
  min-height: 100vh;
}

/* ── Sidebar ───────────────────────────────────────────────────────────── */

.sidebar {
  position: fixed;
  top: 0; left: 0; bottom: 0;
  width: var(--sidebar-w);
  background: var(--sidebar-bg);
  color: var(--sidebar-fg);
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 100;
  display: flex;
  flex-direction: column;
  border-right: 2px solid var(--gold);
  scrollbar-width: thin;
  scrollbar-color: #5a3e2b #2c1810;
}

.sidebar::-webkit-scrollbar { width: 6px; }
.sidebar::-webkit-scrollbar-track { background: var(--sidebar-bg); }
.sidebar::-webkit-scrollbar-thumb { background: #5a3e2b; border-radius: 3px; }

.sidebar-header {
  padding: 1.3rem 1rem .8rem;
  text-align: center;
  border-bottom: 1px solid rgba(232, 213, 160, .2);
  flex-shrink: 0;
}
.sidebar-header a {
  text-decoration: none;
  color: inherit;
}
.sidebar-title {
  font-size: .85rem;
  font-weight: 700;
  color: var(--gold-faint);
  letter-spacing: .12em;
  text-transform: uppercase;
}
.sidebar-ornament {
  color: var(--gold);
  font-size: .7rem;
  letter-spacing: .4em;
  margin-top: .2rem;
  user-select: none;
}

/* Version selector */
.version-select-wrap {
  padding: .6rem 1rem;
  border-bottom: 1px solid rgba(232, 213, 160, .15);
  flex-shrink: 0;
}
.version-select-wrap label {
  display: block;
  font-size: .55rem;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--gold);
  margin-bottom: .3rem;
}
.version-select {
  width: 100%;
  padding: .35rem .5rem;
  font-family: inherit;
  font-size: .7rem;
  background: rgba(255,253,247,.08);
  color: var(--sidebar-fg);
  border: 1px solid rgba(232, 213, 160, .25);
  cursor: pointer;
  letter-spacing: .03em;
}
.version-select:focus {
  outline: 1px solid var(--gold);
}
.version-select option {
  background: var(--sidebar-bg);
  color: var(--sidebar-fg);
}

/* Testament group */
.sb-testament {
  font-size: .55rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .15em;
  color: var(--gold);
  padding: .7rem 1rem .3rem;
  user-select: none;
}

/* Book list */
.sb-books {
  list-style: none;
  padding: 0;
}
.sb-book-item {
  position: relative;
}
.sb-book-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: .28rem 1rem;
  font-size: .72rem;
  color: var(--sidebar-fg);
  text-decoration: none;
  transition: all .15s;
  border-left: 2px solid transparent;
}
.sb-book-link:hover {
  background: rgba(232, 213, 160, .08);
  color: var(--gold-faint);
  border-left-color: var(--gold);
}
.sb-book-link.active {
  background: rgba(232, 213, 160, .12);
  color: var(--gold-faint);
  border-left-color: var(--gold);
  font-weight: 700;
}
.sb-book-link .abbr {
  color: inherit;
}
.sb-book-link .count {
  font-size: .55rem;
  color: rgba(216, 207, 192, .4);
  font-style: italic;
}

/* Chapter list inside sidebar (when book is active) */
.sb-chapters {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  padding: .3rem 1rem .5rem 1.6rem;
  background: rgba(0,0,0,.15);
}
.sb-ch-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 1.6rem;
  font-size: .62rem;
  color: var(--sidebar-fg);
  text-decoration: none;
  border: 1px solid rgba(232, 213, 160, .12);
  transition: all .15s;
}
.sb-ch-link:hover {
  background: var(--wine);
  color: var(--white);
  border-color: var(--wine);
}
.sb-ch-link.active {
  background: var(--gold);
  color: var(--sidebar-bg);
  border-color: var(--gold);
  font-weight: 700;
}

/* Sidebar toggle (mobile) */
.sidebar-toggle {
  display: none;
  position: fixed;
  top: .6rem; left: .6rem;
  z-index: 200;
  background: var(--sidebar-bg);
  color: var(--gold-faint);
  border: 1px solid var(--gold);
  width: 2.4rem; height: 2.4rem;
  font-size: 1.1rem;
  cursor: pointer;
  align-items: center;
  justify-content: center;
  font-family: inherit;
}
.sidebar-close {
  display: none;
  position: absolute;
  top: .4rem; right: .4rem;
  background: none;
  border: none;
  color: var(--sidebar-fg);
  font-size: 1.1rem;
  cursor: pointer;
  padding: .2rem .4rem;
}

/* ── Main content ──────────────────────────────────────────────────────── */

.content {
  flex: 1;
  margin-left: var(--sidebar-w);
  min-height: 100vh;
  position: relative;
}
.content::before {
  content: '';
  position: fixed;
  top: 8px; right: 8px; bottom: 8px;
  left: calc(var(--sidebar-w) + 8px);
  border: 2px solid var(--gold-faint);
  pointer-events: none;
  z-index: 50;
}

.content-header {
  text-align: center;
  padding: 2rem 1rem 1rem;
}
.content-header h1 {
  font-size: 2.2rem;
  font-weight: 700;
  color: var(--wine-dark);
  letter-spacing: .12em;
  text-transform: uppercase;
}
.content-header .subtitle {
  font-size: .85rem;
  font-style: italic;
  color: var(--ink-faint);
  letter-spacing: .06em;
  margin-top: .1rem;
}

.ornament {
  text-align: center;
  color: var(--gold);
  font-size: 1rem;
  letter-spacing: .5em;
  margin: .6rem 0;
  user-select: none;
}

main {
  max-width: 52rem;
  margin: 0 auto;
  padding: 0 2rem 4rem;
}

/* ── Home page (landing) ───────────────────────────────────────────────── */

.home-hero {
  text-align: center;
  padding: 4rem 2rem 2rem;
}
.home-hero h1 {
  font-size: 3rem;
  font-weight: 700;
  color: var(--wine-dark);
  letter-spacing: .15em;
  text-transform: uppercase;
  margin-bottom: .3rem;
}
.home-hero .subtitle {
  font-size: 1rem;
  font-style: italic;
  color: var(--ink-faint);
  letter-spacing: .08em;
}
.home-ornament {
  text-align: center;
  color: var(--gold);
  font-size: 1.2rem;
  letter-spacing: .6em;
  margin: 1.5rem 0;
  user-select: none;
}

.version-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1.2rem;
  max-width: 58rem;
  margin: 0 auto;
  padding: 0 2rem 4rem;
}
.version-card {
  display: block;
  background: var(--white);
  border: 1px solid var(--gold-faint);
  padding: 1.5rem 1.6rem;
  text-decoration: none;
  color: var(--ink);
  transition: all .25s;
  position: relative;
  overflow: hidden;
}
.version-card::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0;
  width: 100%; height: 2px;
  background: var(--gold);
  transform: scaleX(0);
  transform-origin: center;
  transition: transform .3s;
}
.version-card:hover {
  border-color: var(--gold-light);
  box-shadow: 0 6px 20px var(--shadow);
  transform: translateY(-2px);
}
.version-card:hover::after { transform: scaleX(1); }
.version-card .vc-abbr {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--wine-dark);
  letter-spacing: .08em;
}
.version-card .vc-name {
  font-size: .82rem;
  color: var(--ink-light);
  margin-top: .15rem;
}
.version-card .vc-year {
  font-size: .7rem;
  font-style: italic;
  color: var(--ink-faint);
  margin-top: .3rem;
}

/* ── Testament sections ────────────────────────────────────────────────── */

.testament-title {
  font-size: 1.05rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .18em;
  color: var(--wine);
  text-align: center;
  margin: 2rem 0 1rem;
  position: relative;
}
.testament-title::before,
.testament-title::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 22%;
  height: 1px;
  background: linear-gradient(to var(--dir, right), var(--gold-faint), transparent);
}
.testament-title::before { left: 0; --dir: right; }
.testament-title::after  { right: 0; --dir: left; }

/* ── Book grid ─────────────────────────────────────────────────────────── */

.book-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: .8rem;
  margin-bottom: 1.2rem;
}
.book-card {
  display: block;
  background: var(--white);
  border: 1px solid var(--gold-faint);
  padding: .8rem 1rem;
  text-decoration: none;
  color: var(--ink);
  transition: all .25s;
  position: relative;
  overflow: hidden;
}
.book-card::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0;
  width: 100%; height: 2px;
  background: var(--gold);
  transform: scaleX(0);
  transform-origin: center;
  transition: transform .3s;
}
.book-card:hover {
  border-color: var(--gold-light);
  box-shadow: 0 4px 14px var(--shadow);
  transform: translateY(-2px);
}
.book-card:hover::after { transform: scaleX(1); }
.book-card .book-name {
  font-size: .85rem;
  font-weight: 700;
  color: var(--wine-dark);
  margin-bottom: .15rem;
}
.book-card .book-meta {
  font-size: .68rem;
  color: var(--ink-faint);
  font-style: italic;
}

/* ── Chapter grid (book page) ──────────────────────────────────────────── */

.book-heading {
  text-align: center;
  margin: 1.2rem 0;
}
.book-heading h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--wine-dark);
  letter-spacing: .1em;
  text-transform: uppercase;
}
.book-heading .chapter-count {
  font-size: .8rem;
  font-style: italic;
  color: var(--ink-faint);
  margin-top: .15rem;
}

.chapter-grid {
  display: flex;
  flex-wrap: wrap;
  gap: .5rem;
  justify-content: center;
  margin: 1.5rem 0;
}
.chapter-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.8rem; height: 2.8rem;
  border: 1px solid var(--gold-faint);
  background: var(--white);
  color: var(--ink);
  text-decoration: none;
  font-size: .8rem;
  transition: all .2s;
}
.chapter-link:hover {
  background: var(--wine);
  color: var(--white);
  border-color: var(--wine);
  transform: scale(1.08);
}

/* ── Chapter reading page ──────────────────────────────────────────────── */

.chapter-heading {
  text-align: center;
  margin: 1rem 0 1.5rem;
}
.chapter-heading h2 {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--wine-dark);
  letter-spacing: .08em;
}
.chapter-heading .ch-label {
  font-size: .9rem;
  color: var(--gold);
  letter-spacing: .15em;
  text-transform: uppercase;
  margin-bottom: .2rem;
}

.verse-text {
  max-width: 36rem;
  margin: 0 auto;
  text-align: justify;
  hyphens: auto;
}
.verse-text p {
  margin-bottom: .15rem;
  text-indent: 1.5em;
}
.verse-text p:first-child { text-indent: 0; }
.verse-num {
  font-size: .6em;
  font-weight: 700;
  color: var(--wine);
  vertical-align: super;
  margin-right: .12em;
  line-height: 0;
}
.drop-cap {
  float: left;
  font-size: 3.6em;
  line-height: .75;
  padding-right: .08em;
  padding-top: .06em;
  color: var(--wine);
  font-weight: 700;
}

/* ── Chapter nav ───────────────────────────────────────────────────────── */

.chapter-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 36rem;
  margin: 2.5rem auto 0;
  padding-top: 1.2rem;
  border-top: 1px solid var(--gold-faint);
  font-size: .78rem;
}
.chapter-nav a {
  color: var(--wine);
  text-decoration: none;
  letter-spacing: .04em;
  transition: color .2s;
}
.chapter-nav a:hover { color: var(--gold); }
.chapter-nav .placeholder { width: 8rem; }

/* ── Footer ────────────────────────────────────────────────────────────── */

footer {
  text-align: center;
  padding: 2rem 1rem 2.5rem;
  font-size: .68rem;
  color: var(--ink-faint);
  font-style: italic;
  letter-spacing: .03em;
}

/* ── Responsive ────────────────────────────────────────────────────────── */

@media (max-width: 860px) {
  :root { --sidebar-w: 260px; }
}

@media (max-width: 700px) {
  html { font-size: 16px; }
  :root { --sidebar-w: 0px; }

  .sidebar {
    transform: translateX(-100%);
    transition: transform .3s ease;
    width: 280px;
  }
  .sidebar.open {
    transform: translateX(0);
  }
  .sidebar-toggle {
    display: flex;
  }
  .sidebar-close {
    display: block;
  }
  .content { margin-left: 0; }
  .content::before { left: 4px; top: 4px; right: 4px; bottom: 4px; }
  .content-header h1 { font-size: 1.5rem; }
  .home-hero h1 { font-size: 1.8rem; }
  main { padding: 0 1rem 3rem; }
  .book-grid { grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); }
  .verse-text { text-align: left; }
  .version-grid { grid-template-columns: 1fr; padding: 0 1rem 3rem; }
}
"""

# ---------------------------------------------------------------------------
# Masonic SVG symbols (inline, no external files)
# ---------------------------------------------------------------------------

SVG_SQUARE_COMPASSES = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" class="masonic-symbol">
  <g fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
    <!-- Compasses -->
    <line x1="100" y1="30" x2="55" y2="170"/>
    <line x1="100" y1="30" x2="145" y2="170"/>
    <!-- Square -->
    <polyline points="60,90 100,140 140,90"/>
    <!-- G -->
    <circle cx="100" cy="105" r="16" stroke-width="2"/>
    <text x="100" y="112" text-anchor="middle" font-family="Libre Baskerville, serif" font-size="22" font-weight="700" fill="currentColor" stroke="none">G</text>
  </g>
</svg>'''

SVG_ALL_SEEING_EYE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 140" class="masonic-symbol">
  <g fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <!-- Triangle / radiance -->
    <polygon points="100,10 30,120 170,120" stroke-width="2"/>
    <!-- Rays -->
    <line x1="100" y1="5" x2="100" y2="-8" stroke-width="1.5"/>
    <line x1="75" y1="12" x2="65" y2="0" stroke-width="1.5"/>
    <line x1="125" y1="12" x2="135" y2="0" stroke-width="1.5"/>
    <line x1="55" y1="30" x2="40" y2="20" stroke-width="1.5"/>
    <line x1="145" y1="30" x2="160" y2="20" stroke-width="1.5"/>
    <!-- Eye -->
    <ellipse cx="100" cy="72" rx="30" ry="18"/>
    <circle cx="100" cy="72" r="9" fill="currentColor"/>
    <circle cx="100" cy="72" r="4" fill="none" stroke="#0a1628" stroke-width="1.5"/>
  </g>
</svg>'''

SVG_PILLARS = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 160" class="masonic-symbol masonic-pillars">
  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
    <!-- Left pillar (Jachin) -->
    <rect x="40" y="30" width="30" height="100" rx="2"/>
    <rect x="35" y="22" width="40" height="10" rx="2"/>
    <rect x="35" y="128" width="40" height="10" rx="2"/>
    <circle cx="55" cy="16" r="8"/>
    <text x="55" y="152" text-anchor="middle" font-family="Libre Baskerville, serif" font-size="11" fill="currentColor" stroke="none" font-style="italic">Jachin</text>
    <!-- Right pillar (Boaz) -->
    <rect x="230" y="30" width="30" height="100" rx="2"/>
    <rect x="225" y="22" width="40" height="10" rx="2"/>
    <rect x="225" y="128" width="40" height="10" rx="2"/>
    <circle cx="245" cy="16" r="8"/>
    <text x="245" y="152" text-anchor="middle" font-family="Libre Baskerville, serif" font-size="11" fill="currentColor" stroke="none" font-style="italic">Boaz</text>
    <!-- Arch -->
    <path d="M 75 26 Q 150 -20 225 26" stroke-width="2.5"/>
    <!-- All-seeing eye in arch center -->
    <polygon points="150,10 140,30 160,30" stroke-width="1.5"/>
    <circle cx="150" cy="22" r="4" fill="currentColor"/>
  </g>
</svg>'''

SVG_DIVIDER = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 30" class="masonic-divider">
  <g fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
    <line x1="10" y1="15" x2="130" y2="15" opacity=".4"/>
    <line x1="270" y1="15" x2="390" y2="15" opacity=".4"/>
    <!-- Small square & compasses -->
    <line x1="200" y1="4" x2="185" y2="26"/>
    <line x1="200" y1="4" x2="215" y2="26"/>
    <polyline points="188,16 200,24 212,16"/>
    <!-- Stars -->
    <text x="150" y="20" font-size="10" fill="currentColor" stroke="none">&#x2736;</text>
    <text x="244" y="20" font-size="10" fill="currentColor" stroke="none">&#x2736;</text>
  </g>
</svg>'''

# ---------------------------------------------------------------------------
# Masonic CSS theme (overrides for .masonic-theme)
# ---------------------------------------------------------------------------

MASONIC_CSS = r"""
/* ── Masonic Theme Overrides ───────────────────────────────────────────── */

.masonic-theme {
  --parchment:  #0a1628;
  --cream:      #0f1d33;
  --sidebar-bg: #060e1c;
  --sidebar-fg: #b8c4d8;
  --sidebar-hi: #c9a84c;
  --gold:       #c9a84c;
  --gold-light: #dbbe5e;
  --gold-faint: rgba(201, 168, 76, .35);
  --ink:        #d4dae6;
  --ink-light:  #a0aec0;
  --ink-faint:  #6b7a90;
  --wine:       #c9a84c;
  --wine-dark:  #dbbe5e;
  --white:      #111e34;
  --shadow:     rgba(0, 0, 0, .3);

  background: #0a1628;
  color: #d4dae6;
}

/* Decorative border */
.masonic-theme .content::before {
  border-color: rgba(201, 168, 76, .3);
}

/* Sidebar */
.masonic-theme .sidebar {
  background: linear-gradient(180deg, #060e1c 0%, #0a1628 100%);
  border-right-color: var(--gold);
}
.masonic-theme .sidebar::-webkit-scrollbar-thumb { background: #2a3a56; }
.masonic-theme .sidebar::-webkit-scrollbar-track { background: #060e1c; }

.masonic-theme .sb-book-link:hover {
  background: rgba(201, 168, 76, .08);
}
.masonic-theme .sb-book-link.active {
  background: rgba(201, 168, 76, .12);
}
.masonic-theme .sb-ch-link:hover {
  background: var(--gold);
  color: #0a1628;
  border-color: var(--gold);
}
.masonic-theme .sb-chapters {
  background: rgba(0, 0, 0, .3);
}

/* Version select */
.masonic-theme .version-select {
  background: rgba(201, 168, 76, .06);
  border-color: rgba(201, 168, 76, .25);
}
.masonic-theme .version-select option {
  background: #060e1c;
}

/* Cards */
.masonic-theme .book-card,
.masonic-theme .version-card {
  background: #111e34;
  border-color: rgba(201, 168, 76, .2);
}
.masonic-theme .book-card:hover,
.masonic-theme .version-card:hover {
  border-color: var(--gold);
  box-shadow: 0 4px 20px rgba(201, 168, 76, .15);
}
.masonic-theme .book-card::after,
.masonic-theme .version-card::after {
  background: var(--gold);
}
.masonic-theme .book-card .book-name {
  color: var(--gold);
}

/* Chapter links */
.masonic-theme .chapter-link {
  background: #111e34;
  border-color: rgba(201, 168, 76, .2);
  color: #d4dae6;
}
.masonic-theme .chapter-link:hover {
  background: var(--gold);
  color: #0a1628;
  border-color: var(--gold);
}

/* Reading text */
.masonic-theme .verse-num {
  color: var(--gold);
}
.masonic-theme .drop-cap {
  color: var(--gold);
}

/* Chapter nav */
.masonic-theme .chapter-nav {
  border-top-color: rgba(201, 168, 76, .2);
}
.masonic-theme .chapter-nav a {
  color: var(--gold);
}
.masonic-theme .chapter-nav a:hover {
  color: #dbbe5e;
}

/* Footer */
.masonic-theme footer {
  color: #6b7a90;
}

/* Testament titles */
.masonic-theme .testament-title {
  color: var(--gold);
}
.masonic-theme .testament-title::before,
.masonic-theme .testament-title::after {
  background: linear-gradient(to var(--dir, right), rgba(201, 168, 76, .3), transparent);
}

/* ── Masonic symbols ───────────────────────────────────────────────────── */

.masonic-symbol {
  display: block;
  margin: 0 auto;
  color: var(--gold, #c9a84c);
}
.masonic-hero-symbol {
  width: 120px;
  height: 120px;
  margin: 1.5rem auto;
}
.masonic-header-symbol {
  width: 50px;
  height: 50px;
  margin: .5rem auto;
}
.masonic-chapter-symbol {
  width: 60px;
  height: 60px;
  margin: .8rem auto .3rem;
}
.masonic-divider {
  display: block;
  width: 260px;
  height: 24px;
  margin: .8rem auto;
  color: var(--gold, #c9a84c);
}
.masonic-pillars {
  width: 220px;
  height: 120px;
}
.masonic-footer-symbol {
  width: 40px;
  height: 40px;
  margin: .5rem auto;
  opacity: .4;
}

/* Masonic sidebar header emblem */
.masonic-theme .sidebar-header {
  padding-bottom: .6rem;
}
.masonic-sidebar-emblem {
  width: 42px;
  height: 42px;
  margin: .4rem auto 0;
  opacity: .7;
}

/* Masonic mobile toggle */
.masonic-theme .sidebar-toggle {
  background: #060e1c;
  color: var(--gold);
  border-color: var(--gold);
}

/* Responsive fixes for masonic theme */
@media (max-width: 700px) {
  .masonic-theme .content::before {
    border-color: rgba(201, 168, 76, .2);
  }
}

/* ── Masonic home card (on landing page) ───────────────────────────────── */

.masonic-home-card {
  background: #0f1d33;
  border-color: rgba(201, 168, 76, .4);
  color: #d4dae6;
}
.masonic-home-card .vc-abbr {
  color: #c9a84c;
}
.masonic-home-card .vc-name {
  color: #a0aec0;
}
.masonic-home-card .vc-year {
  color: #6b7a90;
}
.masonic-home-card:hover {
  border-color: #c9a84c;
  box-shadow: 0 6px 24px rgba(201, 168, 76, .2);
}
.masonic-home-card::after {
  background: #c9a84c;
}
"""

# ---------------------------------------------------------------------------
# Sidebar JS (for mobile toggle + version switcher)
# ---------------------------------------------------------------------------

SIDEBAR_JS = r"""
document.addEventListener('DOMContentLoaded', function() {
  var toggle = document.querySelector('.sidebar-toggle');
  var sidebar = document.querySelector('.sidebar');
  var close = document.querySelector('.sidebar-close');
  if (toggle && sidebar) {
    toggle.addEventListener('click', function() { sidebar.classList.toggle('open'); });
  }
  if (close && sidebar) {
    close.addEventListener('click', function() { sidebar.classList.remove('open'); });
  }
  var sel = document.querySelector('.version-select');
  if (sel) {
    sel.addEventListener('change', function() {
      var val = sel.value;
      if (val) window.location.href = val;
    });
  }
});
"""

# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def get_theme(ver):
    """Return the theme name for a version config, or None."""
    return ver.get("theme") if isinstance(ver, dict) else None

def is_masonic(ver):
    return get_theme(ver) == "masonic"

def sidebar_html(ver_cfg, versions, books, active_book=None, active_chapter=None, depth=0):
    """Build the sidebar HTML with book list + chapter sub-nav."""
    ver_id = ver_cfg["id"] if isinstance(ver_cfg, dict) else ver_cfg
    prefix = "../" * depth
    masonic = is_masonic(ver_cfg)

    # Version select – build the <option> list with URLs pointing to the equivalent page
    # depth=0 means we are at {ver}/index.html, so sibling versions are ../{other}/index.html
    # depth=1 means we are at {ver}/{book}/index.html or {ver}/{book}/{ch}.html
    ver_options = ""
    for v in versions:
        selected = ' selected' if v["id"] == ver_id else ''
        if active_book and active_chapter:
            href = f"../../{v['id']}/{slug(active_book)}/{active_chapter}.html"
        elif active_book:
            href = f"../../{v['id']}/{slug(active_book)}/index.html"
        else:
            # depth 0: at {ver}/index.html -> ../{other}/index.html
            href = f"../{v['id']}/index.html"
        ver_options += f'      <option value="{href}"{selected}>{v["abbr"]} &mdash; {v["name"]}</option>\n'

    # Book list
    book_list_html = ""
    book_list_html += '<div class="sb-testament">Old Testament</div>\n<ul class="sb-books">\n'
    for i, bname in enumerate(CANONICAL_ORDER):
        if i == 39:
            book_list_html += '</ul>\n<div class="sb-testament">New Testament</div>\n<ul class="sb-books">\n'

        if bname not in books:
            continue
        n_ch = len(books[bname]["chapters"])
        active_cls = ' active' if bname == active_book else ''

        if depth == 0:
            book_href = f"{slug(bname)}/index.html"
        elif active_chapter:
            book_href = f"../{slug(bname)}/index.html"
        else:
            book_href = f"../{slug(bname)}/index.html"

        book_list_html += f'<li class="sb-book-item">\n'
        book_list_html += f'  <a class="sb-book-link{active_cls}" href="{book_href}">'
        book_list_html += f'<span class="abbr">{esc(BOOK_ABBR.get(bname, bname))}</span>'
        book_list_html += f'<span class="count">{n_ch}</span></a>\n'

        if bname == active_book:
            book_list_html += '  <div class="sb-chapters">\n'
            for ch in books[bname]["chapters"]:
                ch_num = ch["chapter"]
                ch_active = ' active' if str(ch_num) == str(active_chapter) else ''
                ch_href = f"{ch_num}.html"
                book_list_html += f'    <a class="sb-ch-link{ch_active}" href="{ch_href}">{ch_num}</a>\n'
            book_list_html += '  </div>\n'

        book_list_html += '</li>\n'
    book_list_html += '</ul>\n'

    # Home link: version index is at {ver}/index.html, so home = ../index.html
    # Book page is at {ver}/{book}/index.html, so home = ../../index.html
    # Chapter page is at {ver}/{book}/{ch}.html, so home = ../../index.html
    if depth == 0:
        home_href = "../index.html"
    else:
        home_href = "../../index.html"

    # Masonic sidebar emblem
    emblem = ""
    if masonic:
        emblem = f'<div class="masonic-sidebar-emblem">{SVG_ALL_SEEING_EYE}</div>'

    sidebar_title = "Masonic Bible" if masonic else "The Holy Bible"
    sidebar_orn = '&#x25B3; &#x2726; &#x25B3;' if masonic else '&mdash; &#x2726; &#x271D; &#x2726; &mdash;'

    return f"""<button class="sidebar-toggle" aria-label="Open navigation">&#9776;</button>
<aside class="sidebar">
  <button class="sidebar-close" aria-label="Close navigation">&times;</button>
  <div class="sidebar-header">
    <a href="{home_href}">
      <div class="sidebar-title">{sidebar_title}</div>
      <div class="sidebar-ornament">{sidebar_orn}</div>
      {emblem}
    </a>
  </div>
  <div class="version-select-wrap">
    <label for="version-sel">Translation</label>
    <select id="version-sel" class="version-select">
{ver_options}    </select>
  </div>
  {book_list_html}
</aside>"""


def page_shell(title, body_content, sidebar, depth=0, theme=None):
    prefix = "../" * depth
    body_cls = ' class="masonic-theme"' if theme == "masonic" else ''
    extra_css = f'\n  <link rel="stylesheet" href="{prefix}masonic.css">' if theme == "masonic" else ''
    masonic_footer = ""
    if theme == "masonic":
        masonic_footer = f"""<footer>
  <div class="masonic-footer-symbol">{SVG_SQUARE_COMPASSES}</div>
  The Holy Bible &middot; Masonic Edition &middot; Public Domain<br>
  &ldquo;So mote it be.&rdquo;
</footer>"""
    else:
        masonic_footer = """<footer>
  The Holy Bible &middot; Public Domain<br>
  &ldquo;Thy word is a lamp unto my feet, and a light unto my path.&rdquo; &mdash; Psalm 119:105
</footer>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="stylesheet" href="{prefix}style.css">{extra_css}
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x271D;</text></svg>">
</head>
<body{body_cls}>
<div class="page-wrap">
{sidebar}
<div class="content">
{body_content}
{masonic_footer}
</div>
</div>
<script>{SIDEBAR_JS}</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Page generators
# ---------------------------------------------------------------------------

def generate_home():
    """Landing page: pick a translation."""
    cards = ""
    for v in VERSIONS:
        if is_masonic(v):
            cards += f"""
    <a class="version-card masonic-home-card" href="{v['id']}/index.html">
      <div class="vc-abbr">{esc(v['abbr'])}</div>
      <div class="vc-name">{esc(v['name'])}</div>
      <div class="vc-year">{esc(v['year'])}</div>
    </a>"""
        else:
            cards += f"""
    <a class="version-card" href="{v['id']}/index.html">
      <div class="vc-abbr">{esc(v['abbr'])}</div>
      <div class="vc-name">{esc(v['name'])}</div>
      <div class="vc-year">{esc(v['year'])}</div>
    </a>"""

    body = f"""
  <div class="home-hero">
    <h1>The Holy Bible</h1>
    <p class="subtitle">Select a Translation</p>
  </div>
  <div class="home-ornament">&mdash; &#x2726; &#x271D; &#x2726; &mdash;</div>
  <div class="version-grid">{cards}
  </div>
  <footer>
    The Holy Bible &middot; Public Domain<br>
    &ldquo;Thy word is a lamp unto my feet, and a light unto my path.&rdquo; &mdash; Psalm 119:105
  </footer>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>The Holy Bible</title>
  <link rel="stylesheet" href="style.css">
  <link rel="stylesheet" href="masonic.css">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x271D;</text></svg>">
</head>
<body>
{body}
</body>
</html>"""


def generate_version_index(ver, books):
    """Version home page: OT/NT book grid with sidebar."""
    masonic = is_masonic(ver)

    ot_cards = ""
    for name in OT_BOOKS:
        if name not in books:
            continue
        n_ch = len(books[name]["chapters"])
        w = "chapter" if n_ch == 1 else "chapters"
        ot_cards += f"""
      <a class="book-card" href="{slug(name)}/index.html">
        <div class="book-name">{esc(name)}</div>
        <div class="book-meta">{n_ch} {w}</div>
      </a>"""

    nt_cards = ""
    for name in NT_BOOKS:
        if name not in books:
            continue
        n_ch = len(books[name]["chapters"])
        w = "chapter" if n_ch == 1 else "chapters"
        nt_cards += f"""
      <a class="book-card" href="{slug(name)}/index.html">
        <div class="book-name">{esc(name)}</div>
        <div class="book-meta">{n_ch} {w}</div>
      </a>"""

    sb = sidebar_html(ver, VERSIONS, books, depth=0)

    if masonic:
        hero_symbol = f'<div class="masonic-hero-symbol">{SVG_SQUARE_COMPASSES}</div>'
        divider = f'<div>{SVG_DIVIDER}</div>'
        pillars = f'<div class="masonic-pillars" style="margin:1rem auto;text-align:center">{SVG_PILLARS}</div>'
        title_text = "The Masonic Bible"
    else:
        hero_symbol = ""
        divider = '<div class="ornament">&mdash; &#x2726; &#x271D; &#x2726; &mdash;</div>'
        pillars = ""
        title_text = "The Holy Bible"

    body = f"""
  <div class="content-header">
    {hero_symbol}
    <h1>{title_text}</h1>
    <p class="subtitle">{esc(ver['name'])}</p>
  </div>
  {divider}
  {pillars}
  <main>
    <div class="testament-title">The Old Testament</div>
    <div class="book-grid">{ot_cards}
    </div>
    <div class="testament-title">The New Testament</div>
    <div class="book-grid">{nt_cards}
    </div>
  </main>"""

    return page_shell(f"The Holy Bible - {ver['abbr']}", body, sb, depth=1,
                      theme=get_theme(ver))


def generate_book_page(ver, books, book_name):
    masonic = is_masonic(ver)
    chapters = books[book_name]["chapters"]
    n_ch = len(chapters)
    w = "chapter" if n_ch == 1 else "chapters"

    links = ""
    for ch in chapters:
        links += f'      <a class="chapter-link" href="{ch["chapter"]}.html">{ch["chapter"]}</a>\n'

    sb = sidebar_html(ver, VERSIONS, books, active_book=book_name, depth=1)

    header_sym = f'<div class="masonic-header-symbol">{SVG_ALL_SEEING_EYE}</div>' if masonic else ''
    divider = f'<div>{SVG_DIVIDER}</div>' if masonic else '<div class="ornament">&mdash; &#x2726; &mdash;</div>'

    body = f"""
  <div class="content-header">
    {header_sym}
    <h1>{esc(book_name)}</h1>
    <p class="subtitle">{esc(ver['name'])}</p>
  </div>
  {divider}
  <main>
    <div class="book-heading">
      <h2>{esc(book_name)}</h2>
      <div class="chapter-count">{n_ch} {w}</div>
    </div>
    <div class="chapter-grid">
{links}    </div>
  </main>"""

    return page_shell(f"{book_name} - {ver['abbr']}", body, sb, depth=2,
                      theme=get_theme(ver))


def generate_chapter_page(ver, books, book_name, chapter_index):
    masonic = is_masonic(ver)
    book = books[book_name]
    chapters = book["chapters"]
    ch = chapters[chapter_index]
    ch_num = ch["chapter"]

    verses_html = ""
    for i, v in enumerate(ch["verses"]):
        text = esc(v["text"])
        vn = v["verse"]
        if i == 0 and text:
            first_letter = text[0]
            rest = text[1:]
            verses_html += f'<p><span class="verse-num">{vn}</span><span class="drop-cap">{first_letter}</span>{rest}</p>\n'
        else:
            verses_html += f'<p><span class="verse-num">{vn}</span>{text}</p>\n'

    # Prev/next navigation (within version)
    book_index = CANONICAL_ORDER.index(book_name)

    prev_link = ""
    if chapter_index > 0:
        prev_ch = chapters[chapter_index - 1]["chapter"]
        prev_link = f'<a href="{prev_ch}.html">&larr; Chapter {prev_ch}</a>'
    elif book_index > 0:
        prev_book = CANONICAL_ORDER[book_index - 1]
        if prev_book in books:
            prev_ch = books[prev_book]["chapters"][-1]["chapter"]
            prev_link = f'<a href="../{slug(prev_book)}/{prev_ch}.html">&larr; {esc(prev_book)} {prev_ch}</a>'

    next_link = ""
    if chapter_index < len(chapters) - 1:
        next_ch = chapters[chapter_index + 1]["chapter"]
        next_link = f'<a href="{next_ch}.html">Chapter {next_ch} &rarr;</a>'
    elif book_index < len(CANONICAL_ORDER) - 1:
        next_book = CANONICAL_ORDER[book_index + 1]
        if next_book in books:
            next_link = f'<a href="../{slug(next_book)}/1.html">{esc(next_book)} 1 &rarr;</a>'

    sb = sidebar_html(ver, VERSIONS, books,
                      active_book=book_name, active_chapter=ch_num, depth=1)

    chapter_sym = f'<div class="masonic-chapter-symbol">{SVG_ALL_SEEING_EYE}</div>' if masonic else ''
    divider = f'<div>{SVG_DIVIDER}</div>' if masonic else '<div class="ornament">&mdash; &#x2726; &mdash;</div>'

    body = f"""
  <div class="content-header">
    <h1>{esc(book_name)}</h1>
    <p class="subtitle">{esc(ver['name'])}</p>
  </div>
  {divider}
  <main>
    <div class="chapter-heading">
      {chapter_sym}
      <div class="ch-label">Chapter {ch_num}</div>
      <h2>{esc(book_name)}</h2>
    </div>
    <div class="verse-text">
      {verses_html}
    </div>
    <nav class="chapter-nav">
      <div>{prev_link if prev_link else '<span class="placeholder"></span>'}</div>
      <div><a href="index.html">All Chapters</a></div>
      <div>{next_link if next_link else '<span class="placeholder"></span>'}</div>
    </nav>
  </main>"""

    return page_shell(f"{book_name} {ch_num} - {ver['abbr']}", body, sb, depth=2,
                      theme=get_theme(ver))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import shutil
    # Clean output directory
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    # Write CSS
    with open(os.path.join(OUTPUT_DIR, "style.css"), "w") as f:
        f.write(CSS)
    print("  style.css")

    # Write Masonic CSS
    with open(os.path.join(OUTPUT_DIR, "masonic.css"), "w") as f:
        f.write(MASONIC_CSS)
    print("  masonic.css")

    # Generate landing page
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
        f.write(generate_home())
    print("  index.html (home)")

    # Load and generate each version
    for ver in VERSIONS:
        print(f"\n  [{ver['abbr']}] Loading {ver['file']}...")
        books = load_version(ver)
        found = [n for n in CANONICAL_ORDER if n in books]
        print(f"  [{ver['abbr']}] {len(found)} books loaded")

        ver_dir = os.path.join(OUTPUT_DIR, ver["id"])
        os.makedirs(ver_dir, exist_ok=True)

        # Version index
        with open(os.path.join(ver_dir, "index.html"), "w") as f:
            f.write(generate_version_index(ver, books))

        total_ch = 0
        for bname in CANONICAL_ORDER:
            if bname not in books:
                continue
            book_dir = os.path.join(ver_dir, slug(bname))
            os.makedirs(book_dir, exist_ok=True)

            # Book index
            with open(os.path.join(book_dir, "index.html"), "w") as f:
                f.write(generate_book_page(ver, books, bname))

            # Chapters
            for i, ch in enumerate(books[bname]["chapters"]):
                with open(os.path.join(book_dir, f'{ch["chapter"]}.html'), "w") as f:
                    f.write(generate_chapter_page(ver, books, bname, i))
                total_ch += 1

        print(f"  [{ver['abbr']}] Generated {len(found)} books, {total_ch} chapters")

    print(f"\nDone! Output: {os.path.abspath(OUTPUT_DIR)}/")


if __name__ == "__main__":
    main()
