#!/usr/bin/env python3
"""
Static site generator for The Holy Bible (KJV).
Generates a beautiful, static HTML website with all 66 books and 1,189 chapters.
"""

import json
import os
import re

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = "site"
DATA_FILE = "data/kjv.json"

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slug(name):
    """Turn a book name into a URL-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def book_path(name):
    return f"{slug(name)}/index.html"


def chapter_path(name, ch):
    return f"{slug(name)}/{ch}.html"


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');

/* ── Reset & Base ──────────────────────────────────────────────────────── */

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --parchment:  #faf6ed;
  --cream:      #f5f0e3;
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

html {
  font-size: 18px;
  scroll-behavior: smooth;
}

body {
  font-family: 'Libre Baskerville', 'Georgia', 'Times New Roman', serif;
  background: var(--parchment);
  color: var(--ink);
  line-height: 1.8;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}

/* ── Decorative page border ────────────────────────────────────────────── */

body::before {
  content: '';
  position: fixed;
  inset: 8px;
  border: 2px solid var(--gold-faint);
  pointer-events: none;
  z-index: 9999;
}

/* ── Top ornament bar ──────────────────────────────────────────────────── */

.top-ornament {
  text-align: center;
  padding: 1.4rem 1rem 0.6rem;
  color: var(--gold);
  font-size: 1.3rem;
  letter-spacing: .6em;
  user-select: none;
}

/* ── Header ────────────────────────────────────────────────────────────── */

header {
  text-align: center;
  padding: 1.5rem 1rem 2rem;
}

header h1 {
  font-size: 2.6rem;
  font-weight: 700;
  color: var(--wine-dark);
  letter-spacing: .12em;
  text-transform: uppercase;
  margin-bottom: .2rem;
}

header .subtitle {
  font-size: 0.95rem;
  font-style: italic;
  color: var(--ink-faint);
  letter-spacing: .08em;
}

.ornament {
  display: block;
  text-align: center;
  color: var(--gold);
  font-size: 1.1rem;
  letter-spacing: .5em;
  margin: .8rem 0;
  user-select: none;
}

/* ── Navigation breadcrumb ─────────────────────────────────────────────── */

.breadcrumb {
  text-align: center;
  padding: .5rem 1rem;
  font-size: .78rem;
  color: var(--ink-faint);
  letter-spacing: .04em;
}
.breadcrumb a {
  color: var(--wine);
  text-decoration: none;
  transition: color .2s;
}
.breadcrumb a:hover {
  color: var(--gold);
}
.breadcrumb .sep {
  margin: 0 .4em;
  color: var(--gold-faint);
}

/* ── Main content wrapper ──────────────────────────────────────────────── */

main {
  max-width: 56rem;
  margin: 0 auto;
  padding: 0 2rem 4rem;
}

/* ── Testament sections (index page) ───────────────────────────────────── */

.testament-title {
  font-size: 1.15rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .18em;
  color: var(--wine);
  text-align: center;
  margin: 2.5rem 0 1.2rem;
  position: relative;
}
.testament-title::before,
.testament-title::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 25%;
  height: 1px;
  background: linear-gradient(to var(--dir, right), var(--gold-faint), transparent);
}
.testament-title::before { left: 0; --dir: right; }
.testament-title::after  { right: 0; --dir: left; }

/* ── Book grid ─────────────────────────────────────────────────────────── */

.book-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.book-card {
  display: block;
  background: var(--white);
  border: 1px solid var(--gold-faint);
  padding: 1rem 1.2rem;
  text-decoration: none;
  color: var(--ink);
  transition: all .25s ease;
  position: relative;
  overflow: hidden;
}
.book-card::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: var(--gold);
  transform: scaleX(0);
  transform-origin: center;
  transition: transform .3s ease;
}
.book-card:hover {
  border-color: var(--gold-light);
  box-shadow: 0 4px 16px var(--shadow);
  transform: translateY(-2px);
}
.book-card:hover::after {
  transform: scaleX(1);
}
.book-card .book-name {
  font-size: .92rem;
  font-weight: 700;
  color: var(--wine-dark);
  margin-bottom: .2rem;
}
.book-card .book-meta {
  font-size: .72rem;
  color: var(--ink-faint);
  font-style: italic;
}

/* ── Chapter grid (book page) ──────────────────────────────────────────── */

.book-heading {
  text-align: center;
  margin: 1.5rem 0;
}
.book-heading h2 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--wine-dark);
  letter-spacing: .1em;
  text-transform: uppercase;
}
.book-heading .chapter-count {
  font-size: .85rem;
  font-style: italic;
  color: var(--ink-faint);
  margin-top: .2rem;
}

.chapter-grid {
  display: flex;
  flex-wrap: wrap;
  gap: .6rem;
  justify-content: center;
  margin: 2rem 0;
}

.chapter-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border: 1px solid var(--gold-faint);
  background: var(--white);
  color: var(--ink);
  text-decoration: none;
  font-size: .85rem;
  transition: all .2s ease;
}
.chapter-link:hover {
  background: var(--wine);
  color: var(--white);
  border-color: var(--wine);
  transform: scale(1.1);
}

/* ── Chapter reading page ──────────────────────────────────────────────── */

.chapter-heading {
  text-align: center;
  margin: 1rem 0 2rem;
}
.chapter-heading h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--wine-dark);
  letter-spacing: .08em;
}
.chapter-heading .ch-label {
  font-size: 1rem;
  color: var(--gold);
  letter-spacing: .15em;
  text-transform: uppercase;
  margin-bottom: .3rem;
}

.verse-text {
  max-width: 38rem;
  margin: 0 auto;
  text-align: justify;
  hyphens: auto;
}
.verse-text p {
  margin-bottom: .2rem;
  text-indent: 1.5em;
}
.verse-text p:first-child {
  text-indent: 0;
}
.verse-num {
  font-size: .65em;
  font-weight: 700;
  color: var(--wine);
  vertical-align: super;
  margin-right: .15em;
  line-height: 0;
}

/* ── Chapter navigation ────────────────────────────────────────────────── */

.chapter-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 38rem;
  margin: 3rem auto 0;
  padding-top: 1.5rem;
  border-top: 1px solid var(--gold-faint);
  font-size: .82rem;
}
.chapter-nav a {
  color: var(--wine);
  text-decoration: none;
  letter-spacing: .04em;
  transition: color .2s;
}
.chapter-nav a:hover {
  color: var(--gold);
}
.chapter-nav .placeholder {
  width: 8rem;
}

/* ── Footer ────────────────────────────────────────────────────────────── */

footer {
  text-align: center;
  padding: 2rem 1rem 3rem;
  font-size: .72rem;
  color: var(--ink-faint);
  font-style: italic;
  letter-spacing: .03em;
}

/* ── Drop cap for chapter start ────────────────────────────────────────── */

.drop-cap {
  float: left;
  font-size: 3.8em;
  line-height: .75;
  padding-right: .08em;
  padding-top: .06em;
  color: var(--wine);
  font-weight: 700;
}

/* ── Responsive ────────────────────────────────────────────────────────── */

@media (max-width: 640px) {
  html { font-size: 16px; }
  header h1 { font-size: 1.6rem; }
  main { padding: 0 1rem 3rem; }
  .book-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
  body::before { inset: 4px; }
  .verse-text { text-align: left; }
}
"""

