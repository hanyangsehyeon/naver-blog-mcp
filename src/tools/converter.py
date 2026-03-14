import json
import os
from google import genai

class BlogConverter:
    """스타일 가이드 활용해서 줄글 → 블로그 변환"""

    def __init__(self, style_guide_path="./data/style_guide.json"):
        # 스타일 가이드 로드
        with open(style_guide_path, 'r', encoding='utf-8') as f:
            self.style_guide = json.load(f)

        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = 'gemini-2.0-flash'

    def convert(self, raw_text: str) -> dict:
        """
        줄글 → 블로그 형식 변환
        """
        # 1. 프롬프트 구성 (스타일 가이드 활용)
        prompt = self._build_conversion_prompt(raw_text)

        # 2. Gemini API 호출
        response = self.client.models.generate_content(model=self.model, contents=prompt)

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

def convert_to_blog_post(raw_text: str) -> dict:
    """줄글을 블로그 형식의 JSON으로 변환합니다."""
    converter = BlogConverter()
    return converter.convert(raw_text)
