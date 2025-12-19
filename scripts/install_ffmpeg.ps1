# FFmpeg Installation Script for Windows
# This script downloads and installs FFmpeg to C:\ffmpeg

Write-Host "FFmpeg Installation Script" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""

# Configuration
$ffmpegVersion = "7.1"
$ffmpegUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
$installPath = "C:\ffmpeg"
$tempZip = "$env:TEMP\ffmpeg.zip"

# Check if already installed
if (Test-Path "$installPath\bin\ffmpeg.exe") {
    Write-Host "FFmpeg is already installed at $installPath" -ForegroundColor Yellow
    $version = & "$installPath\bin\ffmpeg.exe" -version 2>&1 | Select-Object -First 1
    Write-Host "Current version: $version" -ForegroundColor Cyan

    $response = Read-Host "Do you want to reinstall? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Installation cancelled." -ForegroundColor Yellow
        exit 0
    }

    Write-Host "Removing existing installation..." -ForegroundColor Yellow
    Remove-Item -Path $installPath -Recurse -Force -ErrorAction SilentlyContinue
}

# Download FFmpeg
Write-Host "Downloading FFmpeg from GitHub..." -ForegroundColor Cyan
try {
    # Use Invoke-WebRequest with progress
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $tempZip -UseBasicParsing
    Write-Host "Download complete!" -ForegroundColor Green
} catch {
    Write-Host "Error downloading FFmpeg: $_" -ForegroundColor Red
    exit 1
}

# Extract FFmpeg
Write-Host "Extracting FFmpeg..." -ForegroundColor Cyan
try {
    Expand-Archive -Path $tempZip -DestinationPath "$env:TEMP\ffmpeg_extract" -Force

    # Find the ffmpeg folder (it has a version-specific name)
    $extractedFolder = Get-ChildItem -Path "$env:TEMP\ffmpeg_extract" -Directory | Select-Object -First 1

    # Move to final location
    if (Test-Path $installPath) {
        Remove-Item -Path $installPath -Recurse -Force
    }
    Move-Item -Path $extractedFolder.FullName -Destination $installPath -Force

    Write-Host "Extraction complete!" -ForegroundColor Green
} catch {
    Write-Host "Error extracting FFmpeg: $_" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item -Path $tempZip -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:TEMP\ffmpeg_extract" -Recurse -Force -ErrorAction SilentlyContinue

# Verify installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Cyan
if (Test-Path "$installPath\bin\ffmpeg.exe") {
    Write-Host "FFmpeg installed successfully at: $installPath" -ForegroundColor Green
    $version = & "$installPath\bin\ffmpeg.exe" -version 2>&1 | Select-Object -First 1
    Write-Host "Version: $version" -ForegroundColor Cyan
} else {
    Write-Host "Installation failed: ffmpeg.exe not found" -ForegroundColor Red
    exit 1
}

# Check if already in PATH
Write-Host ""
Write-Host "Checking PATH environment variable..." -ForegroundColor Cyan
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$ffmpegBinPath = "$installPath\bin"

if ($currentPath -like "*$ffmpegBinPath*") {
    Write-Host "FFmpeg is already in PATH" -ForegroundColor Green
} else {
    Write-Host "Adding FFmpeg to PATH..." -ForegroundColor Yellow

    try {
        # Add to user PATH (safer than system PATH, no admin required)
        $newPath = $currentPath + ";$ffmpegBinPath"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")

        Write-Host "FFmpeg added to PATH successfully!" -ForegroundColor Green
        Write-Host "Note: You may need to restart your terminal for PATH changes to take effect." -ForegroundColor Yellow

        # Update PATH for current session
        $env:Path += ";$ffmpegBinPath"
    } catch {
        Write-Host "Could not automatically add to PATH: $_" -ForegroundColor Red
        Write-Host "Please manually add the following to your PATH:" -ForegroundColor Yellow
        Write-Host "  $ffmpegBinPath" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "=========================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""
Write-Host "Test FFmpeg with: ffmpeg -version" -ForegroundColor Cyan
Write-Host ""

# Test in current session
Write-Host "Testing FFmpeg in current session..." -ForegroundColor Cyan
try {
    $testResult = & ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "Success! $testResult" -ForegroundColor Green
} catch {
    Write-Host "FFmpeg not yet available in current session." -ForegroundColor Yellow
    Write-Host "Please open a new terminal window to use FFmpeg." -ForegroundColor Yellow
}