# ---------------------------------------------------------------------------
# HTML Helpers
# ---------------------------------------------------------------------------

def page_shell(title, body, depth=0):
    """Wrap body content in the full HTML shell."""
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="{prefix}style.css">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x271D;</text></svg>">
</head>
<body>
<div class="top-ornament">&mdash; &#x2726; &mdash;</div>
{body}
<footer>
  The Holy Bible &middot; King James Version &middot; Public Domain<br>
  &ldquo;Thy word is a lamp unto my feet, and a light unto my path.&rdquo; &mdash; Psalm 119:105
</footer>
</body>
</html>"""


def breadcrumb(*parts):
    """Build a breadcrumb bar. Each part is (label, href) or just label for current page."""
    items = []
    for p in parts:
        if isinstance(p, tuple):
            items.append(f'<a href="{p[1]}">{p[0]}</a>')
        else:
            items.append(p)
    return '<nav class="breadcrumb">' + '<span class="sep">&#x2022;</span>'.join(items) + '</nav>'


# ---------------------------------------------------------------------------
# Page generators
# ---------------------------------------------------------------------------

def generate_index(books):
    """Generate the main index page with all 66 books."""
    ot_cards = ""
    for name in OT_BOOKS:
        b = books[name]
        n_ch = len(b["chapters"])
        ch_word = "chapter" if n_ch == 1 else "chapters"
        ot_cards += f"""
    <a class="book-card" href="{slug(name)}/index.html">
      <div class="book-name">{name}</div>
      <div class="book-meta">{n_ch} {ch_word}</div>
    </a>"""

    nt_cards = ""
    for name in NT_BOOKS:
        b = books[name]
        n_ch = len(b["chapters"])
        ch_word = "chapter" if n_ch == 1 else "chapters"
        nt_cards += f"""
    <a class="book-card" href="{slug(name)}/index.html">
      <div class="book-name">{name}</div>
      <div class="book-meta">{n_ch} {ch_word}</div>
    </a>"""

    body = f"""
<header>
  <h1>The Holy Bible</h1>
  <p class="subtitle">King James Version</p>
</header>
<div class="ornament">&mdash; &#x2726; &#x271D; &#x2726; &mdash;</div>
<main>
  <div class="testament-title">The Old Testament</div>
  <div class="book-grid">{ot_cards}
  </div>

  <div class="testament-title">The New Testament</div>
  <div class="book-grid">{nt_cards}
  </div>
