from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.sip import voidptr
from PyQt5.QtNetwork import QTcpSocket


class TCPSocketWorker(QObject):
    errorWhenSettingDescriptor = pyqtSignal(QTcpSocket.SocketError)

    def __init__(self, handle: voidptr) -> None:
        self.handle = handle
        self.tcpSock = QTcpSocket(self)
    
    @pyqtSlot()
    def onStart(self):
        isSuccess = self.tcpSock.setSocketDescriptor(self.handle)
        if not isSuccess:
            self.errorWhenSettingDescriptor.emit(self.tcpSock.error())
        print("Worker socket started !")
    
    @pyqtSlot()
    def onClose(self):
        self.tcpSock.close()
        print("Worker socket closed !")
    
    @pyqtSlot(bytes)
    def onDataReadyToSend(self, data: bytes):
        self.tcpSock.writeData(data)



        
