# 네이버 블로그 MCP

Gemini CLI를 두뇌로, MCP 서버를 손발로 사용하는 네이버 블로그 자동화 도구입니다.
외부 API 키 없이 Gemini CLI의 언어 능력으로 스타일 학습과 글 변환을 수행합니다.

## 구조

```
Gemini CLI (두뇌)
  ├─ 블로그 글 분석 → 스타일 가이드 작성
  └─ 줄글 → 블로그 JSON 변환

MCP 서버 (손발)
  ├─ learn_blog_style   : 블로그 크롤링
  ├─ read_file          : 스타일 가이드 로드
  ├─ save_file          : 스타일 가이드 저장
  ├─ fetch_raw_posts    : 개별 게시글 크롤링
  └─ publish_to_naver   : Selenium으로 발행
```

## 설치

```bash
pip install -r requirements.txt
playwright install chromium
```

## 실행

프로젝트 루트에서 Gemini CLI 실행:
```bash
gemini
```

`.gemini/settings.json`에 MCP 서버가 등록되어 있어 자동으로 연결됩니다.

## 사용법

### 스타일 학습 (최초 1회)

```
learn_blog_style 도구로 https://blog.naver.com/YOUR_ID 블로그 글 20개를 크롤링하고,
분석해서 ./data/style_guide.json에 저장해줘
```

### 글 변환 및 발행

```
[줄글 붙여넣기]
위 내용을 내 블로그 스타일로 변환하고 발행해줘
```

## 파일 구조

```
naver-blog-mcp/
├── .gemini/
│   └── settings.json       # MCP 서버 연결 설정
├── GEMINI.md               # Gemini CLI 시스템 프롬프트 (자동 로드)
├── data/
│   └── style_guide.json    # 학습된 스타일 가이드
├── src/
│   ├── server.py           # MCP 서버 진입점
│   ├── crawler/
│   │   └── naver_crawler.py
│   ├── selenium_driver/
│   │   ├── driver.py
│   │   ├── login.py
│   │   └── editor.py
│   └── tools/
│       ├── file_io.py
│       ├── learner.py
│       └── publisher.py
└── requirements.txt
```
