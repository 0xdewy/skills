#!/usr/bin/env python3
"""repo_map.py — emit a live, token-budgeted code map of a git repo for an LLM.

Builds the map directly from git-tracked source via tree-sitter — no aider — so it
is read-only w.r.t. both the repo AND the user's home: nothing is cached, fetched,
or phoned home, and it runs unchanged in sandboxed environments. Symbols carry
their definition line numbers so an agent can jump straight to `Read path:line`.

Lazy / progressive disclosure — pay for depth only where you need it:

  Tier 1 OUTLINE   repo_map.py                   whole-repo inventory; central files
                                                 get ranked symbols + line numbers,
                                                 the long tail gets bare paths.
                                                 Size-aware token budget.
  Tier 2 EXPAND    repo_map.py --expand PATH     full signatures + lines for one file
                   repo_map.py --subtree PATH    or directory (no budget cap).
  Tier 3 XREF      repo_map.py --xref NAME       definition + reference sites of one
                                                 symbol as file:line.

  --json           machine-readable summary at any tier.
  --more           2x the outline budget.
  --tokens N       explicit override (0 = unlimited).

Ranking: files are scored by PageRank-style centrality over an import/reference
graph. Python resolves real imports; other languages use discriminating
symbol-name references (generic names defined in many files are skipped to keep
the graph clean).

Exit codes: 0 = map printed; 1 = tree-sitter-language-pack missing;
2 = not a git repo; 3 = no source files / no matches; 4 = other failure.
"""

import argparse
import os
import re
import subprocess
import sys

try:
    from tree_sitter import Parser, Query, QueryCursor
    from tree_sitter_language_pack import get_language
    _HAVE_TS = True
except ImportError:
    _HAVE_TS = False

EXT_TO_LANG = {
    ".py": "python", ".pyi": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".hh": "cpp",
    ".php": "php",
    ".sh": "bash", ".bash": "bash",
}

LANG_QUERY = {
    "python": "(function_definition name: (identifier) @name) @def\n"
              "(class_definition name: (identifier) @name) @def",
    "javascript": "(function_declaration name: (identifier) @name) @def\n"
                  "(class_declaration name: (identifier) @name) @def\n"
                  "(method_definition name: (property_identifier) @name) @def",
    "typescript": "(function_declaration name: (identifier) @name) @def\n"
                  "(class_declaration name: (type_identifier) @name) @def\n"
                  "(method_definition name: (property_identifier) @name) @def\n"
                  "(interface_declaration name: (type_identifier) @name) @def\n"
                  "(type_alias_declaration name: (type_identifier) @name) @def",
    "tsx": "(function_declaration name: (identifier) @name) @def\n"
           "(class_declaration name: (type_identifier) @name) @def\n"
           "(method_definition name: (property_identifier) @name) @def",
    "go": "(function_declaration name: (identifier) @name) @def\n"
          "(method_declaration name: (field_identifier) @name) @def\n"
          "(type_declaration (type_spec name: (type_identifier) @name)) @def",
    "rust": "(function_item name: (identifier) @name) @def\n"
            "(struct_item name: (type_identifier) @name) @def\n"
            "(enum_item name: (type_identifier) @name) @def\n"
            "(trait_item name: (type_identifier) @name) @def",
    "java": "(method_declaration name: (identifier) @name) @def\n"
            "(class_declaration name: (identifier) @name) @def\n"
            "(interface_declaration name: (identifier) @name) @def\n"
            "(constructor_declaration name: (identifier) @name) @def",
    "ruby": "(method name: (identifier) @name) @def\n"
            "(class name: (constant) @name) @def\n"
            "(module name: (constant) @name) @def",
    "c": "(function_definition declarator: (function_declarator declarator: (identifier) @name)) @def",
    "cpp": "(function_definition declarator: (function_declarator declarator: (identifier) @name)) @def\n"
           "(class_specifier name: (type_identifier) @name) @def",
    "php": "(function_definition name: (name) @name) @def\n"
           "(class_declaration name: (name) @name) @def\n"
           "(method_declaration name: (name) @name) @def",
    "bash": "(function_definition name: (word) @name) @def",
}

KIND = {
    "function_definition": "func", "function_declaration": "func", "function_item": "func",
    "method_definition": "func", "method_declaration": "func", "method": "func",
    "constructor_declaration": "ctor",
    "class_definition": "class", "class_declaration": "class", "class_specifier": "class", "class": "class",
    "interface_declaration": "iface", "trait_item": "trait",
    "struct_item": "struct", "enum_item": "enum",
    "type_alias_declaration": "type", "type_declaration": "type",
}

