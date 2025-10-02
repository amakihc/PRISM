# gui_layout.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QComboBox, QSizePolicy
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class UILayout(QWidget):
    """PRISMアプリケーションのUIレイアウトを構築するクラス"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PRISM - GUI Prototype")
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.create_widgets()
        self.add_widgets_to_layout()

    def create_widgets(self):
        """UIコンポーネントの作成と初期設定"""
        # アプリケーション名ラベル
        self.app_title_label = QLabel("PRISM")
        self.app_title_label.setFixedWidth(150) 
        title_font = QFont("Helvetica", 24, QFont.Bold)
        self.app_title_label.setFont(title_font)
        self.app_title_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # ファイル選択ボタンとラベル
        self.browse_button = QPushButton("Select CSV File")
        self.browse_button.setFixedWidth(150)
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # チャンネル選択ラベルとコンボボックス
        self.channel_label = QLabel("Select Channel:")
        self.channel_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.channel_combo_box = QComboBox()
        self.channel_combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # グラフウィジェットの作成 (Matplotlib FigureCanvas)
        self.font_size = 20
        
        # 時系列プロットのFigureとAxes
        self.time_series_figure = Figure(figsize=(5, 4), facecolor='white')
        self.time_series_canvas = FigureCanvas(self.time_series_figure)
        self.time_series_axes = self.time_series_figure.add_subplot(111)
        self.setup_axes(self.time_series_axes, "Time Series Plot", "Time [s]", "Amplitude", log_mode=False)
        
        # PSDプロットのFigureとAxes
        self.psd_figure = Figure(figsize=(5, 4), facecolor='white')
        self.psd_canvas = FigureCanvas(self.psd_figure)
        self.psd_axes = self.psd_figure.add_subplot(111)
        self.setup_axes(self.psd_axes, "Amplitude Spectral Density", "Frequency [Hz]", "ASD", log_mode=True)
        
        # Figureの余白調整
        self.time_series_figure.tight_layout()
        self.psd_figure.tight_layout()

    def setup_axes(self, ax, title, xlabel, ylabel, log_mode):
        """MatplotlibのAxesオブジェクトの共通設定"""
        ax.set_title(title, fontsize=self.font_size)
        ax.set_xlabel(xlabel, fontsize=self.font_size)
        ax.set_ylabel(ylabel, fontsize=self.font_size)
        
        ax.tick_params(axis='both', which='major', labelsize=self.font_size)
        ax.grid(True, linestyle='-', alpha=0.3, color='gray') 
        ax.tick_params(colors='black')

        if log_mode:
            ax.set_xscale('log')
            ax.set_yscale('log')
            
    def add_widgets_to_layout(self):
        """ウィジェットをメインレイアウトに配置"""
        # ファイル選択エリアのレイアウト
        file_selection_layout = QHBoxLayout()
        file_selection_layout.addWidget(self.browse_button, 0)
        file_selection_layout.addWidget(self.file_path_label, 1)
        
        file_selection_widget = QWidget()
        file_selection_widget.setLayout(file_selection_layout)
        file_selection_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) 

        # チャンネル選択エリアのレイアウト
        channel_selection_layout = QHBoxLayout()
        channel_selection_layout.addWidget(self.channel_label, 0)
        channel_selection_layout.addWidget(self.channel_combo_box, 1)
        
        channel_selection_widget = QWidget()
        channel_selection_widget.setLayout(channel_selection_layout)
        channel_selection_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) 

        # 最上部のコントロールバーレイアウト
        top_layout = QHBoxLayout()
        
        # PRISMロゴ (固定幅)
        top_layout.addWidget(self.app_title_label, 0) 
        
        # ファイル選択とチャンネル選択 (残りのスペースを1:1で分割)
        top_layout.addWidget(file_selection_widget, 1) 
        top_layout.addWidget(channel_selection_widget, 1) 
        
        # グラフエリアのレイアウト
        graph_layout = QHBoxLayout()
        graph_layout.addWidget(self.time_series_canvas)
        graph_layout.addWidget(self.psd_canvas)

        # メインレイアウトに垂直に配置
        self.main_layout.addLayout(top_layout)
        self.main_layout.addLayout(graph_layout)