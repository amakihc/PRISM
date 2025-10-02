# data_processor.py

import pandas as pd
from scipy.signal import welch
import numpy as np

def load_csv_data(file_path):
    """
    指定されたパスからCSVファイルを読み込み、ヘッダーとサンプリングレートを動的に検出する。
    """
    try:
        # ヘッダー行を動的に見つける
        header_row_index = None
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                # '%', '#'などで始まらない行をヘッダー行と仮定
                if not line.strip().startswith(('%', '#', ';', '[', ' ')):
                    header_row_index = i
                    break

        if header_row_index is None:
            print("Error: Could not find a valid header row in the CSV file.")
            return None, None

        # 見つかったヘッダー行を使ってCSVを読み込む
        # `%`で始まる行はコメントとしてスキップ
        df = pd.read_csv(file_path, comment='%', header=header_row_index)

        # 列名の前後の空白を削除
        df.columns = df.columns.str.strip()

        # 最初の列を時間データとして使用
        time_column = df.columns[0]
        time_data = df[time_column].values

        # 最初の2つのタイムスタンプからサンプリングレートを計算
        time_diff = time_data[1] - time_data[0]
        sampling_rate = 1.0 / time_diff if time_diff != 0 else 0

        # データフレームとサンプリングレートを返す
        return df, sampling_rate

    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None, None

def compute_psd(data, sampling_rate):
    """
    Welch法により、与えられたデータからsqrt(PSD)を計算する
    """
    if sampling_rate <= 0:
        return np.array([]), np.array([])
        
    # SciPyのwelch法を使用してPSDを計算
    frequencies, psd = welch(data, fs=sampling_rate, nperseg=1024)
    # sqrt(PSD)を計算
    sqrt_psd = np.sqrt(psd)
    return frequencies, sqrt_psd