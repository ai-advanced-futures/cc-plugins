"""Build a project with all five brains and links across them.

The integration test (tests/test_fixture_project.py) and the ask evaluation
(eval/run_ask_eval.py) use it. Each write goes through the save code of a brain.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PLUGINS = Path(__file__).resolve().parents[2]
SCRIPTS = {"knowledge": PLUGINS / "knowledge" / "scripts" / "knowledge_graph.py",
           "prd": PLUGINS / "product" / "scripts" / "prd.py",
           "ddd": PLUGINS / "business-domain" / "scripts" / "ddd.py",
           "adr": PLUGINS / "architecture" / "scripts" / "adr.py",
           "system-design": PLUGINS / "system-design" / "scripts" / "system_design.py"}


def run(script, root, *args) -> str:
    result = subprocess.run([sys.executable, str(script), "--root", str(root), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{Path(script).name} {' '.join(args)} failed:\n{result.stdout}{result.stderr}")
    return result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""


def page(printed: str) -> str:
    """The bundle path of a page from the root-relative path that a save script prints."""
    return "/" + "/".join(Path(printed).parts[-2:])


def build(root: Path) -> Path:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    run(SCRIPTS["knowledge"], root, "init")
    run(SCRIPTS["prd"], root, "init", "--title", "Shop", "--description", "An online shop.")
    run(SCRIPTS["ddd"], root, "init")
    subprocess.run([sys.executable, str(PLUGINS / "architecture" / "scripts" / "scaffold.py"), "--target", str(root),
                    "--today", "2026-10-29"], check=True, capture_output=True)
    run(SCRIPTS["adr"], root, "init")
    run(SCRIPTS["system-design"], root, "init", "--title", "Shop system")
    persona = run(SCRIPTS["prd"], root, "new", "Persona", "--title", "Buyer", "--description", "A person who buys goods.")
    need = run(SCRIPTS["prd"], root, "new", "Need", "--title", "Pay fast", "--description", "The buyer pays in one step.",
               "--set", "kind=job", "--link", f"serves={page(persona)}")
    capability = run(SCRIPTS["prd"], root, "new", "Capability", "--title", "Take card payments",
                     "--description", "The shop takes card payments.", "--link", f"addresses={page(need)}")
    run(SCRIPTS["prd"], root, "regen")
    context = run(SCRIPTS["ddd"], root, "new", "Context", "--title", "Billing", "--description", "Invoices and payments.",
                  "--set", "subdomain=core")
    term = run(SCRIPTS["ddd"], root, "new", "Term", "--title", "Invoice", "--description", "A request to pay.",
               "--set", "kind=entity", "--set", f"context={page(context)}")
    decision = run(SCRIPTS["adr"], root, "new", "--title", "Use Postgres for invoices", "--area", "data",
                   "--description", "One database holds the invoices.", "--parent-spec", "system-design:/areas/data.md")
    component = run(SCRIPTS["system-design"], root, "new", "Component", "--title", "Billing",
                    "--description", "Owns invoices and payment state.", "--set", "kind=service", "--set", "areas=[data]",
                    "--set", f"realizes=[prd:{page(capability)}]", "--set", f"used_by=[prd:{page(persona)}]")
    run(SCRIPTS["system-design"], root, "link", "data", "decisions", f"adr:/{Path(decision).name}",
        "--with", "key=data-1", "--with", "binds=The store of the invoices", "--with", "source=adr")
    run(SCRIPTS["system-design"], root, "set", "data", "area_state=decided")
    run(SCRIPTS["system-design"], root, "new", "GlossaryTerm", "--title", "Invoice",
        "--description", "The billing record of one order.", "--set", f"same_as=ddd:{page(term)}")
    run(SCRIPTS["knowledge"], root, "new", "Synthesis", "--title", "How billing works",
        "--description", "Billing across the five graphs.")
    run(SCRIPTS["knowledge"], root, "link", "how-billing-works", "sources", f"prd:{page(capability)}")
    run(SCRIPTS["knowledge"], root, "link", "how-billing-works", "sources", f"system-design:{page(component)}")
    return root


if __name__ == "__main__":
    print(build(Path(sys.argv[1])))
