<#
.SYNOPSIS
Run a disposable x64 AZL4 ModuleJail experiment; no RPM is built.
.DESCRIPTION
Supply a subscription, a new rlmenge-modulejail-poc resource group, a dedicated
SSH key, and explicit /32 ingress sources. Provisioning incurs Azure charges.
Phases are prepare, audit, enforce, boot (after Restart), upgrade, boot (after
checking BootLayout and Restart), refresh, and rollback. Record SshCheck with
-Phase enforce, boot, and rollback. Collect evidence, then run summarize.py
on base\build\work\scratch\modulejail-poc\<resource-group>.
Cleanup requires a verified full-pass result and explicit -ApproveDeletion.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('Provision', 'Guest', 'Restart', 'Collect', 'Status', 'Inspect', 'BootLayout', 'SshCheck', 'Cleanup')]
    [string] $Action,
    [ValidateSet('prepare', 'audit', 'enforce', 'boot', 'upgrade', 'rollback', 'refresh')]
    [string] $Phase,
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-fA-F0-9]{8}(-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$')]
    [string] $SubscriptionId,
    [Parameter(Mandatory)]
    [ValidatePattern('^rlmenge-modulejail-poc-[a-z0-9][a-z0-9-]{0,50}$')]
    [string] $ResourceGroup,
    [Parameter(Mandatory)]
    [string] $SshKeyPath,
    [string[]] $AllowedSshCidrs,
    [switch] $ApproveDeletion
)

$ErrorActionPreference = 'Stop'
$Subscription = $SubscriptionId
$Group = $ResourceGroup
$Vm = 'modulejail-poc-x64'
$Image = 'microsoftazurelinux:azurelinux-4:4:4.0.2026110203'
$Key = $SshKeyPath
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Results = Join-Path $RepoRoot "base\build\work\scratch\modulejail-poc\$Group"
New-Item -ItemType Directory -Force $Results | Out-Null

function Invoke-Az {
    param([string[]] $Arguments)
    $output = & az @Arguments --subscription $Subscription --only-show-errors -o json
    if ($LASTEXITCODE -ne 0) { throw "Azure command failed: $($Arguments -join ' ')" }
    if ($output) { return ($output -join "`n" | ConvertFrom-Json) }
}

function Invoke-GuestCommand {
    param([string] $Script, [string] $Label)
    $scriptPath = Join-Path $Results "$Label.sh"
    [IO.File]::WriteAllText($scriptPath, $Script.Replace("`r`n", "`n"), [Text.UTF8Encoding]::new($false))
    $result = Invoke-Az @('vm', 'run-command', 'invoke', '-g', $Group, '-n', $Vm,
        '--command-id', 'RunShellScript', '--scripts', "@$scriptPath")
    $result | ConvertTo-Json -Depth 30 | Set-Content (Join-Path $Results "$Label.json")
    return (($result.value | ForEach-Object { $_.message }) -join "`n")
}

function Get-TrustedSshTarget {
    $vmInfo = Invoke-Az @('vm', 'show', '-g', $Group, '-n', $Vm, '-d')
    if ($vmInfo.publicIps -notmatch '^\d+\.\d+\.\d+\.\d+$') { throw 'Expected one IPv4 address.' }
    $keyOutput = Invoke-GuestCommand 'cat /etc/ssh/ssh_host_ed25519_key.pub' 'ssh-host-key'
    if ($keyOutput -notmatch '(?m)^ssh-ed25519 ([A-Za-z0-9+/=]+)(?: .*)?\r?$') {
        throw 'Missing authenticated SSH host key.'
    }
    $knownHosts = Join-Path $Results 'known_hosts'
    "$($vmInfo.publicIps) ssh-ed25519 $($Matches[1])" | Set-Content $knownHosts -Encoding ascii
    return @{ Address = $vmInfo.publicIps; KnownHosts = $knownHosts }
}

