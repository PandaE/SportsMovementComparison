"""
test_enhanced_video_player.py
测试增强的视频播放器功能
"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
from ui.video_player import VideoPlayer


class VideoPlayerTestWindow(QMainWindow):
    """视频播放器测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("增强视频播放器测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("增强视频播放器测试")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 选择文件按钮
        self.select_file_btn = QPushButton("选择视频文件")
        self.select_file_btn.clicked.connect(self.select_video_file)
        layout.addWidget(self.select_file_btn)
        
        # 视频播放器
        self.video_player = VideoPlayer()
        self.video_player.frame_changed.connect(self.on_frame_changed)
        layout.addWidget(self.video_player)
        
        # 状态信息
        self.status_label = QLabel("请选择视频文件")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("background-color: #f0f8ff; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.status_label)
        
        central_widget.setLayout(layout)
    
    def select_video_file(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择视频文件", 
            "", 
            "视频文件 (*.mp4 *.avi *.mov *.wmv *.flv *.mkv);;所有文件 (*)"
        )
        
        if file_path:
            self.video_player.set_video(file_path)
            self.status_label.setText(f"已加载视频: {os.path.basename(file_path)}")
    
    def on_frame_changed(self, frame_number):
        """帧变化回调"""
        total_frames = self.video_player.get_total_frames()
        self.status_label.setText(
            f"当前帧: {frame_number + 1}/{total_frames} | "
            f"时间: {frame_number / self.video_player.fps:.2f}s"
        )


def main():
    app = QApplication(sys.argv)
    
    # 测试窗口
    test_window = VideoPlayerTestWindow()
    test_window.show()
    
    print("🎬 增强视频播放器测试")
    print("功能特点:")
    print("1. ✅ 帧级别预览 - 直接在界面显示当前帧")
    print("2. ✅ 帧数显示 - 当前帧/总帧数 + 时间信息")
    print("3. ✅ 可拖拽进度条 - 精确到帧的导航")
    print("4. ✅ 逐帧控制 - 上一帧/下一帧按钮")
    print("5. ✅ 多速度播放 - 0.25X, 0.5X, 1X, 1.5X, 2X")
    print("6. ✅ 播放控制 - 播放/暂停功能")
    print()
    print("📝 使用说明:")
    print("- 点击'选择视频文件'导入视频")
    print("- 拖拽进度条可以跳转到任意帧")
    print("- 使用上一帧/下一帧按钮进行精确控制")
    print("- 点击播放按钮开始/暂停播放")
    print("- 点击速度按钮切换播放速度")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()