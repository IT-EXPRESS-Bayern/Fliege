$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$source = Join-Path $root 'data/research_sources/other/banc_2026/supplemental_data_2.txt'
$functions = Join-Path $root 'data/research_sources/other/banc_2026/supplemental_data_9.txt'
$anDnClusters = Join-Path $root 'data/research_sources/other/banc_2026/supplemental_data_6.txt'
$effectorClusters = Join-Path $root 'data/research_sources/other/banc_2026/supplemental_data_7.txt'
$fafbUpdated = Join-Path $root 'data/research_sources/other/banc_2026/supplemental_data_3.txt'
$flywire = Join-Path $root 'data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv'
$missing = Join-Path $root 'data/research_sources/derived/model_missing_fafb_ids.csv'
$reviewed = Join-Path $root 'data/research_sources/other/banc_2026/banc_fafb_reviewed_matches.csv.gz'
$outDir = Join-Path $root 'data/research_sources/other/banc_2026'

$officialIds = [System.Collections.Generic.HashSet[string]]::new()
Import-Csv -LiteralPath $flywire -Delimiter "`t" | ForEach-Object { [void]$officialIds.Add($_.root_id) }
$missingIds = [System.Collections.Generic.HashSet[string]]::new()
Import-Csv -LiteralPath $missing | ForEach-Object { [void]$missingIds.Add($_.root_id) }
$bancIds = [System.Collections.Generic.HashSet[string]]::new()
$matchedFafbIds = [System.Collections.Generic.HashSet[string]]::new()
$matchedMissingFafbIds = [System.Collections.Generic.HashSet[string]]::new()
$matchedRows = 0
$validRows = 0
$invalidRows = 0
$allRows = 0
$dnRows = 0
$anRows = 0
$motorRows = 0
$matchForMissingRows = [System.Collections.Generic.List[object]]::new()

