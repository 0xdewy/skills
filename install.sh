#!/usr/bin/env bash
set -euo pipefail

SKILL_SRC="$(dirname "$(realpath "$0")")/skill"

if [[ ! -f "$SKILL_SRC" ]]; then
    echo "error: skill script not found at $SKILL_SRC" >&2
    exit 1
fi

# Find the best writable directory on PATH
find_target() {
    local -a candidates=()

    case "$(uname -s)" in
        Linux)
            candidates=(
                "$HOME/.local/bin"
                "/usr/local/bin"
                "$HOME/bin"
            )
            ;;
        Darwin)
            candidates=(
                "/usr/local/bin"
                "$HOME/.local/bin"
                "$HOME/bin"
            )
            ;;
        MINGW*|MSYS*|CYGWIN*)
            candidates=(
                "$HOME/bin"
                "/usr/local/bin"
            )
            ;;
        *)
            candidates=(
                "$HOME/.local/bin"
                "/usr/local/bin"
                "$HOME/bin"
            )
            ;;
    esac

    for dir in "${candidates[@]}"; do
        mkdir -p "$dir" 2>/dev/null || continue
        if [[ -w "$dir" ]]; then
            echo "$dir"
            return 0
        fi
    done

    # Last resort: home bin regardless of writability (sudo handles it)
    echo "$HOME/.local/bin"
}

TARGET_DIR=$(find_target)
TARGET="$TARGET_DIR/skill"

cp "$SKILL_SRC" "$TARGET"
chmod +x "$TARGET"

echo "Installed skill to $TARGET"

# Check if the target dir is on PATH
if [[ ":$PATH:" != *":$TARGET_DIR:"* ]]; then
    echo ""
    echo "Note: $TARGET_DIR is not in your PATH."
    echo "Add it with:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "  # put this in ~/.bashrc or ~/.zshrc to persist"
fi

echo ""
echo "Try it:  skill list"
