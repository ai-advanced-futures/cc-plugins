# shellcheck shell=bash
# codex-home.sh — sourced library. Resolves the Codex home for relay's codex children.
# Spec: docs/superpowers/specs/2026-09-26-relay-codex-state-isolation-design.md §5.1.
#
# relay_codex_home_resolve
#   No arguments. Prints the absolute path on stdout and returns 0.
#   On a refusal it prints one message on stderr and returns 1.
#   Reads RELAY_CODEX_HOME (default: $HOME/.relay/codex-home), HOME and CODEX_SQLITE_HOME.
#   Creates the directory (mode 700) when it is missing, because codex exits when
#   CODEX_HOME does not exist.
#   It does not check authentication. The adapter reports an auth failure on the turn,
#   and a check here would copy the adapter's auth rules.
#
# This file sets no shell options. The caller keeps its own `set` flags.

# Collapse repeated slashes, remove "." segments and trailing slashes, so
# "$HOME//./.codex/" compares equal to "$HOME/.codex".
_relay_codex_home_tidy() {
    local p="$1" slash="/"
    while [ "${p#*//}" != "$p" ] || [ "${p#*/./}" != "$p" ]; do
        p="${p//\/\//$slash}"
        p="${p//\/.\//$slash}"
    done
    case "$p" in
        */.) p="${p%/.}/" ;;
    esac
    while [ "${#p}" -gt 1 ] && [ "${p%/}" != "$p" ]; do
        p="${p%/}"
    done
    printf '%s' "$p"
}

# Return 0 when a tidy absolute path names the desktop home "$2/.codex". It compares
# directories by device and inode (test -ef), not by text, so a symlink, a symlinked parent,
# or another letter case on a disk that ignores case still matches. It creates nothing.
#   - The path exists: it is the desktop home when it is the same directory.
#   - The path does not exist yet: mkdir -p would create it, so it is the desktop home when
#     its parent is the home directory and its name is ".codex" in any letter case. On a disk
#     that keeps case this also refuses "~/.CODEX", which is a safe false refusal.
_relay_codex_home_is_desktop() {
    local path="$1" home="$2" parent name
    if [ -e "$path" ] && [ -e "$home/.codex" ] && [ "$path" -ef "$home/.codex" ]; then
        return 0
    fi
    parent="${path%/*}"
    [ -n "$parent" ] || parent="/"
    name="$(printf '%s' "${path##*/}" | tr '[:upper:]' '[:lower:]')"
    [ "$name" = ".codex" ] && [ -d "$parent" ] && [ -d "$home" ] && [ "$parent" -ef "$home" ]
}

relay_codex_home_resolve() {
    local home="${HOME:-}"
    if [ -z "$home" ]; then
        echo "relay: HOME is not set, so the Codex home cannot be resolved. Set HOME or RELAY_CODEX_HOME." >&2
        return 1
    fi
    home="$(_relay_codex_home_tidy "$home")"
    local path="${RELAY_CODEX_HOME:-$home/.relay/codex-home}"
    case "$path" in
        \~) path="$home" ;;
        \~/*) path="$home/${path#\~/}" ;;
        /*) ;;
        *)
            echo "relay: RELAY_CODEX_HOME must be an absolute path (got: $path)." >&2
            return 1
            ;;
    esac
    path="$(_relay_codex_home_tidy "$path")"
    # mkdir -p creates each segment as written, so "a/new/../.codex" creates "a/new".
    case "$path/" in
        */../*)
            echo "relay: RELAY_CODEX_HOME must not hold a '..' segment (got: $path)." >&2
            return 1
            ;;
    esac

    local desktop="$home/.codex"
    local refusal="relay: the Codex home for relay must not be the desktop home ($desktop). Set RELAY_CODEX_HOME to a different directory, or unset it to use $home/.relay/codex-home."
    # Every refusal runs before mkdir, so a refusal never creates a directory.
    if [ "$path" = "$desktop" ] || _relay_codex_home_is_desktop "$path" "$home"; then
        echo "$refusal" >&2
        return 1
    fi
    if [ -n "${CODEX_SQLITE_HOME:-}" ]; then
        echo "relay: CODEX_SQLITE_HOME is set ($CODEX_SQLITE_HOME). Codex would keep its state database outside $path. Unset CODEX_SQLITE_HOME for relay runs." >&2
        return 1
    fi
    if [ -e "$path" ] && [ ! -d "$path" ]; then
        echo "relay: the Codex home $path exists and is not a directory." >&2
        return 1
    fi
    if [ ! -d "$path" ]; then
        ( umask 077 && mkdir -p "$path" ) || {
            echo "relay: cannot create the Codex home $path." >&2
            return 1
        }
    fi

    local abs
    abs="$(cd -P "$path" && pwd)" || {
        echo "relay: cannot open the Codex home $path." >&2
        return 1
    }
    # A last check after mkdir: the directory that now exists must not be the desktop home.
    if [ -e "$desktop" ] && [ "$abs" -ef "$desktop" ]; then
        echo "$refusal" >&2
        return 1
    fi

    if [ -f "$abs/config.toml" ]; then
        if grep -Eq '^[[:space:]]*sqlite_home[[:space:]]*=' "$abs/config.toml"; then
            echo "relay: $abs/config.toml sets sqlite_home. Codex would keep its state database outside $abs. Remove the sqlite_home key." >&2
            return 1
        fi
        if grep -Fq "$desktop" "$abs/config.toml"; then
            echo "relay: warning: $abs/config.toml names the desktop home ($desktop). An MCP server entry that sets CODEX_HOME there sends its state back to the desktop home. Do not copy ~/.codex/config.toml." >&2
        fi
    fi
    printf '%s\n' "$abs"
}
