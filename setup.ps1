# setup.ps1 - LOCAL test setup only. Production runs on GitHub Actions (see README).
# Usage:  powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

python -m pip install -U -r requirements.txt -q
New-Item -ItemType Directory -Force vendor | Out-Null
foreach ($u in 'https://github.com/Jakeschincariol/youtube-agent-skill.git', 'https://github.com/Ootto-AI/claude-content-skills.git') {
    $d = 'vendor\' + [IO.Path]::GetFileNameWithoutExtension($u)
    if (Test-Path $d) { git -C $d pull --ff-only } else { git clone --depth 1 $u $d }
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { winget install -e --id Gyan.FFmpeg }
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Write-Host 'Local setup done. Test:  python daily_viral.py --videos 1 --dry-run' -ForegroundColor Green
