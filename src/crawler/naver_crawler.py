from playwright.async_api import async_playwright, Page
import asyncio

async def get_post_content(page: Page, post_url: str) -> dict:
    """개별 포스트 페이지로 이동하여 제목과 본문 내용을 가져옵니다."""
    await page.goto(post_url, wait_until='domcontentloaded')

    # 개별 포스트 페이지는 mainFrame이 없을 수 있으므로, context를 유연하게 설정합니다.
    context = page.frame(name='mainFrame')
    if not context:
        context = page  # mainFrame이 없으면 page 자체를 context로 사용합니다.

    # 제목 찾기 (여러 선택자를 한 번에 시도)
    title_locator = context.locator('div.pcol1 h3.se_title_text, h3.title, .se-title-text')
    title = "제목을 찾을 수 없습니다."
    if await title_locator.count() > 0:
        title = await title_locator.first.inner_text()

    # 본문 내용 찾기 (여러 선택자를 한 번에 시도)
    content_locator = context.locator('div.se-main-container, div#postViewArea')
    html_content = "본문을 찾을 수 없습니다."
    if await content_locator.count() > 0:
        html_content = await content_locator.first.inner_html()

    return {"title": title, "html": html_content}


async def fetch_raw_posts(blog_url: str, num_posts: int = 5) -> list[dict]:
    """
    네이버 블로그 URL에서 지정된 개수의 최신 게시글을 크롤링하여 제목과 HTML 본문을 반환합니다.
    
    Args:
        blog_url: 크롤링할 네이버 블로그의 URL (예: https://blog.naver.com/myid)
        num_posts: 가져올 게시글의 수 (기본값: 5)
    
    Returns:
        각 게시글의 제목과 HTML이 담긴 딕셔너리의 리스트
    """
    posts = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 블로그 홈으로 이동
        await page.goto(blog_url)

        # 블로그 글 목록이 있는 iframe으로 전환
        main_frame = page.frame(name='mainFrame')
        if not main_frame:
            await browser.close()
            return [{"error": "mainFrame을 찾을 수 없습니다. 블로그 URL을 확인해주세요."}]

        # "목록열기" 버튼이 있으면 클릭
        try:
            list_open_button = main_frame.get_by_text('목록열기', exact=True)
            if list_open_button.is_visible():
                await list_open_button.click()
                await asyncio.sleep(1) # 목록이 로드될 시간을 줍니다.
        except Exception:
            pass # 버튼이 없어도 진행

        # 게시글 링크 수집
        post_links = []
        # 네이버 블로그는 글 목록의 링크 구조가 다양할 수 있습니다.
        # 일반적인 패턴 몇 가지를 시도합니다.
        # 예: ._post_title_, .pcol2 > .pcol2_top > .pcol2_title > a
        locators = main_frame.locator('a[href*="/PostView.naver?"]')
        
        for i in range(await locators.count()):
            if len(post_links) >= num_posts:
                break
            link = locators.nth(i)
            href = await link.get_attribute('href')
            if href and href not in post_links:
                # 상대 경로를 절대 경로로 변환
                if href.startswith('/'):
                    base_url = blog_url.split('?')[0].replace('blog.naver.com/', 'blog.naver.com')
                    url_parts = blog_url.split('/')
                    origin = f"{url_parts[0]}//{url_parts[2]}"
                    href = f"{origin}{href}"
                post_links.append(href)
        
        # 각 링크를 방문하여 내용 크롤링
        for link in post_links:
            try:
                post_data = await get_post_content(page, link)
                posts.append(post_data)
            except Exception as e:
                posts.append({"title": f"Error crawling {link}", "html": str(e)})

        await browser.close()
    
    return posts
