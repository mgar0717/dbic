---
title: 운영 점검·이상 탐지
eyebrow: sql
subtitle: 파일 보관 상태, 무음/누락, 녹취 중단 확인
tag: 점검
---

## 파일 보관 상태

`in_hdd` / `in_stg1` / `in_stg2` 는 존재 여부를 숫자로 표시합니다.
정의서 기준 `0` = 미존재, `100` 미만 = 진행중, `100` = 존재.

```sql
-- 보관 상태 요약 (기간)
SELECT SUM(in_hdd  = 100) AS hdd_ok,
       SUM(in_stg1 = 100) AS stg1_ok,
       SUM(in_stg2 = 100) AS stg2_ok,
       COUNT(*)           AS total
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801' AND r_file_nm < '20260901';

-- HDD 에 파일이 없는 건 (조회 대상인데 실물 없음)
SELECT r_file_nm, usr_nm, ext_no, srv_id, r_file_path, in_hdd, in_stg1, in_stg2
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  in_hdd <> 100
  AND  t_del IS NULL
ORDER BY r_file_nm;

-- 1차 백업(STG1) 누락
SELECT LEFT(r_file_nm, 8) AS ymd, COUNT(*) AS missing
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  in_stg1 <> 100
  AND  t_del IS NULL
GROUP BY LEFT(r_file_nm, 8)
ORDER BY ymd;

-- 백업이 어디에도 없는 건 (가장 위험)
SELECT r_file_nm, usr_nm, srv_id, in_hdd, in_stg1, in_stg2
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  in_stg1 <> 100 AND in_stg2 <> 100
  AND  t_del IS NULL;

-- 진행중 상태로 멈춰 있는 건 (0 < 값 < 100)
SELECT r_file_nm, in_hdd, in_stg1, in_stg2, t_cr, t_up
FROM   tvc_call_file
WHERE  (in_hdd BETWEEN 1 AND 99)
    OR (in_stg1 BETWEEN 1 AND 99)
    OR (in_stg2 BETWEEN 1 AND 99);
```

## 무음·음성 이상

`rx_rtp_cnt`(고객측) / `tx_rtp_cnt`(직원측) 는 녹음 중 수신한 음성 RTP 카운트입니다.
한쪽이 0 이면 단방향 녹취, 둘 다 0 이면 무음 파일일 가능성이 높습니다.

```sql
-- 양방향 모두 음성 없음 (무음 의심)
SELECT r_file_nm, usr_nm, ext_no, r_dur, rx_rtp_cnt, tx_rtp_cnt
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_dur > 5
  AND  IFNULL(rx_rtp_cnt, 0) = 0
  AND  IFNULL(tx_rtp_cnt, 0) = 0;

-- 단방향 녹취 (한쪽만 0)
SELECT r_file_nm, usr_nm, ext_no, r_dur, rx_rtp_cnt, tx_rtp_cnt
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_dur > 5
  AND ((IFNULL(rx_rtp_cnt,0) = 0) XOR (IFNULL(tx_rtp_cnt,0) = 0));

-- 내선별 무음 발생 건수 (특정 전화기 문제 찾기)
SELECT ext_no, COUNT(*) AS silent_cnt
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_dur > 5
  AND  IFNULL(rx_rtp_cnt,0) = 0 AND IFNULL(tx_rtp_cnt,0) = 0
GROUP BY ext_no
ORDER BY silent_cnt DESC;
```

## 녹취 중단 감지

```sql
-- 서버별 마지막 녹취 (오늘 녹취가 끊긴 서버 확인)
SELECT srv_id, MAX(r_file_nm) AS last_file, MAX(t_cr) AS last_ins
FROM   tvc_call_file
GROUP BY srv_id;

-- 오늘 녹취가 0건인 내선 (어제는 있었던 내선 기준)
SELECT e.ext_no, e.ext_desc, e.usr_id
FROM   tvc_ext e
WHERE  e.ext_yn = 'Y'
  AND  e.t_del IS NULL
  AND  NOT EXISTS (
         SELECT 1 FROM tvc_call_file f
         WHERE  f.ext_no = e.ext_no
           AND  f.r_file_nm >= DATE_FORMAT(NOW(), '%Y%m%d')
       )
  AND  EXISTS (
         SELECT 1 FROM tvc_call_file f
         WHERE  f.ext_no = e.ext_no
           AND  f.r_file_nm >= DATE_FORMAT(NOW() - INTERVAL 1 DAY, '%Y%m%d')
           AND  f.r_file_nm <  DATE_FORMAT(NOW(), '%Y%m%d')
       );
```

## 회선 상태

```sql
-- 녹취 장애가 기록된 회선
SELECT srv_id, ext_no, ext_desc, r_state, r_err, r_errtm
FROM   tvc_ext
WHERE  r_err IS NOT NULL AND r_err <> ''
ORDER BY r_errtm DESC;

-- 사용 설정된 회선 수 / 서버별
SELECT srv_id, COUNT(*) AS ext_cnt, SUM(ext_yn = 'Y') AS enabled
FROM   tvc_ext
WHERE  t_del IS NULL
GROUP BY srv_id;

-- 사용자 미배정 회선
SELECT srv_id, ext_no, ext_desc
FROM   tvc_ext
WHERE  ext_yn = 'Y' AND t_del IS NULL
  AND (usr_id IS NULL OR usr_id = '');
```

## HA(메인/백업) 절체

```sql
-- 절체가 발생한 녹취
SELECT r_file_nm, srv_id, r_mainsub, ha_flag_recovery, ha_related_file
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  ha_flag_recovery = 1;

-- 메인/백업 비율
SELECT r_mainsub, COUNT(*) AS cnt
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
GROUP BY r_mainsub;
```

## 삭제 예정·삭제 처리

```sql
-- 삭제 대기 목록
SELECT r_file_nm, srv_id, t_reserv, in_hdd, in_stg1, in_stg2
FROM   tvc_call_del
ORDER BY t_reserv
LIMIT  100;

-- 삭제 진행 현황 (아직 안 지워진 것)
SELECT COUNT(*) AS pending
FROM   tvc_call_del
WHERE  db_del IS NULL OR db_del = '';
```

## 코덱 변환

```sql
-- 변환 안 된 파일
SELECT r_file_nm, srv_id, r_codec, r_dur
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  IFNULL(r_codec, 0) <> 1;
```

## 데이터 정합성

```sql
-- 통화시간과 시작/종료 시각이 안 맞는 건
SELECT r_file_nm, r_start_hms, r_end_hms, r_dur
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_end_hms < r_start_hms;      -- 자정 넘긴 통화이거나 데이터 이상

-- 상담원 정보가 비어 있는 녹취
SELECT LEFT(r_file_nm,8) AS ymd, COUNT(*) AS cnt
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND (usr_id IS NULL OR usr_id = '')
GROUP BY LEFT(r_file_nm,8);

-- 마스터에 없는 상담원 ID 가 박힌 녹취
SELECT DISTINCT f.usr_id, f.usr_nm
FROM   tvc_call_file f
LEFT   JOIN tvc_usr u ON u.usr_id = f.usr_id
WHERE  f.r_file_nm >= '20260801'
  AND  f.usr_id IS NOT NULL AND f.usr_id <> ''
  AND  u.usr_id IS NULL;
```
