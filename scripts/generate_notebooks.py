#!/usr/bin/env python3
"""Generate the maintained Colab course notebooks."""

from __future__ import annotations

import base64
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from nbformat_lite import code_cell, markdown_cell, write_notebook

REPO = "ialimustufa/python-crash-course"
BRANCH = "master"
NOTEBOOK_DIR = ROOT / "notebooks"

SEQUENCE = [
    ("00_Colab_and_First_Program.ipynb", "00 · Colab and your first program"),
    ("01_Values_Strings_and_Conversion.ipynb", "01 · Values, strings, and conversion"),
    ("02_Collections_Indexing_and_Slicing.ipynb", "02 · Collections, indexing, and slicing"),
    ("03_Conditionals_and_Loops.ipynb", "03 · Conditionals and loops"),
    ("04_Functions_Scope_and_Comprehensions.ipynb", "04 · Functions, scope, and comprehensions"),
    ("05_Errors_Modules_and_Files.ipynb", "05 · Errors, modules, and files"),
    ("06_Python_Data_Workflows_for_ML.ipynb", "06 · Python data workflows for ML"),
    ("07_Fundamentals_Capstone.ipynb", "07 · Fundamentals capstone"),
]


def colab_url(filename: str) -> str:
    return (
        "https://colab.research.google.com/github/"
        f"{REPO}/blob/{BRANCH}/notebooks/{filename.replace(' ', '%20')}"
    )


def github_url(filename: str) -> str:
    return f"https://github.com/{REPO}/blob/{BRANCH}/notebooks/{filename.replace(' ', '%20')}"


def badge(filename: str) -> str:
    return (
        f'<a href="{colab_url(filename)}" target="_parent">'
        '<img src="https://colab.research.google.com/assets/colab-badge.svg" '
        'alt="Open In Colab"/></a>'
    )


def nav(current: str) -> str:
    names = [item[0] for item in SEQUENCE]
    index = names.index(current)
    prev_name = names[index - 1] if index > 0 else None
    next_name = names[index + 1] if index + 1 < len(names) else None
    parts = ["## Navigation", ""]
    if prev_name:
        parts.append(
            f"- Previous: [{prev_name}]({github_url(prev_name)}) · "
            f"[Open in Colab]({colab_url(prev_name)})"
        )
    else:
        parts.append("- Previous: this is the first notebook")
    if next_name:
        parts.append(
            f"- Next: [{next_name}]({github_url(next_name)}) · "
            f"[Open in Colab]({colab_url(next_name)})"
        )
    else:
        parts.append("- Next: you finished the sequence. Return to the course README.")
    parts.append(
        "- Course home: [README.md](https://github.com/"
        f"{REPO}/blob/{BRANCH}/README.md)"
    )
    return "\n".join(parts)


def header(filename: str, title: str, minutes: int, prereq: str, objectives: list[str]) -> str:
    objective_lines = "\n".join(f"- {item}" for item in objectives)
    return f"""{badge(filename)}

# {title}

| | |
|---|---|
| Time | about {minutes} minutes |
| Prerequisites | {prereq} |
| Environment | Google Colab, or any Python 3 notebook |
| Thread | Bike-share trips in Indian cities — the same story builds toward the capstone |

## How to use this notebook

1. Click **Open in Colab**, then use **File → Save a copy in Drive**.
2. Run cells **from top to bottom**. If names go missing, use **Runtime → Restart session** and **Run all**.
3. When you see **Predict**, decide the output before you run.
4. Practice cells include a working answer so **Run all** never fails (needed for class and CI). To learn, comment out the answer, rewrite it, then run the check.
5. Hints sit under each practice. Clean solutions are at the end.

Concept sections include diagrams of the idea, not only the code. They show as pictures in Colab and as Mermaid on GitHub.

## What you will be able to do

{objective_lines}
"""


def hint(practice_id: str, text: str) -> str:
    return f"""<details>
<summary>Hint {practice_id}</summary>

{text}

</details>"""


def after_run(text: str) -> str:
    return f"""<details>
<summary>After you run</summary>

{text}

</details>"""


def understanding(items: list[tuple[str, str]]) -> str:
    blocks = ["## Check your understanding", ""]
    for question, answer in items:
        blocks.append(
            f"""<details>
<summary>{question}</summary>

{answer}

</details>
"""
        )
    return "\n".join(blocks)


def solution_block(practice_id: str, code: str) -> str:
    return f"""<details>
<summary>Solution {practice_id}</summary>

```python
{code.strip()}
```

</details>"""


_NBSP = "\u00a0"
_LABEL_PAD = "&nbsp;" * 8


def _pad_label(text: str) -> str:
    """Widen labels so Mermaid SVG rects do not clip the last character."""
    cleaned = (
        text.replace(_NBSP, " ")
        .replace("&nbsp;", "")
        .strip()
        .strip('"')
        .strip()
    )
    return f"{cleaned}{_LABEL_PAD}"


def format_mermaid(source: str) -> str:
    """Normalize a flowchart so GitHub and mermaid.ink keep node text readable."""
    body = textwrap.dedent(source).strip()
    body = re.sub(r"^%%\{init:.*?\}%%\s*", "", body)
    body = re.sub(
        r"(subgraph\s+[A-Za-z][A-Za-z0-9]*\s*)\[([^\]]+)\]",
        lambda m: f'{m.group(1)}["{_pad_label(m.group(2))}"]',
        body,
    )
    body = re.sub(
        r'([A-Za-z][A-Za-z0-9]*)\["([^"]*)"\]',
        lambda m: f'{m.group(1)}["{_pad_label(m.group(2))}"]',
        body,
    )
    body = re.sub(
        r'([A-Za-z][A-Za-z0-9]*)\{"([^"]*)"\}',
        lambda m: f'{m.group(1)}{{"{_pad_label(m.group(2))}"}}',
        body,
    )
    body = re.sub(
        r'([A-Za-z][A-Za-z0-9]*)\[([^\]"\n]+)\]',
        lambda m: f'{m.group(1)}["{_pad_label(m.group(2))}"]',
        body,
    )
    body = re.sub(
        r"([A-Za-z][A-Za-z0-9]*)\{([^{}\"\n]+)\}",
        lambda m: f'{m.group(1)}{{"{_pad_label(m.group(2))}"}}',
        body,
    )
    return body


def mermaid(source: str, alt: str) -> str:
    """Mermaid for GitHub, plus an SVG so the same diagram shows in Colab."""
    raw = textwrap.dedent(source).strip()
    body = format_mermaid(raw)
    encoded = base64.urlsafe_b64encode(body.encode("utf-8")).decode("ascii")
    url = f"https://mermaid.ink/svg/{encoded}"
    return (
        f"![{alt}]({url})\n\n"
        "<details>\n"
        "<summary>Diagram source</summary>\n\n"
        f"```mermaid\n{raw}\n```\n\n"
        "</details>"
    )


class Builder:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self.cells: list[dict] = []
        self.n = 0

    def _id(self, kind: str) -> str:
        self.n += 1
        return f"{self.prefix}-{kind}-{self.n:03d}"

    def md(self, text: str) -> None:
        self.cells.append(markdown_cell(text, self._id("md")))

    def code(self, text: str) -> None:
        self.cells.append(code_cell(text, self._id("code")))


