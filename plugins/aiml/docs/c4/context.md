# C4 Context Diagram — aiml Plugin

## System Context

```mermaid
C4Context
    title aiml Plugin — System Context

    Person(engineer, "Software Engineer", "Builds a feature that needs AI or ML. Needs no data science background.")

    System(aiml, "aiml Plugin", "Guides the engineer from the choice of approach to production MLOps. Skills ask questions; agents write the files.")

    System_Ext(superpowers, "superpowers Plugin (optional)", "Runs the plan of /aiml:plan with executing-plans.")
    System_Ext(context7, "context7 MCP server (optional)", "Gives the current API of each library to scaffold-agent.")
    System_Ext(hf, "HuggingFace Hub", "Models, PEFT/LoRA configs and datasets that the starter code uses.")
    System_Ext(mlflow, "MLflow / W&B", "Experiment tracking and model registry that the ops pipeline names.")

    Rel(engineer, aiml, "Runs /aiml:* skills and answers their questions")
    Rel(superpowers, aiml, "Runs the tasks of docs/aiml/plan.md")
    Rel(aiml, context7, "Reads library API (optional)")
    Rel(aiml, hf, "Names models and configs")
    Rel(aiml, mlflow, "Names tools in the ops pipeline")
```

## Key Relationships

| Actor | Interaction |
|---|---|
| Software Engineer | Runs the `/aiml:*` skills and answers the questions of each skill |
| superpowers (optional) | Runs `docs/aiml/plan.md` with `superpowers:executing-plans`. Without it, the engineer does the tasks in order |
| context7 (optional) | `scaffold-agent` reads the current API of each library from it. Without it, the agent writes the code from the spec and the plan |
| HuggingFace Hub | The starter code and the specs name its models and datasets. The plugin makes no network call |
| MLflow / W&B | The ops pipeline names them for tracking and the registry. The plugin makes no network call |
