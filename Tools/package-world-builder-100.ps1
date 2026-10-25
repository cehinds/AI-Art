param(
    [string]$Destination = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Destination) { $Destination = Join-Path $projectRoot 'Review/world-builder-100.zip' }
$destinationPath = [IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $destinationPath) { throw "Preserved existing archive: $destinationPath. Supply a new -Destination for another revision." }
$manifest = Get-Content -LiteralPath (Join-Path $projectRoot 'Assets/Art/Production/RemasterExpansion/manifest.json') -Raw | ConvertFrom-Json
$selected = @($manifest.assets | Where-Object { $_.source.path -match '^ArtSource/RemasterExpansion/(biomes-natural|biomes-extreme|world-objects)/' })
$tiles = @($selected | Where-Object { $_.kind -eq 'tile' })
$sprites = @($selected | Where-Object { $_.kind -eq 'sprite' })
if ($tiles.Count -ne 100 -or $sprites.Count -ne 32) { throw "Expected exactly 100 tiles and 32 sprites, found $($tiles.Count) tiles and $($sprites.Count) sprites." }
$entries = @()
foreach ($asset in $selected) {
    $sourceFile = Join-Path $projectRoot $asset.path
    if ((Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $asset.sha256) { throw "Asset hash mismatch: $($asset.path)" }
    $prefix = if ($asset.kind -eq 'tile') { 'tiles' } else { 'sprites' }
    $archivePath = "$prefix/$($asset.owner)/$($asset.name).png"
    $entries += [pscustomobject]@{
        id = $asset.id; file = $archivePath; originalPath = $asset.path
        kind = $asset.kind; owner = $asset.owner; state = $asset.name
        width = $asset.width; height = $asset.height; pixelsPerUnit = $asset.ppu
        pivot = $asset.pivot; filter = $asset.filter; sha256 = $asset.sha256
        source = $asset.source.path
    }
}
if (@($entries.file | Select-Object -Unique).Count -ne 132) { throw 'Duplicate archive file names.' }
$support = @()
foreach ($fileName in @('construction-guide.md', 'inventory.json', 'tiles-100-native-atlas.png', 'atlas-coordinates.json')) {
    $sourcePath = "Review/remaster-expansion/worldbuilder100/$fileName"
    $sourceFile = Join-Path $projectRoot $sourcePath
    if (-not (Test-Path -LiteralPath $sourceFile)) { throw "Missing package support file: $sourcePath" }
    $support += [pscustomobject]@{ file = $fileName; originalPath = $sourcePath; sha256 = (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$packageManifest = [ordered]@{
    schema = 1; name = 'World Builder 100'; tileCount = 100; spriteCount = 32
    state = 'Generated review candidates; Unity runtime unverified'
    assets = $entries
}
$readme = @'
# World Builder 100

100 native 32x32 terrain tiles across ten biome families, plus 32 transparent object sprites:
16 directional vehicles at 128x128, 8 trees at 64x64, 4 mountain landmarks and 4 cavern entrances at 64x64.

All assets use 32 pixels per Unity unit. Tile pivots are centered; object pivots are specified per asset
in manifest.json. Import with Sprite(2D/UI), Point filtering, no compression, no mipmaps, Clamp wrapping.
Vehicles are static down/left/right/up views, not animated motion clips. The fantasy propeller plane
is an optional original extension. Transparent frame bounds are not collision footprints.

Terrain sets use NW/N/NE, W/center/E, SW/S/SE outer pieces plus an alternate center. They do not
include a complete inner-corner/autotile matrix or every cross-biome transition. Visible joins and
material repetition still require visual cleanup. Test actual placement before building finished maps.

Generated with the built-in ImageGen tool using online FFII references and approved project art.
Online reference images are not packaged. Source prompts and provenance remain in the project:
Docs/WorldObjectSources.md, Docs/BiomesNaturalSources.md, Docs/BiomesExtremeSources.md,
References/WorldBuilder100/README.md and ArtSource/RemasterExpansion source folders.

PNG files are authoritative. manifest.json gives file hashes, dimensions, PPU, pivots and source paths.
The 320x320 packed atlas contains the same 100 tiles; atlas-coordinates.json maps its cells to IDs.
It is a convenience copy, not another 100 distinct assets. construction-guide.md explains placement.
These are exported review assets, not a playable game or validated Unity scene.
'@
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archiveStream = [IO.File]::Open($destinationPath, [IO.FileMode]::CreateNew)
$archive = [IO.Compression.ZipArchive]::new($archiveStream, [IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($entry in $entries) {
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, (Join-Path $projectRoot $entry.originalPath), $entry.file) | Out-Null
    }
    foreach ($entry in $support) {
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, (Join-Path $projectRoot $entry.originalPath), $entry.file) | Out-Null
    }
    foreach ($item in @(@('manifest.json', ($packageManifest | ConvertTo-Json -Depth 15)), @('README.md', $readme))) {
        $entry = $archive.CreateEntry($item[0])
        $writer = [IO.StreamWriter]::new($entry.Open(), [Text.UTF8Encoding]::new($false))
        try { $writer.Write($item[1]) } finally { $writer.Dispose() }
    }
} finally { $archive.Dispose(); $archiveStream.Dispose() }
$check = [IO.Compression.ZipFile]::OpenRead($destinationPath)
try {
    if ($check.Entries.Count -ne (134 + $support.Count)) { throw "Archive count mismatch: $($check.Entries.Count)" }
    foreach ($item in @($entries) + @($support)) {
        $stream = $check.GetEntry($item.file).Open()
        $sha = [Security.Cryptography.SHA256]::Create()
        try {
            $digest = [Convert]::ToHexString($sha.ComputeHash($stream)).ToLowerInvariant()
            if ($digest -ne $item.sha256) { throw "Packaged hash mismatch: $($item.file)" }
        } finally { $sha.Dispose(); $stream.Dispose() }
    }
} finally { $check.Dispose() }
Write-Output "PASS: 100 tiles + 32 sprites, 132 PNG hashes verified inside $destinationPath"
