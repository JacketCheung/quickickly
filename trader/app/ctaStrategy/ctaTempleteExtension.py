# encoding: UTF-8

import numpy as np
from vnpy.trader.vtObject import VtBarData,VtTradeData,VtOrderData
from vnpy.trader.vtConstant import *
from vnpy.trader.language.chinese.constant import  *
from .ctaBase import *


duo = 100
duoping = 50
kong = 200
kongping = 250


class MyTemplate(object):
    def sellFok(self, price, volume, stop=False):
        '''不成交就撤单'''
        return self.sendOrder(CTAORDER_SELLFOK, price, volume, stop)
    # ----------------------------------------------------------------------
    def coverFok(self, price, volume, stop=False):
        """买平"""
        return self.sendOrder(CTAORDER_COVERFOK, price, volume, stop)
    # ----------------------------------------------------------------------
class orderEnigine(object):
    def __init__(self,buy,sell,short,cover,sellFok,coverFok):
        self.volume = 1
        self.posdetail = None
        self.buy = buy
        self.sell = sell
        self.short = short
        self.cover = cover
        self.sellFok = sellFok
        self.coverFok = coverFok


        self.orderSet = []
        self.activeOrderSet = []
        self.buyOrder = None
        self.sellOrder = None
        self.shortOrder = None
        self.coverOrder = None
    def signal(self,fangxiang,price):
        if fangxiang == duo:
            self.orderBuy(price,self.volume)
        if fangxiang == kong:
            self.orderShort(price,self.volume)
        if fangxiang == duoping:
            self.ordeSell(price,self.volume)
        if fangxiang == kongping:
            self.orderCover(price,self.volume)
    def orderBuy(self, price, volume = 1, stop=False):
            if self.buyOrder is None :
                print 'buyorder'
                self.buyOrder = 0
                self.buy(price,volume,stop)

    def orderSell(self, price, volume=1, stop=False):
        if self.sellOrder is None:
            self.sellOrder = 0
            self.sell(price, volume, stop)

    def orderShort(self, price, volume=1, stop=False):
        if self.shortOrder is None:
            self.shortOrder = 0
            self.short(price, volume, stop)

    def orderCover(self, price, volume=1, stop=False):
        if self.coverOrder is None:
            self.coverOrder = 0
            self.cover(price, volume, stop)
    def onOrder(self,order):
        if order.status == STATUS_NOTTRADED:
            if order.offset == OFFSET_OPEN and order.direction == DIRECTION_LONG:
                self.buyOrder = order
            elif order.offset == OFFSET_OPEN and order.direction == DIRECTION_SHORT:
                self.shortOrder = order
            elif  (order.offset == OFFSET_CLOSE or order.offset == OFFSET_CLOSETODAY or order.offset == OFFSET_CLOSEYESTERDAY) and order.direction == DIRECTION_LONG:
                self.coverOrder = order
            elif ( order.offset == OFFSET_CLOSE or order.offset == OFFSET_CLOSETODAY or order.offset == OFFSET_CLOSEYESTERDAY) and order.direction == DIRECTION_SHORT:
                self.sellOrder = order

    class MyBarGenerator(object):
    def updateTick(self, tick):
        """TICK更新"""
        newMinute = False  # 默认不是新的一分钟
        if tick.datetime.minute == 15 and tick.datetime.hour == 10:
            tick.datetime = tick.datetime.replace(minute=14,second=0,microsecond = 700)
        if tick.datetime.minute == 30 and tick.datetime.hour == 11:
            tick.datetime = tick.datetime.replace(minute=29,second=59,microsecond = 700)
        # 尚未创建对象
        if not self.bar:
            self.bar = VtBarData()
            newMinute = True
        # 新的一分钟
        elif self.bar.datetime.minute != tick.datetime.minute:
            # 生成上一分钟K线的时间戳

            self.bar.datetime = self.bar.datetime.replace(second=0, microsecond=0)  # 将秒和微秒设为0
            self.bar.date = self.bar.datetime.strftime('%Y%m%d')
            self.bar.time = self.bar.datetime.strftime('%H:%M:%S.%f')

            # 推送已经结束的上一分钟K线
            self.onBar(self.bar)

            # 创建新的K线对象
            self.bar = VtBarData()
            newMinute = True

        # 初始化新一分钟的K线数据
        if newMinute:
            self.bar.vtSymbol = tick.vtSymbol
            self.bar.symbol = tick.symbol
            self.bar.exchange = tick.exchange

            self.bar.open = tick.lastPrice
            self.bar.high = tick.lastPrice
            self.bar.low = tick.lastPrice
        # 累加更新老一分钟的K线数据
        else:
            self.bar.high = max(self.bar.high, tick.lastPrice)
            self.bar.low = min(self.bar.low, tick.lastPrice)

        # 通用更新部分
        self.bar.close = tick.lastPrice
        self.bar.datetime = tick.datetime
        self.bar.openInterest = tick.openInterest

        if self.lastTick:
            self.bar.volume += (tick.volume - self.lastTick.volume)  # 当前K线内的成交量

        # 缓存Tick
        self.lastTick = tick


