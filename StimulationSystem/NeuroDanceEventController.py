import time

import OperationSystem.Streaming.NeuroDanceEEGProcess
from StimulationSystem.BaseEventController import BaseEventController
from multiprocessing import shared_memory


class NeuroDanceEventController(BaseEventController):
    def __init__(self) -> None:
        print("NeuroDanceEventController Init")
        OperationSystem.Streaming.NeuroDanceEEGProcess.create_event_share_list()
        self.clearEvent()

    def sendEvent(self, eventType, millisecond):
        sync_event_info = shared_memory.ShareableList(name='Event')
        millis_second = int(round(time.time() * 1000))
        sync_event_info[0] = millis_second
        sync_event_info[1] = eventType

        # NeuroDanceEEGThread.neuro_dance_event_info = NeuroDanceEventInfo(millis_second, eventType)
        print("NeuroDanceEventController stimulatetime{0},,eventType::{1}".format(sync_event_info[0], eventType))

    def clearEvent(self):
        sync_event_info = shared_memory.ShareableList(name='Event')
        sync_event_info[0] = None
        sync_event_info[1] = None
        print("neuroDance clear event")

class NeuroDanceEventInfo:

    def __init__(self, stimulation_time, event_type):
        self.stimulation_time = stimulation_time
        self.event_type = event_type
