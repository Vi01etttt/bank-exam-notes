"""用内存SQLite核对笔记中的查询结果；不连接MySQL或业务库。"""
from pathlib import Path
import platform
import re
import sqlite3


def main():
    folder = Path(__file__).resolve().parent
    note = (folder.parent / "03_SQL题目与实操.md").read_text(encoding="utf-8")
    expected = {
        "01": [[(103, 15000), (104, 15000), (106, 15000)]],
        "02": [[(4, 2, 2)]],
        "03": [[(2, 30000)]],
        "04": [[(1, "张三", 2, 15000), (2, "李四", 2, 30000),
                (3, "王五", 1, 15000), (4, "赵六", 0, 0)]],
        "05": [[(4, "赵六")]],
        "06": [[], [(2,), (3,), (4,)]],
        "07": [[("安全", 106, 15000, 1), ("研发", 103, 15000, 1),
                ("研发", 104, 15000, 1), ("研发", 101, 10000, 2)]],
        "08": [[(10000,)]],
        "09": [[(30000,)]],
        "10": [[(25000,)], [(1, 15000, 2), (2, 30000, 1),
                              (3, 15000, 0), (4, 0, 0)]],
        "11": [[("安全", 2, 1, 0, 1), ("研发", 5, 4, 1, 0)]],
        "12": [[(1,), (2,), (3,)], [(1,), (1,), (1,), (2,), (2,), (3,)]],
        "13": [[(2, "李四", 30000, 22500), (3, "王五", 15000, 7500)]],
        "14": [[(1, 101, 10000), (1, 107, 15000), (2, 103, 15000),
                (2, 104, 30000), (3, 106, 15000)]],
        "15": [[(1, 107, 5000), (2, 104, 15000), (3, 106, 15000), (4, None, None)]],
        "16": [[(101, None, None), (107, 10000, -5000), (103, None, None),
                (104, 15000, 0), (106, None, None)]],
        "17": [[(2, "李四")]],
        "18": [[(106, 15000), (101, 10000)]],
    }
    sections = re.findall(r"^### SQL(\d{2})[^\n]*\n(.*?)(?=^### |^## |\Z)",
                          note, re.MULTILINE | re.DOTALL)
    if [key for key, _ in sections] != list(expected):
        raise AssertionError("SQL题目编号缺失、重复或顺序变化，请核对笔记。")
    report = []
    checked = 0
    with sqlite3.connect(":memory:") as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript((folder / "SQL练习数据.sql").read_text(encoding="utf-8"))
        for key, body in sections:
            queries = re.findall(r"```sql\s*\n(.*?)```", body, re.DOTALL)
            if len(queries) != len(expected[key]):
                raise AssertionError(f"SQL{key}查询数量与预期不符。")
            for index, (query, wanted) in enumerate(zip(queries, expected[key]), start=1):
                rows = connection.execute(query).fetchall()
                if rows != wanted:
                    raise AssertionError(f"SQL{key}-{index}: 实际 {rows!r}，预期 {wanted!r}")
                checked += 1
                report.append(f"| SQL{key}-{index} | 通过 | {len(rows)} |")
    content = ("# SQL例题验证记录\n\n"
               "笔记建档与首次验证日期：2026-10-02；18题扩充验证日期：2026-10-03。本文件由检查脚本生成；再次运行会更新环境与结果。\n\n"
               f"环境：Python {platform.python_version()}，SQLite {sqlite3.sqlite_version}。\n\n"
               f"结果：{len(expected)}题共{checked}段查询全部与预期输出一致，包含两段故意错误的查询。\n\n"
               "验证范围：练习数据导入、查询执行、输出内容和排序。跨部门排序采用SQLite默认规则。\n\n"
               "限制：本次未连接MySQL；结果不证明MySQL事务隔离、锁、执行计划或生产性能。\n\n"
               "| 查询 | 结果 | 返回行数 |\n|---|---|---:|\n"
               + "\n".join(report) + "\n")
    (folder / "SQL验证记录.md").write_text(content, encoding="utf-8")
    print(f"通过：{len(expected)}题 / {checked}段查询。环境SQLite {sqlite3.sqlite_version}，未连接MySQL。")


if __name__ == "__main__":
    main()
