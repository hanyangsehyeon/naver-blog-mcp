# 네이버 블로그 MCP 서버 프로젝트 계획서

## 📌 프로젝트 개요

### 핵심 아이디어
**사람이 쓴 줄글 → MCP가 Gemini에게 블로그 형식 변환 요청 → Selenium 자동 발행**

### 왜 이렇게?
- 블로그 글은 단순 텍스트가 아님
- 단락 나누기, 볼드, 인용구, 정보 박스 필요
- 내 기존 블로그 스타일을 따라야 함
- **이 모든 걸 AI(Gemini)가 기존 글 보고 학습해서 처리**

### 작업 흐름
```
[최초 1회] 스타일 학습
  - 기존 블로그 20개 크롤링
  - Gemini가 "스타일 가이드" 생성 (압축!)
  - JSON 저장 (작은 파일)
  ↓
[평소 사용]
사람: 줄글 작성 (메모장에)
  ↓
Gemini CLI: "이 글 블로그에 올려줘"
  ↓
MCP 서버:
  1. 스타일 가이드 로드 (작은 파일!)
  2. Gemini API 호출:
     "이 줄글을 스타일 가이드에 맞춰 블로그 형식으로 바꿔줘"
  3. Gemini가 블로그 형식으로 재구성
     - 단락 나누기
     - 볼드/하이라이트 표시
     - 인용구 추출
     - 정보 박스 생성
  4. Selenium으로 네이버 발행
  ↓
완료!
```

**장점**: 매번 레퍼런스 3개씩 프롬프트에 넣지 않아서 **토큰 90% 절감!**

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────┐
│          사용자 (Gemini CLI)             │
│                                          │
│  "오늘 제주도 다녀왔다. 맛집 찾았는데    │
│   가성비 좋았고 분위기도 좋았다..."      │
│                                          │
│  → 이거 블로그에 올려줘                  │
└──────────────┬──────────────────────────┘
               │
               ↓ MCP Protocol
