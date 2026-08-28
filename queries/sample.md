---
title: 샘플 (작성 형식)
parent: Queries
nav_order: 1
---

# 샘플 — 작성 형식

새 문서는 `.md` 파일로 만들고, 맨 위에 아래처럼 머리말을 넣습니다.

```yaml
---
title: 문서 제목
parent: Queries    # Queries / Linux / DB Tables 중 하나
nav_order: 2
---
```

SQL은 <code>```sql</code> 로 감싸면 색상이 입혀집니다.

```sql
-- 최근 7일 녹취 건수를 상담사별로 집계
SELECT
    a.agent_id,
    a.agent_name,
    COUNT(*)                AS call_cnt,
    ROUND(AVG(r.duration))  AS avg_sec,
    MAX(r.rec_start_dt)     AS last_call_dt
FROM   rec_master r
JOIN   agent      a  ON a.agent_id = r.agent_id
WHERE  r.rec_start_dt >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND  r.del_yn = 'N'
GROUP BY a.agent_id, a.agent_name
HAVING   COUNT(*) > 10
ORDER BY call_cnt DESC
LIMIT    100;
```

셸 명령은 <code>```bash</code> 로 감쌉니다.

```bash
# 어제자 녹취 파일 용량 확인
find /data/rec/$(date -d yesterday +%Y%m%d) -name '*.wav' -type f \
  | xargs du -ch \
  | tail -1
```

테이블 정의서는 표로 정리합니다.

| 컬럼 | 타입 | NULL | 설명 |
|---|---|---|---|
| `rec_id` | `BIGINT` | N | 녹취 고유 ID (PK) |
| `agent_id` | `VARCHAR(20)` | N | 상담사 ID |
| `rec_start_dt` | `DATETIME` | N | 녹취 시작 시각 |
| `duration` | `INT` | Y | 통화 시간(초) |
| `del_yn` | `CHAR(1)` | N | 삭제 여부 (`Y`/`N`) |
