# Publish the encrypted Impulse Lane app to GitHub Pages (Cody's OK, 2026-10-10).
# Creates Cojack420/site-model once, then pushes the latest encrypted build. Safe to run again to update.
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\codyj\impulse-lane-app'
python build-app.py
$exists = $true
try { gh repo view Cojack420/site-model *> $null; if ($LASTEXITCODE -ne 0) { $exists = $false } } catch { $exists = $false }
if (-not $exists) { gh repo create Cojack420/site-model --public --description "Encrypted site model app" }
if (-not (git remote | Select-String -Quiet origin)) { git remote add origin https://github.com/Cojack420/site-model.git }
git -c user.name="Cody Jackson" -c user.email="codyjacksonwork5@gmail.com" add index.html sw.js manifest.webmanifest icon-192.png icon-512.png build-app.py publish.ps1 .gitignore
git -c user.name="Cody Jackson" -c user.email="codyjacksonwork5@gmail.com" commit -q -m "App build $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git -c credential.helper= -c "credential.helper=!gh auth git-credential" push -q -u origin main
try { gh api -X POST repos/Cojack420/site-model/pages -f "source[branch]=main" -f "source[path]=/" *> $null } catch {}
Write-Host ""
Write-Host "Done. Your app: https://cojack420.github.io/site-model/  (first publish takes 1-2 minutes to go live)"
Write-Host "Password is in your vault keys note."
if (-not $env:NOPAUSE) { Read-Host "Press Enter to close" }
