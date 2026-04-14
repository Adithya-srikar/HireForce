import re
from io import BytesIO
from PyPDF2 import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def extract_urls(text: str) -> dict:
    urls = {"linkedin": None, "github": None, "leetcode": None}

    linkedin_pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)"
    match = re.search(linkedin_pattern, text)
    if match:
        urls["linkedin"] = f"https://linkedin.com/in/{match.group(1)}"

    github_pattern = r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)"
    match = re.search(github_pattern, text)
    if match:
        urls["github"] = f"https://github.com/{match.group(1)}"

    leetcode_pattern = r"(?:https?://)?(?:www\.)?leetcode\.com/(?:u/)?([a-zA-Z0-9_-]+)"
    match = re.search(leetcode_pattern, text)
    if match:
        urls["leetcode"] = f"https://leetcode.com/u/{match.group(1)}"

    return urls


def extract_username_from_url(url: str, platform: str) -> str | None:
    if not url:
        return None
    patterns = {
        "linkedin": r"linkedin\.com/in/([a-zA-Z0-9_-]+)",
        "github": r"github\.com/([a-zA-Z0-9_-]+)",
        "leetcode": r"leetcode\.com/(?:u/)?([a-zA-Z0-9_-]+)",
    }
    match = re.search(patterns.get(platform, ""), url)
    return match.group(1) if match else None
