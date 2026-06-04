param(
    [string]$Source = "$env:USERPROFILE\Downloads",
    [string]$Output = "$PSScriptRoot\..\output"
)

$ErrorActionPreference = "Stop"

$resolvedOutput = Resolve-Path -LiteralPath $Output
$videos = Get-ChildItem -LiteralPath $Source -Recurse -File -Include "output_*.mp4","compressed_*.mp4"

if (-not $videos) {
    Write-Host "No annotated videos found under $Source"
    exit 0
}

foreach ($video in $videos) {
    $target = Join-Path $resolvedOutput $video.Name
    Copy-Item -LiteralPath $video.FullName -Destination $target -Force
    Write-Host "Copied $($video.Name)"
}

Write-Host "Imported $($videos.Count) annotated video file(s) into $resolvedOutput"
