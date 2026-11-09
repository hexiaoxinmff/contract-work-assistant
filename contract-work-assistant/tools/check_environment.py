#!/usr/bin/env python3
"""Read-only environment preflight for the contract-work-assistant skill."""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MIN_PYTHON = (3, 10)
REQUIRED_TOOLS = (
    "check_environment.py",
    "inspect_docx_format.py",
    "fill_docx.py",
    "compare_docx.py",
)
REQUIRED_MODULES = ("argparse", "hashlib", "json", "xml.etree.ElementTree", "zipfile")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docx", type=Path, help="optional DOCX to check for accessible, valid ZIP/XML package")
    parser.add_argument(
        "--output-dir", type=Path,
        help="optional existing output directory; performs a temporary write probe and removes it immediately",
    )
    args = parser.parse_args()

    tool_dir = Path(__file__).resolve().parent
    modules = {}
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
            modules[name] = True
        except Exception as exc:  # report exact environment failure
            modules[name] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    files = {name: (tool_dir / name).is_file() for name in REQUIRED_TOOLS}
    py_ok = sys.version_info[:2] >= MIN_PYTHON
    modules_ok = all(value is True for value in modules.values())
    files_ok = all(files.values())

    docx_result = None
    if args.docx is not None:
        path = args.docx.expanduser().resolve()
        docx_result = {"path": str(path), "exists": path.is_file(), "readable": False, "zip_valid": False}
        if path.is_file():
            try:
                with zipfile.ZipFile(path, "r") as archive:
                    docx_result["zip_valid"] = archive.testzip() is None
                    docx_result["has_document_xml"] = "word/document.xml" in archive.namelist()
                    archive.read("word/document.xml")
                docx_result["readable"] = bool(docx_result["zip_valid"] and docx_result["has_document_xml"])
            except Exception as exc:
                docx_result["error"] = f"{type(exc).__name__}: {exc}"

    output_probe = None
    if args.output_dir is not None:
        target = args.output_dir.expanduser().resolve()
        output_probe = {"path": str(target), "exists": target.is_dir(), "writable": False}
        if target.is_dir():
            probe_path = None
            try:
                with tempfile.NamedTemporaryFile(prefix=".contract-assistant-check-", dir=target, delete=False) as probe:
                    probe.write(b"temporary permission check")
                    probe_path = Path(probe.name)
                output_probe["writable"] = True
            except Exception as exc:
                output_probe["error"] = f"{type(exc).__name__}: {exc}"
            finally:
                if probe_path is not None:
                    try:
                        probe_path.unlink()
                        output_probe["probe_removed"] = True
                    except Exception as exc:
                        output_probe["probe_removed"] = False
                        output_probe["cleanup_error"] = f"{type(exc).__name__}: {exc}"

    result = {
        "python": {"version": sys.version.split()[0], "minimum_required": "3.10", "supported": py_ok},
        "standard_library_modules": modules,
        "tool_files": files,
        "skill_tools_directory": str(tool_dir),
        "docx_check": docx_result,
        "output_directory_probe": output_probe,
        "setup_required": not (py_ok and modules_ok and files_ok),
        "notes": [
            "No third-party Python packages are required.",
            "This check does not grant permissions, install Python, or change agent-platform settings.",
            "The output-directory probe, when requested, creates and removes a temporary file.",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if py_ok and modules_ok and files_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
