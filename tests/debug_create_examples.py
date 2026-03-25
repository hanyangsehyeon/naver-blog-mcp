"""
Debug script for create_examples_from_index.

테스트 항목:
  1. url_index 없을 때 에러 반환 확인
  2. 존재하지 않는 카테고리 에러 반환 확인
  3. 특정 카테고리 크롤링 + examples/ 저장 (포스트 2개 제한)
  4. 중복 실행 시 이미 저장된 포스트 스킵 확인
  5. 저장된 JSON 파일 스키마 검증

Usage:
    python tests/debug_create_examples.py [blog_id] [category_name]
    python tests/debug_create_examples.py treetop0120 "나의 이야기"
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.common import make_driver, STANDARD_BLOG_ID, check, print_summary, PASS, FAIL
from mcp_server.tools.blog_analyzer import (
    create_examples_from_index, fetch_post_urls,
    URL_INDEX_DIR, EXAMPLES_DIR,
)

BLOG_ID       = sys.argv[1] if len(sys.argv) > 1 else STANDARD_BLOG_ID
CATEGORY_NAME = sys.argv[2] if len(sys.argv) > 2 else "나의 이야기"
MAX_POSTS     = 2  # 빠른 테스트용


def _patch_limit(n):
    """create_examples_from_index 내부에서 포스트 수를 n개로 제한하는 패치."""
    import mcp_server.tools.blog_analyzer as mod
    orig = mod.create_examples_from_index

    def limited(driver, blog_id, categories=None):
        import json as _json
        index_path = os.path.join(URL_INDEX_DIR, f"{blog_id}.json")
        with open(index_path, encoding="utf-8") as f:
            index = _json.load(f)
        for cat in index["categories"]:
            index["categories"][cat] = index["categories"][cat][:n]
        # 임시 인덱스 저장
        tmp_path = index_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            _json.dump(index, f, ensure_ascii=False)
        os.replace(tmp_path, index_path)
        return orig(driver, blog_id, categories)

    mod.create_examples_from_index = limited
    return orig


def main():
    results = {}
    driver = make_driver(headless=False)

    try:
        # ── Test 1: url_index 없을 때 에러 ───────────────────────────────────
        print("\n[1] url_index 없을 때 에러 반환 확인")
        fake_result = create_examples_from_index(driver, "없는블로그id_xyz")
        has_error = "error" in fake_result
        print(f"   결과: {fake_result.get('error', '에러 없음')[:80]}")
        check(results, "1. url_index 없을 때 에러", PASS if has_error else FAIL)

        # ── Test 2: url_index 확인 및 준비 ───────────────────────────────────
        print(f"\n[2] url_index/{BLOG_ID}.json 확인")
        index_path = os.path.join(URL_INDEX_DIR, f"{BLOG_ID}.json")
        if not os.path.exists(index_path):
            print(f"   url_index 없음 → fetch_post_urls 실행 중...")
            fetch_result = fetch_post_urls(driver, BLOG_ID, [CATEGORY_NAME])
            print(f"   결과: {fetch_result}")
            check(results, "2. url_index 준비", PASS if "error" not in fetch_result else FAIL,
                  str(fetch_result))
        else:
            with open(index_path, encoding="utf-8") as f:
                index = json.load(f)
            cats = list(index.get("categories", {}).keys())
            print(f"   기존 인덱스 존재: {len(cats)}개 카테고리")
            if CATEGORY_NAME not in cats:
                print(f"   '{CATEGORY_NAME}' 없음 → fetch_post_urls 추가 실행")
                fetch_post_urls(driver, BLOG_ID, [CATEGORY_NAME])
            check(results, "2. url_index 준비", PASS, f"{len(cats)}개 카테고리")

        # ── Test 3: 존재하지 않는 카테고리 에러 ──────────────────────────────
        print(f"\n[3] 존재하지 않는 카테고리 에러 확인")
        bad_result = create_examples_from_index(driver, BLOG_ID, categories=["없는카테고리xyz"])
        has_error2 = "error" in bad_result
        print(f"   결과: {bad_result.get('error', '에러 없음')[:80]}")
        check(results, "3. 없는 카테고리 에러", PASS if has_error2 else FAIL)

        # ── Test 4: 크롤링 + 저장 (MAX_POSTS 제한) ───────────────────────────
        print(f"\n[4] '{CATEGORY_NAME}' 크롤링 (최대 {MAX_POSTS}개)")

        # 인덱스를 MAX_POSTS개로 임시 제한
        with open(index_path, encoding="utf-8") as f:
            index_backup = json.load(f)
        limited_index = dict(index_backup)
        limited_index["categories"] = {
            k: v[:MAX_POSTS] if k == CATEGORY_NAME else []
            for k, v in index_backup["categories"].items()
        }
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(limited_index, f, ensure_ascii=False)

        result = create_examples_from_index(driver, BLOG_ID, categories=[CATEGORY_NAME])

        # 인덱스 복원
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_backup, f, ensure_ascii=False)

        if "error" in result:
            check(results, "4. 크롤링 + 저장", FAIL, result["error"])
        else:
            cat_result = result["categories"].get(CATEGORY_NAME, {})
            saved = cat_result.get("saved", 0)
            skipped = cat_result.get("skipped", 0)
            print(f"   저장: {saved}개 / 스킵: {skipped}개")
            check(results, "4. 크롤링 + 저장", PASS if saved + skipped > 0 else FAIL,
                  f"저장 {saved}개, 스킵 {skipped}개")

        # ── Test 5: 중복 실행 시 스킵 확인 ───────────────────────────────────
        print(f"\n[5] 중복 실행 시 이미 저장된 포스트 스킵 확인")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(limited_index, f, ensure_ascii=False)

        result2 = create_examples_from_index(driver, BLOG_ID, categories=[CATEGORY_NAME])

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_backup, f, ensure_ascii=False)

        if "error" not in result2:
            cat_result2 = result2["categories"].get(CATEGORY_NAME, {})
            saved2 = cat_result2.get("saved", 0)
            skipped2 = cat_result2.get("skipped", 0)
            print(f"   저장: {saved2}개 / 스킵: {skipped2}개")
            check(results, "5. 중복 스킵", PASS if saved2 == 0 and skipped2 > 0 else FAIL,
                  f"신규 저장 {saved2}개 (0이어야 함), 스킵 {skipped2}개")
        else:
            check(results, "5. 중복 스킵", FAIL, result2["error"])

        # ── Test 6: 저장된 JSON 스키마 검증 ──────────────────────────────────
        print(f"\n[6] 저장된 JSON 파일 스키마 검증")
        category_dir = os.path.join(EXAMPLES_DIR, BLOG_ID, CATEGORY_NAME)
        if os.path.exists(category_dir):
            files = [f for f in os.listdir(category_dir) if f.endswith(".json")]
            print(f"   {CATEGORY_NAME}/ — {len(files)}개 파일")
            all_valid = True
            for fname in files[:3]:
                fpath = os.path.join(category_dir, fname)
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                has_keys = all(k in data for k in ["date", "title", "url", "paragraphs"])
                has_paras = isinstance(data.get("paragraphs"), list) and len(data["paragraphs"]) > 0
                if has_keys and has_paras:
                    fmt = sum(1 for p in data["paragraphs"] if p.get("formatting"))
                    print(f"   ✅ {fname}: '{data['title'][:30]}', 단락 {len(data['paragraphs'])}개, 포매팅 {fmt}개")
                else:
                    print(f"   ❌ {fname}: 스키마 오류")
                    all_valid = False
            check(results, "6. JSON 스키마", PASS if all_valid else FAIL)
        else:
            check(results, "6. JSON 스키마", FAIL, "category_dir 없음")

    finally:
        print_summary(results)
        driver.quit()


if __name__ == "__main__":
    main()
