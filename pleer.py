from PyQt5.QtCore import (pyqtSignal, QAbstractItemModel,
                          QFileInfo, QModelIndex, Qt, QTime, QUrl, QSettings)
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import (QMediaContent, QMediaMetaData, QMediaPlayer, QMediaPlaylist)
from PyQt5.QtWidgets import (QApplication, QFileDialog,
                             QHBoxLayout, QLabel, QListView, QMessageBox, QPushButton,
                             QSlider, QStyle, QToolButton, QVBoxLayout, QWidget, QStatusBar)
import os


class PlaylistModel(QAbstractItemModel):
    Title, ColumnCount = range(2)

    def __init__(self, parent=None):
        super(PlaylistModel, self).__init__(parent)

        self.m_playlist = None
        print("Welcome!")

    def rowCount(self, parent=QModelIndex()):
        return self.m_playlist.mediaCount() if self.m_playlist is not None and not parent.isValid() else 0

    def columnCount(self, parent=QModelIndex()):
        return self.ColumnCount if not parent.isValid() else 0

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row,
                                column) if self.m_playlist is not None and not parent.isValid() and row >= 0 and row < self.m_playlist.mediaCount() and column >= 0 and column < self.ColumnCount else QModelIndex()

    def parent(self, child):
        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            if index.column() == self.Title:
                location = self.m_playlist.media(index.row()).canonicalUrl()
                return QFileInfo(location.path()).fileName()

            return self.m_data[index]

        return None

    def playlist(self):
        return self.m_playlist

    def setPlaylist(self, playlist):
        if self.m_playlist is not None:
            self.m_playlist.mediaAboutToBeInserted.disconnect(
                self.beginInsertItems)
            self.m_playlist.mediaInserted.disconnect(self.endInsertItems)
            self.m_playlist.mediaAboutToBeRemoved.disconnect(
                self.beginRemoveItems)
            self.m_playlist.mediaRemoved.disconnect(self.endRemoveItems)
            self.m_playlist.mediaChanged.disconnect(self.changeItems)

        self.beginResetModel()
        self.m_playlist = playlist

        if self.m_playlist is not None:
            self.m_playlist.mediaAboutToBeInserted.connect(
                self.beginInsertItems)
            self.m_playlist.mediaInserted.connect(self.endInsertItems)
            self.m_playlist.mediaAboutToBeRemoved.connect(
                self.beginRemoveItems)
            self.m_playlist.mediaRemoved.connect(self.endRemoveItems)
            self.m_playlist.mediaChanged.connect(self.changeItems)

        self.endResetModel()

    def beginInsertItems(self, start, end):
        self.beginInsertRows(QModelIndex(), start, end)

    def endInsertItems(self):
        self.endInsertRows()

    def beginRemoveItems(self, start, end):
        self.beginRemoveRows(QModelIndex(), start, end)

    def endRemoveItems(self):
        self.endRemoveRows()

    def changeItems(self, start, end):
        self.dataChanged.emit(self.index(start, 0),
                              self.index(end, self.ColumnCount))


class PlayerControls(QWidget):
    play = pyqtSignal()
    pause = pyqtSignal()
    stop = pyqtSignal()
    next = pyqtSignal()
    previous = pyqtSignal()
    changeVolume = pyqtSignal(int)
    changeMuting = pyqtSignal(bool)
    changeRate = pyqtSignal(float)

    def __init__(self, parent=None):
        super(PlayerControls, self).__init__(parent)

        self.playerState = QMediaPlayer.StoppedState
        self.playerMuted = False

        self.playButton = QToolButton(clicked=self.playClicked, toolTip="Play")
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.stopButton = QToolButton(clicked=self.stop, toolTip="Stop")
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopButton.setEnabled(False)

        self.nextButton = QToolButton(clicked=self.next, toolTip="Next")
        self.nextButton.setIcon(
            self.style().standardIcon(QStyle.SP_MediaSkipForward))

        self.previousButton = QToolButton(clicked=self.previous, toolTip="Previous")
        self.previousButton.setIcon(
            self.style().standardIcon(QStyle.SP_MediaSkipBackward))

        self.muteButton = QToolButton(clicked=self.muteClicked, toolTip="Mute")
        self.muteButton.setIcon(
            self.style().standardIcon(QStyle.SP_MediaVolume))

        self.volumeSlider = QSlider(Qt.Horizontal, sliderMoved=self.changeVolume)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setValue(50)
        self.volumeSlider.setStyleSheet(stylesheet(self))

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stopButton)
        layout.addWidget(self.previousButton)
        layout.addWidget(self.playButton)
        layout.addWidget(self.nextButton)
        layout.addWidget(self.muteButton)
        layout.addWidget(self.volumeSlider)
        self.setLayout(layout)

    def state(self):
        return self.playerState

    def setState(self, state):
        if state != self.playerState:
            self.playerState = state

            if state == QMediaPlayer.StoppedState:
                self.stopButton.setEnabled(False)
                self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))
            elif state == QMediaPlayer.PlayingState:
                self.stopButton.setEnabled(True)
                self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
            elif state == QMediaPlayer.PausedState:
                self.stopButton.setEnabled(True)
                self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def volume(self):
        return self.volumeSlider.value()

    def setVolume(self, volume):
        self.volumeSlider.setValue(volume)

    def isMuted(self):
        return self.playerMuted

    def setMuted(self, muted):
        if muted != self.playerMuted:
            self.playerMuted = muted

            self.muteButton.setIcon(
                self.style().standardIcon(
                    QStyle.SP_MediaVolumeMuted if muted else QStyle.SP_MediaVolume))

    def playClicked(self):
        if self.playerState in (QMediaPlayer.StoppedState, QMediaPlayer.PausedState):
            self.play.emit()
        elif self.playerState == QMediaPlayer.PlayingState:
            self.pause.emit()

    def muteClicked(self):
        self.changeMuting.emit(not self.playerMuted)