┌─────────────────────────────────────────┐
│       네이버 블로그 MCP 서버              │
│                                          │
│  [1단계] 스타일 가이드 로드 (1회 학습됨)  │
│    style_guide.json 파일 읽기            │
│    - 톤앤매너: "반말체, 이모지 많이"     │
│    - 단락: "2-3문장씩"                   │
│    - 볼드: "숫자, 강조어"                │
│    - 하이라이트: "결론 문장"             │
│    (작은 파일! ~500 토큰)                │
│                                          │
│  [2단계] Gemini API 호출                 │
│    - 프롬프트 구성:                      │
│      "스타일 가이드에 맞춰 변환해줘"     │
│      [스타일 가이드 JSON]                │
│      [변환할 줄글]                       │
│    - Gemini가 블로그 형식으로 재구성     │
│                                          │
│  [3단계] Selenium 발행                   │
│    - 네이버 로그인                       │
│    - 에디터 조작                         │
│    - 자동 발행                           │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│         네이버 블로그                    │
│  ✓ 단락 잘 나뉨                          │
│  ✓ 볼드/하이라이트 적용됨                │
│  ✓ 인용구 박스 있음                      │
│  ✓ 내 기존 스타일과 일관성 유지          │
└─────────────────────────────────────────┘
```

---

## 🛠️ MCP 도구 설계

### Tool 1: `learn_blog_style` - 스타일 가이드 생성 (1회 또는 업데이트 시) ⭐ 핵심
```python
@mcp_tool
def learn_blog_style(blog_url: str, num_posts: int = 20, force_update: bool = False) -> str:
    """
    내 네이버 블로그 글들을 분석해서 압축된 '스타일 가이드' 생성
    
    Args:
        blog_url: 네이버 블로그 URL
        num_posts: 분석할 글 개수 (기본 20개)
        force_update: 기존 가이드 덮어쓰기 (기본 False)
    
    Returns:
        "스타일 가이드 생성 완료!"
    
    처리 과정:
    1. Playwright로 블로그 크롤링 (20개 글)
    
    2. Gemini API 호출로 스타일 분석:
       프롬프트: "아래 20개 블로그 글을 분석해서 
                 압축된 스타일 가이드를 JSON으로 만들어줘"
       
    3. 생성되는 스타일 가이드 예시:
       {
         "tone": "친근한 반말체, 이모지 자주 사용 (😊✨🎉)",
         "structure": {
           "paragraph_length": "2-3문장",
           "paragraph_break": "주제 전환 시, 3문장 이상 시",
           "intro_style": "개인 경험이나 질문으로 시작",
           "conclusion_style": "추천 + 질문 유도"
         },
         "formatting": {
           "bold": [
             "숫자 포함 표현 (3만원, 5개)",
             "가성비, 맛집, 추천 같은 핵심 키워드",
             "정말, 완전, 대박 강조 부사"
           ],
           "highlight": "결론 문장, 당위 표현",
           "quote": "거의 사용 안 함",
           "info_box": "위치/가격/영업시간 테이블로"
         },
         "examples": {
           "good_intro": "오늘 소개할 곳은 정말 숨은 맛집!",
           "good_conclusion": "꼭 가보세요! 후회 안 해요 😊"
         }
       }
    
    4. style_guide.json 파일로 저장 (매우 작음!)
    
    토큰 절감 효과:
    - 기존: 레퍼런스 3개 = ~5,000 토큰/회
    - 개선: 스타일 가이드 = ~500 토큰/회
    - 90% 절감!

### Tool 2: `convert_to_blog` - 줄글을 블로그로 변환 (스타일 가이드 활용)
```python
@mcp_tool
def convert_to_blog(raw_text: str) -> dict:
    """
    줄글을 블로그 형식으로 변환 (저장된 스타일 가이드 활용)
    
    Args:
        raw_text: 사용자가 작성한 줄글
    
    Returns:
        {
            "title": "생성된 제목",
            "content": [
                {"type": "paragraph", "text": "...", "formatting": [...]},
                {"type": "quote", "text": "인용구"},
                {"type": "info_box", "items": {"위치": "...", "가격": "..."}}
            ]
        }
    
    처리 과정:
    1. style_guide.json 파일 로드 (작은 파일!)
    
    2. Gemini API 호출:
       
       프롬프트:
       "당신은 블로그 글 포맷터입니다.
        아래 스타일 가이드를 따라 줄글을 블로그 형식으로 변환하세요.
        
        # 스타일 가이드
        {스타일 가이드 JSON - 500 토큰 정도}
        
        # 변환 규칙
        - 톤: {tone}
        - 단락: {paragraph_length}씩 나누기
        - 볼드: {bold 패턴들}
        - 하이라이트: {highlight 조건}
        
        # 예시
        도입부: {good_intro}
        결론부: {good_conclusion}
        
        # 변환할 줄글
        {raw_text}
        
        # 출력: JSON만"
    
    3. Gemini 응답을 파싱
    4. 네이버 에디터 형식으로 재구성
    
    토큰 사용:
    - 스타일 가이드: ~500 토큰
    - 줄글: ~500 토큰
    - 총: ~1,000 토큰 (기존 5,500 대비 80% 절감!)
    """
```

**핵심 차이점:**
- ❌ 기존: 레퍼런스 3개 HTML 전체를 매번 프롬프트에 포함 (5,000 토큰)
- ✅ 개선: 압축된 스타일 가이드만 포함 (500 토큰)
- **Gemini가 스타일 가이드를 보고 패턴 학습 → 줄글에 적용**

### Tool 3: `publish_to_naver` - 네이버 발행
```python
@mcp_tool
def publish_to_naver(blog_content: dict, preview: bool = True) -> str:
    """
    변환된 글을 네이버 블로그에 발행
    
    Args:
        blog_content: convert_to_blog의 결과물
        preview: 미리보기 할지 여부
    
    Returns:
        발행된 URL
    
    처리:
    1. Selenium 초기화
    2. 네이버 로그인
    3. 글쓰기 에디터 열기
    4. content 배열 순회하며 요소 추가:
       - paragraph: 텍스트 입력 + 볼드 적용
       - quote: 인용구 박스 삽입
       - info_box: 표 삽입
    5. 미리보기 (선택)
    6. 발행
    """
```

---

## 💻 핵심 구현

### 1. 스타일 가이드 생성 (learn_blog_style)

```python
from google import generativeai as genai
import json

class StyleLearner:
    """블로그 스타일 분석 → 압축된 가이드 생성"""
    
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def learn(self, blog_url: str, num_posts: int = 20) -> dict:
        """
        블로그 크롤링 → Gemini로 스타일 분석 → 가이드 생성
        """
        # 1. 블로그 크롤링
        posts = self._crawl_blog(blog_url, num_posts)
        
        # 2. Gemini에게 스타일 분석 요청
        prompt = self._build_analysis_prompt(posts)
        response = self.model.generate_content(prompt)
        
        # 3. 스타일 가이드 파싱
        style_guide = json.loads(response.text)
        
        # 4. 저장
        with open("./data/style_guide.json", "w", encoding="utf-8") as f:
            json.dump(style_guide, f, ensure_ascii=False, indent=2)
        
        return style_guide
    
    def _build_analysis_prompt(self, posts: list) -> str:
        """
        Gemini에게 보낼 분석 프롬프트
        """
        
        # 블로그 글들을 간단히 포맷팅
        posts_text = ""
        for i, post in enumerate(posts[:20], 1):
            posts_text += f"\n## 글 {i}: {post['title']}\n{post['html'][:1000]}...\n"
        
        prompt = f"""당신은 블로그 스타일 분석 전문가입니다.
