#!/usr/bin/env python3
"""Search local knowledge graphs for knowledge:ask and knowledge:ponder. Standard library only.

  kq.py find [--stdin] [QUERY ...]      print matching pages and passages
  kq.py near NODE [NODE ...] --q WORDS  print pages near the answer

A node is <graph>:/<path in the bundle>. Both readers exclude remote graphs.
The private page cache is outside the project. KQ_CACHE selects its folder;
KQ_CACHE=off stops it. No command writes to a graph.
"""
import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
import tempfile
from collections import Counter
from pathlib import Path

STOP = set("""a an and are as at be been but by can could did do does for from had has have he her his how i if in
into is it its of on or she so than that the their them then there these they this those to was were what when where
which who whom whose why will with would you your""".split())
SKIP_FILES = {"index.md", "log.md", "manifest.md"}
LINK = r"\]\(([^)\s#]+\.md)(?:#[^)]*)?\)"
FIND_MAX, FIND_PAGES, FIND_PAGE_CHARS, NEAR_PAGE_CHARS = 24000, 8, 1800, 2500
PPR_DAMP, PPR_STEPS = 0.5, 30
DESC_CHARS = 300
TYPE_WEIGHT = {"OpenQuestion": 1.5, "Source": 0.6}
LOOSE_NODES = False
CACHE_VERSION = "7"
OUT_MAX = 27000
FIELDS = ("node", "type", "title", "description", "status", "aliases", "passages", "out", "head")


def stem(w):
    if len(w) > 3 and not w.isdigit():
        if w.endswith("ies") and not w.endswith(("eies", "aies")):
            return w[:-3] + "y"
        if w.endswith("es") and not w.endswith(("aes", "ees", "oes")):
            return w[:-1]
        if w.endswith("s") and not w.endswith(("us", "ss")):
            return w[:-1]
    return w


def tokens(text):
    text = re.sub(r"(?<=\d),(?=\d)", "", text.lower())
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text) if w not in STOP and (len(w) > 1 or w.isdigit())]


def clean(text):
    text = re.sub(r"\[\^[^\]]+\]", "", text)                 # footnote marks
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)      # links: keep the words
    return re.sub(r"\s+", " ", text).strip()


def unquote(v):
    v = v.strip()
    return v[1:-1] if len(v) > 1 and v[0] == v[-1] and v[0] in "'\"" else v


class Page:
    __slots__ = ("node", "type", "title", "description", "status", "aliases", "passages", "out", "head")


def parse(node, text, here, bundle, graph):
    p = Page()
    p.node, p.type, p.title, p.description, p.status, p.aliases = node, "", "", "", "", []
    head, body = "", text
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            head, body = text[4:end], text[end + 4:]
    for key in ("type", "title", "description", "status"):
        m = re.search(rf"^{key}:[ \t]*(.*)$", head, re.M)
        if not m:
            continue
        value = m.group(1).strip()
        if value in ("", ">", ">-", ">+", "|", "|-", "|+") or value[:1] in "'\"":
            # a value that continues on indented lines
            more = re.match(r"((?:\n[ \t]+.*|\n[ \t]*(?=\n[ \t]))*)", head[m.end():]).group(1)
            value = " ".join(([] if value[:1] in ">|" else [value]) + [x.strip() for x in more.splitlines() if x.strip()])
        setattr(p, key, unquote(value))
    m = re.search(r"^aliases:[ \t]*\n((?:[ \t]*- .*\n?)+)", head, re.M)
    if m:
        p.aliases = [unquote(a) for a in re.findall(r"^[ \t]*- (.*)$", m.group(1), re.M)]
    cut = body.find("<!-- LINKS:START")
    prose = body if cut == -1 else body[:cut]
    if not p.title:
        m = re.search(r"^# (.+)$", prose, re.M)
        p.title = m.group(1).strip() if m else node
    # links out: markdown links and frontmatter resources
    def to_node(target):
        f = (bundle / target.lstrip("/")) if target.startswith("/") else (here / target)
        try:
            rel = os.path.normpath(f).replace(os.path.normpath(bundle) + os.sep, "", 1)
        except ValueError:
            return None
        if rel.startswith("..") or os.path.isabs(rel) or os.path.basename(rel) in SKIP_FILES:
            return None
        n = f"{graph}:/{rel}"
        return n if n != node else None

    out = []
    for target in re.findall(LINK, body) + re.findall(r"resource:[ \t]*(/\S+\.md)", head):
        n = to_node(target)
        if n and n not in out:
            out.append(n)
    p.out = out
    # passages: one for each paragraph, list item or table row, with its heading
    p.passages, heading, blocks, cur = [], "", [], []

    def flush():
        if cur:
            blocks.append((heading, " ".join(cur)))
            cur.clear()

    for line in prose.splitlines():
        line = line.strip()
        if not line or set(line) <= set("|-: "):
            flush()
        elif re.match(r"\[\^[^\]]+\]:", line):
            flush()
            cur.append("")  # a footnote text: dropped, with its next lines
        elif line.startswith("#"):
            flush()
            heading = line.lstrip("# ").strip()
        elif re.match(r"([-*+>|]|\d+[.)])\s", line) or line.startswith("|"):
            flush()
            cur.append(line)
        else:
            cur.append(line)
    flush()
    for h, raw in blocks:
        if not raw.strip():
            continue
        txt = clean(re.sub(r"^([-*+>]|\d+[.)])\s+", "", raw.strip()))
        if len(txt) < 25:
            continue
        parts = [txt]
        if len(txt) > 900:
            parts, acc = [], ""
            for sent in re.split(r"(?<=[.!?])\s+", txt):
                if acc and len(acc) + len(sent) > 700:
                    parts.append(acc)
                    acc = sent
                else:
                    acc = (acc + " " + sent).strip()
            parts.append(acc)
        for part in parts:
            p.passages.append((h, part, tokens(h + " " + part)))
    p.head = tokens(" ".join([p.title, p.description] + p.aliases))
    return p


