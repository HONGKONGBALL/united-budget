这是一个离线的家庭开支小工具，读取本地价格表，按类别汇总花费、算出每个月的合计，并列出三笔最大的支出。金额用港币，样例是普通杂货和交通，不需要联网，也不调用任何付费接口。

# United Budget

A small offline household budget for United Hackathons V1 (Devonomics).

`budget.py` reads `data.csv` (columns: `item`, `category`, `price`, `date`) and prints a summary. It also writes:

- `output/budget.txt` — the same summary as plain text
- `output/budget.html` — a single local page with category totals, monthly totals, and the three largest purchases
- `output/budget.png` — a chart drawn from that run with Pillow (bars and figures come from the CSV, not a pasted screenshot)

Prices in the sample file are generic grocery and transit amounts in Hong Kong dollars. There are no personal names.

## Run

```bash
python3 budget.py
```

Run it from this directory, or from anywhere: the script looks for `data.csv` next to itself and writes `output/` beside the script.

It is offline. It does not call the network, and it does not use a paid API. Python 3 and Pillow are enough.
