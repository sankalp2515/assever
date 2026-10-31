$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $project
$stamp = Get-Date -Format 'yyyyMMddHHmmss'
$out = Join-Path $project "outputs/assever-evidence/backup-$stamp"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$container = (docker compose -f compose.assever.yml ps -q postgres).Trim()
docker compose -f compose.assever.yml stop api worker | Out-Null
try {
  $results = @()
  foreach ($database in @('assever_ledger','assever_sink')) {
    $restored = "${database}_verify_$stamp"
    docker exec $container pg_dump -U postgres -Fc -f "/tmp/$database.dump" $database
    if ($LASTEXITCODE -ne 0) { throw "Backup failed: $database" }
    docker cp "${container}:/tmp/$database.dump" (Join-Path $out "$database.dump") | Out-Null
    docker exec $container createdb -U postgres $restored
    docker exec $container pg_restore -U postgres --no-owner -d $restored "/tmp/$database.dump"
    if ($LASTEXITCODE -ne 0) { throw "Restore failed: $database" }
    $tables = if ($database -eq 'assever_ledger') { @('schema_versions','sessions','contracts','demand_lines','slots','grants','quotes','proposals','operations','reservations','outbox','observations','events','callbacks','exceptions','lab_runs','model_runs') } else { @('sink_operations','sink_effects','sink_notices') }
    foreach ($table in $tables) {
      # Correctly balanced aggregate expression, built only from fixed local identifiers.
      $sql = "SELECT count(*)::text || ':' || COALESCE(md5(string_agg(row_to_json(t)::text, ',' ORDER BY row_to_json(t)::text)), 'empty') FROM $table t"
      $before = (docker exec $container psql -U postgres -d $database -Atc $sql).Trim()
      $after = (docker exec $container psql -U postgres -d $restored -Atc $sql).Trim()
      if ($before -ne $after) { throw "Restored fingerprint differs: $table" }
      $results += [PSCustomObject]@{database=$database;table=$table;source=$before;restored=$after;match=$true}
    }
  }
  $results | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'verification.json')
  Write-Output "Verified backup/restore: $out"
} finally { docker compose -f compose.assever.yml up -d api worker | Out-Null }
