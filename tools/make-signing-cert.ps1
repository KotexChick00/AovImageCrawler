<#
  make-signing-cert.ps1 — Tạo chứng chỉ ký code TỰ KÝ (self-signed) dùng cho build.

  Chạy một lần:   .\tools\make-signing-cert.ps1
  Kết quả:        signing.pfx (khóa riêng + chứng chỉ, có mật khẩu)  → GIỮ BÍ MẬT, không commit
                  signing.cer (chỉ chứng chỉ công khai)              → dùng để máy khác tin cậy

  Lưu ý: chứng chỉ tự ký KHÔNG được Windows/SmartScreen tin mặc định. Nó cho bạn chữ ký nhất quán
  và phát hiện file bị sửa, nhưng chỉ "Valid" trên máy nào đã cài signing.cer vào kho tin cậy.
#>
param(
    [string]$Subject = "CN=KotexChick00",
    [int]$Years      = 5,
    [string]$OutDir  = "."
)
$ErrorActionPreference = "Stop"

$password = Read-Host "Đặt mật khẩu cho file .pfx" -AsSecureString

$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject $Subject `
    -KeyAlgorithm RSA -KeyLength 3072 -HashAlgorithm SHA256 `
    -KeyExportPolicy Exportable `
    -CertStoreLocation Cert:\CurrentUser\My `
    -NotAfter (Get-Date).AddYears($Years)

$pfx = Join-Path $OutDir "signing.pfx"
$cer = Join-Path $OutDir "signing.cer"
Export-PfxCertificate -Cert $cert -FilePath $pfx -Password $password | Out-Null
Export-Certificate    -Cert $cert -FilePath $cer | Out-Null

Write-Host ""
Write-Host "Đã tạo chứng chỉ:"
Write-Host "  Subject    : $($cert.Subject)"
Write-Host "  Thumbprint : $($cert.Thumbprint)"
Write-Host "  Hết hạn    : $($cert.NotAfter.ToString('yyyy-MM-dd'))"
Write-Host "  PFX        : $pfx   (KHÔNG commit — đã thêm *.pfx vào .gitignore)"
Write-Host "  CER        : $cer"
Write-Host ""
Write-Host "Dùng cho GitHub Actions (tạo 2 secret trong Settings > Secrets > Actions):"
Write-Host "  SIGN_PFX_BASE64   = nội dung lệnh:  [Convert]::ToBase64String([IO.File]::ReadAllBytes('$pfx')) | Set-Clipboard"
Write-Host "  SIGN_PFX_PASSWORD = mật khẩu vừa đặt"
Write-Host ""
Write-Host "Để một máy khác tin chứng chỉ này (chạy PowerShell quyền Admin, chỉ làm trên máy của bạn):"
Write-Host "  Import-Certificate -FilePath signing.cer -CertStoreLocation Cert:\LocalMachine\TrustedPublisher"
Write-Host "  Import-Certificate -FilePath signing.cer -CertStoreLocation Cert:\LocalMachine\Root"
