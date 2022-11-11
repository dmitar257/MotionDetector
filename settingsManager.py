from typing import Dict, List
from PyQt5.QtCore import QObject, pyqtSignal, QSettings
from utils import AlgorithmType, createFolderIfNoExisting
import os


defaultSettings = {
    "frameTransformatorSettings":{
        "backgroundSubstractionSettings":{
            "algorithmType":AlgorithmType.RUNNING_AVG,
            "thresholdBinValue" : 25,
            "runningAvgAlpha": 0.05,
            "gaussianMixtureHistory": 250,
            "runningAvgMinArea": 2000,
            "gaussianMixtureMinArea": 1000      
        },
        "resizeDimension": 500,
        "gaussianBlurKernelSize" : 15,
        "erosionKernelSize": 3,
        "erosionIterations": 4,
        "dilationKernelSize": 3,
        "dilationIterations": 8,  
    },
    "movementRecorderSettings":{
        "movementPresentThreshold": 10000,
        "movementAbsenceThreshold": 3000,
        "recordingsDir": os.path.join(os.getcwd(),'recordings')
    },
    "soundDetectorSettings":{
        "soundDetectionEnabled":True,
        "volumeThreshold":25
    },
    "movementLoggerSettings":{
        "loggingInterval":500,
        "scalingWidth": 800,
        "invertedXaxis":False,
        "loggingPath":"C:\\test\\test.txt"
    },
    "cameraSettings":{
        "cameraIndex":0
    },
    "objectDetectionSettings":{
        "detectionEnabled": False,
        "confidenceThreshold": 0.5
    },
    "emailSubscribers": {
    }
}

