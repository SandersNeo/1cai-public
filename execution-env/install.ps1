# Installation script for Code Execution Environment
# Windows PowerShell

Write-Host "🚀 Installing Code Execution Environment..." -ForegroundColor Green

# Check if Deno is installed
Write-Host "`n📦 Checking Deno installation..." -ForegroundColor Cyan

try {
    $denoVersion = deno --version 2>&1 | Select-String "deno"
    Write-Host "✅ Deno already installed: $denoVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Deno not found. Installing Deno..." -ForegroundColor Yellow
    
    # Install Deno
    irm https://deno.land/install.ps1 | iex
    
    Write-Host "✅ Deno installed successfully!" -ForegroundColor Green
    Write-Host "⚠️  Please restart your terminal to use Deno" -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "`n📁 Creating directories..." -ForegroundColor Cyan

$directories = @(
    ".\servers",
    ".\workspace",
    ".\skills",
    ".\temp"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    } else {
        Write-Host "  Exists: $dir" -ForegroundColor Gray
    }
}

# Create .gitignore
Write-Host "`n📝 Creating .gitignore..." -ForegroundColor Cyan

$gitignore = @"
# Temporary files
temp/
*.tmp

# Workspace (может содержать sensitive data)
workspace/

# Deno cache
.deno/

# Logs
*.log
"@

Set-Content -Path ".\.gitignore" -Value $gitignore
Write-Host "✅ .gitignore created" -ForegroundColor Green

# Test execution
Write-Host "`n🧪 Testing execution environment..." -ForegroundColor Cyan

$testCode = @"
console.log("Hello from Code Execution Environment!");
console.log("Deno version: " + Deno.version.deno);
console.log("TypeScript version: " + Deno.version.typescript);
"@

Set-Content -Path ".\temp\test.ts" -Value $testCode

try {
    deno run --allow-read=.\temp .\temp\test.ts
    Write-Host "✅ Execution test passed!" -ForegroundColor Green
} catch {
    Write-Host "❌ Execution test failed: $_" -ForegroundColor Red
}

# Clean up test file
Remove-Item ".\temp\test.ts" -ErrorAction SilentlyContinue

Write-Host "`n✅ Installation complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Start execution server: deno run --allow-all execution-harness.ts" -ForegroundColor White
Write-Host "  2. Generate MCP APIs: python ../code/py_server/mcp_code_generator.py" -ForegroundColor White
Write-Host "  3. Test from Python: python ../code/py_server/execution_service.py" -ForegroundColor White

Write-Host "`n📚 Documentation: README.md" -ForegroundColor Cyan


