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
# Wikipedia links & descriptions for each book
# ---------------------------------------------------------------------------

BOOK_WIKI = {
    "Genesis": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Genesis",
        "desc": "The book of origins — creation, the fall, the flood, and the patriarchs Abraham, Isaac, Jacob, and Joseph.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Michelangelo,_Creation_of_Adam_06.jpg?width=640",
        "image_alt": "The Creation of Adam by Michelangelo, Sistine Chapel ceiling",
        "image_credit": "Michelangelo, c. 1512",
    },
    "Exodus": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Exodus",
        "desc": "Israel's deliverance from Egypt, the giving of the Law at Sinai, and the construction of the Tabernacle.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Tissot_The_Crossing_of_the_Red_Sea.jpg?width=640",
        "image_alt": "The Crossing of the Red Sea by James Tissot",
        "image_credit": "James Tissot, c. 1900",
    },
    "Leviticus": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Leviticus",
        "desc": "Laws of sacrifice, purity, and holiness given to the priestly tribe of Levi.",
    },
    "Numbers": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Numbers",
        "desc": "The forty years of wandering in the wilderness, from Sinai to the plains of Moab.",
    },
    "Deuteronomy": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Deuteronomy",
        "desc": "Moses' farewell speeches and the renewal of the covenant before entering the Promised Land.",
    },
    "Joshua": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Joshua",
        "desc": "The conquest and division of Canaan under the leadership of Joshua.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Joshua_passing_the_River_Jordan_with_the_Ark_of_the_Covenant_by_Benjamin_West.jpg?width=640",
        "image_alt": "Joshua Passing the River Jordan by Benjamin West",
        "image_credit": "Benjamin West, 1800",
    },
    "Judges": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Judges",
        "desc": "The turbulent era of the judges — Deborah, Gideon, Samson — between the conquest and the monarchy.",
    },
    "Ruth": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Ruth",
        "desc": "A story of loyalty and redemption — Ruth the Moabitess, great-grandmother of King David.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Julius_Schnorr_von_Carolsfeld-_Ruth_im_Feld_des_Boaz.jpg?width=485",
        "image_alt": "Ruth in the Field of Boaz by Julius Schnorr von Carolsfeld",
        "image_credit": "Julius Schnorr von Carolsfeld, 1828",
    },
    "1 Samuel": {
        "url": "https://en.wikipedia.org/wiki/Books_of_Samuel",
        "desc": "From the prophet Samuel through Saul's reign to the rise of David.",
    },
    "2 Samuel": {
        "url": "https://en.wikipedia.org/wiki/Books_of_Samuel",
        "desc": "The reign of King David — triumphs, sins, and the promise of an everlasting dynasty.",
    },
    "1 Kings": {
        "url": "https://en.wikipedia.org/wiki/Books_of_Kings",
        "desc": "Solomon's glory, the building of the Temple, the kingdom divided, and the prophet Elijah.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Visit_of_the_Queen_of_Sheba_to_King_Solomon.jpg?width=640",
        "image_alt": "The Visit of the Queen of Sheba to King Solomon by Edward Poynter",
        "image_credit": "Edward Poynter, 1890",
    },
    "2 Kings": {
        "url": "https://en.wikipedia.org/wiki/Books_of_Kings",
        "desc": "The divided kingdom's decline, the prophet Elisha, and the fall of Israel and Judah.",
    },
    "1 Chronicles": {
        "url": "https://en.wikipedia.org/wiki/Books_of_Chronicles",
        "desc": "Israel's history retold from Adam to David, with emphasis on worship and the Temple.",
    },
    "2 Chronicles": {
        "url": "https://en.wikipedia.org/wiki/Books_of_Chronicles",
        "desc": "From Solomon's Temple to the Babylonian exile and Cyrus' decree of return.",
    },
    "Ezra": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Ezra",
        "desc": "The return from Babylon and the rebuilding of the Temple under Zerubbabel and Ezra.",
    },
    "Nehemiah": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Nehemiah",
        "desc": "Nehemiah rebuilds the walls of Jerusalem and restores the covenant community.",
    },
    "Esther": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Esther",
        "desc": "Queen Esther saves the Jewish people from destruction in the Persian Empire.",
    },
    "Job": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Job",
        "desc": "The great poem of innocent suffering — Job's trials, his friends' debate, and God's answer from the whirlwind.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/L%C3%A9on_Bonnat_-_Job.jpg?width=458",
        "image_alt": "Job by Léon Bonnat",
        "image_credit": "Léon Bonnat, 1880",
    },
    "Psalms": {
        "url": "https://en.wikipedia.org/wiki/Psalms",
        "desc": "The hymnbook of ancient Israel — 150 poems of praise, lament, thanksgiving, and wisdom.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/King_David_Playing_the_Harp_-_Gerard_van_Honthorst_(1622).jpg?width=465",
        "image_alt": "King David Playing the Harp by Gerard van Honthorst",
        "image_credit": "Gerard van Honthorst, 1622",
    },
    "Proverbs": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Proverbs",
        "desc": "Wisdom literature attributed to Solomon — practical counsel for righteous living.",
    },
    "Ecclesiastes": {
        "url": "https://en.wikipedia.org/wiki/Ecclesiastes",
        "desc": "'Vanity of vanities' — the Preacher's meditation on meaning, time, and the fear of God.",
    },
    "Song of Solomon": {
        "url": "https://en.wikipedia.org/wiki/Song_of_Songs",
        "desc": "A lyric poem celebrating love between bride and bridegroom, read as allegory of divine love.",
    },
    "Isaiah": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Isaiah",
        "desc": "The greatest of the prophets — visions of judgment, the Suffering Servant, and a new creation.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Isaiah_(Michelangelo).jpg?width=411",
        "image_alt": "The Prophet Isaiah by Michelangelo, Sistine Chapel",
        "image_credit": "Michelangelo, 1509",
    },
    "Jeremiah": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Jeremiah",
        "desc": "The weeping prophet — warnings of exile, the promise of a new covenant, and Jerusalem's fall.",
    },
    "Lamentations": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Lamentations",
        "desc": "Five poems mourning the destruction of Jerusalem and the Temple in 586 BC.",
    },
    "Ezekiel": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Ezekiel",
        "desc": "Visions from Babylonian exile — the chariot throne, the valley of dry bones, and the restored Temple.",
    },
    "Daniel": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Daniel",
        "desc": "Stories of faithfulness in exile and apocalyptic visions of kingdoms and the Son of Man.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Peter_Paul_Rubens_-_Daniel_in_the_Lions'_Den_-_WGA20199.jpg?width=640",
        "image_alt": "Daniel in the Lions' Den by Peter Paul Rubens",
        "image_credit": "Peter Paul Rubens, c. 1615",
    },
    "Hosea": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Hosea",
        "desc": "God's faithful love portrayed through Hosea's marriage to the unfaithful Gomer.",
    },
    "Joel": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Joel",
        "desc": "A plague of locusts as prelude to the Day of the Lord, and the promise of the Spirit poured out.",
    },
    "Amos": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Amos",
        "desc": "A shepherd-prophet denounces social injustice: 'Let justice roll down like waters.'",
    },
    "Obadiah": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Obadiah",
        "desc": "The shortest book in the Old Testament — a prophecy against Edom.",
    },
    "Jonah": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Jonah",
        "desc": "The reluctant prophet, the great fish, and God's mercy extending even to Nineveh.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Pieter_Lastman_-_Jonah_and_the_Whale_-_Google_Art_Project.jpg?width=640",
        "image_alt": "Jonah and the Whale by Pieter Lastman",
        "image_credit": "Pieter Lastman, 1621",
    },
    "Micah": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Micah",
        "desc": "Justice, mercy, and humility — 'What doth the Lord require of thee?'",
    },
    "Nahum": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Nahum",
        "desc": "A prophecy of the fall of Nineveh, the great Assyrian capital.",
    },
    "Habakkuk": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Habakkuk",
        "desc": "A prophet's dialogue with God about evil and justice — 'the just shall live by faith.'",
    },
    "Zephaniah": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Zephaniah",
        "desc": "The Day of the Lord draws near — judgment and the promise of a humble remnant.",
    },
    "Haggai": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Haggai",
        "desc": "A call to rebuild the Temple after the return from Babylonian exile.",
    },
    "Zechariah": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Zechariah",
        "desc": "Night visions and messianic prophecies accompanying the rebuilding of the Temple.",
    },
    "Malachi": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Malachi",
        "desc": "The last Old Testament prophet — a call to faithfulness before the messenger of the covenant.",
    },
    "Matthew": {
        "url": "https://en.wikipedia.org/wiki/Gospel_of_Matthew",
        "desc": "The Gospel for the Jewish audience — Jesus as the promised Messiah, Son of David.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Sermon_on_the_Mount_Fra_Angelico.jpg?width=640",
        "image_alt": "Sermon on the Mount by Fra Angelico",
        "image_credit": "Fra Angelico, c. 1440",
    },
    "Mark": {
        "url": "https://en.wikipedia.org/wiki/Gospel_of_Mark",
        "desc": "The earliest Gospel — a swift, vivid portrait of Jesus as the suffering servant.",
    },
    "Luke": {
        "url": "https://en.wikipedia.org/wiki/Gospel_of_Luke",
        "desc": "The physician's careful account — Jesus as the compassionate saviour of all people.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Giotto_-_Scrovegni_-_-17-_-_Nativity,_Birth_of_Jesus.jpg?width=640",
        "image_alt": "Nativity, Birth of Jesus by Giotto",
        "image_credit": "Giotto, c. 1305",
    },
    "John": {
        "url": "https://en.wikipedia.org/wiki/Gospel_of_John",
        "desc": "'In the beginning was the Word' — the theological Gospel of signs and discourses.",
    },
    "Acts": {
        "url": "https://en.wikipedia.org/wiki/Acts_of_the_Apostles",
        "desc": "The birth of the Church — from Pentecost in Jerusalem to Paul's arrival in Rome.",
    },
    "Romans": {
        "url": "https://en.wikipedia.org/wiki/Epistle_to_the_Romans",
        "desc": "Paul's magisterial exposition of the Gospel — justification by faith, life in the Spirit.",
    },
    "1 Corinthians": {
        "url": "https://en.wikipedia.org/wiki/First_Epistle_to_the_Corinthians",
        "desc": "Paul addresses divisions, ethics, worship, and the resurrection in the Corinthian church.",
    },
    "2 Corinthians": {
        "url": "https://en.wikipedia.org/wiki/Second_Epistle_to_the_Corinthians",
        "desc": "Paul's most personal letter — weakness, suffering, and the treasure in earthen vessels.",
    },
    "Galatians": {
        "url": "https://en.wikipedia.org/wiki/Epistle_to_the_Galatians",
        "desc": "Freedom in Christ — Paul's passionate defence of justification by faith alone.",
    },
    "Ephesians": {
        "url": "https://en.wikipedia.org/wiki/Epistle_to_the_Ephesians",
        "desc": "The cosmic scope of God's plan — the Church as the body of Christ, the armour of God.",
    },
    "Philippians": {
        "url": "https://en.wikipedia.org/wiki/Epistle_to_the_Philippians",
        "desc": "A letter of joy from prison — 'Rejoice in the Lord always.'",
    },
    "Colossians": {
        "url": "https://en.wikipedia.org/wiki/Epistle_to_the_Colossians",
        "desc": "The supremacy of Christ — 'in him all things hold together.'",
    },
    "1 Thessalonians": {
        "url": "https://en.wikipedia.org/wiki/First_Epistle_to_the_Thessalonians",
        "desc": "Encouragement to a young church and teaching on the Lord's return.",
    },
    "2 Thessalonians": {
        "url": "https://en.wikipedia.org/wiki/Second_Epistle_to_the_Thessalonians",
        "desc": "Further teaching on the Day of the Lord and a call to steadfastness.",
    },
    "1 Timothy": {
        "url": "https://en.wikipedia.org/wiki/First_Epistle_to_Timothy",
        "desc": "Paul's pastoral counsel to young Timothy on church order and sound doctrine.",
    },
    "2 Timothy": {
        "url": "https://en.wikipedia.org/wiki/Second_Epistle_to_Timothy",
        "desc": "Paul's final letter — 'I have fought the good fight, I have finished the course.'",
    },
    "Titus": {
        "url": "https://en.wikipedia.org/wiki/Epistle_to_Titus",
        "desc": "Instructions for church leadership and godly living on the island of Crete.",
    },
    "Philemon": {
        "url": "https://en.wikipedia.org/wiki/Epistle_to_Philemon",
        "desc": "A personal appeal for the runaway slave Onesimus — brotherhood in Christ.",
    },
    "Hebrews": {
        "url": "https://en.wikipedia.org/wiki/Epistle_to_the_Hebrews",
        "desc": "Christ as the great high priest — the superiority of the new covenant over the old.",
    },
    "James": {
        "url": "https://en.wikipedia.org/wiki/Epistle_of_James",
        "desc": "Practical wisdom — 'faith without works is dead.'",
    },
    "1 Peter": {
        "url": "https://en.wikipedia.org/wiki/First_Epistle_of_Peter",
        "desc": "Hope in suffering — 'a living hope through the resurrection of Jesus Christ.'",
    },
    "2 Peter": {
        "url": "https://en.wikipedia.org/wiki/Second_Epistle_of_Peter",
        "desc": "Warnings against false teachers and the certainty of the Lord's return.",
    },
    "1 John": {
        "url": "https://en.wikipedia.org/wiki/First_Epistle_of_John",
        "desc": "'God is light' and 'God is love' — tests of true fellowship with God.",
    },
    "2 John": {
        "url": "https://en.wikipedia.org/wiki/Second_Epistle_of_John",
        "desc": "A brief letter on truth, love, and discernment against deceivers.",
    },
    "3 John": {
        "url": "https://en.wikipedia.org/wiki/Third_Epistle_of_John",
        "desc": "A personal note commending hospitality and warning against Diotrephes.",
    },
    "Jude": {
        "url": "https://en.wikipedia.org/wiki/Epistle_of_Jude",
        "desc": "An urgent appeal to 'contend for the faith' against ungodly intruders.",
    },
    "Revelation": {
        "url": "https://en.wikipedia.org/wiki/Book_of_Revelation",
        "desc": "The apocalyptic vision of John — the Lamb, the seven seals, and the new Jerusalem.",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Flemish_Apocalypse_(detail_of_key_art)_-_BL_Add_MS_17333_f133r.jpg?width=456",
        "image_alt": "The Apocalypse, Flemish illuminated manuscript",
        "image_credit": "Flemish manuscript, c. 1400",
    },
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

