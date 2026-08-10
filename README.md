# 1페이지 정적 블로그

실제 웹페이지는 **`site/index.html` 1개만** 생성합니다. 여러 글은 모두 이 한 페이지 안에 쌓이며, 상단 글 목록에서 각 글의 앵커로 이동합니다.

## 파일 역할

- `content/*.md` : 게시글 원고
- `site/index.html` : 유일한 웹페이지
- `site/posts.json` : 게시글 목록 관리 데이터
- `site/sitemap.xml` : 검색엔진 사이트맵 — 홈페이지 URL 1개만 포함
- `site/robots.txt` : 검색로봇 정책
- `site/rss.xml` : RSS
- `site/style.css` : 스타일시트

## 글 추가

`content` 폴더에 Markdown 파일을 추가합니다.

```text
---
title: 글 제목
date: 2026-08-10
description: 글 설명
slug: my-post
tags: 기록, 일상
---

본문을 Markdown으로 작성합니다.
```

그리고 실행합니다.

```bash
python3 build.py
```

별도의 `posts/*.html`은 생성되지 않습니다. 글 주소는 `https://도메인/#my-post` 형태입니다.

## 최초 설정

`config.json`의 `base_url`을 실제 배포 도메인으로 변경하세요.

```json
"base_url": "https://example.com"
```

네이버 서치어드바이저 메타태그 인증을 이용할 경우 `naver_site_verification`에 발급된 content 값만 입력합니다.

## Vercel

- Build Command: `python3 build.py`
- Output Directory: `site`

## Netlify

- Build command: `python3 build.py`
- Publish directory: `site`

## 네이버 서치어드바이저

배포 후 다음 URL이 정상적으로 열리는지 확인합니다.

- `/`
- `/robots.txt`
- `/sitemap.xml`
- `/rss.xml`

`sitemap.xml`에는 웹페이지가 하나뿐이므로 홈페이지 URL만 등록됩니다.
