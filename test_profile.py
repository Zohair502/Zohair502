"""Checks for truthful public statistics and GitHub-safe README assets."""
import base64
import importlib.util
import re
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('profile_stats', ROOT / 'update-profile.py')
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


class ProfileTests(unittest.TestCase):
    def test_private_and_fork_metrics(self):
        repos = [
            dict(private=False, fork=False, stargazers_count=3, forks_count=2),
            dict(private=False, fork=True, stargazers_count=90, forks_count=80),
            dict(private=True, fork=False, stargazers_count=999, forks_count=999),
            dict(fork=False, stargazers_count=999, forks_count=999),
        ]
        self.assertEqual([v for v, _ in stats.metrics_for(repos)], [2, 1, 3, 2])

    def test_pagination_and_failed_refresh_preserve_existing_cards(self):
        repo = dict(private=False, fork=False, stargazers_count=0, forks_count=0)
        with patch.object(stats, 'public_json', side_effect=[[repo]*100, []]) as request:
            with patch.object(Path, 'write_text') as write:
                stats.main()
        self.assertEqual(request.call_count, 2)
        self.assertIn('page=2', request.call_args.args[0])
        self.assertEqual(write.call_count, 2)
        with patch.object(stats, 'public_json', side_effect=OSError('API unavailable')):
            with patch.object(Path, 'write_text') as write:
                with self.assertRaises(OSError):
                    stats.main()
                write.assert_not_called()

    def test_readme_references_and_svg_safety(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertNotRegex(readme, r'(?i)<(?:script|iframe|style)|\sstyle=|javascript:')
        for ref in re.findall(r'(?:src|srcset)="([^"]+)"', readme):
            self.assertTrue(ref.startswith('./'), ref)
            self.assertTrue((ROOT / ref).is_file(), ref)
        for path in ROOT.rglob('*.svg'):
            svg = ET.parse(path).getroot()
            self.assertEqual(svg.tag, '{http://www.w3.org/2000/svg}svg')
            for element in svg.iter():
                self.assertNotIn(element.tag.split('}')[-1].lower(), ('script', 'foreignobject'))
                for key, value in element.attrib.items():
                    self.assertFalse(key.lower().startswith('on'), (path, key))
                    if key.endswith('href'):
                        self.assertTrue(value.startswith(('data:image/', '#')), (path, key))

    def test_portrait_embeds_exact_original_bytes(self):
        original = (ROOT / 'assets/portrait-original.png').read_bytes()
        for path in (ROOT / 'banner.svg', ROOT / 'assets/hero-mobile.svg'):
            svg = ET.parse(path).getroot()
            image = svg.find('.//{http://www.w3.org/2000/svg}image')
            self.assertEqual(base64.b64decode(image.attrib['href'].split(',', 1)[1]), original)


if __name__ == '__main__':
    unittest.main()
