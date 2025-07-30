class QCAlgorithm:
    def __init__(self):
        self.Portfolio = {}
    def SetStartDate(self, year, month, day): pass
    def SetEndDate(self, year, month, day): pass
    def SetCash(self, amount): pass
    def AddEquity(self, symbol, resolution=None): pass
    def SetHoldings(self, symbol, proportion): pass
    def Debug(self, message): print(message)

try:
    from AlgorithmImports import QCAlgorithm
    print("Imported QCAlgorithm from AlgorithmImports")
    QCAlgorithmClass = QCAlgorithm
except ImportError:
    print("AlgorithmImports not found, using stub QCAlgorithm")
    QCAlgorithmClass = QCAlgorithm

class BasicTemplateAlgorithm(QCAlgorithmClass):
    def Initialize(self):
        self.SetStartDate(2020,1,1)    # Set Start Date
        self.SetEndDate(2020,12,31)    # Set End Date
        self.SetCash(100000)           # Set Strategy Cash

        self.AddEquity("SPY", Resolution.Daily)  # Add Equity

    def OnData(self, data):
        if not self.Portfolio["SPY"].Invested:
            self.SetHoldings("SPY", 1)  # Invest 100% in SPY
            self.Debug("Purchased SPY")