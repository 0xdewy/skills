#!/usr/bin/env bash
set -euo pipefail

CENTRAL_STORE="${XDG_DATA_HOME:-$HOME/.local/share}/skills"
DRY_RUN=false
NON_INTERACTIVE=false
USE_SYMLINKS=true

declare -A TOOL_PATHS=(
    ["claude"]="$HOME/.claude/skills"
    ["opencode"]="$HOME/.config/agents/skills"
    ["hermes"]="$HOME/.local/share/hermes/skills"
)

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Interactive CLI to install AI coding skills locally.

OPTIONS:
    --non-interactive    Run without prompts (use with --install)
    --dry-run            Show what would be done without doing it
    -h, --help           Show this help message

EXAMPLES:
    $(basename "$0")                        # Interactive mode
    $(basename "$0") --dry-run              # Preview changes
    $(basename "$0") --install skill-creator  # Non-interactive install

EOF
}

log() { echo "[INFO] $*" >&2; }
warn() { echo "[WARN] $*" >&2; }
error() { echo "[ERROR] $*" >&2; exit 1; }

detect_tools() {
    local detected=()
    for tool in "${!TOOL_PATHS[@]}"; do
        local path="${TOOL_PATHS[$tool]}"
        if [[ -d "$path" ]] || [[ "$tool" == "hermes" ]]; then
            detected+=("$tool")
        fi
    done
    printf '%s\n' "${detected[@]}"
}

get_local_skills() {
    local skills_dir
    skills_dir="$(dirname "$(dirname "$0")")/skills"
    if [[ -d "$skills_dir" ]]; then
        find -L "$skills_dir" -maxdepth 1 -type d -not -name "skills" -not -name ".git" -print0 | while IFS= read -r -d '' dir; do
            basename "$dir"
        done
    fi
}

get_installed_skills() {
    if [[ ! -d "$CENTRAL_STORE" ]]; then
        return
    fi
    find "$CENTRAL_STORE" -maxdepth 1 -mindepth 1 -type d -print0 | while IFS= read -r -d '' dir; do
        basename "$dir"
    done
}

install_to_central() {
    local source="$1"
    local skill_name="$2"

    if [[ -L "$CENTRAL_STORE/$skill_name" ]]; then
        warn "Skill '$skill_name' already exists in central store (symlink), skipping"
        return 1
    fi

    if [[ -d "$CENTRAL_STORE/$skill_name" ]]; then
        warn "Skill '$skill_name' already exists in central store (directory), skipping"
        return 1
    fi

    if [[ -d "$source" ]]; then
        log "Copying $source to $CENTRAL_STORE/$skill_name"
        [[ "$DRY_RUN" == "true" ]] || cp -r "$source" "$CENTRAL_STORE/$skill_name"
    elif [[ "$source" =~ ^https?:// ]]; then
        log "Cloning $source to $CENTRAL_STORE/$skill_name"
        [[ "$DRY_RUN" == "true" ]] || git clone "$source" "$CENTRAL_STORE/$skill_name"
    else
        error "Invalid source: $source"
        return 1
    fi
}

create_symlinks() {
    local skill_name="$1"
    local -a created=()

    for tool in "${!TOOL_PATHS[@]}"; do
        local target_dir="${TOOL_PATHS[$tool]}"
        local link_path="$target_dir/$skill_name"
        local central_path="$CENTRAL_STORE/$skill_name"

        mkdir -p "$target_dir"

        if [[ -L "$link_path" ]]; then
            local existing_target
            existing_target=$(readlink "$link_path" 2>/dev/null || echo "")
            if [[ -z "$existing_target" ]]; then
                warn "Skill '$skill_name' has broken symlink for $tool, removing"
                rm "$link_path"
            elif [[ "$existing_target" == "$central_path" ]]; then
                warn "Skill '$skill_name' already symlinked for $tool"
            else
                warn "Skill '$skill_name' has existing symlink for $tool (points to $existing_target), skipping"
            fi
        elif [[ -d "$link_path" ]]; then
            warn "Skill '$skill_name' already exists as directory for $tool, skipping"
        else
            log "Symlinking $skill_name -> $link_path"
            [[ "$DRY_RUN" == "true" ]] || ln -s "$central_path" "$link_path"
            created+=("$tool")
        fi
    done

    printf '%s\n' "${created[@]:-}"
}

remove_skill() {
    local skill_name="$1"
    local force="${2:-false}"

    for tool in "${!TOOL_PATHS[@]}"; do
        local link_path="${TOOL_PATHS[$tool]}/$skill_name"
        if [[ -L "$link_path" ]]; then
            local target
            target=$(readlink "$link_path" 2>/dev/null || echo "")
            if [[ -z "$target" ]]; then
                log "Removing broken symlink: $link_path"
                [[ "$DRY_RUN" == "true" ]] || rm "$link_path"
            elif [[ "$target" == "$CENTRAL_STORE/$skill_name" ]] || [[ "$force" == "true" ]]; then
                log "Removing symlink: $link_path"
                [[ "$DRY_RUN" == "true" ]] || rm "$link_path"
            fi
        fi
    done

    if [[ -d "$CENTRAL_STORE/$skill_name" ]] || [[ -L "$CENTRAL_STORE/$skill_name" ]]; then
        if [[ "$force" == "true" ]]; then
            log "Removing from central store: $CENTRAL_STORE/$skill_name"
            [[ "$DRY_RUN" == "true" ]] || rm -rf "$CENTRAL_STORE/$skill_name"
        elif [[ -d "$CENTRAL_STORE/$skill_name" ]] && [[ ! -L "$CENTRAL_STORE/$skill_name" ]]; then
            warn "Skill '$skill_name' is a directory in central store, not removing (use --force to override)"
        fi
    fi
}

interactive_menu() {
    while true; do
        echo ""
        echo "=========================================="
        echo "         Skills Installer CLI"
        echo "=========================================="
        echo ""
        echo "Central store: $CENTRAL_STORE"
        echo ""
        echo "Options:"
        echo "  1) Install local skills"
        echo "  2) Install from GitHub URL"
        echo "  3) List installed skills"
        echo "  4) Remove installed skill"
        echo "  5) Show symlink status"
        echo "  0) Exit"
        echo ""
        echo -n "Select option: "
        read -r choice

        case "$choice" in
            1) install_local_menu ;;
            2) install_github_menu ;;
            3) list_installed ;;
            4) remove_skill_menu ;;
            5) show_symlinks ;;
            0) exit 0 ;;
            *) warn "Invalid option";;
        esac
    done
}