switch ($Action) {
    'Provision' {
        if (-not $AllowedSshCidrs) { throw 'Provision requires explicit -AllowedSshCidrs.' }
        foreach ($cidr in $AllowedSshCidrs) {
            $address = $null
            if ($cidr -notmatch '^(\d+\.\d+\.\d+\.\d+)/32$' -or
                    -not [Net.IPAddress]::TryParse($Matches[1], [ref]$address) -or
                    $address.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork) {
                throw 'SSH ingress sources must be explicit IPv4 /32 addresses.'
            }
        }
        if (Test-Path (Join-Path $Results 'provision.json')) {
            throw 'This one-shot experiment already has provisioning evidence; do not overwrite a prior run.'
        }
        if (Invoke-Az @('group', 'exists', '-n', $Group)) {
            throw 'Dedicated resource group already exists; inspect it rather than overwrite it.'
        }
        if (-not (Test-Path "$Key.pub")) { throw 'Tester public key missing.' }
        Invoke-Az @('group', 'create', '-n', $Group, '-l', 'westus3',
            '--tags', 'owner=rlmenge', 'purpose=modulejail-poc') | Out-Null
        Invoke-Az @('network', 'nsg', 'create', '-g', $Group, '-n', 'modulejail-nsg') | Out-Null
        Invoke-Az (@('network', 'nsg', 'rule', 'create', '-g', $Group,
            '--nsg-name', 'modulejail-nsg', '-n', 'RestrictedSSH', '--priority', '100',
            '--source-address-prefixes') + $AllowedSshCidrs + @(
            '--destination-port-ranges', '22', '--protocol', 'Tcp', '--access', 'Allow')) | Out-Null
        Invoke-Az @('network', 'nsg', 'rule', 'create', '-g', $Group,
            '--nsg-name', 'modulejail-nsg', '-n', 'DenyOtherInbound', '--priority', '200',
            '--source-address-prefixes', '*', '--destination-port-ranges', '*',
            '--protocol', '*', '--access', 'Deny') | Out-Null
        $created = Invoke-Az @('vm', 'create', '-g', $Group, '-n', $Vm,
            '--image', $Image, '--size', 'Standard_D2as_v5', '--admin-username', 'azureuser',
            '--ssh-key-values', "$Key.pub", '--authentication-type', 'ssh',
            '--os-disk-size-gb', '32', '--storage-sku', 'StandardSSD_LRS',
            '--nsg', 'modulejail-nsg', '--nsg-rule', 'NONE', '--public-ip-sku', 'Standard',
            '--vnet-address-prefix', '10.91.0.0/16', '--subnet-address-prefix', '10.91.0.0/24',
            '--security-type', 'TrustedLaunch', '--enable-secure-boot', 'true',
            '--enable-vtpm', 'true')
        $created | ConvertTo-Json -Depth 30 | Set-Content (Join-Path $Results 'provision.json')
        Invoke-Az @('vm', 'boot-diagnostics', 'enable', '-g', $Group, '-n', $Vm) | Out-Null
        $created | Format-List
    }
    'Guest' {
        if (-not $Phase) { throw '-Phase is required.' }
        $payload = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'guest.py')))
        $script = "set -eu`nexport MODULEJAIL_POC_GROUP='$Group'`nexport MODULEJAIL_POC_VM='$Vm'`nexport MODULEJAIL_POC_SUBSCRIPTION='$Subscription'`ncommand -v python3 >/dev/null || tdnf -y install python3`ninstall -d -m 755 /var/lib/modulejail-poc`nprintf '%s' '$payload' | base64 -d > /var/lib/modulejail-poc/guest.py`npython3 /var/lib/modulejail-poc/guest.py $Phase"
        $message = Invoke-GuestCommand $script $Phase
        Write-Output $message
        if ($message -notmatch "(?m)^POC_PHASE_PASS=$Phase\r?$") {
            throw "Phase $Phase failed or output was incomplete; inspect guest phase logs."
        }
    }
    'Restart' {
        Invoke-Az @('vm', 'restart', '-g', $Group, '-n', $Vm) | Out-Null
        Invoke-Az @('vm', 'get-instance-view', '-g', $Group, '-n', $Vm) |
            ConvertTo-Json -Depth 30 | Set-Content (Join-Path $Results 'instance-view.json')
    }
    'Status' {
        Invoke-Az @('resource', 'list', '-g', $Group) | Select-Object name,type,location | Format-Table
        Invoke-Az @('vm', 'show', '-g', $Group, '-n', $Vm, '-d') |
            ConvertTo-Json -Depth 30 | Set-Content (Join-Path $Results 'vm.json')
        Invoke-GuestCommand 'uname -a; systemctl is-active sshd waagent; cat /var/lib/modulejail-poc/state.json; tail -n 16 /var/lib/modulejail-poc/prepare-*.log; modprobe -n -v algif_hash; modprobe -n -v can_raw; modprobe -n -v tipc; sysctl kernel.modules_disabled' 'status'
    }
    'Inspect' {
        Invoke-GuestCommand @'
set -eu
printf '\nKernel helper and relevant modules:\n'
sysctl kernel.modprobe kernel.modules_disabled
grep -E 'CONFIG_(CAN|MODULES|STATIC_USERMODEHELPER|SECURITY_LOCKDOWN|TIPC|CRYPTO_USER_API|IP_SCTP|VSOCKETS)' /boot/config-$(uname -r)
printf '\nInstalled blocking policy:\n'
grep -hE '^(install|blacklist|alias net-pf)' /etc/modprobe.d/*.conf /usr/lib/modprobe.d/*.conf
printf '\nSocket-family alias resolution:\n'
modprobe -n -v net-pf-29
modinfo -F filename can
printf '\nLoaded socket modules:\n'
grep -E '^(can|sctp|tipc|af_alg|algif|vsock|llc)' /proc/modules || test $? -eq 1
'@ 'inspect'
    }
    'BootLayout' {
        Invoke-GuestCommand @'
set -eu
ls -l /boot
printf '\nGRUB kernel/initrd references:\n'
grep -E 'linux|initrd|default|saved_entry' /boot/grub2/grub.cfg
printf '\nGRUB environment:\n'
grub2-editenv /boot/grub2/grubenv list
printf '\nBoot loader specification entries:\n'
cat /boot/loader/entries/*.conf
'@ 'boot-layout'
    }
    'SshCheck' {
        $target = Get-TrustedSshTarget
        $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
        $output = & ssh -i $Key -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes `
            -o "UserKnownHostsFile=$($target.KnownHosts)" "azureuser@$($target.Address)" `
            'id -un; uname -r; if test -f /etc/modprobe.d/modulejail-blacklist.conf; then printf "POLICY=present\n"; else printf "POLICY=absent\n"; fi; cat /proc/sys/kernel/random/boot_id; printf "EXTERNAL_SSH_PASS\n"' 2>&1
        $sshExit = $LASTEXITCODE
        $passed = $sshExit -eq 0 -and $output -contains 'EXTERNAL_SSH_PASS'
        @{ timestamp = $stamp; phase = $Phase; passed = $passed; exit_code = $sshExit; output = "$output" } |
            ConvertTo-Json | Set-Content (Join-Path $Results "ssh-$stamp.json")
        if (-not $passed) {
            Write-Output $output
            throw 'External SSH check failed. Preserve network restrictions; this is a qualification gap.'
        }
        $output
    }
    'Collect' {
        $manifestScript = @'
set -eu
tar --exclude=modulejail-poc/source --exclude=modulejail-poc/gnupg -czf /var/lib/modulejail-poc-evidence.tar.gz -C /var/lib modulejail-poc
sha256sum /var/lib/modulejail-poc-evidence.tar.gz
stat -c '%s' /var/lib/modulejail-poc-evidence.tar.gz
'@
        $manifest = Invoke-GuestCommand $manifestScript 'evidence-manifest'
        if ($manifest -notmatch '(?m)^([a-f0-9]{64})  /var/lib/modulejail-poc-evidence.tar.gz\r?$') {
            throw 'Missing remote evidence hash.'
        }
        $expectedHash = $Matches[1]
        if ($manifest -notmatch '(?m)^([0-9]+)\r?$') { throw 'Missing evidence size.' }
        $size = [int64]$Matches[1]
        if ($size -le 0 -or $size -gt 20971520) { throw 'Evidence archive size outside 1 byte to 20 MiB.' }
        $destination = Join-Path $Results 'evidence.tar.gz'
        $target = Get-TrustedSshTarget
        & ssh -i $Key -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes `
            -o "UserKnownHostsFile=$($target.KnownHosts)" "azureuser@$($target.Address)" `
            'sudo cp /var/lib/modulejail-poc-evidence.tar.gz /home/azureuser/modulejail-poc-evidence.tar.gz && sudo chown azureuser:azureuser /home/azureuser/modulejail-poc-evidence.tar.gz'
        if ($LASTEXITCODE -eq 0) {
            & scp -i $Key -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes `
                -o "UserKnownHostsFile=$($target.KnownHosts)" `
                "azureuser@$($target.Address):/home/azureuser/modulejail-poc-evidence.tar.gz" $destination
            if ($LASTEXITCODE -ne 0) { throw 'SCP evidence transfer failed.' }
        } else {
            Write-Warning 'SSH unavailable; retrieving evidence through authenticated Run Command.'
            $stream = [IO.File]::Create($destination)
            try {
                for ($offset = 0; $offset -lt $size; $offset += 2800) {
                    $chunkScript = "set -eu`nprintf 'CHUNK='`ndd if=/var/lib/modulejail-poc-evidence.tar.gz bs=1 skip=$offset count=2800 status=none | base64 -w0`nprintf '\n'"
                    $chunk = Invoke-GuestCommand $chunkScript "chunk-$offset"
                    if ($chunk -notmatch '(?m)^CHUNK=([A-Za-z0-9+/=]+)\r?$') {
                        throw "Missing or truncated evidence chunk at $offset."
                    }
                    $bytes = [Convert]::FromBase64String($Matches[1])
                    if ($bytes.Length -ne [Math]::Min(2800, $size - $offset)) {
                        throw "Incorrect evidence chunk length at $offset."
                    }
                    $stream.Write($bytes, 0, $bytes.Length)
                }
            } finally { $stream.Dispose() }
        }
        $actualHash = (Get-FileHash $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) { throw 'Evidence SHA256 mismatch.' }
        $actualHash | Set-Content (Join-Path $Results 'evidence.sha256')
        "Verified evidence: $destination ($size bytes, SHA256 $actualHash)"
    }
    'Cleanup' {
        if (-not $ApproveDeletion) { throw 'Explicit -ApproveDeletion is required.' }
        $groupInfo = Invoke-Az @('group', 'show', '-n', $Group)
        if ($groupInfo.tags.owner -ne 'rlmenge' -or $groupInfo.tags.purpose -ne 'modulejail-poc') {
            throw 'Ownership tags do not match.'
        }
        if (-not (Test-Path (Join-Path $Results 'evidence.sha256'))) {
            throw 'Preserve the resource group until evidence has been collected and verified.'
        }
        $summaryFile = Join-Path $Results 'result.json'
        if (-not (Test-Path $summaryFile) -or
                (Get-Content -Raw $summaryFile | ConvertFrom-Json).verdict -ne 'PASS') {
            throw 'The approved cleanup policy requires a verified full-pass result.'
        }
        Invoke-Az @('group', 'delete', '-n', $Group, '--yes') | Out-Null
        if (Invoke-Az @('group', 'exists', '-n', $Group)) { throw 'Resource group still exists.' }
        'Deletion verified.' | Set-Content (Join-Path $Results 'cleanup.txt')
    }
}
