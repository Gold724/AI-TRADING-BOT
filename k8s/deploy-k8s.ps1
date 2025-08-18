# PowerShell Kubernetes Deployment Script for TradeBot Sentinel
# Provides automated deployment with auto-scaling and health checks

param(
    [Parameter(Position=0)]
    [ValidateSet('deploy', 'cleanup', 'scale', 'logs', 'status', 'metrics', 'health', 'restart', 'update', 'help')]
    [string]$Action = 'deploy',
    
    [Parameter(Position=1)]
    [int]$Replicas = 2
)

# Configuration
$Namespace = "tradebot"
$AppName = "tradebot-sentinel"
$DockerImage = "tradebot-sentinel:latest"
$KubectlTimeout = "300s"
$HealthCheckRetries = 30
$HealthCheckDelay = 10

# Functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = 'White'
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" -Color Cyan
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" -Color Green
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" -Color Yellow
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" -Color Red
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check kubectl
    try {
        $null = kubectl version --client --short 2>$null
    }
    catch {
        Write-Error "kubectl is not installed or not in PATH"
        exit 1
    }
    
    # Check cluster connection
    try {
        $null = kubectl cluster-info 2>$null
    }
    catch {
        Write-Error "Cannot connect to Kubernetes cluster"
        exit 1
    }
    
    # Check Docker
    try {
        $null = docker --version 2>$null
    }
    catch {
        Write-Warning "Docker is not installed. Assuming image is already built."
    }
    
    # Check required files
    $RequiredFiles = @(
        "tradebot-config.yaml",
        "tradebot-deployment.yaml",
        "tradebot-service.yaml"
    )
    
    foreach ($File in $RequiredFiles) {
        if (-not (Test-Path $File)) {
            Write-Error "Required file not found: $File"
            exit 1
        }
    }
    
    Write-Success "Prerequisites check passed"
}

function Build-DockerImage {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Info "Building Docker image..."
        
        # Check if Dockerfile exists
        if (Test-Path "..\Dockerfile.cloud") {
            docker build -f "..\Dockerfile.cloud" -t $DockerImage ..
        }
        elseif (Test-Path "..\Dockerfile") {
            docker build -f "..\Dockerfile" -t $DockerImage ..
        }
        else {
            Write-Warning "No Dockerfile found. Assuming image is already built."
            return
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker image built successfully"
        }
        else {
            Write-Error "Failed to build Docker image"
            exit 1
        }
    }
    else {
        Write-Warning "Docker not available. Skipping image build."
    }
}

function New-Namespace {
    Write-Info "Creating namespace: $Namespace"
    
    $ExistingNamespace = kubectl get namespace $Namespace 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Warning "Namespace $Namespace already exists"
    }
    else {
        kubectl create namespace $Namespace
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create namespace"
            exit 1
        }
        Write-Success "Namespace $Namespace created"
    }
    
    # Label namespace for monitoring
    kubectl label namespace $Namespace name=$Namespace --overwrite
    kubectl label namespace $Namespace component=trading-bot --overwrite
}

function Set-Secrets {
    Write-Info "Setting up secrets and configurations..."
    
    # Check if .env file exists for secret generation
    if (Test-Path "../.env") {
        Write-Info "Found .env file. Generating secrets from environment variables..."
        
        # Create a temporary secret file
        $SecretContent = @"
apiVersion: v1
kind: Secret
metadata:
  name: tradebot-secrets
  namespace: $Namespace
type: Opaque
stringData:
"@
        
        # Add environment variables to secret
        $EnvContent = Get-Content "../.env"
        foreach ($Line in $EnvContent) {
            # Skip comments and empty lines
            if ($Line -match '^#' -or [string]::IsNullOrWhiteSpace($Line)) {
                continue
            }
            
            if ($Line -match '^([^=]+)=(.*)$') {
                $Key = $Matches[1]
                $Value = $Matches[2] -replace '^"(.*)"$', '$1'  # Remove quotes
                $SecretContent += "  $Key: `"$Value`"`n"
            }
        }
        
        # Apply the generated secret
        $SecretContent | Out-File -FilePath "temp-secrets.yaml" -Encoding UTF8
        kubectl apply -f "temp-secrets.yaml"
        Remove-Item "temp-secrets.yaml" -Force
        
        Write-Success "Secrets created from .env file"
    }
    else {
        Write-Warning "No .env file found. Using default secrets from tradebot-config.yaml"
    }
}

function Deploy-Resources {
    Write-Info "Deploying Kubernetes resources..."
    
    # Apply configurations in order
    $Resources = @(
        "tradebot-config.yaml",
        "tradebot-deployment.yaml",
        "tradebot-service.yaml"
    )
    
    foreach ($Resource in $Resources) {
        Write-Info "Applying $Resource..."
        kubectl apply -f $Resource --timeout=$KubectlTimeout
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to apply $Resource"
            exit 1
        }
        Write-Success "Applied $Resource"
    }
}

