from abc import ABC, abstractmethod

class BaseExecutor(ABC):
    def __init__(self, signal, stopLoss=None, takeProfit=None):
        self.signal = signal
        self.stopLoss = stopLoss
        self.takeProfit = takeProfit

    @abstractmethod
    def execute_trade(self):
        pass

    @abstractmethod
    def health(self):
        pass