"""Build validated, reproducible launcher packages and a static HTTPS catalog."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse

MAX_BYTES = 16 * 1024 * 1024
KINDS = {"notes", "clock", "links", "image", "system"}
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
ID = re.compile(r"[a-z][a-z0-9-]{1,62}\Z")
VERSION = re.compile(r"\d+\.\d+(?:\.\d+){0,2}\Z")


def valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password


def inspect_manifest(folder: Path) -> tuple[dict, list[Path]]:
    manifest_file = folder / "plugin.json"
    if manifest_file.stat().st_size > 512 * 1024:
        raise ValueError(f"{folder}: plugin.json exceeds 512 KB")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8-sig"))
    if not isinstance(manifest, dict):
        raise ValueError(f"{folder}: manifest must be an object")
    if manifest.get("apiVersion") != 1 or not ID.fullmatch(manifest.get("id", "")):
        raise ValueError(f"{folder}: invalid API version or plugin ID")
    if not VERSION.fullmatch(manifest.get("version", "")) or any(int(part) > 2147483647 for part in manifest["version"].split(".")):
        raise ValueError(f"{folder}: invalid version")
    for key, limit, required in (("name", 80, True), ("author", 100, False), ("description", 2000, False)):
        value = manifest.get(key, "")
        if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
            raise ValueError(f"{folder}: invalid {key}")
    modules = manifest.get("modules", [])
    if not isinstance(modules, list) or not 1 <= len(modules) <= 20:
        raise ValueError(f"{folder}: expected 1-20 modules")
    ids: set[str] = set()
    for module in modules:
        if not isinstance(module, dict):
            raise ValueError(f"{folder}: module must be an object")
        module_id = module.get("id", "")
        if not ID.fullmatch(module_id) or module_id in ids or module.get("kind") not in KINDS:
            raise ValueError(f"{folder}: invalid or duplicate module")
        ids.add(module_id)
        if not isinstance(module.get("title"), str) or not 1 <= len(module["title"].strip()) <= 80:
            raise ValueError(f"{folder}: invalid module title")
        settings = module.get("settings", {})
        if not isinstance(settings, dict) or len(settings) > 20 or any(not isinstance(value, str) or len(value) > 20000 or len(key) > 80 for key, value in settings.items()):
            raise ValueError(f"{folder}: invalid module settings")
        if settings.get("url") and not valid_url(settings["url"]):
            raise ValueError(f"{folder}: links must use HTTPS")
        if settings.get("image"):
            image = Path(settings["image"])
            if image.as_posix() != settings["image"] or not image.parts or image.parts[0] != "assets" or ".." in image.parts or image.suffix.lower() not in IMAGE_TYPES or not (folder / image).is_file():
                raise ValueError(f"{folder}: invalid or missing image")
    files = sorted(path for path in folder.rglob("*") if path.is_file())
    if len(files) > 128 or sum(path.stat().st_size for path in files) > MAX_BYTES:
        raise ValueError(f"{folder}: package exceeds file or size limit")
    names: set[str] = set()
    for path in files:
        relative = path.relative_to(folder).as_posix()
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != folder.parent):
            raise ValueError(f"{folder}: symlinks are not supported")
        if relative.lower() in names or (relative != "plugin.json" and (not relative.startswith("assets/") or path.suffix.lower() not in IMAGE_TYPES or ":" in relative or "\\" in relative)):
            raise ValueError(f"{folder}: unsupported package entry {relative}")
        names.add(relative.lower())
    return manifest, files


def build_catalog(source: Path, output: Path, base_url: str) -> dict:
    if not valid_url(base_url) or urlparse(base_url).query or urlparse(base_url).fragment:
        raise ValueError("--base-url must be an HTTPS directory URL without query or fragment")
    source = source.resolve()
    output = output.resolve()
    if output == source or source in output.parents:
        raise ValueError("Output must be outside the plugin source directory")
    inspected = [inspect_manifest(path.parent) for path in sorted(source.glob("*/plugin.json"))]
    if not inspected:
        raise ValueError("No plugin.json files found in plugin subdirectories")
    ids: set[str] = set()
    for manifest, _ in inspected:
        if manifest["id"] in ids:
            raise ValueError("Duplicate plugin ID: " + manifest["id"])
        ids.add(manifest["id"])
    output.mkdir(parents=True, exist_ok=True)
    entries, hashes = [], []
    for manifest, files in inspected:
        package_name = f'{manifest["id"]}-{manifest["version"]}.hellplugin'
        package = output / package_name
        root = next(path.parent for path in files if path.name == "plugin.json")
        with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_STORED) as archive:
            for path in files:
                entry = zipfile.ZipInfo(path.relative_to(root).as_posix(), (2026, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                content = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8") if entry.filename == "plugin.json" else path.read_bytes()
                archive.writestr(entry, content)
        if package.stat().st_size > MAX_BYTES:
            raise ValueError(f"{package_name}: compressed package too large")
        checksum = hashlib.sha256(package.read_bytes()).hexdigest()
        entries.append({"manifest": manifest, "packageUrl": base_url.rstrip("/") + "/" + package_name, "sha256": checksum})
        hashes.append(checksum + "  " + package_name)
    catalog = {"version": 1, "plugins": entries}
    (output / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "SHA256SUMS").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    return catalog


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("examples/launcher-plugins"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    try:
        catalog = build_catalog(args.source, args.output, args.base_url)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"Plugin catalog build failed: {error}\n")
    print(f"Built {len(catalog['plugins'])} packages and catalog.json in {args.output}")
