---
title: 마스터·이력 조회
eyebrow: sql
subtitle: 사용자·그룹·구간녹취·승인·다운로드·로그
tag: 이력
---

## 사용자 (tvc_usr)

```sql
-- 사용중 계정
SELECT usr_id, usr_nm, gr_cd, usr_lev, ext_no, task_auth, menu_auth, login_tm
FROM   tvc_usr
WHERE  usr_yn = 'Y' AND t_del IS NULL
ORDER BY gr_cd, usr_id;

-- 부서 경로와 함께
SELECT u.usr_id, u.usr_nm, g.gr_sum_nm AS 부서경로, u.ext_no
FROM   tvc_usr u
LEFT   JOIN tvc_group g ON g.gr_cd = u.gr_cd
WHERE  u.usr_yn = 'Y' AND u.t_del IS NULL;

-- 장기 미접속 계정 (90일)
SELECT usr_id, usr_nm, gr_cd, login_tm
FROM   tvc_usr
WHERE  usr_yn = 'Y' AND t_del IS NULL
  AND (login_tm IS NULL OR login_tm < NOW() - INTERVAL 90 DAY)
ORDER BY login_tm;

-- 로그인 실패 누적 계정
SELECT usr_id, usr_nm, login_fail, login_tm
FROM   tvc_usr
WHERE  login_fail > 0
ORDER BY login_fail DESC;

-- 비밀번호 장기 미변경 (180일)
SELECT usr_id, usr_nm, pwdchg_tm
FROM   tvc_usr
WHERE  usr_yn = 'Y' AND t_del IS NULL
  AND (pwdchg_tm IS NULL OR pwdchg_tm < NOW() - INTERVAL 180 DAY);

-- 권한별 인원
SELECT menu_auth, COUNT(*) AS cnt
FROM   tvc_usr
WHERE  usr_yn = 'Y' AND t_del IS NULL
GROUP BY menu_auth;
```

## 그룹 (tvc_group)

```sql
-- 조직도 (레벨 순)
SELECT gr_cd, gr_nm, gr_parent, gr_lev, gr_sum_nm, gr_usrcnt
FROM   tvc_group
WHERE  gr_yn = 'Y' AND t_del IS NULL
ORDER BY gr_sum_cd;

-- 특정 부서 하위 전체
SELECT gr_cd, gr_nm, gr_lev, gr_sum_nm
FROM   tvc_group
WHERE  gr_sum_cd LIKE 'DBIC>001%'
  AND  gr_yn = 'Y';

-- 인원수와 실제 사용자 수가 안 맞는 그룹
SELECT g.gr_cd, g.gr_nm, g.gr_usrcnt AS 기록값, COUNT(u.usr_id) AS 실제값
FROM   tvc_group g
LEFT   JOIN tvc_usr u
       ON u.gr_cd = g.gr_cd AND u.usr_yn = 'Y' AND u.t_del IS NULL
WHERE  g.gr_yn = 'Y' AND g.t_del IS NULL
GROUP BY g.gr_cd, g.gr_nm, g.gr_usrcnt
HAVING g.gr_usrcnt <> COUNT(u.usr_id);
```

## 구간녹취 (tvc_call_part)

```sql
-- 특정 녹취의 구간 목록
SELECT part_id, part_type, part_start, part_end, part_nm, part_state, part_err
FROM   tvc_call_part
WHERE  r_file_nm = '<전체 파일명>'
ORDER BY part_id;

-- 처리 실패한 구간
SELECT r_file_nm, part_id, part_state, part_err, t_cr
FROM   tvc_call_part
WHERE  part_err IS NOT NULL AND part_err <> ''
ORDER BY t_cr DESC
LIMIT  100;

-- 구간녹취가 있는 통화 (원본과 함께)
SELECT f.r_file_nm, f.usr_nm, f.r_dur, COUNT(p.part_id) AS part_cnt
FROM   tvc_call_file f
JOIN   tvc_call_part p ON p.r_file_nm = f.r_file_nm
WHERE  f.r_file_nm >= '20260801'
GROUP BY f.r_file_nm, f.usr_nm, f.r_dur;
```

## 마킹 (tvc_call_mark)