def build_00() -> list[dict]:
    fn = SEQUENCE[0][0]
    b = Builder("00")
    b.md(
        header(
            fn,
            SEQUENCE[0][1],
            35,
            "None. This is the start of the course.",
            [
                "Open Colab, save your own copy, and run cells in order",
                "Use comments, `print()`, and variables",
                "Explain why indentation creates a code block",
                "Read a short traceback and name the error type",
                "Write a small greeting program from variables",
            ],
        )
    )
    b.md(
        """## Colab in 60 seconds

A Colab notebook is a sequence of **markdown cells** (notes) and **code cells** (Python).

- **Shift+Enter** runs the current cell and moves to the next one.
- Variables live in the **runtime**, not in the file on disk. Running cell 5 before cell 4 can fail even if both cells are correct.
- **Runtime → Run all** is the honest test: would this notebook work for the next person?
- Closing the tab later may recycle the runtime. Re-run from the top when that happens.

This course stays on Python's standard library. You do not need to `pip install` anything.

"""
        + mermaid(
            """
            flowchart LR
              notebookFile[Notebook file] --> cells[Markdown and code cells]
              cells --> runtime[Colab runtime]
              runtime --> names[Names and values]
            """,
            "The notebook file is not the runtime; names live in the runtime",
        )
    )
    b.md("## Comments and `print()`")
    b.md("`print()` is how a notebook talks back to you. A line starting with `#` is a comment: Python skips it.")
    b.code(
        """# A comment starts with # and is ignored by Python.
# Shift+Enter runs this cell.

print("Hello, Colab")
print("You can print several lines")"""
    )
    b.md(
        """## Variables

A variable is a **name that refers to a value**. You do not declare a type first. Assignment uses `=`.

Text needs quotes. `city = Mumbai` looks up a name called Mumbai. `city = "Mumbai"` stores text.

"""
        + mermaid(
            """
            flowchart LR
              nameCity[city] --> textMumbai["Mumbai"]
              nameRiders[riders] --> numTwelve[12]
            """,
            "A variable is a name that refers to a value",
        )
    )
    b.code(
        """city = "Mumbai"
riders = 12
print(city)
print(riders)
print(type(city), type(riders))"""
    )
    b.md("**Modify:** change `city` to another city and run the cell again. The old value is gone.")
    b.md(
        """## Predict, then run

What does the next cell print? Three lines or one?"""
    )
    b.code(
        """label = "bike trips"
count = 3
print(label)
print(count)
print(label, count)"""
    )
    b.md(
        after_run(
            "Three lines: `bike trips`, then `3`, then `bike trips 3`. "
            "`print(a, b)` separates values with a space."
        )
    )
    b.md(
        """## Indentation

Python uses indentation to mean "this line belongs to the block above." Other languages often use `{}`. Here, spaces are syntax.

Use **4 spaces** (Colab's Tab key does this). Mixing Tab and spaces, or forgetting the indent after `if`, causes `IndentationError`.

"""
        + mermaid(
            """
            flowchart TB
              ifReady["if ready:"] --> inBlock["indented lines belong to the block"]
              ifReady --> afterBlock["unindented line runs either way"]
            """,
            "Indentation puts lines inside the block above",
        )
    )
    b.code(
        """ready = True
if ready:
    print("Runtime is ready")
    print("This second line is in the same block")
print("This line runs either way")"""
    )
    b.md(
        """## Reading a traceback

The next cells **catch** errors so **Run all** can continue. In real work the kernel would stop.

Read the **error type** first (`NameError`, `IndentationError`), then the line it points at.

`NameError` is the usual result of running cells out of order: you used a name that was never assigned in *this* runtime.

"""
        + mermaid(
            """
            flowchart TB
              traceback[Traceback] --> errType[Read the error type first]
              errType --> errLine[Then the line it points at]
            """,
            "Read the error type in a traceback before the rest",
        )
    )
    b.code(
        """try:
    print(never_assigned)
except NameError as exc:
    print(type(exc).__name__)
    print(exc)"""
    )
    b.code(
        """broken = "if True:\\nprint('this line forgot its indent')"
try:
    exec(broken)
except IndentationError as exc:
    print(type(exc).__name__)
    print(exc)"""
    )
    b.md("## Practice 00.1")
    b.md("Assign your name and a year to variables, then print both.")
    b.code(
        """# Practice 00.1 — comment out the next two assignments and rewrite them.
learner_name = "Alex"
year = 2026
print(learner_name)
print(year)

# Check 00.1
assert isinstance(learner_name, str) and learner_name
assert isinstance(year, int) and year >= 1990
print("Practice 00.1 passed.")"""
    )
    b.md(hint("00.1", "Use quotes for the name. Do not quote the year."))
    b.md("## Practice 00.2")
    b.md(
        "Build a greeting from two variables using `+`. "
        "(f-strings come in notebook 01; `+` is enough here.)"
    )
    b.code(
        """# Practice 00.2
first = "Priya"
course = "Python Crash Course"
greeting = "Hi " + first + ", welcome to " + course + "."
print(greeting)

# Check 00.2
assert first in greeting and course in greeting
assert greeting.startswith("Hi ")
print("Practice 00.2 passed.")"""
    )
    b.md(hint("00.2", 'Glue pieces with `+`. Remember spaces inside the quoted bits: `"Hi "` not `"Hi"`.'))
    b.md(
        """## Common mistakes

- Running cells out of order, then wondering why a name is missing (`NameError`).
- Using `=` (assign) when you meant to compare later with `==`.
- Forgetting quotes around text.
- Editing a cell and not re-running it — the runtime still has the old value.
"""
    )
    b.md("## Recap")
    b.md(
        """- Colab runs Python in a runtime. Order matters.
- Names refer to values. `print()` shows them.
- Indentation defines blocks.
- Tracebacks start with the error type; read that before the rest.
"""
    )
    b.md(
        understanding(
            [
                (
                    "Where do variables live after you run a cell?",
                    "In the runtime, in the order you actually ran cells — not in the markdown, and not on GitHub.",
                ),
                (
                    "What should you read first in a traceback?",
                    "The error type, such as `NameError` or `IndentationError`.",
                ),
            ]
        )
    )
    b.md("## Solutions")
    b.md(solution_block("00.1", 'learner_name = "Alex"\nyear = 2026\nprint(learner_name)\nprint(year)'))
    b.md(
        solution_block(
            "00.2",
            'first = "Priya"\ncourse = "Python Crash Course"\ngreeting = "Hi " + first + ", welcome to " + course + "."',
        )
    )
    b.md(nav(fn))
    return b.cells


