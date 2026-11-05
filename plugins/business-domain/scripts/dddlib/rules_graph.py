"""The edge rules of `ddd.py check`: E4, E5, E6, E8, E9, and E12."""
from .bundle import Bundle, context_id, names, stored_edges
from .issues import ERROR, Issue
from .page import line_of
from .schema import edges

DIRECTIONAL = {"customer-supplier", "conformist", "anti-corruption-layer",
               "open-host-service", "published-language"}
UNDIRECTED = {"shared-kernel", "separate-ways"}
MUD_GUARDS = {"anti-corruption-layer", "conformist"}


def e4(bundle: Bundle) -> list:
    """An edge points to a page that does not exist."""
    return [Issue(ERROR, "E4", path, line_of(page, field_name),
                  f"{field_name}: {target_id} does not exist")
            for path, page in bundle.pages.items()
            for field_name, target_id, target in stored_edges(bundle, page)
            if target not in bundle.pages and target not in bundle.broken]


def e5(bundle: Bundle) -> list:
    """An edge points to a page of a type that the schema does not permit."""
    out = []
    for path, page in bundle.pages.items():
        for field_name, target_id, target in stored_edges(bundle, page):
            other = bundle.pages.get(target)
            if other is None:
                continue
            rule = edges()[field_name]
            if other.type not in rule["targets"]:
                out.append(Issue(ERROR, "E5", path, line_of(page, field_name),
                                 f"{field_name}: {target_id} is a {other.type}. "
                                 f"Permitted: {', '.join(rule['targets'])}"))
            elif other.type == "Term" and rule["kinds"] \
                    and other.frontmatter.get("kind") not in rule["kinds"]:
                out.append(Issue(ERROR, "E5", path, line_of(page, field_name),
                                 f"{field_name}: {target_id} is a Term of kind "
                                 f"{other.frontmatter.get('kind')}. Permitted "
                                 f"kinds: {', '.join(rule['kinds'])}"))
    return out


def _cycles(graph: dict) -> list:
    """Each strongly connected group of more than one node, or of one node
    with an edge to itself (Tarjan)."""
    index, low, stack, on_stack, found = {}, {}, [], set(), []

    def visit(node):
        index[node] = low[node] = len(index)
        stack.append(node)
        on_stack.add(node)
        for nxt in graph.get(node, ()):
            if nxt not in index:
                visit(nxt)
                low[node] = min(low[node], low[nxt])
            elif nxt in on_stack:
                low[node] = min(low[node], index[nxt])
        if low[node] == index[node]:
            group = []
            while True:
                member = stack.pop()
                on_stack.discard(member)
                group.append(member)
                if member == node:
                    break
            if len(group) > 1 or node in graph.get(node, ()):
                found.append(sorted(group))

    for node in sorted(graph):
        if node not in index:
            visit(node)
    return found


def e6(bundle: Bundle) -> list:
    """An edge with `acyclic: true` in the schema makes a cycle."""
    out = []
    graphs = {name: {} for name, rule in edges().items() if rule["acyclic"]}
    for path, page in bundle.pages.items():
        for name, _target_id, target in stored_edges(bundle, page):
            if name in graphs and target in bundle.pages:
                graphs[name].setdefault(path, []).append(target)
    for field_name, graph in graphs.items():
        for group in _cycles(graph):
            first = group[0]
            out.append(Issue(ERROR, "E6", first,
                             line_of(bundle.pages[first], field_name),
                             f"{field_name} cycle: "
                             f"{' -> '.join(p.stem for p in group + [first])}"))
    return out


def _relationships(bundle: Bundle):
    return [(path, page) for path, page in bundle.pages.items()
            if page.type == "Relationship"]


def e8(bundle: Bundle) -> list:
    """A Relationship to a Big Ball of Mud has no anti-corruption-layer and
    no conformist pattern."""
    out = []
    for path, page in _relationships(bundle):
        patterns = set(names(page.frontmatter.get("patterns")))
        if patterns & MUD_GUARDS:
            continue
        for field_name, target_id, target in stored_edges(bundle, page):
            other = bundle.pages.get(target)
            if field_name == "between" and other is not None \
                    and other.frontmatter.get("big_ball_of_mud") is True:
                out.append(Issue(ERROR, "E8", path, line_of(page, "patterns"),
                                 f"{target_id} is a Big Ball of Mud. Add the "
                                 f"anti-corruption-layer or the conformist "
                                 f"pattern."))
    return out


def e9(bundle: Bundle) -> list:
    """A `translates_to` edge joins two pages of the same context."""
    out = []
    for path, page in bundle.pages.items():
        own = context_id(bundle, page)
        for field_name, target_id, target in stored_edges(bundle, page):
            if field_name != "translates_to" or own == "-":
                continue
            if context_id(bundle, bundle.pages.get(target)) == own:
                out.append(Issue(ERROR, "E9", path, line_of(page, field_name),
                                 f"translates_to: {target_id} is in the same "
                                 f"context {own}"))
    return out


def e12(bundle: Bundle) -> list:
    """A Relationship breaks the direction rule of `upstream`."""
    out = []
    for path, page in _relationships(bundle):
        patterns = set(names(page.frontmatter.get("patterns")))
        upstream = page.frontmatter.get("upstream")
        between = names(page.frontmatter.get("between"))
        line = line_of(page, "upstream")
        if patterns & DIRECTIONAL and not upstream:
            out.append(Issue(ERROR, "E12", path, line_of(page, "patterns"),
                             f"the patterns {', '.join(sorted(patterns & DIRECTIONAL))} "
                             f"have a direction. Add `upstream`."))
        if upstream and patterns and patterns <= UNDIRECTED:
            out.append(Issue(ERROR, "E12", path, line,
                             f"{', '.join(sorted(patterns))} has no direction. "
                             f"Remove `upstream`."))
        if upstream and upstream not in between:
            out.append(Issue(ERROR, "E12", path, line,
                             f"upstream: {upstream} is not in `between`"))
    return out


RULES = [e4, e5, e6, e8, e9, e12]
