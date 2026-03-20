# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Naver Blog MCP (Model Context Protocol) server** that automates writing, styling, and publishing content to Naver Blog. Claude Code acts as the AI brain — analyzing style, transforming content, and making decisions — while the MCP server handles side-effecting operations (Selenium browser automation, file I/O).

## Architecture

```
[Claude Code]          ← AI: style analysis, content transformation, decisions
     ↕ MCP protocol
[MCP Server]           ← Tools only: Selenium automation, file I/O
     ↕
[Naver Blog / filesystem]
```

**No separate LLM API calls** — Claude Code itself reads, transforms, and judges content.

### Planned Directory Structure

```
naver-blog-mcp/
├── mcp_server/
│   ├── server.py              # MCP server entrypoint
│   └── tools/
│       ├── blog_analyzer.py   # analyze_blog_style (Selenium + BeautifulSoup)
│       ├── publisher.py       # publish_to_naver (Selenium)
│       └── file_tools.py      # read_file, save_output, get/save style_profile
├── input/                     # Drop raw text files here
├── output/                    # Transformed JSON output (debug/backup)
├── style_profile.json         # Auto-generated after style analysis
└── .env                       # NAVER_ID, NAVER_PW, BLOG_ID
```

## MCP Server Tools

| Tool | Description |
|---|---|
| `analyze_blog_style` | Crawls N recent posts via Selenium, parses Smart Editor ONE HTML, saves `style_profile.json` |
| `get_style_profile` | Returns `style_profile.json` contents (or null if not yet generated) |
| `read_file` | Reads a file from `input/` |
| `publish_to_naver` | Logs into Naver, opens editor, inputs title + paragraphs with formatting, publishes |
| `save_output` | Saves transformed JSON to `output/` for debugging |

## Running the MCP Server

```bash
python mcp_server/server.py
```

Register in `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "naver-blog": {
      "command": "python",
      "args": ["./mcp_server/server.py"],
      "cwd": "/path/to/naver-blog-mcp"
    }
  }
}
```

## Running Tests

```bash
pytest
pytest tests/test_specific.py   # single test file
```

## Tech Stack

| Role | Library |
|---|---|
| MCP server | `mcp` (Anthropic MCP Python SDK) |
| Browser automation | `selenium`, `webdriver-manager` |
| HTML parsing | `beautifulsoup4`, `lxml` |
| Clipboard input | `pyperclip` |
| Env vars | `python-dotenv` |

## Claude Code Workflow (Agent Behavior)

When asked to publish `input/글감.txt`:

1. `read_file("input/글감.txt")` — load raw content
2. `get_style_profile()` — load learned style; if null, run `analyze_blog_style(blog_id=BLOG_ID)` first
3. **Transform content directly** (no API call): apply style rules to produce `paragraphs[]` structure
4. Show transformed result to user and ask "발행할까요?" before publishing
5. `publish_to_naver(title, paragraphs, publish=true)`

## Content Transformation Rules

Apply dynamically using `style_profile.json`:

- **Paragraph splitting**: match `avg_sentences` from profile (typically 2–3 sentences)
- **Bold**: 1–2 key noun/verb phrases per paragraph, per `bold.typical_position`
- **Background color**: apply to tips, conclusions, or important figures — full sentence, not individual words; use colors from `background_colors` list
- **Tone**: follow `tone` field if present; otherwise preserve original

## `style_profile.json` Schema

```json
{
  "analyzed_at": "ISO8601",
  "post_count_analyzed": 10,
  "paragraph": { "avg_sentences": 2.4, "min_sentences": 1, "max_sentences": 3 },
  "bold": { "frequency_ratio": 0.15, "typical_position": "first_sentence_keyword", "avg_per_paragraph": 1.2 },
  "background_colors": ["#FFE6E6", "#FFF9C4"],
  "text_colors": ["#E53935"],
  "tone": "casual_korean",
  "emoji_usage": "moderate",
  "avg_paragraphs_per_post": 8
}
```

## `publish_to_naver` Paragraph Format

