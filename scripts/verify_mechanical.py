#!/usr/bin/env python3
"""Mechanical closeout verifier for ingest / lint-fix runs.

Rebuilt 2026-08-31 and promoted into scripts/ — the 2026-08-27 original lived
in a session scratchpad and was lost with /tmp (lessons.md 2026-08-27).

Checks (each reports its own DENOMINATOR — a denominator below the page count
means pages were silently excluded, which is itself the finding):

  C0  frontmatter YAML parse   HARD ERROR, reported first and separately.
                               A page whose YAML fails vanishes from the
                               denominators of C1/C2/C4/C6/C7 at once.
  C1  six required frontmatter fields (title/category/tags/sources/created/updated)
  C2  summary present and len() <= 200 characters
  C3  no ^[extracted] marker in any form (plain or colon-annotated)
  C4  provenance block: three keys, sums ~1.0, and drift vs recomputed
      marker density (same split_claims semantics as lint check-7)
  C5  wikilinks resolve to real pages (fenced blocks + inline code spans
      stripped first: bash `[[ ]]` and $(...) are not wikilinks)
  C6  sources are machine-independent ~ form (no /Users/... absolute paths)
  C7  tags <= 5, excluding visibility/ system tags
  C8  orphan check: every page named with --new must have >=1 incoming link
      from a content page (index.md entries do not count)
  C9  bookkeeping mtime reconciliation (log.md/index.md/.manifest.json/hot.md)

Usage:
  python3 scripts/verify_mechanical.py <vault> --touched p1.md p2.md ... \
      [--new p3.md ...] [--json out.json]
  python3 scripts/verify_mechanical.py <vault> --today      # pages mtime'd today

Implementation notes that are load-bearing (do not "simplify" these):
  * YAML indented blocks are parsed by LINE ITERATION, never by a regex
    repeat group with \\s* — that pattern silently matches only the first
    line and two independent scripts hit it on the same day (2026-08-27).
  * Scope is the vault CLAUDE.md whitelist. <private-dir>/ and <private-dir>/ are owner
    personal notes and are never read.
"""
import argparse, datetime, json, os, re, sys

CONTENT_DIRS = ["concepts", "entities", "skills", "references",
                "synthesis", "journal", "projects", "misc"]
REQUIRED_FM = ["title", "category", "tags", "sources", "created", "updated"]
SUMMARY_MAX = 200
DRIFT_TOL = 0.20

EXTRACTED_RE = re.compile(r"\^\[extracted(:[^\]]*)?\]")
INFERRED_RE = re.compile(r"\^\[inferred(:[^\]]*)?\]")
AMBIGUOUS_RE = re.compile(r"\^\[ambiguous(:[^\]]*)?\]")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


def iter_pages(vault):
    for d in CONTENT_DIRS:
        root = os.path.join(vault, d)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [x for x in dirnames if x not in {"<company>", "<private-dir>"}]
            for fn in filenames:
                if fn.endswith(".md"):
                    yield os.path.relpath(os.path.join(dirpath, fn), vault)


