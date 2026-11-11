# -*- coding: utf-8 -*-
"""number-readable.py 的单元测试。

运行：
    python -m unittest -v test_number_readable
或用 doctest 单独跑一遍文档示例：
    python -m unittest -v test_number_readable.TestDocstrings
"""

import doctest
import importlib.util
import unittest
from decimal import Decimal
from pathlib import Path

# 业务文件名带连字符，无法直接 import，只能按路径加载
MODULE_PATH = Path(__file__).with_name("number-readable.py")
_spec = importlib.util.spec_from_file_location("number_readable", MODULE_PATH)
nr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nr)


class TestCompactNumber(unittest.TestCase):
    """功能一：数字 → 英文简写（保留两位小数）"""

    def test_core_case(self):
        # 用户给的原例：26054144 → 26.05M
        self.assertEqual(nr.to_compact_number(26054144), "26.05M")

    def test_two_decimals(self):
        self.assertEqual(nr.to_compact_number(1697507113), "1.69B")
        self.assertEqual(nr.to_compact_number(1534000), "1.53M")
        self.assertEqual(nr.to_compact_number(15340), "15.34K")

    def test_trailing_zeros_stripped(self):
        self.assertEqual(nr.to_compact_number(1000), "1K")
        self.assertEqual(nr.to_compact_number(26000000), "26M")
        self.assertEqual(nr.to_compact_number(1500000), "1.5M")

    def test_unit_boundaries(self):
        self.assertEqual(nr.to_compact_number(999), "999")
        self.assertEqual(nr.to_compact_number(1000), "1K")
        self.assertEqual(nr.to_compact_number(999999), "999.99K")
        self.assertEqual(nr.to_compact_number(1000000), "1M")
        self.assertEqual(nr.to_compact_number(999999999), "999.99M")
        self.assertEqual(nr.to_compact_number(1000000000), "1B")

    def test_negative_and_zero(self):
        self.assertEqual(nr.to_compact_number(0), "0")
        self.assertEqual(nr.to_compact_number(-26054144), "-26.05M")

    def test_float_precision(self):
        # 2900000/1e6 在二进制浮点下是 2.8999…，必须仍得 2.9M
        self.assertEqual(nr.to_compact_number(2900000), "2.9M")
        self.assertEqual(nr.to_compact_number(1200000), "1.2M")

    def test_beyond_tera(self):
        self.assertEqual(nr.to_compact_number(10 ** 15), "1000T")

    def test_non_finite(self):
        self.assertEqual(nr.to_compact_number(float("inf")), "inf")
        self.assertEqual(nr.to_compact_number(float("nan")), "nan")


class TestRoundingModes(unittest.TestCase):
    """trunc（截断，默认）与 round（四舍五入）"""

    def test_default_is_truncation(self):
        self.assertEqual(nr.to_compact_number(1697507113), "1.69B")
        self.assertEqual(
            nr.to_compact_number(1697507113),
            nr.to_compact_number(1697507113, rounding=nr.ROUNDING_TRUNC),
        )

    def test_modes_differ(self):
        self.assertEqual(nr.to_compact_number(1697507113, rounding="trunc"), "1.69B")
        self.assertEqual(nr.to_compact_number(1697507113, rounding="round"), "1.7B")

    def test_half_up_rounds_up(self):
        # 1.055 → 1.06（截断得 1.05）
        self.assertEqual(nr.to_compact_number(1055000, rounding="round"), "1.06M")
        self.assertEqual(nr.to_compact_number(1055000, rounding="trunc"), "1.05M")
        self.assertEqual(nr.to_compact_number(1054000, rounding="round"), "1.05M")

    def test_rounding_carries_to_next_unit(self):
        # 顶到 1000.00 必须升档，不能输出 1000M
        self.assertEqual(nr.to_compact_number(999995000, rounding="round"), "1B")
        self.assertEqual(nr.to_compact_number(999999999, rounding="round"), "1B")
        # 截断则停在 999.99
        self.assertEqual(nr.to_compact_number(999999999, rounding="trunc"), "999.99M")

    def test_invalid_mode_raises(self):
        with self.assertRaises(ValueError):
            nr.to_compact_number(1234, rounding="ceil")