아래 20개의 블로그 글을 분석해서 **압축된 스타일 가이드**를 만드세요.

**중요**: 전체 글을 포함하지 말고, **패턴만** 추출하세요!

# 분석할 블로그 글들
{posts_text}

# 출력 형식 (JSON만 출력)

{{
  "tone": "말투, 어미, 이모지 사용 패턴 요약 (한 줄)",
  "structure": {{
    "paragraph_length": "평균 몇 문장인지",
    "paragraph_break": "언제 단락을 나누는지",
    "intro_style": "도입부 스타일 (예: 질문으로 시작)",
    "conclusion_style": "결론부 스타일 (예: 추천 + 질문)"
  }},
  "formatting": {{
    "bold": [
      "어떤 단어/표현에 볼드를 쓰는지 (패턴 3-5개)",
    ],
    "highlight": "어떤 문장을 하이라이트하는지",
    "quote": "인용구 사용 여부 및 패턴",
    "info_box": "정보 박스 사용 여부 및 형식"
  }},
  "examples": {{
    "good_intro": "실제 도입부 예시 한 문장",
    "good_conclusion": "실제 결론부 예시 한 문장"
  }}
}}

**중요**: 반드시 위 JSON 형식으로만 출력하세요.
"""
        return prompt


def learn_blog_style(blog_url: str, force_update: bool = False) -> str:
    """MCP Tool 함수"""
    
    # 이미 스타일 가이드가 있으면 스킵
    if not force_update and os.path.exists("./data/style_guide.json"):
        return "✅ 이미 학습된 스타일이 있습니다. force_update=True로 재학습 가능"
    
    learner = StyleLearner()
    style_guide = learner.learn(blog_url)
    
    return f"✅ 스타일 가이드 생성 완료! (파일 크기: ~{len(json.dumps(style_guide))} bytes)"
```

### 2. 줄글 변환 (convert_to_blog)

```python
class BlogConverter:
    """스타일 가이드 활용해서 줄글 → 블로그 변환"""
    
    def __init__(self, style_guide_path="./data/style_guide.json"):
        # 스타일 가이드 로드
        with open(style_guide_path, 'r', encoding='utf-8') as f:
            self.style_guide = json.load(f)
        
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def convert(self, raw_text: str) -> dict:
        """
        줄글 → 블로그 형식 변환
        """
        # 1. 프롬프트 구성 (스타일 가이드 활용)
        prompt = self._build_conversion_prompt(raw_text)
        
        # 2. Gemini API 호출
        response = self.model.generate_content(prompt)
        
        # 3. JSON 파싱
        try:
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            
            blog_content = json.loads(result_text)
            return blog_content
        
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 실패: {e}")
            raise
    
    def _build_conversion_prompt(self, raw_text: str) -> str:
        """
        스타일 가이드 활용한 변환 프롬프트
        """
        
        sg = self.style_guide  # 축약
        
        prompt = f"""당신은 블로그 글 포맷터입니다.
