"""Turn the lecture PDFs into lernen/course.js.

Only slide text is kept. Diagrams stay on the rendered slide images.
Table-of-contents and cover slides are navigation, not lessons.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / "Data"

FILES = {
    "ft1": DATA / "FT-1_Urformen_2015-07-08.pdf",
    "ft2": DATA / "FT-2_Umformen_2015-07-08.pdf",
    "ft3": DATA / "FT-3_Trennen_2015-07-08.pdf",
    "ft5": DATA / "FT-5_Beschichten_2015-07-08.pdf",
    "ft6": DATA / "FT-6_Handhabung_von_Industrierobotern_2015-07-08.pdf",
    "ft7": DATA / "FT-7_Grundlagen_Fertigungsprozesse_2015-07-08.pdf",
}

OUTLINE_KEYS = (
    "Urformen",
    "Umformen",
    "Trennen",
    "Fügen",
    "Beschichten",
    "Grundlagen",
    "Handhabung",
    "Industrieroboter",
    "Einführung",
    "Stoffeigenschaft",
)


def pages_of(spec) -> list[int]:
    if isinstance(spec, tuple):
        return list(range(spec[0], spec[1] + 1))
    return list(spec)


MODULES = [
    {
        "id": "ueberblick",
        "file": "ft1",
        "title": "Überblick",
        "kicker": "FT I",
        "verb": "",
        "source": "FT-1, vordere Folien",
        "needle": "Der Begriff Fertigungstechnik beinhaltet",
        "sections": [
            {
                "id": "veranstaltung",
                "code": "",
                "title": "Veranstaltung und Lernziele",
                "pages": (3, 7),
            },
            {
                "id": "betrieb",
                "code": "",
                "title": "Industrieunternehmen und Begriffe",
                "pages": [2, 9, 10, 11],
            },
            {
                "id": "din",
                "code": "DIN 8580",
                "title": "Einteilung der Fertigungsverfahren",
                "pages": (12, 14),
            },
        ],
    },
    {
        "id": "urformen",
        "file": "ft1",
        "title": "Urformen",
        "kicker": "Modul 1",
        "verb": "Zusammenhalt schaffen",
        "source": "FT-1 Urformen",
        "needle": "Urformen ist das Fertigen",
        "sections": [
            {"id": "grundlagen", "code": "1.1", "title": "Grundlagen", "pages": (17, 60)},
            {
                "id": "sandguss",
                "code": "1.2",
                "title": "Sandguss, Einteilung, Verfahren, Abläufe",
                "pages": (62, 87),
            },
            {
                "id": "druckguss",
                "code": "1.3",
                "title": "Druckguss, Einteilung, Verfahren, Abläufe",
                "pages": (89, 113),
            },
            {"id": "fehler", "code": "1.4", "title": "Fehler beim Gießen", "pages": (115, 119)},
            {
                "id": "konstruktion",
                "code": "1.5",
                "title": "Einflussgrößen und Konstruktionsrichtlinien",
                "pages": (121, 136),
            },
        ],
    },
    {
        "id": "umformen",
        "file": "ft2",
        "title": "Umformen",
        "kicker": "Modul 2",
        "verb": "Zusammenhalt beibehalten",
        "source": "FT-2 Umformen",
        "needle": "Umformen ist nach DIN 8580",
        "sections": [
            {"id": "literatur", "code": "", "title": "Literatur zur Vorlesung", "pages": [2]},
            {"id": "einteilung", "code": "", "title": "Einteilung der Fertigungsverfahren", "pages": [4]},
            {
                "id": "vorteile",
                "code": "2.1",
                "title": "Einteilung und Vorteile der Umformverfahren",
                "pages": (6, 13),
            },
            {
                "id": "grundlagen",
                "code": "2.2",
                "title": "Ausgewählte umformtechnische Grundlagen",
                "pages": (15, 33),
            },
            {
                "id": "druck",
                "code": "2.3",
                "title": "Verfahren des Druckumformens",
                "pages": (35, 85),
            },
            {
                "id": "zugdruck",
                "code": "2.4",
                "title": "Verfahren des Zug-Druckumformens",
                "pages": (87, 113),
            },
            {"id": "zug", "code": "2.5", "title": "Zugumformen", "pages": (115, 118)},
            {"id": "biegen", "code": "2.6", "title": "Biegen", "pages": (120, 135)},
        ],
    },
    {
        "id": "trennen",
        "file": "ft3",
        "title": "Trennen",
        "kicker": "Modul 3",
        "verb": "Zusammenhalt vermindern",
        "source": "FT-3 Trennen",
        "needle": "Trennen ist Fertigen durch",
        "sections": [
            {"id": "literatur", "code": "", "title": "Literatur zur Vorlesung", "pages": [2]},
            {"id": "einteilung-din", "code": "", "title": "Einteilung der Fertigungsverfahren", "pages": [4]},
            {
                "id": "einteilung",
                "code": "3.1",
                "title": "Einteilung der Fertigungsverfahren Trennen",
                "pages": (6, 11),
            },
            {
                "id": "basis",
                "code": "3.2",
                "title": "Basisgrößen und Grundlagen der Zerspantechnik",
                "pages": (14, 62),
            },
            {"id": "verschleiss", "code": "3.3", "title": "Verschleiß beim Trennen", "pages": (63, 84)},
            {
                "id": "einfluss",
                "code": "3.4",
                "title": "Weitere Einflussfaktoren auf den Spanprozess",
                "pages": (85, 92),
            },
            {"id": "zerteilen", "code": "3.5", "title": "Verfahren des Zerteilens", "pages": (93, 99)},
            {
                "id": "spanen",
                "code": "3.6",
                "title": "Verfahren des Zerspanens mit geometrisch bestimmter Schneide",
                "pages": (100, 186),
            },
            {
                "id": "optimierung",
                "code": "3.7",
                "title": "Optimierung der Trennverfahren zur Erhöhung der Mengenleistung",
                "pages": (188, 199),
            },
        ],
    },
    {
        "id": "beschichten",
        "file": "ft5",
        "title": "Beschichten",
        "kicker": "Modul 5",
        "verb": "Zusammenhalt vermehren",
        "source": "FT-5 Beschichten",
        "needle": "Beschichten ist das Erzeugen",
        "sections": [
            {"id": "literatur", "code": "", "title": "Literatur zur Vorlesung", "pages": [2, 3]},
            {
                "id": "einfuehrung",
                "code": "5.1",
                "title": "Einführung und Verfahrensübersichten",
                "pages": (6, 9),
            },
            {
                "id": "fluessig",
                "code": "5.2",
                "title": "Beschichten aus flüssigem oder plastischen Zustand",
                "pages": (11, 35),
            },
            {
                "id": "gas",
                "code": "5.3",
                "title": "Beschichten aus gasförmigem, dampfförmigen oder ionisiertem Zustand",
                "pages": (37, 70),
            },
            {
                "id": "fest",
                "code": "5.4",
                "title": "Beschichten aus pulverförmigem oder festen Zustand",
                "pages": (72, 102),
            },
        ],
    },
    {
        "id": "roboter",
        "file": "ft6",
        "title": "Handhabung von Industrierobotern",
        "kicker": "Modul 6",
        "verb": "",
        "source": "FT-6 Industrieroboter",
        "needle": "Ein Industrieroboter ist",
        "sections": [
            {
                "id": "begriffe",
                "code": "6.1",
                "title": "Definitionen und Begriffe zum Industrieroboter",
                "pages": (4, 7),
            },
            {
                "id": "aufbau",
                "code": "6.2",
                "title": "Grundlagen, Aufbau und einsatzspezifische Kenngrößen",
                "pages": (9, 11),
            },
            {
                "id": "bauformen",
                "code": "6.3",
                "title": "Grundtypen und Bauformen von Industrierobotern",
                "pages": (13, 19),
            },
            {"id": "programm", "code": "6.4", "title": "Programmierung", "pages": (21, 27)},
            {"id": "trends", "code": "6.5", "title": "Trends und Entwicklungen", "pages": (29, 33)},
        ],
    },
    {
        "id": "grundlagen",
        "file": "ft7",
        "title": "Grundlagen der Fertigungsprozesse",
        "kicker": "Modul 7",
        "verb": "",
        "source": "FT-7 Grundlagen der Fertigungsprozesse",
        "needle": "größtmögliche Wirtschaftlichkeit",
        "sections": [
            {
                "id": "auswahl",
                "code": "7.1",
                "title": "Auswahl und Vergleich der Fertigungsarten",
                "pages": (4, 8),
            },
            {"id": "av", "code": "7.2", "title": "Arbeitsvorbereitung", "pages": (10, 15)},
            {
                "id": "varianten",
                "code": "",
                "title": "Vergleich technologischer Varianten",
                "pages": (16, 19),
            },
            {
                "id": "trends",
                "code": "7.3",
                "title": "Entwicklungstendenzen / Trends",
                "pages": (21, 22),
            },
        ],
    },
]


def normalize(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[\uf0b7\uf0a7\uf076\uf0d8\u2022\u25aa\u25cf\u2043\u25a0]", "\n• ", text)
    return text


def is_garbage(text: str) -> bool:
    priv = sum(1 for ch in text if 0xE000 <= ord(ch) <= 0xF8FF)
    if priv >= 2:
        return True
    letters = sum(ch.isalpha() for ch in text)
    if len(text) > 24 and letters / max(len(text), 1) < 0.28 and priv:
        return True
    return False


def is_toc(text: str) -> bool:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if any(re.fullmatch(r"Inhalt(\s+\S+)?", ln) for ln in lines):
        return True
    outline = []
    other_len = 0
    for ln in lines:
        if re.match(r"^\d+(\.\d+)?\s+\S", ln) and any(k in ln for k in OUTLINE_KEYS):
            outline.append(ln)
        else:
            other_len += len(ln)
    return len(outline) >= 4 and other_len < 90


def content_blocks(page) -> list[dict]:
    items = []
    for block in page.get_text("blocks"):
        x0, y0, x1, y1, text, *_ = block
        if y0 < 78 or y0 > 512:
            continue
        text = normalize(text).strip()
        if not text:
            continue
        if "HOCHSCHULETRIER" in text or "University of Applied Sciences" in text:
            continue
        if text.startswith("Prof. Dr"):
            continue
        items.append(
            {
                "x": round(x0, 1),
                "y": round(y0, 1),
                "w": round(x1 - x0, 1),
                "text": text,
            }
        )
    items.sort(key=lambda b: (b["y"], b["x"]))
    return items


def parse_block(text: str) -> list[dict]:
    if is_garbage(text):
        return []
    lines = []
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln:
            continue
        ln = re.sub(r"^[-–—]\s+", "• ", ln)
        if "•" in ln:
            parts = ln.split("•")
            head = parts[0].strip()
            if head:
                lines.append(head)
            for part in parts[1:]:
                part = part.strip()
                if part:
                    lines.append("• " + part)
                else:
                    lines.append("•")
        else:
            lines.append(ln)

    stitched = []
    index = 0
    while index < len(lines):
        if lines[index].strip() == "•":
            if index + 1 < len(lines) and lines[index + 1].strip() != "•":
                stitched.append("• " + lines[index + 1].strip())
                index += 2
                continue
            index += 1
            continue
        stitched.append(lines[index])
        index += 1
    lines = stitched

    elements: list[dict] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("•"):
            items = []
            while i < len(lines) and lines[i].startswith("•"):
                item = re.sub(r"\s+", " ", lines[i].lstrip("•").strip(" –-"))
                i += 1
                while (
                    item
                    and i < len(lines)
                    and not lines[i].startswith("•")
                    and not re.match(r"^\d+[\.)]\s+", lines[i])
                    and not lines[i].lower().startswith("quelle")
                    and not (
                        lines[i].endswith(":")
                        and len(lines[i]) <= 72
                        and lines[i].count(" ") <= 8
                        and "." not in lines[i][:-1]
                    )
                    and not item.endswith((".", "!", "?", ":"))
                ):
                    item = re.sub(r"\s+", " ", f"{item} {lines[i]}")
                    i += 1
                if item and not is_garbage(item):
                    items.append(item)
            if items:
                elements.append({"t": "ul", "items": items})
            continue
        numbered = re.match(r"^(\d+)[\.)]\s+(.+)", ln)
        if numbered and len(numbered.group(2)) > 1:
            items = []
            while i < len(lines):
                match = re.match(r"^(\d+)[\.)]\s+(.+)", lines[i])
                if not match:
                    break
                item = re.sub(r"\s+", " ", match.group(2).strip())
                if item and not is_garbage(item):
                    items.append(item)
                i += 1
            if items:
                elements.append({"t": "ol", "items": items})
            continue
        if ln.lower().startswith("quelle"):
            elements.append({"t": "source", "text": re.sub(r"\s+", " ", ln)})
            i += 1
            continue
        if ln.endswith(":") and len(ln) <= 72 and ln.count(" ") <= 8 and "." not in ln[:-1]:
            elements.append({"t": "label", "text": re.sub(r"\s+", " ", ln)})
            i += 1
            continue
        buf = [ln]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if (
                nxt.startswith("•")
                or re.match(r"^\d+[\.)]\s+", nxt)
                or nxt.lower().startswith("quelle")
                or (
                    nxt.endswith(":")
                    and len(nxt) <= 72
                    and nxt.count(" ") <= 8
                    and "." not in nxt[:-1]
                )
            ):
                break
            buf.append(nxt)
            i += 1
        paragraph = re.sub(r"\s+", " ", " ".join(buf)).strip()
        if paragraph and not is_garbage(paragraph):
            elements.append({"t": "p", "text": paragraph})
    return elements


def choose_title(blocks: list[dict]) -> tuple[str, list[dict]]:
    if not blocks:
        return "Folie", []
    first = re.sub(r"\s+", " ", blocks[0]["text"]).strip()
    if len(first) <= 170 and not first.endswith("."):
        title = first
        rest = blocks[1:]
    else:
        title = ""
        rest = blocks
        for index, block in enumerate(blocks[1:], start=1):
            flat = re.sub(r"\s+", " ", block["text"]).strip()
            if 10 <= len(flat) <= 150 and "." not in flat[:-1]:
                title = flat
                rest = blocks[:index] + blocks[index + 1 :]
                break
        if not title:
            title = first[:140].rsplit(" ", 1)[0] if len(first) > 140 else first
            rest = blocks
    if rest:
        last = re.sub(r"\s+", " ", rest[-1]["text"]).strip()
        if last == title or (len(last) < 180 and last == title):
            rest = rest[:-1]
    title = re.sub(r"\s+", " ", title).strip(" -–")
    words = title.split()
    if len(words) >= 4 and len(words) % 2 == 0:
        half = len(words) // 2
        if words[:half] == words[half:]:
            title = " ".join(words[:half])
    return title or "Folie", rest


def build_elements(blocks: list[dict]) -> list[dict]:
    bands: list[list[dict]] = []
    for block in blocks:
        if (
            bands
            and abs(block["y"] - bands[-1][0]["y"]) < 16
            and block["w"] < 460
            and bands[-1][0]["w"] < 460
        ):
            bands[-1].append(block)
        else:
            bands.append([block])
    elements: list[dict] = []
    for band in bands:
        band.sort(key=lambda b: b["x"])
        parsed = [parse_block(b["text"]) for b in band]
        parsed = [p for p in parsed if p]
        if not parsed:
            continue
        if len(parsed) >= 2:
            elements.append({"t": "cols", "cols": parsed})
        else:
            elements.extend(parsed[0])
    return elements


def flatten(elements: list[dict]) -> list[str]:
    out: list[str] = []
    for el in elements:
        if el["t"] in ("p", "label", "source"):
            out.append(el["text"])
        elif el["t"] in ("ul", "ol"):
            out.extend(el["items"])
        elif el["t"] == "cols":
            for col in el["cols"]:
                out.extend(flatten(col))
    return out


QUESTION = re.compile(
    r"(Nennen Sie|Geben Sie|Beschreiben Sie|Definieren und|Zeichnen Sie|Wiederholen Sie|Erläutern Sie|\?\?\?)",
    re.IGNORECASE,
)


def merge_wrapped_blocks(blocks: list[dict]) -> list[dict]:
    if not blocks:
        return blocks
    merged = [dict(blocks[0])]
    for block in blocks[1:]:
        prev = merged[-1]
        prev_flat = re.sub(r"\s+", " ", prev["text"]).strip()
        gap = block["y"] - prev["y"]
        same_column = abs(block["x"] - prev["x"]) < 48
        still_open = not prev_flat.endswith((".", "!", "?", ":", "“", "\"", ";"))
        if same_column and 0 <= gap < 34 and still_open:
            prev["text"] = prev_flat + " " + re.sub(r"\s+", " ", block["text"]).strip()
            prev["w"] = max(prev["w"], block["w"])
            prev["y"] = min(prev["y"], block["y"])
        else:
            merged.append(dict(block))
    return merged


def merge_lists(elements: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for el in elements:
        if el["t"] in ("ul", "ol") and merged and merged[-1]["t"] == el["t"]:
            merged[-1]["items"].extend(el["items"])
        else:
            merged.append(el)
    return merged


def prune_shards(elements: list[dict]) -> list[dict]:
    kept = []
    for el in elements:
        if el["t"] == "cols" and flatten([el]) and max(len(t) for t in flatten([el])) < 48:
            continue
        kept.append(el)
    kept = merge_lists(kept)
    frags = flatten(kept)
    longest = max((len(part) for part in frags), default=0)
    has_list = any(el["t"] in ("ul", "ol") and len(el.get("items", [])) >= 2 for el in kept)
    if not has_list and longest < 55 and len(frags) >= 8:
        return []
    return kept


def classify(elements: list[str], blob: str) -> str:
    readable = sum(len(part) for part in elements)
    if readable >= 60:
        kind = "prose"
    else:
        kind = "figure"
    if QUESTION.search(blob) and len(blob) < 560:
        kind = "question"
    if not elements:
        kind = "figure"
    return kind


def slide_from(page, file_key: str, number: int) -> dict | None:
    blocks = content_blocks(page)
    if not blocks:
        return {
            "file": file_key,
            "n": number,
            "title": "Folie",
            "kind": "figure",
            "blocks": [],
            "plain": "",
        }
    raw = "\n".join(b["text"] for b in blocks)
    if is_toc(raw):
        return None
    blocks = merge_wrapped_blocks(blocks)
    title, body = choose_title(blocks)
    elements = prune_shards(build_elements(body))
    texts = flatten(elements)
    kind = classify(texts, raw)
    plain = re.sub(r"\s+", " ", (title + " " + " ".join(texts))).strip()
    return {
        "file": file_key,
        "n": number,
        "title": title,
        "kind": kind,
        "blocks": elements,
        "plain": plain[:1800],
    }


def definition_text(slides: list[dict], needle: str) -> str:
    for slide in slides:
        parts = flatten(slide["blocks"])
        if needle in slide["title"] and slide["title"].endswith(":"):
            pass
        blob_items = parts
        # Prefer the paragraph that contains the needle, plus an immediate list.
        if needle in slide["title"]:
            extra = ""
            if slide["blocks"] and slide["blocks"][0]["t"] == "ul":
                extra = " · " + " · ".join(slide["blocks"][0]["items"])
            return (slide["title"] + extra).strip()
        for index, el in enumerate(slide["blocks"]):
            if el["t"] in ("p", "label") and needle in el["text"]:
                extra = ""
                nxt = slide["blocks"][index + 1] if index + 1 < len(slide["blocks"]) else None
                if nxt and nxt["t"] == "ul":
                    extra = " " + " · ".join(nxt["items"])
                elif nxt and nxt["t"] == "p" and el["text"].rstrip().endswith(":"):
                    extra = " " + nxt["text"]
                return (el["text"] + extra).strip()
            if el["t"] == "ul" and any(needle in item for item in el["items"]):
                return " · ".join(el["items"])
            if el["t"] == "cols":
                for col in el["cols"]:
                    for inner in col:
                        if inner["t"] == "p" and needle in inner["text"]:
                            return inner["text"]
        if needle in slide["plain"]:
            for part in blob_items:
                if needle in part:
                    return part
    return ""


def assigned_map() -> dict[str, set[int]]:
    found: dict[str, set[int]] = {key: set() for key in FILES}
    for module in MODULES:
        for section in module["sections"]:
            for number in pages_of(section["pages"]):
                found[module["file"]].add(number)
    return found


def main() -> int:
    docs = {key: pymupdf.open(path) for key, path in FILES.items()}
    report: list[str] = []
    used: dict[str, set[int]] = {key: set() for key in FILES}
    modules_out = []

    for module in MODULES:
        doc = docs[module["file"]]
        sections_out = []
        all_slides: list[dict] = []
        for section in module["sections"]:
            slides = []
            for number in pages_of(section["pages"]):
                used[module["file"]].add(number)
                page = doc[number - 1]
                slide = slide_from(page, module["file"], number)
                if slide is None:
                    report.append(f"toc  {module['file']} p.{number} in {section['id']}")
                    continue
                slides.append(slide)
                all_slides.append(slide)
            sections_out.append(
                {
                    "id": section["id"],
                    "code": section["code"],
                    "title": section["title"],
                    "slides": slides,
                }
            )
        modules_out.append(
            {
                "id": module["id"],
                "title": module["title"],
                "kicker": module["kicker"],
                "verb": module["verb"],
                "source": module["source"],
                "definition": definition_text(all_slides, module["needle"]),
                "sections": sections_out,
            }
        )
        if not modules_out[-1]["definition"]:
            report.append(f"MISSING definition {module['id']} needle={module['needle']}")

    missing = []
    for key, doc in docs.items():
        assigned = assigned_map()[key]
        for number in range(1, doc.page_count + 1):
            if number in assigned or number == 1:
                continue
            page = doc[number - 1]
            blocks = content_blocks(page)
            raw = "\n".join(b["text"] for b in blocks)
            if not raw.strip() or is_toc(raw):
                report.append(f"skip {key} p.{number} ({'leer' if not raw.strip() else 'inhalt'})")
                continue
            missing.append(f"{key} p.{number}: {re.sub(r'\\s+', ' ', raw)[:120]}")

    course = {
        "title": "Fertigungstechnik I",
        "professor": "Prof. Dr.-Ing. Armin Wittmann",
        "place": "Hochschule Trier",
        "school": "Hochschule für Technik, Wirtschaft und Gestaltung",
        "term": "Sommersemester 2015",
        "program": "Bachelor-Studiengang Maschinenwesen / Fahrzeugtechnik / Wirtschaftsingenieurwesen",
        "module": "Fertigungstechnik I (FT I)",
        "chair": "Produktionstechnik, Betriebsorganisation und Supply Chain Management",
        "din": [
            {"name": "Urformen", "verb": "Zusammenhalt schaffen", "mod": "urformen"},
            {"name": "Umformen", "verb": "Zusammenhalt beibehalten", "mod": "umformen"},
            {"name": "Trennen", "verb": "Zusammenhalt vermindern", "mod": "trennen"},
            {"name": "Fügen", "verb": "Zusammenhalt vermehren", "mod": None},
            {"name": "Beschichten", "verb": "Zusammenhalt vermehren", "mod": "beschichten"},
            {"name": "Stoffeigenschaft ändern", "verb": "", "mod": None},
        ],
        "lernziele": [
            "Ziel ist den Studierenden im Grundstudium ein Basiswissen über Teilefertigung zu vermitteln",
            "Sie lernen die Theorie der Fertigungsverfahren und die Fertigungsprozessgestaltung kennen",
            "Sie kennen die Grundlagen der Verfahrenshauptklassen Urformen, Umformen, Trennen, Fügen, Beschichten",
            "Grundsätze der Fertigungsprozessgestaltung",
        ],
        "begriff": [
            "Fertigungsverfahren",
            "Fertigungsmittel",
            "Fertigungseinrichtungen",
            "Fertigungsstoffe",
        ],
        "ziele": [
            "größtmögliche Wirtschaftlichkeit (minimaler Aufwand, maximaler Nutzen)",
            "Betrachtung des kompletten Fertigungsprozesses",
        ],
        "subziele": [
            "Senkung der Herstellungskosten (z.B. Material-, Maschinen- oder Lohnkosten)",
            "Optimale Maschinenbelegung (geringe Leerzeiten)",
            "Kurze Durchlaufzeiten",
            "Niedrige Lagerkosten / Kapitalbindung",
            "Steigerung der Flexibilität",
            "Qualitätssicherung",
            "Termintreue",
            "Humane Arbeitsbedingungen",
            "Umweltverträglichkeit",
        ],
        "auswahl": [
            {
                "title": "Produkt",
                "items": [
                    "Geometrie",
                    "Erforderliche Qualität (Oberflächengüten, Maßtoleranzen, Randzonen, Belastung, etc.)",
                    "Stückzahl",
                    "Werkstoff",
                ],
            },
            {
                "title": "Verfahren",
                "items": [
                    "Werkstoffverbrauch",
                    "Energiebedarf",
                    "Flexibilität",
                    "Automatisierung",
                ],
            },
            {
                "title": "Wirtschaftlichkeit",
                "items": [
                    "Investitionsaufwand",
                    "Kapitalkosten",
                    "Amortisationszeit",
                    "Wirtschaftliches Risiko",
                    "Vorhandenes Personal und Maschinenausstattung der Fertigung, Prüfung, etc.",
                ],
            },
            {
                "title": "Umwelttechnische und soziale Kriterien",
                "items": ["Arbeitssicherheit", "Arbeitsgestaltung", "Umweltschutz"],
            },
        ],
        "arten": {
            "columns": ["Einzelfertigung", "Serienfertigung", "Mengenfertigung"],
            "rows": [
                ["Stückzahl", "klein", "in Losen", "hoch"],
                ["Produktivität", "gering", "mittel", "hoch"],
                ["Flexibilität", "hoch", "mittel", "gering"],
                ["Automatisierung", "gering", "mittel", "hoch"],
                ["Spezialisierung der Maschinen", "Universalmaschine", "mittel", "Spezialmaschine"],
                ["Vorbereitungsaufwand", "gering", "mittel", "hoch"],
                ["Rohteilherstellung", "Spanen", "Urformen oder Umformen", "Urformen oder Umformen"],
                ["Abfall, Späne", "hoch", "mittel", "gering"],
                ["Kapitalbedarf", "gering", "mittel", "hoch"],
                ["Stückkosten", "hoch", "mittel", "gering"],
            ],
        },
        "gallery": [
            {"file": "ft1", "n": 12},
            {"file": "ft1", "n": 9},
            {"file": "ft1", "n": 13},
            {"file": "ft1", "n": 14},
            {"file": "ft7", "n": 7},
            {"file": "ft7", "n": 8},
        ],
        "modules": modules_out,
    }

    # Point gallery items at the reader once slides exist.
    index = {}
    for module in modules_out:
        for section in module["sections"]:
            for i, slide in enumerate(section["slides"]):
                index[(slide["file"], slide["n"])] = (module["id"], section["id"], i, slide["title"])
    for item in course["gallery"]:
        hit = index.get((item["file"], item["n"]))
        if not hit:
            missing.append(f"gallery {item['file']} p.{item['n']}")
            continue
        item["mod"], item["sec"], item["i"], item["title"] = hit

    payload = json.dumps(course, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    (ROOT / "course.js").write_text("window.COURSE=" + payload + ";\n", encoding="utf-8")
    (ROOT / "build-report.txt").write_text("\n".join(report + ["", "UNASSIGNED", *missing]), encoding="utf-8")

    total = sum(len(s["slides"]) for m in modules_out for s in m["sections"])
    print("slides", total)
    print("missing", len(missing))
    for line in missing:
        print(" !!", line)
    for module in modules_out:
        n = sum(len(s["slides"]) for s in module["sections"])
        defin = module["definition"][:90].replace("\n", " ")
        print(f"{module['id']:12} {n:4}  {defin}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
