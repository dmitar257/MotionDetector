from frame_processors.frameFetcher import FrameFetcher, FrameFetcherSettings
from frame_processors.cameraFrameFetcher import CameraFrameFetcher
from frame_processors.videoFrameFetcher import VideoFrameFetcher
from utils import SourceMediaType

class FrameFetcherFactory:

    frameFetchers = {
        SourceMediaType.CAMERA: CameraFrameFetcher,
        SourceMediaType.VIDEO: VideoFrameFetcher
    }

    @classmethod
    def createFrameFetcher(cls, fetcherType: SourceMediaType, settings: FrameFetcherSettings) -> FrameFetcher:
        return cls.frameFetchers[fetcherType] (settings)



        
