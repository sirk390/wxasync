from wxasync import AsyncBind, WxAsyncApp
import wx
import asyncio
from asyncio.events import get_event_loop
from wx.lib.newevent import NewEvent
import time
from collections import deque
import json
from multiprocessing import Process
import multiprocessing
import itertools

TestEvent, EVT_TEST_EVENT = NewEvent()

class WxCallAfterThroughputTest(wx.Frame):
    def __init__(self, parent=None):
        super(WxCallAfterThroughputTest, self).__init__(parent)
        self.latency_sum = 0
        self.wx_events_pending = 1 # the first one is sent in constructor
        self.total_events_sent = 0
        self.total_to_send = 100000
        self.tstart = time.time()
        wx.CallAfter(self.loop_func, self.tstart)
        
    def loop_func(self, t1):
        tnow = time.time()
        self.latency_sum += (tnow - t1)
        #self.wx_events_received.append(event.t1)
        self.wx_events_pending -= 1
        
        if self.total_events_sent == self.total_to_send and self.wx_events_pending == 0:
            self.tend = time.time()
            self.duration = self.tend - self.tstart
            self.Destroy()

        if self.total_events_sent != self.total_to_send:
            while self.wx_events_pending < 1000:
                wx.CallAfter(self.loop_func, tnow)
                self.total_events_sent += 1
                self.wx_events_pending += 1
                
    def Destroy(self):
        super(WxCallAfterThroughputTest, self).Destroy()

    def results(self):
        avg_latency_ms = (self.latency_sum / self.total_to_send) * 1000
        return {
                "Throughput (msg/s)": int(self.total_to_send/self.duration),
                "Avg Latency (ms)": int(avg_latency_ms),
                "TotalSent": self.total_to_send,
                "Duration": "%.2fs" % (self.duration)}
    @staticmethod
    def run():  
        app = wx.App()
        frame = WxCallAfterThroughputTest()
        app.MainLoop()
        return (json.dumps(frame.results()))

class WxMessageThroughputTest(wx.Frame):
    def __init__(self, parent=None):
        super(WxMessageThroughputTest, self).__init__(parent)
        self.latency_sum = 0
        self.wx_events_pending = 1 # the first one is sent in constructor
        self.total_events_sent = 0
        self.total_to_send = 100000
        self.tstart = time.time()
        self.Bind(EVT_TEST_EVENT, self.loop_func)
        wx.PostEvent(self, TestEvent(t1=time.time()))
        
    def loop_func(self, event):
        tnow = time.time()
        self.latency_sum += (tnow - event.t1)
        #self.wx_events_received.append(event.t1)
        self.wx_events_pending -= 1
        
        if self.total_events_sent == self.total_to_send and self.wx_events_pending == 0:
            self.tend = time.time()
            self.duration = self.tend - self.tstart
            self.Destroy()

        if self.total_events_sent != self.total_to_send:
            while self.wx_events_pending < 1000:
                wx.PostEvent(self, TestEvent(t1=tnow))
                self.total_events_sent += 1
                self.wx_events_pending += 1
                
    def Destroy(self):
        super(WxMessageThroughputTest, self).Destroy()

    def results(self):
        avg_latency_ms = (self.latency_sum / self.total_to_send) * 1000
        return {
                "Throughput(msg/s)": int(self.total_to_send/self.duration),
                "AvgLatency(ms)": int(avg_latency_ms),
                "TotalSent": self.total_to_send,
                "Duration": "%.2fs" % (self.duration)}
    @staticmethod
    def run():  
        app = wx.App()
        frame = WxMessageThroughputTest()
        app.MainLoop()
        return frame.results()
        #print ("wx.App (wx.PostEvent)", frame.results())


