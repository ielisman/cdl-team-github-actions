param(
    [string]$SupabaseUrl = "http://localhost:54321",
    [string]$SupabaseServiceRoleKey,
    [string]$SupabaseSchema = "cdl_scanner",
    [string]$GmailAppPassword
)

if (-not $SupabaseServiceRoleKey) {
    Write-Error "Missing -SupabaseServiceRoleKey. Example: .\set_scanner_env.ps1 -SupabaseServiceRoleKey 'sb_secret_xxx'"
    exit 1
}

$env:SUPABASE_URL = $SupabaseUrl
$env:SUPABASE_SERVICE_ROLE_KEY = $SupabaseServiceRoleKey
$env:SUPABASE_SCHEMA = $SupabaseSchema

if ($GmailAppPassword) {
    $env:GMAIL_APP_PASSWORD = $GmailAppPassword
}

Write-Host "Scanner environment variables set for current shell:" -ForegroundColor Green
Write-Host "SUPABASE_URL=$($env:SUPABASE_URL)"
Write-Host "SUPABASE_SCHEMA=$($env:SUPABASE_SCHEMA)"
Write-Host "SUPABASE_SERVICE_ROLE_KEY=<hidden>"
if ($GmailAppPassword) {
    Write-Host "GMAIL_APP_PASSWORD=<hidden>"
}
Write-Host ""
Write-Host "Now run: python .\testChrome.py"
