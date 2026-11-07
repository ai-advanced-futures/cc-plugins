"""Writes to a remote graph (standard section 12): a full clone, both checks, a push, one PR."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from knowledgelib import DataError, UsageError, manifest, probe, registry, remote
from knowledgelib.issues import ERROR


def _default_branch(clone) -> str:
    return remote.git("symbolic-ref", "--short", "refs/remotes/origin/HEAD", cwd=clone).strip().split("/", 1)[-1]


def work_root() -> Path:
    if os.environ.get("KNOWLEDGE_WORK_DIR"):
        return Path(os.environ["KNOWLEDGE_WORK_DIR"])
    return Path.home() / ".cache" / "claude-knowledge-work"


def major(version) -> int:
    return int(str(version).split(".")[0])


def repo_slug(repo: str) -> str:
    return re.sub(r"^(https?://)?github\.com/", "", repo).removesuffix(".git").strip("/")


def _brain(clone, graph, probe_find):
    data = manifest.read(clone / graph.path)
    if data is None:
        raise DataError(f"{graph.name} has no manifest.md. The owner of {graph.repo} must update its brain and run its setup.")
    found = probe.locate(data["plugin"], data["save_code"], probe_find)
    if found is None:
        raise DataError(f"the brain of {graph.name} ({data['plugin']}) is not installed here. Install it: {data['install']}")
    return data, found[0]


def checkout(root, graphs, name, probe_find=None, fresh=False) -> Path:
    probe_find = probe_find or probe.find
    graph = registry.require(graphs, name)
    if not graph.remote:
        raise UsageError(f"{name} is a local graph")
    clone = work_root() / remote.slug(graph.repo)
    if fresh and clone.exists():
        shutil.rmtree(clone)
    if not (clone / ".git").is_dir():
        clone.parent.mkdir(parents=True, exist_ok=True)
        remote.git("clone", "--quiet", remote.clone_url(graph.repo), str(clone))
    else:
        # The clone is scratch space: an existing clone is reset to the default branch
        # on every checkout, so a second learn or forget run never reuses a stale feature branch. [inferred]
        base = _default_branch(clone)
        remote.git("fetch", "-q", "origin", cwd=clone)
        remote.git("checkout", "-q", base, cwd=clone)
        remote.git("reset", "-q", "--hard", f"origin/{base}", cwd=clone)
        remote.git("clean", "-q", "-fd", cwd=clone)
    data, plugin_root = _brain(clone, graph, probe_find)
    installed = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text("utf-8"))["version"]
    if major(data["plugin_version"]) > major(installed):
        raise DataError(f"{name} was written by {data['plugin']} {data['plugin_version']}, and this project has "
                        f"{installed}. Update the plugin first.")
    return clone


def run_checks(clone, data, plugin_root, probe_find) -> list[str]:
    from knowledgelib import general_check

    failures = []
    probe.check(data["plugin"], data["save_code"])
    save_code = probe.inside(plugin_root, data["save_code"])
    brain = subprocess.run([sys.executable, str(save_code), "--root", str(clone), "check"],
                           capture_output=True, text=True)
    if brain.returncode != 0:
        failures.append(f"the brain check of {data['plugin']} failed:\n{brain.stdout}{brain.stderr}")
    try:
        issues = general_check.check_all(clone, [data["brain"]], probe_find=probe_find)
    except UsageError as error:
        return failures + [f"the general check cannot run: {error}"]
    failures += [issue.text() for issue in issues if issue.level == ERROR]
    return failures


def publish(root, graphs, name, branch, title, body, probe_find=None, gh=None) -> str:
    probe_find = probe_find or probe.find
    gh = gh or os.environ.get("KNOWLEDGE_GH", "gh")
    graph = registry.require(graphs, name)
    clone = work_root() / remote.slug(graph.repo)
    if not (clone / ".git").is_dir():
        raise UsageError(f"no clone of {name}. Run remote-checkout first.")
    data, plugin_root = _brain(clone, graph, probe_find)
    failures = run_checks(clone, data, plugin_root, probe_find)
    if failures:
        raise DataError("the checks failed in the clone, so nothing is pushed:\n" + "\n".join(failures))
    base = _default_branch(clone)
    remote.git("checkout", "-q", "-b", branch, cwd=clone)
    remote.git("add", "-A", cwd=clone)
    remote.git("commit", "-q", "-m", title, cwd=clone)
    head = branch
    if subprocess.run(["git", "push", "-q", "origin", branch], cwd=clone, capture_output=True).returncode != 0:
        fork = subprocess.run([gh, "repo", "fork", "--remote", "--remote-name", "fork"], cwd=clone,
                              capture_output=True, text=True)
        if fork.returncode != 0:
            raise DataError(f"cannot push and cannot fork {graph.repo}: {fork.stderr.strip()}")
        remote.git("push", "-q", "fork", branch, cwd=clone)
        login = subprocess.run([gh, "api", "user", "--jq", ".login"], capture_output=True, text=True).stdout.strip()
        head = f"{login}:{branch}"
    pr = subprocess.run([gh, "pr", "create", "--repo", repo_slug(graph.repo), "--head", head, "--base", base,
                         "--title", title, "--body", body], cwd=clone, capture_output=True, text=True)
    if pr.returncode != 0:
        raise DataError(f"the branch is pushed, but gh pr create failed: {pr.stderr.strip()}")
    return pr.stdout.strip().splitlines()[-1]


def cmd_checkout(args) -> int:
    print(checkout(args.root, registry.read(args.root), args.graph, fresh=args.fresh))
    return 0


def cmd_publish(args) -> int:
    body = Path(args.body_file).read_text("utf-8")
    print(publish(args.root, registry.read(args.root), args.graph, args.branch, args.title, body))
    return 0


def register(sub) -> None:
    parser = sub.add_parser("remote-checkout", help="clone a remote graph for a write")
    parser.add_argument("graph")
    parser.add_argument("--fresh", action="store_true", help="delete an old clone first")
    parser.set_defaults(run=cmd_checkout)
    parser = sub.add_parser("remote-publish", help="check, push, and open one pull request")
    parser.add_argument("graph")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--body-file", required=True)
    parser.set_defaults(run=cmd_publish)