class WxAsyncAsyncIOLatencyTest(wx.Frame):
    """ While using a WxAsyncApp, send only a few messages as 'loop.call_later' (not enough to queue up) through the asyncio event loop and check difference between expected time, and arrived time.
        If the GUI Dispatch blocks the asyncio event loop, you will see it here ().
    """
    def __init__(self, parent=None, loop=None):
        super(WxAsyncAsyncIOLatencyTest, self).__init__(parent)
        self.loop = loop
        self.delay_ms = 100 
        self.delay_s = self.delay_ms / 1000
        self.aio_latency_sum = 0
        self.aio_events_pending = 1 # the first one is sent in constructor
        self.total_events_sent = 0
        self.total_to_send = 100
        self.total_aio_sent = 0
        self.tstart = time.time()
        self.loop.call_soon(self.aio_loop_func, self.tstart) 
        
    def aio_loop_func(self, t1):
        tnow = time.time()
        self.aio_latency_sum += (tnow - t1)
        self.aio_events_pending -= 1
        
        if self.total_events_sent == self.total_to_send and self.aio_events_pending == 0:
            self.tend = time.time()
            self.duration = self.tend - self.tstart
            self.Destroy()

        if self.total_events_sent != self.total_to_send:
            t = tnow + self.delay_s
            self.loop.call_later(self.delay_s, lambda: self.aio_loop_func(tnow+self.delay_s)) 
            self.total_events_sent += 1
            self.aio_events_pending += 1
            self.total_aio_sent += 1
                
    def results(self):
        avg_aio_latency_ms = (self.aio_latency_sum / self.total_aio_sent) * 1000
        return {
                "AvgLatency(ms)": max(int(avg_aio_latency_ms), 0),
                "TotalSent": self.total_aio_sent,
                "Duration": "%.2fs" % (self.duration),
                "MsgInterval(ms)" : self.delay_ms}
    @staticmethod
    def run():  
        loop = get_event_loop()
        app = WxAsyncApp()
        frame = WxAsyncAsyncIOLatencyTest(loop=loop)
        loop.run_until_complete(app.MainLoop())
        return frame.results()



class WxAsyncAppMessageThroughputTest(wx.Frame):
    def __init__(self, parent=None):
        super(WxAsyncAppMessageThroughputTest, self).__init__(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)
        button1 =  wx.Button(self, label="Submit")
        vbox.Add(button1, 1, wx.EXPAND|wx.ALL)
        self.SetSizer(vbox)
        self.Layout()
        AsyncBind(EVT_TEST_EVENT, self.async_callback, self)
        wx.PostEvent(self, TestEvent(t1=time.time()))

        self.latency_sum = 0
        self.wx_events_pending = 1 # the first one is sent in constructor
        self.total_events_sent = 0
        self.total_to_send = 100000
        self.tstart = time.time()
        
    async def async_callback(self, event):
        tnow = time.time()
        self.latency_sum += (tnow - event.t1)
        #self.wx_events_received.append(event.t1)
        self.wx_events_pending -= 1
        
        if self.total_events_sent == self.total_to_send and self.wx_events_pending == 0:
            self.tend = time.time()
            self.duration = self.tend-self.tstart
            self.Destroy()

        if self.total_events_sent != self.total_to_send:
            while self.wx_events_pending < 1000:
                wx.PostEvent(self, TestEvent(t1=tnow))
                self.total_events_sent += 1
                self.wx_events_pending += 1
                
    def Destroy(self):
        super(WxAsyncAppMessageThroughputTest, self).Destroy()

    def results(self):
        avg_latency_ms = (self.latency_sum / self.total_to_send) * 1000
        return {
                "Throughput(msg/s)": int(self.total_to_send/self.duration),
                "AvgLatency(ms)": int(avg_latency_ms),
                "TotalSent": self.total_to_send,
                "Duration": "%.2fs" % (self.duration)}
    @staticmethod
    def run():  
        app = WxAsyncApp()
        frame = WxAsyncAppMessageThroughputTest()
        loop = get_event_loop()
        loop.run_until_complete(app.MainLoop())
        #app.__del__()
        return frame.results()


