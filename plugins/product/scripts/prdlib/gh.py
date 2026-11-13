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

# Every scope that a classic token needs, and what each one pays for.
# `project` reads and writes the Project card, the Status option, and the two
# date fields. `repo` makes the issue, the label, and the milestone. A missing
# scope must stop the run before the first write, because a change set that
# fails in the middle leaves some issues made and some not. A GitHub App token
# has no scope list: `preconditions` checks its rights with the viewer fields
# instead. [inferred]
NEEDED_SCOPES = ("project", "repo")

# One GraphQL call gives each right of the token, so the read needs no account
# of the machine. A team session has an empty `GH_CONFIG_DIR`, and
# `gh auth status` exits 1 there (STORY-351).
RIGHTS_QUERY = """
query($owner: String!, $name: String!, $projectOwner: String!, $number: Int!) {
  viewer { login }
  repository(owner: $owner, name: $name) {
    id
    viewerCanCreateIssues
    owner { __typename id login ... on Organization { viewerCanAdminister } }
  }
  repositoryOwner(login: $projectOwner) {
    ... on ProjectV2Owner { projectV2(number: $number) { viewerCanUpdate } }
  }
}
"""


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
    # The names of the `X-OAuth-Scopes` header, or None when the reply has no
    # such header (a GitHub App token).
    scopes: tuple | None
    # True when the token may make an issue type of the organization.
    org_admin: bool
    can_create_issues: bool
    can_update_project: bool


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


def split_include(text: str) -> tuple[dict, str]:
    """The headers and the body of a `gh api --include` reply. The headers
    end at the first empty line. Each name is in lower case."""
    head, _empty, body = text.replace("\r\n", "\n").partition("\n\n")
    headers = {}
    for line in head.split("\n")[1:]:
        name, colon, value = line.partition(":")
        if colon:
            headers[name.strip().lower()] = value.strip()
    return headers, body


def _rights_data(body: str, stderr: str) -> dict:
    """The `data` of the rights reply. Raises when it holds no repository.
    `gh api` exits 1 for a reply with `errors`, so the caller reads the body
    at any exit code, and the error text comes from the body or from stderr."""
    try:
        reply = json.loads(body) or {}
    except ValueError:
        reply = {}
    data = reply.get("data") or {}
    if not data.get("repository"):
        errors = "; ".join(str(error.get("message", error)) for error
                           in reply.get("errors") or [])
        shown = errors or stderr.strip() or body.strip()
        raise UsageError(
            "the rights read of the token gave no repository: "
            f"{escape_controls(shown[:300])}")
    return data


def preconditions(root: Path, client: Gh) -> Context:
    field = project_field(root)
    repo = client.json(["repo", "view", "--json", "name,owner"])
    full = f"{repo['owner']['login']}/{repo['name']}"
    number = int(field["number"])
    done = client.call([
        "api", "--include", "graphql", "-f", f"query={RIGHTS_QUERY}",
        "-f", f"owner={repo['owner']['login']}", "-f", f"name={repo['name']}",
        "-f", f"projectOwner={field['owner']}", "-F", f"number={number}"])
    headers, body = split_include(done.stdout)
    data = _rights_data(body, done.stderr)
    header = headers.get("x-oauth-scopes")
    scopes = None if header is None else tuple(
        name.strip() for name in header.split(",") if name.strip())
    if scopes is not None:
        for name in NEEDED_SCOPES:
            if name not in scopes:
                raise UsageError(
                    f"the gh token has no `{name}` scope. Run "
                    f"`gh auth refresh -s {name}`.")
    repository = data["repository"]
    if repository.get("viewerCanCreateIssues") is not True:
        raise UsageError(
            f"the token cannot make issues in `{escape_controls(full)}`. "
            f"A GitHub App needs the permission Issues: write.")
    project = (data.get("repositoryOwner") or {}).get("projectV2") or {}
    if project.get("viewerCanUpdate") is not True:
        raise UsageError(
            f"the token cannot write the Project "
            f"`{escape_controls(field['owner'])}/{number}`. A GitHub App "
            f"needs the permission Projects: write.")
    owner = repository.get("owner") or {}
    is_org = owner.get("__typename") == "Organization"
    return Context(
        login=(data.get("viewer") or {})["login"],
        project_owner=field["owner"],
        project_number=number,
        repo=full,
        repo_node_id=repository["id"],
        owner_node_id=owner.get("id", ""),
        owner_is_org=is_org,
        scopes=scopes,
        org_admin=(is_org and owner.get("viewerCanAdminister") is True
                   and (scopes is None or "admin:org" in scopes)),
        can_create_issues=True,
        can_update_project=True,
    )
