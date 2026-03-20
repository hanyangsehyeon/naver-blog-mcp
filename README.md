# naver-blog-mcp

Claude Code로 네이버 블로그에 글을 자동으로 작성하고 임시저장하는 MCP 서버.

Claude가 AI 브레인(스타일 분석, 글 변환, 포맷 판단) 역할을 하고, MCP 서버는 Selenium 브라우저 자동화를 담당한다.

## 구조

```
[Claude Code] ←→ [MCP Server] ←→ [Naver Blog (Selenium)]
```

```
naver-blog-mcp/
├── mcp_server/
│   ├── server.py              # MCP 서버 진입점
│   └── tools/
│       ├── blog_analyzer.py   # 블로그 스타일 학습 (크롤링)
│       ├── publisher.py       # 에디터 입력 + 임시저장
│       └── file_tools.py      # 파일 I/O
├── input/                     # 글감 텍스트 파일 넣는 곳
├── output/                    # 변환 결과 JSON (디버그용)
├── style_profile.json         # analyze_blog_style 실행 후 자동 생성
├── formatting_rules.json      # 포맷 우선순위 규칙 (직접 편집)
└── .env                       # NAVER_ID, NAVER_PW, BLOG_ID, MY_BLOG_ID
```

## 설치

```bash
pip install selenium webdriver-manager beautifulsoup4 lxml pyperclip python-dotenv mcp
```

`.env` 파일 생성:
```
NAVER_ID=your_id
NAVER_PW=your_password
BLOG_ID=blog_to_analyze      # 스타일 학습할 블로그 ID
MY_BLOG_ID=blog_to_publish   # 글 올릴 블로그 ID
```

## MCP 서버 등록

`claude_desktop_config.json`에 추가:
```json
{
  "mcpServers": {
    "naver-blog": {
      "command": "python",
      "args": ["mcp_server/server.py"],
      "cwd": "/path/to/naver-blog-mcp"
    }
  }
}
```

## 사용 흐름

1. **스타일 학습** (최초 1회)
   - `analyze_blog_style(blog_id)` — 최근 글 크롤링, `style_profile.json` 생성
   - 학습 내용: 단락 길이, 볼드/형광펜/글자색 예시 텍스트, 사용 색상

2. **글 작성**
   - `input/글감.txt`에 원고 저장
   - Claude에게 "input/글감.txt 블로그 글로 변환해줘" 요청
   - Claude가 `read_file` → `get_style_profile` + `get_formatting_rules` 참고 → 변환 → 확인 요청 → `publish_to_naver`

3. **임시저장 후 직접 발행**
   - 자동화는 임시저장까지만 수행
   - 사진 첨부, 카테고리 설정, 최종 확인 후 직접 발행

## 포맷 규칙 커스터마이징

`formatting_rules.json`을 편집해 강조 우선순위를 직접 설정할 수 있다:

```json
{
  "rules": [
    {
      "priority": 1,
      "name": "핵심 키워드",
      "description": "글에서 가장 중요한 개념, 수치, 결론",
      "formats": ["highlight", "bold"],
      "highlight_color": "#fff8b2"
    },
    {
      "priority": 2,
      "name": "중요 포인트",
      "description": "주의사항, 팁, 핵심 단계",
      "formats": ["text_color", "bold"],
      "text_color": "#e53935"
    },
    {
      "priority": 3,
      "name": "강조 단어",
      "description": "일반 강조, 키워드",
      "formats": ["bold"]
    }
  ]
}
```

규칙: `highlight` 또는 `text_color` 적용 시 `bold`도 자동으로 함께 적용된다.

## MCP 도구 목록

| 도구 | 설명 |
|---|---|
| `analyze_blog_style` | 블로그 크롤링 → 스타일 학습 → `style_profile.json` 저장 |
| `get_style_profile` | `style_profile.json` 반환 (없으면 null) |
| `get_formatting_rules` | `formatting_rules.json` 반환 |
| `read_file` | `input/` 디렉토리에서 파일 읽기 |
| `save_output` | `output/`에 변환 결과 JSON 저장 |
| `publish_to_naver` | 에디터에 제목 + 단락 입력 후 임시저장 |

## 주요 기술 사항

- **포맷 적용 방식**: Smart Editor ONE의 `input_buffer` iframe에 `ClipboardEvent('paste')`로 HTML 주입. toolbar toggle + send_keys 방식은 포맷이 적용되지 않음.
- **로그인**: QR 코드 로그인 방식 (headless=False 필수)
- **임시저장**: "저장" 버튼 텍스트로 탐색
