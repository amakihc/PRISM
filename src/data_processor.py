# データ処理モジュール

import pandas as pd
from scipy.signal import welch, butter, filtfilt, bilinear
import numpy as np
import csv
import io

def is_numeric_start(text):
    """文字列が数値（科学表記含む）で始まっているかチェックするヘルパー関数"""
    try:
        text = str(text).strip()
        if not text:
            return False
        
        float(text)
        return True
    except ValueError:
        return False

def load_csv_data(file_path):
    """
    CSVファイルを読み込み、ヘッダーを特定し、非数値データを含む行を削除する。
    """
    try:
        # 1. ヘッダー行のインデックスを特定
        header_row_index = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                first_cell = line.strip().split(',')[0].strip()
                
                # 最初のセルが数値で始まっていたら、データ行の開始と判断
                if is_numeric_start(first_cell):
                    header_row_index = i - 1
                    break
                header_row_index = i 
                
        # 2. 正しいヘッダー行を指定してPandasで高速に再読み込み
        if header_row_index < 0:
            header_row_index = 0
            
        df = pd.read_csv(file_path, header=header_row_index, comment='%', on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        
        # 3. データクレンジングと型変換
        
        # すべての列を数値に変換し、変換できない値をNaNとする
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 一つでもNaNがある行を削除
        data_columns_including_time = df.columns
        df.dropna(subset=data_columns_including_time, how='any', inplace=True) 

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

def compute_psd(data, sampling_rate, smoothing_level=1):
    """
    Welch法により、smoothing_levelに基づいてnpersegを対数空間で決定し、sqrt(PSD)を計算する。
    smoothing_level=1でnperseg=データ長の50%、smoothing_level=10でnperseg=256。
    スライダー値の変化に対して視覚的な変化量が均一になるように対数補間する。
    """
    if sampling_rate <= 0 or len(data) < 2:
        return np.array([]), np.array([])

    data_length = len(data)
    nperseg_max = max(512, int(data_length * 0.5))
    nperseg_min = 512

    # smoothing_level: 1 (Low, max) ～ 10 (High, min)
    # 対数空間で補間
    log_max = np.log10(nperseg_max)
    log_min = np.log10(nperseg_min)
    alpha = (smoothing_level - 1) / 9  # 0～1
    log_nperseg = log_max + (log_min - log_max) * alpha
    nperseg_value = int(10 ** log_nperseg)
    nperseg_value = max(nperseg_min, min(nperseg_max, nperseg_value))
    nperseg_value = int(nperseg_value // 2 * 2)  # 偶数にする
    if nperseg_value == 0:
        nperseg_value = data_length

    frequencies, psd = welch(data, fs=sampling_rate, nperseg=nperseg_value)
    sqrt_psd = np.sqrt(psd)
    return frequencies, sqrt_psd

def apply_lpf(data, sampling_rate, lpf_level):
    """バターワースローパスフィルタを適用する"""
    # 1. フィルタOFFの判定
    if lpf_level == 1 or sampling_rate == 0:
        return data
        
    nyquist = sampling_rate / 2

    T = len(data) / sampling_rate
    delta_f = 1.0 / T

    min_cutoff = 5.0 * delta_f
    
    # 2. LPFレベルからカットオフ周波数 (cutoff_freq) を決定する
    
    # LPF OFF(1)はスキップ済み。スライダー値 2〜10 を 0〜1 の範囲に正規化
    normalized_value = (lpf_level - 2) / 8.0 
    normalized_value = np.clip(normalized_value, 0, 1)

    # 対数スケール
    min_log_ratio = np.log10(min_cutoff)
    max_log_ratio = np.log10(nyquist / 10)

    # 対数的に補間し、カットオフ周波数を決定
    log_cutoff = max_log_ratio - normalized_value * (max_log_ratio - min_log_ratio)
    # 対数スケール: 最小フィルタリング (Nyquist/1000) から最大フィルタリング (Nyquist)
    min_log_ratio = np.log10(nyquist / 1000)
    max_log_ratio = np.log10(nyquist)

    # 対数的に補間し、カットオフ周波数を決定
    log_cutoff = min_log_ratio + normalized_value * (min_log_ratio - max_log_ratio)
    # 対数スケール
    min_log_ratio = np.log10(min_cutoff)
    max_log_ratio = np.log10(nyquist / 10)

    # 対数的に補間し、カットオフ周波数を決定
    log_cutoff = max_log_ratio - normalized_value * (max_log_ratio - min_log_ratio)
    cutoff_freq = 10 ** log_cutoff
    
    # カットオフ周波数がナイキスト周波数以下であることを保証
    cutoff_freq = min(cutoff_freq, nyquist)

    
    # 3. アナログフィルタ設計 (s-domain) とデジタル変換
    order = 4 # バターワースフィルタの次数

    
    # 3. アナログフィルタ設計 (s-domain) とデジタル変換
    order = 4 # バターワースフィルタの次数
    
    Wn_analog = 2 * np.pi * cutoff_freq 
    b_analog, a_analog = butter(order, Wn_analog, btype='low', analog=True)
    
    b_digital, a_digital = bilinear(b_analog, a_analog, fs=sampling_rate)
    
    # 4. ゼロ位相フィルタリングの適用
    filtered_data = filtfilt(b_digital, a_digital, data)
    
    return filtered_data