def build_01() -> list[dict]:
    fn = SEQUENCE[1][0]
    b = Builder("01")
    b.md(
        header(
            fn,
            SEQUENCE[1][1],
            45,
            "Notebook 00",
            [
                "Name the common value types: `int`, `float`, `bool`, `None`, `str`",
                "Use arithmetic, comparison, and logical operators",
                "Convert between types on purpose",
                "Index, slice, and format strings",
            ],
        )
    )
    b.md("## Recap warm-up")
    b.code(
        """title = "values and strings"
print(title)
print(type(title))"""
    )
    b.md(
        """## Values and types

| Type | Example | Meaning |
|---|---|---|
| `int` | `7` | whole number |
| `float` | `7.5` | number with a fraction |
| `bool` | `True` / `False` | yes or no |
| `None` | `None` | missing / no value |
| `str` | `"ride"` | text |

`type(x)` reports the type. Python will not add a number to text until you convert one of them.

`/` always gives a `float` (`4 / 2` is `2.0`). `//` is integer division. `**` is power.

"""
        + mermaid(
            """
            flowchart LR
              intType[int] --> okMath[Multiply and add]
              strType[str] --> okText[Index and concatenate]
              mix["str plus int"] --> typeError[TypeError]
            """,
            "The type of a value decides which operations are legal",
        )
    )
    b.code(
        """trips = 7
distance_km = 12.5
active = True
note = None
label = "commute"

print(type(trips), type(distance_km), type(active), type(note), type(label))
print(trips * distance_km)
print("division", 5 / 2, "floor", 5 // 2, "power", 2 ** 3)
print(3 == 3, 3 != 4, 3 < 4)
print(True and False, True or False, not False)"""
    )
    b.md("## Predict: text plus a number")
    b.md("The next cell **catches** `TypeError`. What goes wrong if you add `\"3\"` and `1`?")
    b.code(
        """try:
    print("3" + 1)
except TypeError as exc:
    print(type(exc).__name__)
    print(exc)
print("fixed:", int("3") + 1)
print("or text:", "3" + str(1))"""
    )
    b.md(
        """## Conversion

If a value came from a form or a CSV cell, it is often a **string**, even when it looks like `23`. Convert with `int()`, `float()`, or `str()`.

`int("19.0")` fails because of the decimal point. Use `int(float("19.0"))` when you need a whole number.

Bad conversions raise `ValueError`. Notebook 05 will catch that on purpose.

"""
        + mermaid(
            """
            flowchart LR
              csvCell["CSV cell 23"] --> asText[str]
              asText --> intFn["int()"]
              intFn --> asNumber[23]
              asText --> floatFn["float()"]
              floatFn --> asFloat["23.0"]
            """,
            "A CSV cell is text until you convert it on purpose",
        )
    )
    b.code(
        """raw_age = "23"          # a CSV cell or form field, not a number yet
age = int(raw_age)
print(age, type(age))
print(age + 1)

print(float("3.5"))
print(str(40) + " km")
try:
    int("19.0")
except ValueError as exc:
    print("int on 19.0 failed:", exc)
print("via float:", int(float("19.0")))"""
    )
    b.md(
        """## Strings: index, slice, methods, f-strings

Indexing starts at `0`. Slices are `[start:stop]` and **exclude** `stop`. Negative indexes count from the end.

An f-string puts values into text: `f"{name} logged {trips} trips."`

"""
        + mermaid(
            """
            flowchart LR
              city["Hyderabad"] --> firstCh["index 0 is H"]
              city --> lastCh["index -1 is d"]
              city --> slice["slice 0:5 is Hyder"]
            """,
            "String indexes start at 0; a slice excludes the stop index",
        )
    )
    b.code(
        """city = "Hyderabad"
print(city[0], city[-1])
print(city[0:5])
print(city[::-1])
print(city.lower(), city.upper())
print("Hyder" in city)
print(len(city))

name = "ana"
print(f"{name.title()} logged {trips} trips.")"""
    )
    b.md(
        after_run(
            "`city[0:5]` is `Hyder` (indexes 0–4). "
            "The f-string prints `Ana logged 7 trips.`"
        )
    )
    b.md("## Practice 01.1")
    b.md("Convert 22°C to Fahrenheit: `f = c * 9 / 5 + 32`.")
    b.code(
        """# Practice 01.1
celsius = 22
fahrenheit = celsius * 9 / 5 + 32
print(fahrenheit)

# Check 01.1
assert fahrenheit == 71.6
print("Practice 01.1 passed.")"""
    )
    b.md(hint("01.1", "Use `*` and `/` before `+`. Parentheses are optional here because of operator order."))
    b.md("## Practice 01.2")
    b.md("From `full = \"Ada Lovelace\"`, get the first name and last name with slicing and `split`.")
    b.code(
        """# Practice 01.2
full = "Ada Lovelace"
first_name = full.split()[0]
last_name = full.split()[1]
print(first_name, last_name)

# Check 01.2
assert first_name == "Ada"
assert last_name == "Lovelace"
print("Practice 01.2 passed.")"""
    )
    b.md(hint("01.2", "`full.split()` returns `['Ada', 'Lovelace']`. Index `0` and `1`."))
    b.md("## Practice 01.3")
    b.md("Convert the string `\"19.0\"` to an integer number of years. Truncate toward zero via `int(float(...))`.")
    b.code(
        """# Practice 01.3
raw = "19.0"
years = int(float(raw))
print(years)

# Check 01.3
assert years == 19 and isinstance(years, int)
print("Practice 01.3 passed.")"""
    )
    b.md(hint("01.3", "`int(\"19.0\")` fails. Convert to `float` first, then to `int`."))
    b.md(
        """## Common mistakes

- `+` on strings concatenates: `\"3\" + \"4\"` is `\"34\"`.
- `/` always returns a `float` in Python 3: `4 / 2` is `2.0`. Use `//` for integer division.
- Slices never include the end index: `\"Python\"[0:3]` is `Pyt`.
"""
    )
    b.md("## Recap")
    b.md("Types decide what operations are legal. Convert on purpose. Strings are sequences you can index, slice, and format with f-strings.")
    b.md(
        understanding(
            [
                (
                    "What does int(\"19.0\") do in Python 3?",
                    "It raises `ValueError`. Convert to `float` first, then to `int`.",
                ),
                (
                    "What is \"Python\"[0:3]?",
                    "`Pyt` — the end index is excluded.",
                ),
            ]
        )
    )
    b.md("## Solutions")
    b.md(solution_block("01.1", "celsius = 22\nfahrenheit = celsius * 9 / 5 + 32"))
    b.md(solution_block("01.2", 'full = "Ada Lovelace"\nfirst_name = full.split()[0]\nlast_name = full.split()[1]'))
    b.md(solution_block("01.3", 'raw = "19.0"\nyears = int(float(raw))'))
    b.md(nav(fn))
    return b.cells


def build_02() -> list[dict]:
    fn = SEQUENCE[2][0]
    b = Builder("02")
    b.md(
        header(
            fn,
            SEQUENCE[2][1],
            50,
            "Notebooks 00–01",
            [
                "Create and update lists, tuples, dictionaries, and sets",
                "Index and slice nested collections",
                "Explain aliasing versus a real copy",
                "Store a row of data as a dictionary",
            ],
        )
    )
    b.md("## Recap warm-up")
    b.code(
        """sample = "collections"
print(sample[:3], len(sample))"""
    )
    b.md(
        """## Which collection?

| Collection | Write it | Ordered | Change in place | Duplicate values | Lookup |
|---|---|---|---|---|---|
| list | `[1, 2]` | yes | yes | yes | by index |
| tuple | `(1, 2)` | yes | no | yes | by index |
| dict | `{"k": 1}` | yes (insertion) | yes | keys unique | by key |
| set | `{1, 2}` | no | yes | no | by value |

Machine-learning tables are usually a **list of dictionaries** (one dict per row) until you later load them into pandas.

"""
        + mermaid(
            """
            flowchart LR
              listCol[list] --> grow[Grow and change]
              tupleCol[tuple] --> frozen[Fixed sequence]
              dictCol[dict] --> byKey[Look up by column name]
              setCol[set] --> unique[Unique membership]
            """,
            "Pick a collection by how you look values up and whether they can change",
        )
    )
    b.code(
        """cities = ["Mumbai", "Pune", "Bengaluru"]
print(cities[0], cities[-1], cities[0:2])
cities.append("Hyderabad")
cities[1] = "Pune city"
print(cities)

point = (19.07, 72.87)
print(point[0])
lat, lon = point
print("unpacked", lat, lon)
try:
    point[0] = 0
except TypeError as exc:
    print("tuples do not change:", type(exc).__name__)

rider = {"id": 1, "city": "Mumbai", "hours": 2.0}
print(rider["city"])
rider["hours"] = 2.5
print(rider.get("pass_type", "unknown"))

seen = {"Mumbai", "Pune", "Mumbai"}
print(seen)
print("Pune" in seen)"""
    )
    b.md(
        """## Nested records

A list can hold dictionaries. A dictionary can hold lists. Draw the path: `rows[0][\"city\"]`.

"""
        + mermaid(
            """
            flowchart LR
              rows[rows] --> firstRow["rows[0]"]
              firstRow --> cityField["city is Mumbai"]
            """,
            "Nested access follows a path: first the row, then the key",
        )
    )
    b.code(
        """rows = [
    {"id": 1, "city": "Mumbai", "km": 8.5},
    {"id": 2, "city": "Pune", "km": 3.0},
]
print(rows[0]["city"])
print(rows[1]["km"])
print(rows[0])"""
    )
    b.md(
        """## Aliases and copies

`b = a` does not copy a list. Both names point at the same object. Use `a.copy()` or `list(a)` for a shallow copy. Nested objects still need `copy.deepcopy` if you must duplicate inner lists.

"""
        + mermaid(
            """
            flowchart LR
              original[original] --> sameList[same list]
              alias[alias] --> sameList
              clone[clone] --> otherList[separate list]
            """,
            "An alias shares the list; a copy is a second list",
        )
    )
    b.code(
        """original = ["a", "b"]
alias = original
clone = original.copy()
alias.append("c")
print("original", original)
print("clone   ", clone)
print("same object?", alias is original, clone is original)"""
    )
    b.md("## Practice 02.1")
    b.md("Start from `['cricket', 'football']`. Append `'hockey'`, then replace `'football'` with `'tennis'`.")
    b.code(
        """# Practice 02.1
sports = ["cricket", "football"]
sports.append("hockey")
sports[1] = "tennis"
print(sports)

# Check 02.1
assert sports == ["cricket", "tennis", "hockey"]
print("Practice 02.1 passed.")"""
    )
    b.md(hint("02.1", "`append` adds at the end. `'football'` is index `1`."))
    b.md("## Practice 02.2")
    b.md("Build a rider dictionary with keys `id`, `city`, and `returned` (a boolean).")
    b.code(
        """# Practice 02.2
rider = {"id": 7, "city": "Pune", "returned": True}
print(rider)

# Check 02.2
assert rider["id"] == 7
assert rider["city"] == "Pune"
assert rider["returned"] is True
print("Practice 02.2 passed.")"""
    )
    b.md(hint("02.2", "Use curly braces and `key: value` pairs. `True` is a boolean, not `\"True\"`."))
    b.md("## Practice 02.3")
    b.md("From the nested list `rows`, read the kilometers for the **second** rider (`rows[1]`).")
    b.code(
        """# Practice 02.3
rows = [
    {"id": 1, "km": 8.5},
    {"id": 2, "km": 3.0},
]
km_for_two = rows[1]["km"]
print(km_for_two)

# Check 02.3
assert km_for_two == 3.0
print("Practice 02.3 passed.")"""
    )
    b.md(hint("02.3", "The second dictionary is index `1`. Then use `[\"km\"]`."))
    b.md(
        """## Common mistakes

- `dict[0]` fails unless `0` is actually a key. Use a list for positional access.
- Changing an alias changes the original list.
- Tuples cannot be updated: `point[0] = 0` raises `TypeError`.
"""
    )
    b.md("## Recap")
    b.md("Lists grow and change. Tuples freeze a sequence (good for a lat/lon pair). Dicts map names to values and are the usual shape of one data row.")
    b.md(
        understanding(
            [
                (
                    "Which collection maps a column name to a value for one row?",
                    "A dictionary. A list of dictionaries is a small table.",
                ),
                (
                    "What does b = a mean when a is a list?",
                    "Both names refer to the same list. Use `.copy()` for a separate list.",
                ),
            ]
        )
    )
    b.md("## Solutions")
    b.md(
        solution_block(
            "02.1",
            'sports = ["cricket", "football"]\nsports.append("hockey")\nsports[1] = "tennis"',
        )
    )
    b.md(
        solution_block(
            "02.2",
            'rider = {"id": 7, "city": "Pune", "returned": True}',
        )
    )
    b.md(
        solution_block(
            "02.3",
            'km_for_two = rows[1]["km"]',
        )
    )
    b.md(nav(fn))
    return b.cells


