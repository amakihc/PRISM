# アプリケーションのメインモジュール

import matplotlib
matplotlib.use('QtAgg')

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtGui import QIcon

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui_layout import UILayout
from data_processor import load_csv_data, compute_psd, apply_lpf

__version__ = "1.0.0"

def resource_path(relative_path):
    """"PyInstallerでバンドルされたリソースへの絶対パスを解決するヘルパー関数"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)

class App(QMainWindow):
    """アプリケーションのメインウィンドウクラス"""
    def __init__(self):
        super().__init__()
        self.ui = UILayout(self.app_resource_path)
        self.setCentralWidget(self.ui)
        self.setGeometry(100, 100, 1200, 600)
        self.setWindowTitle("PRISM")

        icon_path = resource_path('src/icons/PRISM_App_Icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print("Icon file not found. Continuing without custom icon.")

        self.df = None
        self.sampling_rate = 0

        self.current_smoothing_level = 1
        self.current_lpf_level = 1

        self.ui.browse_button.clicked.connect(self.browse_file)
        self.ui.channel_combo_box.currentIndexChanged.connect(self.plot_selected_channel)

        self.ui.lpf_slider.valueChanged.connect(self.update_lpf_cutoff)
        self.ui.avg_slider.valueChanged.connect(self.update_smoothing_level)

    def app_resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(__file__), relative_path)

    def update_smoothing_level(self, value):
        """スライドバーの値が変更されたときに呼び出される"""
        self.current_smoothing_level = value

        if self.df is not None:
            self.plot_selected_channel()
        
    def browse_file(self):
        """ファイルダイアログを開き、CSVファイルを選択する"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "CSVファイルを選択", "", "CSV Files (*.csv)"
        )
        if file_path:
            self.ui.file_path_label.setText(file_path)
            self.process_file(file_path)

    def process_file(self, file_path):
        """ファイルを処理し、ドロップダウンリストを更新する"""
        self.df, self.sampling_rate = load_csv_data(file_path)
        if self.df is None or self.df.empty:
            return
        self.ui.channel_combo_box.clear()
        num_columns = len(self.df.columns)
        channel_names = [f"{i}" for i in range(1, num_columns)]
        self.ui.channel_combo_box.addItems(channel_names)
        self.plot_selected_channel()
    
    def plot_selected_channel(self):
        """ドロップダウンリストで選択されたチャンネルのデータをフィルタリングし、プロットする"""
        selected_index = self.ui.channel_combo_box.currentIndex()
        if selected_index < 0 or self.df is None:
            return
            
        data_column_index = selected_index + 1
        
        # 生データと時間データを取得
        raw_signal_data = self.df.iloc[:, data_column_index].values
        time_data = self.df.iloc[:, 0].values

        # LPFフィルタリングの適用
        lpf_level = self.current_lpf_level
        
        if lpf_level != 1: # スライダーがOFF(1)でなければフィルタ適用
            # apply_lpf は内部でアナログフィルタ設計とバイリニア変換を実行
            signal_data = apply_lpf(raw_signal_data, self.sampling_rate, lpf_level)
        else:
            # フィルタOFFの場合は生データをそのまま使用
            signal_data = raw_signal_data
        
        # フィルタリング後のデータでプロットを更新
        self.plot_time_series(time_data, signal_data)
        self.plot_psd(signal_data) # フィルタリングされたデータでPSDも計算
        
    def plot_time_series(self, time_data, signal_data):
        """時系列データをMatplotlibでプロットする"""
        ax = self.ui.time_series_axes
        canvas = self.ui.time_series_canvas
        figure = self.ui.time_series_figure
        ax.clear() 
        ax.plot(time_data, signal_data, color='blue')
        self.ui.setup_axes(ax, "Time Series Plot", "Time [s]", "Amplitude", log_mode=False)
        figure.tight_layout()
        canvas.draw()
        
    def plot_psd(self, data):
        """PSDをMatplotlibでプロットする"""
        ax = self.ui.psd_axes
        canvas = self.ui.psd_canvas
        figure = self.ui.psd_figure

        frequencies, psd = compute_psd(data, self.sampling_rate, self.current_smoothing_level)

        ax.clear()
        if len(frequencies) > 0 and len(psd) > 0:
            ax.plot(frequencies, psd, color='blue')
        self.ui.setup_axes(ax, "Amplitude Spectral Density", "Frequency [Hz]", "ASD", log_mode=True)
        figure.tight_layout()
        canvas.draw()
        
    def update_lpf_cutoff(self, value):
        """"LPFスライダーの値が変更されたときにプロットを再描画"""
        self.current_lpf_level = value
        if self.df is not None:
            self.plot_selected_channel()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    style_file_path = resource_path('src/style.qss')
    try:
        if os.path.exists(style_file_path):
            with open(style_file_path, "r", encoding="utf-8") as f:
                qss_content = f.read()

                url_path = resource_path('src/icons/arrow_down_black.svg').replace('\\', '/')

                qss_content = qss_content.replace('url(CUSTOM_ARROW_PATH);', f'url({url_path});')
                app.setStyleSheet(qss_content)
    except Exception as e:
        print(f"Error applying QSS: {e}")

    window = App()
    window.show()
    sys.exit(app.exec_())