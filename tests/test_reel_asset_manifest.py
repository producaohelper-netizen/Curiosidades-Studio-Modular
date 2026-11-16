import unittest
from universal_engine.reel_asset_manifest import AssetRightsError, validate_asset_manifest


def manifest():
    return {"assets": [
        {"filename": "gancho.png", "license": "CC-BY-4.0", "author": "Autor A", "source_url": "https://commons.wikimedia.org/wiki/File:Example.png"},
        {"filename": "contexto.png", "license": "OWN-WORK", "author": "Equipe", "source_url": "https://example.org/portfolio"},
    ]}


class AssetManifestTests(unittest.TestCase):
    def test_complete_manifest_still_requires_human_verification(self):
        result = validate_asset_manifest(manifest(), ["gancho.png", "contexto.png"])
        self.assertEqual(result["assets_documented"], 2)
        self.assertFalse(result["rights_independently_verified"])
        self.assertFalse(result["publication_approved"])

    def test_missing_license_rejected(self):
        data = manifest()
        del data["assets"][0]["license"]
        with self.assertRaises(AssetRightsError):
            validate_asset_manifest(data, ["gancho.png", "contexto.png"])

    def test_wrong_image_order_rejected(self):
        with self.assertRaises(AssetRightsError):
            validate_asset_manifest(manifest(), ["contexto.png", "gancho.png"])

    def test_missing_author_rejected(self):
        data = manifest()
        data["assets"][0]["author"] = ""
        with self.assertRaises(AssetRightsError):
            validate_asset_manifest(data, ["gancho.png", "contexto.png"])

    def test_untrusted_origin_rejected(self):
        data = manifest()
        data["assets"][0]["source_url"] = "file:///private/image.png"
        with self.assertRaises(AssetRightsError):
            validate_asset_manifest(data, ["gancho.png", "contexto.png"])


if __name__ == "__main__":
    unittest.main()
