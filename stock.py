from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal
import yfinance as yf
import math
import pandas as pd
import plotly.graph_objects as go
import gradio as gr

# 建立 FastAPI 應用實例
app = FastAPI(title="台股查詢 API")

# 設定 CORS，允許所有來源的跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/stock/{symbol}")
def _tw_suffix(s: str) -> str:
    return s if "." in s else f"{s}.TW"

def get_stock(
    symbol: str,
    period: Literal["1d", "5d", "1mo", "1y"] = Query("1mo", description="時間區間: 1d(1天), 5d(1週), 1mo(1月), 1y(1年)"),
):
    symbol = _tw_suffix(symbol)

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"無法取得股票資料: {e}")

    # 若無資料則回傳 404
    if hist.empty:
        raise HTTPException(status_code=404, detail=f"找不到股票代號: {symbol}")

    # 取得股票基本資訊
    try:
        info = ticker.info or {}
    except Exception:
        info = {}

    # 將歷史資料逐筆轉為 dict 列表
    def _to_num(val):
        """將 NaN 或 None 轉為 None，避免 int() 失敗"""
        return None if (isinstance(val, float) and math.isnan(val)) or val is None else val

    records = []
    for date, row in hist.iterrows():
        records.append({
            "date": str(date),
            "open": _to_num(row.get("Open")),
            "high": _to_num(row.get("High")),
            "low": _to_num(row.get("Low")),
            "close": _to_num(row.get("Close")),
            "volume": int(_to_num(row.get("Volume", 0)) or 0),
            "dividends": _to_num(row.get("Dividends", 0)) or 0,
            "stock_splits": _to_num(row.get("Stock Splits", 0)) or 0,
        })

    # 回傳查詢結果
    return {
        "symbol": symbol,
        "period": period,
        "count": len(records),
        "data": records,
        "info": {
            "name": info.get("shortName", "N/A"),
            "current_price": info.get("currentPrice", "N/A"),
            "high_52w": info.get("fiftyTwoWeekHigh", "N/A"),
            "low_52w": info.get("fiftyTwoWeekLow", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
        },
    }


# 直接執行此檔案時啟動伺服器
def fetch_stock(symbol: str, period: str):
    if not symbol:
        return None, None, "請輸入股票代號"

    symbol = _tw_suffix(symbol)

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
    except Exception as e:
        return None, None, f"無法取得資料: {e}"

    if hist.empty:
        return None, None, f"找不到股票代號: {symbol}"

    try:
        info = ticker.info or {}
    except Exception:
        info = {}

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"],
        name="K線",
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
    ))
    fig.add_trace(go.Bar(
        x=hist.index, y=hist["Volume"],
        name="成交量", yaxis="y2",
        marker_color="rgba(100,149,237,0.4)",
    ))
    fig.update_layout(
        template="plotly_dark",
        title=f"{symbol.replace('.TW','')} - {info.get('shortName', '')}",
        xaxis_title="日期",
        yaxis_title="價格",
        yaxis2=dict(title="成交量", overlaying="y", side="right"),
        hovermode="x unified",
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        xaxis=dict(gridcolor="#2d2d44"),
        yaxis=dict(gridcolor="#2d2d44"),
    )

    info_text = (
        f"**名稱**: {info.get('shortName', 'N/A')}\n"
        f"**現價**: {info.get('currentPrice', 'N/A')}\n"
        f"**52週高**: {info.get('fiftyTwoWeekHigh', 'N/A')}\n"
        f"**52週低**: {info.get('fiftyTwoWeekLow', 'N/A')}\n"
        f"**市值**: {info.get('marketCap', 'N/A')}"
    )
    return fig, info_text, "✅ 查詢成功"


css = """
:root { --gradio-primary: #6c63ff; --gradio-primary-hover: #5a52d5; }
.gr-button { background: linear-gradient(135deg, #6c63ff, #4834d4) !important; border: none !important; color: white !important; font-weight: 600 !important; }
.gr-button:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(108,99,255,0.4) !important; }
.gr-input, .gr-dropdown { background: #16213e !important; border: 1px solid #2d2d44 !important; color: #e0e0e0 !important; }
.gr-input:focus, .gr-dropdown:focus { border-color: #6c63ff !important; box-shadow: 0 0 0 2px rgba(108,99,255,0.2) !important; }
label { color: #a0a0b8 !important; font-weight: 500 !important; }
footer { display: none !important; }
"""

with gr.Blocks(title="台股查詢") as demo:
    gr.Markdown(
        "# 📈 台股查詢系統",
    )
    gr.Markdown("輸入台股代號（如 **2330** 台積電、**2317** 鴻海）查詢即時股價與歷史走勢")

    with gr.Row(equal_height=True):
        symbol_input = gr.Textbox(label="股票代號", placeholder="例如: 2330", scale=2)
        period_input = gr.Dropdown(
            choices=["1d", "5d", "1mo", "3mo", "6mo", "1y"],
            value="1mo", label="時間區間", scale=1,
        )
        search_btn = gr.Button("🔍 查詢", scale=1, variant="primary")

    with gr.Row():
        with gr.Column(scale=3):
            plot_output = gr.Plot(label="股價走勢")
        with gr.Column(scale=1):
            info_output = gr.Markdown("### 基本資訊\n請輸入股票代號查詢")

    search_btn.click(fn=fetch_stock, inputs=[symbol_input, period_input], outputs=[plot_output, info_output, gr.Textbox(visible=False)], queue=False)

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False, theme=gr.themes.Soft(primary_hue="violet", neutral_hue="slate"), css=css)