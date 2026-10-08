#!/usr/bin/env python3
"""Offline household budget from a local price CSV. No network calls."""

import csv
import html
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data.csv"
OUT_DIR = ROOT / "output"

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

PALETTE = {
    "Produce": (46, 125, 80),
    "Dairy": (36, 99, 168),
    "Pantry": (184, 112, 32),
    "Transit": (14, 116, 128),
}
FALLBACK = [
    (46, 125, 80),
    (36, 99, 168),
    (184, 112, 32),
    (14, 116, 128),
    (120, 72, 150),
    (168, 62, 62),
]


def money(amount):
    return f"HK${amount:,.2f}"


def load_rows(path):
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        needed = {"item", "category", "price", "date"}
        if not needed.issubset(fields):
            missing = ", ".join(sorted(needed - fields))
            raise SystemExit(f"data.csv is missing columns: {missing}")
        for line_no, raw in enumerate(reader, start=2):
            item = (raw.get("item") or "").strip()
            category = (raw.get("category") or "").strip()
            date = (raw.get("date") or "").strip()
            if not item or not category or not date:
                raise SystemExit(f"Blank item, category, or date on line {line_no}")
            if len(date) < 7 or date[4] != "-":
                raise SystemExit(f"Date must look like YYYY-MM-DD on line {line_no}")
            try:
                price = round(float(raw["price"]), 2)
            except (TypeError, ValueError):
                raise SystemExit(f"Price is not a number on line {line_no}")
            if price < 0:
                raise SystemExit(f"Price cannot be negative on line {line_no}")
            rows.append(
                {
                    "item": item,
                    "category": category,
                    "price": price,
                    "date": date,
                    "month": date[:7],
                }
            )
    if not rows:
        raise SystemExit("data.csv has no purchases")
    return rows


def summarize(rows):
    by_category = defaultdict(float)
    by_month = defaultdict(float)
    for row in rows:
        by_category[row["category"]] += row["price"]
        by_month[row["month"]] += row["price"]
    categories = sorted(by_category.items(), key=lambda pair: (-pair[1], pair[0]))
    months = sorted(by_month.items())
    largest = sorted(rows, key=lambda row: (-row["price"], row["date"], row["item"]))[:3]
    return categories, months, largest


def summary_text(rows, categories, months, largest):
    lines = [
        "Household budget",
        f"Purchases: {len(rows)}",
        "",
        "Spending by category",
    ]
    for name, total in categories:
        lines.append(f"  {name}: {money(total)}")
    lines.append("")
    lines.append("Monthly totals")
    for month, total in months:
        lines.append(f"  {month}: {money(total)}")
    grand = sum(total for _, total in months)
    lines.append(f"  All months: {money(grand)}")
    lines.append("")
    lines.append("Three largest purchases")
    for index, row in enumerate(largest, start=1):
        lines.append(
            f"  {index}. {row['item']} ({row['category']}) "
            f"{money(row['price'])} on {row['date']}"
        )
    return "\n".join(lines) + "\n"


