from asyncio.log import logger
import struct
from typing import Any, Optional, Union
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QThread
import cv2
from PyQt5.QtNetwork import QTcpSocket
from utils import Frame
import uuid
import logging

FRAME_SENDING_INTERVAL = 1/30

logger = logging.getLogger(__name__)

class FrameToNetworkStreamer(QObject):
    connectionTerminated = pyqtSignal(str)

    def __init__(self, client_socket_handle: Any) -> None:
        super().__init__()
        self.client_socket: Optional[QTcpSocket] = None
        self.current_frame: Optional[Frame] = None
        self.sendingTimer: Optional[QTimer] = None
        self.client_socket_handle = client_socket_handle
        self.id = str(uuid.uuid4())
          
    def onStart(self) -> None:
        self.initializeSendingTimer()
        self.sendingTimer.start()
        self.client_socket = QTcpSocket(self)
        self.client_socket.setSocketDescriptor(self.client_socket_handle)
        self.client_socket.disconnected.connect(self.onConnectionTerminated)
    
    def initializeSendingTimer(self) -> None:
        self.sendingTimer = QTimer()
        self.sendingTimer.setInterval(int(FRAME_SENDING_INTERVAL * 1000))
        self.sendingTimer.timeout.connect(self.sendFrame)
    
    def initializeClientSocket(self) -> None:
        self.client_socket = QTcpSocket()
        self.client_socket.setSocketDescriptor(self.client_socket_handle)

    def sendFrame(self) -> None:
        if self.current_frame is None:
            return
        encoded_frame = self.get_encoded_frame(self.current_frame)
        self.writeDataToSocket(encoded_frame)
        self.current_frame = None
    
    def writeDataToSocket(self, content:Union[bytes, bytearray]) -> None:
        bytes_written = self.client_socket.write(content)

    def get_encoded_frame(self, frame: Frame) -> bytearray:
        img_encoded = cv2.imencode('.jpg', frame)[1].tobytes()
        res = struct.pack("I", len(img_encoded))
        frame_bytes_with_size = bytearray(res)
        frame_bytes_with_size.extend(img_encoded)
        return frame_bytes_with_size
        
    @pyqtSlot(Frame)
    def onFrameReceived(self, frame:Frame) -> None:
        self.current_frame = frame
    
    @pyqtSlot()
    def onConnectionTerminated(self) -> None:
        logger.info("Connection with remote client, client_id: %s is terminated !", self.id)
        self.connectionTerminated.emit(self.id)
    
    def get_id(self) -> str:
        return self.id

        


    



    