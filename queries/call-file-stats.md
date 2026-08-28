---
title: 녹취 집계·통계
eyebrow: sql
subtitle: 일별·상담원별·부서별 건수와 통화량
tag: 집계
---

모두 `tvc_call_file` 기준입니다. `r_file_nm` 은 앞 14자리가 `YYYYMMDDHHMMSS` 이므로
날짜는 앞 8자리, 시각은 9~14번째 자리를 잘라 씁니다.

## 일별

```sql
-- 일별 건수·통화량 (8월)
SELECT LEFT(r_file_nm, 8)          AS ymd,
       COUNT(*)                    AS cnt,
       SUM(r_dur)                  AS total_sec,
       ROUND(AVG(r_dur))           AS avg_sec,
       MAX(r_dur)                  AS max_sec
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801' AND r_file_nm < '20260901'
GROUP BY LEFT(r_file_nm, 8)
ORDER BY ymd;
```

> `GROUP BY` 안의 `LEFT()` 는 괜찮습니다. 인덱스는 `WHERE` 의 범위 조건이 이미 태웠기 때문입니다.
> **범위 조건 없이** 전체를 `LEFT()` 로 묶으면 풀스캔이 되니 기간은 항상 걸어주세요.

```sql
-- 시간대별 분포 (하루)
SELECT LEFT(r_start_hms, 2) AS hh,
       COUNT(*)             AS cnt,
       SUM(r_dur)           AS total_sec
FROM   tvc_call_file
WHERE  r_file_nm >= '20260828' AND r_file_nm < '20260829'
GROUP BY LEFT(r_start_hms, 2)
ORDER BY hh;

-- 월별 (연 단위 추이)
SELECT LEFT(r_file_nm, 6) AS ym, COUNT(*) AS cnt, SUM(r_dur) AS total_sec
FROM   tvc_call_file
WHERE  r_file_nm >= '20260101' AND r_file_nm < '20270101'
GROUP BY LEFT(r_file_nm, 6)
ORDER BY ym;
```

## 상담원별

```sql
-- 상담원별 실적 (기간)
SELECT usr_id,
       MAX(usr_nm)                       AS usr_nm,
       COUNT(*)                          AS cnt,
       SUM(r_dur)                        AS total_sec,
       ROUND(AVG(r_dur))                 AS avg_sec,
       SUM(r_calltype = 'IN')            AS in_cnt,
       SUM(r_calltype = 'OUT')           AS out_cnt
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801' AND r_file_nm < '20260901'
  AND  usr_id IS NOT NULL AND usr_id <> ''
GROUP BY usr_id
ORDER BY cnt DESC;
```

> MSSQL 에서는 `SUM(r_calltype = 'IN')` 이 안 됩니다.
> `SUM(CASE WHEN r_calltype = 'IN' THEN 1 ELSE 0 END)` 로 쓰세요.

```sql
-- 상담원별 일자별 (피벗 대신 행으로)
SELECT LEFT(r_file_nm, 8) AS ymd, usr_id, MAX(usr_nm) AS usr_nm, COUNT(*) AS cnt
FROM   tvc_call_file
WHERE  r_file_nm >= '20260825' AND r_file_nm < '20260829'
GROUP BY LEFT(r_file_nm, 8), usr_id
ORDER BY ymd, cnt DESC;

-- 녹취가 한 건도 없는 상담원 (사용중 계정 기준)
SELECT u.usr_id, u.usr_nm, u.gr_cd, u.ext_no
FROM   tvc_usr u
LEFT   JOIN tvc_call_file f
       ON  f.usr_id = u.usr_id
       AND f.r_file_nm >= '20260801' AND f.r_file_nm < '20260901'
WHERE  u.usr_yn = 'Y'
  AND  u.t_del IS NULL
  AND  f.r_file_nm IS NULL;
```

## 부서(그룹)별

```sql
-- 부서별 집계 — 그룹 경로명(gr_sum_nm) 과 함께
SELECT f.gr_cd,
       MAX(g.gr_sum_nm)  AS gr_path,
       COUNT(*)          AS cnt,
       SUM(f.r_dur)      AS total_sec,
       ROUND(AVG(f.r_dur)) AS avg_sec
FROM   tvc_call_file f
LEFT   JOIN tvc_group g ON g.gr_cd = f.gr_cd
WHERE  f.r_file_nm >= '20260801' AND f.r_file_nm < '20260901'
GROUP BY f.gr_cd
ORDER BY cnt DESC;

-- 특정 부서 하위 전체 합계
SELECT COUNT(*) AS cnt, SUM(f.r_dur) AS total_sec
FROM   tvc_call_file f
JOIN   tvc_group     g ON g.gr_cd = f.gr_cd
WHERE  f.r_file_nm >= '20260801'
  AND  g.gr_sum_cd LIKE 'DBIC>001%';
```

## 서버·회선별

```sql
-- 서버별 녹취 건수
SELECT f.srv_id, MAX(s.srv_nm) AS srv_nm, COUNT(*) AS cnt, SUM(f.r_dur) AS total_sec
FROM   tvc_call_file f
LEFT   JOIN tvc_server s ON s.srv_id = f.srv_id
WHERE  f.r_file_nm >= '20260801'
GROUP BY f.srv_id;

-- 내선별 건수 TOP 30
SELECT ext_no, COUNT(*) AS cnt, SUM(r_dur) AS total_sec
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
GROUP BY ext_no
ORDER BY cnt DESC
LIMIT  30;
```

## 통화시간 구간 분포

```sql
SELECT CASE
         WHEN r_dur <   10 THEN '00. 10초 미만'
         WHEN r_dur <   60 THEN '01. 1분 미만'
         WHEN r_dur <  180 THEN '02. 3분 미만'
         WHEN r_dur <  600 THEN '03. 10분 미만'
         WHEN r_dur < 1800 THEN '04. 30분 미만'
         ELSE                   '05. 30분 이상'
       END  AS band,
       COUNT(*) AS cnt
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801' AND r_file_nm < '20260901'
GROUP BY band
ORDER BY band;
```

## 업무구분·상품별

```sql
SELECT call03 AS 업무구분, call04 AS 상품명, COUNT(*) AS cnt, ROUND(AVG(r_dur)) AS avg_sec
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801' AND r_file_nm < '20260901'
  AND  call03 IS NOT NULL AND call03 <> ''
GROUP BY call03, call04
ORDER BY cnt DESC
LIMIT  50;
```

## 전월 대비

```sql
SELECT LEFT(r_file_nm, 6) AS ym,
       COUNT(*)           AS cnt,
       SUM(r_dur)         AS total_sec
FROM   tvc_call_file
WHERE  r_file_nm >= DATE_FORMAT(NOW() - INTERVAL 1 MONTH, '%Y%m01')
GROUP BY LEFT(r_file_nm, 6)
ORDER BY ym;
```
