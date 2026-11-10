# NumberReadable CN

> ⚠️ 此项目代码由 DeepSeek 生成，人工仅做审核与微调。

数字与中文数字**双向**互转的小工具，纯 Windows 原生窗口，体积极小，输入即出结果。

- 正向：`26` + `M` → 中文 `二千六百万`、阿拉伯数字 `26,000,000`
- 反向：中文 `二千六百万` → 英文简写 `26M`

## 界面

```text
 ☑ 精简（去掉零散尾数）      ☐ 缩写四舍五入
 ┌──────────────────────┐
 │      二千六百万        │
 └──────────────────────┘
  [ K ]  [ M ]  [ B ]  [ T ]
    千     百万   十亿    兆
 ──────────────────────────
 大写：二千六百万
 数字：26,000,000
 缩写：26M
```

输入框认两种写法：填 `26` 再点单位按钮就按「26 百万」算；直接填中文数字则按中文数字本身算，此时单位按钮不参与。

## 功能

- **双向转换** — 数字 → 中文数字，中文数字 → `26M` 英文简写
- **即时转换** — 键入即出结果，无需点击按钮
- **四种单位** — K（千）、M（百万）、B（十亿）、T（兆）
- **平铺切换** — 单位按钮一字排开，所见即所得
- **精简模式** — 自动去掉零散尾数，保留 3 位有效数字，一眼看懂
- **两种取舍** — 英文简写可切换「截断」与「四舍五入」，见下节
- **窗口可调** — 随意拉伸，最小 280×230
- **零依赖** — 仅用 Python 标准库 tkinter，无需安装任何第三方包

## 下载

> [Releases](https://github.com/jiahuli/NumberReadable-CN/releases) 下载 `number-readable.exe`（[v1.1 直链](https://github.com/jiahuli/NumberReadable-CN/releases/download/v1.1/number-readable.exe)），约 11 MB 单文件，双击即用，无控制台弹窗，目标机无需安装 Python。

## 核心需求：中文数字 → 英文简写

```python
import importlib.util

spec = importlib.util.spec_from_file_location("number_readable", "number-readable.py")
nr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nr)

nr.chinese_to_number("二千六百万")                            # 26000000
nr.to_compact_number(nr.chinese_to_number("二千六百万"))      # '26M'

# 一步到位
def cn_to_compact(text, rounding="trunc"):
    return nr.to_compact_number(nr.chinese_to_number(text), rounding=rounding)

cn_to_compact("九百六十万")            # '9.6M'
cn_to_compact("十二亿三千万")          # '1.2B'
cn_to_compact("一亿六千九百七十五万")   # '169.7M'
```

`chinese_to_number(text)` 支持 零一二三四五六七八九两、十百千万亿兆，可带「负」前缀，按严格读法解析（`两千三` 得 `2003`，不是口语的 `2300`）。与 `to_chinese_upper()` 互逆，`to_chinese_upper(x)` 再解析回来恒等于 `x`。

## 数字缩写转换（API）

`to_compact_number(num, rounding="trunc")` 把任意数值压成带英文单位缩写的紧凑形式：

```python
nr.to_compact_number(1697507113)                      # '1.6B'  默认截断
nr.to_compact_number(1697507113, rounding="round")    # '1.7B'  四舍五入
nr.to_compact_number(1534000)                         # '1.5M'
nr.to_compact_number(1000)                            # '1K'
nr.to_compact_number(999)                             # '999'
nr.to_compact_number(-1697507113)                     # '-1.6B'
```

### 两种取舍方式

| `rounding` | 规则 | `1697507113` | 什么时候用 |
| --- | --- | --- | --- |
| `"trunc"`（默认） | 第三位小数起直接舍去，结果**只会小于等于**真实值 | `1.6B` | 对外披露、成本与容量承诺、额度上限、风控阈值——宁可说少，不能说多 |
| `"round"` | 第三位小数四舍五入，顶到 `1000.0` 时自动升一档 | `1.7B` | 行情推送、报表概览、界面展示、口头估算——只求量级一眼准确 |

`round` 的升档行为要留意：`999960000` 四舍五入是 `1000.0M`，会输出 `1B` 而不是 `1000M`；`trunc` 则停在 `999.9M`。

### 切换方式

- **界面**：勾选顶栏「缩写四舍五入」即切到四舍五入，取消勾选回到截断；切换立刻重算，无需重新输入。
- **代码**：传 `rounding="round"` 或 `rounding="trunc"`，也可用模块常量 `ROUNDING_TRUNC` / `ROUNDING_HALF_UP`；传其它值抛 `ValueError`。
- **默认值**：`"trunc"`，与旧版行为一致，老代码不受影响。

### 其余规则

- 单位取 K / M / B / T 中**不超过该数值的最大一档**
- 末尾的 `.0` 省略，`1000` 得 `1K` 而不是 `1.0K`
- 低于 1000 原样返回；超过 T 继续沿用 T（`1e15` → `1000T`）
- 负号保留，`-1,000,000` → `-1M`
- `inf` / `nan` 原样返回字符串，不抛异常

> 文件名带连字符无法直接 `import`，上面的 `importlib` 写法是仓库里唯一的加载方式；正式引用时把它复制成合法模块名更省事。

## 测试

```bash
python -m unittest -v test_number_readable
```

共 34 个用例。覆盖中文数字解析（含 万亿兆 嵌套、负号、非法字符、与 `to_chinese_upper()` 的双向回环）、缩写的典型值与单位边界（999 / 1000 / 999999…）、浮点截断精度、负数与非有限值、两种取舍方式的差异与 `round` 升档，以及界面开关和中文输入的联动。最后顺带跑一遍各函数 docstring 里的 doctest。

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

### 1.1

- 新增 `chinese_to_number()`：中文数字 → 整数，与 `to_chinese_upper()` 互逆，支持 万亿兆 嵌套与「负」前缀
- 界面支持反向输入：直接填 `二千六百万` 即出 `26M`，此时单位按钮不参与计算
- 新增 `to_compact_number()`：数值 → K/M/B/T 缩写，界面新增「缩写」一栏
- 缩写支持 `trunc`（截断）与 `round`（四舍五入）两种取舍，界面可勾选切换
- 修掉 `round` 进位到 `1000.0` 的越档问题（`999960000` 现在正确输出 `1B`）
- 新增 `test_number_readable.py`，34 个用例
- 修正 README 中指向已不存在文件 `kmbt-to-chinese.py` 的命令

### 1.0

- 初始版本：K/M/B/T 单位数字 → 中文数字 + 千分位数字

## 许可

MIT License
