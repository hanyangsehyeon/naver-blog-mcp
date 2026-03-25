"""
"나의 이야기" 카테고리 URL 수집 디버깅 스크립트.

단계별로 어디서 실패하는지 확인:
  1. mainFrame 내 카테고리 링크 전수 출력
  2. get_category_post_links 호출 후 toplistWrapper 탐색 과정 추적
  3. _setTopListUrl 셀렉터로 수집된 링크 출력
  4. 목록열기 / 30줄 보기 버튼 존재 여부 확인

Usage:
    python tests/debug_naiui_category.py [blog_id] [category_name]
    python tests/debug_naiui_category.py treetop0120 "나의 이야기"
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from tests.common import make_driver, STANDARD_BLOG_ID
from mcp_server.tools.blog_analyzer import get_blog_categories, get_category_post_links

BLOG_ID       = sys.argv[1] if len(sys.argv) > 1 else STANDARD_BLOG_ID
CATEGORY_NAME = sys.argv[2] if len(sys.argv) > 2 else "나의 이야기"


def main():
    driver = make_driver(headless=False)
    try:
        # ── 1. 카테고리 목록 확인 ─────────────────────────────────────────────
        print(f"\n[1] get_blog_categories({BLOG_ID})")
        categories = get_blog_categories(driver, BLOG_ID)
        print(f"   전체 카테고리 {len(categories)}개:")
        for name, no in categories.items():
            marker = " ◀◀◀" if name == CATEGORY_NAME else ""
            print(f"   '{name}' → categoryNo={no}{marker}")

        if CATEGORY_NAME not in categories:
            print(f"\n   ❌ '{CATEGORY_NAME}' 카테고리가 목록에 없음 — 이름 오타 확인 필요")
            return

        cat_no = categories[CATEGORY_NAME]
        print(f"\n   ✅ '{CATEGORY_NAME}' → categoryNo={cat_no}")

        # ── 2. 카테고리 클릭 후 상태 추적 ────────────────────────────────────
        print(f"\n[2] 카테고리 페이지 로드 및 toplistWrapper 상태 확인")
        driver.get(f"https://blog.naver.com/{BLOG_ID}")
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(1)

        driver.switch_to.frame(driver.find_element(By.ID, "mainFrame"))
        time.sleep(1)

        # 카테고리 클릭 (td.menu1 상단 네비)
        clicked = False
        for link in driver.find_elements(By.CSS_SELECTOR, "td.menu1 a[class*='itemfont']"):
            if link.text.strip().replace("\u00a0", " ") == CATEGORY_NAME:
                print(f"   td.menu1에서 '{CATEGORY_NAME}' 클릭")
                link.click()
                clicked = True
                break

        if not clicked:
            # from=postList 링크로 직접 이동
            for link in driver.find_elements(By.CSS_SELECTOR, f"a[href*='categoryNo={cat_no}'][href*='from=postList']"):
                href = link.get_attribute("href")
                print(f"   td.menu1 미발견 → postList 링크로 이동: {href[:80]}")
                driver.get(href)
                time.sleep(2)
                break
        else:
            time.sleep(2)

        # ── 3. 목록열기 버튼 상태 ─────────────────────────────────────────────
        print(f"\n[3] 목록열기 버튼 확인")
        try:
            blind = driver.find_element(By.ID, "toplistSpanBlind")
            print(f"   toplistSpanBlind 텍스트: '{blind.text.strip()}'")
            if blind.text.strip() == "목록열기":
                print("   → 목록열기 클릭")
                driver.find_element(By.CSS_SELECTOR, "a.btn_openlist").click()
                time.sleep(1.5)
            else:
                print("   → 이미 열려있음")
        except NoSuchElementException:
            print("   toplistSpanBlind 없음 (목록열기 버튼 자체가 없음)")

        # ── 4. toplistWrapper 내 링크 확인 ───────────────────────────────────
        print(f"\n[4] toplistWrapper 내 링크 수 확인")
        try:
            wrapper = driver.find_element(By.ID, "toplistWrapper")
            all_links = wrapper.find_elements(By.TAG_NAME, "a")
            setTop_links = wrapper.find_elements(By.CSS_SELECTOR, "a._setTopListUrl")
            print(f"   toplistWrapper 존재: ✅")
            print(f"   전체 <a> 태그 수: {len(all_links)}")
            print(f"   a._setTopListUrl 수: {len(setTop_links)}")
            for i, a in enumerate(setTop_links[:5]):
                print(f"     [{i+1}] '{a.text.strip()[:50]}' → {(a.get_attribute('href') or '')[:80]}")
        except NoSuchElementException:
            print("   ❌ toplistWrapper 없음")

        # ── 5. 30줄 보기 시도 ─────────────────────────────────────────────────
        print(f"\n[5] 30줄 보기 전환 시도")
        try:
            toggle = driver.find_element(By.ID, "listCountToggle")
            print(f"   listCountToggle 존재: ✅ (현재 텍스트: '{toggle.text.strip()}')")
            toggle.click()
            time.sleep(0.5)
            btn30 = driver.find_element(By.CSS_SELECTOR, "#changeListCount a[data-value='30']")
            print(f"   30줄 보기 버튼 존재: ✅")
            btn30.click()
            time.sleep(2)
        except NoSuchElementException as e:
            print(f"   ❌ 30줄 보기 버튼 없음: {e}")

        # ── 6. 전환 후 링크 재수집 ────────────────────────────────────────────
        print(f"\n[6] 30줄 보기 전환 후 링크 재수집")
        try:
            setTop_links2 = driver.find_elements(By.CSS_SELECTOR, "#toplistWrapper a._setTopListUrl")
            print(f"   a._setTopListUrl 수: {len(setTop_links2)}")
            for i, a in enumerate(setTop_links2[:5]):
                print(f"     [{i+1}] '{a.text.strip()[:50]}' → {(a.get_attribute('href') or '')[:80]}")
        except Exception as e:
            print(f"   오류: {e}")

        # 6번에서 수집한 URL 저장
        urls_step6 = set(a.get_attribute("href") or "" for a in setTop_links2)

        driver.switch_to.default_content()

        # ── 7. get_category_post_links 최종 결과 ──────────────────────────────
        print(f"\n[7] get_category_post_links 최종 결과")
        result = get_category_post_links(driver, BLOG_ID, CATEGORY_NAME, category_no=cat_no)
        if result and "error" in result[0]:
            print(f"   ❌ 에러: {result[0]['error']}")
        else:
            print(f"   수집된 포스트 {len(result)}개")
            for p in result[:5]:
                print(f"     '{p['title'][:50]}'")
                print(f"     {p['url'][:80]}")

            # ── 6 vs 7 비교 ───────────────────────────────────────────────────
            print(f"\n[검증] 6번 vs 7번 URL 일치 여부")
            urls_step7 = set(p["url"] for p in result)
            only_in_6 = urls_step6 - urls_step7
            only_in_7 = urls_step7 - urls_step6
            if not only_in_6 and not only_in_7:
                print(f"   ✅ 완전 일치 ({len(urls_step7)}개)")
            else:
                if only_in_6:
                    print(f"   ❌ 6번에만 있는 URL {len(only_in_6)}개:")
                    for u in list(only_in_6)[:3]:
                        print(f"     {u[:80]}")
                if only_in_7:
                    print(f"   ❌ 7번에만 있는 URL {len(only_in_7)}개:")
                    for u in list(only_in_7)[:3]:
                        print(f"     {u[:80]}")

    finally:
        input("\n브라우저 확인 후 Enter 누르면 종료...")
        driver.quit()


if __name__ == "__main__":
    main()
