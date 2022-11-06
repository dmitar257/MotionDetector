from dataclasses import dataclass
import logging
from PyQt5.QtCore import QThread, QObject, pyqtSlot
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Tuple, Union


logger = logging.getLogger(__name__)

@dataclass
class WorkerGroupInfo:
    worker_obj: QObject
    worker_group: str
    on_start_method: Optional[Callable] = None
    on_close_method: Optional[Callable] = None
    id: Optional[int] = None


class WorkerThreadController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.worker_groups: Dict[str, List[Tuple[QThread, Optional[int]]]] = dict()

    def addWorkerToGroup(self, worker_group_info: WorkerGroupInfo, use_existing_thread: bool = False) -> None:
        worker_thread = self.getWorkerThread(use_existing_thread, worker_group_info.worker_group)
        worker_group_info.worker_obj.moveToThread(worker_thread)
        if worker_group_info.on_start_method:
            worker_thread.started.connect(worker_group_info.on_start_method)
        if worker_group_info.on_close_method:
            worker_thread.finished.connect(worker_group_info.on_close_method)
        self.placeWorkerThreadInGroup(worker_thread, worker_group_info)

    def getWorkerThread(self, using_existing_thread: bool, worker_group_name: str) -> QThread:
        if using_existing_thread and  worker_group_name in self.worker_groups.keys():
            for worker in self.worker_groups[worker_group_name]:
                if not worker[0].isRunning():
                    logger.info("Using existing worker thread from group: %s",worker_group_name)
                    return worker[0]
        logger.info("Creating new worker thread")
        return QThread()

    def placeWorkerThreadInGroup(self, worker_thread: QThread, worker_group_info: WorkerGroupInfo) -> None:
        if worker_group_info.worker_group not in self.worker_groups.keys():
            logger.info("Creating new worker group: %s", worker_group_info.worker_group)
            self.worker_groups[worker_group_info.worker_group] = []
        logger.info("Adding worker to working group: %s", worker_group_info.worker_group)
        self.worker_groups[worker_group_info.worker_group].append((worker_thread, worker_group_info.id))
        
    def startWorkerGroup(self, worker_group_name: str) -> None:
        logger.info("Started worker group: %s", worker_group_name)
        for worker in self.worker_groups[worker_group_name]:
            if not worker[0].isRunning():
                worker[0].start()

    def stopWorkerGroup(self, worker_group_name:str) -> None:
        if not worker_group_name in self.worker_groups:
            logger.info("Worker group: %s could not be found", worker_group_name)
            return
        logger.info("Stoping worker group: %s", worker_group_name)
        for worker in self.worker_groups[worker_group_name]:
            if worker[0].isRunning():
                worker[0].exit()
                worker[0].wait()
        logger.info("Worker group stoped: %s", worker_group_name)

    def stopAllWorkerGroups(self) -> None:
        for worker_group in self.worker_groups.keys():
            self.stopWorkerGroup(worker_group)
    
    def deleteObjectByIdFromWorkerGroup(self, id: int, worker_group_name:str) -> None:
        element_found = False
        index = 0
        for worker in self.worker_groups[worker_group_name]:
            if worker[1] and worker[1]==id and worker[0].isRunning():
                worker[0].exit()
                worker[0].wait()
                logger.info("Found and terminated worker thread for worker with id: %s in worker group: %s", worker[1], worker_group_name)
                element_found = True
                break
            index += 1
        if element_found:
            del self.worker_groups[worker_group_name][index]
    
    def __del__(self):
        logger.info("Thread Worker Destroyed")
        
            



