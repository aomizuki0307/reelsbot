# reelsbot Operations Runbook

> Production deployment and operational procedures for reelsbot Instagram Reels automation

Version: 0.1.0
Last Updated: 2025-12-19

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Setup & Deployment](#setup--deployment)
3. [Operations](#operations)
4. [Scheduling & Automation](#scheduling--automation)
5. [Monitoring & Logging](#monitoring--logging)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)
8. [Disaster Recovery](#disaster-recovery)
9. [Security](#security)

---

## System Requirements

### Minimum Requirements

| Component | Specification |
|-----------|---------------|
| **OS** | Windows 10/11, Windows Server 2019+, Linux, macOS |
| **CPU** | 2 cores, 2.0 GHz+ (4 cores recommended) |
| **RAM** | 4 GB (8 GB recommended) |
| **Storage** | 20 GB free space (50 GB+ for production) |
| **Network** | Stable internet connection |

### Software Dependencies

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.10+ | Runtime environment |
| **FFmpeg** | 4.4+ | Video processing |
| **uv** | Latest | Package management |
| **Git** | 2.30+ | Version control |

### API Access Requirements

1. **LLM Provider** (choose one):
   - **Anthropic Claude API** (recommended)
     - Account: https://console.anthropic.com/
     - Recommended model: `claude-sonnet-4-20250514`
     - Estimated cost: $0.01-0.05 per video

   - **OpenAI API** (alternative)
     - Account: https://platform.openai.com/
     - Recommended model: `gpt-4-turbo-preview`
     - Estimated cost: $0.02-0.08 per video

2. **Instagram Graph API** (future - not in MVP):
   - Business account required
   - App registration needed
   - Access token management

### Cost Estimates

**Daily Production (7 videos/day):**
- LLM API calls: $0.07 - $0.35/day
- Storage: ~500 MB/day (video outputs)
- Monthly total: ~$2 - $10 for API + storage

---

## Setup & Deployment

### Production Installation

#### 1. System Preparation

```powershell
# Update system
winget upgrade --all

# Install Python 3.10+
winget install Python.Python.3.10

# Install FFmpeg
choco install ffmpeg

# Verify installations
python --version
ffmpeg -version
```

#### 2. Application Setup

```powershell
# Clone repository
git clone https://github.com/yourusername/reelsbot.git
cd reelsbot

# Install uv
pip install uv

# Setup environment
make setup

# This creates:
# - .venv/ (virtual environment)
# - outputs/ (video output directory)
# - logs/ (application logs)
# - .env (configuration file)
```

#### 3. Environment Configuration

Create and configure `.env` file:

```ini
# Production .env configuration

# LLM Provider (choose one)
LLM_PROVIDER=anthropic

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Video Settings (production defaults)
DEFAULT_A_DURATION_MIN=8
DEFAULT_A_DURATION_MAX=12
DEFAULT_E_DURATION_MIN=10
DEFAULT_E_DURATION_MAX=14

# Content Mix (70% abstract, 30% educational)
DEFAULT_A_RATIO=70
DEFAULT_E_RATIO=30

# Policy Settings
POLICY_MAX_RETRY=3

# Paths (absolute paths recommended for production)
OUTPUTS_DIR=C:\production\reelsbot\outputs
LOGS_DIR=C:\production\reelsbot\logs
BLOCKED_TERMS_PATH=policies\blocked_terms.txt

# FFmpeg
FFMPEG_PATH=ffmpeg

# Future: Instagram Publishing
META_ACCESS_TOKEN=
INSTAGRAM_ACCOUNT_ID=
```

#### 4. Security Configuration

```powershell
# Set restrictive permissions on .env
icacls .env /inheritance:r
icacls .env /grant:r "%USERNAME%:(R,W)"

# Create logs directory with proper permissions
mkdir logs
icacls logs /grant:r "%USERNAME%:(OI)(CI)F"

# Create outputs directory
mkdir outputs
icacls outputs /grant:r "%USERNAME%:(OI)(CI)F"
```

#### 5. Verification

```powershell
# Run system check
make check-deps

# Display configuration
python -m reelsbot info

# Test run (generate 1 video)
python -m reelsbot run --count 1 --type A --dry-run

# Verify output
dir outputs\run_*\*.mp4
```

### Environment-Specific Configurations

#### Development Environment

```ini
# .env.dev
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-dev-...
DEFAULT_A_RATIO=50
DEFAULT_E_RATIO=50
OUTPUTS_DIR=outputs_dev
LOGS_DIR=logs_dev
```

#### Production Environment

```ini
# .env.prod
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-prod-...
DEFAULT_A_RATIO=70
DEFAULT_E_RATIO=30
OUTPUTS_DIR=C:\production\reelsbot\outputs
LOGS_DIR=C:\production\reelsbot\logs
```

---

## Operations

### Daily Workflow

#### Manual Daily Run

```powershell
# 1. Navigate to project
cd C:\production\reelsbot

# 2. Activate environment
.venv\Scripts\activate

# 3. Generate daily content (2 videos)
python -m reelsbot run --count 2 --mix --dry-run

# 4. Review outputs
dir outputs\run_*\*.mp4 | sort LastWriteTime -Descending | select -First 2

# 5. Manually upload to Instagram
# - Open Instagram app/web
# - Upload videos from outputs/
# - Copy captions from metadata_*.json
```

#### Batch Weekly Run

```powershell
# Generate week's worth of content (7 videos)
python -m reelsbot run --count 7 --mix --dry-run

# Review all outputs
dir outputs\run_*\*.mp4
```

### Content Planning

```powershell
# Generate weekly content plan
python -m reelsbot plan --count 7 --output weekly_plan.json

# Review plan
type weekly_plan.json

# Generate videos based on plan
python -m reelsbot run --count 7 --mix --dry-run
```

### Quality Assurance

```powershell
# Validate generated metadata
python -m reelsbot validate outputs\run_20251219_143022\metadata_1.json

# Batch validate all recent videos
Get-ChildItem outputs\run_*\metadata_*.json -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 10 |
    ForEach-Object { python -m reelsbot validate $_.FullName }
```

---

## Scheduling & Automation

### Windows Task Scheduler Setup

#### Method 1: Using Task Scheduler GUI

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create New Task**
   - Click "Create Task" (not "Create Basic Task")
   - Name: `reelsbot-daily-generation`
   - Description: `Generate daily Instagram Reels content`
   - Check: "Run whether user is logged on or not"
   - Check: "Run with highest privileges"

3. **Triggers Tab**
   - Click "New..."
   - Begin the task: `On a schedule`
   - Settings: `Daily`, Recur every: `1 days`
   - Start time: `09:00:00 AM` (adjust to your timezone)
   - Check: "Enabled"

4. **Actions Tab**
   - Click "New..."
   - Action: `Start a program`
   - Program/script: `C:\production\reelsbot\.venv\Scripts\python.exe`
   - Add arguments: `-m reelsbot run --count 2 --mix --dry-run`
   - Start in: `C:\production\reelsbot`

5. **Conditions Tab**
   - Check: "Start only if the following network connection is available: Any connection"
   - Uncheck: "Start the task only if the computer is on AC power"

6. **Settings Tab**
   - Check: "Allow task to be run on demand"
   - Check: "Run task as soon as possible after a scheduled start is missed"
   - If task fails, restart every: `10 minutes`, Attempt to restart up to: `3 times`

#### Method 2: Using PowerShell Script

Create `C:\production\reelsbot\scripts\setup-scheduler.ps1`:

```powershell
# Setup Windows Task Scheduler for reelsbot

$taskName = "reelsbot-daily-generation"
$pythonPath = "C:\production\reelsbot\.venv\Scripts\python.exe"
$workingDir = "C:\production\reelsbot"
$arguments = "-m reelsbot run --count 2 --mix --dry-run"

# Create task action
$action = New-ScheduledTaskAction -Execute $pythonPath `
    -Argument $arguments `
    -WorkingDirectory $workingDir

# Create task trigger (daily at 9 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At 9am

# Create task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Create task principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U

# Register task
Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Daily reelsbot content generation"

Write-Host "Task '$taskName' created successfully!"
Write-Host "Next run: $(Get-ScheduledTask -TaskName $taskName | Get-ScheduledTaskInfo | Select-Object -ExpandProperty NextRunTime)"
```

Run the setup script:

```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File scripts\setup-scheduler.ps1

# Verify task was created
Get-ScheduledTask -TaskName "reelsbot-daily-generation"

# Test task immediately
Start-ScheduledTask -TaskName "reelsbot-daily-generation"
```

### Alternative: Linux/WSL Cron Job

If running in WSL or Linux:

```bash
# Edit crontab
crontab -e

# Add daily job (runs at 9 AM)
0 9 * * * cd /mnt/c/production/reelsbot && /mnt/c/production/reelsbot/.venv/bin/python -m reelsbot run --count 2 --mix --dry-run >> /mnt/c/production/reelsbot/logs/cron.log 2>&1

# Verify cron job
crontab -l
```

---

## Monitoring & Logging

### Log Files

reelsbot generates detailed logs for each run:

```
logs/
├── run_20251219_143022.log    # Main run log
├── run_20251219_150334.log
└── plan_20251219.log          # Planning log
```

### Log Levels

- **INFO**: Normal operation (plan generation, video creation)
- **WARNING**: Recoverable issues (retry attempts, policy warnings)
- **ERROR**: Failures (API errors, FFmpeg failures)
- **DEBUG**: Detailed diagnostics (disabled in production)

### Monitoring Daily Runs

#### Check Recent Logs

```powershell
# View latest log file
Get-ChildItem logs\*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 50

# Search for errors in last 24 hours
Get-ChildItem logs\*.log |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-1) } |
    Select-String "ERROR" -Context 2, 5
```

#### Check Task Scheduler Status

```powershell
# Get task status
Get-ScheduledTask -TaskName "reelsbot-daily-generation" | Get-ScheduledTaskInfo

# Get task history
Get-ScheduledTask -TaskName "reelsbot-daily-generation" |
    Get-ScheduledTaskInfo |
    Select-Object TaskName, LastRunTime, LastTaskResult, NextRunTime
```

### Monitoring Metrics

Track these metrics for production health:

1. **Success Rate**: Percentage of videos generated successfully
2. **API Call Count**: Number of LLM API calls per day
3. **Generation Time**: Average time to generate one video
4. **Storage Usage**: Disk space used by outputs/
5. **Error Rate**: Number of errors per 100 videos

Create a simple monitoring script:

```powershell
# scripts/monitor-status.ps1

$today = Get-Date -Format "yyyyMMdd"
$todayLogs = Get-ChildItem logs\*$today*.log

Write-Host "=== reelsbot Daily Status ==="
Write-Host "Date: $(Get-Date)"
Write-Host ""

# Count runs today
$runCount = ($todayLogs | Measure-Object).Count
Write-Host "Runs today: $runCount"

# Count videos generated today
$videoCount = (Get-ChildItem outputs\run_$today*\*.mp4 | Measure-Object).Count
Write-Host "Videos generated: $videoCount"

# Check for errors
$errorCount = ($todayLogs | Select-String "ERROR" | Measure-Object).Count
Write-Host "Errors: $errorCount"

# Storage usage
$storageGB = (Get-ChildItem outputs -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
Write-Host "Storage used: $([math]::Round($storageGB, 2)) GB"
```

---

## Troubleshooting

### Common Issues

#### Issue: Task Scheduler Job Not Running

**Symptoms:**
- No new videos in outputs/
- No new log files
- Task shows "Ready" but never runs

**Diagnosis:**
```powershell
# Check task status
Get-ScheduledTask -TaskName "reelsbot-daily-generation" | Format-List *

# Check task history
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" |
    Where-Object { $_.Message -like "*reelsbot*" } |
    Select-Object -First 10
```

**Solutions:**
1. Verify task trigger is configured correctly
2. Check "Run whether user is logged on or not" is enabled
3. Ensure Python path is absolute
4. Test manually: `Start-ScheduledTask -TaskName "reelsbot-daily-generation"`

#### Issue: API Rate Limiting

**Symptoms:**
- Errors: `Rate limit exceeded`
- Multiple retries failing
- Slow generation

**Solutions:**
```powershell
# Reduce batch size
python -m reelsbot run --count 1 --type A

# Add delays between calls (configure in code)
# Or spread generation across day using multiple scheduled tasks
```

#### Issue: FFmpeg Failures

**Symptoms:**
- Error: `ffmpeg command failed`
- Missing video outputs
- Corrupt video files

**Diagnosis:**
```powershell
# Test FFmpeg directly
ffmpeg -version

# Check FFmpeg PATH
where.exe ffmpeg

# Review FFmpeg logs
Get-Content logs\run_*.log | Select-String "ffmpeg"
```

**Solutions:**
1. Reinstall FFmpeg: `choco upgrade ffmpeg`
2. Specify absolute path in .env: `FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe`
3. Check disk space: `Get-PSDrive C`

#### Issue: Disk Space Exhausted

**Symptoms:**
- Error: `No space left on device`
- Write failures
- Corrupt outputs

**Solutions:**
```powershell
# Check disk space
Get-PSDrive C

# Clean old outputs (keep last 30 days)
Get-ChildItem outputs\run_* -Directory |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Recurse -Force

# Clean old logs
Get-ChildItem logs\*.log |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force
```

### Log Analysis

#### Search for Specific Errors

```powershell
# API errors
Get-ChildItem logs\*.log | Select-String "API.*error" -Context 2, 5

# Policy violations
Get-ChildItem logs\*.log | Select-String "policy.*violation" -Context 2, 5

# FFmpeg errors
Get-ChildItem logs\*.log | Select-String "ffmpeg.*failed" -Context 2, 5
```

#### Extract Success/Failure Stats

```powershell
# Count successful generations
$success = (Get-ChildItem logs\*.log | Select-String "Complete!").Count

# Count failures
$failures = (Get-ChildItem logs\*.log | Select-String "Generation failed").Count

Write-Host "Success: $success, Failures: $failures"
Write-Host "Success Rate: $([math]::Round($success / ($success + $failures) * 100, 2))%"
```

---

## Maintenance

### Daily Maintenance

```powershell
# 1. Check task ran successfully
Get-ScheduledTask -TaskName "reelsbot-daily-generation" | Get-ScheduledTaskInfo

# 2. Verify outputs generated
dir outputs\run_$(Get-Date -Format "yyyyMMdd")*\*.mp4

# 3. Review logs for errors
Get-ChildItem logs\run_$(Get-Date -Format "yyyyMMdd")*.log |
    Get-Content | Select-String "ERROR"
```

### Weekly Maintenance

```powershell
# 1. Review success rate
scripts\monitor-status.ps1

# 2. Check API usage and costs
# Review Anthropic/OpenAI dashboard

# 3. Backup recent outputs
robocopy outputs C:\backups\reelsbot\outputs /MIR /MAXAGE:7

# 4. Clean old development outputs
Get-ChildItem outputs_dev -Recurse | Remove-Item -Force -Recurse
```

### Monthly Maintenance

```powershell
# 1. Archive old outputs (keep last 30 days)
$archiveDate = (Get-Date).AddDays(-30).ToString("yyyyMMdd")
Compress-Archive -Path "outputs\run_*" -DestinationPath "archives\outputs_$archiveDate.zip" -Update

# 2. Clean archived outputs
Get-ChildItem outputs\run_* -Directory |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Recurse -Force

# 3. Clean old logs
Get-ChildItem logs\*.log |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force

# 4. Update dependencies
cd C:\production\reelsbot
uv pip list --outdated

# 5. Review and update blocked terms
notepad policies\blocked_terms.txt
```

### Quarterly Maintenance

```powershell
# 1. Update reelsbot to latest version
git fetch origin
git pull origin main
make setup

# 2. Review and optimize configuration
python -m reelsbot info

# 3. Audit API costs
# Review billing dashboards for Anthropic/OpenAI

# 4. Test disaster recovery procedures
# See Disaster Recovery section

# 5. Update documentation
# Review and update this runbook
```

---

## Disaster Recovery

### Backup Strategy

#### What to Back Up

1. **Configuration Files**
   - `.env` (contains API keys)
   - `policies/blocked_terms.txt`
   - Custom scripts

2. **Generated Content** (last 30 days)
   - `outputs/` directory
   - Video files and metadata

3. **Logs** (last 90 days)
   - `logs/` directory

#### Backup Script

Create `scripts/backup-daily.ps1`:

```powershell
# Daily backup script for reelsbot

$backupRoot = "C:\backups\reelsbot"
$date = Get-Date -Format "yyyyMMdd"
$backupPath = "$backupRoot\$date"

# Create backup directory
New-Item -Path $backupPath -ItemType Directory -Force

# Backup .env (encrypted)
Copy-Item .env "$backupPath\.env.backup"

# Backup policies
Copy-Item -Recurse policies "$backupPath\policies"

# Backup recent outputs (last 7 days)
$recentDate = (Get-Date).AddDays(-7).ToString("yyyyMMdd")
Get-ChildItem outputs\run_* -Directory |
    Where-Object { $_.Name -match "run_(\d{8})" -and $Matches[1] -ge $recentDate } |
    Copy-Item -Destination "$backupPath\outputs" -Recurse -Force

# Backup recent logs (last 30 days)
Get-ChildItem logs\*.log |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-30) } |
    Copy-Item -Destination "$backupPath\logs" -Force

# Compress backup
Compress-Archive -Path $backupPath -DestinationPath "$backupRoot\reelsbot_$date.zip"
Remove-Item -Path $backupPath -Recurse -Force

# Clean old backups (keep last 30 days)
Get-ChildItem "$backupRoot\reelsbot_*.zip" |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force

Write-Host "Backup complete: $backupRoot\reelsbot_$date.zip"
```

Schedule daily backups:

```powershell
# Create scheduled task for daily backup
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File C:\production\reelsbot\scripts\backup-daily.ps1" `
    -WorkingDirectory "C:\production\reelsbot"

$trigger = New-ScheduledTaskTrigger -Daily -At 11pm

Register-ScheduledTask -TaskName "reelsbot-daily-backup" `
    -Action $action -Trigger $trigger `
    -Description "Daily backup of reelsbot data"
```

### Recovery Procedures

#### Scenario 1: Configuration File Loss

```powershell
# Restore from latest backup
$latestBackup = Get-ChildItem C:\backups\reelsbot\reelsbot_*.zip |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

Expand-Archive -Path $latestBackup -DestinationPath C:\temp\reelsbot-restore
Copy-Item C:\temp\reelsbot-restore\.env.backup .env
Copy-Item -Recurse C:\temp\reelsbot-restore\policies policies

# Verify restoration
python -m reelsbot info
```

#### Scenario 2: Complete System Failure

```powershell
# 1. Reinstall system dependencies
winget install Python.Python.3.10
choco install ffmpeg

# 2. Clone repository
git clone https://github.com/yourusername/reelsbot.git
cd reelsbot

# 3. Restore from backup
$latestBackup = Get-ChildItem C:\backups\reelsbot\reelsbot_*.zip |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

Expand-Archive -Path $latestBackup -DestinationPath C:\temp\reelsbot-restore

# 4. Restore configuration
Copy-Item C:\temp\reelsbot-restore\.env.backup .env
Copy-Item -Recurse C:\temp\reelsbot-restore\policies policies

# 5. Setup environment
make setup

# 6. Restore recent outputs
Copy-Item -Recurse C:\temp\reelsbot-restore\outputs outputs

# 7. Verify system
python -m reelsbot info
python -m reelsbot run --count 1 --type A --dry-run
```

#### Scenario 3: API Key Compromise

```powershell
# 1. Immediately revoke compromised API key
# - Anthropic: https://console.anthropic.com/settings/keys
# - OpenAI: https://platform.openai.com/api-keys

# 2. Generate new API key

# 3. Update .env
notepad .env  # Update ANTHROPIC_API_KEY or OPENAI_API_KEY

# 4. Verify new key works
python -m reelsbot info
python -m reelsbot run --count 1 --type A --dry-run

# 5. Update scheduled tasks if needed
```

### Data Retention Policy

| Data Type | Retention Period | Storage Location |
|-----------|------------------|------------------|
| Configuration | Indefinite | Version control + backup |
| Active outputs | 30 days | `outputs/` |
| Archived outputs | 1 year | `archives/` (compressed) |
| Logs | 90 days | `logs/` |
| Backups | 30 days | `C:\backups\reelsbot\` |

---

## Security

### API Key Management

1. **Never commit `.env` to version control**
   ```powershell
   # Verify .env is in .gitignore
   Get-Content .gitignore | Select-String "\.env"
   ```

2. **Use environment-specific keys**
   - Development: `sk-ant-dev-...`
   - Production: `sk-ant-prod-...`

3. **Rotate keys quarterly**
   ```powershell
   # Schedule key rotation reminder
   Write-Host "Last key rotation: 2025-12-19"
   Write-Host "Next rotation due: 2026-03-19"
   ```

4. **Secure .env file permissions**
   ```powershell
   # Set restrictive permissions
   icacls .env /inheritance:r
   icacls .env /grant:r "%USERNAME%:(R,W)"
   ```

### Network Security

1. **Use HTTPS for all API calls** (default in reelsbot)
2. **Implement rate limiting** (configured in LLM client)
3. **Monitor for unusual API activity**

### Access Control

```powershell
# Set restrictive permissions on production directory
icacls C:\production\reelsbot /inheritance:r
icacls C:\production\reelsbot /grant:r "Administrators:(OI)(CI)F"
icacls C:\production\reelsbot /grant:r "%USERNAME%:(OI)(CI)M"

# Restrict log access
icacls logs /inheritance:r
icacls logs /grant:r "%USERNAME%:(OI)(CI)F"
```

### Compliance

1. **Content Policy**: All generated content is validated against `policies/blocked_terms.txt`
2. **Brand Safety**: Fictional brand names are generated to avoid real trademark conflicts
3. **Data Privacy**: No personal data is collected or stored
4. **Attribution**: E-type content clearly labeled as "Fictional concept"

---

## Support & Escalation

### Issue Severity Levels

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **P0 - Critical** | Service down, no videos generated | < 1 hour | API key invalid, FFmpeg missing |
| **P1 - High** | Degraded service, partial failures | < 4 hours | High error rate, policy violations |
| **P2 - Medium** | Non-critical issues, workarounds exist | < 24 hours | Slow generation, minor bugs |
| **P3 - Low** | Cosmetic issues, feature requests | < 1 week | UI improvements, documentation |

### Contact Information

- **Project Repository**: https://github.com/yourusername/reelsbot
- **Issue Tracker**: https://github.com/yourusername/reelsbot/issues
- **Documentation**: [README.md](README.md), [ARCHITECTURE.md](ARCHITECTURE.md)

### Emergency Procedures

**If service is completely down:**

1. Check scheduled task status
2. Review latest logs for errors
3. Verify API keys are valid
4. Test FFmpeg availability
5. Run manual generation to isolate issue
6. Restore from last known good backup if needed

---

## Appendix

### Useful Commands Reference

```powershell
# System status
python -m reelsbot info

# Generate content
python -m reelsbot run --count 2 --mix --dry-run

# Validate content
python -m reelsbot validate outputs\run_*\metadata_1.json

# Check dependencies
make check-deps

# View logs
Get-Content logs\run_*.log -Tail 50

# Monitor disk space
Get-PSDrive C

# Check scheduled task
Get-ScheduledTask -TaskName "reelsbot-daily-generation" | Get-ScheduledTaskInfo

# Backup manually
.\scripts\backup-daily.ps1

# Clean old files
make clean
```

### Performance Tuning

**Optimize generation speed:**

1. Use faster LLM models (Claude Haiku instead of Sonnet)
2. Reduce video quality/resolution if acceptable
3. Parallelize generation (future enhancement)
4. Use SSD for outputs directory

**Reduce costs:**

1. Cache LLM responses when possible
2. Use cheaper models for non-critical operations
3. Batch API calls to reduce overhead
4. Monitor and set budget alerts

---

**End of Runbook**

For technical architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md).
For user documentation, see [README.md](README.md).
