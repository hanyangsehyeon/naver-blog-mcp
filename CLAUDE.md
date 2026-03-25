# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Naver Blog MCP server** — Claude Code acts as the AI brain (content transformation, formatting decisions) while the MCP server handles side-effecting operations (Selenium browser automation, file I/O).

## Architecture

```
[Claude Code]          ← AI: content transformation, formatting decisions
     ↕ MCP protocol
[MCP Server]           ← Tools only: Selenium automation, file I/O
     ↕
[Naver Blog / filesystem]
```

**No separate LLM API calls** — Claude Code itself reads, transforms, and judges content.

## Directory Structure

```
naver-blog-mcp/
├── mcp_server/
│   ├── server.py              # MCP server entrypoint (FastMCP)
│   └── tools/
│       ├── blog_analyzer.py   # Selenium crawl + BeautifulSoup parse
│       ├── publisher.py       # publish_to_naver: Selenium editor input + draft save
│       └── file_tools.py      # read_file, save_output, formatting_rules I/O
├── blog_structure/            # DOM 구조 레퍼런스 문서
│   └── treetop0120_main_page.md
├── examples/                  # 크롤링된 포스트 JSON (few-shot 데이터)
│   └── {blog_id}/
│       └── {category_name}/
│           └── YYYYMMDD.json
├── url_index/                 # 카테고리별 URL 인덱스
│   └── {blog_id}.json
├── input/                     # 글감 hwpx 파일
├── drafts/                    # hwpx → txt 변환 결과
├── output/                    # 변환 결과 JSON (디버그/백업용)
├── tests/                     # 디버그 스크립트
│   ├── common.py
│   ├── debug_category_posts.py
│   ├── debug_naiui_category.py
│   ├── debug_create_examples.py
│   └── debug_publisher.py
├── formatting_rules.json      # 서식 우선순위 규칙 (직접 편집)
└── .env                       # STANDARD_BLOG_ID, MY_BLOG_ID
```

## MCP Server Tools

| Tool | Description |
|---|---|
| `tool_get_blog_categories` | 블로그의 전체 카테고리 목록 반환 `{name: categoryNo}` |
| `tool_fetch_post_urls` | 선택한 카테고리의 포스트 URL 수집 → `url_index/{blog_id}.json` 저장 |
| `tool_create_examples` | url_index 기반으로 포스트 크롤링 → `examples/{blog_id}/{category}/YYYYMMDD.json` 저장 |
| `tool_get_formatting_rules` | `formatting_rules.json` 반환 |
| `tool_convert_hwpx` | `input/{file}.hwpx` → `drafts/{file}.txt` 변환 |
| `tool_read_file` | `drafts/` 에서 txt 파일 읽기 |
| `tool_save_output` | 변환된 JSON을 `output/` 에 저장 (디버깅용) |
| `tool_publish_to_naver` | 에디터 열고 제목 + 단락 입력 후 임시저장 |

## Claude Code Workflow

### 글감 포스팅 흐름

1. 사용자에게 블로그 ID와 카테고리 확인
2. `tool_convert_hwpx` — `input/` 의 hwpx 파일을 `drafts/` 에 txt로 변환
3. `tool_read_file` — `drafts/` 에서 변환된 txt 로드
4. `tool_get_formatting_rules` — 서식 우선순위 규칙 로드
5. `examples/{blog_id}/{category}/` 에서 대표 예시 2~3개 직접 읽기
6. **직접 변환**: 예시 스타일 + formatting_rules 적용해서 `paragraphs[]` 생성
7. 변환 결과 사용자에게 보여주고 확인 받기
8. **발행 전 반드시 확인**: "어느 블로그에 발행할까요? (blog_id: {MY_BLOG_ID})" 라고 물어볼 것
9. `tool_publish_to_naver(blog_id, title, paragraphs)` — 임시저장

### 예시 파일 준비 (최초 1회)

```
1. tool_get_blog_categories(blog_id)        # 카테고리 목록 확인
2. tool_fetch_post_urls(blog_id, [cat])     # URL 수집
3. tool_create_examples(blog_id, [cat])     # 포스트 크롤링 + 저장
```

## Content Transformation Rules

`examples/{blog_id}/{category}/` 파일들과 `formatting_rules.json` 기반으로 적용:

- **단락 분리**: 1~2문장 단위로 짧게
- **Bold**: 강조할 핵심 문구에 적용
- **Highlight** (배경색): 중요 문장 전체에 적용, 색상은 examples에서 사용된 색 참고
- **Text color**: 보조 강조, 색상은 examples에서 사용된 색 참고
- **규칙**: `highlight` 또는 `text_color` 적용 시 항상 `bold`도 함께
- **서식 우선순위**: `formatting_rules.json` `rules[].priority` 순서 따름