def find_root(arg):
    if arg:
        return Path(arg).resolve()
    here = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
    for d in [here, *here.parents]:
        if (d / ".claude/knowledge.json").is_file():
            return d
    return None


def graph_files(root):
    """Return registry text, ordered local page files, and all local graph roots."""
    try:
        text = (root / ".claude/knowledge.json").read_text("utf-8")
        registry = json.loads(text)
        graphs = registry.get("graphs", {}) if isinstance(registry, dict) else None
    except (OSError, ValueError) as e:
        sys.exit(f"ERROR: cannot read .claude/knowledge.json: {e}")
    if not isinstance(graphs, dict):
        sys.exit("ERROR: graphs in .claude/knowledge.json must be an object.")
    files, roots = [], []
    for graph, spec in graphs.items():
        if not isinstance(spec, dict):
            continue
        if "repo" in spec:
            print(f"SKIP: remote graph {graph}. Remote graphs are unsupported by ask and ponder.", file=sys.stderr)
            continue
        if not isinstance(spec.get("path"), str) or not spec["path"]:
            continue
        bundle = (root / spec["path"]).resolve()
        roots.append(bundle)
        files += [(graph, bundle, f) for f in sorted(bundle.rglob("*.md")) if f.name not in SKIP_FILES]
    return text, files, roots


def load(root, files=None):
    pages = {}
    for graph, bundle, f in files if files is not None else graph_files(root)[1]:
        node = f"{graph}:/{f.relative_to(bundle).as_posix()}"
        try:
            pages[node] = parse(node, f.read_text("utf-8"), f.parent, bundle, graph)
        except OSError:
            continue
    return pages


def cache_path(root, graph_roots=()):
    """Use only an owner-only folder outside the project; never follow a cache-folder link."""
    if not callable(getattr(os, "getuid", None)) or any(
            not hasattr(os, flag) for flag in ("O_NOFOLLOW", "O_NONBLOCK")):
        return None  # search without a cache when the required file protections are absent
    folder = os.environ.get("KQ_CACHE")
    if folder == "off":
        return None
    base = Path(folder) if folder else Path(tempfile.gettempdir()) / f"kq-private-cache-{os.getuid()}"
    try:
        if any(base.resolve().is_relative_to(folder) for folder in (root, *graph_roots)):
            return None
        base.mkdir(mode=0o700, parents=True, exist_ok=True)
        st = base.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
            return None
        base = base.resolve()
        for parent in base.parents:
            st = parent.stat()
            if st.st_uid not in (0, os.getuid()) or (st.st_mode & 0o022 and not st.st_mode & stat.S_ISVTX):
                return None  # another user must not be able to replace a cache parent
        me = Path(__file__).read_bytes()
    except OSError:
        return None
    return base / (hashlib.sha256(str(root).encode() + b"\0" + me).hexdigest()[:16] + ".json")


