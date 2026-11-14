import tempfile,unittest,json
from pathlib import Path
from universal_engine.trends import parse_rss,traffic,top_five,save_results,Trend
RSS=b"""<?xml version="1.0"?><rss xmlns:ht="https://trends.google.com/trending/rss"><channel>
<item><title>cnj</title><ht:approx_traffic>100K+</ht:approx_traffic><pubDate>Sat</pubDate></item>
<item><title>El Niño</title><ht:approx_traffic>50K+</ht:approx_traffic><pubDate>Sat</pubDate></item>
<item><title>Eclipse lunar</title><ht:approx_traffic>20K+</ht:approx_traffic><pubDate>Sat</pubDate></item>
<item><title>Atlético X Clube</title><ht:approx_traffic>200K+</ht:approx_traffic><pubDate>Sat</pubDate></item>
</channel></rss>"""
class TrendTests(unittest.TestCase):
 def test_volume(self):
  self.assertEqual(traffic("50K+"),50000)
  self.assertEqual(traffic("2M+"),2000000)
 def test_reject_unsuitable_topic(self):
  selected=top_five(parse_rss(RSS))
  names=[x["title"] for x in selected]
  self.assertNotIn("cnj",names)
  self.assertIn("El Niño",names)
  self.assertIn("Eclipse lunar",names)
 def test_rss_origin_and_manifest(self):
  with tempfile.TemporaryDirectory() as d:
   f=save_results(top_five(parse_rss(RSS)),Path(d)/"trends.json")
   data=json.loads(f.read_text())
   self.assertIn("trending/rss?geo=BR",data["source"])
   self.assertIn("recent RSS",data["ranking_scope"])
if __name__=="__main__":unittest.main()