</main>"""

    return page_shell("The Holy Bible — King James Version", body)


def generate_book_page(book_data):
    """Generate a book's chapter listing page."""
    name = book_data["book"]
    chapters = book_data["chapters"]
    n_ch = len(chapters)
    ch_word = "chapter" if n_ch == 1 else "chapters"

    links = ""
    for ch in chapters:
        ch_num = ch["chapter"]
        links += f'<a class="chapter-link" href="{ch_num}.html">{ch_num}</a>\n'

    bc = breadcrumb(("The Holy Bible", "../index.html"), name)

    body = f"""
<header>
  <h1>The Holy Bible</h1>
  <p class="subtitle">King James Version</p>
</header>
{bc}
<div class="ornament">&mdash; &#x2726; &mdash;</div>
<main>
  <div class="book-heading">
    <h2>{name}</h2>
    <div class="chapter-count">{n_ch} {ch_word}</div>
  </div>
  <div class="chapter-grid">
    {links}
  </div>
</main>"""

    return page_shell(f"{name} — KJV Bible", body, depth=1)


def generate_chapter_page(book_data, chapter_index, books):
    """Generate a chapter reading page with verses."""
    name = book_data["book"]
    chapters = book_data["chapters"]
    ch = chapters[chapter_index]
    ch_num = ch["chapter"]

    bc = breadcrumb(
        ("The Holy Bible", "../index.html"),
        (name, "index.html"),
        f"Chapter {ch_num}"
    )

    # Build verse paragraphs
    verses_html = ""
    for i, v in enumerate(ch["verses"]):
        text = v["text"]
        vn = v["verse"]
        if i == 0:
            # Drop cap on first verse
            first_letter = text[0]
            rest = text[1:]
            verses_html += f'<p><span class="verse-num">{vn}</span><span class="drop-cap">{first_letter}</span>{rest}</p>\n'
        else:
            verses_html += f'<p><span class="verse-num">{vn}</span>{text}</p>\n'

    # Navigation: prev / next chapter, including cross-book navigation
    book_index = CANONICAL_ORDER.index(name)

    prev_link = ""
    if chapter_index > 0:
        prev_ch = chapters[chapter_index - 1]["chapter"]
        prev_link = f'<a href="{prev_ch}.html">&larr; Chapter {prev_ch}</a>'
    elif book_index > 0:
        prev_book_name = CANONICAL_ORDER[book_index - 1]
        prev_book = books[prev_book_name]
        prev_ch_num = prev_book["chapters"][-1]["chapter"]
        prev_link = f'<a href="../{slug(prev_book_name)}/{prev_ch_num}.html">&larr; {prev_book_name} {prev_ch_num}</a>'

    next_link = ""
    if chapter_index < len(chapters) - 1:
        next_ch = chapters[chapter_index + 1]["chapter"]
        next_link = f'<a href="{next_ch}.html">Chapter {next_ch} &rarr;</a>'
    elif book_index < len(CANONICAL_ORDER) - 1:
        next_book_name = CANONICAL_ORDER[book_index + 1]
        next_link = f'<a href="../{slug(next_book_name)}/1.html">{next_book_name} 1 &rarr;</a>'

    body = f"""
<header>
  <h1>The Holy Bible</h1>
  <p class="subtitle">King James Version</p>
</header>
{bc}
<div class="ornament">&mdash; &#x2726; &mdash;</div>
<main>
  <div class="chapter-heading">
    <div class="ch-label">Chapter {ch_num}</div>
    <h2>{name}</h2>
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

    return page_shell(f"{name} {ch_num} — KJV Bible", body, depth=1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    with open(DATA_FILE) as f:
        raw_books = json.load(f)

    books = {b["book"]: b for b in raw_books}

    # Ensure output dirs exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Write CSS
    css_path = os.path.join(OUTPUT_DIR, "style.css")
    with open(css_path, "w") as f:
        f.write(CSS)
    print(f"  style.css")

    # Generate index page
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w") as f:
        f.write(generate_index(books))
    print(f"  index.html")

    # Generate each book + chapter pages
    total_chapters = 0
    for name in CANONICAL_ORDER:
        if name not in books:
            print(f"  WARNING: {name} not found in data!")
            continue

        book = books[name]
        book_dir = os.path.join(OUTPUT_DIR, slug(name))
        os.makedirs(book_dir, exist_ok=True)

        # Book index page
        book_index = os.path.join(book_dir, "index.html")
        with open(book_index, "w") as f:
            f.write(generate_book_page(book))

        # Chapter pages
        for i, ch in enumerate(book["chapters"]):
            ch_file = os.path.join(book_dir, f'{ch["chapter"]}.html')
            with open(ch_file, "w") as f:
                f.write(generate_chapter_page(book, i, books))
            total_chapters += 1

        print(f"  {name} ({len(book['chapters'])} chapters)")

    print(f"\nDone! Generated {len(CANONICAL_ORDER)} books, {total_chapters} chapters.")
    print(f"Output: {os.path.abspath(OUTPUT_DIR)}/")


if __name__ == "__main__":
    main()
