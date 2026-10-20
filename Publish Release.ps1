param(
    [Parameter(Mandatory=$true)][string]$Bundle,
    [switch]$Publish,
    [string]$PythonExe = ''
)
$ErrorActionPreference = 'Stop'
$bundleRoot = (Resolve-Path -LiteralPath $Bundle).Path
$manifest = Get-Content -LiteralPath (Join-Path $bundleRoot 'update.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $PythonExe) { $PythonExe = Join-Path $PSScriptRoot '.build-env/Scripts/python.exe' }
$verify = @'
import hashlib,json,pathlib,sys,zipfile
sys.path.insert(0,sys.argv[1])
from release_info import APP_ID,APP_VERSION,UPDATE_REPOSITORY
p=pathlib.Path(sys.argv[2]); m=json.loads((p/'update.json').read_text(encoding='utf-8'))
assert set(m)=={'schemaVersion','appId','version','url','size','sha256','notes'}
assert m['schemaVersion']==1 and m['appId']==APP_ID and m['version']==APP_VERSION
asset=p/f'Naruto-Collector-{APP_VERSION}-Windows.zip'
assert m['url']==f'https://github.com/{UPDATE_REPOSITORY}/releases/download/v{APP_VERSION}/{asset.name}'
assert asset.stat().st_size==m['size'] and hashlib.sha256(asset.read_bytes()).hexdigest()==m['sha256']
expected={asset.name,'update.json','app-release.json','RELEASE-NOTES.md','SHA256SUMS.txt'}
assert {x.name for x in p.iterdir()}==expected
for line in (p/'SHA256SUMS.txt').read_text().splitlines():
 digest,name=line.split('  ',1); assert name in expected-{'SHA256SUMS.txt'} and hashlib.sha256((p/name).read_bytes()).hexdigest()==digest
assert len((p/'SHA256SUMS.txt').read_text().splitlines())==4
with zipfile.ZipFile(asset) as z:
 r=json.loads((p/'app-release.json').read_bytes()); assert z.read('app-release.json')==(p/'app-release.json').read_bytes()
 assert set(z.namelist())==set(r['files'])|{'app-release.json'} and len(z.namelist())==len(r['files'])+1
 assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in r['files'].items())
print(UPDATE_REPOSITORY)
'@
$repository = & $PythonExe -B -c $verify $PSScriptRoot $bundleRoot
if ($LASTEXITCODE -ne 0) { throw 'Release bundle validation failed.' }
$repository = "$repository".Trim()
$tag = 'v' + $manifest.version
if (-not $Publish) {
    Write-Output "Verified browser upload bundle: $bundleRoot. Create immutable $tag draft in $repository; upload all five files, then publish as latest."
    return
}
Get-Command gh -ErrorAction Stop | Out-Null
& gh auth status --hostname github.com
if ($LASTEXITCODE -ne 0) { throw 'Authenticate local gh first; client EXEs never need tokens.' }
& gh release view $tag --repo $repository *> $null
if ($LASTEXITCODE -eq 0) { throw "Release $tag already exists; immutable releases cannot be overwritten." }
# Check repository access before interpreting an absent release.
& gh repo view $repository --json nameWithOwner --jq .nameWithOwner
if ($LASTEXITCODE -ne 0) { throw 'Repository access unavailable.' }
& gh api "repos/$repository/git/ref/tags/$tag" *> $null
if ($LASTEXITCODE -eq 0) { throw "Tag $tag already exists; choose a new application version." }
& gh release create $tag --repo $repository --draft --title "Naruto Collector $($manifest.version)" --notes-file (Join-Path $bundleRoot 'RELEASE-NOTES.md')
if ($LASTEXITCODE -ne 0) { throw 'Draft creation failed; nothing published.' }
$assets = @(Get-ChildItem -LiteralPath $bundleRoot -File | ForEach-Object FullName)
& gh release upload $tag @assets --repo $repository
if ($LASTEXITCODE -ne 0) { throw 'Upload failed. Draft retained for inspection; never clobber or promote incomplete assets.' }
$uploaded = & gh release view $tag --repo $repository --json assets
if ($LASTEXITCODE -ne 0) { throw 'Upload verification failed; draft retained.' }
$remote = $uploaded | ConvertFrom-Json
if (@($remote.assets).Count -ne $assets.Count) { throw 'Asset count differs; draft retained.' }
foreach ($asset in $assets) {
    $local = Get-Item -LiteralPath $asset
    $matches = @($remote.assets | Where-Object { $_.name -ceq $local.Name -and $_.size -eq $local.Length })
    if ($matches.Count -ne 1) { throw 'Remote asset metadata differs; draft retained.' }
}
& gh release edit $tag --repo $repository --draft=false --latest
if ($LASTEXITCODE -ne 0) { throw 'Draft promotion failed.' }
Write-Output "Published $repository $tag. Verify public update.json and ZIP digest independently."
