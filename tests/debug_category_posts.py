"""
Debug script for get_blog_categories / get_category_post_links.

Tests:
  1. get_blog_categories  — 전체 카테고리 목록 반환
  2. get_category_post_links (정상 카테고리) — 목록열기 → 30줄 보기 → 링크 수집
  3. 반환 링크 형식 검증 — {url, title} 구조
  4. get_category_post_links (존재하지 않는 카테고리) — 에러 메시지 포함 여부
  5. 수업이야기 카테고리 동일 검증

Usage:
    python tests/debug_category_posts.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.common import (
    make_driver, STANDARD_BLOG_ID,
    check, print_summary, PASS, FAIL,
)
from mcp_server.tools.blog_analyzer import get_blog_categories, get_category_post_links

# 커맨드라인 인자로 블로그 ID 지정 가능
# 사용법: python tests/debug_category_posts.py [blog_id] [category_name]
# 예시:   python tests/debug_category_posts.py treetop0120 "수업이야기"
BLOG_ID          = sys.argv[1] if len(sys.argv) > 1 else STANDARD_BLOG_ID
TEST_CATEGORY    = sys.argv[2] if len(sys.argv) > 2 else None  # None이면 첫 번째 카테고리 자동 선택
MISSING_CATEGORY = "없는카테고리xyz"


def main():
    results = {}
    print(f"\n대상 블로그: {BLOG_ID}")
    driver = make_driver(headless=False)

    try:
        # ── Test 1: 카테고리 목록 조회 ─────────────────────────────────────────
        print(f"\n[1] get_blog_categories({BLOG_ID})")
        categories = get_blog_categories(driver, BLOG_ID)

        print(f"   발견된 카테고리 {len(categories)}개:")
        for name, no in categories.items():
            print(f"     '{name}' → categoryNo={no}")

        check(results, "1. 카테고리 목록 조회",
              PASS if len(categories) > 0 else FAIL,
              f"{len(categories)}개 발견")

        # ── Test 2: 포스트 링크 수집 ───────────────────────────────────────────
        # TEST_CATEGORY 미지정 시 첫 번째 카테고리 자동 선택
        target_category = TEST_CATEGORY or (list(categories.keys())[0] if categories else None)
        if not target_category:
            print("   카테고리 없음 — 스킵")
            check(results, "2. 포스트 링크 수집", FAIL, "카테고리 없음")
        else:
            pass

        print(f"\n[2] get_category_post_links('{target_category}')")
        posts = get_category_post_links(driver, BLOG_ID, target_category)

        has_error = any("error" in p for p in posts)
        if has_error:
            print(f"   ❌ 에러 반환: {posts[0]}")
        else:
            print(f"   수집된 포스트 {len(posts)}개:")
            for i, p in enumerate(posts[:5]):
                print(f"     [{i+1}] {p['title'][:50]}")
                print(f"          {p['url'][:80]}")
            if len(posts) > 5:
                print(f"     ... 외 {len(posts)-5}개")

        check(results, "2. 포스트 링크 수집",
              PASS if not has_error and len(posts) > 0 else FAIL,
              f"{len(posts)}개 수집")

        # ── Test 3: 링크 형식 검증 ────────────────────────────────────────────
        print(f"\n[3] 링크 형식 검증")
        if not has_error and posts:
            valid = all(
                isinstance(p.get("url"), str) and "logNo=" in p["url"]
                and isinstance(p.get("title"), str) and len(p["title"]) > 0
                for p in posts
            )
            check(results, "3. 링크 형식 (url+title)",
                  PASS if valid else FAIL,
                  "url에 logNo= 포함, title 비어있지 않음")
        else:
            check(results, "3. 링크 형식 (url+title)", FAIL, "포스트 없음 — 스킵")

        # ── Test 4: 없는 카테고리 에러 처리 ───────────────────────────────────
        print(f"\n[4] 없는 카테고리 에러 처리 ('{MISSING_CATEGORY}')")
        error_result = get_category_post_links(driver, BLOG_ID, MISSING_CATEGORY)

        has_error_msg = (
            len(error_result) == 1
            and "error" in error_result[0]
            and "가능한 카테고리" in error_result[0]["error"]
        )
        print(f"   에러 메시지: {error_result[0].get('error', '없음')[:100]}")
        check(results, "4. 없는 카테고리 에러 처리",
              PASS if has_error_msg else FAIL,
              "에러 + 가능한 카테고리 목록 포함 여부")

        # ── Test 5: 두 번째 카테고리도 동작하는지 확인 ───────────────────────
        cat_list = list(categories.keys())
        second_category = cat_list[1] if len(cat_list) > 1 else None
        if second_category and second_category != target_category:
            print(f"\n[5] get_category_post_links('{second_category}') — 두 번째 카테고리")
            posts2 = get_category_post_links(driver, BLOG_ID, second_category)
            has_error2 = any("error" in p for p in posts2)
            print(f"   수집된 포스트 {len(posts2)}개")
            for p in posts2[:3]:
                print(f"     {p.get('title', '')[:50]}")
            check(results, f"5. '{second_category}' 포스트 수집",
                  PASS if not has_error2 and len(posts2) > 0 else FAIL,
                  f"{len(posts2)}개 수집")
        else:
            print(f"\n[5] 두 번째 카테고리 없음 — 스킵")

    finally:
        print_summary(results)
        driver.quit()


if __name__ == "__main__":
    main()
