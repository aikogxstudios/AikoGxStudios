"""Add date labels to the generated snake without changing its animation."""
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen
import re
import xml.etree.ElementTree as ET

def main():
    request = Request("https://github.com/users/aikogxstudios/contributions", headers={"User-Agent": "AikoGx-calendar"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")
    dates = sorted({date.fromisoformat(day) for day in re.findall(r'data-date="([^"]+)"', html)})
    if not dates:
        raise RuntimeError("No calendar dates found")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for path in Path("/tmp/aikogx-snake").glob("*.svg"):
        source = path.read_text()
        root = ET.fromstring(source)
        cells = [node for node in root if node.tag.endswith("rect") and "c" in node.get("class", "").split()]
        if len(cells) != len(dates):
            raise RuntimeError("Calendar dates and animation cells differ; refusing inaccurate labels")
        xs = sorted({float(cell.get("x")) for cell in cells})
        ys = sorted({float(cell.get("y")) for cell in cells})
        if len(ys) != 7 or len(xs) < 52:
            raise RuntimeError("Unexpected animation grid")
        x0, y0 = xs[0], ys[0]
        pitch = xs[1] - xs[0]
        labels = []
        previous = None
        last_x = -1000
        for day in dates:
            key = (day.year, day.month)
            if key != previous:
                x = x0 + ((day - dates[0]).days // 7) * pitch
                if x - last_x >= 30:
                    labels.append(f'<text x="{x:g}" y="-10">{months[day.month-1]}</text>')
                    last_x = x
                previous = key
        for name, index in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
            labels.append(f'<text x="-8" y="{y0+index*pitch+9:g}" text-anchor="end">{name}</text>')
        x, y, width, height = map(float, root.get("viewBox").split())
        new_x = min(x, -42)
        new_width = width + x - new_x
        source = re.sub(r'viewBox="[^"]+"', f'viewBox="{new_x:g} {y:g} {new_width:g} {height:g}"', source, count=1)
        source = re.sub(r'width="[^"]+"', f'width="{new_width:g}"', source, count=1)
        color = "#9198a1" if "dark" in path.name else "#59636e"
        group = f'<g fill="{color}" font-family="Arial,sans-serif" font-size="10">' + "".join(labels) + "</g>"
        source = source.replace("</svg>", group + "</svg>")
        ET.fromstring(source)
        path.write_text(source)
        print(f"Labeled {path.name}: {dates[0]} to {dates[-1]}")

if __name__ == "__main__":
    main()
