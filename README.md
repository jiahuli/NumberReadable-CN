# NumberReadable CN

> ⚠️ 此项目代码由 DeepSeek 生成，人工仅做审核与微调。

数字与中文数字**双向**互转的小工具，纯 Windows 原生窗口，体积极小，输入即出结果。

| 输入 | 输出 | 说明 |
| --- | --- | --- |
| `26054144` | `26.05M` | **功能一**：阿拉伯数字 → 英文简写，保留两位小数 |
| `26.05M` | `两千六百零五万` | **功能二**：英文简写 → 中文数字 |
| `两千六百零五万` | `26,050,000` / `26.05M` | 附赠：中文数字 → 数字 + 简写 |

## 界面

```text
 ☐ 精简（去掉零散尾数）      ☐ 缩写四舍五入
 ┌──────────────────────┐
 │       26054144       │
 └──────────────────────┘
  [ K ]  [ M ]  [ B ]  [ T ]
    千     百万   十亿    兆
 ──────────────────────────
 中文：两千六百零五万四千一百四十四
 数字：26,054,144
 缩写：26.05M
```

输入框认三种写法，优先级从高到低：

1. **中文数字** — `两千六百零五万`。按中文本身算，单位按钮不参与。
2. **英文简写** — `26.05M`、`1.5K`、`3b`。大小写和空格都容忍，单位按钮不参与。
3. **纯数字** — `26054144`。按数值本身算，**不乘单位**，单位按钮不参与。

单位按钮现在是「补后缀」快捷键：输入框里是 `26.05`，点 `M` 就变成 `26.05M`；已有后缀则直接替换，点 `K` 变 `26.05K`。

## 功能

- **双向转换** — 数字 → 英文简写 → 中文数字，任意方向都能查
- **两位小数** — 简写保留两位（`26054144` → `26.05M`），末尾多余的零自动去掉（`1000` → `1K`）
- **口语中文** — 2 在百/千/万/亿位写「两」（两千、两百、两万），十位和个位仍写「二」（二十）
- **即时转换** — 键入即出结果，无需点击按钮
- **两种取舍** — 简写可切「截断」与「四舍五入」，见下节
- **零依赖** — 仅用 Python 标准库 tkinter，无需安装任何第三方包

## 下载

> [Releases](https://github.com/jiahuli/NumberReadable-CN/releases) 下载 `number-readable.exe`（[v1.2 直链](https://github.com/jiahuli/NumberReadable-CN/releases/download/v1.2/number-readable.exe)），约 11 MB 单文件，双击即用，无控制台弹窗，目标机无需安装 Python。

## 功能一：数字 → 英文简写

```python
import importlib.util

spec = importlib.util.spec_from_file_location("number_readable", "number-readable.py")
nr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nr)

nr.to_compact_number(26054144)                      # '26.05M'
nr.to_compact_number(1697507113)                    # '1.69B'
nr.to_compact_number(15340)                         # '15.34K'
nr.to_compact_number(1000)                          # '1K'
nr.to_compact_number(-26054144)                     # '-26.05M'
nr.to_compact_number(1697507113, rounding="round")  # '1.7B'
```

## 功能二：英文简写 → 中文

```python
nr.parse_compact("26.05M")                    # Decimal('26050000.00')
nr.to_chinese_upper(26050000)                 # '两千六百零五万'

# 一步到位
def compact_to_cn(text):
    return nr.to_chinese_upper(int(nr.parse_compact(text)))

compact_to_cn("26.05M")   # '两千六百零五万'
compact_to_cn("1.5K")     # '一千五百'
compact_to_cn("2T")       # '两兆'
```

`parse_compact()` 用 `Decimal` 解析，不走浮点：`"26.05M"` 得精确的 `26050000`，不会变成 `26050000.000000004`。

`to_chinese_upper(num, use_liang=True)` 默认按口语写「两」，传 `use_liang=False` 回到「二千」。

## 取整方式

| `rounding` | 规则 | `1697507113` | 什么时候用 |
| --- | --- | --- | --- |
| `"trunc"`（默认） | 第三位小数起直接舍去，结果**只会小于等于**真实值 | `1.69B` | 对外披露、成本与容量承诺、额度上限、风控阈值——宁可说少，不能说多 |
| `"round"` | 第三位小数四舍五入，顶到 `1000.00` 时自动升一档 | `1.7B` | 行情推送、报表概览、界面展示、口头估算 |

`round` 的升档要留意：`999995000` 四舍五入是 `1000.00M`，输出 `1B` 而不是 `1000M`；`trunc` 则停在 `999.99M`。

- **界面**：勾选顶栏「缩写四舍五入」即切到四舍五入，取消勾选回到截断，切换立刻重算。
- **代码**：传 `rounding="round"` / `"trunc"`，也可用常量 `ROUNDING_TRUNC` / `ROUNDING_HALF_UP`；传其它值抛 `ValueError`。

## 其余规则

- 单位取 K / M / B / T 中**不超过该数值的最大一档**
- 低于 1000 原样返回；超过 T 继续沿用 T（`1e15` → `1000T`）
- 中文按严格读法解析：`两千三` 得 `2003`，不是口语的 `2300`
- 带小数的值没有对应中文写法，界面会在中文一栏提示「仅支持整数中文」，数字和简写照常给
- `inf` / `nan` 原样返回字符串，不抛异常

> 文件名带连字符无法直接 `import`，上面的 `importlib` 写法是仓库里唯一的加载方式；正式引用时把它复制成合法模块名更省事。

## 测试

```bash
python -m unittest -v test_number_readable
```

共 40 个用例。覆盖功能一与功能二的原例、两位小数精度、单位边界（999 / 1000 / 999999…）、`Decimal` 解析无浮点误差、简写与数字的双向回环、「两」的用法（百千万亿用两、十个位用二）、中文解析的万亿兆嵌套与非法字符、两种取舍方式与 `round` 升档，以及界面三条输入路径。最后顺带跑一遍各函数 docstring 里的 doctest。

## 从源码运行

```bash
# 控制台版本（有黑框）
python number-readable.py

# 无控制台版本（推荐日常使用）
pythonw number-readable.pyw
```

要求 Python 3.8+（Windows 自带 tkinter 即可，无需额外安装）。

## 打包为 exe

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "number-readable" number-readable.py
# 输出在 dist/number-readable.exe
```

生成的是单文件、无控制台窗口的绿色版，目标机器无需安装 Python。图标可加 `--icon app.ico`。

## 更新记录

### 1.2

- **简写精度改为两位小数**：`26054144` → `26.05M`（原来是一位）
- **中文改用口语写法「两」**：`两千六百零五万`（原来写「二千」），`use_liang=False` 可关
- **可直接输入英文简写**：`26.05M` 直接出 `两千六百零五万`，新增 `parse_compact()`
- **单位按钮改为补后缀**：不再是隐藏倍数，点 `M` 把 `26.05` 变成 `26.05M`
- **精简默认关闭**：开启会把 `26054144` 抹成 `26000000`，简写就不准了
- 界面标签「大写」改为「中文」，与实际输出一致
- 测试增至 40 个用例

### 1.1

- 新增 `chinese_to_number()`：中文数字 → 整数，支持 万亿兆 嵌套与「负」前缀
- 新增 `to_compact_number()`：数值 → K/M/B/T 简写
- 缩写支持 `trunc` / `round` 两种取舍，界面可切换
- 修掉 `round` 进位到 1000 的越档问题

### 1.0

- 初始版本：K/M/B/T 单位数字 → 中文数字 + 千分位数字

## 许可

MIT License
