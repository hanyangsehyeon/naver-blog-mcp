# treetop0120 — 블로그 메인 페이지 구조

**URL**: `https://blog.naver.com/treetop0120`
**분석일**: 2026-03-22

---

## iframe 구조

메인 컨텐츠 전체가 `iframe#mainFrame` 안에 존재한다.

```
https://blog.naver.com/treetop0120
└── iframe#mainFrame
    └── https://blog.naver.com/PostList.naver?blogId=treetop0120&widgetTypeCall=true&parentCategoryNo=10&...
```

Selenium 접근:
```python
driver.switch_to.frame("mainFrame")
# 작업 후
driver.switch_to.default_content()
```

---

## 포스트 목록

```html
<div id="postListBody" class="post_album_view_s966">
  <div class="blog2_albumlist" id="PostThumbnailAlbumViewArea">
    <ul class="thumblist">
      <li class="item">
        <a href="/PostView.naver?blogId=treetop0120&logNo=224192489371&categoryNo=&parentCategoryNo=10&from=thumbnailList"
           class="link pcol2">
          <div class="area_thumb">
            <img src="https://postfiles.pstatic.net/..." class="thumb">
          </div>
          <div class="area_text">
            <strong class="title ell">포스트 제목</strong>
            <span class="date">2026. 2. 23.</span>
            <span class="read">
              <i class="icon"><span class="blind">댓글수</span></i> 5
            </span>
          </div>
        </a>
      </li>
    </ul>
  </div>
</div>
```

**핵심 selector**:
| 역할 | Selector |
|---|---|
| 목록 컨테이너 | `#postListBody` |
| 포스트 아이템 | `#postListBody li.item` |
| 포스트 링크 | `li.item > a.link` |
| `logNo` 추출 | `a.link` href에서 `logNo=N` 파싱 |
| 제목 | `li.item strong.title` |
| 날짜 | `li.item span.date` |

---

## 카테고리 메뉴

메인 페이지에는 **두 종류의 카테고리 링크**가 존재한다.

### 상단 네비게이션 (`from=menu`)
`td.menu1` 안의 링크. 블로그 설정에 따라 일부 카테고리만 노출됨. **전체 목록으로 신뢰할 수 없음**.

```html
<td class="menu1">
  <ul>
    <li><a href="...&from=menu" class="itemfont ...">블로그</a></li>
    <li><a href="...&categoryNo=23&...&from=menu" class="off itemfont ...">우듬지루미북 논술</a></li>
    <li><a href="...&categoryNo=10&...&from=menu" class="on itemfont ...">우듬지루미북 콘텐츠</a></li>
  </ul>
</td>
```

### 좌측 사이드바 (`from=postList`) ← 전체 카테고리 목록
`from=postList` 파라미터를 가진 링크. **전체 카테고리를 포함**하므로 이걸 사용해야 함.

```html
<a href="/PostList.naver?...&categoryNo=11&...&from=postList">수업이야기</a>
```

**전체 카테고리 목록** (treetop0120 기준):
| categoryNo | 이름 |
|---|---|
| 23 | 우듬지루미북 논술 |
| 20 | 원장소개 |
| 7 | 수업목표 |
| 25 | 수업료 안내 |
| 21 | 오시는길 |
| 10 | 우듬지루미북 콘텐츠 |
| 26 | 우듬지루미북 커리큘럼 |
| 11 | 수업이야기 |
| 12 | 갤러리 |
| 14 | 앎과 책이야기 |
| 29 | 루미북 단계별 책 |
| 31 | 교과수록/연계 도서 |
| 24 | 나의 이야기 |

**핵심 selector**:
| 역할 | Selector |
|---|---|
| 전체 카테고리 링크 | `a[href*='from=postList'][href*='categoryNo=']` |
| categoryNo 추출 | href에서 `categoryNo=N` 파싱 (`0` = 전체보기, 제외) |
| ~~상단 메뉴 (비권장)~~ | ~~`td.menu1 a[class*='itemfont']`~~ 일부만 노출됨 |

---

## 페이지네이션

```html
<div class="blog2_paginate">
  <!-- 현재 페이지: strong 태그 -->
  <strong class="page pcol3 _setTop">1<span class="blind">현재 페이지</span></strong>
  <!-- 다른 페이지: a 태그 -->
  <a href="/PostList.naver?from=postList&blogId=treetop0120&parentCategoryNo=10&currentPage=2"
     class="page pcol2 _setTop">2</a>
</div>
```

**URL 패턴**:
```
/PostList.naver?from=postList&blogId={id}&parentCategoryNo={no}&currentPage={N}
```

**핵심 selector**:
| 역할 | Selector |
|---|---|
| 다음 페이지 링크들 | `.blog2_paginate a[href*='currentPage']` |
| 현재 페이지 번호 | `.blog2_paginate strong.page` |