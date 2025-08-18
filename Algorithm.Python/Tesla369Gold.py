from AlgorithmImports import *

class Tesla369Gold(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2024, 1, 1)
        self.SetCash(100000)  # paper cash; risk is governed by contract sizing
        self.UniverseSettings.Resolution = Resolution.Minute

        # Parameters
        self.tradesPerDay = int(self.GetParameter("trades_per_day") or "3")
        if self.tradesPerDay not in (3,6,9):
            self.tradesPerDay = 3
        self.dailyTarget = float(self.GetParameter("daily_profit_target") or "535.71")
        self.dailyMaxDD = float(self.GetParameter("daily_max_drawdown") or "267.0")
        self.maxContracts = int(self.GetParameter("max_contracts") or "3")
        self.defaultContracts = int(self.GetParameter("default_contracts") or "1")
        
        # Target and Stop percentages
        self.tpPct = float(self.GetParameter("tp_pct") or "0.0015")  # 0.15%
        self.slPct = float(self.GetParameter("sl_pct") or "0.0002")  # 0.02%

        # Add Gold Futures (GC)
        future = self.AddFuture(Futures.Metals.Gold, Resolution.Minute)
        future.SetFilter(timedelta(0), timedelta(days=60))
        self.futureSymbol = None

        self.SetWarmUp(200, Resolution.Minute)
        self.pnlToday = 0
        self.tradesToday = 0
        self.currentDate = None
        
        # Track open orders for OCO management
        self.openOrders = {}
        self.lastTradePrice = None

        # 5-min consolidator & rolling stats
        self.consolidator = TradeBarConsolidator(timedelta(minutes=5))
        self.SubscriptionManager.AddConsolidator(future.Symbol, self.consolidator)
        self.bars5 = RollingWindow[TradeBar](50)
        self.consolidator.DataConsolidated += self.OnFiveMinuteBar

        # Volume average for spike detection
        self.volAvg = SimpleMovingAverage(5)
        self.vwapSumPV = 0
        self.vwapSumV = 0

        # Track prior session H/L
        self.prevSessHigh = None
        self.prevSessLow = None

        # Reset counters daily
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.At(0,1), self.ResetDaily)
        
        # Auto-flat at 15:30 NY
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.At(15,30), self.FlattenPositions)

        # Session windows (NY)
        self.ny = TimeZones.NewYork
        
        # Logging setup
        self.tradeLog = []

    def OnSecuritiesChanged(self, changes):
        # Choose the nearest GC contract
        for sec in changes.AddedSecurities:
            if sec.Symbol.SecurityType == SecurityType.Future and sec.Symbol.ID.Symbol == "GC":
                if self.futureSymbol is None:
                    self.futureSymbol = sec.Symbol
                    self.Debug(f"Selected GC contract: {self.futureSymbol}")

    def ResetDaily(self):
        """Reset daily counters and update session levels"""
        self.pnlToday = 0
        self.tradesToday = 0
        self.currentDate = self.Time.date()
        self.openOrders = {}
        
        # Reset VWAP calculation
        self.vwapSumPV = 0
        self.vwapSumV = 0
        
        # Update previous session H/L using yesterday's data
        if self.bars5.Count > 0:
            highs = [b.High for b in list(self.bars5)]
            lows = [b.Low for b in list(self.bars5)]
            self.prevSessHigh = max(highs) if highs else None
            self.prevSessLow = min(lows) if lows else None
            
        self.Debug(f"Daily reset - PrevHigh: {self.prevSessHigh}, PrevLow: {self.prevSessLow}")
        
    def FlattenPositions(self):
        """Auto-flat all positions at 15:30 NY"""
        if self.futureSymbol and self.Portfolio[self.futureSymbol].Quantity != 0:
            self.Liquidate(self.futureSymbol)
            self.Debug("Auto-flattened positions at 15:30 NY")
            
        # Cancel all open orders
        for ticket in self.openOrders.values():
            if ticket.Status == OrderStatus.Submitted or ticket.Status == OrderStatus.PartiallyFilled:
                ticket.Cancel()
        self.openOrders = {}

    def InSessionWindow(self, nytime):
        """Check if current time is within trading session windows"""
        t = nytime.time()
        if time(3,0) <= t <= time(6,0): return True
        if time(8,20) <= t <= time(11,30): return True
        if time(13,0) <= t <= time(15,30): return True
        return False

    def OnFiveMinuteBar(self, sender, bar: TradeBar):
        if self.futureSymbol is None: return
        if bar.Symbol != self.futureSymbol: return

        # Maintain rolling window & indicators
        self.bars5.Add(bar)
        self.volAvg.Update(bar.EndTime, bar.Volume)
        self.vwapSumPV += bar.Close * bar.Volume
        self.vwapSumV += bar.Volume
        vwap = self.vwapSumPV / self.vwapSumV if self.vwapSumV > 0 else bar.Close

        # Stop if warming up or insufficient data
        if self.IsWarmingUp or self.bars5.Count < 6: return

        # Daily limits check
        if self.tradesToday >= self.tradesPerDay:
            return
        if self.pnlToday >= self.dailyTarget:
            self.Debug(f"Daily target reached: ${self.pnlToday:.2f}")
            return
        if self.pnlToday <= -self.dailyMaxDD:
            self.Debug(f"Daily drawdown limit hit: ${self.pnlToday:.2f}")
            return

        # Session windows (NY)
        nytime = Extensions.ConvertTo(self.Time, self.ny)
        if not self.InSessionWindow(nytime):
            return

        # Signal analysis
        prev5 = self.bars5[1]
        volSpike = self.volAvg.IsReady and (bar.Volume > 2.0 * self.volAvg.Current.Value)
        aboveVWAP = bar.Close > vwap
        belowVWAP = bar.Close < vwap
        
        # Sweep and reject patterns
        sweepUp = (self.prevSessHigh and 
                  bar.High > self.prevSessHigh and 
                  bar.Close < self.prevSessHigh)  # sweep & reject
        sweepDown = (self.prevSessLow and 
                    bar.Low < self.prevSessLow and 
                    bar.Close > self.prevSessLow)  # sweep & reject

        # Determine signal strength: base 1; +1 for VWAP confluence; +1 for volume spike
        strengthBuy = 1 if sweepDown else 0
        strengthSell = 1 if sweepUp else 0
        
        if strengthBuy > 0 and aboveVWAP: strengthBuy += 1
        if strengthSell > 0 and belowVWAP: strengthSell += 1
        
        if volSpike:
            if strengthBuy > 0: strengthBuy += 1
            if strengthSell > 0: strengthSell += 1

        # Position sizing based on signal strength
        sizeBuy = min(max(strengthBuy, 0), self.maxContracts)
        sizeSell = min(max(strengthSell, 0), self.maxContracts)
        
        # Ensure minimum default size for valid signals
        if sizeBuy > 0: sizeBuy = max(sizeBuy, self.defaultContracts)
        if sizeSell > 0: sizeSell = max(sizeSell, self.defaultContracts)

        # Risk guard: don't hold both ways
        invested = self.Portfolio[self.futureSymbol].Quantity

        # Place orders
        if sizeBuy > 0 and invested <= 0:
            ticket = self.MarketOrder(self.futureSymbol, sizeBuy)
            self.tradesToday += 1
            self.lastTradePrice = bar.Close
            self.Debug(f"BUY {sizeBuy} @ {bar.Close:.2f} (strength={strengthBuy}, tradesToday={self.tradesToday})")
            self.AttachTargets(bar, isLong=True, size=sizeBuy)
            
        elif sizeSell > 0 and invested >= 0:
            ticket = self.MarketOrder(self.futureSymbol, -sizeSell)
            self.tradesToday += 1
            self.lastTradePrice = bar.Close
            self.Debug(f"SELL {sizeSell} @ {bar.Close:.2f} (strength={strengthSell}, tradesToday={self.tradesToday})")
            self.AttachTargets(bar, isLong=False, size=sizeSell)

    def AttachTargets(self, bar: TradeBar, isLong: bool, size: int):
        """Attach OCO target and stop orders"""
        if not self.futureSymbol:
            return
            
        entryPrice = bar.Close
        
        if isLong:
            # Long position: TP above entry, SL below entry
            tpPrice = entryPrice * (1 + self.tpPct)
            slPrice = entryPrice * (1 - self.slPct)
            
            # Target order (Limit)
            tpTicket = self.LimitOrder(self.futureSymbol, -size, tpPrice)
            tpTicket.Tag = f"TP_Long_{self.Time}"
            
            # Stop order (Stop Market)
            slTicket = self.StopMarketOrder(self.futureSymbol, -size, slPrice)
            slTicket.Tag = f"SL_Long_{self.Time}"
            
        else:
            # Short position: TP below entry, SL above entry
            tpPrice = entryPrice * (1 - self.tpPct)
            slPrice = entryPrice * (1 + self.slPct)
            
            # Target order (Limit)
            tpTicket = self.LimitOrder(self.futureSymbol, size, tpPrice)
            tpTicket.Tag = f"TP_Short_{self.Time}"
            
            # Stop order (Stop Market)
            slTicket = self.StopMarketOrder(self.futureSymbol, size, slPrice)
            slTicket.Tag = f"SL_Short_{self.Time}"
        
        # Store orders for OCO management
        orderGroup = f"OCO_{self.Time}_{size}"
        self.openOrders[f"{orderGroup}_TP"] = tpTicket
        self.openOrders[f"{orderGroup}_SL"] = slTicket
        
        direction = "LONG" if isLong else "SHORT"
        self.Debug(f"Attached {direction} targets - TP: {tpPrice:.2f}, SL: {slPrice:.2f}")

    def OnOrderEvent(self, orderEvent):
        """Handle order fills and OCO logic"""
        if orderEvent.Status != OrderStatus.Filled:
            return
            
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        if not order:
            return
            
        # Calculate PnL for this fill
        if self.lastTradePrice:
            pnl = 0
            if "TP_" in order.Tag or "SL_" in order.Tag:
                # This is a target or stop fill
                if "Long" in order.Tag:
                    pnl = (orderEvent.FillPrice - self.lastTradePrice) * abs(orderEvent.FillQuantity) * 100  # GC multiplier
                else:
                    pnl = (self.lastTradePrice - orderEvent.FillPrice) * abs(orderEvent.FillQuantity) * 100  # GC multiplier
                
                self.pnlToday += pnl
                
                # Log the trade
                nytime = Extensions.ConvertTo(self.Time, self.ny)
                sessionWindow = self.GetCurrentSession(nytime)
                
                tradeRecord = {
                    'DateTime': nytime.strftime('%Y-%m-%d %H:%M:%S'),
                    'Session': sessionWindow,
                    'Direction': 'LONG' if 'Long' in order.Tag else 'SHORT',
                    'Size': abs(orderEvent.FillQuantity),
                    'EntryPrice': self.lastTradePrice,
                    'ExitPrice': orderEvent.FillPrice,
                    'PnL': pnl,
                    'RunningPnL': self.pnlToday,
                    'Type': 'TP' if 'TP_' in order.Tag else 'SL'
                }
                
                self.tradeLog.append(tradeRecord)
                self.Debug(f"Trade closed: {tradeRecord}")
                
                # Cancel the opposite order (OCO logic)
                self.CancelOppositeOrder(order.Tag)
                
                # Check for alerts
                self.CheckAlerts()
        
    def GetCurrentSession(self, nytime):
        """Determine which session window we're in"""
        t = nytime.time()
        if time(3,0) <= t <= time(6,0): return "Asian"
        if time(8,20) <= t <= time(11,30): return "London"
        if time(13,0) <= t <= time(15,30): return "NY"
        return "Outside"
        
    def CancelOppositeOrder(self, filledOrderTag):
        """Cancel the opposite order in OCO pair"""
        # Extract the base tag to find the pair
        if "_TP" in filledOrderTag:
            oppositeTag = filledOrderTag.replace("_TP", "_SL")
        elif "_SL" in filledOrderTag:
            oppositeTag = filledOrderTag.replace("_SL", "_TP")
        else:
            return
            
        # Find and cancel the opposite order
        for key, ticket in list(self.openOrders.items()):
            if oppositeTag in key:
                if ticket.Status == OrderStatus.Submitted or ticket.Status == OrderStatus.PartiallyFilled:
                    ticket.Cancel()
                    self.Debug(f"Cancelled opposite order: {oppositeTag}")
                del self.openOrders[key]
                break
                
    def CheckAlerts(self):
        """Check for alert conditions"""
        if self.pnlToday >= self.dailyTarget:
            self.Debug(f"🎯 ALERT: Daily target hit! PnL: ${self.pnlToday:.2f}")
            
        if self.pnlToday <= -self.dailyMaxDD:
            self.Debug(f"🚨 ALERT: Daily drawdown limit breached! PnL: ${self.pnlToday:.2f}")
            
        if self.tradesToday >= self.tradesPerDay and self.pnlToday < self.dailyTarget:
            self.Debug(f"⚠️ ALERT: Strategy halted before target - Trades: {self.tradesToday}, PnL: ${self.pnlToday:.2f}")
    
    def OnEndOfAlgorithm(self):
        """Final summary and statistics"""
        self.Debug(f"\n=== Tesla369Gold Strategy Summary ===")
        self.Debug(f"Total Trades: {len(self.tradeLog)}")
        
        if self.tradeLog:
            wins = [t for t in self.tradeLog if t['PnL'] > 0]
            losses = [t for t in self.tradeLog if t['PnL'] <= 0]
            
            winRate = len(wins) / len(self.tradeLog) * 100 if self.tradeLog else 0
            avgWin = sum(t['PnL'] for t in wins) / len(wins) if wins else 0
            avgLoss = sum(t['PnL'] for t in losses) / len(losses) if losses else 0
            
            self.Debug(f"Win Rate: {winRate:.1f}%")
            self.Debug(f"Average Win: ${avgWin:.2f}")
            self.Debug(f"Average Loss: ${avgLoss:.2f}")
            self.Debug(f"Total PnL: ${sum(t['PnL'] for t in self.tradeLog):.2f}")
            
            # Contract size distribution
            sizes = [t['Size'] for t in self.tradeLog]
            if sizes:
                from collections import Counter
                sizeDistribution = Counter(sizes)
                self.Debug(f"Contract Size Distribution: {dict(sizeDistribution)}")
        
        self.Debug(f"=== End Summary ===")