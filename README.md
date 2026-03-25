# naver-blog-mcp

Claude Code로 네이버 블로그에 글을 자동으로 작성하고 임시저장하는 MCP 서버.

Claude가 AI 브레인(글 변환, 서식 결정) 역할을 하고, MCP 서버는 Selenium 브라우저 자동화를 담당한다.

## 구조

```
[Claude Code] ←→ [MCP Server] ←→ [Naver Blog (Selenium)]
```

```
naver-blog-mcp/
├── mcp_server/
│   ├── server.py
│   └── tools/
│       ├── blog_analyzer.py   # 블로그 크롤링 (카테고리, URL 수집, 포스트 파싱)
│       ├── publisher.py       # 에디터 입력 + 임시저장
│       └── file_tools.py      # 파일 I/O
├── examples/                  # 크롤링된 포스트 JSON (few-shot 데이터)
│   └── {blog_id}/{category}/YYYYMMDD.json
├── url_index/                 # 카테고리별 URL 인덱스
│   └── {blog_id}.json
├── input/                     # 글감 hwpx 파일
├── drafts/                    # hwpx → txt 변환 결과
├── output/                    # 변환 결과 JSON (디버그용)
├── formatting_rules.json      # 서식 우선순위 규칙
└── .env
```

## 설치

```bash
pip install selenium webdriver-manager beautifulsoup4 lxml python-dotenv mcp
```

`.env` 파일 생성:
```
STANDARD_BLOG_ID=스타일_참고할_블로그_ID
MY_BLOG_ID=글_올릴_내_블로그_ID
```

## MCP 서버 등록

`.mcp.json` 또는 `claude_desktop_config.json`:
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

### 1. 예시 파일 준비 (최초 1회)

Claude Code에서:
```
{blog_id} 블로그의 카테고리 목록 보여줘
→ tool_get_blog_categories

"{category}" 카테고리 URL 수집해줘
→ tool_fetch_post_urls

수집된 URL 기반으로 examples 저장해줘
→ tool_create_examples
```

### 2. 글 작성 및 발행

```
input/글감.txt를 "{category}" 스타일로 변환해서 {blog_id}에 임시저장해줘
```

Claude가 자동으로:
1. 글감 로드
2. examples/ 참고해서 단락 분리 + 서식 적용
3. 변환 결과 확인 요청
4. 에디터에 붙여넣고 임시저장

임시저장 후 사진 첨부, 카테고리 설정, 최종 발행은 직접 진행.

## MCP 도구 목록

| 도구 | 설명 |
|---|---|
| `tool_get_blog_categories` | 전체 카테고리 목록 반환 |
| `tool_fetch_post_urls` | 카테고리별 URL 수집 → url_index 저장 |
| `tool_create_examples` | URL 기반 포스트 크롤링 → examples 저장 |
| `tool_get_formatting_rules` | formatting_rules.json 반환 |
| `tool_convert_hwpx` | input/{file}.hwpx → drafts/{file}.txt 변환 |
| `tool_read_file` | drafts/ txt 파일 읽기 |
| `tool_save_output` | output/ 에 JSON 저장 |
| `tool_publish_to_naver` | 에디터 입력 + 임시저장 |

## 서식 규칙 커스터마이징

`formatting_rules.json` 직접 편집:

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
      "formats": ["text_color", "bold"],
      "text_color": "#e53935"
    }
  ]
}
```

`highlight` 또는 `text_color` 적용 시 `bold`도 자동으로 함께 적용된다.
