"""The one `gh` process of the round trip, and the preconditions.

Every call to GitHub goes through Gh. The runner is a parameter, so each test
drives a recorded reply and no test touches the network.
"""
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import DataError, UsageError
from .ids import resolve
from .page import load_page
from .textsafe import escape_controls

PROJECT_PAGE = "PROJECT-01"

# Every scope the round trip needs, and what each one pays for. `project`
# reads and writes the Project card, the Status option, and the two date
# fields. `repo` makes the issue, the label, and the milestone. A missing
# scope must stop the run before the first write, because a change set that
# fails in the middle leaves some issues made and some not. [inferred]
NEEDED_SCOPES = ("project", "repo")
# `create_issue_type` of Task 8 writes at organization level. The REST
# endpoint names `admin:org` for a classic token, and `write:org` alone gets
# 403. It is not required: a token without it falls back to the `type:`
# labels.
ORG_SCOPES = ("admin:org",)


@dataclass(frozen=True)
class Completed:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Context:
    login: str
    project_owner: str
    project_number: int
    repo: str
    repo_node_id: str
    owner_node_id: str
    owner_is_org: bool
    org_write: bool


def _run(args):
    done = subprocess.run(["gh", *args], capture_output=True, text=True)
    return Completed(done.returncode, done.stdout, done.stderr)


class Gh:
    def __init__(self, runner=_run):
        self.runner = runner

    def call(self, args) -> Completed:
        return self.runner(args)

    def text(self, args) -> str:
        done = self.call(args)
        if done.returncode != 0:
            # An argument holds a title, a body or an owner of a page, and
            # the error text is the text of GitHub. Both are escaped.
            raise UsageError(
                f"`gh {escape_controls(' '.join(args))}` failed: "
                f"{escape_controls((done.stderr or done.stdout).strip())}")
        return done.stdout

    def json(self, args):
        return json.loads(self.text(args) or "null")


def project_field(root: Path) -> dict:
    """The `github` mapping of PROJECT-01.md. Raises when a key is absent."""
    try:
        page = load_page(resolve(root, PROJECT_PAGE))
    except DataError as error:
        raise UsageError(str(error))
    field = page.frontmatter.get("github") or {}
    if not field.get("owner") or not field.get("number"):
        name = escape_controls(page.path.name)
        raise UsageError(
            f"{name} has no GitHub Project. Add "
            f"`github: {{ owner: <login>, number: <n> }}` to "
            f"docs/product/roadmap/projects/{name}, where <n> is the "
            f"number in the Project URL.")
    return field


def preconditions(root: Path, client: Gh) -> Context:
    field = project_field(root)
    status = client.call(["auth", "status"])
    if status.returncode != 0:
        raise UsageError("`gh auth status` failed. Run `gh auth login`.")
    scopes = status.stdout + status.stderr
    for name in NEEDED_SCOPES:
        if f"'{name}'" not in scopes:
            raise UsageError(
                f"the gh token has no `{name}` scope. Run "
                f"`gh auth refresh -s {name}`.")
    org_write = any(f"'{name}'" in scopes for name in ORG_SCOPES)
    login = client.json(["api", "user", "--jq", "."])["login"]
    repo = client.json(["repo", "view", "--json", "name,owner,id"])
    full = f"{repo['owner']['login']}/{repo['name']}"
    owner = client.json(["api", f"repos/{full}", "--jq", "."])["owner"]
    return Context(
        login=login,
        project_owner=field["owner"],
        project_number=int(field["number"]),
        repo=full,
        repo_node_id=repo["id"],
        owner_node_id=owner.get("node_id", ""),
        owner_is_org=owner.get("type") == "Organization",
        org_write=org_write,
    )