class Player(QWidget):
    fullScreenChanged = pyqtSignal(bool)

    def __init__(self, playlist, parent=None):
        super(Player, self).__init__(parent)
        self.setStyleSheet(stylesheet(self))
        self.colorDialog = None
        self.trackInfo = ""
        self.statusInfo = ""
        self.duration = 0

        self.url = ""
        self.settings = QSettings("QAudioPlayer", "QAudioPlayer")

        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)

        self.player.durationChanged.connect(self.durationChanged)
        self.player.positionChanged.connect(self.positionChanged)
        self.player.metaDataChanged.connect(self.metaDataChanged)
        self.playlist.currentIndexChanged.connect(self.playlistPositionChanged)
        self.player.mediaStatusChanged.connect(self.statusChanged)
        self.player.bufferStatusChanged.connect(self.bufferingProgress)
        self.player.error.connect(self.displayErrorMessage)

        self.playlistModel = PlaylistModel()
        self.playlistModel.setPlaylist(self.playlist)

        self.playlistView = QListView()
        #        self.playlistView.setSpacing(1)
        self.playlistView.setStyleSheet(stylesheet(self))
        self.playlistView.setModel(self.playlistModel)
        self.playlistView.setCurrentIndex(
            self.playlistModel.index(self.playlist.currentIndex(), 0))

        self.playlistView.activated.connect(self.jump)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, round(self.player.duration() / 1000))
        self.slider.setStyleSheet(stylesheet(self))

        self.labelDuration = QLabel()
        self.slider.sliderMoved.connect(self.seek)

        openButton = QPushButton("", clicked=self.open, toolTip="open Files / Playlist\n(clears playlist)")
        openButton.setFixedWidth(36)
        openButton.setIcon(openButton.style().standardIcon(QStyle.SP_DialogOpenButton))

        openAddButton = QPushButton("", clicked=self.openAdd, toolTip="add Files / Playlist\n(add to playlist)")
        openAddButton.setFixedWidth(36)
        openAddButton.setIcon(QIcon.fromTheme("add"))

        clearButton = QPushButton("", clicked=self.clearList)
        clearButton.setFixedWidth(36)
        clearButton.setIcon(QIcon.fromTheme("edit-delete"))
        clearButton.setToolTip("clear List")

        controls = PlayerControls()
        controls.setState(self.player.state())
        controls.setVolume(self.player.volume())
        controls.setMuted(controls.isMuted())

        controls.play.connect(self.player.play)
        controls.pause.connect(self.player.pause)
        controls.stop.connect(self.player.stop)
        controls.next.connect(self.playlist.next)
        controls.previous.connect(self.previousClicked)
        controls.changeVolume.connect(self.player.setVolume)
        controls.changeMuting.connect(self.player.setMuted)
        controls.changeRate.connect(self.player.setPlaybackRate)

        self.player.stateChanged.connect(controls.setState)
        self.player.volumeChanged.connect(controls.setVolume)
        self.player.mutedChanged.connect(controls.setMuted)

        displayLayout = QHBoxLayout()
        displayLayout.addWidget(self.playlistView)

        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(openButton)
        controlLayout.addWidget(openAddButton)
        controlLayout.addWidget(clearButton)
        #        controlLayout.addStretch(1)
        controlLayout.addWidget(controls)
        #        controlLayout.addStretch(1)

        layout = QVBoxLayout()
        layout.addLayout(displayLayout)
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.slider)
        hLayout.addWidget(self.labelDuration)
        layout.addLayout(hLayout)
        layout.addLayout(controlLayout)

        self.statusBar = QStatusBar()
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.statusBar)
        layout.addLayout(vlayout)
        self.statusBar.showMessage("Welcome")
        self.setWindowTitle("Audio Player")
        self.setMinimumSize(300, 200)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        if not self.player.isAvailable():
            QMessageBox.warning(self, "Service not available",
                                "The QMediaPlayer object does not have a valid service.\n"
                                "Please check the media service plugins are installed.")

            controls.setEnabled(False)
            self.playlistView.setEnabled(False)
            openButton.setEnabled(False)
            self.colorButton.setEnabled(False)
            self.fullScreenButton.setEnabled(False)

        self.metaDataChanged()

    def closeEvent(self, event):
        print("goodbye ...")
        event.accept()

    def open(self):
        fileNames, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "Audio Files *.mp3 *.m4a *.ogg *.wav *.m3u")
        if fileNames:
            self.url = fileNames
            self.setPlaylist(fileNames)
            print("added Files to playlist")

    def openAdd(self):
        fileNames, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "Audio Files *.mp3 *.m4a *.ogg *.wav *.m3u")
        if fileNames:
            self.url = fileNames
            self.addToPlaylist(fileNames)
            print("added Files to playlist")

    def openOnStart(self, f):
        self.url = f
        self.addToPlaylist(self.url)
        print("added Files to playlist")

    def clearList(self):
        self.playlist.clear()

    def setPlaylist(self, fileNames):
        self.clearList()
        for name in fileNames:
            fileInfo = QFileInfo(name)
            if fileInfo.exists():
                url = QUrl.fromLocalFile(fileInfo.absoluteFilePath())
                if fileInfo.suffix().lower() == 'm3u':
                    self.playlist.load(url)
                else:
                    self.playlist.addMedia(QMediaContent(url))
            else:
                url = QUrl(name)
                if url.isValid():
                    self.playlist.addMedia(QMediaContent(url))

    def addToPlaylist(self, fileNames):
        for name in fileNames:
            fileInfo = QFileInfo(name)
            if fileInfo.exists():
                url = QUrl.fromLocalFile(fileInfo.absoluteFilePath())
                if fileInfo.suffix().lower() == 'm3u':
                    self.playlist.load(url)
                else:
                    self.playlist.addMedia(QMediaContent(url))
            else:
                url = QUrl(name)
                if url.isValid():
                    self.playlist.addMedia(QMediaContent(url))

    def durationChanged(self, duration):
        duration = round(duration / 1000)

        self.duration = duration
        self.slider.setMaximum(duration)

    def positionChanged(self, progress):
        progress = round(progress / 1000)

        if not self.slider.isSliderDown():
            self.slider.setValue(progress)

        self.updateDurationInfo(progress)

    def metaDataChanged(self):
        if self.player.isMetaDataAvailable():
            # print(self.player.availableMetaData())
            self.setTrackInfo("%s - %s" % (
                self.player.metaData(QMediaMetaData.ContributingArtist),
                self.player.metaData(QMediaMetaData.Title)))

    def previousClicked(self):
        if self.player.position() <= 5000:
            self.playlist.previous()
        else:
            self.player.setPosition(0)

    def jump(self, index):
        if index.isValid():
            self.playlist.setCurrentIndex(index.row())
            self.player.play()

    def playlistPositionChanged(self, position):
        self.playlistView.setCurrentIndex(
            self.playlistModel.index(position, 0))

    def seek(self, seconds):
        self.player.setPosition(seconds * 1000)

    def statusChanged(self, status):
        self.handleCursor(status)

        if status == QMediaPlayer.LoadingMedia:
            self.setStatusInfo("Loading...")
        elif status == QMediaPlayer.StalledMedia:
            self.setStatusInfo("Media Stalled")
        elif status == QMediaPlayer.EndOfMedia:
            QApplication.alert(self)
        elif status == QMediaPlayer.InvalidMedia:
            self.displayErrorMessage()
        else:
            self.setStatusInfo("")

    def handleCursor(self, status):
        if status in (QMediaPlayer.LoadingMedia, QMediaPlayer.BufferingMedia, QMediaPlayer.StalledMedia):
            self.setCursor(Qt.BusyCursor)
        else:
            self.unsetCursor()

    def bufferingProgress(self, progress):
        self.setStatusInfo(f"Buffering {progress}")

    def setTrackInfo(self, info):
        self.trackInfo = info

        if self.statusInfo != "":
            self.statusBar.showMessage(f"{self.trackInfo} | {self.statusInfo}")
        else:
            self.statusBar.showMessage(self.trackInfo)

    def setStatusInfo(self, info):
        self.statusInfo = info

        if self.statusInfo != "":
            self.statusBar.showMessage(f"{self.trackInfo} | {self.statusInfo}")
        else:
            self.statusBar.showMessage(self.trackInfo)

    def displayErrorMessage(self):
        self.setStatusInfo(self.player.errorString())

    def updateDurationInfo(self, currentInfo):
        duration = self.duration
        if currentInfo or duration:
            currentTime = QTime(round((currentInfo / 3600) % 60), round((currentInfo / 60) % 60),
                                round(currentInfo % 60), round((currentInfo * 1000) % 1000))
            totalTime = QTime((round(duration / 3600) % 60), round((duration / 60) % 60),
                              round(duration % 60), round(duration * 1000) % 1000)

            format = 'hh:mm:ss' if duration > 3600 else 'mm:ss'
            tStr = currentTime.toString(format) + " / " + totalTime.toString(format)
        else:
            tStr = ""

        self.labelDuration.setText(tStr)


def stylesheet(self):
    return

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    if len(sys.argv) > 1:
        url = QUrl.fromLocalFile(os.path.realpath(sys.argv[1]))
        player = Player(None)
        print(url)
        player.playlist.load(url)
    else:
        player = Player(None)
    player.setGeometry(100, 100, 500, 350)
    player.show()
    sys.exit(app.exec_())