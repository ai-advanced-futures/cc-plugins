"""Build a synthetic knowledge graph for the tests and the evaluation of scripts/kq.py.

Each name, date and number here is invented. The subject is a community garden that does not exist.
The graph has the shapes that make an ask hard: a question that uses other words than its page, two
sources that disagree, a later correction, and a question that is still open.
Each write goes through knowledge_graph.py. `kq-questions.yaml` holds the questions for this graph.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SAVE = Path(__file__).resolve().parents[1] / "scripts" / "knowledge_graph.py"

# (type, title, description, extra --set values, text)
PAGES = [
    ("Source", "Minutes of the March meeting", "The minutes of the garden committee, March 2031.",
     ["resource=raw/minutes-2031-03.md", "source_kind=transcript", "source_published='2031-03-14'"],
     "The committee met on 14 March 2031. Ines Okoro led the meeting.\n\n"
     "The committee set the plot fee at 40 florins for each season. Nine members voted for it and two "
     "voted against it.\n\n"
     "The committee did not decide who repairs the east fence. Tomas Vell said that the landowner must "
     "pay for it. The item moved to the next meeting."),
    ("Source", "Treasurer report of June", "The report of the treasurer for the first half of 2031.",
     ["resource=raw/treasurer-2031-06.md", "source_kind=report", "source_published='2031-06-30'"],
     "The treasurer, Ruth Abara, wrote this report on 30 June 2031.\n\n"
     "The garden has 62 plots. 55 plots are let and 7 are empty.\n\n"
     "The report gives the plot fee as 45 florins. This is not the value of the March minutes. The "
     "report does not say when the fee changed.\n\n"
     "The income from fees was 2,475 florins. The water bill was 610 florins."),
    ("Source", "Notice of the fee correction", "A notice that corrects the fee in the treasurer report.",
     ["resource=raw/notice-2031-07.md", "source_kind=article", "source_published='2031-07-09'"],
     "The committee sent this notice on 9 July 2031.\n\n"
     "The fee in the treasurer report of June is wrong. The plot fee is 40 florins, as the committee "
     "set it in March. The treasurer used the fee of a draft that the committee did not pass.\n\n"
     "The income line of the report is not corrected yet. The treasurer will send a new report in "
     "September."),
    ("Concept", "Plot fee", "The sum that a member pays for one plot in one season.",
     ["aliases=[seasonal rent, membership charge]"],
     "The plot fee is the sum that a member pays for one plot in one season.\n\n"
     "The committee set it at 40 florins on 14 March 2031. The treasurer report of June gives 45 "
     "florins. A notice of 9 July 2031 says that 45 is wrong and that 40 is the fee.\n\n"
     "A member who joins after 1 August pays half of the fee."),
    ("Concept", "Water allowance", "The volume of water that one plot can use in one week.",
     ["aliases=[irrigation limit]"],
     "Each plot can use 300 litres of water in one week from the shared tank.\n\n"
     "The limit applies from May to September. In the other months there is no limit.\n\n"
     "The allowance depends on the tank: when the level is below one third, the warden cuts the "
     "allowance to 150 litres."),
    ("Concept", "Waiting list", "The list of persons who asked for a plot and do not have one.",
     [],
     "A person who asks for a plot goes on the waiting list. The warden offers an empty plot to the "
     "first person on the list.\n\n"
     "On 30 June 2031 the list had 18 names. Only the warden counted them, and no second person "
     "confirmed the count.\n\n"
     "A person who refuses two offers leaves the list."),
    ("Entity", "Garden committee", "The elected group that runs the garden.",
     ["entity_kind=organization"],
     "The garden committee has 11 members. The members of the garden elect it each January.\n\n"
     "Ines Okoro is the chair. Ruth Abara is the treasurer. Tomas Vell is the warden.\n\n"
     "The committee sets the plot fee and the water allowance. A change needs 6 votes."),
    ("Entity", "Tomas Vell", "The warden of the garden.",
     ["entity_kind=person"],
     "Tomas Vell is the warden of the garden since January 2030.\n\n"
     "The warden keeps the waiting list, offers the empty plots and reads the level of the tank each "
     "Monday.\n\n"
     "The warden cannot change the plot fee."),
    ("Entity", "Ruth Abara", "The treasurer of the garden.",
     ["entity_kind=person"],
     "Ruth Abara is the treasurer of the garden since January 2031.\n\n"
     "The treasurer collects the fees, pays the water bill and writes a report in June and in "
     "December."),
    ("Synthesis", "How a person gets a plot", "The steps from the first request to the first season.",
     [],
     "A person asks the warden for a plot and goes on the waiting list. When a plot is empty, the "
     "warden offers it to the first person on the list.\n\n"
     "The person pays the plot fee to the treasurer and signs the rules. Then the warden gives the key "
     "of the gate.\n\n"
     "The time on the list is not recorded. The warden estimates it at one to two seasons."),
    ("OpenQuestion", "Who repairs the east fence", "No source says who pays for the repair of the east fence.",
     [],
     "The east fence fell in February 2031. It is not decided who repairs it.\n\n"
     "The warden says that the landowner must pay. The lease of the land is not in the graph, so this "
     "is not confirmed.\n\n"
     "The committee moved the item from the March meeting to the next meeting. No later minutes are "
     "in the graph."),
    ("OpenQuestion", "What the true fee income was", "The income from fees in the first half of 2031 is not settled.",
     [],
     "The treasurer report gives 2,475 florins. That is 55 plots at 45 florins.\n\n"
     "The notice of 9 July says that the fee is 40 florins. At 40 florins, 55 plots give 2,200 "
     "florins. No source gives the corrected income.\n\n"
     "A new report is due in September 2031."),
]

# (title of a page, title of the page that it names as a source)
LINKS = [
    ("Plot fee", "Minutes of the March meeting"),
    ("Plot fee", "Treasurer report of June"),
    ("Plot fee", "Notice of the fee correction"),
    ("Water allowance", "Garden committee"),
    ("Waiting list", "Treasurer report of June"),
    ("Waiting list", "Tomas Vell"),
    ("Garden committee", "Minutes of the March meeting"),
    ("How a person gets a plot", "Waiting list"),
    ("How a person gets a plot", "Plot fee"),
    ("How a person gets a plot", "Tomas Vell"),
    ("Who repairs the east fence", "Minutes of the March meeting"),
    ("Who repairs the east fence", "Tomas Vell"),
    ("What the true fee income was", "Treasurer report of June"),
    ("What the true fee income was", "Notice of the fee correction"),
    ("What the true fee income was", "Plot fee"),
]


def run(root, *args, stdin=None) -> str:
    result = subprocess.run([sys.executable, str(SAVE), "--root", str(root), *args], input=stdin,
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"knowledge_graph.py {' '.join(args)} failed:\n{result.stdout}{result.stderr}")
    return result.stdout


def build(root: Path) -> dict:
    """Make the graph in `root`. Returns the bundle path of each page by its title."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    run(root, "init")
    paths = {}
    for kind, title, description, sets, text in PAGES:
        args = ["new", kind, "--title", title, "--description", description]
        for value in sets:
            args += ["--set", value]
        printed = run(root, *args).strip().splitlines()[-1]
        paths[title] = "/" + "/".join(Path(printed).parts[-2:])
        run(root, "body", paths[title], "--file", "-", stdin=text + "\n")
    for page, source in LINKS:
        run(root, "link", paths[page], "sources", paths[source])
    run(root, "regen")
    return paths


if __name__ == "__main__":
    for title, path in build(Path(sys.argv[1])).items():
        print(f"knowledge:{path}\t{title}")