```sql
-- 마킹 목록
SELECT r_file_nm, mark_start, mark_end, mark_state, mark_desc, t_cr
FROM   tvc_call_mark
WHERE  t_del IS NULL
ORDER BY t_cr DESC
LIMIT  100;

-- 특정 녹취의 마킹
SELECT mark_start, mark_end, mark_desc
FROM   tvc_call_mark
WHERE  r_file_nm = '<전체 파일명>'
  AND  t_del IS NULL;
```

## 청취·다운로드 승인 (tvc_appr)

```sql
-- 승인 대기 건
SELECT appr_idx, req_id, req_group, req_time, req_type, req_memo, appr_stat
FROM   tvc_appr
WHERE  req_yn = 'Y'
  AND (appr_stat IS NULL OR appr_stat = '')
ORDER BY req_time DESC;

-- 최근 승인 이력
SELECT appr_idx, req_id, req_type, req_memo,
       appr_id, appr_allow_tm, appr_stat, appr_memo
FROM   tvc_appr
ORDER BY appr_idx DESC
LIMIT  100;

-- 요청자별 요청 건수
SELECT req_id, req_group, COUNT(*) AS cnt
FROM   tvc_appr
WHERE  req_time >= '20260801'
GROUP BY req_id, req_group
ORDER BY cnt DESC;

-- 승인자별 처리 건수
SELECT appr_id, COUNT(*) AS cnt
FROM   tvc_appr
WHERE  appr_allow_tm >= '20260801'
GROUP BY appr_id
ORDER BY cnt DESC;
```

## 다운로드 (tvc_call_down)

```sql
-- 최근 다운로드
SELECT seq, r_file_nm, r_rsrv_ip, r_status
FROM   tvc_call_down
ORDER BY seq DESC
LIMIT  100;

-- 특정 녹취를 누가 받아갔는지
SELECT * FROM tvc_call_down
WHERE  r_file_nm = '<전체 파일명>';

-- 상태별 건수
SELECT r_status, COUNT(*) AS cnt
FROM   tvc_call_down
GROUP BY r_status;
```

## 이벤트 로그 (tvc_log_event)

```sql
-- 최근 로그
SELECT log_tm, usr_id, usr_ip, usr_app, log_type, log_lev, log_data
FROM   tvc_log_event
ORDER BY log_tm DESC
LIMIT  200;

-- 특정 사용자의 활동
SELECT log_tm, usr_ip, log_type, log_data
FROM   tvc_log_event
WHERE  usr_id = 'A12345'
  AND  log_tm >= NOW() - INTERVAL 7 DAY
ORDER BY log_tm DESC;

-- 로그인 이력
SELECT log_tm, usr_id, usr_ip, log_data
FROM   tvc_log_event
WHERE  log_type LIKE '%LOGIN%'
  AND  log_tm >= NOW() - INTERVAL 7 DAY
ORDER BY log_tm DESC;

-- 값이 변경된 이력 (변경 전/후)
SELECT log_tm, usr_id, log_type, log_before, log_after
FROM   tvc_log_event
WHERE  log_before IS NOT NULL AND log_before <> ''
ORDER BY log_tm DESC
LIMIT  100;

-- 에러 로그만
SELECT log_tm, usr_id, log_type, log_data
FROM   tvc_log_event
WHERE  log_lev IN ('ERROR', 'E')
  AND  log_tm >= NOW() - INTERVAL 1 DAY
ORDER BY log_tm DESC;

-- 일별 접속자 수
SELECT DATE(log_tm) AS ymd, COUNT(DISTINCT usr_id) AS users
FROM   tvc_log_event
WHERE  log_tm >= NOW() - INTERVAL 30 DAY
GROUP BY DATE(log_tm)
ORDER BY ymd;

-- 같은 계정 여러 IP 접속 (계정 공유 확인)
SELECT usr_id, COUNT(DISTINCT usr_ip) AS ip_cnt
FROM   tvc_log_event
WHERE  log_tm >= NOW() - INTERVAL 7 DAY
  AND  usr_ip IS NOT NULL AND usr_ip <> ''
GROUP BY usr_id
HAVING COUNT(DISTINCT usr_ip) > 3
ORDER BY ip_cnt DESC;
```

## 서버 (tvc_server)

```sql
SELECT srv_id, srv_ip, srv_nm, srv_main, srv_type, srv_yn, srv_stg1, srv_stg2
FROM   tvc_server
WHERE  t_del IS NULL
ORDER BY srv_sort, srv_id;
```