def build_03() -> list[dict]:
    fn = SEQUENCE[3][0]
    b = Builder("03")
    b.md(
        header(
            fn,
            SEQUENCE[3][1],
            50,
            "Notebooks 00–02",
            [
                "Write `if` / `elif` / `else` branches and validate values",
                "Loop with `for`, `while`, `range`, `enumerate`, and `zip`",
                "Build totals with an accumulator",
                "Flatten a nested list with a nested loop",
            ],
        )
    )
    b.md("## Recap warm-up")
    b.code(
        """hours = [1, 2, 3]
print(sum(hours), hours[-1])"""
    )
    b.md(
        """## Decisions

Python checks conditions from the top. The first true branch runs, then the chain stops.

**Truthiness:** empty lists, empty strings, `0`, and `None` count as false in an `if`. A non-empty list counts as true.

There is no `input()` in these notebooks so **Run all** never waits for a person. Treat variables as if they came from a form.

"""
        + mermaid(
            """
            flowchart TB
              startCheck[Check hours]
              startCheck --> q1{"hours less than 0?"}
              q1 -->|yes| invalid[invalid]
              q1 -->|no| q2{"hours equal 0?"}
              q2 -->|yes| empty[empty]
              q2 -->|no| okStatus[ok]
            """,
            "if / elif / else takes the first true branch, then stops",
        )
    )
    b.code(
        """hours = 2.5
if hours < 0:
    status = "invalid"
elif hours == 0:
    status = "empty"
else:
    status = "ok"
print(status)

valid_cities = {"Mumbai", "Pune", "Bengaluru"}
city = "Pune"
print(city in valid_cities)

if []:
    print("empty list would not print this")
print("empty list is falsy")"""
    )
    b.md(
        """## Loops

- `for item in sequence:` visits each value.
- `range(n)` is `0 .. n-1`.
- `enumerate(sequence)` gives `(index, value)`.
- `zip(a, b)` walks two sequences together.
- `while` repeats until the condition becomes false. **Update the counter**, or it never ends.
- `continue` skips the rest of this round. `break` leaves the loop.

Nested loops are just loops inside loops, not a third kind of loop.

"""
        + mermaid(
            """
            flowchart LR
              seq[sequence] --> visit[visit each item]
              visit --> acc[update accumulator]
              acc --> visit
            """,
            "A loop repeats a path; an accumulator remembers what you have seen",
        )
        + """

"""
        + mermaid(
            """
            flowchart LR
              item[item] --> skip{"continue?"}
              skip -->|yes| nextItem[next item]
              skip -->|no| work[do the work]
              work --> leave{"break?"}
              leave -->|yes| afterLoop[leave the loop]
              leave -->|no| nextItem
            """,
            "continue skips the rest of this round; break leaves the loop",
        )
    )
    b.code(
        """for n in range(3):
    print("range", n)

names = ["Ada", "Grace"]
for index, name in enumerate(names):
    print(index, name)

hours = [1, 2]
km = [4.0, 9.5]
for h, d in zip(hours, km):
    print(h, "h,", d, "km")

total = 0
for h in hours:
    total += h
print("total hours", total)

n = 0
while n < 3:
    print("while", n)
    n += 1

for km_value in [1.2, 8.0, 3.4, 12.1]:
    if km_value < 5:
        continue
    print("long trip", km_value)
    if km_value > 10:
        print("stopping after the first very long trip")
        break"""
    )
    b.md("## Practice 03.1")
    b.md("Classify `score` as `\"fail\"` (< 40), `\"pass\"` (40–74), or `\"distinction\"` (75+).")
    b.code(
        """# Practice 03.1
score = 81
if score < 40:
    grade = "fail"
elif score < 75:
    grade = "pass"
else:
    grade = "distinction"
print(grade)

# Check 03.1
assert grade == "distinction"
print("Practice 03.1 passed.")"""
    )
    b.md(hint("03.1", "Use `if`, `elif`, `else`. 81 is not less than 75, so it should take the last branch."))
    b.md("## Practice 03.2")
    b.md("Count how many trips in `km_list` are at least 5 km.")
    b.code(
        """# Practice 03.2
km_list = [1.2, 8.0, 5.0, 3.4, 12.1]
long_trips = 0
for km in km_list:
    if km >= 5:
        long_trips += 1
print(long_trips)

# Check 03.2
assert long_trips == 3
print("Practice 03.2 passed.")"""
    )
    b.md(hint("03.2", "Start at `0`. Add `1` when `km >= 5`."))
    b.md("## Practice 03.3")
    b.md("Use `zip` to build `\"Mumbai:2.0\"` style strings.")
    b.code(
        """# Practice 03.3
cities = ["Mumbai", "Pune"]
hours = [2.0, 1.5]
labels = []
for city, hour in zip(cities, hours):
    labels.append(f"{city}:{hour}")
print(labels)

# Check 03.3
assert labels == ["Mumbai:2.0", "Pune:1.5"]
print("Practice 03.3 passed.")"""
    )
    b.md(hint("03.3", "`for city, hour in zip(cities, hours):` gives one pair per step."))
    b.md("## Practice 03.4")
    b.md("Flatten `[[1, 2], [3, 4]]` into `[1, 2, 3, 4]` with a nested loop.")
    b.code(
        """# Practice 03.4
matrix = [[1, 2], [3, 4]]
flat = []
for row in matrix:
    for value in row:
        flat.append(value)
print(flat)

# Check 03.4
assert flat == [1, 2, 3, 4]
print("Practice 03.4 passed.")"""
    )
    b.md(hint("03.4", "Outer loop visits each inner list. Inner loop visits each number."))
    b.md(
        """## Common mistakes

- Writing `if score > 40` and `if score > 75` as two separate `if`s when you needed `elif`.
- Forgetting to update the `while` counter (`n += 1`), which never ends.
- Using `range(len(xs))` when `for x in xs` would be clearer.
"""
    )
    b.md("## Recap")
    b.md("Branches choose a path. Loops repeat a path. Accumulators remember what you have seen so far.")
    b.md(
        understanding(
            [
                (
                    "What is a nested loop?",
                    "A loop that runs inside another loop — not a third kind of loop besides `for` and `while`.",
                ),
                (
                    "What does enumerate(xs) yield each step?",
                    "A pair `(index, value)`, starting the index at 0.",
                ),
            ]
        )
    )
    b.md("## Solutions")
    b.md(
        solution_block(
            "03.1",
            'if score < 40:\n    grade = "fail"\nelif score < 75:\n    grade = "pass"\nelse:\n    grade = "distinction"',
        )
    )
    b.md(
        solution_block(
            "03.2",
            "long_trips = 0\nfor km in km_list:\n    if km >= 5:\n        long_trips += 1",
        )
    )
    b.md(
        solution_block(
            "03.3",
            'labels = []\nfor city, hour in zip(cities, hours):\n    labels.append(f"{city}:{hour}")',
        )
    )
    b.md(
        solution_block(
            "03.4",
            "flat = []\nfor row in matrix:\n    for value in row:\n        flat.append(value)",
        )
    )
    b.md(nav(fn))
    return b.cells


