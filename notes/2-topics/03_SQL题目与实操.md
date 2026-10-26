# SQL知识讲解与题目实操

建档日期：2026-10-02；扩充日期：2026-10-03。先学会把题意拆成“查哪些行、怎样关联、按什么分组、最终保留什么”，再写语句。本文面向 MySQL 8.0 和 8.4，窗口函数题需要 MySQL 8.0 或更高版本。18题均为原创练习，数据是虚构的报销记录；SQL01至SQL10为基础，SQL11至SQL18为进阶。

[返回学习导航](../00_学习导航.md) · [数据库原理](01_数据库原理.md) · [综合自测](../4-mock-exams/03_综合自测.md)

## 一 总体知识讲解

### 查询的逻辑顺序

理解一条查询时，可以按 `FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT` 推演；窗口计算发生在分组和 HAVING 后、最终排序与 LIMIT 前。这是理解结果的逻辑模型，数据库执行计划可能重排实际操作。

`WHERE` 筛选分组前的行，`HAVING` 筛选聚合后的组。例如“只统计已批准记录”用 WHERE；“只显示总金额超过200元的人”用 HAVING。写查询时先决定结果粒度：一行是一笔记录、一个用户，还是一个部门。粒度不清楚，JOIN 后就容易重复统计。

| 要求 | 常用写法 | 为什么 |
|---|---|---|
| 只要匹配成功的两表行 | INNER JOIN | 没匹配的行被排除 |
| 保留所有用户，包括没有报销的人 | LEFT JOIN | 没匹配时右表列补 NULL |
| 问某条关联记录是否存在 | EXISTS | 关注存在性，避免为了判断存在而扩大行数 |
| 对同一用户汇总 | GROUP BY user_id | 多条明细压成一个组 |
| 保留明细同时计算排名 | 窗口函数 OVER | 给每行加计算结果，不把明细压成一行 |
| 去掉相同结果行 | DISTINCT | 按选择出的列组合去重，不是修复任意关联错误 |

### NULL和计数

NULL 表示未知或缺失，不等于0，也不等于空字符串。`NULL = NULL` 不为真，判断是否缺失要用 `IS NULL`。WHERE 只保留条件为 TRUE 的行，FALSE 和 UNKNOWN 都不保留。

