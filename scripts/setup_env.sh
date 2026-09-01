#!/usr/bin/env bash
# Creates a local venv, installs requirements, and registers a Jupyter
# kernel named after the project folder.
#
# Usage (from project root):
#   ./scripts/setup_env.sh
#   ./scripts/setup_env.sh my-project

set -euo pipefail

KERNEL_NAME="${1:-$(basename "$PWD")}"

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

python -m ipykernel install --user --name "$KERNEL_NAME" --display-name "Python ($KERNEL_NAME)"

if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "Created .env from .env.example — fill in your secrets."
fi

echo "Done. Kernel '$KERNEL_NAME' registered. Select it in Jupyter/VS Code."
