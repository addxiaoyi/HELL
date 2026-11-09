import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from build_plugin_catalog import build_catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / "source" / "sample"
        self.folder.mkdir(parents=True)
        self.manifest = {"apiVersion": 1, "id": "sample-plugin", "version": "1.0.0", "name": "测试插件", "modules": [{"id": "notes", "title": "便签", "kind": "notes", "settings": {}}]}
        self.write()

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        (self.folder / "plugin.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def build(self, url="https://plugins.example.org/releases"):
        return build_catalog(self.root / "source", self.root / "output", url)

    def test_reproducible_package_hash_and_manifest(self):
        listing = self.build()["plugins"][0]
        package = self.root / "output" / "sample-plugin-1.0.0.hellplugin"
        self.assertEqual(listing["sha256"], hashlib.sha256(package.read_bytes()).hexdigest())
        self.assertEqual(listing["sha256"], self.build()["plugins"][0]["sha256"])
        (self.folder / "plugin.json").write_bytes(json.dumps(self.manifest, indent=4).replace("\n", "\r\n").encode("utf-8"))
        self.assertEqual(listing["sha256"], self.build()["plugins"][0]["sha256"])
        with zipfile.ZipFile(package) as archive:
            self.assertEqual(json.loads(archive.read("plugin.json")), self.manifest)

    def test_executable_is_rejected(self):
        (self.folder / "payload.dll").write_bytes(b"bad")
        with self.assertRaises(ValueError):
            self.build()

    def test_missing_image_is_rejected(self):
        self.manifest["modules"][0]["settings"]["image"] = "assets/missing.png"
        self.write()
        with self.assertRaises(ValueError):
            self.build()

    def test_duplicate_plugin_id_is_rejected(self):
        duplicate = self.root / "source" / "duplicate"
        duplicate.mkdir()
        (duplicate / "plugin.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.build()

    def test_insecure_host_is_rejected(self):
        for url in ("http://example.org", "https://user:password@example.org", "https://example.org/?query"):
            with self.assertRaises(ValueError):
                self.build(url)

    def test_output_cannot_pollute_source(self):
        with self.assertRaises(ValueError):
            build_catalog(self.root / "source", self.folder / "output", "https://plugins.example.org")

    def test_screenshot_must_exist_inside_package(self):
        for image in ("assets/missing.png", "../private.png"):
            self.manifest["screenshots"] = [image]
            self.write()
            with self.assertRaises(ValueError):
                self.build()

    def test_release_notes_reject_invalid_date(self):
        self.manifest["releases"] = [{"version": "1.1.0", "date": "2026-99-99", "notes": "Updated"}]
        self.write()
        with self.assertRaises(ValueError):
            self.build()


if __name__ == "__main__":
    unittest.main()
