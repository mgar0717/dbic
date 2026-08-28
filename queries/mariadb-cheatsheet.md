---
title: MariaDB 자주 쓰는 쿼리
eyebrow: sql
subtitle: 조회·점검·관리용 기본 쿼리 모음
tag: 기본
---

## 접속·현황

```sql
-- 현재 접속 세션
SHOW PROCESSLIST;

-- 버전·주요 변수
SHOW VARIABLES LIKE '%version%';
SHOW VARIABLES LIKE 'max_connections';

-- 현재 실행 중인 오래된 쿼리만
SELECT id, user, host, db, time, state, LEFT(info, 120) AS q
FROM   information_schema.processlist
WHERE  command <> 'Sleep'
  AND  time > 5
ORDER BY time DESC;
```

## 용량 점검

```sql
-- 테이블별 용량 TOP 20
SELECT table_name,
       ROUND(data_length  / 1024 / 1024, 1) AS data_mb,
       ROUND(index_length / 1024 / 1024, 1) AS idx_mb,
       table_rows
FROM   information_schema.tables
WHERE  table_schema = DATABASE()
ORDER BY data_length + index_length DESC
LIMIT  20;

-- DB 전체 용량
SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS total_mb
FROM   information_schema.tables
WHERE  table_schema = DATABASE();
```

## 스키마 확인

```sql
-- 컬럼 목록
SELECT column_name, column_type, is_nullable, column_key, column_comment
FROM   information_schema.columns
WHERE  table_schema = DATABASE()
  AND  table_name   = 'your_table'
ORDER BY ordinal_position;

-- 인덱스 목록
SHOW INDEX FROM your_table;

-- 특정 컬럼명을 쓰는 테이블 찾기
SELECT table_name, column_name
FROM   information_schema.columns
WHERE  table_schema = DATABASE()
  AND  column_name LIKE '%keyword%';
```

## 날짜 조건

```sql
-- 오늘
WHERE reg_dt >= CURDATE()

-- 최근 7일
WHERE reg_dt >= DATE_SUB(NOW(), INTERVAL 7 DAY)

-- 특정 월 (인덱스 타도록 범위로)
WHERE reg_dt >= '2026-08-01' AND reg_dt < '2026-09-01'
```

> `DATE(reg_dt) = '2026-08-01'` 처럼 컬럼을 함수로 감싸면 인덱스를 못 탑니다. 범위 조건으로 쓰세요.

## 백업·복원

```bash
# 스키마+데이터 전체
mysqldump -u<계정> -p <DB명> > dump_$(date +%Y%m%d).sql

# 특정 테이블 데이터만 (구조 제외)
mysqldump -u<계정> -p --no-create-info <DB명> <테이블> > table_data.sql

# 복원
mysql -u<계정> -p <DB명> < dump_20260828.sql
```
