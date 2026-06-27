import re
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse

import httpx


DEFAULT_MAX_PAGES = 5
MAX_PAGES = 20
DEFAULT_MAX_DEPTH = 1
MAX_DEPTH = 3
MAX_TEXT_CHARS_PER_PAGE = 12000
MAX_LINKS_PER_PAGE = 80
MAX_TOTAL_LINKS = 250
MAX_BYTES = 2_000_000
USER_AGENT = (
    "RecturyWebsiteAnalyzer/1.0 "
    "(local CLI website analysis tool; +https://github.com/Rectury-AI/Rectury-Desktop)"
)


class VisibleHTMLParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title = ""
        self.meta = {}
        self.headings = []
        self.links = []
        self.images = []
        self.forms = []
        self.scripts = []
        self.stylesheets = []
        self.text_parts = []
        self._skip_stack = []
        self._current_tag = None
        self._current_heading = None
        self._current_form = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        tag = tag.lower()
        self._current_tag = tag

        if tag in {"script", "style", "noscript", "svg", "canvas"}:
            self._skip_stack.append(tag)

        if tag == "title":
            self._in_title = True

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._current_heading = {"level": tag, "text": ""}

        if tag == "meta":
            name = attrs.get("name") or attrs.get("property")
            content = attrs.get("content")
            if name and content:
                key = name.strip().lower()
                if key in {
                    "description",
                    "og:title",
                    "og:description",
                    "twitter:title",
                    "twitter:description",
                    "keywords",
                    "robots",
                }:
                    self.meta[key] = normalize_space(content)

        if tag == "a" and attrs.get("href"):
            self.links.append(
                {
                    "url": clean_url(urljoin(self.base_url, attrs.get("href"))),
                    "text": normalize_space(attrs.get("title", "")),
                }
            )

        if tag == "img":
            src = attrs.get("src") or attrs.get("data-src")
            if src:
                self.images.append(
                    {
                        "url": clean_url(urljoin(self.base_url, src)),
                        "alt": normalize_space(attrs.get("alt", "")),
                    }
                )

        if tag == "form":
            self._current_form = {
                "action": clean_url(urljoin(self.base_url, attrs.get("action", ""))),
                "method": (attrs.get("method") or "get").lower(),
                "inputs": [],
            }

        if tag in {"input", "textarea", "select", "button"} and self._current_form is not None:
            self._current_form["inputs"].append(
                {
                    "tag": tag,
                    "name": attrs.get("name", ""),
                    "type": attrs.get("type", ""),
                    "label": normalize_space(
                        attrs.get("placeholder") or attrs.get("aria-label") or ""
                    ),
                }
            )

        if tag == "script" and attrs.get("src"):
            self.scripts.append(clean_url(urljoin(self.base_url, attrs["src"])))

        if tag == "link" and (attrs.get("rel") or "").lower() == "stylesheet":
            href = attrs.get("href")
            if href:
                self.stylesheets.append(clean_url(urljoin(self.base_url, href)))

    def handle_endtag(self, tag):
        tag = tag.lower()

        if self._skip_stack and self._skip_stack[-1] == tag:
            self._skip_stack.pop()

        if tag == "title":
            self._in_title = False

        if self._current_heading and tag == self._current_heading["level"]:
            text = normalize_space(self._current_heading["text"])
            if text:
                self.headings.append(
                    {"level": self._current_heading["level"], "text": text}
                )
            self._current_heading = None

        if tag == "form" and self._current_form is not None:
            self.forms.append(self._current_form)
            self._current_form = None

    def handle_data(self, data):
        text = normalize_space(data)
        if not text:
            return

        if self._in_title:
            self.title = normalize_space(f"{self.title} {text}")

        if self._current_heading is not None:
            self._current_heading["text"] = normalize_space(
                f"{self._current_heading['text']} {text}"
            )

        if self._skip_stack:
            return

        self.text_parts.append(text)


