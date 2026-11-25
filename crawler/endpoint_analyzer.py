import re
from urllib.parse import urljoin, urldefrag, urlparse
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from cli.starter import console

JS_PATH_RE = re.compile(r"""["']((?:/|\.\./|\./)[A-Za-z0-9_./?&=-]{2,140})["']""")

def url_clearer(base_url: str, raw: str) -> str | None:
    
    if not raw or raw.startswith(("mailto:", "tel:", "javascript:", "data:", "#")):
        return None

    full_path = urljoin(base_url, raw.strip())
    no_frag, _ = urldefrag(full_path)
    parsed = urlparse(no_frag)

    return no_frag if parsed.scheme in ("http", "https") and parsed.netloc else None

def in_scope(url: str, root_host: str, allow_subs: bool) -> bool:

    host = urlparse(url).netloc.lower()
    root_host = root_host.lower()

    return host == root_host or (allow_subs and host.endswith("." + root_host))

def extract_links(base_url: str, body: str, is_js: bool) -> set[str]:

    if is_js:
        return {u for m in JS_PATH_RE.findall(body) if (u := url_clearer(base_url, m))}

    soup = BeautifulSoup(body, "html.parser")
    found = set()

    for tag, attr in (("a", "href"), ("form", "action"), ("script", "src")):
        for el in soup.find_all(tag):
            if u := url_clearer(base_url, el.get(attr, "")):
                found.add(u)
    return found

async def crawl(start_url: str, max_depth: int = 2, allow_subs: bool = False) -> list[str]:
    host = urlparse(start_url).netloc
    visited: set[str] = set()
    found: set[str] = set()
    queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()

    await queue.put((start_url, 0))

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=10),
        headers=headers,
    ) as session:
        while not queue.empty():
            url, depth = await queue.get()

            if url in visited or depth > max_depth:
                queue.task_done()
                continue
            visited.add(url)

            try:
                async with session.get(url) as resp:
                    if resp.status == 429:
                        console.print(f"[red][!][/] Rate-limited / WAF block (429) on {url}; stopping crawl.")
                        queue.task_done()
                        break

                    if resp.status >= 400:
                        console.print(f"[red][!][/] HTTP {resp.status} on {url}")

                    text = await resp.text(errors="ignore")
                    ctype = resp.headers.get("Content-Type", "").lower()
                    is_js = "javascript" in ctype or url.endswith(".js")

                    for link in extract_links(url, text, is_js):
                        found.add(link)
                        if in_scope(link, host, allow_subs) and link not in visited and depth < max_depth:
                            await queue.put((link, depth + 1))

                await asyncio.sleep(0.5)
            except Exception as e:
                console.print(f"[red][!][/] Error on {url} ({type(e).__name__}): {e or repr(e)}")
            finally:
                queue.task_done()

    return sorted(found)