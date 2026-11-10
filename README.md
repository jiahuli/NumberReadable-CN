# NumberReadable CN

> ⚠️ 此项目代码由 DeepSeek 生成，人工仅做审核与微调。

把英文数字单位缩写（K / M / B / T）一键转为**中文大写**和**阿拉伯数字**的小工具。

纯 Windows 原生窗口，体积极小，输入即出结果。

## 界面

```text
 ☑ 精简（去掉零散尾数）      ☐ 缩写四舍五入
 ┌──────────────────────┐
 │        1.534         │
 └──────────────────────┘
  [ K ]  [ M ]  [ B ]  [ T ]
    千     百万   十亿    兆
 ──────────────────────────
 大写：一百五十三万
 数字：1,530,000
 缩写：1.5M
```

## 功能

- **即时转换** — 键入即出结果，无需点击按钮
- **四种单位** — K（千）、M（百万）、B（十亿）、T（兆）
- **平铺切换** — 单位按钮一字排开，所见即所得
- **精简模式** — 自动去掉零散尾数，保留 3 位有效数字，一眼看懂
- **数字缩写** — 结果同步压缩回 K/M/B/T 紧凑写法（如 `1,530,000` → `1.5M`）
- **两种取舍** — 缩写可切换「截断」与「四舍五入」，见下节
- **窗口可调** — 随意拉伸，最小 280×230
- **零依赖** — 仅用 Python 标准库 tkinter，无需安装任何第三方包

## 下载

> [GitHub Releases](https://github.com/jiahuli/kmbt-to-chinese/releases) 下载 `kmbt-to-chinese.exe`，双击即用，无控制台弹窗。

## 数字缩写转换（API）

`to_compact_number(num, rounding="trunc")` 把任意数值压成带英文单位缩写的紧凑形式：

```python
import importlib.util

spec = importlib.util.spec_from_file_location("number_readable", "number-readable.py")
nr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nr)

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
- **默认值**：`"trunc"`，与 0.1 版行为一致，老代码不受影响。

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

覆盖缩写的典型值、单位边界（999 / 1000 / 999999…）、浮点截断精度、负数与非有限值；另有一组用例专门盯两种取舍方式的差异、`round` 的升档行为、默认值不变，以及界面开关的联动。最后顺带跑一遍各函数 docstring 里的 doctest。

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

### 0.2

- 新增 `to_compact_number()`：数值 → K/M/B/T 缩写，界面新增「缩写」一栏
- 缩写支持 `trunc`（截断）与 `round`（四舍五入）两种取舍，界面可勾选切换
- 修掉 `round` 进位到 `1000.0` 的越档问题（`999960000` 现在正确输出 `1B`）
- 新增 `test_number_readable.py`，23 个用例
- 修正 README 中指向已不存在文件 `kmbt-to-chinese.py` 的命令

## 许可

MIT License