# Names defined in this many or more files are too generic to carry reference
# signal (e.g. `init`, `run`, `parse`) — they only add noise to the graph.
GENERIC_THRESHOLD = 6
MIN_NAME_LEN = 3
_STOPWORDS = {
    "init", "main", "self", "cls", "this", "super", "true", "false", "none", "null",
    "get", "set", "run", "call", "exec", "test", "data", "value", "values", "key",
    "args", "kwargs", "list", "dict", "str", "int", "float", "bool", "print", "length",
    "size", "name", "type", "class", "return", "import", "from", "with", "handle",
}
MAX_FILE_BYTES = 1_000_000
MAX_XREF_REFS = 60

_SYM_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_PY_IMPORT_RE = re.compile(r"^\s*(?:from\s+([.\w]+)\s+import|import\s+([.\w]+))", re.MULTILINE)


class Sym:
    __slots__ = ("name", "kind", "line", "end", "sig")

    def __init__(self, name, kind, line, end, sig):
        self.name = name
        self.kind = kind
        self.line = line
        self.end = end
        self.sig = sig


def die(code, msg):
    print(msg, file=sys.stderr)
    sys.exit(code)


def ntok(s):
    return len(s) // 4


def detect_lang(path):
    ext = os.path.splitext(path)[1].lower()
    lang = EXT_TO_LANG.get(ext)
    return lang if lang and lang in LANG_QUERY else None


def is_git_repo():
    try:
        r = subprocess.run(["git", "rev-parse", "--git-dir"],
                           capture_output=True, text=True)
        return r.returncode == 0
    except FileNotFoundError:
        return False


def tracked_files():
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    if r.returncode != 0:
        return []
    return [p for p in r.stdout.split("\n") if p]


def pagerank(nodes, out_links, alpha=0.85, iters=40):
    """Unweighted PageRank over a file reference graph (power iteration).

    ``out_links[a]`` is the set of files ``a`` references; high-scoring nodes are
    the most depended-upon files (the structural core). Pure, dependency-free.
    """
    n = len(nodes)
    if n == 0:
        return {}
    if n == 1:
        return {nodes[0]: 1.0}
    idx = {p: i for i, p in enumerate(nodes)}
    rank = [1.0 / n] * n
    base = (1.0 - alpha) / n
    for _ in range(iters):
        new = [base] * n
        dangling = 0.0
        for p in nodes:
            i = idx[p]
            tgts = out_links.get(p)
            if not tgts:
                dangling += rank[i]
                continue
            share = alpha * rank[i] / len(tgts)
            for t in tgts:
                new[idx[t]] += share
        if dangling:
            bump = alpha * dangling / n
            new = [x + bump for x in new]
        rank = new
    return {p: rank[idx[p]] for p in nodes}


def _build_parsers():
    """One Parser per language, keyed by language name."""
    parsers = {}
    if not _HAVE_TS:
        return parsers
    for lang in LANG_QUERY:
        try:
            parsers[lang] = Parser(get_language(lang))
        except Exception:
            pass
    return parsers


def extract_symbols(path, parsers):
    """Return (source_text, [Sym, ...]) for a file, or (None, []) if unparsable."""
    try:
        with open(path, "rb") as f:
            raw = f.read(MAX_FILE_BYTES + 1)
    except (OSError, UnicodeError):
        return None, []
    lang = detect_lang(path)
    if lang is None or lang not in parsers:
        return raw, []
    parser = parsers[lang]
    try:
        root = parser.parse(raw).root_node
        q = Query(get_language(lang), LANG_QUERY[lang])
        matches = QueryCursor(q).matches(root)
    except Exception:
        return raw, []
    syms = []
    for _pat, cap in matches:
        defnode = (cap.get("def") or [None])[0]
        namenode = (cap.get("name") or [None])[0]
        if defnode is None:
            continue
        name = ""
        if namenode is not None:
            name = raw[namenode.start_byte:namenode.end_byte].decode("utf-8", "replace")
        kind = KIND.get(defnode.type, defnode.type)
        line = defnode.start_point.row + 1
        end = defnode.end_point.row + 1
        sig = _signature(raw, defnode, kind)
        syms.append(Sym(name, kind, line, end, sig))
    syms.sort(key=lambda s: s.line)
    return raw, syms


def _signature(raw, defnode, kind):
    """First source line of the definition, dedented, cleaned for display."""
    line_start = raw.rfind(b"\n", 0, defnode.start_byte) + 1
    line_end = raw.find(b"\n", defnode.start_byte)
    if line_end == -1:
        line_end = len(raw)
    sig = raw[line_start:line_end].decode("utf-8", "replace").strip()
    return sig.rstrip("{;").rstrip().rstrip(":")


def build_symbol_table(paths, parsers):
    """Return symtab: {path: [Sym]}, linecount: {path: int}, sources: {path: str}."""
    symtab, linecount, sources = {}, {}, {}
    for p in paths:
        raw, syms = extract_symbols(p, parsers)
        if raw is None:
            continue
        symtab[p] = syms
        linecount[p] = raw.count(b"\n") + (0 if raw.endswith(b"\n") or not raw else 1)
        sources[p] = raw.decode("utf-8", "replace")
    return symtab, linecount, sources


