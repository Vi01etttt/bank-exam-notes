-- 原创笔试练习数据。仅在新建练习库执行；不含 DROP / DELETE。
-- 表名加 exam_ 前缀。重复导入会因表已存在报错，应另建练习库。
CREATE TABLE exam_users (
    user_id INTEGER PRIMARY KEY,
    user_name VARCHAR(20) NOT NULL,
    dept VARCHAR(20) NOT NULL,
    email VARCHAR(80)
);
CREATE TABLE exam_expenses (
    expense_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    amount_cent INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    submitted_at DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES exam_users(user_id)
);
CREATE TABLE exam_reviews (
    review_id INTEGER PRIMARY KEY,
    expense_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    FOREIGN KEY (expense_id) REFERENCES exam_expenses(expense_id)
);
INSERT INTO exam_users VALUES
    (1, '张三', '研发', 'zhang@example.invalid'),
    (2, '李四', '研发', NULL),
    (3, '王五', '安全', 'wang@example.invalid'),
    (4, '赵六', '安全', NULL);
INSERT INTO exam_expenses VALUES
    (101, 1, 10000, 'approved', '2026-10-01'),
    (102, 1, 20000, 'pending',  '2026-10-02'),
    (103, 2, 15000, 'approved', '2026-10-01'),
    (104, 2, 15000, 'approved', '2026-10-03'),
    (105, 3, 30000, 'rejected', '2026-10-02'),
    (106, 3, 15000, 'approved', '2026-10-04'),
    (107, 1,  5000, 'approved', '2026-10-05');
INSERT INTO exam_reviews VALUES
    (201, 101, 7), (202, 101, 8), (203, 103, 7);
