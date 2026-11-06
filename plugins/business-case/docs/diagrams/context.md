# business-case — C4 Context

Who the plugin serves and what it touches. One person plays both parts, the
proposer and the funder. The coach runs in that person's session. The judge
runs in a fresh context and is given only a brief that names its input files. The guard hooks stand between
both of them and the case folder.

```mermaid
%%{init: {'theme':'neutral'}}%%
graph TB
    user["The user<br/>proposer or funder, one role at a time"]
    coach["Coach session<br/>/business-case:build, inline"]
    judge["Judge sub-agent<br/>business-case:judge, fresh context"]
    hooks["Guard hooks<br/>write guard · dispatch guard · receipt"]
    casedir["Case folder<br/>business-cases/{slug}/"]
    prd["product plugin<br/>/product:explore; downstream reader"]

    user -->|"answers, reasons, decisions"| coach
    coach -->|"questions, findings"| user
    coach -->|"bc.py only"| casedir
    coach -->|"dispatch: the brief's text, nothing more"| hooks
    hooks -->|"passes only an exact brief"| judge
    judge -->|"reads the files the brief names"| casedir
    judge -->|"writes judge/reply-NNN.json"| hooks
    hooks -->|"allows that one write; records a receipt"| casedir
    hooks -.->|"refuses every other file-tool write"| casedir
    prd -.->|reads| casedir
```

The coach and the judge never share a context. Code writes every file in the
case folder: `bc.py`, and the receipt hook. The judge's reply and the
analysts' replies are the exceptions. ADR-000 is the overview; ADR-006 lists the routes the hooks do
not see.
