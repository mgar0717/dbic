---
title: 녹취 이력 조회 (tvc_call_file)
eyebrow: sql
subtitle: 날짜·상담원·조건별 기본 조회
tag: 기본
---

녹취 이력의 메인 테이블은 `tvc_call_file` 이고 PK 는 `r_file_nm` 입니다.

## 파일명 구조

```
20260619095543m00lixs.807007200
```

| 위치 | 예시 | 의미 |
|---|---|---|
| 1 ~ 14 | `20260619095543` | 년월일시분초 (`YYYYMMDDHHMMSS`) |
| 15 | `m` | 메인 / 이중화 구분 |
| 16 ~ | `00lixs` | 파일내역 + 랜덤값 |
| `.` 뒤 | `807007200` | 내선 |

앞 14자리가 그대로 시각이라 **날짜뿐 아니라 시각까지 PK 범위 비교만으로 조회**됩니다.
별도 컬럼(`r_start_hms` 등)으로 거는 것보다 훨씬 빠르고,
`ORDER BY r_file_nm` 이 곧 시간순 정렬입니다.

뒤에 랜덤값이 붙으므로 **시각만으로는 `=` 매칭이 안 됩니다.** 범위로 거세요.

```sql
-- 09:55:43 에 시작된 통화
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260619095543'
  AND  r_file_nm <  '20260619095544';
```

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

## 시각까지 지정해서 찾기

`r_file_nm` 앞 14자리가 `YYYYMMDDHHMMSS` 이므로, **하루 안의 시간대도 PK 범위로** 걸 수 있습니다.

```sql
-- 8/28 오전 9시~12시 (PK 인덱스 사용)
SELECT r_file_nm, usr_nm, ext_no, r_dur
FROM   tvc_call_file
WHERE  r_file_nm >= '20260828090000'
  AND  r_file_nm <  '20260828120000'
ORDER BY r_file_nm;

-- 특정 시각 전후 10분 (민원·장애 시점 확인)
SELECT r_file_nm, usr_nm, ext_no, r_dur
FROM   tvc_call_file
WHERE  r_file_nm >= '20260828142000'
  AND  r_file_nm <  '20260828144000'
ORDER BY r_file_nm;

-- 심야 시간대 (자정~06시)
SELECT r_file_nm, usr_nm, ext_no
FROM   tvc_call_file
WHERE  r_file_nm >= '20260828000000'
  AND  r_file_nm <  '20260828060000';
```

**여러 날에 걸쳐 같은 시간대**를 보려면 날짜별로 범위가 끊기므로 한 번의 범위 조건으로는
안 됩니다. 이때는 날짜 범위를 먼저 걸어 대상을 좁힌 뒤 시각 부분을 잘라서 비교합니다.

```sql
-- 8월 전체 중 업무시간 외 통화 (09시 이전 / 18시 이후)
SELECT r_file_nm, usr_nm, ext_no, r_dur
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801' AND r_file_nm < '20260901'   -- 먼저 PK 로 좁히고
  AND (SUBSTRING(r_file_nm, 9, 6) <  '090000'                -- 그 안에서 시각 비교
    OR SUBSTRING(r_file_nm, 9, 6) >= '180000')
ORDER BY r_file_nm;
```

> 두 번째 조건의 `SUBSTRING` 은 인덱스를 못 타지만, 앞의 날짜 범위가 이미 대상을 줄여놨기
> 때문에 그 안에서만 비교합니다. **날짜 범위 없이 `SUBSTRING` 만 걸면 풀스캔**이 됩니다.
> 같은 이유로 `r_start_hms` 로 비교해도 되지만, 어차피 인덱스를 못 타는 건 같습니다.

`r_start_hms` / `r_end_hms` 는 `hhmmss` 문자열로 시작·종료 시각을 따로 담고 있습니다.
종료 시각이 필요할 때 쓰세요.

```sql
-- 자정을 넘겨 끝난 통화
SELECT r_file_nm, r_start_hms, r_end_hms, r_dur
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801' AND r_file_nm < '20260901'
  AND  r_end_hms < r_start_hms;
```

## 파일명에서 값 뽑아내기