function Wait-ForDeployment {
    Write-Info "Waiting for deployment to be ready..."
    
    # Wait for deployment to be available
    kubectl wait --for=condition=available deployment/$AppName --namespace=$Namespace --timeout=$KubectlTimeout
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Deployment failed to become available"
        exit 1
    }
    
    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod --selector=app=$AppName --namespace=$Namespace --timeout=$KubectlTimeout
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Pods failed to become ready"
        exit 1
    }
    
    Write-Success "Deployment is ready"
}

function Test-Health {
    Write-Info "Performing health checks..."
    
    $Retries = 0
    $MaxRetries = $HealthCheckRetries
    
    while ($Retries -lt $MaxRetries) {
        # Get pod name
        $PodName = kubectl get pods -n $Namespace -l app=$AppName -o jsonpath='{.items[0].metadata.name}' 2>$null
        
        if ($PodName) {
            # Check health endpoint
            $HealthCheck = kubectl exec -n $Namespace $PodName -- curl -f http://localhost:8001/health/ready 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Health check passed"
                return $true
            }
        }
        
        $Retries++
        Write-Info "Health check attempt $Retries/$MaxRetries failed. Retrying in ${HealthCheckDelay}s..."
        Start-Sleep -Seconds $HealthCheckDelay
    }
    
    Write-Error "Health checks failed after $MaxRetries attempts"
    return $false
}

function Set-Monitoring {
    Write-Info "Setting up monitoring resources..."
    
    # Check if Prometheus Operator is installed
    $ServiceMonitorCRD = kubectl get crd servicemonitors.monitoring.coreos.com 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Prometheus Operator detected. ServiceMonitor will be created."
    }
    else {
        Write-Warning "Prometheus Operator not found. ServiceMonitor will not work without it."
    }
    
    # Apply monitoring configurations if they exist
    if (Test-Path "monitoring-config.yaml") {
        kubectl apply -f "monitoring-config.yaml"
        Write-Success "Monitoring configuration applied"
    }
}

function Set-Ingress {
    Write-Info "Setting up ingress..."
    
    # Check if ingress controller is available
    $NginxIngress = kubectl get ingressclass nginx 2>$null
    $TraefikIngress = kubectl get ingressclass traefik 2>$null
    
    if ($LASTEXITCODE -eq 0 -and $NginxIngress) {
        Write-Info "Nginx ingress controller detected"
    }
    elseif ($LASTEXITCODE -eq 0 -and $TraefikIngress) {
        Write-Info "Traefik ingress controller detected"
    }
    else {
        Write-Warning "No ingress controller detected. Ingress may not work."
    }
    
    # Check if cert-manager is available for SSL
    $CertManagerCRD = kubectl get crd certificates.cert-manager.io 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Info "cert-manager detected. SSL certificates will be automatically managed."
    }
    else {
        Write-Warning "cert-manager not found. SSL certificates will need manual setup."
    }
}

function Show-DeploymentInfo {
    Write-Info "Deployment Information:"
    Write-Host ""
    
    # Show deployment status
    Write-Host "📊 Deployment Status:" -ForegroundColor Yellow
    kubectl get deployment -n $Namespace -l app=$AppName
    Write-Host ""
    
    # Show pods
    Write-Host "🚀 Pods:" -ForegroundColor Yellow
    kubectl get pods -n $Namespace -l app=$AppName -o wide
    Write-Host ""
    
    # Show services
    Write-Host "🌐 Services:" -ForegroundColor Yellow
    kubectl get services -n $Namespace -l app=$AppName
    Write-Host ""
    
    # Show HPA status
    Write-Host "📈 Horizontal Pod Autoscaler:" -ForegroundColor Yellow
    $HPA = kubectl get hpa -n $Namespace -l app=$AppName 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host $HPA
    }
    else {
        Write-Host "HPA not found"
    }
    Write-Host ""
    
    # Show ingress
    Write-Host "🔗 Ingress:" -ForegroundColor Yellow
    $Ingress = kubectl get ingress -n $Namespace -l app=$AppName 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host $Ingress
    }
    else {
        Write-Host "Ingress not found"
    }
    Write-Host ""
    
    # Show useful commands
    Write-Host "📋 Useful Commands:" -ForegroundColor Yellow
    Write-Host "  View logs:        kubectl logs -n $Namespace -l app=$AppName -f"
    Write-Host "  Scale deployment: kubectl scale deployment/$AppName --replicas=3 -n $Namespace"
    Write-Host "  Port forward:     kubectl port-forward -n $Namespace svc/$AppName-service 8000:8000"
    Write-Host "  Health check:     kubectl exec -n $Namespace deployment/$AppName -- curl http://localhost:8001/health"
    Write-Host "  Delete:           kubectl delete namespace $Namespace"
    Write-Host ""
}

