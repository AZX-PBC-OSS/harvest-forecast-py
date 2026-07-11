#!/usr/bin/env python3
"""Regenerate _sync/ from _async/ using the unasync package.

Usage:
    python scripts/unasync.py          # write generated files
    python scripts/unasync.py --check  # verify committed files match source
"""

from __future__ import annotations

import argparse
import sys
import tokenize as std_tokenize
from pathlib import Path

# Running this script directly puts scripts/ on sys.path, which shadows the
# installed unasync package. Remove it so ``import unasync`` finds the package.
_here = Path(__file__).resolve().parent
sys.path = [p for p in sys.path if Path(p).resolve() != _here]

import tokenize_rt
import unasync

_ROOT = Path(__file__).resolve().parent.parent

_RULES: list[unasync.Rule] = [
    unasync.Rule(
        "/_async/",
        "/_sync/",
        additional_replacements={
            "AsyncForecastClient": "SyncForecastClient",
            "AsyncClient": "Client",
            "AsyncRetrying": "Retrying",
            "aclose": "close",
            "_async": "_sync",
        },
    ),
]


def _find_rule(filepath: str) -> unasync.Rule | None:
    """Return the first rule that matches *filepath*, or None."""
    for rule in _RULES:
        if rule._match(filepath):
            return rule
    return None


def _transform(rule: unasync.Rule, filepath: str) -> tuple[str, bytes]:
    """Transform a single async source file and return (out_path, content)."""
    with open(filepath, "rb") as f:
        encoding, _ = std_tokenize.detect_encoding(f.readline)
    with open(filepath, encoding=encoding) as f:
        source = f.read()
    tokens = tokenize_rt.src_to_tokens(source)
    tokens = rule._unasync_tokens(tokens)
    result = tokenize_rt.tokens_to_src(tokens)
    result = result.replace("@pytest.mark.asyncio\n", "")
    out_path = filepath.replace(rule.fromdir, rule.todir)
    return out_path, result.encode(encoding)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform async Python source into sync equivalents.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare generated output against existing files; exit 1 on mismatch.",
    )
    args = parser.parse_args()

    files: list[str] = []
    for pattern in ("src/harvest_forecast/_async/**/*.py", "tests/_async/**/*.py"):
        files.extend(str(f) for f in _ROOT.glob(pattern))

    if not files:
        print("No async source files found.", file=sys.stderr)
        sys.exit(1)

    if args.check:
        mismatches = 0
        for filepath in files:
            rule = _find_rule(filepath)
            if rule is None:
                continue
            out_path, content = _transform(rule, filepath)
            existing = Path(out_path)
            if not existing.exists():
                print(f"Missing: {out_path}", file=sys.stderr)
                mismatches += 1
            elif existing.read_bytes() != content:
                print(f"Changed: {out_path}", file=sys.stderr)
                mismatches += 1
        if mismatches:
            print(f"\n{mismatches} file(s) need regeneration.", file=sys.stderr)
            sys.exit(1)
        print("All sync files up to date.")
    else:
        for filepath in files:
            rule = _find_rule(filepath)
            if rule is None:
                continue
            out_path, content = _transform(rule, filepath)
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_bytes(content)
        print(f"Generated {len(files)} sync file(s).")


if __name__ == "__main__":
    main()
