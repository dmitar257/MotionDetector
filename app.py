from controller import Controller
from views.mainView import MainView
from settingsManager import SettingsManager
from workerThreadController import WorkerThreadController
from PyQt5 import QtWidgets
from logs import setup_logging


def main():
    setup_logging()
    app = QtWidgets.QApplication([])
    settingsManager = SettingsManager()
    view = MainView(settingsManager)
    threadController = WorkerThreadController()
    cnt = Controller(threadController, settingsManager)
    cnt.imageIsReadyForDisplay.connect(view.onImageReceived)
    cnt.previewImagesReadyForDisplay.connect(view.onPreviewImagesReceived)
    cnt.infoAboutFrameFetcherAcquired.connect(view.onListOfCamerasReceived)
    cnt.frameSourceNotFound.connect(view.onNoFrameInputFound)
    cnt.soundDetectionErrorAppeared.connect(view.onSoundDetectionError)
    view.closingWindow.connect(cnt.onCloseSignalReceived)
    view.toogleShowPreviewFrames.connect(cnt.onPreviewFramesToggled)
    view.startFetchingCameraInfo.connect(cnt.onCameraInfoFetcherStart)
    view.toggleMovementDisplayType.connect(cnt.onToggledMovementDisplayType)
    view.show()
    app.exit(app.exec_())

if __name__ == "__main__":
    main()