#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-.}"
PKG_MGR="${2:-npm}"
cd "$PROJECT_DIR"

echo "Checking Playwright installation..."

if [ -f "node_modules/@playwright/test/package.json" ]; then
    echo "Playwright already installed in node_modules."
else
    echo "Installing @playwright/test..."
    case "$PKG_MGR" in
        pnpm) pnpm add -D @playwright/test ;;
        yarn) yarn add -D @playwright/test ;;
        bun) bun add -D @playwright/test ;;
        *) npm install -D @playwright/test ;;
    esac
fi

echo "Checking Chromium browser..."
if npx playwright install --dry-run chromium 2>/dev/null; then
    echo "Chromium already installed."
else
    echo "Installing Chromium for Playwright..."
    npx playwright install chromium
fi

echo "Playwright setup complete."
