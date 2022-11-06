from PyQt5.QtCore import  pyqtSignal, QObject, pyqtSlot
from PyQt5.QtNetwork import QTcpServer, QHostAddress
from typing import Optional
from PyQt5.sip import voidptr
import logging

logger = logging.getLogger(__name__)

class TcpServer(QTcpServer):
    connectionToServerMade = pyqtSignal(voidptr)

    def __init__(self, listening_port: int, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)
        self.listeningPort = listening_port
    
    def incomingConnection(self, handle: voidptr) -> None:
        self.connectionToServerMade.emit(handle)
    
    def startListening(self):
        self.listen(QHostAddress.Any, self.listeningPort)
        logger.info("Started listening for connection requests from clients, on port: %s", self.listeningPort)
    
    def onClose(self):
        logger.info("Closing TCP server socket !")
        self.close()
        
