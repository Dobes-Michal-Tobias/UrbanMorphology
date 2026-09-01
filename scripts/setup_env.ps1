# Creates a local venv, installs requirements, and registers a Jupyter
# kernel named after the project folder so it's identifiable in VS
# Code / Jupyter's kernel picker instead of a generic "Python 3".
#
# Usage (from project root):
#   .\scripts\setup_env.ps1
#   .\scripts\setup_env.ps1 -KernelName "my-project"

param(
    [string]$KernelName = (Split-Path -Leaf (Get-Location))
)

python -m venv .venv
& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

python -m ipykernel install --user --name $KernelName --display-name "Python ($KernelName)"

if (-not (Test-Path .env) -and (Test-Path .env.example)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example - fill in your secrets."
}

Write-Host "Done. Kernel '$KernelName' registered. Select it in Jupyter/VS Code."
