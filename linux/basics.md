---
title: 서버 점검 자주 쓰는 명령
eyebrow: shell
subtitle: 디스크·프로세스·로그·네트워크 확인
tag: 기본
---

## 디스크

```bash
# 파티션별 사용량 (타입 포함)
df -hT

# 현재 폴더에서 용량 큰 것 TOP 10
du -sh ./* 2>/dev/null | sort -rh | head -10

# 특정 폴더 아래 1G 넘는 파일
find /appdata -type f -size +1G -exec ls -lh {} \;

# 삭제했는데 용량이 안 줄 때 — 프로세스가 붙잡고 있는 파일
lsof +L1 | head
```

## 프로세스

```bash
# 메모리 많이 쓰는 순
ps aux --sort=-%mem | head -10

# CPU 많이 쓰는 순
ps aux --sort=-%cpu | head -10

# 특정 프로세스 찾기 (grep 자기 자신 제외)
ps -ef | grep -v grep | grep <이름>

# 실행 중인 프로세스의 실제 경로·작업폴더
ls -l /proc/<PID>/exe /proc/<PID>/cwd
```

## 로그

```bash
# 실시간 추적 (여러 파일 동시)
tail -f /applog/*.log

# 에러만 실시간으로
tail -f app.log | grep --line-buffered -iE 'error|exception|fail'

# 특정 날짜 구간만
sed -n '/2026-08-28 09:00/,/2026-08-28 10:00/p' app.log

# 오늘 에러 횟수를 메시지별로 집계
grep "$(date +%Y-%m-%d)" app.log | grep -i error \
  | awk -F'ERROR' '{print $2}' | sort | uniq -c | sort -rn | head
```

## 네트워크

```bash
# 리스닝 포트 + 프로세스
ss -lntp

# 특정 포트를 누가 쓰는지
ss -lntp | grep :3306

# 연결 상태별 개수
ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn

# 방화벽 열린 포트
firewall-cmd --list-all
```

## 서비스

```bash
systemctl status  <서비스>
systemctl restart <서비스>
systemctl enable  <서비스>          # 부팅 시 자동 시작
journalctl -u <서비스> -n 100 --no-pager
journalctl -u <서비스> --since "1 hour ago"
```

## 파일 찾기

```bash
# 이름으로
find /app -name '*.jar' -type f

# 최근 1일 안에 변경된 파일
find /app -type f -mtime -1

# 내용으로 (바이너리 제외, 파일명만)
grep -rIl 'keyword' /app --include='*.ini'
```

## 압축

```bash
tar -czvf backup_$(date +%Y%m%d).tar.gz <폴더>   # 압축
tar -xzvf backup.tar.gz -C /복원경로              # 해제
tar -tzvf backup.tar.gz | head                    # 내용만 확인
```

> 운영 서버에서 `find /` 처럼 루트 전체를 훑으면 부하가 큽니다. 경로를 좁혀서 쓰세요.
