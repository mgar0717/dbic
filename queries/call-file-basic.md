---
title: 녹취 이력 조회 (tvc_call_file)
eyebrow: sql
subtitle: 날짜·상담원·조건별 기본 조회
tag: 기본
---

녹취 이력의 메인 테이블은 `tvc_call_file` 이고 PK 는 `r_file_nm` 입니다.
날짜 조회는 **PK 인 `r_file_nm` 앞자리(YYYYMMDD)로 범위를 거는 방식**이 가장 빠릅니다.

> 아래는 MariaDB 기준입니다. MSSQL 은 `LIMIT n` → `TOP n`,
> `DATE_FORMAT(NOW(),'%Y%m%d')` → `CONVERT(varchar(8), GETDATE(), 112)` 로 바꿔 쓰세요.

## 날짜로 찾기

```sql
-- 특정 하루
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260828'
  AND  r_file_nm <  '20260829'
ORDER BY r_file_nm;

-- 기간 (8/1 ~ 8/28)
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_file_nm <  '20260829';

-- 오늘
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= DATE_FORMAT(NOW(), '%Y%m%d')
  AND  r_file_nm <  DATE_FORMAT(NOW() + INTERVAL 1 DAY, '%Y%m%d');

-- 최근 7일
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= DATE_FORMAT(NOW() - INTERVAL 7 DAY, '%Y%m%d');
```

`LIKE '20260828%'` 도 같은 결과지만, 범위 조건이 의도가 분명하고 안전합니다.
`LEFT(r_file_nm, 8) = '20260828'` 처럼 **컬럼을 함수로 감싸면 PK 인덱스를 못 탑니다.**

파일명 앞자리가 날짜가 아닌 사이트라면 아래로 실제 형식을 먼저 확인하세요.

```sql
SELECT r_file_nm, r_start_hms, srv_id, ext_no
FROM   tvc_call_file
ORDER BY t_cr DESC
LIMIT  5;
```

## 날짜 + 시간대

`r_start_hms` / `r_end_hms` 는 `hhmmss` 문자열입니다.

```sql
-- 8/28 오전 9시~12시 통화
SELECT r_file_nm, r_start_hms, r_end_hms, usr_nm, ext_no, r_dur
FROM   tvc_call_file
WHERE  r_file_nm >= '20260828' AND r_file_nm < '20260829'
  AND  r_start_hms >= '090000'
  AND  r_start_hms <  '120000'
ORDER BY r_start_hms;

-- 업무시간 외 통화 (09시 이전 / 18시 이후)
SELECT r_file_nm, r_start_hms, usr_nm, ext_no
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND (r_start_hms < '090000' OR r_start_hms >= '180000');
```

## 상담원·부서·내선

```sql
-- 상담원 ID 로
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  usr_id = 'A12345';

-- 상담원명으로 (부분일치)
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  usr_nm LIKE '%홍길동%';

-- 내선번호로
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  ext_no = '1234';

-- 부서(그룹) 하위 전체 — gr_sum_cd 가 'DBIC>001>002' 형태로 경로를 담고 있음
SELECT f.r_file_nm, f.usr_nm, g.gr_sum_nm, f.r_dur
FROM   tvc_call_file f
JOIN   tvc_group     g ON g.gr_cd = f.gr_cd
WHERE  f.r_file_nm >= '20260801'
  AND  g.gr_sum_cd LIKE 'DBIC>001%';
```

## 통화 속성

```sql
-- 인바운드/아웃바운드
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_calltype = 'IN';        -- IN, OUT, 출금동의

-- 통화시간 조건 (r_dur 단위: 초)
SELECT r_file_nm, usr_nm, r_dur
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_dur >= 600                       -- 10분 이상
ORDER BY r_dur DESC;

-- 짧은 통화 (3초 미만) — 오접속·끊김 확인용
SELECT r_file_nm, usr_nm, ext_no, r_dur
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_dur < 3;

-- 마킹된 통화만
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_mark = 1;
```

## 삭제/조회가능 여부

```sql
-- 정상 조회 대상만
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_yn = 'Y'
  AND  t_del IS NULL;

-- 삭제 처리된 건
SELECT r_file_nm, usr_nm, t_del
FROM   tvc_call_file
WHERE  t_del IS NOT NULL
ORDER BY t_del DESC
LIMIT  100;
```

> `r_yn`(조회가능여부)과 `t_del`(삭제시간) 중 어느 쪽을 기준으로 쓰는지는 사이트마다 다릅니다.
> 실제 데이터로 한 번 확인하고 고정해서 쓰세요.

## 업무 정보 컬럼

`call01`~`call20`, `enc01`~`enc05` 는 사이트별로 의미가 배정되는 확장 컬럼입니다.
정의서 기준 기본 배정은 이렇습니다.

| 컬럼 | 의미 | 컬럼 | 의미 |
|---|---|---|---|
| `enc01` | 전화번호 (암호화) | `call05` | 녹음메모 |
| `enc02` | 고객명 (암호화) | `call06` | 조작자행번 |
| `call01` | 고객번호 | `call07` | 권유자행번 |
| `call02` | 시스템구분 | `call11` | 파생 STATUS |
| `call03` | 업무구분 | `call13` | 최종파일 |
| `call04` | 상품명 | `call10` | 추가사유 |

```sql
-- 업무구분·상품으로
SELECT r_file_nm, usr_nm, call03, call04, r_dur
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  call03 = '신규가입'
  AND  call04 LIKE '%적금%';

-- 고객번호로
SELECT * FROM tvc_call_file
WHERE  call01 = '1000123456';

-- 메모가 있는 건만
SELECT r_file_nm, usr_nm, call05
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  call05 IS NOT NULL AND call05 <> '';
```

> `enc01`(전화번호)·`enc02`(고객명)는 암호화 저장이라 평문 `LIKE` 검색이 되지 않습니다.
> 조회하려면 애플리케이션의 암호화 함수로 값을 만들어 `=` 비교해야 합니다.

## 자주 쓰는 조회 한 줄

```sql
-- 특정 파일 한 건 상세
SELECT * FROM tvc_call_file WHERE r_file_nm = '20260828_090142_1234';

-- 가장 최근 녹취 20건
SELECT r_file_nm, r_start_hms, usr_nm, ext_no, r_dur, srv_id
FROM   tvc_call_file
ORDER BY r_file_nm DESC
LIMIT  20;

-- 서버별 최근 녹취 시각 (녹취 중단 확인)
SELECT srv_id, MAX(r_file_nm) AS last_file
FROM   tvc_call_file
GROUP BY srv_id;
```
