from __future__ import annotations

from pathlib import Path

from scripts.check_public_tree import scan


def write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def codes(findings: list[dict[str, str]]) -> set[str]:
    return {item["code"] for item in findings}


def test_clean_public_file_passes(tmp_path: Path) -> None:
    public = write(tmp_path, "README.md", "Synthetic public documentation.\n")
    assert scan(tmp_path, [public], []) == []


def test_forbidden_private_path_is_rejected(tmp_path: Path) -> None:
    private = write(tmp_path, "source/private.py", "print('synthetic')\n")
    assert "forbidden_path" in codes(scan(tmp_path, [private], []))


def test_private_execution_ledger_is_rejected(tmp_path: Path) -> None:
    private = write(tmp_path, "_execution/STATUS.md", "Synthetic private ledger.\n")
    assert "forbidden_path" in codes(scan(tmp_path, [private], []))


def test_private_key_canary_is_rejected(tmp_path: Path) -> None:
    marker = "-----BEGIN " + "OPENSSH " + "PRIVATE KEY-----"
    canary = write(tmp_path, "canary.txt", marker + "\nsynthetic-only\n")
    assert "secret_or_private_path" in codes(scan(tmp_path, [canary], []))


def test_non_loopback_ipv4_canary_is_rejected(tmp_path: Path) -> None:
    synthetic_ip = "198.51.100." + "42"
    canary = write(tmp_path, "canary.txt", f"Synthetic endpoint: {synthetic_ip}\n")
    assert "non_loopback_ipv4" in codes(scan(tmp_path, [canary], []))


def test_restricted_exact_copy_is_rejected(tmp_path: Path) -> None:
    restricted = tmp_path / "restricted"
    source = write(
        restricted,
        "module.py",
        "synthetic = 'restricted fixture'\n" + "# synthetic padding only\n" * 8,
    )
    public = write(tmp_path, "src/copied.py", source.read_text(encoding="utf-8"))
    assert "restricted_source_exact_match" in codes(scan(tmp_path, [public], [restricted]))


def test_restricted_long_snippet_is_rejected(tmp_path: Path) -> None:
    lines = [f"synthetic_line_{index} = '{index:04d}-{'x' * 48}'" for index in range(20)]
    restricted = tmp_path / "restricted"
    write(restricted, "large.py", "\n".join(lines) + "\n")
    public = write(tmp_path, "src/fragment.py", "\n".join(lines[:12]) + "\nextra = True\n")
    assert "restricted_source_long_match" in codes(scan(tmp_path, [public], [restricted]))
