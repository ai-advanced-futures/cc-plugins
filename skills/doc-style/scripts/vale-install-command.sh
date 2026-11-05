#!/usr/bin/env bash
# Print the command that installs Vale on this machine. It installs nothing.
#
# Output: line 1 is the command, line 2 is a comment that tells why.
# Exit 0 when Vale is already installed or a command was found.
#
# Sources: https://docs.vale.sh/topics/installation
# Test hooks: VALE_DETECT_UNAME and VALE_DETECT_OS_RELEASE replace
# `uname -s` and /etc/os-release.

set -u

has() { command -v "$1" >/dev/null 2>&1; }

say() {
  printf '%s\n# %s\n' "$1" "$2"
  exit 0
}

releases='https://github.com/vale-cli/vale/releases'

if has vale; then
  say "vale --version" "Vale is already installed: $(vale --version 2>/dev/null)"
fi

kernel="${VALE_DETECT_UNAME:-$(uname -s 2>/dev/null)}"

case "$kernel" in
  Darwin)
    has brew && say "brew install vale" "macOS with Homebrew."
    say "open $releases" "macOS without Homebrew: download the macOS archive, extract it, and put vale on PATH."
    ;;

  MINGW* | MSYS* | CYGWIN* | Windows_NT)
    has winget && say "winget install -e --id errata-ai.Vale" "Windows with winget."
    has choco && say "choco install vale" "Windows with Chocolatey."
    say "start $releases" "Windows without winget or Chocolatey: download the Windows archive and put vale.exe on PATH."
    ;;

  Linux)
    os_release="${VALE_DETECT_OS_RELEASE:-/etc/os-release}"
    field() { sed -n "s/^$1=//p" "$os_release" 2>/dev/null | tr -d '"'\'; }
    family=" $(field ID) $(field ID_LIKE) "

    if [[ $family == *" arch "* ]] && has pacman; then
      say "sudo pacman -S vale" "Arch Linux: Vale is in the official repositories."
    fi
    has brew && say "brew install vale" "Linux with Homebrew, which follows Vale releases closely."
    has snap && say "sudo snap install vale" "Linux with snap."
    if [[ $family == *" debian "* || $family == *" ubuntu "* ]] && has apt; then
      say "sudo apt install vale" "Debian or Ubuntu: first add the pkg.haus APT archive (https://pkg.haus), because the default archives do not have a current Vale."
    fi
    has docker && say "docker pull jdkato/vale" "Linux with Docker only: run Vale in a container."
    say "xdg-open $releases" "Linux without a supported package manager: download the Linux archive (amd64 or arm64) and put vale on PATH."
    ;;
esac

say "open $releases" "Unknown system ($kernel): download the archive for your platform and put vale on PATH."