아래 스타일 가이드를 **정확히** 따라 줄글을 블로그 형식으로 변환하세요.

# 스타일 가이드

**톤앤매너**: {sg['tone']}

**구조**:
- 단락 길이: {sg['structure']['paragraph_length']}
- 단락 나누기: {sg['structure']['paragraph_break']}
- 도입부: {sg['structure']['intro_style']}
- 결론부: {sg['structure']['conclusion_style']}

**서식**:
- 볼드: {', '.join(sg['formatting']['bold'])}
- 하이라이트: {sg['formatting']['highlight']}
- 인용구: {sg['formatting']['quote']}
- 정보 박스: {sg['formatting']['info_box']}

**예시**:
- 좋은 도입부: "{sg['examples']['good_intro']}"
- 좋은 결론부: "{sg['examples']['good_conclusion']}"

# 변환할 줄글

{raw_text}

# 출력 형식 (JSON만)

{{
  "title": "생성된 제목 (30자 이내, 이모지 가능)",
  "content": [
    {{
      "type": "paragraph",
      "text": "단락 텍스트",
      "formatting": [
        {{"start": 0, "end": 5, "type": "bold"}},
        {{"start": 10, "end": 20, "type": "highlight", "color": "yellow"}}
      ]
    }},
    {{
      "type": "quote",
      "text": "인용구"
    }},
    {{
      "type": "info_box",
      "items": {{"위치": "...", "가격": "...", "영업시간": "..."}}
    }}
  ]
}}

