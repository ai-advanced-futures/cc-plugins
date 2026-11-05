# Reference: Check prose with Vale

Vale (https://vale.sh) is a command-line linter for prose. The `vale-cli/Google` package (https://github.com/vale-cli/Google, MIT license) holds 37 rules from the Google developer documentation style guide. The Vale project makes this package. Google does not.

Vale finds errors that a pattern can match: headings that are not in sentence case, a missing serial comma, "please", Latin abbreviations, words from the word list, exclamation marks, and "will". It does not check tone, the order of a procedure, or link text.

## Check that Vale is installed

Run the script in this skill. It reads the operating system, the Linux distribution, and the package managers on `PATH`. It prints one install command and the reason for it. It installs nothing.

```bash
bash <skill-dir>/scripts/vale-install-command.sh
```

When line 1 is `vale --version`, Vale is installed. Otherwise, give the user the command from line 1 and the reason from line 2. Do not run the command yourself, because it can need `sudo` or a password.

When the shell cannot run bash, such as PowerShell on Windows, pick the first row that matches:

| System | Command |
| --- | --- |
| Windows with winget | `winget install -e --id errata-ai.Vale` |
| Windows with Chocolatey | `choco install vale` |
| macOS with Homebrew | `brew install vale` |
| Arch Linux | `sudo pacman -S vale` |
| Linux with Homebrew | `brew install vale` |
| Linux with snap | `sudo snap install vale` |
| Debian or Ubuntu, after you add the pkg.haus APT archive | `sudo apt install vale` |
| Docker | `docker pull jdkato/vale` |
| Other | download an archive from https://github.com/vale-cli/vale/releases |

Source: https://docs.vale.sh/topics/installation

## Configure a repository

Put this file at the root of the repository as `.vale.ini`. The pinned URL makes each run use the same rules.

```ini
StylesPath = .github/styles
MinAlertLevel = suggestion

Packages = https://github.com/vale-cli/Google/releases/download/v0.7.1/Google.zip

[*.md]
BasedOnStyles = Google
```

Then download the rules:

```bash
vale sync
```

Add `.github/styles/Google/` to `.gitignore`, because `vale sync` makes it again.

## Run a check

```bash
vale README.md docs/
vale --output=line README.md
```

`--output=line` prints one line for each alert: `file:line:column:rule:message`.

## Read the result

| Level | Action |
| --- | --- |
| error | Fix it. |
| warning | Fix it, or keep the text when the project rule or the user asks for it. |
| suggestion | Fix it when the fix does not change the meaning. |

To turn off a rule for a project, add a line under `[*.md]`, for example `Google.Passive = NO`.