```python
paragraphs = [
  {
    "text": "단락 내용",
    "formatting": [
      {"type": "bold", "start": 0, "end": 4},
      {"type": "background", "start": 5, "end": 20, "value": "#FFF9C4"}
    ]
  }
]
```

## Known Technical Issues

| Issue | Solution |
|---|---|
| Text input (send_keys / toolbar) | Only `send_keys` on `input_buffer` iframe body works for plain text. Toolbar toggle + send_keys/paste does NOT apply formatting. |
| **Formatting (bold, bg, color)** | **Use HTML ClipboardEvent paste**: dispatch `ClipboardEvent('paste')` with `DataTransfer` containing `text/html` (e.g. `<b>text</b>`, `<span style="background-color:#fff8b2">text</span>`) inside the iframe. Works for Korean + ASCII. |
| iframe DOM access | Blog main page uses `mainFrame` iframe for post list; post viewer (`PostView.naver?logNo=`) renders content directly — no iframe switch needed for crawling |
| Background color — no hex input | Color picker uses 72 predefined swatches only: `.se-color-palette[title='#hexval']` |
| '내돈내산 기능 이용안내' popup | Appears randomly; click 취소 inside `[class*='layer_popup_wrap']` — ESC does not work. Use `dismiss_naver_popups()` from `tests/common.py` |
| Login CAPTCHA / 2FA | Run `headless=False`, allow manual intervention, then continue |

## Selenium Verification TODO

Each item is a discrete, independently testable unit. Work through them in order — later items depend on earlier ones being confirmed stable. Start all tests with `headless=False` to visually confirm behavior.

### Group 1: Driver Setup

- [ ] **1.1 Basic driver init** — `webdriver.Chrome()` launches without error; `webdriver-manager` resolves correct chromedriver version
- [ ] **1.2 Headless mode** — `--headless=new` flag works; page title readable without visible window
- [ ] **1.3 Non-headless mode** — visible Chrome window opens (required for CAPTCHA/2FA fallback)
- [ ] **1.4 Window size in headless** — `--window-size=1920,1080` prevents viewport-related element visibility issues
- [ ] **1.5 Driver teardown** — `driver.quit()` cleans up without zombie `chromedriver` processes
- [ ] **1.6 `.env` loading** — `python-dotenv` reads `NAVER_ID`, `NAVER_PW`, `BLOG_ID` correctly

### Group 2: Naver Login Flow

- [ ] **2.1 Navigate to login page** — `driver.get("https://nid.naver.com/nidlogin.login")` loads without redirect or block
- [ ] **2.2 ID/PW field locators** — `By.ID "id"` and `"pw"` resolve stably
- [ ] **2.3 `send_keys` on login fields** — characters actually typed (some sites block JS-injected keystrokes)
- [ ] **2.4 `send_keys` JS fallback** — `execute_script` value injection + triggering `input` event gets accepted if 2.3 fails
- [ ] **2.5 Submit button click** — no `ElementNotInteractableException`
- [ ] **2.6 Post-login URL check** — `driver.current_url` does not contain `nidlogin` after submit
- [ ] **2.7 CAPTCHA detection** — identify DOM element/URL pattern signaling CAPTCHA so code can pause for manual resolution
- [ ] **2.8 2FA detection** — identify secondary auth screen; `WebDriverWait` on post-auth element works
- [ ] **2.9 Session persistence** — after login, `driver.get("https://blog.naver.com")` shows logged-in state
- [ ] **2.10 Cookie reuse** — `driver.get_cookies()` save/reload avoids re-login on repeat runs (optional optimization)

### Group 3: Blog Post Crawling (Style Analysis)

- [ ] **3.1 Blog main page load** — `driver.get(f"https://blog.naver.com/{blog_id}")` loads correctly
- [ ] **3.2 Post list selector** — CSS selector/XPath captures N post links from blog main page
- [ ] **3.3 Viewer iframe detection** — `find_element(By.ID, "mainFrame")` present; `switch_to.frame("mainFrame")` works
- [ ] **3.4 Smart Editor ONE DOM in iframe** — `se-text-paragraph` class elements present in `page_source` after iframe switch
- [ ] **3.5 BeautifulSoup parse** — `.se-text-paragraph`, `.se-bold`, inline `background-color` styles parsed correctly
- [ ] **3.6 Switching back from iframe** — `driver.switch_to.default_content()` returns context to outer page
- [ ] **3.7 Crawl rate / bot detection** — rapid sequential `driver.get()` calls don't trigger Naver bot block; determine if `time.sleep` needed
- [ ] **3.8 Login required for crawling** — confirm whether public blog posts are accessible without login

