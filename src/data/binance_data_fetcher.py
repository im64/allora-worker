import os
import time
from typing import Optional
from datetime import datetime

import pandas as pd
import requests

BASE_URL = "https://fapi.binance.com"


class DataFetcher:
    """
    A class to fetch and normalize data from Binance Futures API.
    """

    def __init__(self, cache_folder="data/sets"):
        self.cache_folder = cache_folder
        if not os.path.exists(self.cache_folder):
            os.makedirs(self.cache_folder)  # Ensure the 'sets' folder exists

    def _generate_filename(self, symbol, start_time, end_time, interval):
        """Generate a unique filename for the parquet file based on the parameters."""
        # Convert timestamps to dates for filename
        start_date = pd.to_datetime(start_time, unit='ms').strftime('%Y-%m-%d') if start_time else "start"
        end_date = pd.to_datetime(end_time, unit='ms').strftime('%Y-%m-%d') if end_time else "end"
        return os.path.join(
            self.cache_folder, f"{symbol}_{start_date}_to_{end_date}_{interval}.parquet"
        )

    def fetch_symbols(self):
        """Fetches all tradable symbols from the Binance Futures API."""
        url = f"{BASE_URL}/fapi/v1/exchangeInfo"
        response = requests.get(url)
        print(f'Fetching data using URL: {url}')
        response.raise_for_status()
        data = response.json()
        return [symbol['symbol'] for symbol in data['symbols']]

    def fetch_klines(self, symbol, interval='1m', start_time=None, end_time=None, limit=1500):
        """Fetch historical kline (candlestick) data for a given symbol."""
        url = f"{BASE_URL}/fapi/v1/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_time,
            'endTime': end_time,
            'limit': limit
        }
        # Remove None values from params
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, params=params)
        params_str = '&'.join([f'{k}={v}' for k,v in params.items()])
        print(f'Fetching data using URL: {url}?{params_str}')
        response.raise_for_status()
        return response.json()

    def _normalize_binance_data(self, data) -> pd.DataFrame:
        """Normalize Binance kline data to match the required schema."""
        if not data:
            return pd.DataFrame()

        columns = [
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ]

        df = pd.DataFrame(data, columns=columns)

        # Convert timestamps to datetime
        df['date'] = pd.to_datetime(df['close_time'], unit='ms')

        # Convert numeric columns
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])

        # Select and reorder columns to match the standard format
        return df[['date', 'open', 'high', 'low', 'close', 'volume']]

    def fetch_data(self, symbol: str, interval: str = '1m',
                  start_time: Optional[str] = None,
                  end_time: Optional[str] = None,
                  chunk_size: int = 30 * 24 * 60 * 60 * 1000  # 30 days in milliseconds
                  ) -> pd.DataFrame:
        """
        Fetch historical data for a symbol in chunks to handle rate limits.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Kline interval (e.g., '1m', '5m', '1h', '1d')
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            chunk_size: Size of each data chunk in milliseconds

        Returns:
            DataFrame with historical price data
        """


        converted_start_time = int(datetime.strptime(start_time, "%Y-%m-%d").timestamp()) * 1000 if start_time else int(time.time() * 1000)
        converted_end_time = int(datetime.strptime(end_time, "%Y-%m-%d").timestamp()) * 1000 if end_time else converted_start_time - (6 * 30 * 24 * 60 * 60 * 1000)

        filename = self._generate_filename(symbol, converted_start_time, converted_end_time, interval)

        # Always fetch fresh data to ensure we have the most recent prices
        all_data = []
        current_start = converted_start_time

        # Fetch data in chunks
        while current_start < converted_end_time:
            current_end = min(current_start + chunk_size, converted_end_time)

            try:
                print(f"Fetching data for {symbol} from {pd.to_datetime(current_start, unit='ms')} "
                      f"to {pd.to_datetime(current_end, unit='ms')}...")

                chunk_data = self.fetch_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=current_start,
                    end_time=current_end
                )

                if not chunk_data:
                    print("No more data available.")
                    break

                all_data.extend(chunk_data)
                current_start = chunk_data[-1][6] + 1  # Next start time is after the last close time

                time.sleep(0.2)  # Rate limiting

            except Exception as e:
                print(f"Error fetching data: {e}")
                break

        if all_data:
            df = self._normalize_binance_data(all_data)
            print(f"Saving data to {filename}...")
            df.to_parquet(filename, index=False)
            return df

        return pd.DataFrame()

    def download_all_symbols(self, interval='1d', period="6_months"):
        """
        Download data for all available trading pairs.

        Args:
            interval: Kline interval (e.g., '1m', '5m', '1h', '1d')
            period: Period identifier for the filename
        """
        try:
            symbols = self.fetch_symbols()
            print(f"Found {len(symbols)} symbols.")
        except Exception as e:
            print(f"Error fetching symbols: {e}")
            return

        for symbol in symbols:
            try:
                print(f"Processing {symbol}...")
                self.fetch_data(symbol=symbol, interval=interval)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
