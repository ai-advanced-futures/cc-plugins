---
name: verify
description: Verify the Sofa watcher launcher without starting or restarting a real session.
---

# Verify the watcher launcher

Use this recipe for `scripts/bg-watch`. For another Sofa change, choose its own runtime surface.

1. Create an isolated temporary folder under the job's temporary directory. Put a fake executable named `claude` in its `bin` folder. It must print its arguments and the parsed JSON after `--settings`, then exit with a chosen code. It must not call a real Claude binary.
2. From the Sofa plugin folder, run the real `scripts/bg-watch check` with Python 3 in a fresh environment. Set PATH to only the fake folder and system command folders. Capture stdout and the exit code.
3. Confirm the observed arguments: `claude-sonnet-5-5`, `--permission-mode auto`, `--permission-prompts none`, and `/bg-watch check`. The JSON must keep `$defaults`, set `classifyAllShell` to true, and disable bypass mode.
4. Make the fake exit 7. Run the same command and confirm exit 7 with only one launch. Then pass an extra `--permission-mode bypassPermissions` argument to the launcher: it must give usage text and exit 2 without calling the fake.
5. Report these observations inline. This verifies the launcher, not the live safety classifier or the delivery of `retry`. Do not run the watcher against real sessions, change a crontab, or change user settings as a verification step.
