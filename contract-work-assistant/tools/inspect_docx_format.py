#!/usr/bin/env python3
"""Read-only DOCX OOXML inspector for paragraph/run formatting provenance.

Uses only Python's standard library. It does not modify the source file and
does not claim to reproduce Word's complete layout/rendering engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def q(local: str) -> str:
    return f"{{{W}}}{local}"


def text_of(node: ET.Element) -> str:
    return "".join(t.text or "" for t in node.findall(".//w:t", NS))


def get_val(node: ET.Element | None) -> str | None:
    if node is None:
        return None
    return node.get(q("val"), "true")


def run_props(rpr: ET.Element | None) -> dict:
    if rpr is None:
        return {"present": False}
    out: dict = {"present": True}
    fonts = rpr.find("w:rFonts", NS)
    if fonts is not None:
        out["rFonts"] = {k.rsplit("}", 1)[-1]: v for k, v in fonts.attrib.items()}
    for tag in ("sz", "szCs", "b", "bCs", "i", "color", "highlight", "rStyle", "vertAlign"):
        el = rpr.find(f"w:{tag}", NS)
        if el is None:
            continue
        value = get_val(el)
        if tag in ("sz", "szCs") and value and value.isdigit():
            out[tag + "_half_points"] = int(value)
            out[tag + "_points"] = int(value) / 2
        else:
            out[tag] = value
    return out


def style_record(styles: ET.Element, style_id: str | None) -> dict | None:
    if style_id is None:
        style = styles.find("w:style[@w:type='paragraph'][@w:default='1']", NS)
        if style is None:
            style = styles.find("w:style[@w:styleId='Normal']", NS)
    else:
        style = styles.find(f"w:style[@w:styleId='{style_id}']", NS)
    if style is None:
        return None
    name = style.find("w:name", NS)
    based = style.find("w:basedOn", NS)
    ppr = style.find("w:pPr", NS)
    jc = ppr.find("w:jc", NS) if ppr is not None else None
    rpr = style.find("w:rPr", NS)
    return {
        "styleId": style.get(q("styleId")),
        "name": name.get(q("val")) if name is not None else None,
        "basedOn": based.get(q("val")) if based is not None else None,
        "paragraph_alignment": get_val(jc),
        "run_properties": run_props(rpr),
    }


def style_chain(styles: ET.Element, style_id: str | None) -> list[dict]:
    chain = []
    seen = set()
    current = style_id
    while True:
        item = style_record(styles, current)
        if item is None or item["styleId"] in seen:
            break
        seen.add(item["styleId"])
        chain.append(item)
        current = item["basedOn"]
        if current is None:
            break
    return chain


def inspect(path: Path, needles: list[str]) -> dict:
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as zf:
        bad_member = zf.testzip()
        document = ET.fromstring(zf.read("word/document.xml"))
        styles = ET.fromstring(zf.read("word/styles.xml"))
    defaults = styles.find("w:docDefaults/w:rPrDefault/w:rPr", NS)
    paragraphs = []
    for idx, p in enumerate(document.findall(".//w:body/w:p", NS), 1):
        ptext = text_of(p)
        if not any(needle in ptext for needle in needles):
            continue
        ppr = p.find("w:pPr", NS)
        pstyle = ppr.find("w:pStyle", NS) if ppr is not None else None
        style_id = pstyle.get(q("val")) if pstyle is not None else None
        jc = ppr.find("w:jc", NS) if ppr is not None else None
        paragraph_mark_rpr = ppr.find("w:rPr", NS) if ppr is not None else None
        runs = []
        for run_idx, run in enumerate(p.findall("w:r", NS), 1):
            rpr = run.find("w:rPr", NS)
            direct = run_props(rpr)
            char_style_id = direct.get("rStyle")
            runs.append({
                "run_index": run_idx,
                "text": text_of(run),
                "direct_run_properties": direct,
                "character_style_chain": style_chain(styles, char_style_id) if char_style_id else [],
                "raw_rPr_xml": ET.tostring(rpr, encoding="unicode") if rpr is not None else None,
            })
        paragraphs.append({
            "paragraph_index_1_based": idx,
            "text": ptext,
            "pStyle_direct_reference": style_id,
            "paragraph_style_chain": style_chain(styles, style_id),
            "paragraph_direct_alignment": get_val(jc),
            "paragraph_mark_run_properties": run_props(paragraph_mark_rpr),
            "runs": runs,
        })
    return {
        "source_file": str(path.resolve()),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "zip_integrity_error_member": bad_member,
        "docDefaults_run_properties": run_props(defaults),
        "default_paragraph_style_definition": style_record(styles, None),
        "matches": paragraphs,
        "limitations": [
            "Reports stored OOXML properties and style definitions; it does not reproduce Word's complete cascade or visual renderer.",
            "Theme font names may require theme.xml resolution; final visual appearance should be confirmed by rendering in Word when material.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, help="source DOCX; read-only")
    parser.add_argument("--match", action="append", required=True,
                        help="paragraph text or unique substring; repeat for multiple paragraphs")
    args = parser.parse_args()
    if not args.docx.is_file():
        print(json.dumps({"error": "file_not_found", "path": str(args.docx)}, ensure_ascii=False))
        return 2
    try:
        result = inspect(args.docx, args.match)
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
        return 2
    if not result["matches"]:
        result["warning"] = "No paragraph matched the supplied text. Do not infer formatting for a missing match."
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["matches"] else 1


if __name__ == "__main__":
    sys.exit(main())
