import yfinance as yf
import datetime
import os

def calculate_scores():
    # データ取得（過去1ヶ月分）
    tickers = {
        "NVDA": "NVDA",   # AI代表
        "TSM": "TSM",     # 半導体生産
        "VIX": "^VIX",    # 恐怖指数
        "10Y": "^TNX",    # 米10年債
        "2Y": "^SHY"      # 米2年債（短期）
    }
    
    data = {}
    for name, symbol in tickers.items():
        t = yf.Ticker(symbol)
        data[name] = t.history(period="1mo")

    # 1. AIサイクルスコア (NVDAとTSMの移動平均乖離率などで算出)
    nvda_now = data["NVDA"]["Close"].iloc[-1]
    nvda_ma = data["NVDA"]["Close"].mean()
    ai_score = int(max(0, min(100, (nvda_now / nvda_ma) * 80)))

    # 2. 市場リスクスコア (VIXのレベルで算出)
    vix_now = data["VIX"]["Close"].iloc[-1]
    market_score = int(max(0, min(100, (vix_now / 40) * 100)))

    # 3. 景気リスクスコア (逆イールドを監視)
    yield_10y = data["10Y"]["Close"].iloc[-1]
    economy_score = 25 # デフォルト
    if yield_10y < 3.5: economy_score += 20 # 低金利/異常時

    return ai_score, market_score, economy_score, nvda_now, vix_now

# スコア取得
ai, mkt, eco, nvda_p, vix_p = calculate_scores()
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
time_str = now.strftime("%Y-%m-%d %H:%M")

# HTMLのテンプレートを読み込んで置換（元のHTMLをベースに）
with open("template.html", "r", encoding="utf-8") as f:
    html = f.read()

# データの流し込み
html = html.replace('id="aiScore">88', f'id="aiScore">{ai}')
html = html.replace('id="marketScore">28', f'id="marketScore">{mkt}')
html = html.replace('id="economyScore">24', f'id="economyScore">{eco}')
html = html.replace('2026年6月21日', f'更新: {time_str} (日本時間)')

# ファイル書き出し
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
