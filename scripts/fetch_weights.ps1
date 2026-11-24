# Downloads trained ONNX weights from the latest GitHub Release into backend/app/dominance/weights/
$ErrorActionPreference = "Stop"
$repo = "kartikpagariya25/arterion-coronary-dominance"
$dest = Join-Path $PSScriptRoot "..\backend\app\dominance\weights"
New-Item -ItemType Directory -Force $dest | Out-Null
foreach ($f in "dominance_model.onnx") {
  Write-Host "Downloading $f ..."
  Invoke-WebRequest "https://github.com/$repo/releases/latest/download/$f" -OutFile (Join-Path $dest $f)
}
Write-Host "Done."
