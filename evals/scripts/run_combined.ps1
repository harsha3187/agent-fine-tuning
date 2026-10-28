param(
    [Parameter(Mandatory)][string]$Deployment,
    [int]$Rollouts = 1,
    [int]$Workers = 2,
    [string]$Split = "development",
    [string]$Stage = "baseline",
    [string[]]$Tasks = @("product", "shop", "voucher", "compound")
)
# Runs the combined (original + synthetic) set for one model deployment. Resumable per task.
$ErrorActionPreference = "Continue"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = "."
$env:SHOPPINGBENCH_API_TOKEN = (az containerapp secret show -n azcauys2j2qdjfnto -g rg-agent-optimizer-rft --secret-name sb-api-token --query value -o tsv)
$env:SHOPPINGBENCH_TOOL_URL = "https://azcauys2j2qdjfnto.jollypebble-b11b13a6.eastus2.azurecontainerapps.io"
$env:MAI_OPENAI_BASE_URL = "https://aoptrft-foundry-eus2.openai.azure.com/openai/v1"
$env:MAI_MODEL_DEPLOYMENT_NAME = $Deployment
$out = "evals\results\combined\$Stage\$Deployment\$Split"
New-Item -ItemType Directory -Force $out | Out-Null
foreach ($task in $Tasks) {
    # Compound cases are graded as voucher tasks and use the voucher agent.
    $agent = if ($task -eq "compound") { "voucher" } else { $task }
    $env:SHOPPINGBENCH_TASK = $agent
    $env:OPTIMIZATION_LOCAL_DIR = (Resolve-Path "agents\$agent\$Stage").Path
    & .\.venv\Scripts\python evals\scripts\evaluate_agent.py `
        --dataset "evals\datasets\combined\$Split\$task.jsonl" `
        --documents data\combined\search-documents.jsonl `
        --output "$out\$task.jsonl" --rollouts $Rollouts --workers $Workers `
        --record-errors-as-zero *> "$out\$task.log"
    "$task exit=$LASTEXITCODE"
}
