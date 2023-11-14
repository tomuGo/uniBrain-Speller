

class BaseStreaming:

    eventExist = False

    def __init__(self, config) -> None:
        pass

    # def run(self):
    #     pass

    def connect(self):
        pass

    def disconnect(self):
        pass

    def readFixedData(self, startPoint, length):
        pass

    def readFlowData(self, startPoint, length):
        pass