def build_04() -> list[dict]:
    fn = SEQUENCE[4][0]
    b = Builder("04")
    b.md(
        header(
            fn,
            SEQUENCE[4][1],
            50,
            "Notebooks 00–03",
            [
                "Define functions with parameters, defaults, and return values",
                "Keep work in local scope and write a one-line docstring",
                "Split a task into small pure functions",
                "Rewrite a simple loop as a list comprehension",
            ],
        )
    )
    b.md("## Recap warm-up")
    b.code(
        """values = [2, 4, 4]
print(sum(values) / len(values))"""
    )
    b.md(
        """## Functions

A function is a named block you can reuse. `return` sends a value back. If you omit `return`, the result is `None`.

Names assigned inside a function are **local**. They do not overwrite names outside unless you go looking for trouble with `global` (skip that here).

A **pure** function depends only on its arguments and does not change lists or dicts that were passed in.

"""
        + mermaid(
            """
            flowchart LR
              args[arguments] --> body[function body]
              body --> ret[return value]
              body --> noneRet["None if no return"]
            """,
            "Arguments go in; return sends a value back, or None if you omit return",
        )
        + """

"""
        + mermaid(
            """
            flowchart TB
              outerN["outer n stays 10"]
              callFn["add_one(3)"] --> localN["local n is 4"]
              callFn --> outerN
            """,
            "Names assigned inside a function are local",
        )
    )
    b.code(
        """def celsius_to_fahrenheit(celsius):
    \"\"\"Convert a Celsius temperature to Fahrenheit.\"\"\"
    return celsius * 9 / 5 + 32

print(celsius_to_fahrenheit(22))

def label_trip(city, hours=1.0):
    return f"{city} ({hours}h)"

print(label_trip("Mumbai"))
print(label_trip("Pune", hours=2.5))

def min_max(nums):
    return min(nums), max(nums)

low, high = min_max([3, 9, 4])
print(low, high)

def shout(message):
    print(message.upper())

result = shout("ok")
print("shout returned", result)

n = 10
def add_one(x):
    n = x + 1
    return n

print("function result", add_one(3), "outer n still", n)"""
    )
    b.md(
        """## Comprehensions

A list comprehension builds a new list: `[expression for item in sequence if condition]`.

There are dict comprehensions too: `{k: v for ...}`. Start with a loop if the expression is hard to read.

`lambda` is a tiny anonymous function. Prefer a named `def` unless you need a one-off sort key. `map` and `filter` exist; comprehensions are usually clearer.

"""
        + mermaid(
            """
            flowchart LR
              km[km values] --> keep["keep if >= 5"]
              keep --> newList[new list]
            """,
            "A comprehension walks a sequence and builds a new collection",
        )
    )
    b.code(
        """km = [1.2, 8.0, 5.0]
long_only = [value for value in km if value >= 5]
squared = [value * value for value in km]
print(long_only, squared)

rows = [{"id": 1, "city": "Mumbai"}, {"id": 2, "city": "Pune"}]
by_id = {row["id"]: row["city"] for row in rows}
print(by_id)

pairs = [("b", 2), ("a", 1)]
print(sorted(pairs, key=lambda item: item[0]))"""
    )
    b.md("## Practice 04.1")
    b.md("Write `area(radius, pi=3.14159)` that returns the circle area.")
    b.code(
        """# Practice 04.1
def area(radius, pi=3.14159):
    \"\"\"Return the area of a circle.\"\"\"
    return pi * radius ** 2

print(area(5))

# Check 04.1
assert abs(area(5) - 78.53975) < 1e-6
assert abs(area(1, pi=3) - 3) < 1e-9
print("Practice 04.1 passed.")"""
    )
    b.md(hint("04.1", "`return pi * radius ** 2`. `**` binds before `*`."))
    b.md("## Practice 04.2")
    b.md("Write `seconds_to_hms(total)` that returns `(hours, minutes, seconds)` as integers.")
    b.code(
        """# Practice 04.2
def seconds_to_hms(total):
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return hours, minutes, seconds

print(seconds_to_hms(3665))

# Check 04.2
assert seconds_to_hms(3665) == (1, 1, 5)
print("Practice 04.2 passed.")"""
    )
    b.md(hint("04.2", "There are 3600 seconds in an hour and 60 in a minute. Use `//` and `%`."))
    b.md("## Practice 04.3")
    b.md("Use a comprehension to get city names in title case from the list of dicts.")
    b.code(
        """# Practice 04.3
rows = [{"city": "mumbai"}, {"city": "pune"}]
cities = [row["city"].title() for row in rows]
print(cities)

# Check 04.3
assert cities == ["Mumbai", "Pune"]
print("Practice 04.3 passed.")"""
    )
    b.md(hint("04.3", '`[row["city"].title() for row in rows]`'))
    b.md(
        """## Common mistakes

- Forgetting `return` and then asserting against `None`.
- Mutating a list argument inside a function when the caller still needs the original.
- Packing a whole program into one function instead of three small ones.
"""
    )
    b.md("## Recap")
    b.md("Functions name an idea, isolate scope, and return results. Comprehensions are loops that build a collection in one expression.")
    b.md(
        understanding(
            [
                (
                    "If a function has no return statement, what does it return?",
                    "`None`. Printing inside the function is a side effect, not a return value.",
                ),
                (
                    "Does a list comprehension change the original list?",
                    "No. It builds a **new** list.",
                ),
            ]
        )
    )
    b.md("## Solutions")
    b.md(solution_block("04.1", "def area(radius, pi=3.14159):\n    return pi * radius ** 2"))
    b.md(
        solution_block(
            "04.2",
            "def seconds_to_hms(total):\n    hours = total // 3600\n    minutes = (total % 3600) // 60\n    seconds = total % 60\n    return hours, minutes, seconds",
        )
    )
    b.md(solution_block("04.3", 'cities = [row["city"].title() for row in rows]'))
    b.md(nav(fn))
    return b.cells


