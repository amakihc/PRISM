# アプリケーションのメインモジュール

import matplotlib
matplotlib.use('QtAgg')

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui_layout import UILayout
from data_processor import load_csv_data, compute_psd, compute_autocorrelation
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class AdvancedWindow(QDialog):
    def __init__(self, parent=None, signal_data=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Analysis")
        self.setWindowModality(Qt.ApplicationModal)
        self.signal_data = signal_data

        main_layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(8, 6), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        self.plot_correlogram()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button)

    def plot_correlogram(self):
        """コレログラムを計算してプロットする"""
        if self.signal_data is None or len(self.signal_data) == 0:
            return
        
        ax = self.figure.add_subplot(111)

        max_lags = min(10000, len(self.signal_data))

        lags, autocorr = compute_autocorrelation(self.signal_data[:max_lags])

        ax.clear()
        ax.plot(lags, autocorr, color='red')

        ax.set_title("Correlogram", fontsize=14)
        ax.set_xlabel("Lag", fontsize=12)
        ax.set_ylabel("Autocorrelation", fontsize=12)
        ax.grid(True, alpha=0.5)
        self.figure.tight_layout()
        self.canvas.draw()

class App(QMainWindow):
    """アプリケーションのメインウィンドウクラス"""
    def __init__(self):
        super().__init__()
        self.ui = UILayout()
        self.setCentralWidget(self.ui)
        self.setGeometry(100, 100, 1200, 600)
        self.setWindowTitle("PRISM - Data Visualizer")

        self.df = None
        self.sampling_rate = 0

        self.current_smoothing_level = 1

        self.ui.browse_button.clicked.connect(self.browse_file)
        self.ui.channel_combo_box.currentIndexChanged.connect(self.plot_selected_channel)

        self.ui.avg_slider.valueChanged.connect(self.update_smoothing_level)

        self.ui.advanced_button.clicked.connect(self.show_advanced_window)

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
        channel_names = [f"Column {i}" for i in range(1, num_columns)]
        self.ui.channel_combo_box.addItems(channel_names)
        self.plot_selected_channel()
    
    def plot_selected_channel(self):
        """ドロップダウンリストで選択されたチャンネルのデータをプロットする"""
        selected_index = self.ui.channel_combo_box.currentIndex()
        if selected_index < 0 or self.df is None:
            return
        data_column_index = selected_index + 1
        signal_data = self.df.iloc[:, data_column_index].values
        time_data = self.df.iloc[:, 0].values
        self.plot_time_series(time_data, signal_data)
        self.plot_psd(signal_data)
        
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

    def show_advanced_window(self):
        """高度な分析ウィンドウを表示する"""
        selected_index = self.ui.channel_combo_box.currentIndex()
        if selected_index < 0 or self.df is None:
            return
        data_column_index = selected_index + 1
        signal_data = self.df.iloc[:, data_column_index].values

        advanced_window = AdvancedWindow(self, signal_data=signal_data)
        advanced_window.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())