param(
    [string]$Python = "python",
    [switch]$Obfuscate
)
$ErrorActionPreference = "Stop"
$buildArgs = @((Join-Path $PSScriptRoot "build.py"))
if ($Obfuscate) { $buildArgs += "--obfuscate" }
& $Python @buildArgs
if ($LASTEXITCODE -ne 0) { throw "Packaging failed (exit $LASTEXITCODE)." }
