#!/usr/bin/env bash
set -euo pipefail

PYTHON=${PYTHON:-python3}

# Create venv with python3 explicitly
$PYTHON -m venv .venv
source .venv/bin/activate

# Always use "python -m pip" from the venv to avoid system pip confusion
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install black flake8 isort pytest pre-commit python-dotenv

pre-commit install
npm install

# Create develop branch if it doesn't exist
git rev-parse --verify develop >/dev/null 2>&1 || git checkout -b develop

echo "✅ Repo bootstrap complete. Next:"
echo "1) Terminal A: make dev"
echo "2) Terminal B: npm run dev:css"
