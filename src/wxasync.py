from asyncio.events import get_event_loop
import asyncio
import wx
import warnings
from asyncio.futures import CancelledError
from collections import defaultdict
import platform



IS_MAC = platform.system() == "Darwin"

class WxAsyncApp(wx.App):
    def __init__(self, warn_on_cancel_callback=False, loop=None):
        super(WxAsyncApp, self).__init__()
        self.loop = loop or get_event_loop()
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
                    evtloop.DispatchTimeout(0)
                else:
                    while evtloop.Pending():
                        evtloop.Dispatch()
                await asyncio.sleep(0.005)
                evtloop.ProcessIdle()

    def ExitMainLoop(self):
        self.exiting = True

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



