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

# Determine build tool (nmake or make.exe)
$make = Get-Command nmake -ErrorAction SilentlyContinue
if (-not $make) {
    $make = Get-Command make -ErrorAction SilentlyContinue
}
if (-not $make) {
    $bundledMake = Join-Path $ScriptDir 'make.exe'
    if (Test-Path $bundledMake) {
        $make = Get-Item $bundledMake
    }
}
if (-not $make) {
    Write-Error "No suitable build tool ('nmake' or 'make.exe') found"
    Write-Host "Install Visual Studio Build Tools (provides nmake) or MSYS2"
    Write-Host "Chocolatey : choco install make"
    Write-Host "MSYS2       : pacman -S make"
    exit 1
}
$make = if ($make -is [string]) { $make } else { $make.Source }

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
Write-Host "DLL built successfully at $dllPath"