def python_module_to_path(mod):
    """Map a dotted python module to candidate repo paths."""
    parts = [seg for seg in mod.replace(".", "/").split("/") if seg and seg != "."]
    if not parts:
        return []
    base = "/".join(parts)
    return [base + ".py", base + "/__init__.py"]


def build_reference_graph(symtab, sources):
    """out_links[a] = set of files `a` references.

    Python files resolve real imports; every file additionally contributes edges
    via discriminating symbol-name mentions (names defined in only a few files),
    which gives cross-language coupling without per-language import parsers.
    """
    name_to_files = {}
    for path, syms in symtab.items():
        for s in syms:
            nm = s.name
            if len(nm) < MIN_NAME_LEN or not nm[0].isalpha() or nm.lower() in _STOPWORDS:
                continue
            name_to_files.setdefault(nm, set()).add(path)
    # Drop generic names defined in many files — they only add noise.
    name_to_files = {nm: fs for nm, fs in name_to_files.items()
                     if len(fs) < GENERIC_THRESHOLD}

    out_links = {p: set() for p in symtab}
    for path, src in sources.items():
        is_py = path.endswith(".py")
        if is_py:
            for m in _PY_IMPORT_RE.finditer(src):
                mod = m.group(1) or m.group(2)
                if mod:
                    for cand in python_module_to_path(mod):
                        if cand in symtab and cand != path:
                            out_links[path].add(cand)
        wordset = set(_SYM_RE.findall(src))
        for w in wordset:
            defs = name_to_files.get(w)
            if defs:
                for d in defs:
                    if d != path:
                        out_links[path].add(d)
    return out_links


def render_outline(symtab, linecount, scores, budget):
    """Whole-repo inventory: central files get ranked symbols + lines, the rest
    get bare paths (with line range so the agent knows size + that symbols exist
    to expand). Concentrates detail where centrality is highest."""
    order = sorted(symtab.keys(), key=lambda p: (-scores.get(p, 0.0), p))
    out, spent = [], 0
    detailed = 0
    for path in order:
        syms = symtab[path]
        lc = linecount.get(path, 0)
        header = "%s:1-%d" % (path, lc) if syms else path
        block = [header]
        for s in syms:
            block.append("  %5d  %s %s" % (s.line, s.kind, s.name))
        cost = ntok("\n".join(block))
        if syms and spent + cost <= budget:
            out.extend(block)
            spent += cost
            detailed += 1
        else:
            out.append(header if syms else path)
            spent += ntok(out[-1])
    return out, detailed


def render_expand(symtab, linecount, paths):
    """Full signatures + line numbers for the matched files, no budget cap."""
    out = []
    for path in sorted(paths):
        syms = symtab.get(path, [])
        lc = linecount.get(path, 0)
        out.append("%s:1-%d" % (path, lc) if syms else path)
        for s in syms:
            out.append("  %5d  %s" % (s.line, s.sig))
    return out


def render_xref(name, symtab, sources):
    """Definition site(s) + reference site lines for one symbol."""
    defs, refs = [], []
    for path, syms in symtab.items():
        for s in syms:
            if s.name == name:
                defs.append("%s:%d" % (path, s.line))
    if not defs:
        return None, None, None
    rx = re.compile(r"\b" + re.escape(name) + r"\b")
    for path, src in sources.items():
        for i, ln in enumerate(src.split("\n"), start=1):
            if rx.search(ln):
                refs.append("%s:%d" % (path, i))
    seen = set(defs)
    clean_refs = [r for r in refs if r not in seen and not seen.add(r)]
    return defs, clean_refs[:MAX_XREF_REFS], len(clean_refs)


def size_aware_budget(total_source_tokens):
    return max(1000, min(4000, round(total_source_tokens * 0.10)))


def is_under(path, target):
    target = target.rstrip("/")
    return path == target or path.startswith(target + "/")


def footer(tier, emitted_files, total_files, budget, total_tokens, extra=""):
    sub = ("  " + extra) if extra else ""
    if tier == "outline":
        if total_tokens and budget >= total_tokens:
            ratio = "full map of %d source tokens" % total_tokens
        else:
            ratio = "budget=%d (~%.0f%% of %d source tokens)" % (
                budget, 100.0 * budget / total_tokens if total_tokens else 0, total_tokens)
        return ("agentify: %s — %d/%d files detailed (%d bare-path), %s%s"
                % (tier, emitted_files, total_files, total_files - emitted_files,
                   ratio, sub))
    return ("agentify: %s — %d files, budget=%s%s"
            % (tier, emitted_files, "uncapped" if budget is None else budget, sub))