### Group 4: Smart Editor ONE — Text Input

- [ ] **4.1 Navigate to write page** — `driver.get("https://blog.naver.com/PostWriteForm.naver")` while logged in loads editor
- [ ] **4.2 Title field locator** — stable selector for title input/contenteditable element
- [ ] **4.3 Title input via `send_keys`** — no character drops or duplication
- [ ] **4.4 Body editor iframe detection** — selector for editor iframe (different from viewer `mainFrame`)
- [ ] **4.5 Body `contenteditable` locator** — inside editor iframe, find div that accepts text input
- [ ] **4.6 `send_keys` for body text** — single paragraph inserted without dropped characters
- [ ] **4.7 Clipboard paste (`pyperclip` + Ctrl+V)** — text inserted correctly via clipboard
- [ ] **4.8 JS `execCommand('insertText')` fallback** — works when both 4.6 and 4.7 fail
- [ ] **4.9 Paragraph separator via Enter** — `Keys.ENTER` creates a new Smart Editor paragraph block (not just a line break); verify in DOM
- [ ] **4.10 Korean text input** — all three input methods handle Korean (UTF-8 multibyte) without corruption
- [ ] **4.11 Multi-paragraph loop stability** — paste+Enter cycle for 8+ paragraphs doesn't cause focus loss or duplicate blocks

### Group 5: Smart Editor ONE — Formatting (Highest Risk)

- [x] **5.1 JS text range selection** — `window.getSelection()` + `Range` API selects text; JS return value is None but `getSelection().toString()` confirms selection works
- [x] **5.2 Selection survives Python context switch** — JS-set selection persists across Python context switch ✅
- [x] **5.3 Bold via keyboard shortcut** — `Cmd+B` (Mac) after JS selection applies bold; `se-bold` appears in DOM ✅
- [x] **5.4 Bold via toolbar button** — selector: `.se-bold-toolbar-button` ✅
- [x] **5.5 Background color toolbar button locator** — selector: `.se-background-color-toolbar-button` ✅
- [x] **5.6 Color palette dynamic loading** — picker opens as `.se-property-color-picker-container`; use `EC.presence_of_element_located` ✅
- [x] **5.7 Custom hex color input** — ⚠️ NO hex input available; must use 72 predefined swatches only via `.se-color-palette[title='#hexval']`
- [x] **5.8 Background color spans full sentence** — select full paragraph via `range.selectNodeContents(para)` + click `.se-color-palette[title='#fff8b2']` ✅
- [x] **5.9 Formatting on multi-paragraph content** — bold + bg color on separate paragraphs coexist without interference ✅
- [x] **5.10 Text color change** — selector: `.se-font-color-toolbar-button` ✅
- [x] **5.11 Formatting state after paste** — new paragraph does not inherit bold/background from previous ✅
- [ ] **5.12 JS style injection fallback** — ⚠️ Smart Editor ONE blocks direct DOM `insertBefore` manipulation; skip this fallback

### Group 6: Publishing Flow

- [ ] **6.1 Draft save button locator** — stable selector for "임시저장"; distinct from publish button
- [ ] **6.2 Draft save click** — saves without navigating away; DOM shows save confirmation
- [ ] **6.3 Publish button locator** — stable selector for "발행"
- [ ] **6.4 Publish confirmation dialog** — detect if modal appears after clicking publish; identify confirm button selector
- [ ] **6.5 Category / visibility settings** — check if publish flow presents dialogs that must be configured
- [ ] **6.6 Post-publish URL extraction** — resulting post URL accessible via `driver.current_url`, redirect, or DOM element
- [ ] **6.7 Error state detection** — DOM indicators for publish failure (missing title, network error toast)
