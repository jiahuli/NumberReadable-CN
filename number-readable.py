# -*- coding: utf-8 -*-
"""
数字转换器 - 数字与中文数字双向转换

- 输入 26 / 1.534 并选单位（K/M/B/T）→ 中文数字 + 千分位数字
- 输入 二千六百万 这类中文数字 → 数字 + K/M/B/T 英文简写

Windows 原生 UI，低占用，可调大小
"""

import math
import re
import tkinter as tk
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from tkinter import ttk

# ── 中文数字转换 ────────────────────────────────────────────

DIGITS = "零一二三四五六七八九"
UNITS_SMALL = ["", "十", "百", "千"]
UNITS_BIG = ["", "万", "亿", "兆"]


def _convert_4digits(n: int) -> str:
    """转换最多四位数字为中文（保留一十）"""
    if n == 0:
        return "零"

    parts = []
    for i in range(4):
        digit = n % 10
        n //= 10
        if digit != 0:
            parts.append(DIGITS[digit] + UNITS_SMALL[i])
        else:
            if parts and parts[-1] != "零":
                parts.append("零")

    while parts and parts[-1] == "零":
        parts.pop()

    return "".join(reversed(parts))


def _convert_group(n: int, *, is_most_significant: bool = False) -> str:
    """转换四位数字为一组。

    is_most_significant=True 时 "一十" 简化为 "十"（如 十万、十亿）；
    内部组保留 "一十"（如 十万零一十、一亿零一十万）。
    """
    s = _convert_4digits(n)
    if is_most_significant and s.startswith("一十"):
        s = s[1:]
    return s


def to_chinese_upper(num: int) -> str:
    """将整数转为中文大写"""
    if num == 0:
        return "零"

    if num < 0:
        return "负" + to_chinese_upper(-num)

    groups = []
    n = num
    while n > 0:
        groups.append(n % 10000)
        n //= 10000

    result_parts = []
    for i in range(len(groups) - 1, -1, -1):
        g = groups[i]
        if g == 0:
            if result_parts and result_parts[-1] != "零":
                result_parts.append("零")
        else:
            is_ms = (i == len(groups) - 1)
            text = _convert_group(g, is_most_significant=is_ms)

            if result_parts and g < 1000:
                result_parts.append("零")

            result_parts.append(text)

        if g != 0 and i > 0:
            result_parts.append(UNITS_BIG[i])

    result = "".join(result_parts)
    result = re.sub(r"零+", "零", result)
    result = result.rstrip("零")

    if not result:
        result = "零"

    return result


# ── 中文数字解析（to_chinese_upper 的逆运算）──────────────────

_CN_DIGITS = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}
_CN_SMALL_UNITS = {"十": 10, "百": 100, "千": 1000}
_CN_BIG_UNITS = (("兆", 10 ** 12), ("亿", 10 ** 8), ("万", 10 ** 4))

# 输入里出现这些字符，就按中文数字解析
CN_NUMERALS = "".join(_CN_DIGITS) + "".join(_CN_SMALL_UNITS) + "".join(
    unit for unit, _ in _CN_BIG_UNITS
) + "负"


def _parse_cn_section(text: str) -> int:
    """解析不含 万/亿/兆 的一段，如 "二千三百" → 2300"""
    total = 0
    number = 0
    for ch in text:
        if ch in _CN_DIGITS:
            number = _CN_DIGITS[ch]
        elif ch in _CN_SMALL_UNITS:
            if number == 0:
                number = 1          # "十五" 的 十 前面没有数字
            total += number * _CN_SMALL_UNITS[ch]
            number = 0
        elif ch.isdigit():
            number = int(ch)        # 容忍 "1亿" 这种混写
        else:
            raise ValueError(f"无法识别的字符：{ch!r}")
    return total + number


def chinese_to_number(text: str) -> int:
    """把中文小写数字解析成整数，与 to_chinese_upper 互逆。

    支持 零一二三四五六七八九两、十百千万亿兆，可带「负」前缀。
    按严格读法解析（"两千三" 会得 2003，口语的 2300 不在支持范围内）。

    >>> chinese_to_number("二千六百万")
    26000000
    >>> chinese_to_number("一亿六千九百七十五万")
    169750000
    >>> chinese_to_number("十五")
    15
    >>> chinese_to_number("一万亿")
    1000000000000
    >>> chinese_to_number("负一千")
    -1000
    """
    raw = text.strip()
    if not raw:
        raise ValueError("请输入中文数字")

    if raw.startswith("负"):
        return -chinese_to_number(raw[1:])

    # 大单位从大到小切分："一万亿" 先切 亿，"一亿二千万" 先切 亿再切 万
    for unit, multiplier in _CN_BIG_UNITS:
        if unit in raw:
            head, _, tail = raw.partition(unit)
            head_value = chinese_to_number(head) if head else 1
            tail_value = chinese_to_number(tail) if tail else 0
            return head_value * multiplier + tail_value

    return _parse_cn_section(raw)


