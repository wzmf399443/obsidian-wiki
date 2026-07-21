#!/usr/bin/env python3
"""Manual ingest delta: sha256 compare of sources dir vs vault .manifest.json.

Why this exists: the CLI's cache-check/batch-plan falsely report everything
modified (see .rules/operations.md). This is the trusted fallback, run ≥3 times
(2026-07-06/07/08) and promoted to a script per the repeat-3-times rule.

Usage: python3 scripts/manual_delta.py [vault_path] [sources_dir]
Output: JSON summary {unchanged, modified, new, renamed_hash_match, ...}.

Handles the real manifest layout (verified 2026-07-08):
- top-level {version, last_updated, sources, projects, stats}
- sources is an OBJECT keyed by absolute path, plus virtual keys
  (conversation:<slug>, inline:<slug>:<date>) that are not file paths
- entries may carry source_removed: true (deleted sources, annotated
  2026-07-08) — excluded from the missing count
"""
import hashlib, json, os, sys

VAULT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/<workspace>/<vault-repo>/<vault>")
SRC = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/<workspace>/wiki-source")
EXCLUDE_DIRS = {".git", ".claude", ".serena", ".playwright-mcp", "attachments"}
EXTS = {".md", ".txt"}

manifest = json.load(open(os.path.join(VAULT, ".manifest.json")))
sources = manifest["sources"]
assert isinstance(sources, dict), "unexpected manifest sources layout"

def norm(p):
    # manifest keys use machine-independent ~ form since 2026-07-16
    return os.path.normpath(os.path.abspath(os.path.expanduser(p)))

by_path, by_hash = {}, {}
virtual_keys, removed = [], []
for k, v in sources.items():
    if not (k.startswith("/") or k.startswith("~")):
        virtual_keys.append(k)
        continue
    if v.get("source_removed"):
        removed.append(k)
        continue
    by_path[norm(k)] = v
    h = (v.get("content_hash") or "").removeprefix("sha256:")
    if h:
        by_hash.setdefault(h, []).append(k)

new, modified, unchanged, renamed = [], [], [], []
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for f in files:
        if os.path.splitext(f)[1].lower() not in EXTS:
            continue
        fp = os.path.join(root, f)
        if norm(fp) == norm(os.path.join(SRC, "INDEX.md")):
            continue  # root-level INDEX.md excluded per operations.md
        h = hashlib.sha256(open(fp, "rb").read()).hexdigest()
        hit = by_path.get(norm(fp))
        if hit:
            mh = (hit.get("content_hash") or "").removeprefix("sha256:")
            (unchanged if mh == h else modified).append(fp)
        elif h in by_hash:
            renamed.append({"path": fp, "old_keys": by_hash[h]})
        else:
            new.append(fp)

missing = [k for k in by_path if not os.path.exists(k)]

print(json.dumps({
    "scanned": len(new) + len(modified) + len(unchanged) + len(renamed),
    "manifest_entries": len(sources),
    "unchanged": len(unchanged),
    "modified": sorted(modified),
    "new": sorted(new),
    "renamed_hash_match": renamed,
    "missing_unannotated": sorted(missing),
    "annotated_removed": len(removed),
    "virtual_keys": len(virtual_keys),
}, ensure_ascii=False, indent=1))
