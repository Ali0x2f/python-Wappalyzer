from typing import Any, Mapping, Optional

import aiohttp

from .webpage import IWebPage, WebPage


class WebPageFetcher:
    def __init__(self,
                 browser: str = "none",
                 headers: Optional[Mapping[str, str]] = None,
                 useragent: Optional[str] = None,
                 timeout: int = 10,
                 verify: bool = True,
                 wait_until: str = "networkidle") -> None:
        self.browser = browser
        self.headers = dict(headers or {})
        self.useragent = useragent
        self.timeout = timeout
        self.verify = verify
        self.wait_until = wait_until
        self._session: Optional[aiohttp.ClientSession] = None
        self._playwright = None
        self._browser = None
        self._context = None

    async def __aenter__(self) -> "WebPageFetcher":
        if self.browser == "none":
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(ssl=self.verify)
            self._session = aiohttp.ClientSession(
                headers=self._merged_headers(),
                timeout=timeout,
                connector=connector,
            )
            return self

        if self.browser == "playwright":
            try:
                from playwright.async_api import async_playwright
            except ImportError as exc:
                raise RuntimeError(
                    "Playwright support requires `pip install python-Wappalyzer[browser]` "
                    "and `python -m playwright install chromium`."
                ) from exc

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

            context_headers = self._merged_headers()
            user_agent = self.useragent or context_headers.pop("User-Agent", None)
            self._context = await self._browser.new_context(
                ignore_https_errors=not self.verify,
                user_agent=user_agent,
                extra_http_headers=context_headers or None,
            )
            return self

        raise ValueError("browser must be 'none' or 'playwright'")

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    def _merged_headers(self) -> Mapping[str, str]:
        headers = dict(self.headers)
        if self.useragent:
            headers["User-Agent"] = self.useragent
        return headers

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def fetch(self, url: str) -> IWebPage:
        if self.browser == "none":
            if self._session is None:
                raise RuntimeError("HTTP fetcher is not initialized")
            return await WebPage.new_from_url_async(
                url,
                aiohttp_client_session=self._session,
                timeout=self.timeout,
            )

        if self.browser == "playwright":
            if self._context is None:
                raise RuntimeError("Playwright fetcher is not initialized")
            page = await self._context.new_page()
            try:
                response = await page.goto(
                    url,
                    wait_until=self.wait_until,
                    timeout=self.timeout * 1000,
                )
                headers = await response.all_headers() if response is not None else {}
                return WebPage(page.url, await page.content(), headers)
            finally:
                await page.close()

        raise ValueError("browser must be 'none' or 'playwright'")
