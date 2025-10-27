import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import logging

class DBLoader:
    def __init__(self, db_url="postgresql://ai_user:bbmuser01@192.168.0.137:5433/ai_stock"):
        self.engine = create_engine(db_url)
        self.create_table()

    def create_table(self):
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS daily_prices (
                    date DATE NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    close NUMERIC(10,4) NOT NULL,
                    PRIMARY KEY (date, symbol)
                )
            """))
            conn.commit()

    def download_and_save(self, symbols, start=None, end=None):
        end = end or datetime.today().strftime("%Y-%m-%d")
        for s in symbols:
            try:
                # 關鍵：每次只下載一檔，避免 MultiIndex
                df = yf.download(s, start=start, end=end, progress=False, auto_adjust=False)
                if df.empty:
                    print(f"  {s}: 無資料")
                    continue
                
                # ***** START OF CRITICAL FIX *****
                # 檢查欄位是否為 MultiIndex，並進行扁平化
                if isinstance(df.columns, pd.MultiIndex):
                    # 將 MultiIndex 的第二層作為新的欄位名稱（例如 ['Close', 'QQQ'] -> 'Close'）
                    df.columns = df.columns.droplevel(1)
                # ***** END OF CRITICAL FIX *****

                # 診斷 (現在只會輸出單層欄位名稱)
                # print(f"  {s} 欄位: {list(df.columns)}") # 可以移除這行或保持
                
                if 'Close' not in df.columns:
                    print(f"  {s}: 無 Close 欄位，跳過")
                    continue
                
                data = df['Close'].reset_index()
                data['symbol'] = s
                # 確保 'Date' 欄位存在且名稱正確
                data = data[['Date', 'symbol', 'Close']].rename(columns={'Date': 'date', 'Close': 'close'})
                data.to_sql('daily_prices', self.engine, if_exists='append', index=False, method='multi')
                print(f"  {s}: {len(data)} 筆已儲存到 PostgreSQL (192.168.0.137:5433)")
            except Exception as e:
                print(f"  {s} 儲存失敗: {e}")

    def load_from_db(self, symbols, start, end):
        query = f"""
            SELECT date, symbol, close
            FROM daily_prices
            WHERE symbol IN ({','.join(f"'{s}'" for s in symbols)})
              AND date BETWEEN '{start}' AND '{end}'
        """
        df = pd.read_sql(query, self.engine)
        if df.empty:
            return None
        return df.pivot(index='date', columns='symbol', values='close')

if __name__ == "__main__":
    loader = DBLoader()
    symbols = ["QQQ", "NVDA", "TSLA", "AAPL", "MSFT"]
    loader.download_and_save(symbols, start="2023-01-01")