Import-Csv -LiteralPath $source | ForEach-Object {
  $allRows++
  [void]$bancIds.Add($_.root_id)
  if ($_.super_class -eq 'descending') { $dnRows++ }
  if ($_.super_class -eq 'ascending') { $anRows++ }
  if ($_.super_class -eq 'motor') { $motorRows++ }
  if ($_.fafb_match -and $_.fafb_match -ne 'NA') {
    $matchedRows++
    [void]$matchedFafbIds.Add($_.fafb_match)
    if ($officialIds.Contains($_.fafb_match)) { $validRows++ } else { $invalidRows++ }
    if ($missingIds.Contains($_.fafb_match)) {
      [void]$matchedMissingFafbIds.Add($_.fafb_match)
      $matchForMissingRows.Add([pscustomobject]@{
        fafb_v783_root_id = $_.fafb_match
        banc_v888_root_id = $_.root_id
        banc_super_class = $_.super_class
        banc_cell_class = $_.cell_class
        banc_cell_type = $_.cell_type
        banc_region = $_.region
        banc_side = $_.side
        banc_cell_function = $_.cell_function
        evidence = 'cross-animal_match_only_no_exact_synapse_transfer'
      })
    }
  }
}
$crosswalkPath = Join-Path $outDir 'banc_matches_for_616_fafb_missing_ids.csv'
$matchForMissingRows | Export-Csv -LiteralPath $crosswalkPath -NoTypeInformation -Encoding utf8
$reviewedTotal = 0
$reviewedValid = 0
$reviewedInvalid = 0
$reviewedValidNonNumericIds = 0
$reviewedMissingRows = [System.Collections.Generic.List[object]]::new()
$reviewedMissingIds = [System.Collections.Generic.HashSet[string]]::new()
Import-Csv -LiteralPath $reviewed | ForEach-Object {
  $reviewedTotal++
  if ($_.valid -eq 't') {
    $reviewedValid++
    if ($_.query_id -notmatch '^\d+$' -or $_.match_id -notmatch '^\d+$') {
      $reviewedValidNonNumericIds++
      return
    }
    if ($missingIds.Contains($_.match_id)) {
      [void]$reviewedMissingIds.Add($_.match_id)
      $reviewedMissingRows.Add([pscustomobject]@{
        fafb_v783_root_id = $_.match_id
        banc_v888_root_id = $_.query_id
        banc_matched_cell_type = $_.match_cell_type
        reviewed_valid = $_.valid
        evidence = 'reviewed_cross_animal_match_only_no_exact_synapse_transfer'
      })
    }
  } else { $reviewedInvalid++ }
}
$reviewedMissingRows | Export-Csv -LiteralPath (Join-Path $outDir 'banc_reviewed_matches_for_616_fafb_missing_ids.csv') -NoTypeInformation -Encoding utf8
$functionRows = @(Import-Csv -LiteralPath $functions)
$anDnRows = @(Import-Csv -LiteralPath $anDnClusters)
$effectorRows = @(Import-Csv -LiteralPath $effectorClusters)
$fafbUpdatedRows = 0
$fafbUpdatedInOfficial = 0
$fafbUpdatedOutsideOfficial = 0
$fafbUpdatedMissing = [System.Collections.Generic.List[object]]::new()
Import-Csv -LiteralPath $fafbUpdated | ForEach-Object {
  $fafbUpdatedRows++
  if ($officialIds.Contains($_.root_783)) { $fafbUpdatedInOfficial++ } else { $fafbUpdatedOutsideOfficial++ }
  if ($missingIds.Contains($_.root_783)) { $fafbUpdatedMissing.Add($_) }
}
$fafbUpdatedMissing | Export-Csv -LiteralPath (Join-Path $outDir 'banc_updated_fafb_annotations_for_616.csv') -NoTypeInformation -Encoding utf8
$audit = [ordered]@{
  paper = 'Bates et al. Nature 2026, doi:10.1038/s41586-026-10735-w'
  dataset = 'Harvard Dataverse doi:10.7910/DVN/7WTH1N; BANC v888'
  source_table = 'supplemental_data_2.txt'
  official_fafb_annotation = 'flywire_annotations v2.1.0'
  source_rows = $allRows
  unique_banc_v888_root_ids = $bancIds.Count
  rows_with_fafb_match = $matchedRows
  unique_fafb_match_ids = $matchedFafbIds.Count
  matched_rows_whose_fafb_id_is_in_official_v783_annotations = $validRows
  matched_rows_whose_fafb_id_is_not_in_official_v783_annotations = $invalidRows
  official_fafb_v783_ids = $officialIds.Count
  fafb_v783_ids_without_original_proofread_edge = $missingIds.Count
  those_missing_ids_with_banc_match = $matchedMissingFafbIds.Count
  banc_rows_matching_those_missing_ids = $matchForMissingRows.Count
  banc_descending_rows = $dnRows
  banc_ascending_rows = $anRows
  banc_motor_rows = $motorRows
  literature_function_rows = $functionRows.Count
  an_dn_cluster_rows = $anDnRows.Count
  an_dn_cluster_names = @($anDnRows | Where-Object { $_.super_cluster -and $_.super_cluster -ne 'NA' } | Select-Object -ExpandProperty super_cluster -Unique | Sort-Object)
  effector_cluster_rows = $effectorRows.Count
  effector_cluster_names = @($effectorRows | Where-Object { $_.super_cluster -and $_.super_cluster -ne 'NA' } | Select-Object -ExpandProperty super_cluster -Unique | Sort-Object)
  updated_fafb_metadata_rows = $fafbUpdatedRows
  updated_fafb_metadata_rows_in_official_v783_annotations = $fafbUpdatedInOfficial
  updated_fafb_metadata_rows_outside_official_v783_annotations = $fafbUpdatedOutsideOfficial
  updated_fafb_metadata_rows_for_missing_616 = $fafbUpdatedMissing.Count
  reviewed_fafb_matches_total_rows = $reviewedTotal
  reviewed_fafb_matches_valid_rows = $reviewedValid
  reviewed_fafb_matches_invalid_rows = $reviewedInvalid
  reviewed_valid_rows_with_non_numeric_root_ids = $reviewedValidNonNumericIds
  reviewed_valid_missing_fafb_ids = $reviewedMissingIds.Count
  reviewed_valid_rows_for_missing_fafb_ids = $reviewedMissingRows.Count
  derived_crosswalk = 'banc_matches_for_616_fafb_missing_ids.csv'
  derived_reviewed_crosswalk = 'banc_reviewed_matches_for_616_fafb_missing_ids.csv'
  derived_updated_fafb_annotations_for_missing = 'banc_updated_fafb_annotations_for_616.csv'
  interpretation = 'The FAFB match ID links corresponding neurons across different fly specimens. It is not an identical physical neuron or an observed FAFB synapse. Match IDs can recur in BANC rows.'
}
$audit | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $outDir 'crosswalk_audit.json') -Encoding utf8
$audit | ConvertTo-Json -Depth 4