메인/이중화 구분과 내선은 컬럼(`r_mainsub`, `ext_no`)에도 들어있지만,
파일명에서 직접 꺼내면 **컬럼과 실제 파일이 어긋난 건**을 찾을 수 있습니다.

```sql
-- 파일명 분해해서 보기
SELECT r_file_nm,
       SUBSTRING(r_file_nm,  1, 14)        AS 일시,
       SUBSTRING(r_file_nm, 15,  1)        AS 구분,
       SUBSTRING_INDEX(r_file_nm, '.', -1) AS 내선_파일명,
       ext_no                              AS 내선_컬럼,
       r_mainsub
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
LIMIT  20;

-- 메인/이중화 구분자별 건수 (어떤 값이 쓰이는지 확인)
SELECT SUBSTRING(r_file_nm, 15, 1) AS 구분, COUNT(*) AS cnt
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
GROUP BY SUBSTRING(r_file_nm, 15, 1);

-- 파일명의 내선과 ext_no 컬럼이 다른 건 (정합성 확인)
SELECT r_file_nm, ext_no, SUBSTRING_INDEX(r_file_nm, '.', -1) AS 파일명_내선
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  SUBSTRING_INDEX(r_file_nm, '.', -1) <> ext_no;
```

> MSSQL 에는 `SUBSTRING_INDEX` 가 없습니다.
> `RIGHT(r_file_nm, CHARINDEX('.', REVERSE(r_file_nm)) - 1)` 로 바꿔 쓰세요.

내선으로 찾을 때는 파일명이 아니라 **`ext_no` 컬럼**을 쓰세요.
`LIKE '%.807007200'` 은 앞이 `%` 라 인덱스를 못 탑니다.

```sql
-- 권장
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  ext_no = '807007200';
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
  AND  ext_no = '807007200';

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

## 노출 여부 / 삭제 여부

두 컬럼은 **서로 다른 것**입니다. 헷갈리기 쉬우니 구분해서 쓰세요.

| 컬럼 | 의미 |
|---|---|
| `r_yn` | **조회 화면에 보여줄지 여부.** `N` 이면 데이터·파일은 그대로 있고 사용자에게만 안 보임 |
| `t_del` | **삭제 처리 시각.** 값이 있으면 삭제된 건 |

```sql
-- 사용자가 실제로 볼 수 있는 건만 (조회 화면과 같은 조건)
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_yn = 'Y'
  AND  t_del IS NULL;

-- 통계·점검용: 숨김 처리된 것까지 전부 (r_yn 조건 없이)
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  t_del IS NULL;

-- 숨김 처리된 건 (데이터는 살아있는데 조회에서 빠진 것)
SELECT r_file_nm, usr_nm, ext_no, r_yn, t_up
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801'
  AND  r_yn <> 'Y'
  AND  t_del IS NULL
ORDER BY r_file_nm DESC;

-- 삭제 처리된 건
SELECT r_file_nm, usr_nm, t_del
FROM   tvc_call_file
WHERE  t_del IS NOT NULL
ORDER BY t_del DESC
LIMIT  100;

-- 일자별 숨김 건수 (갑자기 늘면 확인 필요)
SELECT LEFT(r_file_nm, 8) AS ymd,
       COUNT(*)                  AS total,
       SUM(r_yn <> 'Y')          AS hidden
FROM   tvc_call_file
WHERE  r_file_nm >= '20260801' AND r_file_nm < '20260901'
  AND  t_del IS NULL
GROUP BY LEFT(r_file_nm, 8)
ORDER BY ymd;
```

> 건수를 세는 통계에서 `r_yn = 'Y'` 를 걸면 **숨김 처리된 통화가 빠져서** 실제 발생 건수와
> 달라집니다. 화면에 보이는 것과 맞춰야 할 때만 걸고, 실적·점검 집계에는 빼세요.

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
-- 특정 파일 한 건 상세 (전체 파일명을 알 때)
SELECT * FROM tvc_call_file WHERE r_file_nm = '<전체 파일명>';

-- 시각만 알 때 — 앞 14자리로 찾기 (뒤에 문자열이 더 붙으므로 = 로는 안 잡힘)
SELECT * FROM tvc_call_file
WHERE  r_file_nm >= '20260828090142'
  AND  r_file_nm <  '20260828090143';

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