class TestParseCompact(unittest.TestCase):
    """26.05M → 数值，供功能二使用"""

    def test_core_case(self):
        self.assertEqual(nr.parse_compact("26.05M"), Decimal("26050000"))
        self.assertEqual(int(nr.parse_compact("26.05M")), 26050000)

    def test_all_units(self):
        self.assertEqual(int(nr.parse_compact("1.5K")), 1500)
        self.assertEqual(int(nr.parse_compact("26.05M")), 26050000)
        self.assertEqual(int(nr.parse_compact("3B")), 3000000000)
        self.assertEqual(int(nr.parse_compact("2T")), 2000000000000)

    def test_case_and_space_tolerant(self):
        self.assertEqual(int(nr.parse_compact("3b")), 3000000000)
        self.assertEqual(int(nr.parse_compact(" 26.05 m ")), 26050000)

    def test_no_float_error(self):
        # 26.05 * 1e6 用浮点会得 26050000.000000004，Decimal 不会
        self.assertEqual(nr.parse_compact("26.05M"), Decimal("26050000"))

    def test_invalid(self):
        for bad in ("26.05", "M", "abc", "", "26.05X"):
            with self.assertRaises(ValueError, msg=bad):
                nr.parse_compact(bad)

    def test_round_trip(self):
        for text in ("26.05M", "1.5K", "2T", "999.99K"):
            self.assertEqual(
                nr.to_compact_number(nr.parse_compact(text)), text, f"回环失败：{text}"
            )


class TestChineseNumber(unittest.TestCase):
    """功能二：英文简写 → 中文（两千六一五万那种写法）"""

    def test_core_case(self):
        self.assertEqual(nr.to_chinese_upper(26050000), "两千六百零五万")

    def test_uses_liang(self):
        self.assertEqual(nr.to_chinese_upper(200), "两百")
        self.assertEqual(nr.to_chinese_upper(2000), "两千")
        self.assertEqual(nr.to_chinese_upper(20000), "两万")
        self.assertEqual(nr.to_chinese_upper(200000000), "两亿")
        # 十位和个位的 2 仍写「二」
        self.assertEqual(nr.to_chinese_upper(20), "二十")
        self.assertEqual(nr.to_chinese_upper(2), "二")

    def test_can_disable_liang(self):
        self.assertEqual(nr.to_chinese_upper(2000, use_liang=False), "二千")
        self.assertEqual(nr.to_chinese_upper(20000, use_liang=False), "二万")

    def test_classic_cases(self):
        self.assertEqual(nr.to_chinese_upper(0), "零")
        self.assertEqual(nr.to_chinese_upper(1530000), "一百五十三万")
        self.assertEqual(nr.to_chinese_upper(100010), "十万零一十")
        self.assertEqual(nr.to_chinese_upper(-1000), "负一千")


class TestChineseToNumber(unittest.TestCase):
    """中文数字 → 整数"""

    def test_core_case(self):
        self.assertEqual(nr.chinese_to_number("两千六百零五万"), 26050000)

    def test_typical_values(self):
        self.assertEqual(nr.chinese_to_number("十五"), 15)
        self.assertEqual(nr.chinese_to_number("一百零五"), 105)
        self.assertEqual(nr.chinese_to_number("两千三百"), 2300)
        self.assertEqual(nr.chinese_to_number("一亿六千九百七十五万"), 169750000)
        self.assertEqual(nr.chinese_to_number("零"), 0)

    def test_big_units_nesting(self):
        self.assertEqual(nr.chinese_to_number("一万亿"), 10 ** 12)
        self.assertEqual(nr.chinese_to_number("一兆二千亿"), 12 * 10 ** 11)
        self.assertEqual(nr.chinese_to_number("十二亿三千万"), 1230000000)

    def test_prefix_and_aliases(self):
        self.assertEqual(nr.chinese_to_number("负一千"), -1000)
        self.assertEqual(nr.chinese_to_number("两千"), 2000)
        self.assertEqual(nr.chinese_to_number(" 三亿 "), 300000000)

    def test_invalid_input(self):
        for bad in ("", "abc", "二百X"):
            with self.assertRaises(ValueError, msg=bad):
                nr.chinese_to_number(bad)

    def test_round_trip(self):
        for value in (0, 7, 15, 105, 2300, 20000, 26050000, 169750000, 1230000000):
            text = nr.to_chinese_upper(value)
            self.assertEqual(nr.chinese_to_number(text), value, f"回环失败：{value} → {text}")