def build_05() -> list[dict]:
    fn = SEQUENCE[5][0]
    b = Builder("05")
    b.md(
        header(
            fn,
            SEQUENCE[5][1],
            50,
            "Notebooks 00–04",
            [
                "Tell syntax, runtime, and logic errors apart",
                "Catch a specific exception and raise a clear one",
                "Import from the standard library",
                "Read and write JSON and CSV with `pathlib`",
            ],
        )
    )
    b.md("## Recap warm-up")
    b.code(
        """def double(n):
    return n * 2

print(double(21))"""
    )
    b.md(
        """## Three kinds of errors

| Kind | When you see it | Example |
|---|---|---|
| Syntax | before the cell really runs | missing colon, bad indent |
| Runtime | while running | `int("bike")`, `1/0`, missing key |
| Logic | it runs, the answer is wrong | averaging with the wrong list |

Catch only errors you expect. Bare `except:` hides bugs. After you convert data, `assert` the shape you promised.

"""
        + mermaid(
            """
            flowchart TB
              syntax[Syntax] --> beforeRun[Fails before the cell runs]
              runtimeErr[Runtime] --> whileRun[Fails while running]
              logicErr[Logic] --> wrongAnswer[Runs but the answer is wrong]
            """,
            "Syntax, runtime, and logic errors show up at different times",
        )
        + """

"""
        + mermaid(
            """
            flowchart LR
              tryBlock[try] --> okPath["return int(text)"]
              tryBlock --> badPath[ValueError]
              badPath --> catchNone[return None]
            """,
            "Catch only the failure you expect, then continue",
        )
    )
    b.code(
        """# Syntax: caught so Run all continues
try:
    compile("if True print('missing colon')", "<cell>", "exec")
except SyntaxError as exc:
    print("syntax:", type(exc).__name__)

# Runtime
raw = "not a number"
try:
    int(raw)
except ValueError as exc:
    print("runtime:", type(exc).__name__, exc)

# Logic: the cell runs, the answer is still wrong
km = [8.0, 4.0]
wrong_mean = sum(km) / 3
right_mean = sum(km) / len(km)
print("logic bug mean", wrong_mean, "correct mean", right_mean)

def require_positive(hours):
    if hours < 0:
        raise ValueError("hours must be >= 0")
    return hours

print(require_positive(2))
try:
    require_positive(-1)
except ValueError as exc:
    print(exc)

assert require_positive(2) == 2"""
    )
    b.md(
        """## Modules and files

`import math` loads a library. Colab files live in a **temporary** folder (`/content` on Colab). Restarting the runtime can delete them. This notebook writes under `Path.cwd() / "_course_data"` so it also works in GitHub Actions.

Always open files with a `with` block so they close even if something fails. Prefer `pathlib.Path` over raw `"/tmp/file.csv"` strings.

"""
        + mermaid(
            """
            flowchart LR
              payload[dict] --> dumps["json.dumps"]
              dumps --> writeFile["Path.write_text"]
              writeFile --> readFile["Path.read_text"]
              readFile --> loads["json.loads"]
              loads --> dictBack[dict]
            """,
            "JSON is a dict written as text, then read back as a dict",
        )
    )
    b.code(
        """import csv
import json
import math
from pathlib import Path

print(round(math.pi, 4))

DATA_DIR = Path.cwd() / "_course_data"
DATA_DIR.mkdir(exist_ok=True)

payload = {"city": "Mumbai", "trips": 3}
json_path = DATA_DIR / "rider.json"
json_path.write_text(json.dumps(payload), encoding="utf-8")
loaded = json.loads(json_path.read_text(encoding="utf-8"))
print(loaded)

csv_path = DATA_DIR / "trips.csv"
with csv_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=["id", "city"])
    writer.writeheader()
    writer.writerow({"id": 1, "city": "Pune"})

with csv_path.open(newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
print(rows)"""
    )
    b.md("## Practice 05.1")
    b.md("Write `parse_int(text)` that returns the integer, or `None` if conversion fails.")
    b.code(
        """# Practice 05.1
def parse_int(text):
    try:
        return int(text)
    except (TypeError, ValueError):
        return None

print(parse_int("42"), parse_int("nope"))

# Check 05.1
assert parse_int("42") == 42
assert parse_int("nope") is None
print("Practice 05.1 passed.")"""
    )
    b.md(hint("05.1", "Wrap `int(text)` in `try`. Catch `ValueError` and `TypeError`, then `return None`."))
    b.md("## Practice 05.2")
    b.md("Write a dict to `DATA_DIR / \"practice.json\"` and read it back.")
    b.code(
        """# Practice 05.2
practice_path = DATA_DIR / "practice.json"
record = {"id": 10, "city": "Bengaluru"}
practice_path.write_text(json.dumps(record), encoding="utf-8")
restored = json.loads(practice_path.read_text(encoding="utf-8"))
print(restored)

# Check 05.2
assert restored == record
print("Practice 05.2 passed.")"""
    )
    b.md(hint("05.2", "`json.dumps` turns a dict into text. `json.loads` reverses it."))
    b.md("## Practice 05.3")
    b.md("Parse this CSV text into a list of dictionaries with integer `id` values.")
    b.code(
        """# Practice 05.3
import io

csv_text = "id,city\\n1,Mumbai\\n2,Pune\\n"
parsed = []
reader = csv.DictReader(io.StringIO(csv_text))
for row in reader:
    parsed.append({"id": int(row["id"]), "city": row["city"]})
print(parsed)

# Check 05.3
assert parsed == [{"id": 1, "city": "Mumbai"}, {"id": 2, "city": "Pune"}]
print("Practice 05.3 passed.")"""
    )
    b.md(hint("05.3", "`csv.DictReader` yields rows. Convert `row[\"id\"]` with `int`."))
    b.md(
        """## Common mistakes

- Catching every exception and continuing silently.
- Opening a file and never closing it (use `with`).
- Assuming Colab files survive a runtime restart. They often do not.
"""
    )
    b.md("## Recap")
    b.md("Name the error, catch only what you expect, and keep data in files you control. JSON and CSV are the usual hand-off formats before pandas.")
    b.md(
        understanding(
            [
                (
                    "int(\"bike\") is which kind of problem?",
                    "A runtime `ValueError`. The line is legal Python; it fails while running.",
                ),
                (
                    "Why open files with a with block?",
                    "The file is closed even if the cell fails halfway through.",
                ),
            ]
        )
    )
    b.md("## Solutions")
    b.md(
        solution_block(
            "05.1",
            "def parse_int(text):\n    try:\n        return int(text)\n    except (TypeError, ValueError):\n        return None",
        )
    )
    b.md(
        solution_block(
            "05.2",
            'practice_path.write_text(json.dumps(record), encoding="utf-8")\nrestored = json.loads(practice_path.read_text(encoding="utf-8"))',
        )
    )
    b.md(
        solution_block(
            "05.3",
            'parsed = []\nfor row in csv.DictReader(io.StringIO(csv_text)):\n    parsed.append({"id": int(row["id"]), "city": row["city"]})',
        )
    )
    b.md(nav(fn))
    return b.cells


