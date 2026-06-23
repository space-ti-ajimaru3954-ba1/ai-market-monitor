import yfinance as yf
import datetime

def get_fundamental_data(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        # 売上成長率 (Financials)
        fin = t.quarterly_financials
        rev_g = None
        if 'Total Revenue' in fin.index and fin.shape[1] >= 4:
            rev_g = (fin.loc['Total Revenue'].iloc[0] / fin.loc['Total Revenue'].iloc[-1] - 1) * 100
        
        # CAPEX成長率 (Cash Flow)
        cf = t.quarterly_cashflow
        capex_labels = ['Capital Expenditure', 'Purchase Of Property Plant Equipment', 'Purchase of Property, Plant and Equipment']
        capex_g = None
        label = next((l for l in capex_labels if l in cf.index), None)
        if label and cf.shape[1] >= 4:
            capex_g = (abs(cf.loc[label].iloc[0]) / abs(cf.loc[label].iloc[-1]) - 1) * 100
            
        return rev_g, capex_g
    except:
        return None, None

def calculate_logic():
    # 1. 市場データ (先行・結果系)
    tickers = {"FNGS": "FNGS", "SOXX": "SOXX", "SPY": "SPY", "VIX": "^VIX"}
    data = {}
    for name, symbol in tickers.items():
        t = yf.Ticker(symbol)
        hist = t.history(period="2y")
        if hist.empty: raise Exception(f"Failed: {symbol}")
        data[name] = hist

    # 先行系: SOXX/SPY相対力
    ratio = data["SOXX"]["Close"] / data["SPY"]["Close"]
    curr_rs_bad = 1 if ratio.iloc[-1] < ratio.rolling(200).mean().iloc[-1] else 0
    # 結果系: FNGS MA200 & VIX
    fngs_c = data["FNGS"]["Close"]
    curr_p_bad = 1 if fngs_c.iloc[-1] < fngs_c.rolling(200).mean().iloc[-1] else 0
    vix = data["VIX"]["Close"].iloc[-1]

    # 2. 原因系：AIファンダメンタル (0:OK, 1:BAD, -1:UNKNOWN)
    # CAPEX (Big4)
    big4 = ["MSFT", "AMZN", "GOOGL", "META"]
    capex_growths = [get_fundamental_data(s)[1] for s in big4]
    valid_c = [g for g in capex_growths if g is not None]
    if not valid_c: f_capex = -1
    else: f_capex = 1 if (sum(valid_c)/len(valid_c)) < 15 else 0

    # NVDA
    nvda_rev_g, _ = get_fundamental_data("NVDA")
    f_nvda = -1 if nvda_rev_g is None else (1 if nvda_rev_g < 30 else 0)

    # Memory (Micron)
    mu_rev_g, _ = get_fundamental_data("MU")
    f_memory = -1 if mu_rev_g is None else (1 if mu_rev_g < 20 else 0)

    # 3. フェーズ判定 (状態管理)
    fundamental_bad_count = [f_capex, f_nvda, f_memory].count(1)
    has_unknown = 1 if -1 in [f_capex, f_nvda, f_memory] else 0
    
    phase = "GREEN" # 正常
    if fundamental_bad_count == 1: phase = "YELLOW"
    if fundamental_bad_count == 2: phase = "ORANGE"
    if fundamental_bad_count >= 3: phase = "RED"
    if fundamental_bad_count >= 3 and curr_rs_bad and curr_p_bad: phase = "PURPLE"
    
    # UNKNOWNがある場合は警告状態を付与
    if has_unknown: phase = "CHECK"

    return phase, f_capex, f_nvda, f_memory, curr_rs_bad, curr_p_bad, int(vix)

try:
    phase, f_c, f_n, f_m, rs_b, p_b, vix = calculate_logic()
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    time_str = now.strftime("%Y-%m-%d %H:%M")

    with open("template.html", "r", encoding="utf-8") as f:
        html = f.read()

    def status_label(val):
        if val == -1: return "UNKNOWN"
        return "BAD" if val == 1 else "OK"

    html = html.replace('{{PHASE}}', phase)
    html = html.replace('{{F_CAPEX}}', status_label(f_c))
    html = html.replace('{{F_NVDA}}', status_label(f_n))
    html = html.replace('{{F_MEMORY}}', status_label(f_m))
    html = html.replace('{{S_RS}}', 'BAD' if rs_b else 'OK')
    html = html.replace('{{S_PRICE}}', 'BAD' if p_b else 'OK')
    html = html.replace('{{VIX}}', str(vix))
    html = html.replace('{{LAST_UPDATE}}', time_str)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
except Exception as e:
    print(f"Error: {e}")
    exit(1)
