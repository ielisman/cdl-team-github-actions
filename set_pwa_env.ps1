param(
    [string]$SupabaseUrl = "http://localhost:54321",
    [string]$SupabaseAnonKey,
    [string]$SupabaseSchema = "cdl_scanner",
    [string]$FirebaseApiKey = "",
    [string]$FirebaseAuthDomain = "",
    [string]$FirebaseProjectId = "",
    [string]$FirebaseStorageBucket = "",
    [string]$FirebaseMessagingSenderId = "",
    [string]$FirebaseAppId = "",
    [string]$FirebaseVapidKey = ""
)

if (-not $SupabaseAnonKey) {
    Write-Error "Missing -SupabaseAnonKey. Example: .\set_pwa_env.ps1 -SupabaseAnonKey 'eyJ...'"
    exit 1
}

$pwaDir = Join-Path $PSScriptRoot "cdl-pwa"
$envPath = Join-Path $pwaDir ".env"

$lines = @(
    "VITE_SUPABASE_URL=$SupabaseUrl",
    "VITE_SUPABASE_ANON_KEY=$SupabaseAnonKey",
    "VITE_SUPABASE_SCHEMA=$SupabaseSchema",
    "",
    "VITE_FIREBASE_API_KEY=$FirebaseApiKey",
    "VITE_FIREBASE_AUTH_DOMAIN=$FirebaseAuthDomain",
    "VITE_FIREBASE_PROJECT_ID=$FirebaseProjectId",
    "VITE_FIREBASE_STORAGE_BUCKET=$FirebaseStorageBucket",
    "VITE_FIREBASE_MESSAGING_SENDER_ID=$FirebaseMessagingSenderId",
    "VITE_FIREBASE_APP_ID=$FirebaseAppId",
    "VITE_FIREBASE_VAPID_KEY=$FirebaseVapidKey"
)

Set-Content -Path $envPath -Value $lines -Encoding UTF8

Write-Host "Created/updated $envPath" -ForegroundColor Green
Write-Host "Next:"
Write-Host "1) cd .\cdl-pwa"
Write-Host "2) npm run dev   (or npm run build)"
