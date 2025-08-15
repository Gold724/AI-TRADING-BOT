# PowerShell script to run the TRAE multi-agent system

# Ensure we're in the correct directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $scriptPath

# Create logs directory if it doesn't exist
if (-not (Test-Path -Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "Created logs directory"
}

# Check if phase-5.md exists
if (-not (Test-Path -Path "trae_prompts\phase-5.md")) {
    Write-Host "Error: phase-5.md not found in trae_prompts directory" -ForegroundColor Red
    exit 1
}

# Check if agents_registry.yml exists
if (-not (Test-Path -Path "config\agents_registry.yml")) {
    Write-Host "Error: agents_registry.yml not found in config directory" -ForegroundColor Red
    exit 1
}

# Run the multi-agent example
Write-Host "Running TRAE Multi-Agent System..." -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

try {
    python examples/multi_agent_example.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "\nMulti-agent system ran successfully!" -ForegroundColor Green
        
        # Check if a decision log was created
        if (Test-Path -Path "logs\multi_agent_example.json") {
            Write-Host "Decision log created at logs\multi_agent_example.json" -ForegroundColor Green
            
            # Ask if user wants to visualize the decision
            $visualize = Read-Host "Would you like to visualize the decision? (y/n)"
            if ($visualize -eq "y") {
                Write-Host "\nGenerating visualizations..." -ForegroundColor Cyan
                python tools/visualize_decision.py --decision-file logs/multi_agent_example.json
            }
            
            # Ask if user wants to monitor agent performance
            $monitor = Read-Host "Would you like to monitor agent performance? (y/n)"
            if ($monitor -eq "y") {
                Write-Host "\nGenerating performance reports..." -ForegroundColor Cyan
                python tools/monitor_agents.py
            }
        }
    } else {
        Write-Host "\nError running multi-agent system" -ForegroundColor Red
    }
} catch {
    Write-Host "\nException occurred: $_" -ForegroundColor Red
}

Write-Host "\nDone!" -ForegroundColor Cyan