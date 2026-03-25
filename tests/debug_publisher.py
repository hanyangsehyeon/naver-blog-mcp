"""
Debug script for publish_to_naver.
examples/treetop0120/우듬지루미북 콘텐츠/ 에서 첫 번째 파일을 골라
MY_BLOG_ID 블로그에 임시저장으로 포스팅.

Usage:
    python tests/debug_publisher.py
    python tests/debug_publisher.py [example_file_path]
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.common import make_driver, login_with_qr, MY_BLOG_ID
from mcp_server.tools.publisher import publish_to_naver

OUTPUT_DIR   = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
EXAMPLE_PATH = sys.argv[1] if len(sys.argv) > 1 else None
TARGET_BLOG  = MY_BLOG_ID


def pick_output() -> str:
    files = sorted(f for f in os.listdir(OUTPUT_DIR) if f.endswith(".json"))
    if not files:
        raise FileNotFoundError(f"output/ 에 JSON 파일 없음")
    return os.path.join(OUTPUT_DIR, files[0])


def main():
    example_path = EXAMPLE_PATH or pick_output()
    print(f"\n사용할 파일: {example_path}")

    with open(example_path, encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "테스트 포스트")
    paragraphs = data.get("paragraphs", [])
    print(f"제목: {title}")
    print(f"단락 수: {len(paragraphs)}개")
    print(f"포매팅 있는 단락: {sum(1 for p in paragraphs if p.get('formatting'))}개")
    print(f"발행 대상 블로그: {TARGET_BLOG}")

    if not TARGET_BLOG:
        print("❌ .env에 MY_BLOG_ID 설정 필요")
        return

    driver = make_driver(headless=False)
    try:
        login_with_qr(driver)

        print("\n에디터 열고 포스팅 중...")
        result = publish_to_naver(driver, blog_id=TARGET_BLOG, title=title, paragraphs=paragraphs)
        print(f"\n결과: {result}")

        input("\n브라우저에서 결과 확인 후 Enter 누르면 종료...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