class WxAsyncAppCombinedThroughputTest(wx.Frame):
    """ Send the maxiumun number of events both through the asyncio event loop and through
       the wx Event loop, using both "loop.call_soon" and "wx.PostEvent", measure throughput and latency"""
    def __init__(self,  loop=None):
        super(WxAsyncAppCombinedThroughputTest, self).__init__()
        self.loop = loop
        AsyncBind(EVT_TEST_EVENT, self.wx_loop_func, self)

        self.wx_latency_sum = 0
        self.aio_latency_sum = 0
        self.wx_events_pending = 1 # the first one is sent in constructor
        self.aio_events_pending = 1 # the first one is sent in constructor
        self.total_events_sent = 0
        self.total_to_send = 200000
        self.total_wx_sent = 0
        self.total_aio_sent = 0
        self.tstart = time.time()
        wx.PostEvent(self, TestEvent(t1=self.tstart))
        self.loop.call_soon(self.aio_loop_func, self.tstart) #, *args
        
    async def wx_loop_func(self, event):
        tnow = time.time()
        self.wx_latency_sum += (tnow - event.t1)
        self.wx_events_pending -= 1
        
        if self.total_events_sent == self.total_to_send and self.aio_events_pending == 0  and self.wx_events_pending == 0:
            self.tend = time.time()
            self.duration = self.tend-self.tstart
            self.Destroy()

        if self.total_events_sent != self.total_to_send:
            while self.wx_events_pending < 1000:
                wx.PostEvent(self, TestEvent(t1=tnow))
                self.total_events_sent += 1
                self.total_wx_sent += 1
                self.wx_events_pending += 1

    def aio_loop_func(self, t1):
        tnow = time.time()
        self.aio_latency_sum += (tnow - t1)
        self.aio_events_pending -= 1
        
        if self.total_events_sent == self.total_to_send and self.aio_events_pending == 0  and self.wx_events_pending == 0:
            self.tend = time.time()
            self.duration = self.tend - self.tstart
            self.Destroy()

        if self.total_events_sent != self.total_to_send:
            while self.aio_events_pending < 1000:
                self.loop.call_soon(self.aio_loop_func, tnow) #, *args
                self.total_events_sent += 1
                self.aio_events_pending += 1
                self.total_aio_sent += 1
                
    def results(self):
        avg_aio_latency_ms = (self.aio_latency_sum / self.total_aio_sent) * 1000
        avg_wx_latency_ms = (self.wx_latency_sum / self.total_wx_sent) * 1000
        return {
                "wxThroughput(msg/s)": int(self.total_wx_sent/self.duration),
                "wxAvgLatency(ms)": int(avg_wx_latency_ms),
                "wxTotalSent": self.total_wx_sent,
                "aioThroughput(msg/s)": int(self.total_aio_sent/self.duration),
                "aioAvgLatency(ms)": int(avg_aio_latency_ms),
                "aioTotalSent": self.total_aio_sent,
                "Duration": "%.2fs" % (self.duration),
                "MsgInterval(ms)" : "none"}
        
    @staticmethod
    def run():  
        loop = get_event_loop()
        app = WxAsyncApp()
        frame = WxAsyncAppCombinedThroughputTest(loop=loop)
        loop.run_until_complete(app.MainLoop())
        return frame.results()
        #print ("wxAsyncApp (wx.PostEvent+loop.call_soon)", frame.results())

