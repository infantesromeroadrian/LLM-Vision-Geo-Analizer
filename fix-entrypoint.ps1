# PowerShell script to convert line endings from Windows (CRLF) to Unix (LF)
$content = Get-Content -Raw -Path "docker-entrypoint.sh"
$content = $content -replace "`r`n", "`n"
$content | Set-Content -NoNewline -Path "docker-entrypoint.sh"
Write-Host "Line endings have been converted from CRLF to LF for docker-entrypoint.sh" 