install_local_menu() {
    local repo_skills_dir
    repo_skills_dir="$(dirname "$(dirname "$0")")/skills"

    if [[ ! -d "$repo_skills_dir" ]]; then
        error "No local skills directory found at $repo_skills_dir"
        return
    fi

    echo ""
    echo "Available local skills:"
    echo ""

    local -a skills=()
    while IFS= read -r -d '' entry; do
        skills+=("$(basename "$entry")")
    done < <(find "$repo_skills_dir" -maxdepth 1 -mindepth 1 -print0 | sort -z)

    if [[ ${#skills[@]} -eq 0 ]]; then
        warn "No skills found in $repo_skills_dir"
        return
    fi

    local install_skills_array=()
    select skill in "${skills[@]}" "All" "Back to main menu"; do
        if [[ "$skill" == "Back to main menu" ]]; then
            return
        elif [[ "$skill" == "All" ]]; then
            install_skills_array=("${skills[@]}")
            break
        elif [[ -n "$skill" ]]; then
            install_skills_array=("$skill")
            break
        else
            warn "Invalid selection"
        fi
    done

    if [[ ${#install_skills_array[@]} -eq 0 ]]; then
        return
    fi

    echo ""
    echo "Installing to tools:"
    for tool in "${!TOOL_PATHS[@]}"; do
        echo "  - $tool: ${TOOL_PATHS[$tool]}"
    done
    echo ""

    local confirmed
    echo -n "Proceed with installation? [Y/n] "
    read -r confirmed
    if [[ "$confirmed" =~ ^[Nn]$ ]]; then
        return
    fi

    mkdir -p "$CENTRAL_STORE" || { error "Failed to create $CENTRAL_STORE"; return 1; }

    for skill_name in "${install_skills_array[@]}"; do
        local source="$repo_skills_dir/$skill_name"
        if [[ ! -d "$source" ]]; then
            error "Skill directory not found: $source"
            continue
        fi

        log "Installing '$skill_name'..."
        install_to_central "$source" "$skill_name" || continue
        local created
        created=$(create_symlinks "$skill_name")
        log "Installed '$skill_name' to: ${created:-all tools}"
    done

    echo ""
    log "Done!"
}

install_github_menu() {
    echo ""
    echo -n "Enter GitHub repo URL (e.g., https://github.com/user/repo): "
    read -r github_url

    if [[ ! "$github_url" =~ ^https?://github\.com/ ]]; then
        error "Invalid GitHub URL (must start with https://github.com/)"
        return
    fi

    local skill_name
    skill_name=$(basename "$github_url" .git)
    if [[ -z "$skill_name" ]]; then
        error "Could not determine skill name from URL"
        return
    fi

    local full_url="$github_url"
    if [[ "$github_url" != *".git" ]]; then
        full_url="${github_url}.git"
    fi

    echo ""
    log "Installing '$skill_name' from GitHub..."
    mkdir -p "$CENTRAL_STORE" || { error "Failed to create $CENTRAL_STORE"; return 1; }
    install_to_central "$full_url" "$skill_name" || return

    local created
    created=$(create_symlinks "$skill_name")
    log "Installed '$skill_name' to: ${created:-all tools}"
}

list_installed() {
    echo ""
    echo "Installed skills in central store:"
    echo ""

    if [[ ! -d "$CENTRAL_STORE" ]]; then
        warn "No skills installed"
        return
    fi

    local count=0
    while IFS= read -r -d '' skill_dir; do
        local skill_name
        skill_name=$(basename "$skill_dir")
        echo "  - $skill_name"
        ((count++))
    done < <(find "$CENTRAL_STORE" -maxdepth 1 -mindepth 1 -type d -print0 | sort -z)

    if [[ $count -eq 0 ]]; then
        warn "No skills installed"
    fi
}

remove_skill_menu() {
    echo ""
    echo "Select skill to remove:"
    echo ""

    local -a installed=()
    while IFS= read -r -d '' skill_dir; do
        installed+=("$(basename "$skill_dir")")
    done < <(find "$CENTRAL_STORE" -maxdepth 1 -mindepth 1 -type d -print0 | sort -z)

    if [[ ${#installed[@]} -eq 0 ]]; then
        warn "No skills installed"
        return
    fi

    select skill in "${installed[@]}" "Back to main menu"; do
        if [[ "$skill" == "Back to main menu" ]]; then
            return
        elif [[ -n "$skill" ]]; then
            remove_skill "$skill"
            log "Removed '$skill'"
            break
        else
            warn "Invalid selection"
        fi
    done
}

show_symlinks() {
    echo ""
    echo "Symlink status:"
    echo ""

    local found=0
    while IFS= read -r -d '' skill_dir; do
        local skill_name
        skill_name=$(basename "$skill_dir")
        found=1
        echo "Skill: $skill_name"
        echo "  Central: $CENTRAL_STORE/$skill_name"
        for tool in "${!TOOL_PATHS[@]}"; do
            local link_path="${TOOL_PATHS[$tool]}/$skill_name"
            if [[ -L "$link_path" ]]; then
                local target
                target=$(readlink "$link_path" 2>/dev/null || echo "broken")
                echo "  $tool: $link_path -> $target"
            else
                echo "  $tool: not linked"
            fi
        done
        echo ""
    done < <(find "$CENTRAL_STORE" -maxdepth 1 -mindepth 1 -type d -print0 | sort -z)

    if [[ $found -eq 0 ]]; then
        warn "No skills installed"
    fi
}

install_skill() {
    local skill_path="$1"
    local skill_name
    skill_name=$(basename "$skill_path")

    mkdir -p "$CENTRAL_STORE" || { error "Failed to create $CENTRAL_STORE"; return 1; }
    install_to_central "$skill_path" "$skill_name" || return
    create_symlinks "$skill_name"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --non-interactive)
                NON_INTERACTIVE=true
                shift
                ;;
            --install)
                shift
                if [[ $# -eq 0 ]]; then
                    error "--install requires a skill path or URL"
                fi
                install_skill "$1"
                exit 0
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
}

main() {
    mkdir -p "$CENTRAL_STORE" || { error "Failed to create $CENTRAL_STORE"; exit 1; }

    if [[ "$NON_INTERACTIVE" == "true" ]]; then
        error "Non-interactive mode requires --install <path>"
    fi

    if [[ ! -t 0 ]]; then
        error "Not running in terminal. Use --non-interactive --install <path>"
    fi

    interactive_menu
}

parse_args "$@"
main