def normalize_space(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def clean_url(url):
    if not url:
        return ""
    cleaned, _fragment = urldefrag(url)
    return cleaned


def normalize_start_url(url):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url is required.")

    value = url.strip()
    parsed = urlparse(value)

    if not parsed.scheme:
        value = "https://" + value
        parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are supported.")

    if not parsed.netloc:
        raise ValueError("URL must include a host.")

    return clean_url(value)


def same_site(url, root):
    parsed_url = urlparse(url)
    parsed_root = urlparse(root)
    return parsed_url.scheme in {"http", "https"} and parsed_url.netloc == parsed_root.netloc


def classify_links(links, root_url):
    internal = []
    external = []
    seen = set()

    for link in links:
        url = link.get("url", "")
        if not url or url in seen:
            continue
        seen.add(url)

        target = internal if same_site(url, root_url) else external
        target.append({"url": url, "text": link.get("text", "")})

    return internal, external


def extract_page(response, url, root_url):
    content_type = response.headers.get("content-type", "")
    raw = response.content[:MAX_BYTES]

    if "text/html" not in content_type.lower():
        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "content_type": content_type,
            "html": False,
            "bytes": len(response.content),
            "text_excerpt": "",
            "title": "",
            "meta": {},
            "headings": [],
            "internal_links": [],
            "external_links": [],
            "images": [],
            "forms": [],
            "scripts": [],
            "stylesheets": [],
        }

    parser = VisibleHTMLParser(str(response.url))
    parser.feed(raw.decode(response.encoding or "utf-8", errors="replace"))
    text = normalize_space(" ".join(parser.text_parts))
    internal_links, external_links = classify_links(parser.links, root_url)

    return {
        "url": str(response.url),
        "requested_url": url,
        "status_code": response.status_code,
        "content_type": content_type,
        "html": True,
        "bytes": len(response.content),
        "title": parser.title,
        "meta": parser.meta,
        "headings": parser.headings[:60],
        "text_excerpt": text[:MAX_TEXT_CHARS_PER_PAGE],
        "text_truncated": len(text) > MAX_TEXT_CHARS_PER_PAGE,
        "word_count": len(text.split()),
        "internal_links": internal_links[:MAX_LINKS_PER_PAGE],
        "external_links": external_links[:MAX_LINKS_PER_PAGE],
        "images": parser.images[:80],
        "forms": parser.forms[:20],
        "scripts": parser.scripts[:80],
        "stylesheets": parser.stylesheets[:80],
    }


def analyze_website(
    url,
    state,
    crawl=True,
    max_pages=DEFAULT_MAX_PAGES,
    max_depth=DEFAULT_MAX_DEPTH,
    include_assets=True,
):
    try:
        start_url = normalize_start_url(url)
    except ValueError as error:
        return {"error": str(error), "code": "invalid_url"}

    if not isinstance(max_pages, int):
        max_pages = DEFAULT_MAX_PAGES
    if not isinstance(max_depth, int):
        max_depth = DEFAULT_MAX_DEPTH

    max_pages = max(1, min(max_pages, MAX_PAGES))
    max_depth = max(0, min(max_depth, MAX_DEPTH))
    crawl = bool(crawl)

    queue = deque([(start_url, 0)])
    queued = {start_url}
    visited = set()
    pages = []
    errors = []

    try:
        with httpx.Client(
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"},
            follow_redirects=True,
            timeout=httpx.Timeout(12.0, connect=6.0),
        ) as client:
            while queue and len(pages) < max_pages:
                current_url, depth = queue.popleft()
                if current_url in visited:
                    continue

                visited.add(current_url)

                try:
                    response = client.get(current_url)
                    page = extract_page(response, current_url, start_url)
                    pages.append(page)
                except httpx.HTTPError as error:
                    errors.append({"url": current_url, "error": str(error)})
                    continue

                if not crawl or depth >= max_depth or not page.get("html"):
                    continue

                for link in page.get("internal_links", []):
                    next_url = link.get("url")
                    if not next_url or next_url in queued or next_url in visited:
                        continue
                    if not same_site(next_url, start_url):
                        continue
                    queued.add(next_url)
                    queue.append((next_url, depth + 1))
                    if len(queued) >= max_pages * 8:
                        break
    except Exception as error:
        return {"error": str(error), "code": "request_failed"}

    all_internal = []
    all_external = []
    seen_internal = set()
    seen_external = set()

    for page in pages:
        for link in page.get("internal_links", []):
            target = link.get("url")
            if target and target not in seen_internal:
                seen_internal.add(target)
                all_internal.append(link)
        for link in page.get("external_links", []):
            target = link.get("url")
            if target and target not in seen_external:
                seen_external.add(target)
                all_external.append(link)

    if not include_assets:
        for page in pages:
            page.pop("images", None)
            page.pop("scripts", None)
            page.pop("stylesheets", None)

    return {
        "success": True,
        "start_url": start_url,
        "pages_fetched": len(pages),
        "max_pages": max_pages,
        "max_depth": max_depth,
        "crawl": crawl,
        "pages": pages,
        "site_links": {
            "internal": all_internal[:MAX_TOTAL_LINKS],
            "external": all_external[:MAX_TOTAL_LINKS],
            "internal_total": len(all_internal),
            "external_total": len(all_external),
        },
        "errors": errors,
        "limitations": [
            "Fetches public HTTP/HTTPS content only.",
            "Does not execute JavaScript or bypass authentication, paywalls, CAPTCHA, or robots/access controls.",
        ],
    }