def format_number(num: int) -> str:
    """给整数加千分位逗号"""
    return f"{num:,}"


def simplify_number(n: int) -> int:
    """去掉零散尾数，保留 3 位有效数字。

    >>> simplify_number(1534000)
    1530000
    >>> simplify_number(15340)
    15300
    """
    if n == 0:
        return 0
    s = str(n)
    if len(s) <= 3:
        return n
    keep = s[:3]
    zeros = "0" * (len(s) - 3)
    return int(keep + zeros)


# ── 数字缩写转换 ────────────────────────────────────────────

UNITS = [
    ("K", "千",      1_000),
    ("M", "百万",    1_000_000),
    ("B", "十亿",    1_000_000_000),
    ("T", "兆",      1_000_000_000_000),
]

# 缩写时的取整方式
ROUNDING_TRUNC = "trunc"        # 截断：只少不多
ROUNDING_HALF_UP = "round"      # 四舍五入：尽量贴近真实值

_ROUNDING_MODES = {
    ROUNDING_TRUNC: ROUND_DOWN,
    ROUNDING_HALF_UP: ROUND_HALF_UP,
}


def to_compact_number(num: float, rounding: str = ROUNDING_TRUNC) -> str:
    """把数值压成带英文单位缩写的紧凑形式。

    单位取 K / M / B / T 中不超过该数值的最大一档，保留一位小数。
    ``rounding`` 决定多出来的那位小数怎么处理：

    - ``"trunc"``（默认，截断）：直接舍去，结果永远不大于真实值。
      适合对外披露、成本与容量承诺、额度上限等"宁可说少不可说多"的场合。
    - ``"round"``（四舍五入）：取最接近真实值的写法，进位到 1000.0
      时会自动升一档，适合行情、报表概览、界面展示等只求量级一眼准确的地方。

    末尾的 ".0" 省略；低于 1000 时原样返回；超过 T 时继续沿用 T。

    >>> to_compact_number(1697507113)
    '1.6B'
    >>> to_compact_number(1697507113, rounding="round")
    '1.7B'
    >>> to_compact_number(999960000, rounding="round")
    '1B'
    >>> to_compact_number(1534000)
    '1.5M'
    >>> to_compact_number(1000)
    '1K'
    >>> to_compact_number(-1697507113)
    '-1.6B'
    """
    if rounding not in _ROUNDING_MODES:
        raise ValueError(f"未知的取舍方式：{rounding!r}，只支持 'trunc' 或 'round'")

    if not math.isfinite(num):
        return str(num)

    if num < 0:
        return "-" + to_compact_number(-num, rounding=rounding)

    mode = _ROUNDING_MODES[rounding]

    index = -1
    for i, (_, _, multiplier) in enumerate(UNITS):
        if num >= multiplier:
            index = i

    if index < 0:
        return str(int(num)) if num == int(num) else f"{num:g}"

    for i in range(index, len(UNITS)):
        symbol, _, scale = UNITS[i]
        # 用 Decimal 做取舍，避开 2900000/1e6 = 2.8999… 这类二进制浮点误差
        tenths = (Decimal(str(num)) / Decimal(scale)).quantize(
            Decimal("0.1"), rounding=mode,
        )
        # 四舍五入可能顶到 1000.0，需要升一档：999,999,999 → 1B
        if tenths < 1000 or i == len(UNITS) - 1:
            break

    return f"{tenths:.1f}".rstrip("0").rstrip(".") + symbol


# ── 主窗口 ──────────────────────────────────────────────────


