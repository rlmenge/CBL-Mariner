$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Group = 'rlmenge-modulejail-poc-test-' + [Guid]::NewGuid().ToString('N')
$Fixture = Join-Path $RepoRoot "base\build\work\scratch\modulejail-poc\$Group"
New-Item -ItemType Directory -Force $Fixture | Out-Null
$Key = Join-Path $Fixture 'test-key'
'test fixture, not a real key' | Set-Content "$Key.pub"
$Parameters = @{
    SubscriptionId = '11111111-1111-1111-1111-111111111111'
    ResourceGroup = $Group
    SshKeyPath = $Key
}
$Calls = [Collections.Generic.List[object]]::new()

function az {
    $Arguments = [string[]]$args
    $Calls.Add($Arguments)
    $global:LASTEXITCODE = 0
    if ($Arguments[0] -eq 'group' -and $Arguments[1] -eq 'exists') { return 'false' }
    if ($Arguments[0] -eq 'vm' -and $Arguments[1] -eq 'run-command') {
        $index = [Array]::IndexOf($Arguments, '--scripts')
        $payload = Get-Content -Raw $Arguments[$index + 1].Substring(1)
        foreach ($expected in @(
            "export MODULEJAIL_POC_GROUP='$($Parameters.ResourceGroup)'",
            "export MODULEJAIL_POC_VM='modulejail-poc-x64'",
            "export MODULEJAIL_POC_SUBSCRIPTION='$($Parameters.SubscriptionId)'"
        )) {
            if (-not $payload.Contains($expected)) { throw "Guest identity input missing: $expected" }
        }
        return '{"value":[{"message":"POC_PHASE_PASS=audit"}]}'
    }
    return '{}'
}

try {
    $rejected = $false
    try { & "$PSScriptRoot\Invoke-Poc.ps1" -Action Provision @Parameters }
    catch {
        if ($_.Exception.Message -notlike '*explicit -AllowedSshCidrs*') { throw }
        $rejected = $true
    }
    if (-not $rejected -or $Calls.Count) { throw 'Missing ingress must fail before Azure calls.' }
    $rejected = $false
    try { & "$PSScriptRoot\Invoke-Poc.ps1" -Action Provision @Parameters -AllowedSshCidrs '0.0.0.0/0' }
    catch {
        if ($_.Exception.Message -notlike '*IPv4 /32*') { throw }
        $rejected = $true
    }
    if (-not $rejected -or $Calls.Count) { throw 'Broad ingress must fail before Azure calls.' }
    $sources = @('203.0.113.1/32', '198.51.100.2/32')
    & "$PSScriptRoot\Invoke-Poc.ps1" -Action Provision @Parameters -AllowedSshCidrs $sources
    $rules = @($Calls | Where-Object { $_ -contains 'RestrictedSSH' } | ForEach-Object { ,$_ })
    if ($rules.Count -ne 1) { throw 'Expected one restricted SSH rule.' }
    $rule = $rules[0]
    $index = [Array]::IndexOf($rule, '--source-address-prefixes')
    if ($rule[$index + 1] -ne $sources[0] -or $rule[$index + 2] -ne $sources[1]) {
        throw 'Explicit SSH sources were not passed to Azure unchanged.'
    }
    & "$PSScriptRoot\Invoke-Poc.ps1" -Action Guest -Phase audit @Parameters
    Write-Output 'Controller tests passed; all Azure calls were mocked.'
} finally {
    Remove-Item Function:az
    Remove-Item -LiteralPath $Fixture -Recurse -Force
}
