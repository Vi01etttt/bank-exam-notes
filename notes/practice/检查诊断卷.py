"""在内存中核验诊断卷的SQL、数值和逻辑，不连接业务数据库。"""
from pathlib import Path
import json
import re
import sqlite3
from fractions import Fraction

notes = Path(__file__).resolve().parents[1]
question_text = (notes / '17_秋招基础诊断卷.md').read_text(encoding='utf-8')
answer_text = (notes / '18_诊断卷答案与补学路线.md').read_text(encoding='utf-8')

def question(n):
    m = re.search(rf'### DIAG-{n:02d}[^\n]*\n(.*?)(?=\n### DIAG-|\n## 二 作答纸)', question_text, re.S)
    assert m, n
    return m[1]

def answer(n):
    m = re.search(rf'### DIAG-{n:02d}\s+答案([A-D]+)[。，]', answer_text)
    assert m, n
    return m[1]

def options(n):
    return dict(re.findall(r'^- ([A-D])\. (.+)$', question(n), re.M))

def selected(n):
    return options(n)[answer(n)]

db = sqlite3.connect(':memory:')
db.executescript('''
CREATE TABLE users(id INTEGER PRIMARY KEY);
CREATE TABLE orders(id INTEGER PRIMARY KEY, user_id INTEGER, status TEXT);
INSERT INTO users VALUES(1),(2);
INSERT INTO orders VALUES(11,1,'PAID'),(12,1,'PENDING');
''')
q14 = re.search(r'```sql\n(.*?)```', question(14), re.S)[1]
actual = db.execute(q14).fetchall()
assert actual == [(1, 2, 2), (2, 1, 0)], actual
assert '(1,2,2)' in selected(14) and '(2,1,0)' in selected(14)

# Include a user with only an unpaid order to distinguish ON from WHERE repairs.
db.executescript("INSERT INTO users VALUES(3); INSERT INTO orders VALUES(13,3,'PENDING');")
valid=[]
observed={}
for label, option in options(15).items():
    fragment=option.strip('`')
    rows=db.execute('SELECT u.id,o.id FROM users u '+fragment+' ORDER BY u.id,o.id').fetchall()
    observed[label]=rows
    if rows == [(1,11),(2,None),(3,None)]:
        valid.append(label)
assert valid == [answer(15)], (valid, answer(15), observed)
wrong_repair=db.execute("SELECT u.id,o.id FROM users u LEFT JOIN orders o ON o.user_id=u.id WHERE o.status='PAID' OR o.id IS NULL ORDER BY u.id").fetchall()
assert wrong_repair == [(1,11),(2,None)]

q16 = re.search(r'`(SELECT 1 WHERE .*?;)`', question(16))[1]
assert db.execute(q16).fetchall() == []
assert '不返回行' in selected(16)
db.close()

nodes,edges=map(int,re.search(r'有(\d+)个节点、(\d+)条边',question(9)).groups())
assert int(selected(9)) == edges-nodes+2

sequence=list(map(int,re.search(r'依次访问`([^`]+)`',question(19))[1].split(',')))
capacity=int(re.search(r'可容纳(\d+)个页面',question(19))[1])
lru=[]; faults=0; trace=[]
for page in sequence:
    hit=page in lru
    if hit:
        lru.remove(page)
    else:
        faults+=1
        if len(lru)==capacity:
            lru.pop()
    lru.insert(0,page)
    trace.append((page,list(lru),not hit,faults))
assert faults==int(selected(19))==5

last_total,last_online,current_total,current_online=map(int,re.search(r'去年业务总量(\d+)万笔，其中线上(\d+)万笔；今年总量(\d+)万笔，其中线上(\d+)万笔',question(22)).groups())
delta=(Fraction(current_online,current_total)-Fraction(last_online,last_total))*100
assert delta==10 and selected(22)=='10个百分点'

# Enumerate all truth assignments satisfying P => Q and not Q.
models=[(p,q) for p in [False,True] for q in [False,True] if (not p or q) and not q]
assert models==[(False,False)]
assert selected(23)=='该申请没有通过审核'

ids=re.findall(r'^### DIAG-(\d{2})',question_text,re.M)
assert ids==[f'{n:02d}' for n in range(1,25)]
for n in range(1,25):
    assert set(options(n))==set('ABCD')
    assert set(answer(n)) <= set('ABCD')
    if n!=12:
        assert len(answer(n))==1
table_pairs=dict(re.findall(r'\| (\d{2}) \| ([A-D]+) (?=\|)',answer_text))
assert len(table_pairs)==24
assert all(table_pairs[f'{n:02d}']==answer(n) for n in range(1,25))
print(json.dumps({'status':'passed','sqlite_version':sqlite3.sqlite_version,'questions':len(ids),'checks':['SQL14外连接计数','SQL15四个选项及错误修补反例','SQL16三值逻辑','环形复杂度数值','LRU逐次轨迹','百分点精确分数计算','命题真值枚举','题号及速查答案一致性'],'java_executed':False,'lru_trace':trace},ensure_ascii=False,indent=2))