**중요**: JSON만 출력. 다른 설명 불필요.
"""
        return prompt


def convert_to_blog(raw_text: str) -> dict:
    """MCP Tool 함수"""
    converter = BlogConverter()
    return converter.convert(raw_text)
```

### 토큰 사용량 비교

```python
# 기존 방식 (레퍼런스 3개 직접 포함)
prompt_tokens = {
    "reference_1_html": 1500,
    "reference_2_html": 1500,
    "reference_3_html": 1500,
    "instructions": 500,
    "raw_text": 500,
}
# 총: 5,500 토큰

# 개선 방식 (스타일 가이드)
prompt_tokens_new = {
    "style_guide_json": 500,  # 압축됨!
    "instructions": 300,
    "raw_text": 500,
}
# 총: 1,300 토큰

# 절감률: (5500 - 1300) / 5500 = 76% 절감!
```

---

## 🔌 Gemini CLI 연동

### MCP 설정 파일

**위치**: Gemini CLI의 MCP 설정 경로

```json
{
  "mcpServers": {
    "naver-blog": {
      "command": "python",
      "args": ["/path/to/naver-blog-mcp/src/server.py"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key",
        "NAVER_ID": "your-naver-id"
      }
    }
  }
}
```

---

## 🎬 실제 사용 흐름

### 1단계: 스타일 학습 (최초 1회)

```bash
gemini

> 내 블로그 학습해줘
> https://blog.naver.com/myid

[MCP: learn_blog_style 실행]
✓ 블로그 크롤링 중... (20개 글)
✓ Gemini에게 스타일 분석 요청...
✓ 압축된 스타일 가이드 생성!
✓ style_guide.json 저장 (약 2KB)

비용: ~300원 (1회만!)

> 학습 완료! 이제 글을 변환할 수 있어요.
```

### 2단계: 줄글 변환 + 발행 (평소)

```bash
> 이 글 블로그에 올려줘:
>
> 오늘 홍대에서 브런치 카페 발견했다. 이름은 "모닝글로리"인데 
> 분위기가 정말 좋았다. 에그베네딕트 먹었는데 가격은 15000원. 
> 양도 많고 맛도 좋았다. 라떼도 주문했는데 라떼아트가 예뻤다.
> 인테리어는 화이트톤에 식물이 많았고 창가 자리가 특히 좋았다.
> 영업시간은 9시부터 6시까지. 주차는 안되니까 대중교통 추천한다.
> 주말엔 웨이팅 있을 수 있으니 평일 가는 게 좋을 것 같다.

[MCP: convert_to_blog 실행]
✓ style_guide.json 로드 (작은 파일!)
✓ Gemini에게 변환 요청... (토큰 적게 씀!)
✓ 블로그 형식으로 재구성 완료!

비용: ~10원 (매번)

제목: 홍대 브런치 카페 "모닝글로리" 후기 ☕✨

단락 구성:
- 도입부 (발견 스토리)
- 메뉴 소개 (에그베네딕트, 라떼)
- 분위기 (인테리어, 좌석)
- 정보 박스 (가격, 영업시간, 주차)
- 팁 (웨이팅 피하기)

발행할까요? (y/n)

> y

[MCP: publish_to_naver 실행]
✓ 네이버 로그인
✓ 에디터 열기
✓ 제목 입력
✓ 본문 작성 중...
  - 단락 1/5
  - 볼드 적용: "에그베네딕트", "15000원"
  - 정보 박스 삽입
✓ 발행 완료!

비용: 0원 (Selenium 무료)

> ✅ 발행 완료!
> URL: https://blog.naver.com/myid/223456789
```

### 3단계: 스타일 가이드 업데이트 (필요 시)

```bash
# 한 달 후, 블로그 스타일이 바뀌었다면...

> 블로그 스타일 다시 학습해줘

[MCP: learn_blog_style(force_update=True) 실행]
✓ 최신 블로그 20개 크롤링
✓ Gemini로 스타일 재분석
✓ style_guide.json 업데이트!

비용: ~300원 (필요할 때만!)

> ✅ 최신 스타일 반영 완료!
```

---

## 📊 프로젝트 구조

```
naver-blog-mcp/
├── src/
│   ├── server.py                 # MCP 서버 메인
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── learner.py            # learn_blog_style ⭐
│   │   ├── converter.py          # convert_to_blog (스타일 가이드 활용)
│   │   ├── publisher.py          # publish_to_naver
│   │   └── preview.py
│   ├── selenium_driver/
│   │   ├── driver.py
│   │   ├── login.py
│   │   └── editor.py
│   └── crawler/
│       └── naver_crawler.py      # 블로그 크롤링 (Playwright)
├── data/
│   └── style_guide.json          # ⭐ 압축된 스타일 가이드 (작은 파일!)
├── config/
│   └── mcp_config.json
├── requirements.txt
└── README.md
```

### style_guide.json 예시
```json
{
  "tone": "친근한 반말체, 이모지 자주 사용 (😊✨🎉👍)",
  "structure": {
    "paragraph_length": "2-3문장",
    "paragraph_break": "주제 전환 시, 3문장 이상 연속 시",
    "intro_style": "개인적 경험이나 질문으로 시작",
    "conclusion_style": "추천 문구 + 질문 유도"
  },
  "formatting": {
    "bold": [
      "숫자 포함 표현 (3만원, 5개)",
      "가성비, 맛집, 추천, 강추 같은 핵심 키워드",
      "정말, 완전, 대박 같은 강조 부사"
    ],
    "highlight": "결론 문장, '꼭 해봐야 할' 같은 당위 표현",
    "quote": "거의 사용 안 함",
    "info_box": "위치/가격/영업시간을 테이블로 정리"
  },
  "examples": {
    "good_intro": "오늘 소개할 곳은 정말 숨은 맛집이에요!",
    "good_conclusion": "여러분도 꼭 가보세요! 후회 안 할 거예요 😊"
  }
}
```

**파일 크기**: ~2KB (매우 작음! 레퍼런스 3개 HTML은 ~50KB였음)

### requirements.txt
```
# MCP
mcp>=1.0.0

# AI
google-generativeai>=0.3.0

# 웹 자동화
selenium>=4.15.0
playwright>=1.40.0
webdriver-manager>=4.0.0

# 유틸
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
```

---

## ⚡ 핵심 차별점

### 기존 방식 (❌)
```
1. 사람이 글 씀
2. AI가 처음부터 끝까지 작성
3. 결과물이 내 스타일과 안 맞음
```

### 다른 자동화 방식 (❌)
```
1. 사람이 줄글로 씀
2. AI가 매번 레퍼런스 3개를 프롬프트에 포함 (5,000 토큰!)
3. 토큰 비용 많이 듦
```

### 우리 방식 (✅)
```
1. 사람이 줄글로 씀 (편하게)
2. [1회] Gemini가 내 블로그 20개 분석 → 압축된 스타일 가이드 생성
3. [매번] 스타일 가이드만 프롬프트에 포함 (500 토큰!)
4. AI가 "이 가이드대로 변환"
5. 결과물이 내 기존 글들과 일관성 유지
```

### 장점 요약
- ✅ **토큰 76% 절감**: 5,500 토큰 → 1,300 토큰
- ✅ **비용 60% 절감**: 월 1,500원 → 600원
- ✅ **속도 빠름**: 프롬프트가 짧아서 응답 빠름
- ✅ **스타일 일관성**: 압축 과정에서 패턴이 더 명확해짐

---

## 💰 비용

### 무료
- Selenium (오픈소스)
- Playwright (오픈소스)
- Python (무료)

### 유료 (Gemini API만)

#### 초기 학습 (1회)
- 블로그 20개 분석: ~30,000 토큰
- 비용: ~300원
- **평생 1회만 (또는 몇 달에 1번 업데이트)**

#### 글 변환 (매번)
- 스타일 가이드: ~500 토큰
- 줄글: ~500 토큰
- 총: ~1,000 토큰
- 비용: ~10원/글

**월 30개 글 작성 시:**
- 초기 학습: 300원 (1회)
- 글 변환: 10원 × 30 = 300원
- **총: 600원/월**

### 기존 방식 대비 비교
```
[기존 - 레퍼런스 3개씩 매번 포함]
- 학습: 없음
- 글 변환: ~50원/글 (5,500 토큰)
- 월 30개: 1,500원

[개선 - 스타일 가이드]
- 학습: 300원 (1회)
- 글 변환: ~10원/글 (1,000 토큰)
- 월 30개: 600원

절감률: 60% 절감! 🎉
```

---

## 🎯 다음 단계

1. **MCP 서버 개발**
   - `learn_blog_style` 구현 (Gemini로 스타일 가이드 생성)
   - `convert_to_blog` 구현 (스타일 가이드 활용)
   - `publish_to_naver` 구현 (Selenium)

2. **Gemini CLI 설정**
   - MCP 서버 연결
   - 환경 변수 설정

3. **테스트**
   - 기존 블로그 학습 → 스타일 가이드 생성
   - 줄글 변환 테스트
   - 발행 테스트

4. **개선**
   - 이미지 자동 삽입 (선택)
   - 태그 자동 추출
   - 카테고리 자동 분류
   - 스타일 가이드 자동 업데이트 (주기적)