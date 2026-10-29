import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

from config.custom_tools import SCRAPE_WEBSITE_TOOL
from utils.youtube import get_youtube_transcript


def validate_public_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("A public HTTP(S) URL without credentials is required.")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    if not addresses or any(not ipaddress.ip_address(address[4][0]).is_global for address in addresses):
        raise ValueError("Private and local network addresses are not allowed.")
    return url


@tool(SCRAPE_WEBSITE_TOOL["name"], description=SCRAPE_WEBSITE_TOOL["description"])
def scrape_website(url: str) -> str:
    # shortcut: DNS validation cannot prevent rebinding, enforce outbound network policy before public deployment.
    for _ in range(6):
        validate_public_url(url)
        with requests.get(url, timeout=15, stream=True, allow_redirects=False) as response:
            if response.is_redirect:
                url = urljoin(url, response.headers["Location"])
                continue
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if not any(kind in content_type for kind in ("text/html", "text/plain", "application/xhtml+xml")):
                raise ValueError("Only HTML and plain-text pages are supported.")
            content = bytearray()
            for chunk in response.iter_content(8192):
                content.extend(chunk)
                if len(content) > 1_000_000:
                    raise ValueError("Website exceeds the 1 MB download limit.")
            soup = BeautifulSoup(bytes(content), "html.parser")
            for element in soup(["script", "style", "nav", "footer"]):
                element.decompose()
            return f"Source: {url}\n{soup.get_text(' ', strip=True)[:12000]}"
    raise ValueError("Too many redirects.")


@tool
def youtube_transcript(url: str) -> str:
    """Retrieve an English YouTube transcript from a video URL or video ID."""
    transcript = get_youtube_transcript(url)
    if len(transcript) > 60000:
        return f"Source: {url}\n{transcript[:60000]}\n[Transcript truncated]"
    return f"Source: {url}\n{transcript}"


class CustomTools:
    def get_custom_tools(self) -> list:
        return [scrape_website, youtube_transcript]
