param(
  [string]$Destination = 'data/research_sources/other/banc_2026'
)

$ErrorActionPreference = 'Stop'
$datasetDoi = 'doi:10.7910/DVN/7WTH1N'
$apiUrl = "https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=$datasetDoi"
$selected = @(
  'supplemental_data_1.txt',
  'supplemental_data_2.txt',
  'supplemental_data_3.txt',
  'supplemental_data_4.txt',
  'supplemental_data_5.txt',
  'supplemental_data_6.txt',
  'supplemental_data_7.txt',
  'supplemental_data_8.txt',
  'supplemental_data_9.txt',
  'supplemental_data_10.txt',
  'banc_fafb_reviewed_matches.csv.gz',
  'neck_connective_y121000.parquet',
  'peripheral_nerves.parquet',
  'cell_info.parquet',
  'banc_888_meta.feather',
  'banc_888_edgelist_simple_v2.feather',
  'banc_888_edgelist_simple_v3.feather'
)

$target = Join-Path (Get-Location).Path $Destination
New-Item -ItemType Directory -Force -Path $target | Out-Null
$response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 120
if ($response.status -ne 'OK') { throw "Harvard Dataverse metadata API: $($response.status)" }
$files = @($response.data.latestVersion.files)
$catalog = @($files | ForEach-Object {
  [pscustomobject]@{
    filename = $_.dataFile.filename
    id = $_.dataFile.id
    bytes = $_.dataFile.filesize
    md5 = $_.dataFile.md5
    categories = @($_.categories)
  }
})
$provenance = [ordered]@{
  dataset_doi = $datasetDoi
  dataset_api = $apiUrl
  release = 'BANC CAVE materialization v888 (Nature 2026 final version)'
  dataverse_dataset_id = $response.data.id
  dataverse_version_number = $response.data.latestVersion.versionNumber
  dataverse_version_minor_number = $response.data.latestVersion.versionMinorNumber
  dataverse_version_id = $response.data.latestVersion.id
  dataverse_release_time = $response.data.latestVersion.releaseTime
  license = $response.data.latestVersion.license.name
  fetched_utc = (Get-Date).ToUniversalTime().ToString('o')
  number_of_files_in_dataverse = $catalog.Count
  selected_files = $selected
  catalog = $catalog
}
$provenance | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $target 'dataverse_catalog.json') -Encoding utf8

foreach ($name in $selected) {
  $file = $catalog | Where-Object { $_.filename -eq $name } | Select-Object -First 1
  if ($null -eq $file) { throw "Missing in Dataverse: $name" }
  $path = Join-Path $target $name
  if (Test-Path -LiteralPath $path) {
    $current = Get-Item -LiteralPath $path
    if ($current.Length -eq $file.bytes -and (Get-FileHash -LiteralPath $path -Algorithm MD5).Hash.ToLowerInvariant() -eq $file.md5.ToLowerInvariant()) {
      Write-Output "Verified existing: $name"
      continue
    }
  }
  $url = "https://dataverse.harvard.edu/api/access/datafile/$($file.id)"
  $part = "$path.partial"
  $verified = $false
  for ($attempt = 1; $attempt -le 3; $attempt++) {
    try {
      Write-Output "Downloading $name ($($file.bytes) bytes), attempt $attempt"
      Invoke-WebRequest -Uri $url -OutFile $part -TimeoutSec 1800
      $actualBytes = (Get-Item -LiteralPath $part).Length
      $actualMd5 = (Get-FileHash -LiteralPath $part -Algorithm MD5).Hash.ToLowerInvariant()
      if ($actualBytes -ne $file.bytes -or $actualMd5 -ne $file.md5.ToLowerInvariant()) {
        throw "Integrity mismatch: expected $($file.bytes)/$($file.md5), got $actualBytes/$actualMd5"
      }
      Move-Item -LiteralPath $part -Destination $path -Force
      Write-Output "Verified: $name"
      $verified = $true
      break
    } catch {
      Write-Warning $_
      if ($attempt -eq 3) { throw }
      Start-Sleep -Seconds (5 * $attempt)
    }
  }
  if (-not $verified) { throw "Failed download: $name" }
}

Write-Output "BANC selected data ready: $($selected.Count) files"