def main():
    ap = argparse.ArgumentParser(
        description="Emit a live, token-budgeted code map (tree-sitter, no aider).")
    ap.add_argument("--tokens", type=int, default=None,
                    help="explicit token budget (0 = unlimited). Overrides size-aware default.")
    ap.add_argument("--more", action="store_true",
                    help="2x the outline budget (deeper first pass).")
    ap.add_argument("--expand", default=None, metavar="PATH",
                    help="Tier 2: full signatures + line numbers for a file or directory.")
    ap.add_argument("--subtree", default=None, metavar="PATH",
                    help="Alias for --expand (scoped to a subtree).")
    ap.add_argument("--xref", default=None, metavar="SYMBOL",
                    help="Tier 3: definition + reference sites (file:line) for one symbol.")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON instead of the text map.")
    args = ap.parse_args()

    if not _HAVE_TS:
        die(1, "tree-sitter-language-pack is not installed. Install it:\n"
              "  pip install tree-sitter-language-pack\n"
              "The map is built locally; no API key is required.")

    if not is_git_repo():
        die(2, "not a git repository. The map is built from git-tracked files, so the "
              "target must be inside a git repo. Commit your files first.")

    paths = [p for p in tracked_files() if detect_lang(p) or True]
    source_paths = [p for p in paths if detect_lang(p) is not None]
    if not source_paths:
        die(3, "no supported source files found (git-tracked, parseable languages: "
              + ", ".join(sorted(set(EXT_TO_LANG.values()))) + ").")

    parsers = _build_parsers()
    symtab, linecount, sources = build_symbol_table(source_paths, parsers)
    if not symtab:
        die(3, "no source files could be read.")

    import json as _json

    # ---- Tier 3: XREF -------------------------------------------------------
    if args.xref:
        defs, refs, total_refs = render_xref(args.xref, symtab, sources)
        if defs is None:
            die(3, "no definition found for symbol '%s'. Check the name (it must "
                  "match a function/class/method name in the map)." % args.xref)
        if args.json:
            print(_json.dumps({"symbol": args.xref, "definitions": defs,
                               "references": refs, "total_references": total_refs}))
        else:
            print("def %s" % args.xref)
            for d in defs:
                print("  " + d)
            print("refs (%d shown, %d total):" % (len(refs), total_refs))
            for r in refs:
                print("  " + r)
            sys.stderr.write("agentify: xref — %d definition(s), %d reference(s) "
                             "(%d shown)  symbol=%s\n"
                             % (len(defs), total_refs, len(refs), args.xref))
        return

    # ---- reference graph + ranking -----------------------------------------
    out_links = build_reference_graph(symtab, sources)
    scores = pagerank(list(symtab.keys()), out_links)
    total_tokens = sum(ntok(src) for src in sources.values())

    # ---- Tier 2: EXPAND -----------------------------------------------------
    if args.expand or args.subtree:
        target = args.expand or args.subtree
        matched = [p for p in symtab if is_under(p, target)]
        if not matched:
            die(3, "no tracked source files under '%s'. Use a repo-relative file or "
                  "directory path." % target)
        lines = render_expand(symtab, linecount, matched)
        if args.json:
            payload = {"tier": "expand", "path": target, "files": []}
            for p in matched:
                payload["files"].append({
                    "path": p, "lines": linecount.get(p, 0),
                    "symbols": [{"line": s.line, "end": s.end, "kind": s.kind,
                                 "signature": s.sig} for s in symtab.get(p, [])]})
            print(_json.dumps(payload))
        else:
            sys.stdout.write("\n".join(lines) + "\n")
            sys.stderr.write(footer("expand", len(matched), len(symtab), None,
                                    total_tokens, "path=%s" % target) + "\n")
        return

    # ---- Tier 1: OUTLINE ----------------------------------------------------
    if args.tokens is not None and args.tokens == 0:
        budget = 1_000_000
    elif args.tokens is not None:
        budget = args.tokens
    else:
        budget = size_aware_budget(total_tokens)
        if args.more:
            budget = min(12000, budget * 2)

    lines, detailed = render_outline(symtab, linecount, scores, budget)
    if args.json:
        payload = {"tier": "outline", "token_budget": budget,
                   "source_tokens": total_tokens, "files_total": len(symtab),
                   "files_detailed": detailed,
                   "ranked": [{"path": p, "score": round(scores.get(p, 0.0), 6)}
                              for p in sorted(symtab, key=lambda x: -scores.get(x, 0))]}
        print(_json.dumps(payload))
        return

    sys.stdout.write("\n".join(lines) + "\n")
    sys.stderr.write(footer("outline", detailed, len(symtab), budget, total_tokens) + "\n")


if __name__ == "__main__":
    main()
