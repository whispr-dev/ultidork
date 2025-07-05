# fix_environment.ps1
# Run this in PowerShell to fix your environment

Write-Host "=== Fixing OmniDork Environment ===" -ForegroundColor Cyan

# 1. First, let's check if 2CAPTCHA_API is actually set
Write-Host "`n[*] Checking environment variables:" -ForegroundColor Yellow
Write-Host "2CAPTCHA_API = $env:2CAPTCHA_API"
Write-Host "CAPTCHA_API_KEY = $env:CAPTCHA_API_KEY"

# Show all env vars containing "CAPTCHA"
Write-Host "`n[*] All CAPTCHA-related env vars:" -ForegroundColor Yellow
Get-ChildItem env: | Where-Object {$_.Name -like "*CAPTCHA*"} | ForEach-Object {
    Write-Host "$($_.Name) = $($_.Value)"
}

# 2. Deactivate broken venv
Write-Host "`n[*] Deactivating broken venv..." -ForegroundColor Yellow
deactivate 2>$null

# 3. Create new venv in current directory
Write-Host "`n[*] Creating fresh virtual environment..." -ForegroundColor Yellow
python -m venv venv_new

# 4. Activate new venv
Write-Host "[*] Activating new venv..." -ForegroundColor Yellow
& .\venv_new\Scripts\Activate.ps1

# 5. Upgrade pip
Write-Host "`n[*] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 6. Install all requirements
Write-Host "`n[*] Installing requirements..." -ForegroundColor Yellow
$requirements = @(
    "aiohttp",
    "beautifulsoup4",
    "colorama",
    "selenium",
    "selenium-wire",
    "undetected-chromedriver",
    "requests",
    "cryptography",
    "flask",
    "gunicorn",
    "asyncio",
    "argparse",
    "webdriver-manager"
)

foreach ($req in $requirements) {
    Write-Host "Installing $req..." -ForegroundColor Green
    python -m pip install $req
}

# 7. Create missing directories
Write-Host "`n[*] Creating required directories..." -ForegroundColor Yellow
$dirs = @(
    "data",
    "data/accounts",
    "data/proxies",
    "exported_proxies",
    "logs"
)

foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Green
    }
}

# 8. Create sample accounts file
Write-Host "`n[*] Creating sample accounts file..." -ForegroundColor Yellow
$accountsJson = @'
[
    {
        "email": "test@example.com",
        "password": "testpass123",
        "notes": "Replace with real accounts"
    }
]
'@
$accountsJson | Out-File -FilePath "data/accounts/my_accounts.json" -Encoding utf8

# 9. Set environment variable for current session
Write-Host "`n[*] Setting CAPTCHA_API_KEY for current session..." -ForegroundColor Yellow
if ($env:2CAPTCHA_API) {
    $env:CAPTCHA_API_KEY = $env:2CAPTCHA_API
    Write-Host "Copied 2CAPTCHA_API to CAPTCHA_API_KEY" -ForegroundColor Green
} else {
    Write-Host "WARNING: 2CAPTCHA_API not found in environment!" -ForegroundColor Red
    Write-Host "You may need to set it in System Properties > Environment Variables" -ForegroundColor Yellow
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "Run this to test: python check_environment.py" -ForegroundColor Green