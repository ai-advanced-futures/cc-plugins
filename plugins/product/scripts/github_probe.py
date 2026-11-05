#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""github_probe.py — the five GitHub questions the wiki never tested.

The spec takes the safe path for each one until this probe answers it (D37).
Run it against a TEST Project and a TEST repository: it makes issues, a
milestone, a Status option, and a sub-issue link, and it does not remove them.
Put its output in the pull request.

    uv run scripts/github_probe.py --repo acme/prd-probe --owner acme \
        --project 7 --confirm
"""
import argparse
import json
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    key: str
    asks: str
    safe_path: str


QUESTIONS = (
    Question("option-ids",
             "Does a change of the Status options keep the option IDs of the "
             "items?",
             "apply reads the field list again after any change of the "
             "options and never keeps an option ID across it."),
    Question("cycle",
             "Does GitHub refuse a cycle in blockedBy?",
             "Rule E6 refuses a cycle in the bundle, so the push never "
             "carries one."),
    Question("sub-issue-limits",
             "What are the real limits for sub-issues?",
             "github plan refuses a parent with more than 100 children, the "
             "documented limit."),
    Question("status-actor",
             "Which field gives the login of the person who last changed the "
             "Status value of an item?",
             "pull reads project_item.status_actor and falls back to the gh "
             "login with the note `(pulled from GitHub)`."),
    Question("closed-actor",
             "Which event gives the login of the person who closed an issue?",
             "pull reads closed_by and falls back to the gh login."),
)


def gh(args, allow_fail=False):
    done = subprocess.run(["gh", *args], capture_output=True, text=True)
    if done.returncode != 0 and not allow_fail:
        raise SystemExit(f"`gh {' '.join(args)}` failed: {done.stderr.strip()}")
    return done


def ask_option_ids(args) -> str:
    """The option IDs as they stand now, and the step that answers the question.

    The question asks what a *change* of the options does to the IDs. This
    function only reads them, so it cannot answer it: a read before a read
    always reports the same IDs, and a `same: true` from two reads would read
    as the answer `a change keeps the IDs`, which nothing here tested.
    """
    before = _status_options(args)
    return json.dumps(before, indent=2, sort_keys=True) + (
        "\nThe IDs above are one read. To answer the question, rename one "
        "option with the `updateProjectV2SingleSelectField` mutation, run "
        "this probe again, and compare the two blocks: an ID that changed "
        "means apply must read the field list again after any change of the "
        "options.")


def _status_options(args) -> dict:
    data = json.loads(gh(["project", "field-list", str(args.project),
                          "--owner", args.owner, "--format", "json"]).stdout)
    for field in data.get("fields", []):
        if field.get("name") == "Status":
            return {option["name"]: option["id"]
                    for option in field.get("options", [])}
    return {}


def ask_cycle(args) -> str:
    return ("Make two issues in the test repository, add each as blockedBy of "
            "the other with `gh api graphql -f query=mutation{addBlockedBy}`, "
            "and record whether the second call gives an error.")


def ask_sub_issue_limits(args) -> str:
    return ("Add sub-issues to one parent until the API refuses, and record "
            "the count and the message.")


def ask_status_actor(args) -> str:
    data = gh(["api", "graphql", "-f", "query=" + STATUS_ACTOR_QUERY,
               "-f", f"owner={args.owner}", "-F", f"number={args.project}"],
              allow_fail=True)
    return data.stdout or data.stderr


def ask_closed_actor(args) -> str:
    data = gh(["api", f"repos/{args.repo}/issues/1/timeline"], allow_fail=True)
    return data.stdout[:2000] or data.stderr


STATUS_ACTOR_QUERY = """
query($owner: String!, $number: Int!) {
  organization(login: $owner) {
    projectV2(number: $number) {
      items(first: 5) {
        nodes {
          fieldValues(first: 10) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name updatedAt creator { login }
              }
            }
          }
        }
      }
    }
  }
}
"""

# The calls that `github apply` and `ghsnapshot.fetch` make with a name or
# a shape that no source this build read confirmed. Each one is marked
# [inferred] in the code. Run each by hand on the test Project and write the
# result into the pull request.
UNTESTED_CALLS = (
    ("blockedBy",
     "ghsnapshot.ISSUE_QUERY reads `blockedBy(first: 50) { totalCount nodes "
     "{ number id } }` on an Issue. Run the query on an issue with one "
     "blocker and check that the field and its shape exist."),
    ("addBlockedBy",
     "apply sends `addBlockedBy(input: {issueId, blockingIssueId})`. Run it "
     "on two test issues and check the input field names."),
    ("removeBlockedBy",
     "apply sends `removeBlockedBy(input: {issueId, blockingIssueId})`. Run "
     "it on the pair above and check that the link is gone."),
    ("replaceParent",
     "apply moves a child with `addSubIssue(input: {issueId, subIssueId, "
     "replaceParent: true})`. Move a sub-issue to a second parent and check "
     "that the first parent lost it."),
    ("removeSubIssue",
     "apply drops a parent with `removeSubIssue(input: {issueId, "
     "subIssueId})`. Run it and check that the child has no parent."),
    ("item-list date key",
     "ghsnapshot._cards reads the planned dates as the keys `Planned start` "
     "and `Planned end` of `gh project item-list --format json`. Set a date "
     "on one card and check the key that item-list gives."),
    ("options[] list",
     "apply sends the Status options as `-f 'options[][name]=Backlog' -f "
     "'options[][color]=GRAY' -f 'options[][description]='`, one group for "
     "each option. Make a single-select field on a test Project this way "
     "and check that it has every option, in order."),
    ("addProjectV2ItemById twice",
     "apply adds an issue to the Project when the snapshot shows no card. "
     "Add one issue twice and check that the second call gives the same "
     "card and no error."),
)

ANSWERS = {
    "option-ids": ask_option_ids,
    "cycle": ask_cycle,
    "sub-issue-limits": ask_sub_issue_limits,
    "status-actor": ask_status_actor,
    "closed-actor": ask_closed_actor,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="github_probe.py",
        description="Answer the five untested GitHub questions of the OKF "
                    "roadmap design. Run it against a test Project and a "
                    "test repository only: it writes and does not clean up.")
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--owner", required=True,
                        help="the Project owner login")
    parser.add_argument("--project", required=True, type=int,
                        help="the Project number")
    parser.add_argument("--confirm", action="store_true",
                        help="run against the test Project named above")
    args = parser.parse_args(argv)
    if not args.confirm:
        print("This probe writes to the Project. Add --confirm when the "
              "Project and the repository are test ones.", file=sys.stderr)
        return 2
    for question in QUESTIONS:
        print(f"## {question.key}\n\n{question.asks}\n")
        print(f"Safe path until the answer: {question.safe_path}\n")
        print("```")
        print(ANSWERS[question.key](args))
        print("```\n")
    print("## Calls to run by hand\n")
    for name, check in UNTESTED_CALLS:
        print(f"- [ ] **{name}**: {check}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
