$ErrorActionPreference = 'Stop'

$preferredAliases = @('Wi-Fi', 'Ethernet')
$lanIp = $null

foreach ($alias in $preferredAliases) {
  $lanIp = Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias $alias -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
    Select-Object -First 1 -ExpandProperty IPAddress
  if ($lanIp) { break }
}

if (-not $lanIp) {
  $lanIp = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
    Select-Object -First 1 -ExpandProperty IPAddress
}

if (-not $lanIp) {
  Write-Error 'No local Wi-Fi/Ethernet IPv4 address was found. Connect this computer to the same network as the phone and try again.'
  exit 1
}

$env:REACT_NATIVE_PACKAGER_HOSTNAME = $lanIp
$env:EXPO_PUBLIC_API_URL = "http://$lanIp`:8000"
Write-Host "MindBloom API will use http://$lanIp`:8000. Start the backend on this computer before using save actions."
Write-Host "Expo will advertise exp://$lanIp. Keep the phone and computer on the same Wi-Fi network."
& npx expo start --clear --lan $args
exit $LASTEXITCODE