class SettingsManager(QObject):
    frameDetectionSettingsSet = pyqtSignal(dict)
    frameRecordingSettingsSet = pyqtSignal(dict)
    soundDetectionSettingsSet = pyqtSignal(dict)
    movementLoggerSettingsSet = pyqtSignal(dict)
    cameraSettingsSet = pyqtSignal(dict)
    objectDetectionSettingsSet = pyqtSignal(dict)
    emailSubscriberAdded = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("MasterWork","MotionDetector")
        self.currentSettings = self.loadSettings()
        self.initializeDirs()
        self.reloadRecordingPathIfNeeded()
        
    def initializeDirs(self) -> None:
        createFolderIfNoExisting(self.currentSettings["movementRecorderSettings"]["recordingsDir"])
        createFolderIfNoExisting(os.path.dirname(self.currentSettings["movementLoggerSettings"]["loggingPath"]))

    def getAllSettings(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings
        return self.currentSettings
    
    def getFrameTransformationSettings(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings["frameTransformatorSettings"]
        return self.currentSettings["frameTransformatorSettings"]
    
    def getHardDetectionFrameTransformationSettings(self) -> Dict:
        return {
            "backgroundSubstractionSettings":{
                "algorithmType":AlgorithmType.RUNNING_AVG,
                "thresholdBinValue" : 20,
                "runningAvgAlpha": 0.03,
                "gaussianMixtureHistory": 250,
                "runningAvgMinArea": 10000,
                "gaussianMixtureMinArea": 2000      
            },
            "resizeDimension": 500,
            "gaussianBlurKernelSize" : 15,
            "erosionKernelSize": 7,
            "erosionIterations": 5,
            "dilationKernelSize": 3,
            "dilationIterations": 8,  
        }
    
    def getMovementTrackerSettings(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings["movementRecorderSettings"]
        return self.currentSettings["movementRecorderSettings"]
    
    def getSoundDetectionSettings(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings["soundDetectorSettings"]
        return self.currentSettings["soundDetectorSettings"]

    def getMovementLoggerSettingss(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings["movementLoggerSettings"]        
        return self.currentSettings["movementLoggerSettings"]
    
    def getCameraSettings(self) -> Dict:
        return self.currentSettings["cameraSettings"]
    
    def getObjectDetectionSettings(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings["objectDetectionSettings"]  
        return self.currentSettings["objectDetectionSettings"]
    
    def getEmailSubscribers(self) -> List:
        return self.currentSettings["emailSubscribers"]
    
    def setSoundDetectionSettings(self, soundDetectionSettings: Dict) -> Dict:
        self.currentSettings["soundDetectorSettings"] = soundDetectionSettings
        self.soundDetectionSettingsSet.emit(soundDetectionSettings)

    def setFrameTransformationSettings(self, motionDetectionSettings: Dict) -> None:
        self.currentSettings["frameTransformatorSettings"] = motionDetectionSettings
        self.frameDetectionSettingsSet.emit(motionDetectionSettings)
    
    def setFrameRecordingSettings(self, motionRecordingSettings: Dict) -> None:
        self.currentSettings["movementRecorderSettings"] = motionRecordingSettings
        self.frameRecordingSettingsSet.emit(motionRecordingSettings)
    
    def setMovementLoggerSettings(self, motionRecordingSettings: Dict) -> None:
        self.currentSettings["movementLoggerSettings"] = motionRecordingSettings
        self.movementLoggerSettingsSet.emit(motionRecordingSettings)
    
    def setCameraSettings(self, cameraSettings: Dict) -> None:
        self.currentSettings["cameraSettings"] = cameraSettings
        self.cameraSettingsSet.emit(cameraSettings)
    
    def setObjectDetectionSettings(self, objectDetectionSettings: Dict) -> None:
        self.currentSettings["objectDetectionSettings"] = objectDetectionSettings
        self.objectDetectionSettingsSet.emit(objectDetectionSettings)
    
    def addEmailSubscription(self, emailSubDict: Dict) -> None:
        self.currentSettings["emailSubscribers"][emailSubDict["email"]] = emailSubDict
        self.emailSubscriberAdded.emit(emailSubDict) 
    
    def saveSettings(self) -> None:
        self.saveSettingsToIniFile()
    
    def loadSettings(self) -> Dict:
        if self.valuesInIniExists():
            return self.loadSettingsFromIniFile()
        return defaultSettings.copy()
    
    def valuesInIniExists(self) -> bool:
        return self.settings.value("configExists")

    def saveSettingsToIniFile(self) -> None:
        self.settings.setValue("algorithmType", self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['algorithmType'])
        self.settings.setValue("gaussianBlurKernelSize",self.currentSettings['frameTransformatorSettings']['gaussianBlurKernelSize'])
        self.settings.setValue("resizeDimension",self.currentSettings['frameTransformatorSettings']['resizeDimension'])
        self.settings.setValue("thresholdBinValue",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['thresholdBinValue'])
        self.settings.setValue("erosionKernelSize",self.currentSettings['frameTransformatorSettings']['erosionKernelSize'])
        self.settings.setValue("erosionIterations",self.currentSettings['frameTransformatorSettings']['erosionIterations'])
        self.settings.setValue("dilationKernelSize",self.currentSettings['frameTransformatorSettings']['dilationKernelSize'])
        self.settings.setValue("dilationIterations",self.currentSettings['frameTransformatorSettings']['dilationIterations'])
        self.settings.setValue("runningAvgMinArea",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['runningAvgMinArea'])
        self.settings.setValue("runningAvgAlpha",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['runningAvgAlpha'])
        self.settings.setValue("gaussianMixtureMinArea",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['gaussianMixtureMinArea'])
        self.settings.setValue("gaussianMixtureHistory",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['gaussianMixtureHistory'])
        self.settings.setValue("movementPresentThreshold", self.currentSettings['movementRecorderSettings']['movementPresentThreshold'])
        self.settings.setValue("movementAbsenceThreshold", self.currentSettings['movementRecorderSettings']['movementAbsenceThreshold'])
        self.settings.setValue("recordingsDir",self.currentSettings['movementRecorderSettings']['recordingsDir'])
        self.settings.setValue("volumeThreshold",self.currentSettings['soundDetectorSettings']['volumeThreshold'])
        self.settings.setValue("soundDetectionEnabled",self.currentSettings['soundDetectorSettings']['soundDetectionEnabled'])
        self.settings.setValue("loggingInterval",self.currentSettings["movementLoggerSettings"]['loggingInterval'])
        self.settings.setValue("scalingWidth",self.currentSettings["movementLoggerSettings"]['scalingWidth'])
        self.settings.setValue("invertedXaxis",self.currentSettings["movementLoggerSettings"]['invertedXaxis'])
        self.settings.setValue("loggingPath",self.currentSettings["movementLoggerSettings"]['loggingPath'])
        self.settings.setValue("cameraIndex",self.currentSettings["cameraSettings"]['cameraIndex'])
        self.settings.setValue("detectionEnabled",self.currentSettings["objectDetectionSettings"]['detectionEnabled'])
        self.settings.setValue("confidenceThreshold",self.currentSettings["objectDetectionSettings"]['confidenceThreshold'])
        self.settings.setValue("emailSubscribers", self.currentSettings["emailSubscribers"])
        self.settings.setValue("configExists", True)

    def loadSettingsFromIniFile(self) -> Dict:
        return {
            "frameTransformatorSettings":{
                "backgroundSubstractionSettings":{
                    "algorithmType": AlgorithmType(self.settings.value("algorithmType")),
                    "thresholdBinValue" : self.settings.value("thresholdBinValue"),
                    "runningAvgAlpha": float(self.settings.value("runningAvgAlpha")),
                    "gaussianMixtureHistory": self.settings.value("gaussianMixtureHistory"),
                    "runningAvgMinArea": self.settings.value("runningAvgMinArea"),
                    "gaussianMixtureMinArea": self.settings.value("gaussianMixtureMinArea")      
                },
                "resizeDimension": self.settings.value("resizeDimension"),
                "gaussianBlurKernelSize" : self.settings.value("gaussianBlurKernelSize"),
                "erosionKernelSize": self.settings.value("erosionKernelSize"),
                "erosionIterations": self.settings.value("erosionIterations"),
                "dilationKernelSize": self.settings.value("dilationKernelSize"),
                "dilationIterations": self.settings.value("dilationIterations"),  
            },
            "movementRecorderSettings":{
                "movementPresentThreshold": self.settings.value("movementPresentThreshold"),
                "movementAbsenceThreshold": self.settings.value("movementAbsenceThreshold"),
                "recordingsDir": self.settings.value("recordingsDir")
            },
            "soundDetectorSettings":{
                "soundDetectionEnabled": True if self.settings.value('soundDetectionEnabled') in ['true','True'] else False,
                "volumeThreshold":self.settings.value("volumeThreshold")
            },
            "movementLoggerSettings":{
                "loggingInterval":self.settings.value("loggingInterval"),
                "scalingWidth": self.settings.value("scalingWidth"),
                "invertedXaxis": True if self.settings.value('invertedXaxis') in ['true','True'] else False,
                "loggingPath":self.settings.value("loggingPath")
            },
            "cameraSettings":{
                "cameraIndex": self.settings.value("cameraIndex")
            },
            "objectDetectionSettings":{
                "detectionEnabled": True if self.settings.value('detectionEnabled') in ['true','True'] else False,
                "confidenceThreshold": float(self.settings.value("confidenceThreshold"))
            },
            "emailSubscribers": self.settings.value("emailSubscribers")      
        }
    
    def reloadRecordingPathIfNeeded(self) -> None:
        if not os.path.exists(self.currentSettings["movementRecorderSettings"]["recordingsDir"]):
            self.currentSettings["movementRecorderSettings"]["recordingsDir"] = defaultSettings["movementRecorderSettings"]["recordingsDir"]

