"""执行Python读码笔记中的10段独立代码，核对教学答案。"""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import platform
import re


def main():
    folder = Path(__file__).resolve().parent
    content = (folder.parent / "10_Python语言与读码.md").read_text(encoding="utf-8")
    expected = {
        "01": "True False True\n[[1, 9], [2]] [[1], [2]]\n",
        "02": "[1]\n[1, 2]\n[3]\n[1, 2, 4]\n",
        "03": "[2, 2, 2]\n[0, 1, 2]\n",
        "04": "[[9, 0], [9, 0]]\n[[9, 0], [0, 0]]\n",
        "06": "0\n[1, 4]\n[]\n",
        "07": "2\n",
        "08": "['local']\n['shared']\n",
        "09": "['乙', '丙', '甲']\n['甲', '乙', '丙']\n",
        "10": "-5\nFalse\nTrue\n2 4\n",
        "11": "60\n3\n",
    }
    sections = dict(re.findall(r"^### PY(\d{2})[^\n]*\n(.*?)(?=^### |^## |\Z)",
                               content, re.MULTILINE | re.DOTALL))
    if set(sections) != {f"{n:02d}" for n in range(1, 13)}:
        raise AssertionError("题号不完整，请核对12题。")
    for key, wanted in expected.items():
        blocks = re.findall(r"```python\s*\n(.*?)```", sections[key], re.DOTALL)
        if len(blocks) != 1:
            raise AssertionError(f"PY{key}应有一段独立Python代码。")
        buffer = StringIO()
        with redirect_stdout(buffer):
            exec(compile(blocks[0], f"PY{key}", "exec"), {})
        if buffer.getvalue() != wanted:
            raise AssertionError(f"PY{key}: 实际 {buffer.getvalue()!r}, 预期 {wanted!r}")
    print(f"通过：10段Python读码代码，Python {platform.python_version()}。")


if __name__ == "__main__":
    main()
