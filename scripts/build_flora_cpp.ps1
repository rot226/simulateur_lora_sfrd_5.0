# PowerShell script to build the native FLoRa physical layer library
# Mirrors the logic of scripts/build_flora_cpp.sh for Windows environments

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir   = Split-Path $ScriptDir -Parent
$FloraDir  = Join-Path $RootDir 'flora-master'

if (-not (Test-Path $FloraDir)) {
    Write-Error "Directory '$FloraDir' not found"
    exit 1
}

Set-Location $FloraDir

# Determine make executable (make or mingw32-make)
$make = Get-Command make -ErrorAction SilentlyContinue
if (-not $make) {
    $make = Get-Command mingw32-make -ErrorAction SilentlyContinue
}
if (-not $make) {
    Write-Error "'make' or 'mingw32-make' not found in PATH"
    exit 1
}
$make = $make.Source

# Generate makefiles if missing
if (-not (Test-Path 'src/Makefile')) {
    & $make makefiles
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# Build the library using all available cores
$jobs = [Environment]::ProcessorCount
& $make 'libflora_phy.dll' ("-j$jobs")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$dllPath = Join-Path $FloraDir 'libflora_phy.dll'
Write-Host "Build succeeded. DLL available at $dllPath (flora-master/libflora_phy.dll)"
