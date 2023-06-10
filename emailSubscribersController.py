from dataclasses import dataclass
from datetime import datetime, timedelta
import imageio.v3 as iio
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QThread
from typing import Dict, Optional, List, Tuple
import yagmail
import io
from utils import Frame
import cv2
import logging

logger = logging.getLogger(__name__)

GIF_DURATION = 2500

@dataclass
class EmailSubsriber:
    username: str
    email: str
    backoffIntervalHour: int
    backoffIntervalMinute: int
    last_warning_sent_date: datetime = datetime.fromisoformat('1970-01-01T00:00:00')

class EmailSubscribersController(QObject):
    toggleCreatingMovementGIF = pyqtSignal(bool)
    def __init__(
        self
        ) -> None:
        super().__init__()
        self.allSubscribers: Dict[str, EmailSubsriber] = dict()
        self.listOfUnprocessedSubscribers: List[EmailSubsriber] = []
        self.movementDetectedTimestamp = None
        self.yag = None
        self.enableNotifications = False

    @pyqtSlot()
    def onStart(self) -> None:
        self.yag = yagmail.SMTP('detectiontest993@gmail.com', 'utashauoaipfjkpf')
    
    @pyqtSlot(bool)
    def onContinuousMovementToggled(self, movementPresent:bool) -> None:
        if not self.enableNotifications:
            return
        if movementPresent:
            curentTime = datetime.now()
            if self.subscribersForProcessing(curentTime):
                self.movementDetectedTimestamp = curentTime
                self.toggleCreatingMovementGIF.emit(True)
        else:
            self.toggleCreatingMovementGIF.emit(False)

    def subscribersForProcessing(self, curentTime: datetime) -> bool:
        for email in self.allSubscribers:
            td = timedelta(hours=self.allSubscribers[email].backoffIntervalHour, minutes=self.allSubscribers[email].backoffIntervalMinute)
            if self.allSubscribers[email].last_warning_sent_date + td <= curentTime:
                self.listOfUnprocessedSubscribers.append(self.allSubscribers[email])
        return len(self.listOfUnprocessedSubscribers) > 0
            
    @pyqtSlot(bytes)
    def onGifCreated(self, gifContent: bytes) -> None:
        if not self.movementDetectedTimestamp:
            raise BaseException("Movement Detected timetamp is None")
        gif_content = io.BytesIO(gifContent)
        movement_timestamp_str = self.movementDetectedTimestamp.strftime("%m%d%Y_%H%M%S")
        gif_content.name = f"movement_{movement_timestamp_str}.gif"
        self.sendGifToSubscribers(gif_content)


    def sendGifToSubscribers(self, bytesBuffer: io.BytesIO) -> None:
        for subscriber in self.listOfUnprocessedSubscribers:
            try:
                self.yag.send(
                    to=subscriber.email,
                    subject="Movement detected",
                    contents=self.getMessageForSubscriber(subscriber),
                    attachments = bytesBuffer
                )
                subscriber.last_warning_sent_date = self.movementDetectedTimestamp
            except Exception as e:
                logger.error("Error during sending email notification to subscriber: %s", subscriber.email)
                logger.error(e)
                continue
        self.listOfUnprocessedSubscribers.clear()

    def getMessageForSubscriber(self, subscriber: EmailSubsriber) -> str:
        return f"""
            Hello {subscriber.username}, 

                We have detected continuous movement in one of the cameras you are subscribed to.
                In attachment we are providing you with a video material where you can observe the movement in question.

            Kind regards,
            Motion Detection Bot
        """
    
    def loadSubscriberSettings(self, subscriberSettings:Dict) -> None:
        for email in subscriberSettings["emailSubscribers"]:
            self.allSubscribers[email] = EmailSubsriber(
                subscriberSettings["emailSubscribers"][email]["username"],
                email,
                subscriberSettings["emailSubscribers"][email]["backoff"]["hour"],
                backoffIntervalMinute=subscriberSettings["emailSubscribers"][email]["backoff"]["minutes"]
                )
        self.enableNotifications = subscriberSettings["broadcastToSubscribers"]
        
    @pyqtSlot(dict)
    def onSubscriberAdded(self, subscriber: Dict) -> None:
        email = subscriber["email"]
        if email in self.allSubscribers:
            self.allSubscribers[email].email = email
            self.allSubscribers[email].username = subscriber["username"]
            self.allSubscribers[email].backoffIntervalHour = subscriber["backoff"]["hour"]
            self.allSubscribers[email].backoffIntervalMinute = subscriber["backoff"]["minutes"]
            return
        self.allSubscribers[email] = EmailSubsriber(
            subscriber["username"],
            subscriber["email"],
            subscriber["backoff"]["hour"], 
            subscriber["backoff"]["minutes"]
        )
    
    @pyqtSlot(bool)
    def onEnableNotificationsToggled(self, enabled: bool) -> None:
        logger.info("Email notification toggled, value: %s", enabled)
        self.enableNotifications = enabled
            
class GifCreator(QObject):
    gifReady = pyqtSignal(bytes)
    toggledRunning = pyqtSignal(bool)
    def __init__(self) -> None:
        super().__init__()
        self.running = False
        self.framesForGif: List[Frame] = []
        self.gifCreationTimer = None
    
    @pyqtSlot(bool)
    def onCreateGifToggle(self, togleCreate: bool) -> None:
        self.running = togleCreate
        if not self.running:
            self.framesForGif.clear()
        else:
            if not self.gifCreationTimer:
                self.gifCreationTimer = QTimer()
                self.gifCreationTimer.setInterval(GIF_DURATION)
                self.gifCreationTimer.timeout.connect(self.onGifCreationStart)
                self.gifCreationTimer.setSingleShot(True)
            self.gifCreationTimer.start()
        self.toggledRunning.emit(togleCreate)
    
    @pyqtSlot()
    def onGifCreationStart(self) -> None:
        if not self.framesForGif:
            return
        gifBytes = io.BytesIO()
        logger.info("Started creating GIF")
        iio.imwrite(gifBytes, self.framesForGif, extension=".gif")
        logger.info("Finished creating GIF")
        gifBytes.seek(0)
        self.gifReady.emit(gifBytes.getvalue())
        self.running = False
        self.toggledRunning.emit(False)

    @pyqtSlot(Frame)
    def onFrameReceived(self, frame: Frame) -> None:
        if not self.running:
            return
        self.framesForGif.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


    

    

    




    

    

