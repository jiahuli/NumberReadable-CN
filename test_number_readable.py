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
from pathlib import Path

# 业务文件名带连字符，无法直接 import，只能按路径加载
MODULE_PATH = Path(__file__).with_name("number-readable.py")
_spec = importlib.util.spec_from_file_location("number_readable", MODULE_PATH)
nr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nr)


class TestToCompactNumber(unittest.TestCase):
    """to_compact_number：数值 → K / M / B / T 缩写"""

    def test_typical_values(self):
        self.assertEqual(nr.to_compact_number(1697507113), "1.6B")
        self.assertEqual(nr.to_compact_number(1534000), "1.5M")
        self.assertEqual(nr.to_compact_number(2400000000000), "2.4T")

    def test_truncates_instead_of_rounding(self):
        # 1.6975 B 保留一位小数是截断得 1.6B，不是四舍五入的 1.7B
        self.assertEqual(nr.to_compact_number(1697507113), "1.6B")
        self.assertEqual(nr.to_compact_number(1999999), "1.9M")
        self.assertEqual(nr.to_compact_number(999959999), "999.9M")

    def test_unit_boundaries(self):
        self.assertEqual(nr.to_compact_number(999), "999")
        self.assertEqual(nr.to_compact_number(1000), "1K")
        self.assertEqual(nr.to_compact_number(999999), "999.9K")
        self.assertEqual(nr.to_compact_number(1000000), "1M")
        self.assertEqual(nr.to_compact_number(999999999), "999.9M")
        self.assertEqual(nr.to_compact_number(1000000000), "1B")

    def test_zero_and_small_values(self):
        self.assertEqual(nr.to_compact_number(0), "0")
        self.assertEqual(nr.to_compact_number(7), "7")
        self.assertEqual(nr.to_compact_number(999.9), "999.9")

    def test_integer_has_no_trailing_zero(self):
        self.assertEqual(nr.to_compact_number(1000), "1K")
        self.assertEqual(nr.to_compact_number(2000000), "2M")

    def test_negative_values(self):
        self.assertEqual(nr.to_compact_number(-1697507113), "-1.6B")
        self.assertEqual(nr.to_compact_number(-1000), "-1K")

    def test_float_input(self):
        self.assertEqual(nr.to_compact_number(12.5), "12.5")
        self.assertEqual(nr.to_compact_number(1500.0), "1.5K")

    def test_float_precision(self):
        # 2900000/1e6 在二进制浮点下是 2.8999…，若用浮点截断会错得 2.8M
        self.assertEqual(nr.to_compact_number(2900000), "2.9M")
        self.assertEqual(nr.to_compact_number(1200000), "1.2M")

    def test_beyond_tera(self):
        # 超出 T 档继续沿用 T，与 JS Intl compact 行为一致
        self.assertEqual(nr.to_compact_number(1000000000000000), "1000T")

    def test_non_finite(self):
        self.assertEqual(nr.to_compact_number(float("inf")), "inf")
        self.assertEqual(nr.to_compact_number(float("nan")), "nan")


class TestRoundingModes(unittest.TestCase):
    """rounding="trunc"(截断) 与 "round"(四舍五入) 的差异"""

    def test_default_is_truncation(self):
        # 不传第二个参数时行为与旧版一致，不能悄悄变
        self.assertEqual(nr.to_compact_number(1697507113), "1.6B")
        self.assertEqual(
            nr.to_compact_number(1697507113),
            nr.to_compact_number(1697507113, rounding=nr.ROUNDING_TRUNC),
        )

    def test_both_modes_differ_where_expected(self):
        self.assertEqual(nr.to_compact_number(1697507113, rounding="trunc"), "1.6B")
        self.assertEqual(nr.to_compact_number(1697507113, rounding="round"), "1.7B")

    def test_half_up_rounds_up(self):
        # 1.05 → 1.1（截断会得 1.0）；1.04 → 1.0
        self.assertEqual(nr.to_compact_number(1050000, rounding="round"), "1.1M")
        self.assertEqual(nr.to_compact_number(1050000, rounding="trunc"), "1M")
        self.assertEqual(nr.to_compact_number(1040000, rounding="round"), "1M")

    def test_rounding_carries_to_next_unit(self):
        # 四舍五入顶到 1000.0 必须升档，不能输出 1000M
        self.assertEqual(nr.to_compact_number(999960000, rounding="round"), "1B")
        self.assertEqual(nr.to_compact_number(999999999, rounding="round"), "1B")
        self.assertEqual(nr.to_compact_number(999999999999, rounding="round"), "1T")
        # 截断则老老实实停在 999.9
        self.assertEqual(nr.to_compact_number(999999999, rounding="trunc"), "999.9M")

    def test_truncation_never_exceeds_value(self):
        for value in (1697507113, 999960000, 1234567, 87654321):
            text = nr.to_compact_number(value, rounding="trunc")
            self.assertLessEqual(_parse_compact(text), value)

    def test_rounding_stays_within_one_step(self):
        # 四舍五入误差不应超过半个最小刻度
        for value in (1697507113, 999960000, 1234567, 87654321):
            text = nr.to_compact_number(value, rounding="round")
            self.assertLessEqual(abs(_parse_compact(text) - value), value * 0.05)

    def test_negative_keeps_rounding_mode(self):
        self.assertEqual(nr.to_compact_number(-1697507113, rounding="round"), "-1.7B")
        self.assertEqual(nr.to_compact_number(-1697507113, rounding="trunc"), "-1.6B")

    def test_invalid_mode_raises(self):
        with self.assertRaises(ValueError):
            nr.to_compact_number(1234, rounding="ceil")

    def test_ui_toggle_wiring(self):
        # 界面开关默认截断，切到四舍五入后结果跟着变
        app = nr.NumberConverter()
        try:
            app.root.withdraw()
            app.entry_var.set("1697.507113")
            app._select_unit("M")
            app._convert()
            self.assertEqual(app.compact_label.cget("text"), "1.6B")

            app.round_var.set(True)
            app._convert()
            self.assertEqual(app.compact_label.cget("text"), "1.7B")
        finally:
            app.root.destroy()


def _parse_compact(text: str) -> float:
    """把 '1.6B' 之类的缩写还原成数值，供断言使用"""
    suffix = text[-1]
    scale = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000, "T": 1_000_000_000_000}
    if suffix in scale:
        return float(text[:-1]) * scale[suffix]
    return float(text)


class TestExistingHelpers(unittest.TestCase):
    """顺带守住原有转换函数，避免新增功能带来回归"""

    def test_format_number(self):
        self.assertEqual(nr.format_number(1534000), "1,534,000")
        self.assertEqual(nr.format_number(0), "0")

    def test_simplify_number(self):
        self.assertEqual(nr.simplify_number(1534000), 1530000)
        self.assertEqual(nr.simplify_number(15340), 15300)
        self.assertEqual(nr.simplify_number(0), 0)

    def test_to_chinese_upper(self):
        self.assertEqual(nr.to_chinese_upper(0), "零")
        self.assertEqual(nr.to_chinese_upper(1530000), "一百五十三万")
        self.assertEqual(nr.to_chinese_upper(100010), "十万零一十")
        self.assertEqual(nr.to_chinese_upper(-1000), "负一千")


class TestDocstrings(unittest.TestCase):
    """docstring 里写的示例必须能跑通"""

    def test_doctests(self):
        results = doctest.testmod(nr, verbose=False)
        self.assertEqual(results.failed, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