def split_fm(text):
    """Return (frontmatter_text, body). Empty fm text if no leading ---."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[4:end], text[end + 4:]


def fm_block(fm_text, key):
    """Read an indented YAML block by LINE ITERATION (never regex repeat).

    Returns {subkey: raw_value_string} for `key:` followed by indented lines.
    Handles the block being the LAST field in the frontmatter.
    """
    lines = fm_text.split("\n")
    out, collecting = {}, False
    for line in lines:
        if not collecting:
            if re.match(r"^%s:\s*$" % re.escape(key), line):
                collecting = True
            continue
        if line.strip() == "":
            continue
        if not line.startswith((" ", "\t")):
            break                      # dedent ends the block
        m = re.match(r"^\s+([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
        else:
            break                      # list item or nested block: not ours
    return out


def is_claim_line(line):
    s = line.strip()
    if not s or s.startswith("#") or s.startswith("```") or s.startswith("~~~"):
        return False
    if re.match(r"^\|.*\|$", s) or re.match(r"^[-*_]{3,}$", s):
        return False
    return True


def split_claims(body):
    body2 = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    return [l for l in body2.split("\n") if is_claim_line(l)]


def strip_code(body):
    """Remove fenced blocks and inline code spans before wikilink scanning."""
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    body = re.sub(r"~~~.*?~~~", "", body, flags=re.DOTALL)
    body = re.sub(r"`[^`\n]*`", "", body)
    return body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--touched", nargs="*", default=[])
    ap.add_argument("--new", nargs="*", default=[])
    ap.add_argument("--today", action="store_true")
    ap.add_argument("--json")
    args = ap.parse_args()
    vault = os.path.abspath(os.path.expanduser(args.vault))

    try:
        import yaml
    except ImportError:
        print("PyYAML required: uv run --with pyyaml python3 ...", file=sys.stderr)
        return 2

    all_rel = sorted(iter_pages(vault))
    if args.today:
        today = datetime.date.today()
        touched = [r for r in all_rel
                   if datetime.date.fromtimestamp(
                       os.path.getmtime(os.path.join(vault, r))) == today]
    else:
        touched = [r.replace(vault + "/", "") for r in args.touched]
    new_pages = [r.replace(vault + "/", "") for r in args.new]

    # ---- load every page once (whole vault: needed for the link universe) ----
    pages = {}
    for rel in all_rel:
        with open(os.path.join(vault, rel), encoding="utf-8") as fh:
            text = fh.read()
        fm_text, body = split_fm(text)
        try:
            fm = yaml.safe_load(fm_text) if fm_text.strip() else {}
            yaml_err = None
        except Exception as e:                       # noqa: BLE001
            fm, yaml_err = None, str(e).split("\n")[0]
        pages[rel] = {"text": text, "fm_text": fm_text, "body": body,
                      "fm": fm if isinstance(fm, dict) else None,
                      "yaml_err": yaml_err}

    basenames = {os.path.splitext(os.path.basename(r))[0]: r for r in all_rel}
    incoming = {r: 0 for r in all_rel}
    for rel, p in pages.items():
        for m in WIKILINK_RE.finditer(strip_code(p["body"])):
            tgt = m.group(1).strip().split("/")[-1]
            if tgt in basenames and basenames[tgt] != rel:
                incoming[basenames[tgt]] += 1

    findings = {("C%d" % i): [] for i in range(10)}
    denom = {}

    denom["C0"] = len(touched)
    for rel in touched:
        p = pages.get(rel)
        if p is None:
            findings["C0"].append("%s: FILE NOT FOUND in content dirs" % rel)
            continue
        if p["yaml_err"]:
            findings["C0"].append("%s: YAML parse FAILED — %s" % (rel, p["yaml_err"]))

    parsable = [r for r in touched
                if pages.get(r) and pages[r]["fm"] is not None]
    denom["C1"] = denom["C2"] = denom["C4"] = denom["C6"] = denom["C7"] = len(parsable)
    denom["C3"] = denom["C5"] = len(touched)
    denom["C8"] = len(new_pages)

    for rel in parsable:
        p, fm = pages[rel], pages[rel]["fm"]

        missing = [k for k in REQUIRED_FM if k not in fm or fm[k] in (None, "")]
        if missing:
            findings["C1"].append("%s: missing %s" % (rel, ",".join(missing)))

        s = fm.get("summary")
        if not s:
            findings["C2"].append("%s: no summary" % rel)
        elif len(str(s)) > SUMMARY_MAX:
            findings["C2"].append("%s: summary %d chars (>%d)"
                                  % (rel, len(str(s)), SUMMARY_MAX))

        prov = fm_block(p["fm_text"], "provenance")
        if not prov:
            findings["C4"].append("%s: no provenance block" % rel)
        else:
            try:
                vals = {k: float(v) for k, v in prov.items()}
            except ValueError:
                findings["C4"].append("%s: non-numeric provenance %s" % (rel, prov))
                vals = {}
            if vals:
                if abs(sum(vals.values()) - 1.0) > 0.05:
                    findings["C4"].append("%s: provenance sums %.2f (keys=%s)"
                                          % (rel, sum(vals.values()), ",".join(vals)))
                claims = split_claims(p["body"])
                n = len(claims) or 1
                r_inf = sum(1 for c in claims if INFERRED_RE.search(c)) / n
                r_amb = sum(1 for c in claims if AMBIGUOUS_RE.search(c)) / n
                for key, rec in (("inferred", r_inf), ("ambiguous", r_amb)):
                    dec = vals.get(key)
                    if dec is not None and abs(dec - rec) > DRIFT_TOL:
                        findings["C4"].append(
                            "%s: %s declared %.2f vs recomputed %.2f (drift %.2f, %d claim lines)"
                            % (rel, key, dec, rec, abs(dec - rec), len(claims)))

        srcs = fm.get("sources")
        for src in (srcs if isinstance(srcs, list) else [srcs] if srcs else []):
            if isinstance(src, str) and src.startswith("/Users/"):
                findings["C6"].append("%s: absolute source path %s" % (rel, src))

        tags = fm.get("tags") or []
        real = [t for t in tags if not str(t).startswith("visibility/")]
        if len(real) > 5:
            findings["C7"].append("%s: %d tags (>5): %s" % (rel, len(real), real))

    for rel in touched:
        p = pages.get(rel)
        if not p:
            continue
        for i, line in enumerate(p["text"].split("\n"), 1):
            if EXTRACTED_RE.search(line):
                findings["C3"].append("%s:%d: forbidden ^[extracted]" % (rel, i))
        for m in WIKILINK_RE.finditer(strip_code(p["body"])):
            tgt = m.group(1).strip().split("/")[-1]
            if tgt not in basenames:
                findings["C5"].append("%s: broken wikilink [[%s]]" % (rel, m.group(1).strip()))

    for rel in new_pages:
        if rel not in incoming:
            findings["C8"].append("%s: not found in content dirs" % rel)
        elif incoming[rel] == 0:
            findings["C8"].append("%s: ORPHAN — 0 incoming links" % rel)

    denom["C9"] = 4
    stat = {}
    for f in ("log.md", "index.md", ".manifest.json", "hot.md"):
        fp = os.path.join(vault, f)
        stat[f] = (datetime.datetime.fromtimestamp(os.path.getmtime(fp)).isoformat()
                   if os.path.exists(fp) else "MISSING")
        if stat[f] == "MISSING":
            findings["C9"].append("%s: MISSING" % f)

    labels = {
        "C0": "frontmatter YAML parse (HARD ERROR)",
        "C1": "six required frontmatter fields",
        "C2": "summary present and <=200 chars",
        "C3": "no ^[extracted] marker",
        "C4": "provenance block sane + drift <=0.20",
        "C5": "wikilinks resolve",
        "C6": "sources in ~ form",
        "C7": "tags <=5 (excl. visibility/)",
        "C8": "new pages have >=1 incoming link",
        "C9": "bookkeeping files present",
    }
    print("vault pages in scope: %d | touched: %d | new: %d\n"
          % (len(all_rel), len(touched), len(new_pages)))
    total = 0
    for c in sorted(labels):
        n = len(findings[c])
        total += n
        print("%s %-42s denom=%-4s findings=%d" % (c, labels[c], denom.get(c, "?"), n))
        for line in findings[c]:
            print("      - %s" % line)
    print("\nbookkeeping mtimes: %s" % json.dumps(stat, ensure_ascii=False))
    print("TOTAL FINDINGS: %d" % total)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"denominators": denom, "findings": findings,
                       "bookkeeping_mtimes": stat, "total": total,
                       "touched": touched, "new": new_pages}, fh,
                      ensure_ascii=False, indent=2)
        print("wrote %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
