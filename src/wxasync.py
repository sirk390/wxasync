from asyncio.events import get_event_loop
import asyncio
import wx
import warnings
from asyncio.futures import CancelledError
from collections import defaultdict
import platform


GlobalWxAsyncApp = None


IS_MAC = platform.system() == "Darwin"  


class WxAsyncApp(wx.App):
    def __init__(self, warn_on_cancel_callback=False, loop=None):
        global GlobalWxAsyncApp
        super(WxAsyncApp, self).__init__()
        self.loop = loop or get_event_loop()
        GlobalWxAsyncApp = self
        self.BoundObjects = {}
        self.RunningTasks = defaultdict(set)
        self.SetExitOnFrameDelete(True)
        self.exiting = False
        self.warn_on_cancel_callback = warn_on_cancel_callback
        
    async def MainLoop(self):
        evtloop = wx.GUIEventLoop()
        with wx.EventLoopActivator(evtloop):
            while not self.exiting:
                if IS_MAC:
                    # evtloop.Pending() just returns True on MacOs
                    evtloop.Dispatch()
                else:
                    while evtloop.Pending():
                        evtloop.Dispatch()
                await asyncio.sleep(0.005)
                evtloop.ProcessIdle()
                
    def ExitMainLoop(self):
        self.exiting = True

    def AsyncBind(self, event_binder, async_callback, object):
        if object not in self.BoundObjects:
            self.BoundObjects[object] = {}
            object.Bind(wx.EVT_WINDOW_DESTROY, lambda event: self.OnDestroy(event, object))
        self.BoundObjects[object][event_binder.typeId] = async_callback
        object.Bind(event_binder, lambda event: self.OnEvent(event, object, event_binder.typeId))
        
    def OnEvent(self, event, obj, type):
        asyncallback = self.BoundObjects[obj][type]
        event_task = self.loop.create_task(asyncallback(event.Clone()))
        event_task.add_done_callback(self.OnEventCompleted)
        event_task.obj = obj
        self.RunningTasks[obj].add(event_task)
    
    def OnEventCompleted(self, event_task):
        try:
            # This gathers completed callbacks (otherwise asyncio will show a warning)
            # Note: exceptions from callbacks raise here
            # we just let them bubble as there is nothing we can do at this point
            _res = event_task.result() 
        except CancelledError:
            pass
        self.RunningTasks[event_task.obj].remove(event_task)
    
    def OnDestroy(self, event, obj):
        # Cancel async callbacks
        for task in self.RunningTasks[obj]:
            task.cancel()
            if self.warn_on_cancel_callback:
                warnings.warn("cancelling callback" + str(obj) + str(task))
        del self.RunningTasks[obj]
        del self.BoundObjects[obj]


def AsyncBind(event, async_callback, obj):
    if GlobalWxAsyncApp is None:
        raise Exception("Create a 'WxAsyncApp' first")
    GlobalWxAsyncApp.AsyncBind(event, async_callback, obj)
    
    
