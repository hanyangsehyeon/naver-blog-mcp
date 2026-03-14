from src.crawler.naver_crawler import fetch_raw_posts


async def learn_blog_style(blog_url: str, num_posts: int = 20) -> list[dict]:
    """
    네이버 블로그에서 게시글을 크롤링하여 스타일 학습용 원문 데이터를 반환합니다.
    반환된 데이터를 분석하여 스타일 가이드를 직접 작성한 뒤 save_file로 저장하세요.

    Args:
        blog_url: 분석할 네이버 블로그 URL (예: https://blog.naver.com/myid)
        num_posts: 가져올 게시글 수 (기본값: 20)

    Returns:
        각 게시글의 제목과 HTML이 담긴 딕셔너리 리스트
    """
    return await fetch_raw_posts(blog_url, num_posts)
