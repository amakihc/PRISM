# データ処理用モジュール

import pandas as pd
from scipy.signal import welch
import numpy as np
import io

def is_numeric_start(text):
    """文字列が数値（科学表記含む）で始まっているかチェックするヘルパー関数"""
    try:
        # 文字列の前後の空白を削除
        text = str(text).strip()
        
        # 空白または空文字列は数値ではない
        if not text:
            return False
            
        # 負号、正号、または数字で始まっていれば、数値の可能性が高い
        if text.startswith(('-', '+')) or text[0].isdigit():
            # 試しにfloatに変換し、エラーがなければTrue
            float(text)
            return True
        return False
    except ValueError:
        return False

def load_csv_data(file_path):
    """
    CSVファイルを読み込み、数値データが始まる行の1つ上をヘッダーとして特定し、高速に読み込む。
    
    Args:
        file_path (str): CSVファイルのパス

    Returns:
        tuple: (pd.DataFrame, float) クリーンなデータとサンプリングレート
    """
    try:
        # 1. ヘッダー行のインデックスを特定する
        header_row_index = 0
        
        # ファイル全体を一行ずつ読み込む (メタデータの特定のみに使うため高速)
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                # 最初の列（時間データ）の値を取得
                first_cell = line.strip().split(',')[0].strip()
                
                # 最初のセルが数値で始まっていたら、データ行の開始と判断
                if is_numeric_start(first_cell):
                    # データが始まる行の1つ上をヘッダーとして設定
                    header_row_index = i - 1
                    break
                # ヘッダーが見つからなかった場合（最終的にheader=0になる）
                header_row_index = i 
                
        # 2. 正しいヘッダー行を指定してファイルをPandasで高速に再読み込み
        # header_row_indexが-1以下になる場合は0行目から読み込み
        if header_row_index < 0:
            header_row_index = 0
            
        # on_bad_lines='skip'で、誤った行があっても無視させる
        df = pd.read_csv(file_path, header=header_row_index, comment='%', on_bad_lines='skip')

        # 列名の前後の空白を削除
        df.columns = df.columns.str.strip()
        
        # 3. データクレンジングと型変換 (高速処理)
        
        # すべての列に対して、非数値データをNaNに変換
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 時間列を含め、一つでもNaNがある行を削除
        # これがあなたのアイデア「全部数値になったら」を高速に実行する部分です
        data_columns_including_time = df.columns
        df.dropna(subset=data_columns_including_time, how='any', inplace=True) # how='any'で一つでもNaNがあれば削除

        if df.empty or len(df) < 2:
            print("Warning: No valid numeric data rows were found or data is too short.")
            return None, None
        
        # 4. サンプリングレートの計算
        
        time_column = df.columns[0]
        time_data = df[time_column].values

        time_diff = time_data[1] - time_data[0]
        sampling_rate = 1.0 / time_diff if time_diff != 0 else 0

        return df, sampling_rate

    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None, None

def compute_psd(data, sampling_rate):
    """Welch法により、与えられたデータからsqrt(PSD)を計算する"""
    if sampling_rate <= 0:
        return np.array([]), np.array([])
        
    frequencies, psd = welch(data, fs=sampling_rate, nperseg=len(data))
    sqrt_psd = np.sqrt(psd)
    return frequencies, sqrt_psd