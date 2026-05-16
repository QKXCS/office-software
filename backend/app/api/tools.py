import re
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/tools", tags=["tools"])


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class SearchResponse(BaseModel):
    status: str
    results: list[SearchResult]


async def _do_search(query: str, max_results: int = 5) -> SearchResponse:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                "https://cn.bing.com/search",
                params={"q": query, "count": max_results},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            if resp.status_code != 200:
                return SearchResponse(status="error", results=[
                    SearchResult(title="搜索失败", url="", snippet=f"HTTP {resp.status_code}")
                ])

            text = resp.text
            results = []
            snippets = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', text, re.DOTALL)
            for snip in snippets[:max_results]:
                title_m = re.search(r'<h2[^>]*><a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', snip, re.DOTALL)
                snippet_m = re.search(r'<p[^>]*>(.*?)</p>', snip, re.DOTALL)
                if title_m:
                    results.append(SearchResult(
                        title=re.sub(r'<[^>]+>', '', title_m.group(2)),
                        url=title_m.group(1),
                        snippet=re.sub(r'<[^>]+>', '', snippet_m.group(1)) if snippet_m else "",
                    ))

            if not results:
                return SearchResponse(status="ok", results=[
                    SearchResult(title="未找到结果", url="", snippet="请尝试其他关键词。")
                ])
            return SearchResponse(status="ok", results=results)
    except Exception as e:
        return SearchResponse(status="error", results=[
            SearchResult(title="搜索失败", url="", snippet=str(e))
        ])


@router.post("/search")
async def web_search(req: SearchRequest) -> SearchResponse:
    return await _do_search(req.query, req.max_results)