## Formatting Index Rules (CRITICAL)

`start`/`end`는 **Python slice 방식 (exclusive end)** 으로 동작한다.
`text[start:end]` 가 실제 서식이 적용되는 문자열이다.

```python
text = "이 낯선 흙이 나를 밀어내지 않을 것이라는 '심리적 안전함'입니다."
#                                          22 24        33
# text[22:31] == "는 '심리적 안전"   ← 잘못된 예시 (는+공백 포함, 함 빠짐)
# text[24:33] == "'심리적 안전함'"   ← 올바른 예시
```

**인덱스 생성 절차** (서식 적용할 문자열 범위 지정 시):
1. `text.index(target_string)` 로 start 계산
2. `end = start + len(target_string)` 로 end 계산
3. **반드시 `text[start:end] == target_string` 검증 후 사용**

절대 직접 숫자를 세지 말 것 — 반드시 위 계산식으로 도출할 것.

## Paragraph Format

```python
paragraphs = [
  {
    "text": "단락 내용",
    "formatting": [
      {"type": "bold", "start": 0, "end": 4},
      {"type": "highlight", "start": 5, "end": 20, "color": "#fff8b2"},
      {"type": "text_color", "start": 0, "end": 10, "color": "#387cbb"}
    ]
  }
]
```

`highlight` 또는 `text_color` 적용 시 `_build_html()`이 자동으로 `bold`도 함께 적용.

## Naver Blog HTML Structure Reference

### Blog Main Page — 포스트 목록

상세 DOM 구조: `blog_structure/treetop0120_main_page.md`

**요점**:
- 카테고리별 포스트 목록: `PostList.naver?blogId={id}&from=postList&categoryNo={no}` 로 직접 접근 (iframe 불필요)
- 카테고리 전체 목록: 블로그 메인 `mainFrame` iframe 내 `a[href*='from=postList'][href*='categoryNo=']`
- 포스트 링크: `#postListBody li.item > a.link`
- 목록열기: `#toplistSpanBlind` → `a.btn_openlist`
- toplist 링크: `#toplistWrapper a._setTopListUrl`

### Smart Editor ONE — 에디터

**접근 URL**: `https://blog.naver.com/PostWriteForm.naver?blogId={blog_id}`

- 제목: `.se-title-text` 클릭 → `input_buffer[0]` iframe → `send_keys`
- 본문: 모든 단락을 `<div>` 블록으로 묶어 ClipboardEvent paste 1회
- 임시저장: 텍스트 "저장" / "임시저장" 버튼

### Post Viewer — 크롤링 selector

| 역할 | Selector |
|---|---|
| 단락 블록 | `.se-text-paragraph` |
| 인라인 배경색 | `span[style*='background-color']` |
| 인라인 글자색 | `span[style*='color']` |
| 게시일 | `.se_publishDate`, `.blog_date`, `.se-date` 순서로 시도 |

### Common Popups

`dismiss_naver_popups()` (in `tests/common.py`) 로 처리:

| 팝업 | 처리 |
|---|---|
| "작성 중인 글" | `.se-popup-button-cancel` 클릭 |
| "도움말" 패널 | `.se-help-panel-close-button` 클릭 |
| "내돈내산 기능 이용안내" | `[class*='layer_popup_wrap']` 취소 버튼 클릭 (ESC 불가) |

## Known Technical Issues

| Issue | Solution |
|---|---|
| **서식 적용** | toolbar toggle + send_keys 불가. HTML ClipboardEvent paste 사용 |
| **다중 단락 서식 블리드** | 각 단락을 `<div>`로 감싸 일괄 paste 1회 |
| **iframe DOM 접근** | 블로그 메인은 `mainFrame` iframe 전환 필요; PostList/PostView 직접 접근 시 불필요 |
| **로그인** | QR 코드 로그인 (`headless=False` 필수), URL 수집/크롤링은 로그인 불필요 |
| **한글 입력** | `send_keys` 대신 ClipboardEvent HTML paste — 문자 손상 없음 |
| **30줄 보기** | `listCountToggle` 클릭 후 frame 재진입 금지 — 카테고리 필터 리셋됨 |

## 추후 개선 사항

- **벡터 유사도 기반 few-shot 선택**: 글감 내용과 가장 유사한 examples/ 파일을 자동으로 찾아 Claude에게 전달 (현재는 수동으로 카테고리 지정)