function Remove-Deployment {
    Write-Info "Cleaning up deployment..."
    
    # Delete namespace (this will delete all resources in it)
    kubectl delete namespace $Namespace --timeout=$KubectlTimeout
    
    Write-Success "Cleanup completed"
}

function Set-Scale {
    param([int]$ReplicaCount)
    
    Write-Info "Scaling deployment to $ReplicaCount replicas..."
    
    kubectl scale deployment/$AppName --replicas=$ReplicaCount -n $Namespace
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to scale deployment"
        exit 1
    }
    
    kubectl wait --for=condition=available deployment/$AppName --namespace=$Namespace --timeout=$KubectlTimeout
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Deployment failed to scale properly"
        exit 1
    }
    
    Write-Success "Deployment scaled to $ReplicaCount replicas"
}

function Show-Logs {
    Write-Info "Showing application logs..."
    kubectl logs -n $Namespace -l app=$AppName -f --tail=100
}

function Show-Metrics {
    Write-Info "Showing deployment metrics..."
    
    # Get pod metrics if metrics-server is available
    $PodMetrics = kubectl top pods -n $Namespace 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "📊 Pod Resource Usage:" -ForegroundColor Yellow
        kubectl top pods -n $Namespace -l app=$AppName
        Write-Host ""
    }
    
    # Show HPA metrics
    $HPA = kubectl get hpa -n $Namespace -l app=$AppName 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "📈 HPA Metrics:" -ForegroundColor Yellow
        kubectl describe hpa -n $Namespace -l app=$AppName
        Write-Host ""
    }
}

function Restart-Deployment {
    Write-Info "Restarting deployment..."
    kubectl rollout restart deployment/$AppName -n $Namespace
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to restart deployment"
        exit 1
    }
    
    Wait-ForDeployment
    $HealthResult = Test-Health
    if ($HealthResult) {
        Write-Success "Deployment restarted successfully"
    }
    else {
        Write-Error "Deployment restart failed health checks"
        exit 1
    }
}

function Update-Deployment {
    Write-Info "Updating deployment..."
    Build-DockerImage
    
    kubectl set image deployment/$AppName tradebot-app=$DockerImage -n $Namespace
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to update deployment image"
        exit 1
    }
    
    kubectl rollout status deployment/$AppName -n $Namespace --timeout=$KubectlTimeout
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Deployment update failed"
        exit 1
    }
    
    $HealthResult = Test-Health
    if ($HealthResult) {
        Write-Success "Deployment updated successfully"
    }
    else {
        Write-Error "Deployment update failed health checks"
        exit 1
    }
}

function Show-Help {
    Write-Host "Usage: .\deploy-k8s.ps1 [action] [options]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Yellow
    Write-Host "  deploy          Deploy the TradeBot Sentinel (default)"
    Write-Host "  cleanup         Remove all resources"
    Write-Host "  scale [N]       Scale deployment to N replicas (default: 2)"
    Write-Host "  logs            Show application logs"
    Write-Host "  status          Show deployment status"
    Write-Host "  metrics         Show resource metrics"
    Write-Host "  health          Perform health checks"
    Write-Host "  restart         Restart the deployment"
    Write-Host "  update          Update deployment with new image"
    Write-Host "  help            Show this help message"
    Write-Host ""
}

# Main execution
switch ($Action) {
    'deploy' {
        Write-Info "Starting TradeBot Sentinel deployment..."
        Test-Prerequisites
        Build-DockerImage
        New-Namespace
        Set-Secrets
        Deploy-Resources
        Wait-ForDeployment
        $HealthResult = Test-Health
        if (-not $HealthResult) {
            Write-Error "Deployment failed health checks"
            exit 1
        }
        Set-Monitoring
        Set-Ingress
        Show-DeploymentInfo
        Write-Success "Deployment completed successfully!"
    }
    
    'cleanup' {
        Remove-Deployment
    }
    
    'scale' {
        Set-Scale -ReplicaCount $Replicas
    }
    
    'logs' {
        Show-Logs
    }
    
    'status' {
        Show-DeploymentInfo
    }
    
    'metrics' {
        Show-Metrics
    }
    
    'health' {
        $HealthResult = Test-Health
        if (-not $HealthResult) {
            exit 1
        }
    }
    
    'restart' {
        Restart-Deployment
    }
    
    'update' {
        Update-Deployment
    }
    
    'help' {
        Show-Help
    }
    
    default {
        Write-Error "Unknown action: $Action"
        Write-Host "Use '.\deploy-k8s.ps1 help' for usage information"
        exit 1
    }
}