def build_06() -> list[dict]:
    fn = SEQUENCE[6][0]
    b = Builder("06")
    b.md(
        header(
            fn,
            SEQUENCE[6][1],
            55,
            "Notebooks 00–05",
            [
                "Clean a list of dictionaries: types, missing values, duplicates",
                "Filter, sort, group, and aggregate without pandas",
                "Separate features from a target column",
                "Make a deterministic train/validation split and scale with train-only statistics",
            ],
        )
    )
    b.md("## Recap warm-up")
    b.code(
        """row = {"hours": "2", "km": "8.5"}
print(int(row["hours"]), float(row["km"]))"""
    )
    b.md(
        """## Why this notebook exists

NumPy, pandas, and scikit-learn all expect **tidy rows**: consistent keys, numeric types, no surprise blanks, and a target you did not accidentally leak into the features.

You will do that work in pure Python. The same ideas map onto `DataFrame.dropna`, `train_test_split`, and `MinMaxScaler` later.

Libraries are objects with methods: `model.fit(X, y)`. A tiny class below shows attributes and methods without becoming an OOP course.

"""
        + mermaid(
            """
            flowchart TB
              raw[raw rows] --> clean["type, drop, dedupe"]
              clean --> tidy[list of dictionaries]
              tidy --> later[pandas and sklearn later]
            """,
            "Tidy rows in Python are the same idea libraries will automate later",
        )
    )
    b.code(
        """class Table:
    \"\"\"A tiny stand-in for the object style you will meet in ML libraries.\"\"\"

    def __init__(self, rows):
        self.rows = rows

    @property
    def n_rows(self):
        return len(self.rows)

    def column(self, name):
        return [row[name] for row in self.rows]

raw_rows = [
    {"id": "1", "city": "Mumbai", "hours": "2", "km": "8.0", "returned": "yes"},
    {"id": "2", "city": "Pune", "hours": "", "km": "3.0", "returned": "yes"},
    {"id": "3", "city": "Mumbai", "hours": "1", "km": "4.0", "returned": "no"},
    {"id": "4", "city": "Goa", "hours": "abc", "km": "5.0", "returned": "yes"},
    {"id": "5", "city": "Pune", "hours": "3", "km": "9.0", "returned": "yes"},
    {"id": "5", "city": "Pune", "hours": "3", "km": "9.0", "returned": "yes"},
    {"id": "6", "city": "Mumbai", "hours": "2", "km": "18.0", "returned": "no"},
]
print("raw rows", Table(raw_rows).n_rows)"""
    )
    b.md(
        """## Clean, then transform

"""
        + mermaid(
            """
            flowchart TB
              rawRow[each raw row] --> dup{"duplicate id?"}
              dup -->|yes| dropDup[drop duplicate]
              dup -->|no| parse[parse hours and km]
              parse --> bad{"missing or invalid?"}
              bad -->|yes| dropBad[drop the row]
              bad -->|no| keep[keep a typed row]
            """,
            "Clean by dropping bad rows before you transform the rest",
        )
    )
    b.code(
        """def parse_float(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def clean_rows(rows):
    cleaned = []
    seen_ids = set()
    report = {"dropped_missing": 0, "dropped_duplicate": 0, "dropped_invalid": 0}
    for row in rows:
        if row["id"] in seen_ids:
            report["dropped_duplicate"] += 1
            continue
        hours = parse_float(row["hours"])
        km = parse_float(row["km"])
        if hours is None or km is None:
            if row["hours"] in (None, "") or row["km"] in (None, ""):
                report["dropped_missing"] += 1
            else:
                report["dropped_invalid"] += 1
            continue
        seen_ids.add(row["id"])
        cleaned.append(
            {
                "id": int(row["id"]),
                "city": row["city"],
                "hours": hours,
                "km": km,
                "returned": row["returned"] == "yes",
                "km_per_hour": km / hours,
            }
        )
    return cleaned, report

trips, quality = clean_rows(raw_rows)
print(trips)
print(quality)"""
    )
    b.code(
        """mumbai = [row for row in trips if row["city"] == "Mumbai"]
by_km = sorted(trips, key=lambda row: row["km"], reverse=True)

totals = {}
for row in trips:
    totals[row["city"]] = totals.get(row["city"], 0) + row["km"]
print("Mumbai rows", len(mumbai))
print("farthest id", by_km[0]["id"])
print("km by city", totals)"""
    )
    b.md(
        """## Features, target, split, scale

The **target** is the thing you would predict (`returned`). **Features** are the inputs.

Split **before** you compute min/max or averages. If the validation rows influence scaling, you have leaked information.

This split is deterministic: sort by `id`, first 80% train, remainder validation. No random shuffle, so CI stays stable.

"""
        + mermaid(
            """
            flowchart TB
              rows[tidy rows] --> xy[features X and target y]
              xy --> splitFirst[split by id]
              splitFirst --> train[train]
              splitFirst --> valid[valid]
              train --> fit[fit min-max on train]
              fit --> scaleT[scale train]
              fit --> scaleV[scale valid]
            """,
            "Split first, then fit scaling on train only",
        )
        + """

"""
        + mermaid(
            """
            flowchart LR
              wrong[scale all rows first] --> leak[validation leaked]
              right[split first] --> noLeak[train-only bounds]
            """,
            "Scaling before the split lets validation rows influence train",
        )
    )
    b.code(
        """def split_rows(rows, fraction=0.8):
    ordered = sorted(rows, key=lambda row: row["id"])
    cut = int(len(ordered) * fraction)
    if cut == 0 or cut == len(ordered):
        raise ValueError("split would leave an empty side")
    return ordered[:cut], ordered[cut:]


def min_max_fit(rows, columns):
    stats = {}
    for column in columns:
        values = [row[column] for row in rows]
        stats[column] = {"min": min(values), "max": max(values)}
    return stats


def min_max_transform(rows, stats):
    scaled = []
    for row in rows:
        item = dict(row)
        for column, bounds in stats.items():
            span = bounds["max"] - bounds["min"]
            item[column] = 0.0 if span == 0 else (row[column] - bounds["min"]) / span
        scaled.append(item)
    return scaled

feature_cols = ["hours", "km"]
train, valid = split_rows(trips)
stats = min_max_fit(train, feature_cols)
train_scaled = min_max_transform(train, stats)
valid_scaled = min_max_transform(valid, stats)
print("train ids", [row["id"] for row in train])
print("valid ids", [row["id"] for row in valid])
print("train-only scaler", stats)

leaky_max = max(row["km"] for row in trips)
train_max = stats["km"]["max"]
print("km max on all rows", leaky_max)
print("km max on train only", train_max)
print("leaking would shrink train values because the 18 km row sits in validation")"""
    )
    b.md("## Practice 06.1")
    b.md("Return only rows whose `hours` is at least 2.")
    b.code(
        """# Practice 06.1
long_enough = [row for row in trips if row["hours"] >= 2]
print(long_enough)

# Check 06.1
assert [row["id"] for row in long_enough] == [1, 5, 6]
print("Practice 06.1 passed.")"""
    )
    b.md(hint("06.1", "A list comprehension with `if row[\"hours\"] >= 2`."))
    b.md("## Practice 06.2")
    b.md("Compute mean `km` grouped by `city`.")
    b.code(
        """# Practice 06.2
sums = {}
counts = {}
for row in trips:
    city = row["city"]
    sums[city] = sums.get(city, 0.0) + row["km"]
    counts[city] = counts.get(city, 0) + 1
mean_km = {city: sums[city] / counts[city] for city in sums}
print(mean_km)

# Check 06.2
assert abs(mean_km["Mumbai"] - 10.0) < 1e-9
print("Practice 06.2 passed.")"""
    )
    b.md(hint("06.2", "Keep a running sum and a count per city, then divide."))
    b.md("## Practice 06.3")
    b.md("Build `X` (list of `[hours, km]`) and `y` (list of `returned`) from `trips`.")
    b.code(
        """# Practice 06.3
X = [[row["hours"], row["km"]] for row in trips]
y = [row["returned"] for row in trips]
print(X, y)

# Check 06.3
assert X[0] == [2.0, 8.0]
assert y == [True, False, True, False]
print("Practice 06.3 passed.")"""
    )
    b.md(hint("06.3", "Two comprehensions: one nested list for features, one list for the boolean target."))
    b.md(
        """## Common mistakes

- Scaling the full dataset, then splitting. Fit on train only.
- Leaving the target inside `X`.
- Using `set` iteration order when you need a stable split.
"""
    )
    b.md("## Recap")
    b.md("Cleaning, splitting, and scaling are Python problems first. Libraries automate the same steps; they do not replace them.")
    b.md(
        understanding(
            [
                (
                    "When should you compute min/max for scaling?",
                    "On the training rows only, then apply those bounds to validation.",
                ),
                (
                    "Where does the target column belong?",
                    "Out of X, stored separately as y. If it stays in X, a model can cheat.",
                ),
            ]
        )
    )
    b.md("## Solutions")
    b.md(solution_block("06.1", "long_enough = [row for row in trips if row[\"hours\"] >= 2]"))
    b.md(
        solution_block(
            "06.2",
            "sums, counts = {}, {}\nfor row in trips:\n    sums[row['city']] = sums.get(row['city'], 0.0) + row['km']\n    counts[row['city']] = counts.get(row['city'], 0) + 1\nmean_km = {city: sums[city] / counts[city] for city in sums}",
        )
    )
    b.md(
        solution_block(
            "06.3",
            'X = [[row["hours"], row["km"]] for row in trips]\ny = [row["returned"] for row in trips]',
        )
    )
    b.md(nav(fn))
    return b.cells


