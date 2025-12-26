import sys
import os
from pathlib import Path
import json 

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QFileDialog,
    QVBoxLayout,
    QLabel,
    QGraphicsOpacityEffect,
    QSlider
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QFont


config_file = Path("config.json")

def load_config():
    if config_file.exists():
        return json.loads(config_file.read_text())
    return {}

def save_config(cfg):
    config_file.write_text(json.dumps(cfg, indent=2))

class FadeLetterOverlay(QLabel):
    def __init__(self, parent, duration=3000, margin=10):
        """
        parent: the widget to overlay on (e.g., QVideoWidget)
        duration: fade duration in milliseconds
        margin: distance from bottom-right corner
        """
        super().__init__(parent)
        self.duration = duration
        self.margin = margin

        # Default style
        self.setFont(QFont("Arial", 100, QFont.Weight.Bold))
        self.setStyleSheet("color: gray;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Opacity effect
        # self.opacity_effect = QGraphicsOpacityEffect()
        # self.setGraphicsEffect(self.opacity_effect)
        # self.opacity_effect.setOpacity(0.0)
        self.hide()

        # Timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.leave)

    def activateText(self, text):
        """
        Show the letter overlay and start fade-out timer
        """
        print(f"this text {text}")
        super().setText(text)
        self.adjustSize()
        # Place bottom-right
        # self.move(
        #     self.parent().width() - self.width() - self.margin,
        #     self.parent().height() - self.height() - self.margin
        # )
        print(
            self.parent().width() - self.width() - self.margin,
            self.parent().height() - self.height() - self.margin
        )
        
        self.move(
           -1000,-1000
        )
        self.raise_()
        self.elapsed = 0
        self.show()

        print("self.isVisible()",self.isVisible())

        if self.hide_timer.isActive():
            self.hide_timer.stop()
        self.hide_timer.start(self.duration)

    def resizeEvent(self, event):
        """
        Keep overlay at bottom-right if parent resizes
        """
        print("resize")
        super().resizeEvent(event)
        if self.isVisible():
            self.move(
                self.parent().width() - self.width() - self.margin,
                self.parent().height() - self.height() - self.margin
            )


    def leave(self):
        print("leave")
        self.hide()

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Player")
        self.resize(800, 500)

        self.video = QVideoWidget()
        # print("self.video.video_widget.geometry()", self.video.video_widget.geometry())

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)

        self.player.setVideoOutput(self.video)
        self.player.setAudioOutput(self.audio)

        layout = QVBoxLayout()
        layout.addWidget(self.video)
        self.setLayout(layout)

        filekey = "__FILE_PATH_VIDEO_CACHE__"

        self.storage = load_config()
        filecache = self.storage.get(filekey)
        if filecache is None:
            filecache = ""


        print("file chacke ", filecache)

        file, _ = QFileDialog.getOpenFileName(
            self, "Select Video",
            filecache,
            filter="Video Files (*.mp4 *.avi *.mkv *.mov)",
        )

        print("file", file)
        self.storage[filekey] = file
        save_config(self.storage)
        

        if not file:
            sys.exit()

        self.player.setSource(QUrl.fromLocalFile(file))
        self.player.play()

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)

        self.slider.sliderPressed.connect(lambda: self.player.pause())
        self.slider.sliderReleased.connect(lambda: self.player.play())
        self.slider.sliderMoved.connect(self.player.setPosition)


        layout.addWidget(self.slider)


        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)

        tpkeysKey = "__TP_KEYS__"

        alltpkeys = self.storage.get(tpkeysKey)
        if alltpkeys is None:
            alltpkeys = {file:{}}
            self.storage[tpkeysKey] = alltpkeys

        self.tpkeys = alltpkeys.get(file)
        if self.tpkeys is None:
            self.tpkeys = {}
            alltpkeys[file] = self.tpkeys


        self.playbackSpeed = 1

        self.playbackSpeedLabel = FadeLetterOverlay(self)
       

    def on_position_changed(self, position):
        # position is in milliseconds
        self.slider.setValue(position)

    def on_duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def on_slider_moved(self, position):
        self.player.setPosition(position)
        self.slider.sliderMoved.connect(self.on_slider_moved)

    def keyPressEvent(self, event):
        ctrl_pressed = event.modifiers() & Qt.KeyboardModifier.ControlModifier

        if event.key() == Qt.Key.Key_Space:
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.pause()
            else:
                self.player.play()

        elif event.key() == Qt.Key.Key_A:
            pos = self.player.position()
            self.player.setPosition(max(0, pos - 2000))
        elif event.key() == Qt.Key.Key_D:
            pos = self.player.position()
            self.player.setPosition(max(0, pos + 2000))
        elif event.key() == Qt.Key.Key_Escape:
            self.player.stop()
            QApplication.quit()
        elif Qt.Key.Key_1 <= event.key() <= Qt.Key.Key_9:
            number_pressed = event.key() - Qt.Key.Key_0

            if ctrl_pressed:
                self.tpkeys[number_pressed] = str(self.player.position())
                save_config(self.storage)
            else:
                position = self.tpkeys.get(str(number_pressed))
                if position is None: return

                self.player.setPosition(position)
                self.player.play()

            # Do whatever you want with number_pressed
        elif event.key() == Qt.Key.Key_Comma:
            self.playbackSpeed -= 0.1
            self.player.setPlaybackRate(self.playbackSpeed)
            self.playbackSpeedLabel.activateText(f"{self.playbackSpeed:.1f}x")
            self.playbackSpeedLabel.raise_()
        elif event.key() == Qt.Key.Key_Period:
            self.playbackSpeed += 0.1
            self.player.setPlaybackRate(self.playbackSpeed)
            self.playbackSpeedLabel.activateText(f"{self.playbackSpeed:.1f}x")
            self.playbackSpeedLabel.raise_()

        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VideoPlayer()
    w.show()
    sys.exit(app.exec())