class NumberConverter:
    """数字转换器主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("数字转换器")
        self.root.geometry("380x240")
        self.root.minsize(280, 230)
        self.root.resizable(True, True)

        # 居中显示
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")

        self._unit_buttons: list[ttk.Button] = []
        self._unit_multipliers: dict[str, int] = {}
        self._build_ui()

    def _build_ui(self):
        font_label  = ("Microsoft YaHei UI", 10)
        font_result = ("Microsoft YaHei UI", 11, "bold")
        font_big    = ("Microsoft YaHei UI", 14, "bold")

        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        # ── 顶栏：精简开关（替代标题，节省空间）──
        top = ttk.Frame(main)
        top.pack(fill=tk.X, pady=(0, 8))

        self.simplify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            top,
            text="精简（去掉零散尾数）",
            variable=self.simplify_var,
            command=self._convert,
        ).pack(side=tk.LEFT)

        # 缩写取整方式：不勾=截断，勾上=四舍五入
        self.round_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            top,
            text="缩写四舍五入",
            variable=self.round_var,
            command=self._convert,
        ).pack(side=tk.RIGHT)

        # ── 输入区 ──
        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(
            main,
            textvariable=self.entry_var,
            font=font_label,
            justify="center",
        )
        self.entry.pack(fill=tk.X)

        # ── 单位按钮组 ──
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(8, 6))

        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)
        btn_frame.columnconfigure(3, weight=1)

        self.unit_var = tk.StringVar(value="M")

        for idx, (sym, label, mult) in enumerate(UNITS):
            self._unit_multipliers[sym] = mult
            btn = ttk.Button(
                btn_frame,
                text=f"{sym}\n{label}",
                command=lambda s=sym: self._select_unit(s),
            )
            btn.grid(row=0, column=idx, sticky="ew", padx=1)
            self._unit_buttons.append(btn)

        # ── 结果区（大写在上，数字在下）──
        result_frame = ttk.Frame(main)
        result_frame.pack(fill=tk.BOTH, expand=True)

        # 中文大写（字号更大，放上面避免缩小时被裁切）
        row_cap = ttk.Frame(result_frame)
        row_cap.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(row_cap, text="大写：", font=font_label, width=5).pack(side=tk.LEFT)
        self.cap_label = ttk.Label(
            row_cap, text="—", font=font_big, foreground="#C43E1C",
        )
        self.cap_label.pack(side=tk.LEFT)

        # 数字形式
        row_num = ttk.Frame(result_frame)
        row_num.pack(fill=tk.X)
        ttk.Label(row_num, text="数字：", font=font_label, width=5).pack(side=tk.LEFT)
        self.num_label = ttk.Label(
            row_num, text="—", font=font_result, foreground="#0078D4",
        )
        self.num_label.pack(side=tk.LEFT)

        # 缩写形式
        row_compact = ttk.Frame(result_frame)
        row_compact.pack(fill=tk.X)
        ttk.Label(row_compact, text="缩写：", font=font_label, width=5).pack(side=tk.LEFT)
        self.compact_label = ttk.Label(
            row_compact, text="—", font=font_result, foreground="#107C10",
        )
        self.compact_label.pack(side=tk.LEFT)

        # ── 初始选中样式 ──
        self._update_button_style("M")

        # ── 自动转换 ──
        self.entry_var.trace_add("write", lambda *_: self._convert())
        self.unit_var.trace_add("write", lambda *_: self._convert())

        self.entry.focus_set()

    def _select_unit(self, sym: str):
        self.unit_var.set(sym)
        self._update_button_style(sym)

    def _update_button_style(self, active: str):
        for btn in self._unit_buttons:
            btn_sym = btn.cget("text").split("\n")[0]
            if btn_sym == active:
                btn.state(["pressed"])
            else:
                btn.state(["!pressed"])

    def _convert(self):
        raw = self.entry_var.get().strip()
        unit = self.unit_var.get()
        rounding = ROUNDING_HALF_UP if self.round_var.get() else ROUNDING_TRUNC

        if not raw:
            self.num_label.config(text="—", foreground="#0078D4")
            self.cap_label.config(text="—", foreground="#C43E1C")
            self.compact_label.config(text="—", foreground="#107C10")
            return

        # 反向输入：中文数字直接解析，不再乘单位
        if any(ch in CN_NUMERALS for ch in raw):
            try:
                number = chinese_to_number(raw)
            except ValueError:
                self.num_label.config(text="无法识别的中文数字", foreground="red")
                self.cap_label.config(text="—", foreground="#C43E1C")
                self.compact_label.config(text="—", foreground="#107C10")
                return

            if number < 0:
                self.num_label.config(text="请输入正数", foreground="red")
                self.cap_label.config(text="—", foreground="#C43E1C")
                self.compact_label.config(text="—", foreground="#107C10")
                return

            self._show_int(number, rounding)
            return

        try:
            value = float(raw)
        except ValueError:
            self.num_label.config(text="无效数字", foreground="red")
            self.cap_label.config(text="—", foreground="#C43E1C")
            self.compact_label.config(text="—", foreground="#107C10")
            return

        if value < 0:
            self.num_label.config(text="请输入正数", foreground="red")
            self.cap_label.config(text="—", foreground="#C43E1C")
            self.compact_label.config(text="—", foreground="#107C10")
            return

        multiplier = self._unit_multipliers[unit]
        result = value * multiplier

        if result == int(result):
            int_result = int(result)
        else:
            int_result = int(round(result))
            if abs(int_result - result) > 0.001:
                self.num_label.config(
                    text=f"{result:,.6f}".rstrip("0").rstrip("."),
                    foreground="#0078D4",
                )
                self.cap_label.config(text="（仅支持整数大写）", foreground="gray")
                self.compact_label.config(
                    text=to_compact_number(result, rounding=rounding),
                    foreground="#107C10",
                )
                return

        self._show_int(int_result, rounding)

    def _show_int(self, number: int, rounding: str):
        """统一渲染整数结果：数字 / 中文 / 缩写"""
        if self.simplify_var.get():
            number = simplify_number(number)        # 精简模式：去掉零散尾数

        self.num_label.config(text=format_number(number), foreground="#0078D4")
        self.cap_label.config(text=to_chinese_upper(number), foreground="#C43E1C")
        self.compact_label.config(
            text=to_compact_number(number, rounding=rounding), foreground="#107C10",
        )

    def run(self):
        self.root.mainloop()


# ── 入口 ────────────────────────────────────────────────────

if __name__ == "__main__":
    app = NumberConverter()
    app.run()
