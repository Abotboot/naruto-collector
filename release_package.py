"""Create clean immutable public releases from an explicitly inventoried frozen build."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

from release_info import APP_ID, APP_VERSION, UPDATE_REPOSITORY

ROOT_FILES = {'Naruto Collector.exe', 'Naruto Update Helper.exe', 'entry-collector.swf',
              'bridge.json', 'chat-answers.json', 'quiz-reviewed.json', 'requirements.txt',
              'variety-shop-qualification.json', 'README.md'}
ROOT_DIRS = {'_internal', 'assets', 'licenses'}
SEEDS = {'chat-answers.json', 'quiz-reviewed.json'}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def inventory(root):
    result = {}
    seen = set()
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError('Linked release path')
        if not path.is_file():
            continue
        name = path.relative_to(root).as_posix()
        if name == 'app-release.json':
            continue
        parts = PurePosixPath(name).parts
        if name.casefold() in seen or any(':' in p or '\\' in p or p.endswith(('.', ' ')) for p in parts):
            raise ValueError('Unsafe/colliding release path')
        seen.add(name.casefold())
        if len(parts) == 1 and name not in ROOT_FILES or len(parts) > 1 and parts[0] not in ROOT_DIRS:
            raise ValueError('Unapproved public runtime path: ' + name)
        if any(p.casefold() in {'profiles', 'history', 'cache', '__pycache__', '.git', 'source', 'work',
                                'settings.json', 'profiles.json', 'balance-ledger.csv', 'pending-claims.json'} for p in parts):
            raise ValueError('Private release path: ' + name)
        if path.suffix.casefold() in {'.py', '.pyc', '.ps1', '.log', '.csv', '.sqlite', '.db', '.pem', '.key'}:
            raise ValueError('Source/private release file: ' + name)
        result[name] = sha(path)
    return result


def write_inventory(root):
    files = inventory(root)
    if not {'Naruto Collector.exe', 'Naruto Update Helper.exe', 'bridge.json', 'entry-collector.swf'} <= files.keys():
        raise ValueError('Incomplete frozen runtime')
    write_json(root / 'app-release.json', dict(schemaVersion=1, appId=APP_ID, version=APP_VERSION, files=files))
    return files


def package(root, output, notes):
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Release output must be outside runtime')
    files = inventory(root)
    record = json.loads((root / 'app-release.json').read_text(encoding='utf-8'))
    if record != dict(schemaVersion=1, appId=APP_ID, version=APP_VERSION, files=files):
        raise ValueError('Frozen inventory differs')
    # Banks are public seeds produced by Build EXE.ps1, never copied from an install.
    chat = json.loads((root / 'chat-answers.json').read_text(encoding='utf-8'))
    quiz = json.loads((root / 'quiz-reviewed.json').read_text(encoding='utf-8'))
    if set(chat) != {'answers'} or not isinstance(chat['answers'], dict) or not isinstance(quiz, dict):
        raise ValueError('Public bank schema differs')
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in quiz.items()):
        raise ValueError('Public reviewed bank schema differs')
    # Clients reject update.json over 64 KiB; it is written as UTF-8, not ASCII.
    if len(notes.encode('utf-8')) > 32000:
        raise ValueError('Release notes too long')
    asset = output / f'Naruto-Collector-{APP_VERSION}-Windows.zip'
    manifest = dict(schemaVersion=1, appId=APP_ID, version=APP_VERSION,
                    url=f'https://github.com/{UPDATE_REPOSITORY}/releases/download/v{APP_VERSION}/{asset.name}',
                    size=2**63 - 1, sha256='0' * 64, notes=notes)
    # JSON escapes control characters; the UTF-8 notes bound alone is insufficient.
    # Reserve the largest supported size field before creating an immutable bundle.
    if len((json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')) > 65536:
        raise ValueError('Serialized update manifest too long')
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(asset, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted([*files, 'app-release.json']):
            item = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, (root / name).read_bytes())
    # Detect source mutation while packaging.
    if inventory(root) != files:
        raise ValueError('Runtime changed during packaging')
    manifest.update(size=asset.stat().st_size, sha256=sha(asset))
    write_json(output / 'update.json', manifest)
    (output / 'app-release.json').write_bytes((root / 'app-release.json').read_bytes())
    (output / 'RELEASE-NOTES.md').write_text(notes + '\n', encoding='utf-8')
    (output / 'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(output.iterdir()) if p.is_file()), encoding='utf-8')
    return manifest


def version_resource(path):
    if not re.fullmatch(r'\d+\.\d+\.\d+', APP_VERSION):
        raise ValueError('Invalid application version')
    version = tuple(map(int, APP_VERSION.split('.'))) + (0,)
    path.write_text("VSVersionInfo(ffi=FixedFileInfo(filevers=" + repr(version) + ", prodvers=" + repr(version) + ", mask=0x3f, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0,0)), kids=[StringFileInfo([StringTable('040904B0',[StringStruct('FileDescription','Naruto Collector'),StringStruct('ProductName','Naruto Collector'),StringStruct('FileVersion','" + APP_VERSION + "'),StringStruct('ProductVersion','" + APP_VERSION + "')])]),VarFileInfo([VarStruct('Translation',[1033,1200])])])", encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('inventory'); p.add_argument('root', type=Path)
    p = sub.add_parser('version-resource'); p.add_argument('path', type=Path)
    p = sub.add_parser('package'); p.add_argument('root', type=Path); p.add_argument('output', type=Path); p.add_argument('--notes', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'inventory':
        print(json.dumps({'runtimeFiles': len(write_inventory(args.root)) + 1}))
    elif args.command == 'version-resource':
        version_resource(args.path)
    else:
        result = package(args.root, args.output, args.notes.read_text(encoding='utf-8'))
        print(json.dumps({k: result[k] for k in ('version', 'size', 'sha256')}))


if __name__ == '__main__':
    main()
