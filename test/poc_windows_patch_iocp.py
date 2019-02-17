"""
This is a proof of concept to patch the ProactorEventLoop under windows and use
MsgWaitForMultipleObjectsEx instead of GetQueuedCompletionStatus.
This should improve latency and performances for GUI messages  

Conclusion: It works but it is actually slower.
"""

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
import ctypes
    
from asyncio.events import get_event_loop
import asyncio
import wx
import warnings
from asyncio.futures import CancelledError
from collections import defaultdict
import platform


TestEvent, EVT_TEST_EVENT = NewEvent()


IS_MAC = platform.system() == "Darwin"

class WxAsyncApp(wx.App):
    def __init__(self, warn_on_cancel_callback=False, loop=None):
        super(WxAsyncApp, self).__init__()
        self.loop = loop or get_event_loop()
        self.BoundObjects = {}
        self.RunningTasks = defaultdict(set)
        self.SetExitOnFrameDelete(True)
        self.exiting = asyncio.Event()
        self.warn_on_cancel_callback = warn_on_cancel_callback
        self.evtloop = wx.GUIEventLoop()
        self.activator = wx.EventLoopActivator(self.evtloop)
        self.activator.__enter__()
    
    def DispatchMessages(self):
        c = 0
        while self.evtloop.Pending():
            c += 1
            self.evtloop.Dispatch()
        print ("d", c)
        self.evtloop.ProcessIdle()
    
    async def MainLoop(self):
        await self.exiting.wait()

    def ExitMainLoop(self):
        self.exiting.set()

    def AsyncBind(self, event_binder, async_callback, object):
        """Bind a coroutine to a wx Event. Note that when wx object is destroyed, any coroutine still running will be cancelled automatically.
        """ 
        if object not in self.BoundObjects:
            self.BoundObjects[object] = defaultdict(list)
            object.Bind(wx.EVT_WINDOW_DESTROY, lambda event: self.OnDestroy(event, object))
        self.BoundObjects[object][event_binder.typeId].append(async_callback)
        object.Bind(event_binder, lambda event: self.OnEvent(event, object, event_binder.typeId))

    def StartCoroutine(self, coroutine, obj):
        """Start and attach a coroutine to a wx object. When object is destroyed, the coroutine will be cancelled automatically.
        """ 
        if asyncio.iscoroutinefunction(coroutine):
            coroutine = coroutine()
        task = self.loop.create_task(coroutine)
        task.add_done_callback(self.OnTaskCompleted)
        task.obj = obj
        self.RunningTasks[obj].add(task)

    def OnEvent(self, event, obj, type):
        for asyncallback in self.BoundObjects[obj][type]:
            self.StartCoroutine(asyncallback(event.Clone()), obj)

    def OnTaskCompleted(self, task):
        try:
            # This gathers completed callbacks (otherwise asyncio will show a warning)
            # Note: exceptions from callbacks raise here
            # we just let them bubble as there is nothing we can do at this point
            _res = task.result()
        except CancelledError:
            # Cancelled because the window was destroyed, this is normal so ignore it
            pass
        self.RunningTasks[task.obj].remove(task)

    def OnDestroy(self, event, obj):
        # Cancel async callbacks
        for task in self.RunningTasks[obj]:
            if not task.done():
                task.cancel()
                if self.warn_on_cancel_callback:
                    warnings.warn("cancelling callback" + str(obj) + str(task))
        del self.BoundObjects[obj]


def AsyncBind(event, async_callback, obj):
    app = wx.App.Get()
    if type(app) is not WxAsyncApp:
        raise Exception("Create a 'WxAsyncApp' first")
    app.AsyncBind(event, async_callback, obj)


def StartCoroutine(coroutine, obj):
    app = wx.App.Get()
    if type(app) is not WxAsyncApp:
        raise Exception("Create a 'WxAsyncApp' first")
    app.StartCoroutine(coroutine, obj)



class TestFrame(wx.Frame):
    def __init__(self, parent=None):
        super(TestFrame, self).__init__(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)
        button1 =  wx.Button(self, label="Submit")
        self.edit =  wx.StaticText(self, style=wx.ALIGN_CENTRE_HORIZONTAL|wx.ST_NO_AUTORESIZE)
        vbox.Add(button1, 2, wx.EXPAND|wx.ALL)
        vbox.AddStretchSpacer(1)
        vbox.Add(self.edit, 1, wx.EXPAND|wx.ALL)
        self.SetSizer(vbox)
        self.Layout()
        
        AsyncBind(wx.EVT_BUTTON, self.async_callback, button1)
        AsyncBind(wx.EVT_BUTTON, self.async_callback2, button1)
        StartCoroutine(self.async_job, self)
        
    async def async_callback(self, event):
        self.edit.SetLabel("Button clicked")
        await asyncio.sleep(1)
        self.edit.SetLabel("Working")
        await asyncio.sleep(1)
        self.edit.SetLabel("Completed")

    async def async_callback2(self, event):
        self.edit.SetLabel("Button clicked 2")
        await asyncio.sleep(0.5)
        self.edit.SetLabel("Working 2")
        await asyncio.sleep(1.2)
        self.edit.SetLabel("Completed 2")

    async def async_job(self):
        t0 = 0
        while True:
            t = time.time()
            print ("hello", t - t0)
            t0 = t
            await asyncio.sleep(0.2)

    def callback(self, event):
        print ("huhhiu")


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
        self.total_to_send = 2000000
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

QS_ALLINPUT = 0x04FF
QS_ALLPOSTMESSAGE = 0x0100
MWMO_ALERTABLE = 0x0002


WAIT_TIMEOUT = 258
WAIT_IO_COMPLETION = 0x000000C0

if __name__ == '__main__':
    import _overlapped

    orig = _overlapped.GetQueuedCompletionStatus 
    def GetQueuedCompletionStatus(iocp, ms):
        handles = ctypes.c_int(iocp)
        result = ctypes.windll.user32.MsgWaitForMultipleObjectsEx(1, ctypes.byref(handles), 1, QS_ALLINPUT|QS_ALLPOSTMESSAGE, MWMO_ALERTABLE)
        if result == WAIT_IO_COMPLETION:
            return orig (iocp, ms)
        elif result == WAIT_TIMEOUT:
            return
        app = wx.App.Get()
        if type(app) is not WxAsyncApp:
            raise Exception("Create a 'WxAsyncApp' first")
        app.DispatchMessages()
        
    _overlapped.GetQueuedCompletionStatus = GetQueuedCompletionStatus
    loop = asyncio.ProactorEventLoop()
    
    asyncio.set_event_loop(loop)
    
      
    app = WxAsyncApp()

    '''frame = TestFrame()
    frame.Show()
    app.SetTopWindow(frame)
    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
    '''
    print (WxMessageThroughputTest.run())