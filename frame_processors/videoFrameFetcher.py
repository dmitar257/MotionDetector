from frame_processors.frameFetcher import FrameFetcher, FrameFetcherSettings

class VideoFrameFetcher(FrameFetcher):

    def __init__(self, frameFetcherSEttings: FrameFetcherSettings):
        super().__init__(frameFetcherSEttings)
    
    def startCapturingFrames(self) -> None:
        pass