/* ── Dark mode ─────────────────────────────────────────────────────────── */

[data-theme="dark"] {
  --parchment:  #1a1a1a;
  --cream:      #222;
  --sidebar-bg: #111;
  --sidebar-fg: #c8c0b0;
  --sidebar-hi: #d4b063;
  --gold:       #c9a84c;
  --gold-light: #d4b063;
  --gold-faint: rgba(201, 168, 76, .25);
  --ink:        #d4d0c8;
  --ink-light:  #a89e8c;
  --ink-faint:  #7a7060;
  --wine:       #b8545e;
  --wine-dark:  #d4a060;
  --white:      #242424;
  --shadow:     rgba(0, 0, 0, .3);
}
[data-theme="dark"] .sidebar {
  background: linear-gradient(180deg, #111 0%, #1a1a1a 100%);
}
[data-theme="dark"] .sidebar::-webkit-scrollbar-thumb { background: #444; }
[data-theme="dark"] .version-select { background: rgba(255,255,255,.06); }
[data-theme="dark"] .version-select option { background: #111; }
[data-theme="dark"] .verse-text p:hover { background: rgba(201, 168, 76, .05); }

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --parchment:  #1a1a1a;
    --cream:      #222;
    --sidebar-bg: #111;
    --sidebar-fg: #c8c0b0;
    --sidebar-hi: #d4b063;
    --gold:       #c9a84c;
    --gold-light: #d4b063;
    --gold-faint: rgba(201, 168, 76, .25);
    --ink:        #d4d0c8;
    --ink-light:  #a89e8c;
    --ink-faint:  #7a7060;
    --wine:       #b8545e;
    --wine-dark:  #d4a060;
    --white:      #242424;
    --shadow:     rgba(0, 0, 0, .3);
  }
  :root:not([data-theme="light"]) .sidebar {
    background: linear-gradient(180deg, #111 0%, #1a1a1a 100%);
  }
  :root:not([data-theme="light"]) .sidebar::-webkit-scrollbar-thumb { background: #444; }
  :root:not([data-theme="light"]) .version-select { background: rgba(255,255,255,.06); }
  :root:not([data-theme="light"]) .version-select option { background: #111; }
  :root:not([data-theme="light"]) .verse-text p:hover { background: rgba(201, 168, 76, .05); }
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
  border-right: 2px solid var(--gold-faint);
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
.home-intro {
  text-align: center;
  max-width: 36rem;
  margin: 0 auto 2rem;
  font-size: .82rem;
  font-style: italic;
  color: var(--ink-faint);
  line-height: 1.8;
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
  position: relative;
}
.drop-cap .verse-num {
  position: absolute;
  top: .08em;
  left: -.4em;
  font-size: .18em;
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

/* ── Book info panel (with Wikipedia link, description, image) ────────── */

.book-info {
  max-width: 36rem;
  margin: 0 auto 1.5rem;
  text-align: center;
}
.book-info-desc {
  font-size: .82rem;
  font-style: italic;
  color: var(--ink-faint);
  line-height: 1.7;
  margin-bottom: .6rem;
}
.book-info-link {
  display: inline-block;
  font-size: .68rem;
  color: var(--wine);
  text-decoration: none;
  letter-spacing: .06em;
  text-transform: uppercase;
  border: 1px solid var(--gold-faint);
  padding: .3rem .8rem;
  transition: all .25s;
}
.book-info-link:hover {
  background: var(--wine);
  color: var(--white);
  border-color: var(--wine);
}
.book-image-wrap {
  max-width: 36rem;
  margin: 0 auto 1.8rem;
  text-align: center;
}
.book-image {
  max-width: 100%;
  max-height: 320px;
  border: 2px solid var(--gold-faint);
  box-shadow: 0 6px 24px var(--shadow);
  object-fit: contain;
}
.book-image-credit {
  font-size: .6rem;
  color: var(--ink-faint);
  font-style: italic;
  margin-top: .4rem;
  letter-spacing: .03em;
}

/* ── Dark mode toggle ─────────────────────────────────────────────────── */

.theme-toggle {
  position: fixed;
  top: .8rem;
  right: .8rem;
  z-index: 100;
  background: var(--white);
  color: var(--ink);
  border: 1px solid var(--gold-faint);
  width: 2.2rem;
  height: 2.2rem;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .25s;
  font-family: inherit;
  border-radius: 50%;
  box-shadow: 0 2px 8px var(--shadow);
  line-height: 1;
}
.theme-toggle:hover {
  background: var(--gold);
  color: var(--ink);
  border-color: var(--gold);
  transform: scale(1.1);
}

/* ── Reading progress bar ─────────────────────────────────────────────── */

.reading-progress {
  position: fixed;
  top: 0;
  left: var(--sidebar-w);
  right: 0;
  height: 3px;
  z-index: 90;
  background: transparent;
}
.reading-progress-bar {
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, var(--wine), var(--gold));
  transition: width .1s linear;
}

/* ── Scroll to top ────────────────────────────────────────────────────── */

.scroll-top {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 2.4rem;
  height: 2.4rem;
  background: var(--wine);
  color: var(--white);
  border: 1px solid var(--gold-faint);
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  visibility: hidden;
  transition: all .3s;
  z-index: 80;
  font-family: inherit;
}
.scroll-top.visible {
  opacity: 1;
  visibility: visible;
}
.scroll-top:hover {
  background: var(--gold);
  color: var(--ink);
  transform: translateY(-2px);
}

/* ── Verse hover highlight ────────────────────────────────────────────── */

.verse-text p {
  transition: background .2s;
  padding: .08em .3em;
  margin-left: -.3em;
  margin-right: -.3em;
  border-radius: 2px;
}
.verse-text p:hover {
  background: rgba(184, 134, 11, .06);
}

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
  .content { margin-left: 0; border-right: none; }
  .content-header h1 { font-size: 1.5rem; }
  .home-hero h1 { font-size: 1.8rem; }
  main { padding: 0 1rem 3rem; }
  .book-grid { grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); }
  .verse-text { text-align: left; }
  .version-grid { grid-template-columns: 1fr; padding: 0 1rem 3rem; }
  .reading-progress { left: 0; }
  .scroll-top { bottom: 1rem; right: 1rem; width: 2rem; height: 2rem; font-size: .8rem; }
  .book-image { max-height: 220px; }
  .theme-toggle { top: .5rem; right: .5rem; width: 1.8rem; height: 1.8rem; font-size: .85rem; }
}
"""

# ---------------------------------------------------------------------------
# Masonic SVG symbols (inline, no external files)
# ---------------------------------------------------------------------------

SVG_SQUARE_COMPASSES = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" class="masonic-symbol">
  <g fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
    <line x1="100" y1="30" x2="55" y2="170"/>
    <line x1="100" y1="30" x2="145" y2="170"/>
    <polyline points="60,90 100,140 140,90"/>
    <circle cx="100" cy="105" r="16" stroke-width="2"/>
    <text x="100" y="112" text-anchor="middle" font-family="Libre Baskerville, serif" font-size="22" font-weight="700" fill="currentColor" stroke="none">G</text>
  </g>
</svg>'''

SVG_ALL_SEEING_EYE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 140" class="masonic-symbol">
  <g fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="100,10 30,120 170,120" stroke-width="2"/>
    <line x1="100" y1="5" x2="100" y2="-8" stroke-width="1.5"/>
    <line x1="75" y1="12" x2="65" y2="0" stroke-width="1.5"/>
    <line x1="125" y1="12" x2="135" y2="0" stroke-width="1.5"/>
    <line x1="55" y1="30" x2="40" y2="20" stroke-width="1.5"/>
    <line x1="145" y1="30" x2="160" y2="20" stroke-width="1.5"/>
    <ellipse cx="100" cy="72" rx="30" ry="18"/>
    <circle cx="100" cy="72" r="9" fill="currentColor"/>
    <circle cx="100" cy="72" r="4" fill="none" stroke="#0a1628" stroke-width="1.5"/>
  </g>
</svg>'''

SVG_PILLARS = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 160" class="masonic-symbol masonic-pillars">
  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
    <rect x="40" y="30" width="30" height="100" rx="2"/>
    <rect x="35" y="22" width="40" height="10" rx="2"/>
    <rect x="35" y="128" width="40" height="10" rx="2"/>
    <circle cx="55" cy="16" r="8"/>
    <text x="55" y="152" text-anchor="middle" font-family="Libre Baskerville, serif" font-size="11" fill="currentColor" stroke="none" font-style="italic">Jachin</text>
    <rect x="230" y="30" width="30" height="100" rx="2"/>
    <rect x="225" y="22" width="40" height="10" rx="2"/>
    <rect x="225" y="128" width="40" height="10" rx="2"/>
    <circle cx="245" cy="16" r="8"/>
    <text x="245" y="152" text-anchor="middle" font-family="Libre Baskerville, serif" font-size="11" fill="currentColor" stroke="none" font-style="italic">Boaz</text>
    <path d="M 75 26 Q 150 -20 225 26" stroke-width="2.5"/>
    <polygon points="150,10 140,30 160,30" stroke-width="1.5"/>
    <circle cx="150" cy="22" r="4" fill="currentColor"/>
  </g>
</svg>'''

SVG_DIVIDER = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 30" class="masonic-divider">
  <g fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
    <line x1="10" y1="15" x2="130" y2="15" opacity=".4"/>
    <line x1="270" y1="15" x2="390" y2="15" opacity=".4"/>
    <line x1="200" y1="4" x2="185" y2="26"/>
    <line x1="200" y1="4" x2="215" y2="26"/>
    <polyline points="188,16 200,24 212,16"/>
    <text x="150" y="20" font-size="10" fill="currentColor" stroke="none">&#x2736;</text>
    <text x="244" y="20" font-size="10" fill="currentColor" stroke="none">&#x2736;</text>
  </g>
</svg>'''

SVG_TROWEL = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" class="masonic-symbol masonic-inline-sym">
  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M20,55 Q15,50 18,42 L40,15 Q42,12 45,15 L50,22 Q52,25 48,28 L25,52 Q22,56 20,55Z"/>
    <line x1="48" y1="28" x2="62" y2="60"/>
    <ellipse cx="64" cy="64" rx="6" ry="4" transform="rotate(-40 64 64)"/>
  </g>
</svg>'''

SVG_LEVEL_PLUMB = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80" class="masonic-symbol masonic-inline-sym">
  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="15,65 60,15 105,65"/>
    <line x1="60" y1="15" x2="60" y2="55"/>
    <circle cx="60" cy="60" r="5" fill="currentColor"/>
    <line x1="15" y1="65" x2="105" y2="65"/>
  </g>
</svg>'''

SVG_HOURGLASS_SKULL = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120" class="masonic-symbol masonic-inline-sym">
  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <rect x="25" y="5" width="50" height="6" rx="2"/>
    <rect x="25" y="69" width="50" height="6" rx="2"/>
    <path d="M30,11 L30,28 Q50,50 50,40 Q50,50 70,28 L70,11"/>
    <path d="M30,69 L30,52 Q50,30 50,40 Q50,30 70,52 L70,69"/>
    <line x1="48" y1="36" x2="52" y2="44" stroke-width="1.5"/>
    <circle cx="50" cy="97" r="12"/>
    <circle cx="45" cy="94" r="2.5" fill="currentColor"/>
    <circle cx="55" cy="94" r="2.5" fill="currentColor"/>
    <path d="M44,102 Q50,106 56,102" stroke-width="1.5"/>
  </g>
</svg>'''

SVG_ACACIA = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 60" class="masonic-symbol masonic-inline-sym">
  <g fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
    <line x1="20" y1="50" x2="80" y2="50" stroke-width="2"/>
    <line x1="50" y1="50" x2="50" y2="20"/>
    <ellipse cx="38" cy="22" rx="10" ry="6" fill="currentColor" opacity=".6" stroke="none"/>
    <ellipse cx="62" cy="22" rx="10" ry="6" fill="currentColor" opacity=".6" stroke="none"/>
    <ellipse cx="50" cy="14" rx="10" ry="6" fill="currentColor" opacity=".6" stroke="none"/>
    <ellipse cx="30" cy="30" rx="8" ry="5" fill="currentColor" opacity=".4" stroke="none"/>
    <ellipse cx="70" cy="30" rx="8" ry="5" fill="currentColor" opacity=".4" stroke="none"/>
  </g>
</svg>'''

SVG_BLAZING_STAR = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" class="masonic-symbol masonic-inline-sym">
  <g fill="currentColor" stroke="currentColor" stroke-width="1">
    <polygon points="50,5 58,35 90,35 64,55 73,85 50,67 27,85 36,55 10,35 42,35" opacity=".8"/>
    <circle cx="50" cy="48" r="10" fill="none" stroke-width="2"/>
    <text x="50" y="54" text-anchor="middle" font-family="Libre Baskerville, serif" font-size="14" font-weight="700" stroke="none">G</text>
  </g>
</svg>'''

# ---------------------------------------------------------------------------
# Masonic ritual passage annotations
# Key: (book_name, chapter_str) -> list of {verses, degree, symbol, title, note}
# Verse ranges: "1-3" or "7" or "all"
# ---------------------------------------------------------------------------

MASONIC_PASSAGES = {
    # ── First Degree: Entered Apprentice ───────────────────────────────────
    ("Genesis", "1"): [
        {"verses": "1-3", "degree": "Entered Apprentice",
         "symbol": "light", "title": "Let There Be Light",
         "note": "The candidate receives light &mdash; the central moment of initiation. From darkness to illumination, the first step on the path of the Craft."},
    ],
    ("Psalms", "133"): [
        {"verses": "1-3", "degree": "Entered Apprentice",
         "symbol": "unity", "title": "Behold, How Good",
         "note": "The psalm of Brotherly Love, traditionally recited at the opening of the Lodge. Unity is the first tenet of Freemasonry."},
    ],
    ("Ruth", "4"): [
        {"verses": "7-8", "degree": "Entered Apprentice",
         "symbol": "shoe", "title": "The Plucking Off of the Shoe",
         "note": "An ancient mode of confirmation &mdash; a token of sincerity. The rite of discalceation recalls the candidate&rsquo;s preparation for initiation."},
    ],
    ("Matthew", "7"): [
        {"verses": "7-8", "degree": "Entered Apprentice",
         "symbol": "ask", "title": "Ask, and It Shall Be Given",
         "note": "The candidate must seek knowledge of his own volition. None are compelled &mdash; the door opens only to him who knocks."},
    ],
    ("Amos", "7"): [
        {"verses": "7-8", "degree": "Entered Apprentice",
         "symbol": "plumb", "title": "The Plumb Line",
         "note": "The working tool of the Entered Apprentice. The Lord sets a plumb line in the midst of His people &mdash; a symbol of moral rectitude and upright conduct."},
    ],

    # ── Second Degree: Fellow Craft ────────────────────────────────────────
    ("Judges", "12"): [
        {"verses": "1-6", "degree": "Fellow Craft",
         "symbol": "word", "title": "Shibboleth",
         "note": "The password of the Second Degree. The Ephraimites could not frame to pronounce it right &mdash; a token of recognition among the initiated."},
    ],
    ("1 Kings", "6"): [
        {"verses": "1-8", "degree": "Fellow Craft",
         "symbol": "temple", "title": "The Building of the Temple",
         "note": "The Fellow Craft ascends the winding staircase of Solomon&rsquo;s Temple. These chapters are the heart of Craft Masonry &mdash; the sacred architecture of the soul."},
    ],
    ("1 Kings", "7"): [
        {"verses": "13-22", "degree": "Fellow Craft",
         "symbol": "pillars", "title": "The Two Great Pillars",
         "note": "Jachin and Boaz &mdash; &ldquo;He shall establish&rdquo; and &ldquo;In it is strength.&rdquo; The twin pillars at the porch of the Temple, through which the Fellow Craft symbolically passes."},
    ],
    ("2 Chronicles", "3"): [
        {"verses": "15-17", "degree": "Fellow Craft",
         "symbol": "pillars", "title": "Pillars of the Porch",
         "note": "The parallel account of the pillars, with their chapiters of lilies, pomegranates, and network &mdash; symbols of peace, plenty, and the interconnection of all Brethren."},
    ],
    ("Ecclesiastes", "12"): [
        {"verses": "1-7", "degree": "Fellow Craft",
         "symbol": "mortality", "title": "Remember Thy Creator",
         "note": "A meditation on mortality read in the Second Degree. The silver cord, the golden bowl, the pitcher at the fountain &mdash; all allegories of the frailty of life."},
    ],

    # ── Third Degree: Master Mason ─────────────────────────────────────────
    ("1 Kings", "5"): [
        {"verses": "1-18", "degree": "Master Mason",
         "symbol": "craft", "title": "The Preparation of Materials",
         "note": "Solomon&rsquo;s covenant with Hiram of Tyre. The cedar, the stone, the levy of workers &mdash; the great labour begins. In the Third Degree, the legend of the Master Builder unfolds."},
    ],
    ("Genesis", "4"): [
        {"verses": "22", "degree": "Master Mason",
         "symbol": "craft", "title": "Tubal-Cain",
         "note": "The first artificer in brass and iron &mdash; an instructor of every craftsman. Tubal-Cain is the pass-grip word of the Master Mason degree."},
    ],
    ("2 Chronicles", "2"): [
        {"verses": "1-16", "degree": "Master Mason",
         "symbol": "temple", "title": "Solomon Prepares to Build",
         "note": "The census of the workers, the request for a cunning man &mdash; the Temple as the supreme symbol of the Master&rsquo;s work, ordered from chaos."},
    ],
    ("Ecclesiastes", "3"): [
        {"verses": "1-8", "degree": "Master Mason",
         "symbol": "time", "title": "To Every Thing a Season",
         "note": "A time to be born and a time to die, a time to build up &mdash; the great allegory of cycles. The Master Mason contemplates the hourglass."},
    ],
    ("John", "1"): [
        {"verses": "1-5", "degree": "Master Mason",
         "symbol": "light", "title": "In the Beginning Was the Word",
         "note": "The Logos &mdash; the sacred Word, lost and sought. The light shineth in darkness, and the darkness comprehended it not. The central mystery of the Third Degree."},
    ],

    # ── General Masonic significance ───────────────────────────────────────
    ("Proverbs", "2"): [
        {"verses": "1-9", "degree": "General",
         "symbol": "wisdom", "title": "The Search for Wisdom",
         "note": "Seek her as silver, search for her as hid treasures &mdash; the Craft is a system of morality, veiled in allegory and illustrated by symbols."},
    ],
    ("Genesis", "28"): [
        {"verses": "10-22", "degree": "General",
         "symbol": "ladder", "title": "Jacob's Ladder",
         "note": "The ladder reaching to heaven, with angels ascending and descending. In Masonic symbolism: Faith, Hope, and Charity &mdash; the three principal rounds."},
    ],
    ("Exodus", "3"): [
        {"verses": "1-6", "degree": "General",
         "symbol": "fire", "title": "The Burning Bush",
         "note": "Holy ground &mdash; put off thy shoes. The sacred fire that burns but does not consume, a symbol of the Divine presence in the Lodge."},
    ],
    ("Psalms", "24"): [
        {"verses": "3-5", "degree": "General",
         "symbol": "purity", "title": "Who Shall Ascend",
         "note": "He that hath clean hands, and a pure heart &mdash; the qualifications for admission to the holy hill, and to the Lodge."},
    ],
    ("Isaiah", "28"): [
        {"verses": "16-17", "degree": "General",
         "symbol": "cornerstone", "title": "The Cornerstone",
         "note": "A tried stone, a precious cornerstone, a sure foundation &mdash; judgment laid to the line, and righteousness to the plummet. The working tools made divine."},
    ],
    ("Proverbs", "3"): [
        {"verses": "13-20", "degree": "General",
         "symbol": "wisdom", "title": "Happy Is the Man That Findeth Wisdom",
         "note": "She is more precious than rubies. By wisdom hath the Lord founded the earth &mdash; the Great Architect of the Universe, the supreme Masonic conception of the Divine."},
    ],
    ("Psalms", "127"): [
        {"verses": "1", "degree": "General",
         "symbol": "temple", "title": "Except the Lord Build the House",
         "note": "The builders labour in vain without the Grand Architect. The eternal lesson of the Craft: all labour must be consecrated."},
    ],
    ("Genesis", "22"): [
        {"verses": "1-14", "degree": "General",
         "symbol": "faith", "title": "The Sacrifice of Isaac on Mount Moriah",
         "note": "Mount Moriah &mdash; the same ground upon which Solomon would raise the Temple. The supreme trial of faith, the foundation stone of the sacred hill."},
    ],
}

# Map symbol keys to inline SVG snippets for margin annotations
SYMBOL_SVGS = {
    "light":       SVG_ALL_SEEING_EYE,
    "unity":       SVG_SQUARE_COMPASSES,
    "pillars":     SVG_PILLARS,
    "temple":      SVG_PILLARS,
    "craft":       SVG_TROWEL,
    "plumb":       SVG_LEVEL_PLUMB,
    "mortality":   SVG_HOURGLASS_SKULL,
    "time":        SVG_HOURGLASS_SKULL,
    "word":        SVG_BLAZING_STAR,
    "wisdom":      SVG_BLAZING_STAR,
    "ask":         SVG_BLAZING_STAR,
    "shoe":        SVG_SQUARE_COMPASSES,
    "ladder":      SVG_LEVEL_PLUMB,
    "fire":        SVG_ALL_SEEING_EYE,
    "purity":      SVG_LEVEL_PLUMB,
    "cornerstone": SVG_TROWEL,
    "faith":       SVG_ALL_SEEING_EYE,
}

DEGREE_LABELS = {
    "Entered Apprentice": "I\u00b0",
    "Fellow Craft":       "II\u00b0",
    "Master Mason":       "III\u00b0",
    "General":            "\u25b3",
}

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
.masonic-theme .content {
  border-right-color: rgba(201, 168, 76, .3);
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

/* ── Starfield background ──────────────────────────────────────────────── */

.masonic-theme .content {
  background:
    radial-gradient(1px 1px at 10% 15%, rgba(201,168,76,.3), transparent),
    radial-gradient(1px 1px at 25% 35%, rgba(201,168,76,.2), transparent),
    radial-gradient(1px 1px at 40% 8%, rgba(201,168,76,.25), transparent),
    radial-gradient(1px 1px at 55% 42%, rgba(201,168,76,.15), transparent),
    radial-gradient(1px 1px at 70% 20%, rgba(201,168,76,.3), transparent),
    radial-gradient(1px 1px at 85% 55%, rgba(201,168,76,.2), transparent),
    radial-gradient(1px 1px at 15% 65%, rgba(201,168,76,.15), transparent),
    radial-gradient(1px 1px at 50% 80%, rgba(201,168,76,.2), transparent),
    radial-gradient(1px 1px at 92% 12%, rgba(201,168,76,.25), transparent),
    radial-gradient(1px 1px at 78% 72%, rgba(201,168,76,.15), transparent),
    radial-gradient(1px 1px at 33% 90%, rgba(201,168,76,.2), transparent),
    radial-gradient(1px 1px at 62% 58%, rgba(201,168,76,.12), transparent);
  background-color: #0a1628;
}

/* ── Checkered floor (chapter pages) ───────────────────────────────────── */

.masonic-theme .chapter-nav {
  background:
    repeating-conic-gradient(
      rgba(201,168,76,.06) 0% 25%,
      transparent 0% 50%
    )
    0 0 / 24px 24px;
  padding: 1.5rem 1rem;
  border-top: 1px solid rgba(201,168,76,.2);
  margin-top: 2.5rem;
}

/* ── Ritual verse annotations ──────────────────────────────────────────── */

.masonic-annotation {
  position: relative;
  background: rgba(201, 168, 76, .04);
  border-left: 3px solid rgba(201, 168, 76, .5);
  padding: .6rem .8rem .6rem 1rem;
  margin: 1.2rem 0;
  border-radius: 0 4px 4px 0;
}
.masonic-annotation::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(201,168,76,.06), transparent 60%);
  pointer-events: none;
  border-radius: 0 4px 4px 0;
}

.masonic-ann-header {
  display: flex;
  align-items: center;
  gap: .5rem;
  margin-bottom: .4rem;
}
.masonic-ann-degree {
  font-size: .6rem;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: #c9a84c;
  background: rgba(201,168,76,.12);
  padding: .15rem .5rem;
  border: 1px solid rgba(201,168,76,.25);
}
.masonic-ann-title {
  font-size: .78rem;
  font-weight: 700;
  font-style: italic;
  color: #dbbe5e;
  letter-spacing: .04em;
}
.masonic-ann-note {
  font-size: .72rem;
  color: #a0aec0;
  line-height: 1.6;
  font-style: italic;
}
.masonic-ann-symbol {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  color: rgba(201,168,76,.6);
}
.masonic-ann-symbol .masonic-symbol,
.masonic-ann-symbol .masonic-inline-sym {
  width: 100%;
  height: 100%;
}

/* Highlighted verse (within annotated passage) */
.masonic-verse-hl {
  background: rgba(201, 168, 76, .06);
  border-left: 2px solid rgba(201, 168, 76, .3);
  padding-left: .6em;
  margin-left: -.6em;
}

/* ── Lodge Reference page ──────────────────────────────────────────────── */

.lodge-ref-intro {
  text-align: center;
  max-width: 36rem;
  margin: 0 auto 2rem;
  font-style: italic;
  color: #a0aec0;
  font-size: .85rem;
  line-height: 1.8;
}

.degree-section {
  margin: 2rem 0;
}
.degree-heading {
  display: flex;
  align-items: center;
  gap: .8rem;
  margin-bottom: 1rem;
  padding-bottom: .5rem;
  border-bottom: 1px solid rgba(201,168,76,.2);
}
.degree-heading h3 {
  font-size: 1.1rem;
  color: #dbbe5e;
  letter-spacing: .08em;
}
.degree-heading .degree-num {
  font-size: .75rem;
  font-weight: 700;
  color: #0a1628;
  background: #c9a84c;
  padding: .2rem .6rem;
  letter-spacing: .1em;
}
.degree-heading .degree-sym {
  width: 36px;
  height: 36px;
  color: #c9a84c;
}
.degree-heading .degree-sym .masonic-symbol,
.degree-heading .degree-sym .masonic-inline-sym {
  width: 100%;
  height: 100%;
}

.ref-card {
  display: block;
  background: #111e34;
  border: 1px solid rgba(201,168,76,.15);
  padding: 1rem 1.2rem;
  margin-bottom: .8rem;
  text-decoration: none;
  color: #d4dae6;
  transition: all .2s;
  position: relative;
  overflow: hidden;
}
.ref-card::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0;
  width: 100%; height: 2px;
  background: #c9a84c;
  transform: scaleX(0);
  transform-origin: center;
  transition: transform .3s;
}
.ref-card:hover {
  border-color: #c9a84c;
  box-shadow: 0 4px 16px rgba(201,168,76,.12);
}
.ref-card:hover::after { transform: scaleX(1); }
.ref-card .ref-title {
  font-size: .88rem;
  font-weight: 700;
  color: #dbbe5e;
  margin-bottom: .2rem;
}
.ref-card .ref-cite {
  font-size: .72rem;
  color: #c9a84c;
  font-style: italic;
  margin-bottom: .3rem;
}
.ref-card .ref-note {
  font-size: .72rem;
  color: #8899b0;
  line-height: 1.5;
}

/* Responsive fixes for masonic theme */
@media (max-width: 700px) {
  .masonic-theme .content {
    border-right: none;
  }
  .masonic-annotation {
    margin-left: -.5rem;
    margin-right: -.5rem;
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

/* Masonic overrides for new features */
.masonic-theme .book-info-desc {
  color: #8899b0;
}
.masonic-theme .book-info-link {
  color: #c9a84c;
  border-color: rgba(201, 168, 76, .3);
}
.masonic-theme .book-info-link:hover {
  background: #c9a84c;
  color: #0a1628;
  border-color: #c9a84c;
}
.masonic-theme .book-image {
  border-color: rgba(201, 168, 76, .3);
}
.masonic-theme .book-image-credit {
  color: #6b7a90;
}
.masonic-theme .reading-progress-bar {
  background: linear-gradient(90deg, #c9a84c, #dbbe5e);
}
.masonic-theme .scroll-top {
  background: #111e34;
  color: #c9a84c;
  border-color: rgba(201, 168, 76, .3);
}
.masonic-theme .scroll-top:hover {
  background: #c9a84c;
  color: #0a1628;
}
.masonic-theme .verse-text p:hover {
  background: rgba(201, 168, 76, .04);
}
"""

# ---------------------------------------------------------------------------
# Sidebar JS (for mobile toggle + version switcher)
# ---------------------------------------------------------------------------

THEME_JS = r"""
(function(){
  var saved = localStorage.getItem('bible-theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
})();
"""

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
  // Reading progress bar
  var bar = document.querySelector('.reading-progress-bar');
  var scrollBtn = document.querySelector('.scroll-top');
  if (bar || scrollBtn) {
    window.addEventListener('scroll', function() {
      var h = document.documentElement;
      var pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
      if (bar) bar.style.width = pct + '%';
      if (scrollBtn) {
        if (h.scrollTop > 400) scrollBtn.classList.add('visible');
        else scrollBtn.classList.remove('visible');
      }
    });
  }
  if (scrollBtn) {
    scrollBtn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
  // Dark mode toggle
  var themeBtn = document.querySelector('.theme-toggle');
  if (themeBtn) {
    function updateIcon() {
      var current = document.documentElement.getAttribute('data-theme');
      var isDark = current === 'dark' || (!current && window.matchMedia('(prefers-color-scheme: dark)').matches);
      themeBtn.textContent = isDark ? '\u2600' : '\u263D';
      themeBtn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
    }
    updateIcon();
    themeBtn.addEventListener('click', function() {
      var current = document.documentElement.getAttribute('data-theme');
      var isDark = current === 'dark' || (!current && window.matchMedia('(prefers-color-scheme: dark)').matches);
      var next = isDark ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('bible-theme', next);
      updateIcon();
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
  <script>{THEME_JS}</script>
</head>
<body{body_cls}>
<div class="reading-progress"><div class="reading-progress-bar"></div></div>
<button class="theme-toggle" aria-label="Toggle dark mode">&#x263D;</button>
<div class="page-wrap">
{sidebar}
<div class="content">
{body_content}
{masonic_footer}
</div>
</div>
<button class="scroll-top" aria-label="Scroll to top">&#x2191;</button>
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
  <div class="home-intro">
    Seven public-domain translations of the Holy Scriptures, spanning from the
    eighteenth to the twentieth century, presented here for study, devotion, and
    comparison.
  </div>
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
  <script>{THEME_JS}</script>
</head>
<body>
<button class="theme-toggle" aria-label="Toggle dark mode">&#x263D;</button>
{body}
<script>{SIDEBAR_JS}</script>
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
        lodge_ref = f"""
    <div style="text-align:center;margin:2rem 0 1rem">
      <a class="ref-card" href="lodge-reference.html" style="display:inline-block;max-width:28rem;text-align:center">
        <div class="ref-title" style="font-size:1rem">&#x25B3; Lodge Reference &#x25B3;</div>
        <div class="ref-note" style="margin-top:.3rem">Key passages for Masonic ritual and study, arranged by degree</div>
      </a>
    </div>
    <div>{SVG_DIVIDER}</div>"""
    else:
        hero_symbol = ""
        divider = '<div class="ornament">&mdash; &#x2726; &#x271D; &#x2726; &mdash;</div>'
        pillars = ""
        title_text = "The Holy Bible"
        lodge_ref = ""

    body = f"""
  <div class="content-header">
    {hero_symbol}
    <h1>{title_text}</h1>
    <p class="subtitle">{esc(ver['name'])}</p>
  </div>
  {divider}
  {pillars}
  {lodge_ref}
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

    # Book info from BOOK_WIKI
    wiki = BOOK_WIKI.get(book_name, {})
    info_html = ""
    if wiki:
        desc = wiki.get("desc", "")
        url = wiki.get("url", "")
        desc_part = f'<div class="book-info-desc">{esc(desc)}</div>' if desc else ""
        link_part = f'<a class="book-info-link" href="{url}" target="_blank" rel="noopener">Read on Wikipedia &#x2197;</a>' if url else ""
        info_html = f'<div class="book-info">{desc_part}{link_part}</div>'

    image_html = ""
    if wiki.get("image"):
        credit = wiki.get("image_credit", "")
        credit_part = f'<div class="book-image-credit">{esc(credit)}</div>' if credit else ""
        image_html = f'''<div class="book-image-wrap">
      <img class="book-image" src="{wiki["image"]}" alt="{esc(wiki.get("image_alt", book_name))}" loading="lazy">
      {credit_part}
    </div>'''

    body = f"""
  <div class="content-header">
    {header_sym}
    <h1>{esc(book_name)}</h1>
    <p class="subtitle">{esc(ver['name'])}</p>
  </div>
  {divider}
  <main>
    {image_html}
    {info_html}
    <div class="book-heading">
      <h2>{esc(book_name)}</h2>
      <div class="chapter-count">{n_ch} {w}</div>
    </div>
    <div class="chapter-grid">
{links}    </div>
  </main>"""

    return page_shell(f"{book_name} - {ver['abbr']}", body, sb, depth=2,
                      theme=get_theme(ver))


def _parse_verse_range(rng_str):
    """Parse '1-3' or '7' or 'all' into a set of verse number strings."""
    if rng_str == "all":
        return None  # means all
    parts = rng_str.split("-")
    if len(parts) == 2:
        return {str(v) for v in range(int(parts[0]), int(parts[1]) + 1)}
    return {parts[0]}


def generate_chapter_page(ver, books, book_name, chapter_index):
    masonic = is_masonic(ver)
    book = books[book_name]
    chapters = book["chapters"]
    ch = chapters[chapter_index]
    ch_num = ch["chapter"]

    # Get Masonic annotations for this chapter
    annotations = MASONIC_PASSAGES.get((book_name, str(ch_num)), []) if masonic else []

    # Build a map of verse_num -> list of annotations that include it
    verse_ann_map = {}  # verse_str -> [ann, ...]
    ann_start_verses = {}  # ann index -> first verse in range (to insert annotation box before)
    for ai, ann in enumerate(annotations):
        vset = _parse_verse_range(ann["verses"])
        if vset is None:
            for v in ch["verses"]:
                verse_ann_map.setdefault(v["verse"], []).append(ai)
            ann_start_verses[ai] = ch["verses"][0]["verse"] if ch["verses"] else "1"
        else:
            first = min(vset, key=lambda x: int(x))
            ann_start_verses[ai] = first
            for vs in vset:
                verse_ann_map.setdefault(vs, []).append(ai)

    # Track which annotations we've already inserted
    inserted_anns = set()

    verses_html = ""
    for i, v in enumerate(ch["verses"]):
        text = esc(v["text"])
        vn = v["verse"]

        # Insert annotation box before the first highlighted verse
        if masonic:
            for ai, ann in enumerate(annotations):
                if ai not in inserted_anns and ann_start_verses.get(ai) == vn:
                    inserted_anns.add(ai)
                    sym_svg = SYMBOL_SVGS.get(ann.get("symbol", ""), SVG_BLAZING_STAR)
                    deg_label = DEGREE_LABELS.get(ann["degree"], "")
                    verses_html += f'''<div class="masonic-annotation">
  <div class="masonic-ann-header">
    <span class="masonic-ann-degree">{deg_label} {esc(ann["degree"])}</span>
    <span class="masonic-ann-title">{ann["title"]}</span>
    <span class="masonic-ann-symbol">{sym_svg}</span>
  </div>
  <div class="masonic-ann-note">{ann["note"]}</div>
</div>\n'''

        is_hl = vn in verse_ann_map
        hl_cls = ' class="masonic-verse-hl"' if is_hl else ''

        if i == 0 and text:
            first_letter = text[0]
            rest = text[1:]
            verses_html += f'<p{hl_cls}><span class="drop-cap"><span class="verse-num">{vn}</span>{first_letter}</span>{rest}</p>\n'
        else:
            verses_html += f'<p{hl_cls}><span class="verse-num">{vn}</span>{text}</p>\n'

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

    # Show book image and description on first chapter only
    wiki = BOOK_WIKI.get(book_name, {})
    first_ch_extras = ""
    if chapter_index == 0 and wiki:
        parts = []
        if wiki.get("image"):
            credit = wiki.get("image_credit", "")
            credit_part = f'<div class="book-image-credit">{esc(credit)}</div>' if credit else ""
            parts.append(f'''<div class="book-image-wrap">
        <img class="book-image" src="{wiki["image"]}" alt="{esc(wiki.get("image_alt", book_name))}" loading="lazy">
        {credit_part}
      </div>''')
        if wiki.get("desc"):
            link_part = ""
            if wiki.get("url"):
                link_part = f' <a class="book-info-link" href="{wiki["url"]}" target="_blank" rel="noopener">Wikipedia &#x2197;</a>'
            parts.append(f'<div class="book-info"><div class="book-info-desc">{esc(wiki["desc"])}</div>{link_part}</div>')
        first_ch_extras = "\n    ".join(parts)

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
    {first_ch_extras}
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


def generate_lodge_reference(ver, books):
    """Generate the Masonic Lodge Reference page with passages grouped by degree."""
    sb = sidebar_html(ver, VERSIONS, books, depth=0)

    # Group passages by degree
    degree_order = ["Entered Apprentice", "Fellow Craft", "Master Mason", "General"]
    degree_syms = {
        "Entered Apprentice": SVG_LEVEL_PLUMB,
        "Fellow Craft":       SVG_PILLARS,
        "Master Mason":       SVG_HOURGLASS_SKULL,
        "General":            SVG_BLAZING_STAR,
    }
    degree_subtitles = {
        "Entered Apprentice": "The First Degree &mdash; From Darkness to Light",
        "Fellow Craft":       "The Second Degree &mdash; The Winding Staircase",
        "Master Mason":       "The Third Degree &mdash; The Legend of the Master Builder",
        "General":            "Passages of Universal Masonic Significance",
    }

    grouped = {d: [] for d in degree_order}
    for (bk, ch), anns in sorted(MASONIC_PASSAGES.items(), key=lambda x: (CANONICAL_ORDER.index(x[0][0]) if x[0][0] in CANONICAL_ORDER else 999, int(x[0][1]))):
        for ann in anns:
            grouped[ann["degree"]].append((bk, ch, ann))

    sections_html = ""
    for deg in degree_order:
        entries = grouped[deg]
        if not entries:
            continue
        deg_num = DEGREE_LABELS.get(deg, "")
        sym = degree_syms.get(deg, SVG_BLAZING_STAR)
        sub = degree_subtitles.get(deg, "")

        cards_html = ""
        for bk, ch, ann in entries:
            verse_ref = f"{bk} {ch}:{ann['verses']}"
            href = f"{slug(bk)}/{ch}.html"
            cards_html += f'''<a class="ref-card" href="{href}">
  <div class="ref-title">{ann["title"]}</div>
  <div class="ref-cite">{esc(verse_ref)}</div>
  <div class="ref-note">{ann["note"]}</div>
</a>\n'''

        sections_html += f'''<div class="degree-section">
  <div class="degree-heading">
    <span class="degree-num">{deg_num}</span>
    <h3>{esc(deg)}</h3>
    <span class="degree-sym">{sym}</span>
  </div>
  <p style="font-size:.78rem;color:#8899b0;font-style:italic;margin-bottom:1rem">{sub}</p>
  {cards_html}
</div>\n'''

    body = f"""
  <div class="content-header">
    <div class="masonic-hero-symbol">{SVG_SQUARE_COMPASSES}</div>
    <h1>Lodge Reference</h1>
    <p class="subtitle">Key Passages for Masonic Ritual &amp; Study</p>
  </div>
  <div>{SVG_DIVIDER}</div>
  <main>
    <div class="lodge-ref-intro">
      The Volume of the Sacred Law is one of the Three Great Lights of Freemasonry,
      and lies open upon the altar of every regular Lodge. The following passages bear
      special significance in the rituals, symbols, and teachings of the Craft &mdash;
      arranged here by degree for the instruction of the Brethren.
    </div>
    {sections_html}
  </main>"""

    return page_shell("Lodge Reference - Masonic Bible", body, sb, depth=1,
                      theme="masonic")


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

        # Lodge Reference page (Masonic edition only)
        if is_masonic(ver):
            with open(os.path.join(ver_dir, "lodge-reference.html"), "w") as f:
                f.write(generate_lodge_reference(ver, books))
            print(f"  [{ver['abbr']}] lodge-reference.html")

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
