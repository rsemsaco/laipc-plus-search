"""Dependency-free structural checks for the isolated static landing page."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'docs'
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.links=[]; self.labels=[]; self.controls=[]; self.h1=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag=='h1': self.h1+=1
        if tag=='label' and 'for' in a: self.labels.append(a['for'])
        for key in ('href','src'):
            if key in a: self.links.append(a[key])
p=Page(); p.feed((ROOT/'index.html').read_text())
assert p.h1==1, 'One primary heading required'
assert len(p.ids)==len(set(p.ids)), 'Duplicate IDs'
for link in p.links:
    if link.startswith('#'): assert link[1:] in p.ids, f'Broken anchor: {link}'
    elif not urlsplit(link).scheme:
        assert (ROOT/unquote(urlsplit(link).path)).is_file(), f'Missing asset: {link}'
for label in p.labels: assert label in p.ids
js=(ROOT/'assets/site.js').read_text()
for target in re.findall(r"\$\('([^']+)'\)",js): assert target in p.ids, f'Missing JS target: {target}'
assert 'innerHTML' not in js, 'Keep user text out of HTML injection sinks'
assert 'fetch(' not in js and 'localStorage' not in js, 'Demo must remain local and transient'
assert 'prefers-reduced-motion' in (ROOT/'assets/site.css').read_text()
ET.parse(ROOT/'assets/symbol.svg'); ET.parse(ROOT/'sitemap.xml')
assert sum(f.stat().st_size for f in ROOT.rglob('*') if f.is_file()) < 100_000
print('PASS: anchors, assets, unique IDs, JS targets, SVG, sitemap, motion preference, local-only demo, <100 KB.')
