#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"

FRAMEWORK="unknown"
BUILD_TOOL="unknown"
PKG_MGR="npm"
DEV_CMD="npm run dev"
HAS_TS=false
IS_NATIVE=false
ROUTING="unknown"

if [ -f "package.json" ]; then
    DEPS=$(cat package.json | tr -d '\n' | sed 's/.*"dependencies":{[^}]*}//; s/.*"devDependencies":{[^}]*}//' || true)
    ALL_DEPS=$(cat package.json 2>/dev/null)

    if echo "$ALL_DEPS" | grep -q '"expo"'; then
        FRAMEWORK="react"
        BUILD_TOOL="expo"
        DEV_CMD="npx expo start"
        IS_NATIVE=true
    elif echo "$ALL_DEPS" | grep -q '"react-native"'; then
        FRAMEWORK="react"
        BUILD_TOOL="react-native"
        DEV_CMD="npx react-native start"
        IS_NATIVE=true
    elif echo "$ALL_DEPS" | grep -q '"next"'; then
        FRAMEWORK="react"
        BUILD_TOOL="next"
        DEV_CMD="npx next dev"
        ROUTING="file-based"
    elif echo "$ALL_DEPS" | grep -q '"@remix-run'; then
        FRAMEWORK="react"
        BUILD_TOOL="remix"
        DEV_CMD="npx remix dev"
    elif echo "$ALL_DEPS" | grep -q '"@sveltejs/kit"'; then
        FRAMEWORK="svelte"
        BUILD_TOOL="sveltekit"
        DEV_CMD="npx vite dev"
        ROUTING="file-based"
    elif echo "$ALL_DEPS" | grep -q '"svelte"'; then
        FRAMEWORK="svelte"
        BUILD_TOOL="vite"
        DEV_CMD="npx vite"
    elif echo "$ALL_DEPS" | grep -q '"vue"'; then
        if echo "$ALL_DEPS" | grep -q '"nuxt"'; then
            FRAMEWORK="vue"
            BUILD_TOOL="nuxt"
            DEV_CMD="npx nuxt dev"
            ROUTING="file-based"
        else
            FRAMEWORK="vue"
            BUILD_TOOL="vite"
            DEV_CMD="npx vite"
        fi
    elif echo "$ALL_DEPS" | grep -q '"@angular/core"'; then
        FRAMEWORK="angular"
        BUILD_TOOL="angular"
        DEV_CMD="npx ng serve"
    elif echo "$ALL_DEPS" | grep -q '"solid-js"'; then
        FRAMEWORK="solid"
        BUILD_TOOL="vite"
        DEV_CMD="npx vite"
    elif echo "$ALL_DEPS" | grep -q '"preact"'; then
        FRAMEWORK="preact"
        BUILD_TOOL="vite"
        DEV_CMD="npx vite"
    elif echo "$ALL_DEPS" | grep -q '"astro"'; then
        FRAMEWORK="astro"
        BUILD_TOOL="astro"
        DEV_CMD="npx astro dev"
        ROUTING="file-based"
    elif echo "$ALL_DEPS" | grep -q '"react"'; then
        FRAMEWORK="react"
        BUILD_TOOL="vite"
        DEV_CMD="npx vite"
    fi

    if echo "$ALL_DEPS" | grep -q '"typescript"'; then
        HAS_TS=true
    fi

    if [ "$BUILD_TOOL" = "vite" ]; then
        if [ -f "vite.config.ts" ] || [ -f "vite.config.js" ]; then
            BUILD_TOOL="vite"
        fi
    fi

    if [ -f "scripts" ] || echo "$ALL_DEPS" | grep -q '"dev"'; then
        SCRIPT_DEV=$(echo "$ALL_DEPS" | grep -o '"dev"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*: *"//' | sed 's/"//')
        if [ -n "$SCRIPT_DEV" ]; then
            DEV_CMD_OVERRIDE=""
            case "$PKG_MGR" in
                pnpm) DEV_CMD_OVERRIDE="pnpm dev" ;;
                yarn) DEV_CMD_OVERRIDE="yarn dev" ;;
                bun) DEV_CMD_OVERRIDE="bun run dev" ;;
                npm) DEV_CMD_OVERRIDE="npm run dev" ;;
            esac
            if [ -n "$DEV_CMD_OVERRIDE" ]; then
                DEV_CMD="$DEV_CMD_OVERRIDE"
            fi
        fi
    fi
fi

if [ -f "pnpm-lock.yaml" ]; then
    PKG_MGR="pnpm"
elif [ -f "yarn.lock" ]; then
    PKG_MGR="yarn"
elif [ -f "bun.lockb" ] || [ -f "bun.lock" ]; then
    PKG_MGR="bun"
elif [ -f "package-lock.json" ]; then
    PKG_MGR="npm"
fi

case "$PKG_MGR" in
    pnpm)
        DEV_CMD=$(echo "$DEV_CMD" | sed 's/^npx /pnpm /' | sed 's/^npm run /pnpm /')
        ;;
    yarn)
        DEV_CMD=$(echo "$DEV_CMD" | sed 's/^npx /yarn /' | sed 's/^npm run /yarn /')
        ;;
    bun)
        DEV_CMD=$(echo "$DEV_CMD" | sed 's/^npx /bunx /' | sed 's/^npm run /bun run /')
        ;;
esac

if [ "$ROUTING" = "unknown" ]; then
    if [ -d "src/routes" ] || [ -d "app/routes" ] || [ -d "pages" ]; then
        ROUTING="file-based"
    elif [ -d "src/app" ] && [ -f "next.config"* ]; then
        ROUTING="file-based"
    else
        ROUTING="config-based"
    fi
fi

PLAYWRIGHT_INSTALLED=false
if [ -f "node_modules/@playwright/test/package.json" ] || echo "${ALL_DEPS:-}" | grep -q '"@playwright/test"'; then
    PLAYWRIGHT_INSTALLED=true
fi

DETOX_INSTALLED=false
if [ -f "node_modules/detox/package.json" ] || echo "${ALL_DEPS:-}" | grep -q '"detox"'; then
    DETOX_INSTALLED=true
fi

echo "FRAMEWORK=$FRAMEWORK"
echo "BUILD_TOOL=$BUILD_TOOL"
echo "PKG_MGR=$PKG_MGR"
echo "DEV_CMD=$DEV_CMD"
echo "HAS_TS=$HAS_TS"
echo "IS_NATIVE=$IS_NATIVE"
echo "ROUTING=$ROUTING"
echo "PLAYWRIGHT_INSTALLED=$PLAYWRIGHT_INSTALLED"
echo "DETOX_INSTALLED=$DETOX_INSTALLED"
