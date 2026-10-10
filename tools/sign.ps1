<#
  sign.ps1 — Ký số một file .exe bằng Authenticode (không cần cài Windows SDK / signtool).

  Dùng với file .pfx:
    .\tools\sign.ps1 -File "dist\AoV Image Crawler.exe" -PfxPath .\signing.pfx -PfxPassword (Read-Host -AsSecureString)
  Dùng chứng chỉ có sẵn trong kho Windows (kể cả chứng chỉ trên USB token, sẽ hỏi PIN):
    .\tools\sign.ps1 -File "dist\AoV Image Crawler.exe" -Thumbprint <thumbprint>

  Ký XONG mới tính SHA-256: ký làm đổi nội dung file, nên checksum phải tính sau bước này.
#>
param(
    [Parameter(Mandatory)][string]$File,
    [string]$PfxPath,
    [securestring]$PfxPassword,
    [string]$Thumbprint,
    [string[]]$TimestampUrls = @(
        "http://timestamp.digicert.com",
        "http://timestamp.sectigo.com",
        "http://timestamp.globalsign.com/tsa/r6advanced1"
    )
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path $File)) { throw "Không thấy file cần ký: $File" }

# 1) Lấy chứng chỉ
if ($Thumbprint) {
    $cert = Get-ChildItem Cert:\CurrentUser\My, Cert:\LocalMachine\My -ErrorAction SilentlyContinue |
            Where-Object Thumbprint -eq $Thumbprint | Select-Object -First 1
    if (-not $cert) { throw "Không thấy chứng chỉ có thumbprint $Thumbprint trong kho Windows." }
}
elseif ($PfxPath) {
    if (-not (Test-Path $PfxPath)) { throw "Không thấy file .pfx: $PfxPath" }
    if (-not $PfxPassword) { throw "Thiếu -PfxPassword cho file .pfx." }
    $cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($PfxPath, $PfxPassword)
}
else { throw "Cần -PfxPath hoặc -Thumbprint." }

if (-not $cert.HasPrivateKey) { throw "Chứng chỉ không có khóa riêng, không thể ký." }
if ($cert.NotAfter -lt (Get-Date)) { throw "Chứng chỉ đã hết hạn ($($cert.NotAfter))." }

# 2) Ký + đóng dấu thời gian (timestamp giữ chữ ký hợp lệ sau khi chứng chỉ hết hạn). Thử lần lượt các máy chủ.
$signed = $null
foreach ($url in $TimestampUrls) {
    try {
        $signed = Set-AuthenticodeSignature -FilePath $File -Certificate $cert `
                    -HashAlgorithm SHA256 -TimestampServer $url -ErrorAction Stop
        if ($signed.SignerCertificate) { break }
    }
    catch { Write-Warning "Timestamp server lỗi ($url): $($_.Exception.Message)" }
}
if (-not $signed -or -not $signed.SignerCertificate) { throw "Ký thất bại với mọi timestamp server." }

# 3) Kiểm tra lại
$sig = Get-AuthenticodeSignature -FilePath $File
if ($sig.Status -in @("NotSigned", "HashMismatch")) { throw "Chữ ký không hợp lệ: $($sig.Status) — $($sig.StatusMessage)" }

Write-Host "Đã ký: $File"
Write-Host "  Người ký   : $($sig.SignerCertificate.Subject)"
Write-Host "  Thumbprint : $($sig.SignerCertificate.Thumbprint)"
Write-Host "  Timestamp  : $(if ($sig.TimeStamperCertificate) { 'có' } else { 'KHÔNG' })"
Write-Host "  Trạng thái : $($sig.Status)"
if ($sig.Status -ne "Valid") {
    Write-Host "  (Trạng thái khác 'Valid' là bình thường với chứng chỉ tự ký: máy này chưa tin chứng chỉ gốc.)"
}