def build_07() -> list[dict]:
    fn = SEQUENCE[7][0]
    b = Builder("07")
    b.md(
        header(
            fn,
            SEQUENCE[7][1],
            60,
            "Notebooks 00–06",
            [
                "Parse a dirty CSV of bike-share trips",
                "Drop missing, malformed, and duplicate rows and report counts",
                "Derive features and a data-quality summary",
                "Split, scale with train-only bounds, and assert invariants",
            ],
        )
    )
    b.md(
        """## Capstone: prepare a bike-share table

You are given raw trip logs as CSV text (no download). Produce a training table a later ML library could consume.

**Done means all checks in this notebook print `passed`.** You will not fit a model.

Suggested steps:

1. Parse CSV to dictionaries.
2. Validate and convert types.
3. Remove duplicates, missing required values, and malformed numbers.
4. Derive `km_per_hour` and `age_group`.
5. Summarize quality.
6. Drop the target from features.
7. Deterministic 80/20 split by `id`.
8. Min-max scale `hours`, `km`, and `km_per_hour` using **train** mins and maxes only.

What should happen to each raw row:

| id | Problem | Fate |
|---|---|---|
| 1 | clean | keep |
| 2 | blank `hours` | drop missing |
| 3 | clean | keep |
| 4 | appears twice | keep first, drop duplicate |
| 5 | `hours` is `abc` | drop invalid |
| 6 | clean | keep |
| 7 | clean (teen rider) | keep |
| 8 | clean | keep |

Nine data rows in, six useful rows out. Sorted ids `[1, 3, 4, 6, 7, 8]`; 80% train is the first four.

"""
        + mermaid(
            """
            flowchart TB
              csvText[CSV text] --> parseRows[parse]
              parseRows --> dropBad["drop missing, invalid, duplicate"]
              dropBad --> derive[derive km_per_hour and age_group]
              derive --> splitData["split 80/20 by id"]
              splitData --> scale[train-only min-max]
              scale --> bundle[JSON bundle]
            """,
            "Capstone pipeline: parse, clean, derive, split, scale, export",
        )
        + """

"""
        + mermaid(
            """
            flowchart TB
              nine[9 data rows] --> keep["keep 1, 3, 4, 6, 7, 8"]
              nine --> miss["drop id 2 missing"]
              nine --> dup["drop second id 4"]
              nine --> inv["drop id 5 invalid"]
            """,
            "Nine rows in, six kept, three dropped for distinct reasons",
        )
    )
    b.md("## The raw file")
    b.code(
        """from pathlib import Path
import csv
import io

RAW_CSV = \"\"\"id,city,hours,km,rider_age,pass_type,returned
1,Mumbai,2,8.5,24,annual,yes
2,Pune,,3.0,31,casual,yes
3,Mumbai,1,4.0,19,annual,no
4,Bengaluru,3,12.0,41,annual,yes
4,Bengaluru,3,12.0,41,annual,yes
5,Mumbai,abc,5.0,22,casual,no
6,Pune,2.5,6.0,28,annual,yes
7,Bengaluru,0.5,1.2,17,casual,yes
8,Mumbai,4,18.0,35,annual,no
\"\"\"

DATA_DIR = Path.cwd() / "_course_data"
DATA_DIR.mkdir(exist_ok=True)
raw_path = DATA_DIR / "bike_trips_raw.csv"
raw_path.write_text(RAW_CSV, encoding="utf-8")
print(raw_path.read_text(encoding="utf-8"))"""
    )
    b.md("## Practice 07.1 — parse, clean, derive")
    b.code(
        """# Practice 07.1
def parse_float(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def age_group(age):
    if age < 18:
        return "teen"
    if age < 35:
        return "adult"
    return "older"


def prepare(csv_text):
    report = {
        "rows_in": 0,
        "dropped_missing": 0,
        "dropped_invalid": 0,
        "dropped_duplicate": 0,
        "rows_out": 0,
    }
    cleaned = []
    seen = set()
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    for row in reader:
        report["rows_in"] += 1
        if row["id"] in seen:
            report["dropped_duplicate"] += 1
            continue
        hours = parse_float(row["hours"])
        km = parse_float(row["km"])
        age = parse_float(row["rider_age"])
        missing = row["hours"] in ("", None) or row["km"] in ("", None) or row["rider_age"] in ("", None)
        if hours is None or km is None or age is None:
            if missing:
                report["dropped_missing"] += 1
            else:
                report["dropped_invalid"] += 1
            continue
        if hours <= 0:
            report["dropped_invalid"] += 1
            continue
        seen.add(row["id"])
        cleaned.append(
            {
                "id": int(row["id"]),
                "city": row["city"],
                "hours": hours,
                "km": km,
                "rider_age": int(age),
                "pass_type": row["pass_type"],
                "returned": row["returned"] == "yes",
                "km_per_hour": km / hours,
                "age_group": age_group(int(age)),
            }
        )
    report["rows_out"] = len(cleaned)
    return cleaned, report

trips, quality = prepare(RAW_CSV)
print("quality:", quality)
print("kept ids:", [row["id"] for row in trips])
print(
    f"{quality['rows_in']} in → "
    f"missing {quality['dropped_missing']}, "
    f"invalid {quality['dropped_invalid']}, "
    f"duplicate {quality['dropped_duplicate']} → "
    f"{quality['rows_out']} out"
)

# Check 07.1
assert quality["rows_in"] == 9
assert quality["dropped_duplicate"] == 1
assert quality["dropped_missing"] == 1
assert quality["dropped_invalid"] == 1
assert quality["rows_out"] == 6
assert {row["id"] for row in trips} == {1, 3, 4, 6, 7, 8}
print("Practice 07.1 passed.")"""
    )
    b.md(
        hint(
            "07.1",
            "Nine data rows. Row 2 has blank hours (missing). The second row 4 is a duplicate. Row 5 has `abc` hours (invalid). Keep ids 1, 3, 4, 6, 7, 8.",
        )
    )
    b.md("## Practice 07.2 — split, separate target, scale")
    b.code(
        """# Practice 07.2
FEATURE_COLUMNS = ["hours", "km", "km_per_hour"]
TARGET = "returned"


def split_rows(rows, fraction=0.8):
    ordered = sorted(rows, key=lambda row: row["id"])
    cut = int(len(ordered) * fraction)
    return ordered[:cut], ordered[cut:]


def fit_scaler(rows, columns):
    return {
        column: {
            "min": min(row[column] for row in rows),
            "max": max(row[column] for row in rows),
        }
        for column in columns
    }


def apply_scaler(rows, stats):
    output = []
    for row in rows:
        item = dict(row)
        for column, bounds in stats.items():
            span = bounds["max"] - bounds["min"]
            item[column] = 0.0 if span == 0 else (row[column] - bounds["min"]) / span
        output.append(item)
    return output


def features_and_target(rows):
    X = [[row[column] for column in FEATURE_COLUMNS] for row in rows]
    y = [row[TARGET] for row in rows]
    return X, y

train, valid = split_rows(trips, 0.8)
scaler = fit_scaler(train, FEATURE_COLUMNS)
train_scaled = apply_scaler(train, scaler)
valid_scaled = apply_scaler(valid, scaler)
X_train, y_train = features_and_target(train_scaled)
X_valid, y_valid = features_and_target(valid_scaled)

print("train", [row["id"] for row in train])
print("valid", [row["id"] for row in valid])
print("scaler", scaler)

# Check 07.2
assert [row["id"] for row in train] == [1, 3, 4, 6]
assert [row["id"] for row in valid] == [7, 8]
assert TARGET not in FEATURE_COLUMNS
assert len(X_train[0]) == 3
for column, bounds in scaler.items():
    train_values = [row[column] for row in train_scaled]
    assert min(train_values) >= 0 - 1e-9
    assert max(train_values) <= 1 + 1e-9
print("Practice 07.2 passed.")"""
    )
    b.md(
        hint(
            "07.2",
            "Sort by `id`. With 6 rows, `int(6 * 0.8)` is 4, so validation is the last two ids. Fit mins and maxes on train only.",
        )
    )
    b.md("## Practice 07.3 — export and invariants")
    b.code(
        """# Practice 07.3
import json

export_path = DATA_DIR / "bike_trips_prepared.json"
bundle = {
    "quality": quality,
    "feature_columns": FEATURE_COLUMNS,
    "target": TARGET,
    "train_ids": [row["id"] for row in train],
    "valid_ids": [row["id"] for row in valid],
    "scaler": scaler,
}
export_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
saved = json.loads(export_path.read_text(encoding="utf-8"))

# Check 07.3
assert saved["train_ids"] == [1, 3, 4, 6]
assert saved["valid_ids"] == [7, 8]
assert set(saved["train_ids"]).isdisjoint(saved["valid_ids"])
assert saved["quality"]["rows_out"] == 6
print("Wrote", export_path)
print("Practice 07.3 passed.")"""
    )
    b.md(hint("07.3", "Dump a JSON object with the quality report, ids, and scaler. Then assert train and valid ids do not overlap."))
    b.md(
        """## You are ready for ML libraries when

- You can load rows, clean them, and say what each column means.
- You can keep the target out of the feature matrix.
- You can split first and compute statistics on train only.
- You can check those promises with `assert`.

**Next:** NumPy arrays, pandas DataFrames, a plotting library, then scikit-learn's `Pipeline` and `train_test_split`. The verbs stay the same."""
    )
    b.md(
        """## Common mistakes

- Keeping duplicate id 4 or the blank-hours row.
- Scaling before splitting.
- Putting `returned` inside `X`.
"""
    )
    b.md("## Recap")
    b.md("A usable ML dataset is a software product: parsed, typed, documented, split, and checked. You built that product in Python.")
    b.md(
        understanding(
            [
                (
                    "Does this capstone ask you to train a model?",
                    "No. Stop after a clean, split, scaled table. Libraries come next.",
                ),
                (
                    "pandas dropna + sklearn train_test_split is closest to which step here?",
                    "Cleaning rows, then splitting before you scale.",
                ),
            ]
        )
    )
    b.md("## Solutions")
    b.md(
        solution_block(
            "07.1",
            """# Skip duplicate ids, blank hours, and non-numeric hours.
# Keep 1, 3, 4, 6, 7, 8. Derive km_per_hour = km / hours.
cleaned, report = prepare(RAW_CSV)
assert report["rows_out"] == 6""",
        )
    )
    b.md(
        solution_block(
            "07.2",
            """train, valid = split_rows(trips, 0.8)
# ids [1, 3, 4, 6] then [7, 8]
scaler = fit_scaler(train, FEATURE_COLUMNS)
X_train, y_train = features_and_target(apply_scaler(train, scaler))""",
        )
    )
    b.md(
        solution_block(
            "07.3",
            """bundle = {
    "quality": quality,
    "feature_columns": FEATURE_COLUMNS,
    "target": TARGET,
    "train_ids": [row["id"] for row in train],
    "valid_ids": [row["id"] for row in valid],
    "scaler": scaler,
}
export_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")""",
        )
    )
    b.md(nav(fn))
    return b.cells


BUILDERS = {
    SEQUENCE[0][0]: build_00,
    SEQUENCE[1][0]: build_01,
    SEQUENCE[2][0]: build_02,
    SEQUENCE[3][0]: build_03,
    SEQUENCE[4][0]: build_04,
    SEQUENCE[5][0]: build_05,
    SEQUENCE[6][0]: build_06,
    SEQUENCE[7][0]: build_07,
}


def main() -> None:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    for filename, _title in SEQUENCE:
        path = NOTEBOOK_DIR / filename
        write_notebook(path, BUILDERS[filename]())
        print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