def read_cache(path):
    """Read plain JSON, not executable data, from an owner-only regular file."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "r", encoding="utf-8") as stream:
        st = os.fstat(stream.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
            raise ValueError("unsafe cache file")
        return json.load(stream)


def cache_rows(rows):
    """Reject incomplete or malformed cached pages before the search uses them."""
    if not isinstance(rows, list):
        raise ValueError("invalid cached pages")
    pages = {}
    strings = lambda values: isinstance(values, list) and all(isinstance(v, str) for v in values)
    for row in rows:
        if not isinstance(row, list) or len(row) != len(FIELDS):
            raise ValueError("invalid cached page")
        p = Page()
        for key, value in zip(FIELDS, row):
            setattr(p, key, value)
        if not all(isinstance(getattr(p, key), str) for key in FIELDS[:5]):
            raise ValueError("invalid cached page fields")
        if not all(strings(getattr(p, key)) for key in ("aliases", "out", "head")):
            raise ValueError("invalid cached page lists")
        if not isinstance(p.passages, list):
            raise ValueError("invalid cached passages")
        for passage in p.passages:
            if (not isinstance(passage, list) or len(passage) != 3 or
                    not all(isinstance(v, str) for v in passage[:2]) or not strings(passage[2])):
                raise ValueError("invalid cached passage")
        pages[p.node] = p
    return pages


def cached_pages(root):
    """Reuse parsed pages only while the registry, script, and graph file state match."""
    text, files, graph_roots = graph_files(root)
    path = cache_path(root, graph_roots)
    if path is None:
        return load(root, files), "off"
    h = hashlib.sha256((CACHE_VERSION + text).encode())
    try:
        for _graph, _bundle, f in files:
            st = f.stat()
            h.update(f"{f} {st.st_mtime_ns} {st.st_ctime_ns} {st.st_size} {st.st_ino}\n".encode())
    except OSError:
        return load(root, files), "no stat"
    mark = h.hexdigest()
    try:
        data = read_cache(path)
        if isinstance(data, dict) and data.get("mark") == mark:
            pages = cache_rows(data["pages"])
            expected = {f"{graph}:/{f.relative_to(bundle).as_posix()}" for graph, bundle, f in files}
            if set(pages) == expected:
                return pages, "read"
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        pass
    pages = load(root, files)
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"mark": mark, "pages": [[getattr(p, k) for k in FIELDS] for p in pages.values()]}, stream)
        os.replace(tmp, path)
    except OSError:
        return pages, "not written"
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
    return pages, "written"


class Index:
    def __init__(self, pages):
        self.pages = pages
        self.units = []  # (node, passage number or -1 for the head, tokens)
        for node, p in pages.items():
            self.units.append((node, -1, p.head))
            for i, (_h, _t, toks) in enumerate(p.passages):
                self.units.append((node, i, toks))
        self.n = len(self.units)
        self.avg = (sum(len(u[2]) for u in self.units) / self.n) if self.n else 1.0
        self.df = Counter()
        for _n, _i, toks in self.units:
            self.df.update(set(toks))
        self.inlinks = {}
        for node, p in pages.items():
            for t in p.out:
                self.inlinks.setdefault(t, []).append(node)
        self.memo_nb, self.memo_score = {}, {}

    def score_units(self, q):
        """BM25 score of each unit that holds a query term."""
        q = set(q)
        memo = frozenset(q)
        if memo in self.memo_score:
            return self.memo_score[memo]
        idf = {t: math.log(1 + (self.n - self.df[t] + 0.5) / (self.df[t] + 0.5)) for t in q if self.df.get(t)}
        out = self.memo_score[memo] = {}
        if not idf:
            return out
        for k, (_node, _i, toks) in enumerate(self.units):
            tf = Counter(t for t in toks if t in idf)
            if not tf:
                continue
            norm = 1.2 * (1 - 0.75 + 0.75 * len(toks) / self.avg)
            out[k] = sum(idf[t] * f * 2.2 / (f + norm) for t, f in tf.items())
        return out

    def rank(self, q):
        """Pages by score: the head, plus the 3 best passages with weights 1, 1/2, 1/4."""
        per = {}
        for k, s in self.score_units(q).items():
            node, i, _ = self.units[k]
            per.setdefault(node, []).append((s, i))
        ranked = []
        for node, hits in per.items():
            head = sum(s for s, i in hits if i == -1)
            body = sorted(((s, i) for s, i in hits if i >= 0), reverse=True)
            score = head + sum(s * w for (s, _i), w in zip(body, (1, 0.5, 0.25)))
            ranked.append((score, node, body, head))
        ranked.sort(key=lambda r: (-r[0], r[1]))
        return ranked

    def neighbors(self, node):
        if node in self.memo_nb:
            return self.memo_nb[node]
        seen, out = set(), []
        for n in self.pages[node].out + self.inlinks.get(node, []):
            if n in self.pages and n not in seen and n != node:
                seen.add(n)
                out.append(n)
        self.memo_nb[node] = out
        return out


def cut(text, n):
    return text if len(text) <= n else text[: n - 3].rstrip() + "..."


def head_line(p):
    extra = f" | status: {p.status}" if p.status else ""
    return f"== {p.node} | {p.type or '-'} | {p.title}{extra}"


def fix_nodes(ix, nodes):
    """A model can write a node with no graph name. Take the page with that path when one graph has it."""
    out = []
    for n in nodes:
        if n not in ix.pages:
            path = "/" + n.split(":/", 1)[-1].lstrip("/")
            same = [k for k in ix.pages if k.split(":", 1)[1] == path]
            if len(same) != 1 and LOOSE_NODES:
                name = lambda k: k.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1].lower()
                bare = lambda k: name(k)[:-3] if name(k).endswith(".md") else name(k)
                same = [k for k in ix.pages if k.split(":", 1)[1] == path.rstrip("/") + ".md"]
                if len(same) != 1:
                    same = [k for k in ix.pages if bare(k) == bare(n)]
            n = same[0] if len(same) == 1 else n
        out.append(n)
    return out


def fuse(ix, queries):
    """Passages and pages by the sum of 1 / (10 + rank) over the queries."""
    sc, pg = {}, {}
    for query in queries:
        q = tokens(query)
        units = sorted(((s, k) for k, s in ix.score_units(q).items() if ix.units[k][1] >= 0), reverse=True)[:200]
        for r, (_s, k) in enumerate(units):
            key = ix.units[k][:2]
            sc[key] = sc.get(key, 0.0) + 1.0 / (10 + r)
        for r, x in enumerate(ix.rank(q)[:30]):
            pg[x[1]] = pg.get(x[1], 0.0) + 1.0 / (10 + r)
    return sc, pg


def fill(ix, node, best, cap):
    """Take the best passages first, then use page order up to the character limit."""
    p, keep, used = ix.pages[node], [], 0
    order = list(best) + [i for i in range(len(p.passages)) if i not in best]
    for i in dict.fromkeys(order):
        size = min(len(p.passages[i][1]), 700) + 20
        if keep and used + size > cap:
            break
        keep.append(i)
        used += size
    return sorted(keep)


def page_lines(ix, node, keep):
    p = ix.pages[node]
    lines = [head_line(p)]
    if p.description and DESC_CHARS:
        lines.append(f"   description: {cut(p.description, DESC_CHARS)}")
    for i in keep:
        h, t, _ = p.passages[i]
        lines.append(f"   > {('[' + h + '] ') if h else ''}{cut(t, 700)}")
    return lines


def add_block(out, lines, used, budget):
    size = sum(len(x) + 1 for x in lines)
    if used + size > budget:
        return used, False
    out.extend(lines)
    return used + size, True


def do_find(ix, queries, out):
    sc, pg = fuse(ix, queries)
    best = {}
    for (n, i), _s in sorted(sc.items(), key=lambda kv: (-kv[1], kv[0])):
        best.setdefault(n, []).append(i)
    out.append("SEARCHES: " + " | ".join(queries))
    top = sorted(pg, key=lambda n: (-pg[n], n))
    if not top:
        out.append("   no page matches these words.")
    used, full = 0, []
    for n in top[:FIND_PAGES]:
        keep = fill(ix, n, best.get(n, []), FIND_PAGE_CHARS)
        used, ok = add_block(out, page_lines(ix, n, keep), used, FIND_MAX)
        if not ok:
            break
        full.append(n)
    first = True
    for n, passages in best.items():
        if n in full:
            continue
        lines = (["MORE PASSAGES (the best passages of other pages):"] if first else []) + page_lines(ix, n, sorted(passages[:2]))
        used, ok = add_block(out, lines, used, FIND_MAX)
        if not ok:
            break
        first = False
    out.append("")
    return full


def page_rank(ix, seeds):
    """Personalized PageRank: a walk that starts again from the seed pages. Links count in both directions."""
    total = len(seeds)
    start = {n: 1.0 / total for n in seeds}
    r = dict(start)
    for _ in range(PPR_STEPS):
        nxt = {}
        for n, v in r.items():
            nb = ix.neighbors(n)
            for m in nb:
                nxt[m] = nxt.get(m, 0.0) + PPR_DAMP * v / len(nb)
        for n, v in start.items():
            nxt[n] = nxt.get(n, 0.0) + (1 - PPR_DAMP) * v
        r = nxt
    return r


def do_near(ix, nodes, q, out, max_chars=FIND_MAX):
    bad = [n for n in nodes if n not in ix.pages]
    nodes = [n for n in nodes if n in ix.pages]
    if bad:
        out.append("not a page, ignored: " + ", ".join(bad))
    if not nodes:
        out.append("Give the node of a page from a find result.")
        return []
    ranked = {r[1]: r for r in ix.rank(q)}
    weight = lambda n: TYPE_WEIGHT.get(ix.pages[n].type, 1.0)
    match = lambda n: ranked[n][0] if n in ranked else 0.0
    r = page_rank(ix, nodes)
    walk = [n for n in sorted(r, key=lambda n: (-r[n] * (1 + match(n)) * weight(n), n)) if n not in nodes]
    found = [n for n in sorted(ranked, key=lambda n: (-match(n) * weight(n), n)) if n not in nodes]
    order = list(dict.fromkeys(x for trio in zip(walk[0::2], walk[1::2], found) for x in trio)) or walk
    out.append("PAGES NEAR THE ANSWER (a walk along the links from " + ", ".join(nodes) + "; 2 of 3 pages are "
               "from the walk, 1 of 3 is from a search with the words of the answer):")
    used, shown = 0, []
    for n in order:
        best = [i for _s, i in (ranked[n][2] if n in ranked else [])]
        keep = fill(ix, n, best, NEAR_PAGE_CHARS)
        used, ok = add_block(out, page_lines(ix, n, keep), used, max_chars)
        if not ok:
            break
        shown.append(n)
    out.append("")
    return shown


def main():
    global LOOSE_NODES
    try:
        conf = json.loads(Path(__file__).with_name("kq.json").read_text("utf-8"))
        if not isinstance(conf, dict):
            conf = {}
    except (OSError, ValueError):
        conf = {}
    LOOSE_NODES = conf.get("nodes") == "loose"
    ap = argparse.ArgumentParser(prog="kq.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--root")
    sub = ap.add_subparsers(dest="cmd", required=True)
    find = sub.add_parser("find", help="search local pages")
    find.add_argument("queries", nargs="*")
    find.add_argument("--stdin", action="store_true")
    near = sub.add_parser("near", help="find pages near the answer")
    near.add_argument("nodes", nargs="+")
    near.add_argument("--q", default="")
    a = ap.parse_args()
    if a.cmd == "find":
        queries = [q for q in a.queries if q.strip()][:6]
        if a.stdin:
            text = " ".join(sys.stdin.read().split())
            queries += [text] if text else []
        if not queries:
            print("Give me a question. Run `/knowledge:ask <your question>`.")
            return 0
    root = find_root(a.root)
    if root is None or not (root / ".claude/knowledge.json").is_file():
        print("No .claude/knowledge.json is available. Run /knowledge:setup to register a graph.")
        return 0
    ix = Index(cached_pages(root)[0])
    if not ix.pages:
        print("No local knowledge pages are available. Use /knowledge:setup to register a local graph. "
              "Remote graphs are unsupported by ask and ponder.")
        return 0
    out = []
    if a.cmd == "find":
        do_find(ix, queries, out)
    else:
        near_conf = conf.get("near", {})
        cap = near_conf.get("max", FIND_MAX) if isinstance(near_conf, dict) else FIND_MAX
        if not isinstance(cap, int) or cap <= 0:
            cap = FIND_MAX
        do_near(ix, fix_nodes(ix, a.nodes), tokens(a.q), out, cap)
    text = "\n".join(out)
    if len(text) > OUT_MAX:
        text = text[:OUT_MAX] + f"\n(the output is cut at {OUT_MAX} characters.)"
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