class MyArray(object):
    def __init__(self, lastshort= 0,lastlong = 0,lastdea = 0,size=100):
        """Constructor"""
        self.count = 0  # 缓存计数
        self.size = size  # 缓存大小
        self.inited = False  # True if count>=size

        self.openArray = np.zeros(size)  # OHLC
        self.highArray = np.zeros(size)
        self.lowArray = np.zeros(size)
        self.closeArray = np.zeros(size)
        self.volumeArray = np.zeros(size)

        self.langshu = 0

        self.datetime = None

        self.tick = None

        self.diff = 0
        self.dea = 0
        self.short = 0
        self.long = 0
        self.macd = 0
        self.mj = 0

        self.lastdiff = 0
        self.lastdea = lastdea
        self.lastshort = lastshort
        self.lastlong = lastlong
        self.lastmacd = 0
        self.lastmj = 0

        self.redWaveCount = 0
        self.greendWaveCount = 0
        self.lastRedWaveCount = 0
        self.lastGreenWaveCount = 0
        self.waveCounts = 0

    def inred(self):
        return self.macd > 0
    def updateBar(self, bar):
        """更新K线"""
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True

        self.openArray[0:self.size - 1] = self.openArray[1:self.size]
        self.highArray[0:self.size - 1] = self.highArray[1:self.size]
        self.lowArray[0:self.size - 1] = self.lowArray[1:self.size]
        self.closeArray[0:self.size - 1] = self.closeArray[1:self.size]
        self.volumeArray[0:self.size - 1] = self.volumeArray[1:self.size]

        self.openArray[-1] = bar.open
        self.highArray[-1] = bar.high
        self.lowArray[-1] = bar.low
        self.closeArray[-1] = bar.close
        self.volumeArray[-1] = bar.volume

        self.caculateMACD(bar.close)
        self.datetime = bar.datetime

        self.countWave()
    def caculateEMA(self, price, lastEMA, alpha=2.0 / 13.0):
        return alpha * price + (1 - alpha) * lastEMA

    def updateTick(self, tick):
        self.caculateMACD(tick.lastPrice)
        self.close[-1] = tick.lastPrice
        self.tick = tick
    def caculateMACD(self, lastPrice):
        if self.lastshort == 0 and self.lastlong == 0:
            self.short = lastPrice
            self.long = lastPrice
        else:
            self.short = self.caculateEMA(lastPrice, self.lastshort)
            self.long = self.caculateEMA(lastPrice, self.lastlong, 2.0 / 27.0)
        self.diff = self.short - self.long
        self.dea = self.caculateEMA(self.diff, self.lastdea, 0.2)
        self.macd = 2 * (self.diff - self.dea)
        self.mj = self.macd - self.lastmacd

    def newprice(self, lastPrice):
        self.caculateMACD(lastPrice)

    def endBar(self):
        self.lastshort = self.short
        self.lastdea = self.dea
        self.lastdiff = self.diff
        self.lastlong = self.long
        self.lastmacd = self.macd
        self.lastmj = self.mj

    # print('endbar,and short is ',self.short,'diffis',self.diff,'lastshort is',self.lastshort)
    def dj(self):
        return self.diff - self.lastdiff

    def countWave(self):
        if self.macd >0 and self.lastmacd < 0:
            self.lastRedWaveCount = self.redWaveCount
            self.redWaveCount = 1
            self.waveCounts += 1
        elif self.macd < 0 and self.lastmacd > 0:
            self.lastGreenWaveCount = self.greendWaveCount
            self.greendWaveCount = 1
            self.waveCounts += 1
        elif self.macd <0 and self.lastmacd < 0:
            self.greendWaveCount += 1
        elif self.macd >0 and self.lastmacd >0:
            self.redWaveCount += 1