`COUNT(*)` 数行；`COUNT(列)` 数该列非 NULL 的行；`COUNT(DISTINCT 列)` 数不同的非 NULL 值。SUM、AVG 通常忽略 NULL；无输入行时 SUM 返回 NULL，可用 `COALESCE(SUM(...), 0)` 按业务需要转成0。LEFT JOIN 没有匹配时仍有一行，所以统计右表记录应数右表非空主键。见 [MySQL聚合函数](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html) 与 [NULL规则](https://dev.mysql.com/doc/refman/8.4/en/working-with-null.html)。

### 关联与排名的边界

LEFT JOIN 中，把右表状态限制放在 ON，表示“只关联符合状态的记录，但保留所有左表行”；把它放在 WHERE，未匹配行的 NULL 可能被过滤，结果就不再保留所有用户。见 [MySQL JOIN说明](https://dev.mysql.com/doc/refman/8.4/en/join.html)。

`ROW_NUMBER` 每行一个序号；`RANK` 并列相同、下一名跳号；`DENSE_RANK` 并列相同、下一名不跳号。值 `100、100、80` 对应排名分别为 `1、2、3`，`1、1、3`，`1、1、2`。ROW_NUMBER 想在相同金额下稳定选出某一行，排序需加唯一键；给 DENSE_RANK 加唯一键则会破坏金额并列。见 [MySQL窗口函数](https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html)。

分组查询中，SELECT 的非聚合列应放入 GROUP BY，或在数据库允许的明确函数依赖下使用；本笔记直接列出所有非聚合列，避免依赖宽松分组设置。分页必须有确定排序，相同金额时加主键；没有 ORDER BY 就不承诺结果顺序。

### 做题的五步

1. 圈出“所有、没有、至少、每组、前几名、包括并列”等词。
2. 定义一行结果代表什么，并选主表。
3. 列出过滤条件，分清行条件和组条件。
4. 写关联和聚合，手算一两个用户检查是否重复。
5. 检查 NULL、零条记录、并列、日期边界与排序。

## 二 统一练习数据

用 [SQL练习数据.sql](../6-resources/practice/SQL练习数据.sql) 初始化一个新练习库。金额统一用整数“分”；`approved` 为已批准，`pending` 为待审批，`rejected` 为已拒绝。日期表示提交日，本文不含时区转换。

| 用户编号 | 姓名 | 部门 | email是否为空 |
|---|---|---|---|
| 1 | 张三 | 研发 | 否 |
| 2 | 李四 | 研发 | 是 |
| 3 | 王五 | 安全 | 否 |
| 4 | 赵六 | 安全 | 是 |

| 报销编号 | 用户编号 | 金额分 | 状态 | 提交日 |
|---|---|---:|---|---|
| 101 | 1 | 10000 | approved | 2026-10-01 |
| 102 | 1 | 20000 | pending | 2026-10-02 |
| 103 | 2 | 15000 | approved | 2026-10-01 |
| 104 | 2 | 15000 | approved | 2026-10-03 |
| 105 | 3 | 30000 | rejected | 2026-10-02 |
| 106 | 3 | 15000 | approved | 2026-10-04 |
| 107 | 1 | 5000 | approved | 2026-10-05 |

审核记录：101有两条，103有一条，其他报销没有审核记录。审核表只是本题演示一对多关系，不能从它推导真实项目的审批状态。

## 三 十道题与解析

先遮住代码和答案，独立写语句，再手算结果。各题共用上面的初始数据，不修改数据。

### SQL01 筛选并稳定排序

**题目：** 查出已批准且金额至少15000分的报销，按金额降序、报销编号升序返回编号和金额。

**答案：**

```sql
SELECT expense_id, amount_cent
FROM exam_expenses
WHERE status = 'approved' AND amount_cent >= 15000
ORDER BY amount_cent DESC, expense_id ASC;
```

**结果：** `(103,15000)、(104,15000)、(106,15000)`。

**讲解：** AND 表示两个要求同时满足。105金额更大但被拒绝，102尚待审批，都应排除。三个入选金额相同，第二排序键确保顺序确定。

**易错点：** 把 AND 写成 OR，会把高金额但未批准的记录算进去。关联知识：条件筛选与多列排序。

### SQL02 COUNT的三种口径

**题目：** 统计用户总数、填了email的用户数、不同部门数。

```sql
SELECT COUNT(*) AS total_users,
       COUNT(email) AS users_with_email,
       COUNT(DISTINCT dept) AS dept_count
FROM exam_users;
```

**答案：** `(4,2,2)`。

**讲解：** 四行用户全部计入 COUNT(*)；两行email为 NULL 不计入 COUNT(email)；研发和安全各出现多次，DISTINCT后只剩两个部门。

**易错点：** `COUNT(email)` 不等于统计“email字段存在的行数”；表中每一行都有该列，计数看的是值。关联知识：NULL与聚合。

### SQL03 WHERE和HAVING

**题目：** 按用户统计已批准总额，仅返回总额至少20000分的用户编号和总额。

```sql
SELECT user_id, SUM(amount_cent) AS approved_cent
FROM exam_expenses
WHERE status = 'approved'
GROUP BY user_id
HAVING SUM(amount_cent) >= 20000
ORDER BY user_id;
```

**答案：** `(2,30000)`。

**讲解：** 先过滤状态，再按用户分组。用户1为10000+5000=15000，用户2为15000+15000=30000，用户3为15000，只有用户2达标。

**易错点：** `WHERE amount_cent >= 20000` 是筛单笔金额，会把两笔15000组成的合格总额漏掉。关联知识：分组前后条件。

### SQL04 保留没有报销的用户

**题目：** 返回全部用户的已批准笔数和总额，无记录者显示0。

```sql
SELECT u.user_id, u.user_name,
       COUNT(e.expense_id) AS approved_count,
       COALESCE(SUM(e.amount_cent), 0) AS approved_cent
FROM exam_users AS u
LEFT JOIN exam_expenses AS e
  ON e.user_id = u.user_id AND e.status = 'approved'
GROUP BY u.user_id, u.user_name
ORDER BY u.user_id;
```

**答案：** `(1,张三,2,15000)、(2,李四,2,30000)、(3,王五,1,15000)、(4,赵六,0,0)`。

**讲解：** 用户表是主表，状态条件放 ON。用户4获得右表全 NULL 的补位行，COUNT(e.expense_id)=0，SUM为 NULL 后转成0。

**易错点：** COUNT(*) 会把用户4的补位行数成1；`WHERE e.status='approved'` 会过滤用户4。关联知识：外连接、NULL、计数。

### SQL05 查询从未提交过报销的用户

**题目：** 返回没有任何报销记录的用户编号和姓名，不论报销状态。

```sql
SELECT u.user_id, u.user_name
FROM exam_users AS u
WHERE NOT EXISTS (
  SELECT 1 FROM exam_expenses AS e WHERE e.user_id = u.user_id
)
ORDER BY u.user_id;
```

**答案：** `(4,赵六)`。

**讲解：** 对每个用户判断是否存在至少一条报销。用户1、2、3均存在，NOT EXISTS排除他们。也可LEFT JOIN后用 `WHERE e.expense_id IS NULL`，这里主键不允许NULL，因此能表示没匹配。

**易错点：** “没有已批准报销”和“没有任何报销”条件不同；本题不应筛approved。关联知识：相关子查询和反关联。

### SQL06 NOT IN遇到NULL

**题目：** 假设排除列表意外包含 `(1,NULL)`，下列查询能否返回用户2、3、4？

```sql
SELECT user_id FROM exam_users
WHERE user_id NOT IN (1, NULL)
ORDER BY user_id;
```

**答案：** 返回零行。以用户2为例，条件相当于 `2<>1 AND 2<>NULL`，为 TRUE AND UNKNOWN，仍是 UNKNOWN，WHERE不保留。

**改写：** 用NOT EXISTS明确忽略无法匹配的NULL项。

```sql
WITH blocked AS (SELECT 1 AS user_id UNION ALL SELECT NULL)
SELECT u.user_id FROM exam_users AS u
WHERE NOT EXISTS (
  SELECT 1 FROM blocked AS b WHERE b.user_id = u.user_id
)
ORDER BY u.user_id;
```

**结果：** `(2)、(3)、(4)`。

**易错点：** 不能背成“NOT IN永远错误”；列表保证非NULL时没有本题问题。关联知识：三值逻辑。有关比较含NULL的行为见 [MySQL比较运算符](https://dev.mysql.com/doc/refman/8.4/en/comparison-operators.html)。

### SQL07 每部门前两档金额且保留并列

**题目：** 在已批准报销中，找出各部门金额最高的两个不同档位，保留同档位全部记录。返回部门、编号、金额和档位。

```sql
WITH ranked AS (
  SELECT u.dept, e.expense_id, e.amount_cent,
         DENSE_RANK() OVER (
           PARTITION BY u.dept ORDER BY e.amount_cent DESC
         ) AS amount_rank
  FROM exam_expenses AS e
  JOIN exam_users AS u ON u.user_id = e.user_id
  WHERE e.status = 'approved'
)
SELECT dept, expense_id, amount_cent, amount_rank
FROM ranked
WHERE amount_rank <= 2
ORDER BY dept, amount_rank, expense_id;
```

**答案：** 研发：103和104均为15000分第1档，101为10000分第2档；安全：106为15000分第1档。跨部门显示顺序由数据库排序规则决定，不影响部门内档位。

**讲解：** PARTITION BY按部门各算一份排名，DENSE_RANK按不同金额连续编号。外层WHERE筛选已算出的排名，不能在同一层WHERE直接引用窗口结果。

**易错点：** ROW_NUMBER只取两行，会漏掉研发第2档；RANK给10000编号3，也不符合“前两档”。关联知识：窗口与聚合的区别。

### SQL08 第二高的不同金额

**题目：** 求全体已批准报销中第二高的不同金额。

```sql
SELECT MAX(amount_cent) AS second_amount_cent
FROM exam_expenses
WHERE status = 'approved'
  AND amount_cent < (
    SELECT MAX(amount_cent) FROM exam_expenses WHERE status = 'approved'
  );
```

**答案：** `(10000)`。已批准的不同金额为15000、10000、5000。

**讲解：** 内层求最高档15000，外层只取更低金额，再求MAX得到10000。若不足两档，聚合返回一行NULL，符合“第二档不存在”。

**易错点：** 排序后 `LIMIT 1 OFFSET 1` 只取第二行，可能仍是15000；应先去重或按不同档位排名。关联知识：子查询、去重与并列。

### SQL09 日期区间的半开写法

**题目：** 统计10月2日至10月4日提交的已批准总额，包含这三天。

```sql
SELECT COALESCE(SUM(amount_cent), 0) AS approved_cent
FROM exam_expenses
WHERE status = 'approved'
  AND submitted_at >= '2026-10-02'
  AND submitted_at < '2026-10-05';
```

**答案：** `(30000)`，104与106各15000。

**讲解：** “下界包含、下一个日期不包含”叫半开区间。当前DATE列也可用BETWEEN包含两端；以后若换成DATETIME，同样的半开思路仍能覆盖10月4日全天。

**易错点：** DATETIME写 `<= '2026-10-04'` 往往只覆盖该日零点。日期函数套列还可能影响索引选择，优化时用EXPLAIN确认。关联知识：边界测试与范围条件。

### SQL10 一对多关联导致重复求和

**题目：** 下列查询为什么把张三的已批准总额算为25000？怎样同时显示每人的已批准总额和这些报销的审核记录数，包括没有报销的用户？

```sql
SELECT SUM(e.amount_cent) AS wrong_cent
FROM exam_expenses AS e
LEFT JOIN exam_reviews AS r ON r.expense_id = e.expense_id
WHERE e.user_id = 1 AND e.status = 'approved';
```

**答案与推导：** 101对应两条审核，因此10000被相加两次；107没审核但外连接保留一行5000，总计25000。张三实际总额是15000。

**正确写法：** 先把审核表压成每笔报销一行，再关联用户和报销。

```sql
WITH review_counts AS (
  SELECT expense_id, COUNT(*) AS review_count
  FROM exam_reviews GROUP BY expense_id
)
SELECT u.user_id,
       COALESCE(SUM(e.amount_cent), 0) AS approved_cent,
       COALESCE(SUM(rc.review_count), 0) AS review_count
FROM exam_users AS u
LEFT JOIN exam_expenses AS e
  ON e.user_id = u.user_id AND e.status = 'approved'
LEFT JOIN review_counts AS rc ON rc.expense_id = e.expense_id
GROUP BY u.user_id
ORDER BY u.user_id;
```

**结果：** `(1,15000,2)、(2,30000,1)、(3,15000,0)、(4,0,0)`。

**易错点：** `SUM(DISTINCT amount_cent)` 按金额去重，李四两笔同为15000，反而会把正确总额30000算成15000。关联知识：关联基数与聚合粒度。

## 四 运行与结果核对

在秋招根目录用Python标准库即可做查询结果核对：

```powershell
python -X utf8 .\notes\practice\检查SQL答案.py
```

脚本使用全新的内存SQLite库，执行本文18题中的21段查询，包括两段错误示例，逐段核对预期输出；不连接已有业务数据库。SQLite只能帮助核对本题数据结果，不能验证MySQL隔离、锁、索引计划、严格分组规则或全部方言行为。

若要在MySQL练习，先自行新建空练习库，再导入SQL数据文件；表已存在时换一个库，不要在现有项目库重复导入。SQL文件没有删除和覆盖语句。连接与导入的PowerShell示例：

```powershell
mysql -u 你的练习用户名 -p 新建的练习库名
```

进入MySQL客户端后，用客户端 `source` 命令读取文件，建议路径使用正斜杠：

```text
source C:/Users/98761/Desktop/Learning/秋招/notes/practice/SQL练习数据.sql;
```

本文的MySQL语义按官方文档核对；实际检查结果与环境见 [SQL验证记录](../6-resources/practice/SQL验证记录.md)。MySQL导入与运行由你在练习库完成，不把SQLite结果写成MySQL实测。

## 五 一页速记与达标

| 检查项 | 做题前提醒 |
|---|---|
| 所有用户 | 从用户表开始LEFT JOIN，检查右表条件的位置 |
| 没有记录 | NOT EXISTS或外连接后判断右表非空主键IS NULL |
| 总额达标 | 行条件WHERE，汇总条件HAVING |
| 保留并列档位 | DENSE_RANK；不能加唯一键破坏并列 |
| 第二高 | 先问“第二行”还是“第二个不同值” |
| NULL | IS NULL；COUNT列不数NULL；NOT IN警惕NULL |
| 日期 | 下界包含、下一天不包含 |
| 关联后求和 | 先确认一对多是否复制了明细 |
| 应用输入 | 绑定参数，不拼接用户值；表名等动态标识符用白名单 |

参数化查询将数据和SQL结构分开，但不能代替业务权限检查，见 [OWASP参数化查询说明](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)。

达标标准：不看答案重写SQL03、SQL04、SQL05、SQL07、SQL10；能解释为什么NULL和一对多关联会改变结果；修改一条样例后能先手算新输出，再运行核对。读过或运行过不等于能独立作答。

## 六 进阶知识讲解

### 条件聚合与集合操作

`CASE WHEN 条件 THEN 值 ELSE 值 END` 是一个产生值的表达式。把满足条件的行变成1，其他行变成0，再SUM，就能在同一张汇总表中分别统计不同状态。`COUNT(CASE WHEN 条件 THEN 1 ELSE 0 END)` 却会把两种结果都数进去，因为0也是非NULL值；若用COUNT，应让不满足条件的分支产生NULL。表达式规则见 [MySQL流程控制函数](https://dev.mysql.com/doc/refman/8.4/en/flow-control-functions.html)。

UNION把两份结果按列纵向合并，默认去掉重复结果行；UNION ALL保留重复。JOIN是按关联条件横向配对，可能一对多展开，二者目的不同。UNION两侧要有相同列数及兼容类型，最终ORDER BY作用于合并结果。需要重复就用ALL，不能先去重再试图找回丢失的重复次数。见 [MySQL UNION](https://dev.mysql.com/doc/refman/8.4/en/union.html)。

### CTE与窗口框架

WITH定义的公共表表达式（CTE）是当前语句内可引用的命名结果，适合把“先按用户求和，再求部门均值，再筛选”拆成可读的阶段。它不是自动持久化的表，也不保证一定比子查询快；是否合并、物化取决于查询和优化器。递归CTE还要有起始行、递推关系与终止条件，本章先掌握非递归写法。见 [MySQL WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html)。

窗口函数有三个不同维度：`PARTITION BY`规定哪些行分成一组，窗口内部ORDER BY规定计算顺序，frame规定当前行的聚合范围。最终结果的显示顺序仍由最外层ORDER BY决定。

| 写法 | 计算范围 | 适合任务 |
|---|---|---|
| `OVER (PARTITION BY user_id)` | 该用户整个分区 | 每行旁边显示用户总额 |
| `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | 排序后第一行到当前行 | 逐行累计 |
| `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` | 当前行及之前最多两行 | 最近三条记录移动平均 |
| `LAG(amount_cent)` | 排序后的上一行值 | 环比、相邻记录差值 |
| `ROW_NUMBER()` | 分区内逐行编号 | 每用户选最新一条 |

ROWS按行位置界定，RANGE按排序值的范围及同值行界定。MySQL有ORDER BY且省略frame时，聚合窗口默认通常是 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`，相同排序值的同行可能一起进入累计。希望逐条累计时，明确ROWS并提供稳定排序键。LAG/LEAD和排名函数不按聚合frame来限定分区，不能把所有窗口函数理解成同一种累计。见 [MySQL窗口框架](https://dev.mysql.com/doc/refman/8.4/en/window-functions-frames.html)。

### 所有条件和分页边界

“所有报销都已批准”可以转换成“不存在未批准的报销”。若题目还要求至少有一笔报销，需要再加EXISTS，否则从逻辑上没有报销的人也满足“不存在反例”，这叫空集上的全称命题为真。

OFFSET分页表达“跳过前N行”，偏移很大时可能扫描许多行；数据同时增删时，行的位置会变化。游标分页记住上一页末尾的排序键，查询排在该键之后的记录。多列排序时比较条件要与每列方向对应，并且最终排序应能唯一确定次序。它能减少对位置偏移的依赖，但不能单独保证多次查询看到完全一致的快照。

## 七 进阶题目与解析

以下8题仍使用第二节的原始三张表，无需修改练习数据。

### SQL11 一次分组统计多种状态

**题目：** 按部门返回报销总笔数、已批准笔数、待审批笔数、已拒绝笔数。

```sql
SELECT u.dept, COUNT(*) AS total_count,
       SUM(CASE WHEN e.status = 'approved' THEN 1 ELSE 0 END) AS approved_count,
       SUM(CASE WHEN e.status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
       SUM(CASE WHEN e.status = 'rejected' THEN 1 ELSE 0 END) AS rejected_count
FROM exam_expenses AS e
JOIN exam_users AS u ON u.user_id = e.user_id
GROUP BY u.dept
ORDER BY u.dept;
```

**答案：** 安全部门 `(2,1,0,1)`，研发部门 `(5,4,1,0)`；四个数字依次为总数、批准、待审、拒绝。

**推理：** 先把报销关联到部门。研发有101、102、103、104、107，其中只有102待审批；安全有105、106。每个CASE先生成一列0/1，再按部门求和。

**易错点：** 这里结果只要求有报销的部门，因此使用INNER JOIN。若要显示零报销部门，需要部门主表和外连接，并按报销主键计数。关联知识：条件聚合、主表选择。

### SQL12 UNION与UNION ALL

**题目：** 合并“有已批准报销的用户编号”和“有待审批报销的用户编号”，比较以下两种结果。

```sql
SELECT user_id FROM exam_expenses WHERE status = 'approved'
UNION
SELECT user_id FROM exam_expenses WHERE status = 'pending'
ORDER BY user_id;
```

```sql
SELECT user_id FROM exam_expenses WHERE status = 'approved'
UNION ALL
SELECT user_id FROM exam_expenses WHERE status = 'pending'
ORDER BY user_id;
```

**答案：** 第一段为 `1、2、3`；第二段为 `1、1、1、2、2、3`。

**推理：** 已批准分支有5行，待审批分支有1行。UNION对合并后的用户编号去重，所以只剩三个用户；ALL保留每笔报销对应的用户编号，包括同一分支内部的重复。

**易错点：** UNION不仅去掉两个分支之间的重叠，还去掉最终结果中相同的行；需要计数时不可随意去重。关联知识：集合与多重集语义。

### SQL13 超过本部门人均批准总额的用户

**题目：** 每人先计算已批准总额，没有报销的人按0计算，再找出高于本部门人均总额的人。

```sql
WITH totals AS (
  SELECT u.user_id, u.user_name, u.dept,
         COALESCE(SUM(e.amount_cent), 0) AS approved_cent
  FROM exam_users AS u
  LEFT JOIN exam_expenses AS e
    ON e.user_id = u.user_id AND e.status = 'approved'
  GROUP BY u.user_id, u.user_name, u.dept
), compared AS (
  SELECT totals.*,
         AVG(approved_cent) OVER (PARTITION BY dept) AS dept_average
  FROM totals
)
SELECT user_id, user_name, approved_cent, dept_average
FROM compared
WHERE approved_cent > dept_average
ORDER BY user_id;
```

**答案：** `(2,李四,30000,22500)`、`(3,王五,15000,7500)`。

**推理：** 研发两人的总额是15000、30000，均值22500；安全两人是15000、0，均值7500。先按人汇总后，AVG才是人均总额。

**易错点：** 直接AVG报销金额算的是“平均单笔金额”；漏掉零报销用户也会改变分母。关联知识：粒度、CTE、窗口聚合。

### SQL14 按提交顺序计算累计金额

**题目：** 对已批准报销，按每人提交日、报销编号升序，显示用户编号、报销编号和累计金额。

```sql
SELECT user_id, expense_id,
       SUM(amount_cent) OVER (
         PARTITION BY user_id
         ORDER BY submitted_at, expense_id
         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS running_cent
FROM exam_expenses
WHERE status = 'approved'
ORDER BY user_id, submitted_at, expense_id;
```

**答案：** `(1,101,10000)、(1,107,15000)、(2,103,15000)、(2,104,30000)、(3,106,15000)`。

**推理：** 每个用户单独开始累计，第二笔金额加到第一笔累计上。WHERE先排除未批准记录，因此102不进入张三的累计。

**易错点：** 只写 `OVER(PARTITION BY user_id)` 得到每行相同的用户总额；缺少唯一排序键可能让同日记录次序不确定。关联知识：分区、排序、frame。

### SQL15 每个用户最新一笔报销

**题目：** 不区分状态，查出每个用户最新提交的一笔报销；同日按编号较大者优先；没有报销的人也保留。

```sql
WITH latest AS (
  SELECT e.*,
         ROW_NUMBER() OVER (
           PARTITION BY user_id ORDER BY submitted_at DESC, expense_id DESC
         ) AS rn
  FROM exam_expenses AS e
)
SELECT u.user_id, l.expense_id, l.amount_cent
FROM exam_users AS u
LEFT JOIN latest AS l ON l.user_id = u.user_id AND l.rn = 1
ORDER BY u.user_id;
```

**答案：** `(1,107,5000)、(2,104,15000)、(3,106,15000)、(4,NULL,NULL)`。

**推理：** 先在用户分区中给明细编号，再只关联第1条。赵六仍由用户主表保留。

**易错点：** `MAX(submitted_at)` 加任意expense_id不能保证编号来自那一天；外层 `WHERE l.rn=1` 会去掉赵六。关联知识：分组取一条、外连接条件。

### SQL16 与上一笔金额比较

**题目：** 已批准报销按每人提交日、编号升序，返回编号、上一笔金额、本笔比上一笔增加多少。第一笔没有前值，保留NULL。

```sql
WITH compared AS (
  SELECT user_id, expense_id, submitted_at, amount_cent,
         LAG(amount_cent) OVER (
           PARTITION BY user_id ORDER BY submitted_at, expense_id
         ) AS previous_cent
  FROM exam_expenses WHERE status = 'approved'
)
SELECT expense_id, previous_cent, amount_cent - previous_cent AS change_cent
FROM compared
ORDER BY user_id, submitted_at, expense_id;
```

**答案：** `(101,NULL,NULL)、(107,10000,-5000)、(103,NULL,NULL)、(104,15000,0)、(106,NULL,NULL)`。

**推理：** LAG取同一用户在该排序下的上一行，不是编号减1的记录。NULL参与减法得到NULL，准确表示没有比较基准。

**易错点：** 不经说明把第一笔前值补0，会把“没有前值”改成“前值确实为0”。关联知识：LAG、缺失值与业务含义。

### SQL17 全部报销都已批准且至少有一笔

**题目：** 返回至少提交过一笔报销，且所有报销都已批准的用户。

```sql
SELECT u.user_id, u.user_name
FROM exam_users AS u
WHERE EXISTS (
  SELECT 1 FROM exam_expenses AS e WHERE e.user_id = u.user_id
)
AND NOT EXISTS (
  SELECT 1 FROM exam_expenses AS e
  WHERE e.user_id = u.user_id
    AND (e.status <> 'approved' OR e.status IS NULL)
)
ORDER BY u.user_id;
```

**答案：** `(2,李四)`。

**推理：** 张三有待审批，王五有已拒绝，均存在反例；李四两笔都是批准。赵六虽没有反例，但不满足至少一笔。

**易错点：** 只写“存在已批准”不能说明其余记录也批准；只写NOT EXISTS反例会纳入没有报销的人。当前status非空，NULL条件是为说明可空数据时应明确缺失状态不算批准。关联知识：存在量词、全称条件、三值逻辑。

### SQL18 根据上一页最后一条继续分页

**题目：** 已批准记录按金额降序、编号升序。第一页取了103和104，上一页末尾键为 `(15000,104)`。写出下一页最多2条。

```sql
SELECT expense_id, amount_cent
FROM exam_expenses
WHERE status = 'approved'
  AND (amount_cent < 15000 OR (amount_cent = 15000 AND expense_id > 104))
ORDER BY amount_cent DESC, expense_id ASC
LIMIT 2;
```

**答案：** `(106,15000)、(101,10000)`。

**推理：** 排在104之后的记录，要么金额更小，要么金额相同但编号更大；先接上同金额106，再接下一档101。

**易错点：** 只写 `amount_cent<15000` 会跳过并列的106；只写 `expense_id>104` 会漏掉编号小但金额更低的101。关联知识：多列排序、游标分页与稳定次序。

进阶达标：能解释“平均单笔”和“每人总额再求平均”的差别；能区分排名、累计和前值；能把“全部满足”改写成“不存在反例”；能按升降序写出下一页边界。
