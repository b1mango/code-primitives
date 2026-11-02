import json
import re
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import readme_kit as kit

HERE = Path(__file__).parent
EXAMPLE = HERE / "example" / "readme-kit.json"
SVG_NS = "{http://www.w3.org/2000/svg}"


def load_example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


class FontTest(unittest.TestCase):
    def test_every_glyph_is_rectangular_and_seven_rows(self):
        for ch, glyph in kit.FONT.items():
            self.assertEqual(len(glyph), 7, ch)
            self.assertEqual(len({len(r) for r in glyph}), 1, f"ragged glyph {ch!r}")
            self.assertTrue(set("".join(glyph)) <= {"#", "."}, ch)

    def test_covers_ascii_uppercase_and_digits(self):
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            self.assertIn(ch, kit.FONT)

    def test_lowercase_maps_to_uppercase_and_unknown_to_question_mark(self):
        self.assertEqual(kit.pixel_path("abc", 0, 0, 1), kit.pixel_path("ABC", 0, 0, 1))
        self.assertEqual(kit.pixel_path("~", 0, 0, 1), kit.pixel_path("?", 0, 0, 1))

    def test_width_matches_glyph_sum_plus_tracking(self):
        # H(6) + I(4) + 1 tracking = 11 cells
        self.assertEqual(kit.pixel_width("HI", 2), 22)
        self.assertEqual(kit.pixel_width("", 2), 0)

    def test_path_cell_count_matches_bitmap(self):
        d = kit.pixel_path("E", 0, 0, 1)
        lit = sum(r.count("#") for r in kit.FONT["E"])
        widths = [float(w) for w in re.findall(r"h(\d+(?:\.\d+)?)v", d)]
        self.assertEqual(sum(widths), lit)

    def test_underscore_sits_on_baseline(self):
        self.assertEqual(kit.FONT["_"][-1], "######")
        self.assertEqual(kit.FONT["_"][0], "......")


class TextWidthTest(unittest.TestCase):
    def test_cjk_is_wider_than_latin(self):
        self.assertGreater(kit.text_width("中文", 14), kit.text_width("ab", 14))
        self.assertAlmostEqual(kit.text_width("中文", 10), 20)


class ThemeTest(unittest.TestCase):
    REQUIRED = {"shell", "hi", "lo", "shadow", "line", "ink", "ink_soft", "vent", "screen", "grain",
                "plate", "plate_ink", "key", "key_shadow", "key_hi", "accent", "accent_shadow", "accent_ink"}

    def test_every_theme_has_both_modes_with_same_keys(self):
        for name, theme in kit.THEMES.items():
            self.assertEqual(len(theme["leds"]), 3, name)
            for mode in kit.MODES:
                self.assertEqual(set(theme[mode]), self.REQUIRED, f"{name}/{mode}")

    def test_unknown_theme_raises(self):
        with self.assertRaises(ValueError):
            kit.palette("neon", "day")


class AssetTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_example()
        self.files = kit.render_assets(self.cfg, EXAMPLE.parent)

    def test_every_asset_has_day_and_night_twin(self):
        stems = {re.sub(r"-(day|night)\.svg$", "", f) for f in self.files}
        for stem in stems:
            self.assertIn(f"{stem}-day.svg", self.files)
            self.assertIn(f"{stem}-night.svg", self.files)
        expected = 1 + len(self.cfg["languages"]) + len(self.cfg["keys"]) + len(self.cfg["sections"])
        self.assertEqual(len(stems), expected)

    def test_all_assets_are_well_formed_svg_with_accessible_label(self):
        for name, svg in self.files.items():
            root = ET.fromstring(svg)
            self.assertEqual(root.tag, SVG_NS + "svg", name)
            self.assertEqual(root.get("role"), "img", name)
            self.assertTrue(root.get("aria-label"), name)
            self.assertIsNotNone(root.find(SVG_NS + "title"), name)

    def test_day_and_night_differ_only_in_colour(self):
        strip = lambda s: re.sub(r"#[0-9a-fA-F]{3,8}|rgba\([^)]*\)", "C", s)
        for name in self.files:
            if name.endswith("-day.svg"):
                twin = name.replace("-day.svg", "-night.svg")
                self.assertEqual(strip(self.files[name]), strip(self.files[twin]), name)

    def test_output_is_deterministic(self):
        again = kit.render_assets(self.cfg, EXAMPLE.parent)
        self.assertEqual(self.files, again)

    def test_text_is_xml_escaped(self):
        p = kit.palette("beige", "day")
        svg = kit.keycap_svg('A&B <"x">', "", p)
        root = ET.fromstring(svg)
        self.assertEqual(root.get("aria-label"), 'A&B <"x">')

    def test_section_layout_stays_inside_canvas(self):
        p = kit.palette("slate", "night")
        svg = kit.section_svg("CONTRIBUTORS", "贡献和致谢", 12, p)
        for m in re.finditer(r'<rect x="([\d.]+)"[^>]*width="([\d.]+)"', svg):
            self.assertLessEqual(float(m.group(1)) + float(m.group(2)), kit.WIDTH, m.group(0))

    def test_hero_title_scales_down_to_fit(self):
        for title in ("AB", "RETRO KIT", "PRIMITIVES LAB"):
            cell = kit.title_cell(title)
            self.assertLessEqual(cell, 10)
            self.assertLessEqual(kit.pixel_width(title, cell), kit.TITLE_MAX_W, title)
        self.assertGreater(kit.title_cell("AB"), kit.title_cell("PRIMITIVES LAB"))

    def test_hero_title_too_long_raises(self):
        cfg = dict(self.cfg, hero=dict(self.cfg["hero"], title="A VERY LONG PROJECT TITLE"))
        with self.assertRaises(ValueError):
            kit.hero_svg(cfg, kit.palette("beige", "day"), EXAMPLE.parent)

    def test_animation_can_be_disabled(self):
        cfg = dict(self.cfg, animate=False)
        files = kit.render_assets(cfg, EXAMPLE.parent)
        self.assertNotIn("<animate", files["hero-day.svg"])
        self.assertIn("<animate", self.files["hero-day.svg"])

    def test_sprite_rejects_ragged_rows(self):
        with self.assertRaises(ValueError):
            kit.sprite_svg({"palette": {"a": "#000"}, "rows": ["aa", "a"]}, 0, 0, 100, 100,
                           kit.palette("beige", "day"))

    def test_sprite_theme_tokens_resolve(self):
        p = kit.palette("mint", "day")
        out = kit.sprite_svg({"palette": {"a": "$accent", "b": "$led2"}, "rows": ["ab"]}, 0, 0, 10, 10, p)
        self.assertIn(p["accent"], out)
        self.assertIn(p["leds"][2], out)

    def test_hero_embeds_image(self):
        with tempfile.TemporaryDirectory() as d:
            img = Path(d) / "a.png"
            img.write_bytes(b"\x89PNG\r\n\x1a\nfake")
            cfg = dict(self.cfg, hero=dict(self.cfg["hero"], image="a.png"))
            svg = kit.hero_svg(cfg, kit.palette("beige", "day"), Path(d))
            self.assertIn("data:image/png;base64,", svg)
            self.assertNotIn("FLOPPY", svg)


class MarkdownTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_example()

    def test_picture_switches_on_color_scheme(self):
        html = kit.picture("assets/readme", "hero", "x", "100%")
        self.assertIn('media="(prefers-color-scheme: dark)"', html)
        self.assertIn('srcset="assets/readme/hero-night.svg"', html)
        self.assertIn('src="assets/readme/hero-day.svg"', html)

    def test_template_placeholders_are_filled(self):
        tpl = "{{kit:hero}}\n{{ kit:section:intro }}\n{{kit:keys}}\n{{kit:badges}}\n{{kit:lang}}"
        out = kit.render_template(tpl, self.cfg)
        self.assertNotIn("{{", out)
        self.assertIn("sec-intro-night.svg", out)
        self.assertIn("img.shields.io", out)

    def test_unknown_placeholder_fails_loudly(self):
        with self.assertRaises(KeyError):
            kit.render_template("{{kit:section:missing}}", self.cfg)

    def test_static_badge_escaping_and_palette_colours(self):
        cfg = {"badges": [{"label": "Python", "message": "3.12+ beta-1"}]}
        (url, _, _), = kit.badge_urls(cfg, "beige")
        self.assertIn("/badge/Python-3.12%2B%20beta--1-8fd6a0?", url)
        self.assertIn("labelColor=5a544a", url)

    def test_github_badge_requires_repo(self):
        with self.assertRaises(ValueError):
            kit.badge_urls({"badges": [{"github": "stars"}]}, "beige")


class BuildTest(unittest.TestCase):
    def test_build_writes_assets_readme_and_preview(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            cfg = load_example()
            cfg["hero"].pop("image", None)
            (d / "kit.json").write_text(json.dumps(cfg), encoding="utf-8")
            (d / "tpl.md").write_text("{{kit:hero}}", encoding="utf-8")
            kit.build(d / "kit.json", d / "tpl.md", d / "README.md", d / "preview.html", d / "gallery")
            self.assertTrue((d / "assets/readme/hero-night.svg").exists())
            self.assertEqual(len(list((d / "gallery").glob("hero-*.svg"))), 2 * len(kit.THEMES))
            self.assertIn("<picture>", (d / "README.md").read_text(encoding="utf-8"))
            self.assertIn("hero-day.svg", (d / "preview.html").read_text(encoding="utf-8"))

    def test_render_benchmark(self):
        cfg = load_example()
        n = 20
        t = time.perf_counter()
        for _ in range(n):
            kit.render_assets(cfg, EXAMPLE.parent)
        per = (time.perf_counter() - t) / n * 1000
        print(f"\nrender_assets: {per:.2f} ms per full asset set")
        self.assertLess(per, 500)


if __name__ == "__main__":
    unittest.main()
