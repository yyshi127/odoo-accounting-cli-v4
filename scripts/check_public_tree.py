#!/usr/bin/env python3
"""Fail closed when a proposed public Git tree contains private material."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

FORBIDDEN_PARTS = {
    ".tooling",
    ".venv",
    "_execution",
    "evidence",
    "node_modules",
    "releases",
    "source",
}
FORBIDDEN_NAMES = {
    "auth.json",
    "current",
    "settings.json",
}
FORBIDDEN_SUFFIXES = {
    ".backup",
    ".db",
    ".dump",
    ".key",
    ".log",
    ".p12",
    ".pem",
    ".pfx",
    ".sql",
    ".sqlite",
    ".sqlite3",
}
TEXT_SUFFIXES = {".csv", ".js", ".md", ".py", ".ts", ".xml"}
MAX_PUBLIC_FILE_BYTES = 2 * 1024 * 1024
EXACT_MATCH_MIN_BYTES = 128
SIMILARITY_WINDOW_LINES = 12
SIMILARITY_MIN_BYTES = 512

SECRET_PATTERNS = (
    re.compile(b"-----BEGIN " + b"(?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(
        rb"(?i)(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"]?"
        rb"[A-Za-z0-9_./+=-]{16,}"
    ),
    re.compile(rb"[a-zA-Z][a-zA-Z0-9+.-]*://[^/\s:@]+:[^/\s@]+@"),
    re.compile(rb"(?:[A-Za-z]:\\Users\\|/(?:root|home)/)[^\s'\"]+"),
    re.compile(rb"/(?:opt|mnt)/odoo(?:/|\b)[^\s'\"]*"),
)
IPV4_PATTERN = re.compile(rb"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tracked_paths(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [root / item.decode("utf-8") for item in completed.stdout.split(b"\0") if item]


def normalized_lines(data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="ignore")
    return [line.strip() for line in text.splitlines() if line.strip()]


def window_hashes(data: bytes) -> set[str]:
    lines = normalized_lines(data)
    result: set[str] = set()
    for index in range(len(lines) - SIMILARITY_WINDOW_LINES + 1):
        block = "\n".join(lines[index : index + SIMILARITY_WINDOW_LINES]).encode()
        if len(block) >= SIMILARITY_MIN_BYTES:
            result.add(sha256(block))
    return result


def scan(root: Path, paths: list[Path], restricted_roots: list[Path]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    public_hashes: dict[str, str] = {}
    public_windows: dict[str, set[str]] = defaultdict(set)

    for path in paths:
        relative = path.relative_to(root).as_posix()
        relative_parts = path.relative_to(root).parts
        parts = set(relative_parts)
        if (
            parts & FORBIDDEN_PARTS
            or relative_parts[:2] == ("generated", "initial")
            or path.name in FORBIDDEN_NAMES
        ):
            findings.append({"code": "forbidden_path", "path": relative})
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            findings.append({"code": "forbidden_extension", "path": relative})
            continue
        if not path.is_file():
            findings.append({"code": "missing_tracked_file", "path": relative})
            continue
        data = path.read_bytes()
        if len(data) > MAX_PUBLIC_FILE_BYTES:
            findings.append({"code": "file_too_large", "path": relative})
        for pattern in SECRET_PATTERNS:
            if pattern.search(data):
                findings.append({"code": "secret_or_private_path", "path": relative})
                break
        for match in IPV4_PATTERN.finditer(data):
            value = match.group(0)
            if not value.startswith((b"127.", b"0.")):
                findings.append({"code": "non_loopback_ipv4", "path": relative})
                break
        if len(data) >= EXACT_MATCH_MIN_BYTES:
            public_hashes[sha256(data)] = relative
        if path.suffix.lower() in TEXT_SUFFIXES:
            for digest in window_hashes(data):
                public_windows[digest].add(relative)

    for root_index, restricted_root in enumerate(restricted_roots, start=1):
        if not restricted_root.is_dir():
            findings.append({"code": "restricted_root_missing", "path": f"root-{root_index}"})
            continue
        for source in restricted_root.rglob("*"):
            if not source.is_file() or ".git" in source.parts or "__pycache__" in source.parts:
                continue
            try:
                data = source.read_bytes()
            except OSError:
                findings.append({"code": "restricted_source_unreadable", "path": f"root-{root_index}"})
                continue
            if len(data) >= EXACT_MATCH_MIN_BYTES and sha256(data) in public_hashes:
                findings.append(
                    {"code": "restricted_source_exact_match", "path": public_hashes[sha256(data)]}
                )
            if source.suffix.lower() in TEXT_SUFFIXES and len(data) <= 4 * 1024 * 1024:
                for digest in window_hashes(data) & public_windows.keys():
                    for relative in public_windows[digest]:
                        findings.append({"code": "restricted_source_long_match", "path": relative})

    return sorted(findings, key=lambda item: (item["path"], item["code"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--restricted-root", type=Path, action="append", default=[])
    args = parser.parse_args()
    root = args.root.resolve()
    findings = scan(root, tracked_paths(root), [item.resolve() for item in args.restricted_root])
    print(json.dumps({"success": not findings, "findings": findings}, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
