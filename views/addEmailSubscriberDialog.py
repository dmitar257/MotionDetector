from typing import Any, Dict, Optional
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QMessageBox
import re

EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

class AddEmailSubscriberDialog(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        uic.loadUi('ui/addEmailSubscriberDialog.ui',self)
        self.setWindowTitle("Add Email Subscriber")
        self.usernameLineEdit = self.findChild(QtWidgets.QLineEdit,'usernameLineEdit')
        self.emailLineEdit = self.findChild(QtWidgets.QLineEdit,'emailLineEdit')
        self.hoursSpinBox = self.findChild(QtWidgets.QSpinBox, 'hoursSpinBox')
        self.minutesSpinBox = self.findChild(QtWidgets.QSpinBox, 'minutesSpinBox')
        self.addUserBtn = self.findChild(QtWidgets.QPushButton,'addUserButton')
        self.cancelButton = self.findChild(QtWidgets.QPushButton,'cancelButton')
    
        self.addUserBtn.clicked.connect(self.onAddUserBtnClicked)
        self.cancelButton.clicked.connect(self.onCancelBtnClicked)
        self.setWhatsThisTips()
    
    def onAddUserBtnClicked(self) -> None:
        username = self.usernameLineEdit.text().strip()
        email = self.emailLineEdit.text().strip()
        if len(username) < 3:
            self.displayUsernameErrorMesageBox()
            return
        if not self.checkEmail(email):
            self.displayEmailErrorMesageBox()
            return
        self.accept()
    
    def onCancelBtnClicked(self) -> None:
        self.reject()

    def displayUsernameErrorMesageBox(self) -> None:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Invalid username")
        msg.setInformativeText("Username must be more than 4 characters long !")
        msg.setWindowTitle("Input error")
        msg.exec_()

    def checkEmail(self, email: str) -> bool:
        if(re.fullmatch(EMAIL_REGEX, email)):
            return True
        return False
    
    def displayEmailErrorMesageBox(self) -> None:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Invalid email")
        msg.setInformativeText("Please provide regular email string as input")
        msg.setWindowTitle("Input error")
        msg.exec_()
    
    def getData(self) -> Dict:
        return {
            "username": self.usernameLineEdit.text(),
            "email": self.emailLineEdit.text(),
            "backoff":{
                "minutes": self.minutesSpinBox.value(),
                "hour": self.hoursSpinBox.value()
            }
        }
        
    def setWhatsThisTips(self) -> None:
        usernameInfo = "Username of subscriber who wants to receive GIF notifications on continuous movement detection"
        emailInfo = 'Email of subscriber who wants to receive GIF notifications on continuous movement detection. Needs to follow email format'
        timeInfo = 'Backoff interval in hours and minutes. When continuos movement is detected the subscriber will receive the email notification. As a spam block, if any further movement is detected while this interval has not expired from last notiffication, the subscriber wont be notified.'
        self.findChild(QtWidgets.QLabel, 'usernameLabel').setWhatsThis(usernameInfo)
        self.findChild(QtWidgets.QLineEdit, 'usernameLineEdit').setWhatsThis(usernameInfo)
        self.findChild(QtWidgets.QLabel, 'emailLabel').setWhatsThis(emailInfo)
        self.findChild(QtWidgets.QLineEdit, 'emailLineEdit').setWhatsThis(emailInfo)
        self.findChild(QtWidgets.QLabel, 'backoffTimeLabel').setWhatsThis(timeInfo)
        self.findChild(QtWidgets.QLabel, 'hoursLabel').setWhatsThis(timeInfo)
        self.findChild(QtWidgets.QLabel, 'minutesLabel').setWhatsThis(timeInfo)
        self.findChild(QtWidgets.QSpinBox, 'hoursSpinBox').setWhatsThis(timeInfo)
        self.findChild(QtWidgets.QSpinBox, 'minutesSpinBox').setWhatsThis(timeInfo)