class WxAsyncAppCombinedLatencyTest(wx.Frame):
    """ Send few events (not enough to queue up the event loop) both through the asyncio event loop and through
        the wx Event loop, using both "loop.call_soon" and "wx.PostEvent", and measure latency"""
    def __init__(self, parent=None, loop=None):
        super(WxAsyncAppCombinedLatencyTest, self).__init__(parent)
        self.loop = loop
        AsyncBind(EVT_TEST_EVENT, self.wx_loop_func, self)
        self.delay_ms = 10 
        self.delay_s = self.delay_ms / 1000
        self.wx_latency_sum = 0
        self.aio_latency_sum = 0
        self.wx_events_pending = 1 # the first one is sent in constructor
        self.aio_events_pending = 1 # the first one is sent in constructor
        self.total_events_sent = 0
        self.total_to_send = 1000
        self.total_wx_sent = 0
        self.total_aio_sent = 0
        self.tstart = time.time()
        wx.PostEvent(self, TestEvent(t1=self.tstart))
        self.loop.call_soon(self.aio_loop_func, self.tstart) #, *args
        
    async def wx_loop_func(self, event):
        tnow = time.time()
        self.wx_latency_sum += (tnow - event.t1)
        #print (tnow - event.t1, tnow, event.t1)
        #self.wx_events_received.append(event.t1)
        self.wx_events_pending -= 1
        
        if self.total_events_sent == self.total_to_send and self.wx_events_pending == 0:
            self.tend = time.time()
            self.duration = self.tend-self.tstart
            self.Destroy()

        if self.total_events_sent != self.total_to_send:
            wx.CallLater(self.delay_ms, lambda : wx.PostEvent(self, TestEvent(t1=tnow+self.delay_s)))
            self.total_events_sent += 1
            self.total_wx_sent += 1
            self.wx_events_pending += 1

    def aio_loop_func(self, t1):
        tnow = time.time()
        self.aio_latency_sum += (tnow - t1)
        self.aio_events_pending -= 1
        
        if self.total_events_sent == self.total_to_send and self.aio_events_pending == 0:
            self.tend = time.time()
            self.duration = self.tend - self.tstart
            self.Destroy()

        if self.total_events_sent != self.total_to_send:
            self.loop.call_later(self.delay_s, lambda: self.aio_loop_func(tnow+self.delay_s)) 
            self.total_events_sent += 1
            self.aio_events_pending += 1
            self.total_aio_sent += 1
                
    def Destroy(self):
        super(WxAsyncAppCombinedLatencyTest, self).Destroy()

    def results(self):
        avg_aio_latency_ms = (self.aio_latency_sum / self.total_aio_sent) * 1000
        avg_wx_latency_ms = (self.wx_latency_sum / self.total_wx_sent) * 1000
        return {
                "wxAvgLatency(ms)": max(int(avg_wx_latency_ms), 0), # can be negative, due to "loop.call_later" calling a few ms earlier than expected
                "wxTotalSent": self.total_wx_sent,
                "aioAvgLatency(ms)": max(int(avg_aio_latency_ms), 0), # can be negative, due to "loop.call_later" calling a few ms earlier than expected
                "aioTotalSent": self.total_aio_sent,
                "Duration": "%.2fs" % (self.duration),
                "MsgInterval(ms)" : self.delay_ms}
    @staticmethod
    def run():  
        loop = get_event_loop()
        app = WxAsyncApp()
        frame = WxAsyncAppCombinedLatencyTest(loop=loop)
        loop.run_until_complete(app.MainLoop())
        return frame.results()


class AioThroughputTest():
    """ Send the maxiumun number of events through the asyncio event loop using "loop.call_soon" and measure throughput and latency"""
    def __init__(self, loop):
        self.loop = loop
        self.latency_sum  = 0
        self.events_pending = 1 # the first one is sent in constructor
        self.total_events_sent = 0
        self.total_to_send = 200000
        self.tstart = time.time()
        self.loop.call_soon(self.loop_func, self.tstart)
        
    def loop_func(self, t1):
        tnow = time.time()
        self.latency_sum += (tnow - t1)
        self.events_pending -= 1
        
        if self.total_events_sent == self.total_to_send and self.events_pending == 0:
            self.tend = time.time()
            self.duration = self.tend - self.tstart
            self.loop.stop()

        if self.total_events_sent != self.total_to_send:
            while self.events_pending < 10000:
                self.loop.call_soon(self.loop_func, tnow) #, *args
                self.total_events_sent += 1
                self.events_pending += 1
                
    def results(self):
        avg_latency_ms = (self.latency_sum / self.total_to_send) * 1000
        return {
                "Throughput(msg/s)": int(self.total_to_send/self.duration),
                "AvgLatency(ms)": int(avg_latency_ms),
                "TotalSent": self.total_to_send,
                "Duration": "%.2fs" % (self.duration)}
    @staticmethod
    def run():  
        loop = get_event_loop()
        test = AioThroughputTest(loop)
        loop.run_forever()
        return test.results()

