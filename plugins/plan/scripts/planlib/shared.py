"""Cooperative Plan gate on one normal Git branch; never merge a proposal."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shlex
import subprocess
import tempfile
import uuid

from . import PlanError

COORDINATION_REF = "refs/heads/plan-coordination"
DATA_REF = "refs/dolt/data"
INFO_REF = "refs/heads/__dolt_remote_info__"
_HEX = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
_FIELDS = {"schema_version", "workspace_id", "control_id", "status", "attempt", "actor",
           "operation", "request_id", "observed_data_ref", "published_data_ref", "digest"}


REPO_ENV_KEYS = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_OBJECT_DIRECTORY", "GIT_DIR",
    "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE", "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
    "GIT_COMMON_DIR", "GIT_NAMESPACE",
}


_URL_REWRITE = re.compile(r"url\..*\.(?:push)?insteadof", re.IGNORECASE | re.DOTALL)
_SSH_TRANSPORT = re.compile(r"git\+ssh://git@([^/:@\s]+)/(\S+)")
_HTTPS_TRANSPORT = re.compile(r"git\+https://([^/:@\s]+)/(\S+)")


def equivalent_transports(transport_url: str) -> set[str]:
    """Give the SSH and HTTPS forms of one host and path; Plan 0.2.0 saved either form."""
    forms = {transport_url}
    ssh = _SSH_TRANSPORT.fullmatch(transport_url)
    https = _HTTPS_TRANSPORT.fullmatch(transport_url)
    if ssh:
        forms.add("git+https://" + ssh[1] + "/" + ssh[2])
    elif https:
        forms.add("git+ssh://git@" + https[1] + "/" + https[2])
    return forms


class SharedCommandError(PlanError):
    """A shared command has an unknown effect, not a validation refusal."""


class GateBusyError(PlanError):
    """The server refused a proposal before it acquired the shared gate."""


def git_environment():
    """Keep session credentials and identity; remove only repository routing."""
    env = {key: value for key, value in os.environ.items() if key not in REPO_ENV_KEYS}
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": ""})
    count = env.get("GIT_CONFIG_COUNT", "0")
    if not count.isdecimal() or not 0 <= int(count) <= 128:
        raise PlanError("session Git configuration count is invalid")
    count = int(count)
    if any("GIT_CONFIG_KEY_" + str(i) not in env or "GIT_CONFIG_VALUE_" + str(i) not in env for i in range(count)):
        raise PlanError("session Git configuration is incomplete")
    # A session URL rewrite routes the shared remote to another address than Beads saved.
    pairs = [(env.pop("GIT_CONFIG_KEY_" + str(i)), env.pop("GIT_CONFIG_VALUE_" + str(i))) for i in range(count)]
    pairs = [(key, value) for key, value in pairs if not _URL_REWRITE.fullmatch(key)]
    for index, (key, value) in enumerate(pairs):
        env["GIT_CONFIG_KEY_" + str(index)] = key
        env["GIT_CONFIG_VALUE_" + str(index)] = value
    count = len(pairs)
    for key, value in (("core.hooksPath", os.devnull), ("protocol.ext.allow", "never"), ("commit.gpgsign", "false")):
        env["GIT_CONFIG_KEY_" + str(count)] = key
        env["GIT_CONFIG_VALUE_" + str(count)] = value
        count += 1
    env["GIT_CONFIG_COUNT"] = str(count)
    return env


def capture(command, *, cwd, env, timeout=60, stdin=None):
    """Bound the command and its children, including a pipe held by a child."""
    try:
        child = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 encoding="utf-8", errors="replace", start_new_session=True)
    except OSError as exc:
        raise SharedCommandError("cannot start a shared-workspace command") from exc
    try:
        out, err = child.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            child.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            for stream in (child.stdin, child.stdout, child.stderr):
                if stream:
                    stream.close()
        raise SharedCommandError("shared-workspace command timed out; its effect is unknown; retain the gate") from exc
    return subprocess.CompletedProcess(command, child.returncode, out, err)


def atomic_json(path: Path, value: dict):
    if path.is_symlink():
        raise PlanError("shared-workspace state cannot be a symbolic link")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".plan-shared-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


def issue_digest(issues):
    rows = []
    for issue in issues:
        row = dict(issue)
        if isinstance(row.get("dependencies"), list):
            row["dependencies"] = sorted(row["dependencies"], key=lambda edge: json.dumps(edge, sort_keys=True))
        if isinstance(row.get("labels"), list):
            row["labels"] = sorted(row["labels"])
        rows.append(row)
    rows.sort(key=lambda row: row["id"])
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def dolt_url(url: str) -> str:
    """Use only native Git transports, not Git external helper commands."""
    if url.startswith("/"):
        return "git+" + Path(url).resolve().as_uri()
    if url.startswith(("file://", "https://", "ssh://")):
        return "git+" + url
    match = re.fullmatch(r"([A-Za-z0-9_.@-]+):([^\s:]+)", url)
    if match and "@" in match[1]:
        return "git+ssh://" + match[1] + "/" + match[2]
    raise PlanError("shared Plan needs an absolute file, HTTPS, or SSH Git remote")


class GitGate:
    def __init__(self, source_root: Path, remote: str, workspace_id=None, control_id=None, *,
                 actor="agent:plan", operation="operation", request_id=None, state_dir=None, timeout=60):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", remote):
            raise PlanError("shared Git remote name is invalid")
        for value in (actor, operation):
            if not isinstance(value, str) or not value or len(value) > 512 or any(ord(c) < 32 for c in value):
                raise PlanError("shared actor and operation must be nonempty text without control characters")
        if request_id is not None and (not isinstance(request_id, str) or not request_id or len(request_id) > 512):
            raise PlanError("shared request ID is invalid")
        self.root = Path(source_root).resolve()
        self.remote = remote
        self.workspace_id = workspace_id
        self.control_id = control_id
        self.actor, self.operation, self.request_id = actor, operation, request_id
        self.state_dir = Path(state_dir) if state_dir else self.root / ".claude/plan"
        self.timeout = timeout
        self.tip = None
        self.state = None
        self.lock_tip = None
        self.env = git_environment()
        ssh = self.env.get("GIT_SSH_COMMAND")
        if not ssh:
            configured = self.git("config", "--get", "core.sshCommand", check=False)
            ssh = configured.stdout.strip() if configured.returncode == 0 else ""
        if not ssh:
            ssh = shlex.quote(self.env["GIT_SSH"]) if self.env.get("GIT_SSH") else "ssh"
        self.env["GIT_SSH_COMMAND"] = ssh + " -o BatchMode=yes"
        self.journal = None
        self.confirmed_release: dict | None = None
        fetch = self.git("remote", "get-url", "--all", remote).stdout.splitlines()
        push = self.git("remote", "get-url", "--push", "--all", remote).stdout.splitlines()
        if len(fetch) != 1 or fetch != push:
            raise PlanError("shared Plan requires one identical fetch and push Git remote")
        self.url = fetch[0]
        self.transport_url = dolt_url(self.url)

    def git(self, *args, stdin=None, check=True):
        result = capture(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "-c", "protocol.ext.allow=never",
                          "-C", str(self.root), *args], cwd=self.root, env=self.env,
                         timeout=self.timeout, stdin=stdin)
        if check and result.returncode:
            raise PlanError("shared Git command failed; no success was confirmed")
        return result

    def remote_ref(self, ref):
        result = self.git("ls-remote", "--refs", self.remote, ref)
        rows = result.stdout.splitlines()
        if not rows:
            return None
        if len(rows) != 1:
            raise PlanError("shared remote returned an ambiguous ref")
        fields = rows[0].split()
        if len(fields) != 2 or fields[1] != ref or not _HEX.fullmatch(fields[0]):
            raise PlanError("shared remote returned an invalid ref")
        return fields[0]

    @staticmethod
    def validate(state):
        if (not isinstance(state, dict) or set(state) != _FIELDS
                or type(state.get("schema_version")) is not int or state.get("schema_version") != 1):
            raise PlanError("unsupported shared Plan gate state")
        for key in ("workspace_id", "control_id", "attempt", "actor", "operation"):
            value = state[key]
            if not isinstance(value, str) or not value or len(value) > 512 or any(ord(c) < 32 for c in value):
                raise PlanError("invalid shared Plan gate identity")
        if not re.fullmatch(r"[0-9a-f]{32}", state["attempt"]):
            raise PlanError("invalid shared Plan gate attempt")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*", state["workspace_id"]):
            raise PlanError("invalid shared Plan workspace identity")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", state["control_id"]):
            raise PlanError("invalid shared Plan control identity")
        if not isinstance(state["status"], str) or state["status"] not in {"locked", "unlocked"}:
            raise PlanError("invalid shared Plan gate status")
        if state["request_id"] is not None and (not isinstance(state["request_id"], str)
                                                or not state["request_id"] or len(state["request_id"]) > 512):
            raise PlanError("invalid shared Plan request identity")
        for key in ("observed_data_ref", "published_data_ref"):
            if state[key] is not None and (not isinstance(state[key], str) or not _HEX.fullmatch(state[key])):
                raise PlanError("invalid shared Plan data ref")
        digest = state["digest"]
        if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise PlanError("invalid shared Plan data digest")
        if state["status"] == "unlocked" and (state["published_data_ref"] is None or digest is None):
            raise PlanError("unlocked shared Plan gate has no published baseline")
        return state

    def observe(self):
        tip = self.remote_ref(COORDINATION_REF)
        if tip is None:
            self.tip, self.state = None, None
            return None
        # Fetch the observed object, not a moving remote tracking branch.
        self.git("fetch", "--no-tags", "--no-write-fetch-head", self.remote, tip)
        state = self._read_state(tip)
        if self.workspace_id is not None and (state["workspace_id"] != self.workspace_id
                                              or state["control_id"] != self.control_id):
            raise PlanError("shared gate belongs to another Plan workspace")
        self.tip, self.state = tip, state
        return state

    def _read_state(self, tip):
        result = self.git("show", tip + ":state.json")
        if len(result.stdout) > 16384:
            raise PlanError("shared Plan gate state is too large")
        try:
            return self.validate(json.loads(result.stdout))
        except (ValueError, TypeError) as exc:
            raise PlanError("shared Plan gate is not valid JSON") from exc

    def _released_attempt(self, journal, immutable):
        """Prove the saved lock's own release is in the observed branch history."""
        if self.tip is None or self.tip == journal["tip"]:
            return None
        ancestor = self.git("merge-base", "--is-ancestor", journal["tip"], self.tip, check=False)
        if ancestor.returncode == 1:
            return None
        if ancestor.returncode:
            raise PlanError("cannot verify shared release history; retain the local attempt")
        history = self.git("rev-list", "--first-parent", "--ancestry-path", "--reverse",
                           journal["tip"] + ".." + self.tip).stdout.splitlines()
        if not history or not _HEX.fullmatch(history[0]):
            return None
        released = history[0]
        parents = self.git("rev-list", "--parents", "-n", "1", released).stdout.split()
        if parents != [released, journal["tip"]]:
            return None
        state = self._read_state(released)
        if state["status"] != "unlocked" or any(state[key] != journal["gate_state"][key] for key in immutable):
            return None
        return state

    def proposal(self, state, parent=None):
        self.validate(state)
        blob = self.git("hash-object", "-w", "--stdin", stdin=json.dumps(state, sort_keys=True) + "\n").stdout.strip()
        tree = self.git("mktree", stdin="100644 blob " + blob + "\tstate.json\n").stdout.strip()
        args = ["commit-tree", tree]
        if parent:
            args += ["-p", parent]
        return self.git(*args, stdin="Plan shared " + state["status"] + "\n").stdout.strip()

    def push(self, commit, *, confirm_tip=True):
        # No force, lease, merge, or rebase is permitted for the gate.
        result = self.git("push", "--porcelain", self.remote, commit + ":" + COORDINATION_REF, check=False)
        if result.returncode:
            refused = any(line.startswith("!\t") and (
                          ("[rejected]" in line and any(reason in line for reason in
                           ("(fetch first)", "(non-fast-forward)", "(stale info)")))
                          or ("[remote rejected]" in line and "(failed to update ref)" in line))
                          for line in result.stdout.splitlines())
            if refused and self.remote_ref(COORDINATION_REF) != commit:
                raise GateBusyError("shared gate is busy; do not retry or merge the proposal")
            raise PlanError("shared gate push was refused or its effect is unknown; do not retry or merge the proposal")
        if confirm_tip and self.remote_ref(COORDINATION_REF) != commit:
            raise PlanError("shared gate push was not confirmed; retain the gate")

    def acquire(self, *, bootstrap=False):
        state = self.observe()
        if state is None:
            if not bootstrap or not self.workspace_id or not self.control_id:
                raise PlanError("shared Plan is not enabled; share the existing workspace while all writers are paused")
            state = {"schema_version": 1, "workspace_id": self.workspace_id, "control_id": self.control_id,
                     "status": "locked", "attempt": uuid.uuid4().hex, "actor": self.actor,
                     "operation": self.operation, "request_id": self.request_id,
                     "observed_data_ref": self.remote_ref(DATA_REF), "published_data_ref": None, "digest": None}
        else:
            if bootstrap:
                raise PlanError("shared Plan is already enabled; join its published control instead")
            if state["status"] != "unlocked":
                raise PlanError("shared Plan is locked by " + state["actor"] + " for " + state["operation"]
                                + " (attempt " + state["attempt"] + "); stop the original owner before review; no automatic takeover")
            state = {**state, "status": "locked", "attempt": uuid.uuid4().hex, "actor": self.actor,
                     "operation": self.operation, "request_id": self.request_id,
                     "observed_data_ref": state["published_data_ref"]}
        proposal = self.proposal(state, self.tip)
        self.journal = {"schema_version": 1, "attempt": state["attempt"], "tip": proposal,
                        "workspace_id": state["workspace_id"], "control_id": state["control_id"],
                        "remote": self.remote, "remote_fingerprint": hashlib.sha256(self.transport_url.encode()).hexdigest(),
                        "operation": self.operation, "request_id": self.request_id, "gate_state": dict(state),
                        "phase": "acquiring", "owned_local": None, "publication": None}
        self.save_attempt()
        try:
            self.push(proposal)
        except GateBusyError:
            (self.state_dir / "plan-shared-attempt.json").unlink(missing_ok=True)
            raise
        self.lock_tip, self.state = proposal, state
        return state

    def save_attempt(self, **changes):
        if self.journal is None:
            raise PlanError("shared attempt has no local journal; retain the gate")
        self.journal.update(changes)
        atomic_json(self.state_dir / "plan-shared-attempt.json", self.journal)

    def _unpublished_attempt(self, journal):
        """Prove the remote history excludes a proposal from its known parent."""
        if journal["phase"] != "acquiring" or journal["owned_local"] is not None or journal["publication"] is not None:
            return False
        proposal = journal["tip"]
        if self.tip == proposal:
            return False
        parents = self.git("rev-list", "--parents", "-n", "1", proposal).stdout.split()
        saved = journal["gate_state"]
        if self._read_state(proposal) != saved:
            return False
        if self.state is None:
            return (parents == [proposal] and saved["operation"] == "share" and saved["digest"] is None
                    and saved["published_data_ref"] is None)
        if len(parents) != 2 or parents[0] != proposal:
            return False
        parent = parents[1]
        prior = self.state if parent == self.tip else self._read_state(parent)
        expected = {**prior, **{key: saved[key] for key in ("attempt", "actor", "operation", "request_id")},
                    "status": "locked", "observed_data_ref": prior["published_data_ref"]}
        if prior["status"] != "unlocked" or saved != expected:
            return False
        for commit, required in ((parent, 0), (proposal, 1)):
            result = self.git("merge-base", "--is-ancestor", commit, self.tip, check=False)
            if result.returncode not in (0, 1):
                raise PlanError("cannot verify acquisition history; retain the local attempt")
            if result.returncode != required:
                return False
        return True

    def restore_attempt(self):
        self.confirmed_release = None
        self.unpublished_attempt = False
        path = self.state_dir / "plan-shared-attempt.json"
        try:
            if path.is_symlink():
                raise PlanError("shared recovery journal cannot be a symbolic link")
            journal = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PlanError("shared recovery needs this machine's saved attempt; no cross-machine takeover") from exc
        fields = {"schema_version", "attempt", "tip", "workspace_id", "control_id", "remote", "remote_fingerprint",
                  "operation", "request_id", "gate_state", "phase", "owned_local", "publication"}
        if not isinstance(journal, dict) or set(journal) != fields or type(journal.get("schema_version")) is not int or journal["schema_version"] != 1:
            raise PlanError("unsupported shared recovery journal; no gate was cleared")
        identity = {"workspace_id": self.workspace_id, "control_id": self.control_id, "remote": self.remote}
        fingerprints = {hashlib.sha256(url.encode()).hexdigest() for url in equivalent_transports(self.transport_url)}
        if (any(journal.get(key) != value for key, value in identity.items())
                or journal.get("remote_fingerprint") not in fingerprints):
            raise PlanError("shared recovery journal does not match this workspace and remote")
        if journal["phase"] not in ("acquiring", "read-sync", "operation", "publishing", "releasing"):
            raise PlanError("shared recovery journal phase is invalid")
        saved = self.validate(journal["gate_state"])
        if (saved["status"] != "locked" or saved["attempt"] != journal["attempt"]
                or saved["workspace_id"] != self.workspace_id or saved["control_id"] != self.control_id
                or saved["operation"] != journal["operation"] or saved["request_id"] != journal["request_id"]
                or not isinstance(journal["tip"], str) or not _HEX.fullmatch(journal["tip"])):
            raise PlanError("shared recovery journal has an invalid owner token")
        current = self.observe()
        if self._unpublished_attempt(journal):
            self.journal, self.lock_tip = journal, None
            self.unpublished_attempt = True
            return current if current is not None else saved
        immutable = {"attempt", "workspace_id", "control_id", "actor", "operation", "request_id", "observed_data_ref"}
        released = self._released_attempt(journal, immutable)
        if released is not None:
            self.journal, self.lock_tip = journal, None
            self.confirmed_release = released
            return released
        if current is None or any(current[key] != saved[key] for key in immutable):
            raise PlanError("shared recovery token does not own the observed remote gate")
        if current["status"] != "locked":
            raise PlanError("shared release is not a verified successor of the saved attempt")
        if self.tip != journal["tip"]:
            raise PlanError("shared gate tip changed; recovery cannot take over another attempt")
        self.journal = journal
        self.lock_tip = self.tip
        return current

    def check_owner(self):
        if self.lock_tip is None or self.remote_ref(COORDINATION_REF) != self.lock_tip:
            raise PlanError("shared gate ownership changed; stop without publication")

    def release(self, data_ref, digest):
        self.check_owner()
        if self.journal is not None:
            self.save_attempt(phase="releasing")
        state = {**self.state, "status": "unlocked", "published_data_ref": data_ref, "digest": digest}
        proposal = self.proposal(state, self.lock_tip)
        # A successful unlock push is confirmed even if the next owner acquires at once.
        # Acquisition still requires the proposal to remain the current tip.
        self.push(proposal, confirm_tip=False)
        self.tip, self.state, self.lock_tip = proposal, state, None
        (self.state_dir / "plan-shared-attempt.json").unlink(missing_ok=True)
