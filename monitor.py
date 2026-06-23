import yfinance as yf
import datetime
import os

def calculate_scores():
    # データ取得（過去1ヶ月分）
    # 修正点: ^SHY を SHY (ETF) に変更
    tickers = {
        "NVDA": "NVDA",   
        "TSM": "TSM",     
        "VIX": "^VIX",    
        "10Y": "^TNX",    
        "SHY": "SHY"      
    }
    
    data = {}
    for name, symbol in tickers.items():
        t = yf.Ticker(symbol)
        data[name] = t.history(period="1mo")

    # 1. AIサイクルスコア (NVDAの移動平均乖離)
    nvda_now = data["NVDA"]["Close"].iloc[-1]
    nvda_ma = data["NVDA"]["Close"].mean()
    ai_score = int(max(0, min(100, (nvda_now / nvda_ma) * 80)))

    # 2. 市場リスクスコア (VIXのレベル)
    vix_now = data["VIX"]["Close"].iloc[-1]
    market_score = int(max(0, min(100, (vix_now / 40) * 100)))

    # 3. 景気リスクスコア
    # 短期債ETF(SHY)が急落＝金利急上昇＝景気リスク、という簡易ロジック
    shy_now = data["SHY"]["Close"].iloc[-1]
    shy_ma = data["SHY"]["Close"].mean()
    economy_score = 25
    if shy_now < shy_ma:
        economy_score += 15 # 短期債価格の下落（金利上昇）による警戒点灯

    return ai_score, market_score, economy_score, nvda_now, vix_now

# スコア取得
ai, mkt, eco, nvda_p, vix_p = calculate_scores()
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
time_str = now.strftime("%Y-%m-%d %H:%M")

# HTMLの書き換え
with open("template.html", "r", encoding="utf-8") as f:
    html = f.read()

# データの流し込み
html = html.replace('id="aiVal">88', f'id="aiVal">{ai}')
html = html.replace('id="marketVal">28', f'id="marketVal">{mkt}')
html = html.replace('id="economyScore">24', f'id="economyScore">{eco}')
html = html.replace('2026年6月21日', f'{time_str} (日本時間)')

# 表示数値の同期（上部の大きな数字用）
html = html.replace('id="aiScore">88', f'id="aiScore">{ai}')
html = html.replace('id="marketScore">28', f'id="marketScore">{mkt}')

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
