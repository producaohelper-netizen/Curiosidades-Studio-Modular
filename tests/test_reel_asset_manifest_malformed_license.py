"""Regression tests: malformed license declarations must fail closed."""
import unittest

from universal_engine.reel_asset_manifest import AssetRightsError, validate_asset_manifest


class MalformedLicenseTests(unittest.TestCase):
    def test_non_string_license_values_are_rejected(self):
        for value in (None, [], {}, ["CC0-1.0"], 42, True):
            with self.subTest(value=value):
                manifest = {"assets": [{
                    "filename": "frame.png",
                    "license": value,
                    "author": "Example photographer",
                    "source_url": "https://example.org/frame.png",
                }]}
                with self.assertRaises(AssetRightsError):
                    validate_asset_manifest(manifest, ["frame.png"])


if __name__ == "__main__":
    unittest.main()