def call_and_queue_result(func, queue):
    queue.put(func())
 
def run_in_bg_process(func):
    queue = multiprocessing.Queue()
    p = Process(target=call_and_queue_result, args=(func, queue))
    p.start()
    p.join()
    return queue.get()

def flatten_list(lst_of_lst):
    return  list(itertools.chain.from_iterable(lst_of_lst))

def format_table(data):
    lens = [[len(str(e)) for e in row] for row in data]
    collens = [max(col) for col in zip(*lens)]
    row_strs = []
    for row in data:
        row_strs.append(" ".join([str(elm).rjust(l) if i else str(elm).ljust(l) for i, (l, elm) in enumerate(zip(collens, row))]))
    return "\n".join(row_strs)

def format_stat_results(results):
    columns = sorted(set(flatten_list([statlist.keys() for statlist in results.values()])))
    table = [[""] + columns]
    for key, stats in results.items():
        table.append([key] + [stats.get(c, "") for c in columns])
    return (format_table(table))
    
if __name__ == '__main__':
    results = {}
    results = {}
    results["wxAsyncApp (asyncio latency)"] = WxAsyncAsyncIOLatencyTest.run()
    
    results["wx.App (wx.PostEvent)"] = WxMessageThroughputTest.run()
    results["asyncio (loop.call_soon)"] = AioThroughputTest.run()
    results["wxAsyncApp (wx.PostEvent)"] = WxAsyncAppMessageThroughputTest.run()
    
    print ("Individual Tests: ")
    print (format_stat_results(results))
    
    combined_results = {}
    combined_results["wxAsyncApp (wx.PostEvent+loop.call_soon) throughput"] = WxAsyncAppCombinedThroughputTest.run()
    combined_results["wxAsyncApp (wx.PostEvent+loop.call_soon) latency"] = WxAsyncAppCombinedLatencyTest.run()
    print ("\nCombined Tests, using wx and asyncio at the same time:\n")
    print (format_stat_results(combined_results))


"""
Windows (Core I7-7700K 4.2Ghz):
        
    Individual Tests: 
                                 AvgLatency(ms) Duration MsgInterval(ms) Throughput(msg/s) TotalSent
    wxAsyncApp (asyncio latency)              0    9.37s             100                         100
    wx.App (wx.PostEvent)                    11    1.13s                             88561    100000
    asyncio (loop.call_soon)                 17    0.35s                            571325    200000
    wxAsyncApp (wx.PostEvent)                19    1.99s                             50279    100000
    
    Combined Tests, using wx and asyncio at the same time:
    
                                                        Duration MsgInterval(ms) aioAvgLatency(ms) aioThroughput(msg/s) aioTotalSent wxAvgLatency(ms) wxThroughput(msg/s) wxTotalSent
    wxAsyncApp (wx.PostEvent+loop.call_soon) throughput    1.79s            none                13                74763       134000               27               36823       66000
    wxAsyncApp (wx.PostEvent+loop.call_soon) latency       1.84s              10                -7                               882                0                             118
    
On MacOS (VM of Core I7-7700K 4.2Ghz):
        
    Individual Tests: 
                                 AvgLatency(ms) Duration MsgInterval(ms) Throughput(msg/s) TotalSent
    wxAsyncApp (asyncio latency)              0   10.08s             100                         100
    wx.App (wx.PostEvent)                    16    1.62s                             61677    100000
    asyncio (loop.call_soon)                 29    0.60s                            332176    200000
    wxAsyncApp (wx.PostEvent)                25    2.55s                             39244    100000
    
    Combined Tests, using wx and asyncio at the same time:
    
                                                        Duration MsgInterval(ms) aioAvgLatency(ms) aioThroughput(msg/s) aioTotalSent wxAvgLatency(ms) wxThroughput(msg/s) wxTotalSent
    wxAsyncApp (wx.PostEvent+loop.call_soon) throughput    1.69s            none                11                88970       150000               33               29656       50000
    wxAsyncApp (wx.PostEvent+loop.call_soon) latency       6.87s              10                 0                               629                8                             371
       
"""