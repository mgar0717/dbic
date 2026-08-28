# dbic

쿼리, 리눅스 명령어 정리 등 개인 지식/문서 저장소.

> 사내 시스템 정보(스키마·서버 주소 등)는 이 공개 저장소에 두지 않습니다.
> 그런 문서는 오프라인 단일 HTML 파일로 따로 보관합니다.

웹으로 보기 → **https://mgar0717.github.io/dbic/**

`main` 에 push 하면 GitHub Pages 가 자동으로 재빌드·배포합니다.

## 구성

- `queries/` — SQL 쿼리 모음
- `linux/` — 리눅스 명령어·문법 정리
- `_layouts/`, `_includes/`, `assets/` — 사이트 테마 (외부 테마 없이 직접 구성)

## 문서 추가하기

해당 폴더에 `.md` 파일을 만들고 머리말을 넣습니다. 목록 카드와 헤더가 자동으로 만들어집니다.

```yaml
---
layout: page
title: 문서 제목
eyebrow: sql          # 헤더 위 작은 라벨 (선택)
subtitle: 한 줄 설명   # 목록 카드에도 표시 (선택)
tag: 집계             # 목록 카드의 배지 (선택)
---
```

형식 예시는 `queries/sample.md` 참고.


## 로컬에서 미리보기

```bash
gem install jekyll
cp _config.yml _config.local.yml
jekyll build --config _config.local.yml -d _site
# baseurl 이 /dbic 이므로 상위 폴더에 dbic 이름으로 두고 서빙
mkdir -p .serve && cp -r _site .serve/dbic && (cd .serve && python3 -m http.server 8899)
# → http://127.0.0.1:8899/dbic/
```