def write_html(path, rows, categories, months, largest):
    grand = sum(total for _, total in months)
    cat_rows = "\n".join(
        "<tr><td>{name}</td><td class='num'>{amount}</td></tr>".format(
            name=html.escape(name), amount=money(total)
        )
        for name, total in categories
    )
    month_rows = "\n".join(
        "<tr><td>{month}</td><td class='num'>{amount}</td></tr>".format(
            month=html.escape(month), amount=money(total)
        )
        for month, total in months
    )
    top_rows = "\n".join(
        "<tr><td>{n}</td><td>{item}</td><td>{cat}</td>"
        "<td class='num'>{amount}</td><td>{date}</td></tr>".format(
            n=index,
            item=html.escape(row["item"]),
            cat=html.escape(row["category"]),
            amount=money(row["price"]),
            date=html.escape(row["date"]),
        )
        for index, row in enumerate(largest, start=1)
    )
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Household budget</title>
<style>
  body {{ font-family: sans-serif; margin: 2rem; color: #1c1c1c; background: #f7f4ee; }}
  h1 {{ margin-bottom: 0.2rem; }}
  p {{ color: #444; }}
  section {{ background: #fff; padding: 1rem 1.2rem; margin: 1rem 0; border: 1px solid #e2dcd0; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ text-align: left; padding: 0.35rem 0.5rem; border-bottom: 1px solid #eee; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .grand {{ font-weight: bold; }}
</style>
</head>
<body>
  <h1>Household budget</h1>
  <p>Offline summary of {len(rows)} local purchases. Amounts are Hong Kong dollars.</p>
  <section>
    <h2>Spending by category</h2>
    <table>
      <thead><tr><th>Category</th><th class="num">Total</th></tr></thead>
      <tbody>
        {cat_rows}
      </tbody>
    </table>
  </section>
  <section>
    <h2>Monthly totals</h2>
    <table>
      <thead><tr><th>Month</th><th class="num">Total</th></tr></thead>
      <tbody>
        {month_rows}
        <tr class="grand"><td>All months</td><td class="num">{money(grand)}</td></tr>
      </tbody>
    </table>
  </section>
  <section>
    <h2>Three largest purchases</h2>
    <table>
      <thead><tr><th>#</th><th>Item</th><th>Category</th><th class="num">Price</th><th>Date</th></tr></thead>
      <tbody>
        {top_rows}
      </tbody>
    </table>
  </section>
</body>
</html>
"""
    path.write_text(page, encoding="utf-8")


def color_for(name, index):
    return PALETTE.get(name, FALLBACK[index % len(FALLBACK)])


def render_png(path, categories, months, largest):
    width, height = 1200, 860
    image = Image.new("RGB", (width, height), (247, 244, 238))
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(FONT_BOLD, 36)
    head = ImageFont.truetype(FONT_BOLD, 22)
    body = ImageFont.truetype(FONT, 18)
    small = ImageFont.truetype(FONT, 16)
    mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 18)

    draw.rectangle((0, 0, width, 92), fill=(28, 48, 42))
    draw.text((40, 22), "Household budget", font=title, fill=(247, 244, 238))
    draw.text((40, 64), "Category spend, monthly totals, largest purchases  ·  HKD", font=small, fill=(196, 214, 204))

    draw.text((40, 120), "Spending by category", font=head, fill=(28, 48, 42))
    max_total = max(total for _, total in categories) if categories else 1
    panel_x = 900
    bar_left = 160
    widest_label = max(
        (draw.textlength(money(total), font=mono) for _, total in categories),
        default=0,
    )
    bar_max = int(panel_x - 28 - widest_label - bar_left)
    top = 168
    for index, (name, total) in enumerate(categories):
        y = top + index * 72
        color = color_for(name, index)
        draw.text((40, y + 8), name, font=body, fill=(40, 40, 40))
        length = int(bar_max * (total / max_total)) if max_total else 0
        length = max(length, 4)
        draw.rounded_rectangle((bar_left, y, bar_left + length, y + 36), radius=6, fill=color)
        draw.text((bar_left + length + 12, y + 8), money(total), font=mono, fill=(30, 30, 30))

    draw.rounded_rectangle((panel_x, 150, 1160, 430), radius=10, fill=(255, 255, 255), outline=(226, 220, 208))
    draw.text((panel_x + 20, 168), "Monthly totals", font=head, fill=(28, 48, 42))
    y = 214
    for month, total in months:
        draw.text((panel_x + 20, y), month, font=body, fill=(60, 60, 60))
        label = money(total)
        tw = draw.textlength(label, font=mono)
        draw.text((1140 - tw, y), label, font=mono, fill=(20, 20, 20))
        y += 36
    grand = sum(total for _, total in months)
    draw.line((panel_x + 20, y + 4, 1140, y + 4), fill=(210, 200, 186), width=1)
    draw.text((panel_x + 20, y + 16), "All months", font=ImageFont.truetype(FONT_BOLD, 18), fill=(28, 48, 42))
    label = money(grand)
    tw = draw.textlength(label, font=mono)
    draw.text((1140 - tw, y + 16), label, font=mono, fill=(28, 48, 42))

    draw.text((40, 520), "Three largest purchases", font=head, fill=(28, 48, 42))
    card_w = 360
    for index, row in enumerate(largest):
        x = 40 + index * (card_w + 20)
        draw.rounded_rectangle((x, 566, x + card_w, 800), radius=10, fill=(255, 255, 255), outline=(226, 220, 208))
        draw.rectangle((x, 566, x + 8, 800), fill=color_for(row["category"], index))
        draw.text((x + 24, 586), f"#{index + 1}", font=head, fill=(28, 48, 42))
        draw.text((x + 24, 630), row["item"], font=ImageFont.truetype(FONT_BOLD, 20), fill=(20, 20, 20))
        draw.text((x + 24, 668), row["category"], font=body, fill=(90, 90, 90))
        draw.text((x + 24, 712), money(row["price"]), font=ImageFont.truetype(FONT_BOLD, 26), fill=(28, 48, 42))
        draw.text((x + 24, 752), row["date"], font=small, fill=(90, 90, 90))

    image.save(path, "PNG")


def main():
    rows = load_rows(DATA_PATH)
    categories, months, largest = summarize(rows)
    text = summary_text(rows, categories, months, largest)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "budget.txt").write_text(text, encoding="utf-8")
    write_html(OUT_DIR / "budget.html", rows, categories, months, largest)
    render_png(OUT_DIR / "budget.png", categories, months, largest)
    print(text, end="")
    print(f"Wrote {OUT_DIR / 'budget.txt'}")
    print(f"Wrote {OUT_DIR / 'budget.html'}")
    print(f"Wrote {OUT_DIR / 'budget.png'}")


if __name__ == "__main__":
    main()
