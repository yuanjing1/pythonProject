<#
    Registers "Clinic Uptime Monitor" in Windows Task Scheduler: one probe at
    logon, then every PROBE_MINUTES (from clinic_monitor_config.py). Runs under
    pythonw.exe so no console window flashes. Re-run after changing PROBE_MINUTES.

    Usage:  powershell -ExecutionPolicy Bypass -File install_task.ps1
    Remove: powershell -ExecutionPolicy Bypass -File install_task.ps1 -Uninstall
#>
param(
    [switch]$Uninstall,
    [string]$TaskName = "Clinic Uptime Monitor"
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $here "clinic_monitor.py"

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed scheduled task '$TaskName'."
    return
}

# pythonw.exe = same interpreter as python.exe, but windowless
$python = (Get-Command python).Source
$pythonw = Join-Path (Split-Path -Parent $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { $pythonw = $python }

if (-not (Test-Path (Join-Path $here "clinic_monitor_config.py"))) {
    throw "clinic_monitor_config.py is missing - copy clinic_monitor_config.example.py to it and set NTFY_TOPIC first."
}

# Single source of truth for the cadence: PROBE_MINUTES in the config file.
Push-Location $here
try {
    $out = & $python -c "import clinic_monitor_config as c; print(c.PROBE_MINUTES)"
    if ($LASTEXITCODE -ne 0) { throw "could not read PROBE_MINUTES from clinic_monitor_config.py" }
} finally { Pop-Location }
$IntervalMinutes = [int]$out
if ($IntervalMinutes -lt 1) { throw "PROBE_MINUTES must be at least 1 (got $out)." }

$action =New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`"" -WorkingDirectory $here

# Every $IntervalMinutes forever, plus one probe right after logon.
$repeating = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddMinutes(2) `
            -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
            -RepetitionDuration (New-TimeSpan -Days 3650)
$atLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
              -DontStopIfGoingOnBatteries -StartWhenAvailable `
              -ExecutionTimeLimit (New-TimeSpan -Minutes 2) `
              -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
               -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action `
    -Trigger @($repeating, $atLogon) -Settings $settings -Principal $principal `
    -Description "Probes the clinic app every $IntervalMinutes minutes and pushes a phone alert via ntfy.sh when it is down." `
    -Force | Out-Null

Write-Host "Registered '$TaskName': probes every $IntervalMinutes min using $pythonw"
Write-Host "Run now:  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Log:      $(Join-Path $here 'clinic_monitor.log')"
