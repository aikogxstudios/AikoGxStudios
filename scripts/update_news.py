"""Refresh only the public studio-news section. No credentials required."""
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import re
import xml.etree.ElementTree as ET

def main():
    request = Request("https://aikogx.es/feed/", headers={"User-Agent": "AikoGx-Profile-News"})
    with urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read(2_000_000))
    entries = []
    for item in root.findall("./channel/item"):
        title = " ".join((item.findtext("title") or "").split())
        link = (item.findtext("link") or "").strip()
        url = urlsplit(link)
        if not title or url.scheme != "https" or url.hostname not in {"aikogx.es", "www.aikogx.es"}:
            continue
        title = re.sub(r"([\\\[\]_*\x60<>])", r"\\\1", title)
        link = link.replace("(", "%28").replace(")", "%29")
        date = parsedate_to_datetime(item.findtext("pubDate")).astimezone(timezone.utc)
        entries.append((date, title, link))
    if not entries:
        raise RuntimeError("No valid public news; README preserved")
    lines = [f"- **{date.strftime('%d %b %Y')}** — {title}"
             for date, title, link in sorted(entries, reverse=True)[:3]]
    path = Path("README.md")
    original = path.read_text(encoding="utf-8")
    pattern = r"(<!-- START:STUDIO_UPDATES -->)\n.*?\n(<!-- END:STUDIO_UPDATES -->)"
    updated, count = re.subn(pattern, lambda match: match[1] + "\n" + "\n".join(lines) + "\n" + match[2], original, flags=re.S)
    if count != 1:
        raise RuntimeError("Expected one news section; README preserved")
    if updated != original:
        path.write_text(updated, encoding="utf-8")
    print(f"Checked {len(lines)} public news entries.")

if __name__ == "__main__":
    main()