class TestExistingHelpers(unittest.TestCase):
    def test_format_number(self):
        self.assertEqual(nr.format_number(26054144), "26,054,144")
        self.assertEqual(nr.format_number(0), "0")

    def test_simplify_number(self):
        self.assertEqual(nr.simplify_number(1534000), 1530000)
        self.assertEqual(nr.simplify_number(15340), 15300)
        self.assertEqual(nr.simplify_number(0), 0)


class TestUi(unittest.TestCase):
    """界面三条路径：纯数字 / 英文简写 / 中文数字"""

    def setUp(self):
        self.app = nr.NumberConverter()
        self.app.root.withdraw()

    def tearDown(self):
        self.app.root.destroy()

    def _convert(self, text):
        self.app.entry_var.set(text)
        self.app._convert()
        return (
            self.app.cap_label.cget("text"),
            self.app.num_label.cget("text"),
            self.app.compact_label.cget("text"),
        )

    def test_plain_number(self):
        # 功能一：26054144 → 26.05M
        cn, num, compact = self._convert("26054144")
        self.assertEqual(compact, "26.05M")
        self.assertEqual(num, "26,054,144")
        self.assertEqual(cn, "两千六百零五万四千一百四十四")

    def test_compact_input_gives_chinese(self):
        # 功能二：26.05M → 两千六百零五万
        cn, num, compact = self._convert("26.05M")
        self.assertEqual(cn, "两千六百零五万")
        self.assertEqual(num, "26,050,000")
        self.assertEqual(compact, "26.05M")

    def test_chinese_input(self):
        cn, num, compact = self._convert("两千六百零五万")
        self.assertEqual(num, "26,050,000")
        self.assertEqual(compact, "26.05M")

    def test_unit_button_appends_suffix(self):
        self.app.entry_var.set("26.05")
        self.app._select_unit("M")
        self.assertEqual(self.app.entry_var.get(), "26.05M")
        self.assertEqual(self.app.cap_label.cget("text"), "两千六百零五万")

    def test_unit_button_switches_suffix(self):
        self.app.entry_var.set("26.05M")
        self.app._select_unit("K")
        self.assertEqual(self.app.entry_var.get(), "26.05K")

    def test_simplify_off_by_default(self):
        self.assertFalse(self.app.simplify_var.get())

    def test_rounding_toggle(self):
        self.app.entry_var.set("1697507113")
        self.app._convert()
        self.assertEqual(self.app.compact_label.cget("text"), "1.69B")
        self.app.round_var.set(True)
        self.app._convert()
        self.assertEqual(self.app.compact_label.cget("text"), "1.7B")

    def test_errors(self):
        self.assertEqual(self._convert("abc")[1], "无效数字")
        self.assertEqual(self._convert("二百X")[1], "无法识别的中文数字")
        self.assertEqual(self._convert("-5")[1], "请输入正数")
        self.assertEqual(self._convert("")[1], "—")


class TestDocstrings(unittest.TestCase):
    def test_doctests(self):
        results = doctest.testmod(nr, verbose=False)
        self.assertEqual(results.failed, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
