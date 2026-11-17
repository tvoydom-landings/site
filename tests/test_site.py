"""Проверки сайта: python3 -m unittest discover tests  (только стандартная библиотека).

Запускаются в GitHub Actions на каждом PR и перед публикацией: данные читаются, страницы собираются,
черновик закрыт от поисковиков, чистовая — без пометок черновика.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build  # noqa: E402
from template import Mortgage  # noqa: E402

HOUSES = sorted((ROOT / "data/houses").glob("*.json"))
REQUIRED = ("code", "name", "status", "price", "address", "village", "areas", "cadastral", "photos")


class Data(unittest.TestCase):
    def test_houses(self):
        self.assertTrue(HOUSES, "нет ни одного дома в data/houses/")
        for p in HOUSES:
            d = json.loads(p.read_text(encoding="utf-8"))
            with self.subTest(p.name):
                self.assertEqual(d["code"], p.stem, "имя файла = код дома = адрес страницы")
                self.assertRegex(d["code"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
                for k in REQUIRED:
                    self.assertIn(k, d)
                self.assertIsInstance(d["price"], int)
                self.assertIn(d["status"], ("в продаже", "задаток", "продан"))
                for ph in d["photos"]:
                    self.assertTrue((ROOT / "photos" / d["code"] / f"{ph['n']:02d}.jpg").exists(), ph)
                    self.assertTrue((ROOT / "photos" / d["code"] / f"{ph['n']:02d}-s.jpg").exists(), ph)

    def test_mortgage_texts(self):
        m = Mortgage(json.loads((ROOT / "data/mortgage.json").read_text(encoding="utf-8")))
        self.assertRegex(m.rate_range, r"^от [\d,]+ до [\d,]+ %$")
        self.assertIn("п.п.", m.subsidy_note())
        self.assertEqual(m.kids_buttons().count("<button"), m.max_kids)

    def test_check_finds_problems(self):
        self.assertTrue(build.check("x", '<script src="https://cdn.example.com/a.js"></script>'))
        self.assertTrue(build.check("x", '<img src="/img/01.jpg">'))
        self.assertFalse(build.check("x", '<img src="img/01.jpg"><link href="../shared/default/landing.css">'))


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.draft, cls.final = Path(cls.tmp.name, "draft"), Path(cls.tmp.name, "final")
        for out, draft in ((cls.draft, True), (cls.final, False)):
            problems = build.build(out, draft)
            assert not problems, problems

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def pages(self, out: Path):
        return {p.stem: (out / p.stem / "index.html").read_text(encoding="utf-8") for p in HOUSES}

    def test_draft_closed(self):
        self.assertIn("Disallow: /", (self.draft / "robots.txt").read_text())
        for code, h in self.pages(self.draft).items():
            with self.subTest(code):
                self.assertIn('<meta name="robots" content="noindex">', h)
                self.assertIn('class="draft-bar"', h)

    def test_final_clean(self):
        self.assertNotIn("Disallow", (self.final / "robots.txt").read_text())
        for code, h in self.pages(self.final).items():
            with self.subTest(code):
                for mark in ('class="draft-bar"', 'class="need"', "noindex"):
                    self.assertNotIn(mark, h)

    def test_pages(self):
        for code, h in self.pages(self.final).items():
            d = json.loads((ROOT / "data/houses" / f"{code}.json").read_text(encoding="utf-8"))
            with self.subTest(code):
                self.assertIn(f'data-price="{d["price"]}"', h)
                self.assertIn(build.rub(d["price"]) + " ₽", h)
                for kn in d["cadastral"]:
                    self.assertIn(f'data-copy="{kn["number"]}"', h)
                self.assertNotIn("Первый платёж", h)
                self.assertNotIn("переплат", h.lower())
                # все свои файлы на месте: стили, скрипты, фото
                for ref in re.findall(r'(?:src|href)="(\.\./[^"#?]+|img/[^"#?]+)"', h):
                    self.assertTrue((self.final / code / ref).resolve().exists(), ref)

    def test_calculator_files(self):
        rates = (self.final / "shared/calc/rates.mjs").read_text(encoding="utf-8")
        self.assertIn("export const PROGRAM", rates)
        self.assertTrue((self.final / "shared/calc/mortgage.mjs").exists())

    @unittest.skipUnless(subprocess.run(["node", "--version"], capture_output=True).returncode == 0
                         if __import__("shutil").which("node") else False, "нет node")
    def test_calculator_runs(self):
        # тот же движок, что у Продажника, считает по data/mortgage.json
        js = ("const m = await import(process.argv[1]); const r = m.calculate({price: 10000000, children: 2});"
              "if (!r.valid || !(r.payment > 0)) process.exit(1); console.log(r.payment);")
        url = (self.final / "shared/calc/mortgage.mjs").as_uri()
        r = subprocess.run(["node", "--input-type=module", "-e", js, url], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
