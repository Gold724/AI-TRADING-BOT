# Mock AlgorithmImports for testing purposes
# This file provides mock implementations of QuantConnect classes for local testing

from datetime import datetime, timedelta
import random

class QCAlgorithm:
    """Mock QuantConnect Algorithm base class"""
    def __init__(self):
        self.Portfolio = MockPortfolio()
        self.Securities = MockSecurities()
        self.Schedule = MockSchedule()
        self.DateRules = MockDateRules()
        self.TimeRules = MockTimeRules()
        self.Time = datetime.now()
    def Log(self, message):
        print(f"[{self.Time.strftime('%H:%M:%S')}] {message}")
        
    def Debug(self, message):
        print(f"[DEBUG] {message}")
        
    def Error(self, message):
        print(f"[ERROR] {message}")
        
    def SetStartDate(self, year, month, day):
        pass
        
    def SetEndDate(self, year, month, day):
        pass
        
    def SetCash(self, amount):
        pass
        
    def SetTimeZone(self, timezone):
        pass
        
    def AddFuture(self, future_type, resolution=None, contractFilter=None):
        return MockSecurity(future_type)
        
    def AddEquity(self, symbol, resolution=None):
        return MockSecurity(symbol)
        
    def MarketOrder(self, symbol, quantity):
        return MockOrderTicket()
        
    def LimitOrder(self, symbol, quantity, price):
        return MockOrderTicket()
        
    def StopMarketOrder(self, symbol, quantity, stop_price):
        return MockOrderTicket()
        
class MockPortfolio:
    def __init__(self):
        self.TotalPortfolioValue = 100000
        self.Cash = 100000
        
class MockSecurities:
    def __init__(self):
        pass
        
class MockSchedule:
    def __init__(self):
        pass
        
    def On(self, *args, **kwargs):
        pass
        
class MockDateRules:
    """Mock DateRules class"""
    def EveryDay(self, symbol=None):
        return "EveryDay"
        
    def Every(self, days):
        return f"Every{days}Days"

class MockTimeRules:
    """Mock TimeRules class"""
    def At(self, hour, minute):
        return f"At{hour}:{minute}"
        
    def AfterMarketOpen(self, symbol, minutes=0):
        return f"AfterMarketOpen+{minutes}min"
        
class MockSecurity:
    def __init__(self, symbol):
        self.Symbol = symbol
        self.Price = 2000.0  # Mock gold price
        
class MockOrderTicket:
    def __init__(self):
        self.OrderId = random.randint(1000, 9999)
        
class Futures:
    @staticmethod
    def Gold():
        return "GC"
    
    class Metals:
        Gold = "GC"
        
class Resolution:
    Minute = "Minute"
    Hour = "Hour"
    Daily = "Daily"
    
class Market:
    COMEX = "COMEX"
    USA = "USA"
    
class DataMappingMode:
    LastTradingDay = "LastTradingDay"
    FirstDayMonth = "FirstDayMonth"
    
class DataNormalizationMode:
    Raw = "Raw"
    
class TimeZones:
    NewYork = "America/New_York"
    UTC = "UTC"