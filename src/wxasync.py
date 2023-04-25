from asyncio.events import get_event_loop
import asyncio
import wx
import wx.html
import warnings
from asyncio import CancelledError
from collections import defaultdict
import platform
from asyncio.locks import Event
from asyncio.coroutines import iscoroutinefunction
import asyncio


IS_MAC = platform.system() == "Darwin"

class WxAsyncApp(wx.App):
    def __init__(self, warn_on_cancel_callback=False, sleep_duration=0.02, **kwargs):
        self.BoundObjects = {}
        self.RunningTasks = defaultdict(set)
        self.exiting = False
        self.ui_idle = True
        self.sleep_duration = sleep_duration
        self.warn_on_cancel_callback = warn_on_cancel_callback
        super(WxAsyncApp, self).__init__(**kwargs)
        self.SetExitOnFrameDelete(True)

    async def MainLoop(self):
        # inspired by https://github.com/wxWidgets/Phoenix/blob/master/samples/mainloop/mainloop.py
        evtloop = wx.GUIEventLoop()
        with wx.EventLoopActivator(evtloop):
            while not self.exiting:
                if IS_MAC:
                    # evtloop.Pending() just returns True on MacOs
                    evtloop.DispatchTimeout(0)
                    self.ui_idle = False
                else:
                    while evtloop.Pending():
                        evtloop.Dispatch()
                        await asyncio.sleep(0)
                        self.ui_idle = False
                await asyncio.sleep(self.sleep_duration)
                self.ProcessPendingEvents()
                if not self.ui_idle:
                    evtloop.ProcessIdle()
                    self.ui_idle = True
            self.exiting = False

    def ExitMainLoop(self):
        self.exiting = True

    def AsyncBind(self, event_binder, async_callback, object, source=None, id=wx.ID_ANY, id2=wx.ID_ANY):
        """Bind a coroutine to a wx Event. Note that when wx object is destroyed, any coroutine still running will be cancelled automatically.
        """ 
        # We restrict the object to wx.Windows to be able to cancel the coroutines on EVT_WINDOW_DESTROY, even if wx.Bind works with any wx.EvtHandler
        if not isinstance(object, wx.Window):
            raise Exception("object must be a wx.Window")
        if not iscoroutinefunction(async_callback):
            raise Exception("async_callback is not a coroutine function")
        if object not in self.BoundObjects:
            self.BoundObjects[object] = defaultdict(list)
            object.Bind(wx.EVT_WINDOW_DESTROY, lambda event: self.OnDestroy(event, object), object)
        self.BoundObjects[object][event_binder.typeId].append(async_callback)
        object.Bind(event_binder, lambda event: StartCoroutine(async_callback(event.Clone()), object), source=source, id=id, id2=id2)

    def StartCoroutine(self, coroutine, obj):
        """Start and attach a coroutine to a wx object. When object is destroyed, the coroutine will be cancelled automatically.
           returns an asyncio.Task
        """ 
        # We restrict the object to wx.Windows to be able to cancel the coroutines on EVT_WINDOW_DESTROY, even if wx.Bind works with any wx.EvtHandler
        if not isinstance(obj, wx.Window):
            raise Exception("obj must be a wx.Window")
        if asyncio.iscoroutinefunction(coroutine):
            coroutine = coroutine()
        if obj not in self.BoundObjects:
            self.BoundObjects[obj] = defaultdict(list)
            obj.Bind(wx.EVT_WINDOW_DESTROY, lambda event: self.OnDestroy(event, obj), obj)
        task = asyncio.create_task(coroutine)
        task.add_done_callback(self.OnTaskCompleted)
        task.obj = obj
        self.RunningTasks[obj].add(task)
        return task

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


def AsyncBind(event, async_callback, object, source=None, id=wx.ID_ANY, id2=wx.ID_ANY):
    app = wx.App.Get()
    if not isinstance(app, WxAsyncApp):
        raise Exception("Create a 'WxAsyncApp' first")
    app.AsyncBind(event, async_callback, object, source=source, id=id, id2=id2)


def StartCoroutine(coroutine, obj):
    app = wx.App.Get()
    if not isinstance(app, WxAsyncApp):
        raise Exception("Create a 'WxAsyncApp' first")
    return app.StartCoroutine(coroutine, obj)


#
#  Note: os level dialogs like wx.FileDialog, wx.DirDialog, wx.FontDialog, wx.ColourDialog, wx.MessageDialog are 
#  handled differently: 
#    * They only support ShowModal
#    * They must be run in an executor to avoid blocking the main event loop
# 


async def ShowModalInExecutor(dlg):
    loop = asyncio.get_running_loop()    
    return await loop.run_in_executor(None, dlg.ShowModal)
        

async def AsyncShowDialog(dlg):
    if type(dlg) in [wx.FileDialog, wx.DirDialog, wx.FontDialog, wx.ColourDialog, wx.MessageDialog]:
        raise Exception("This type of dialog cannot be shown modless, please use 'AsyncShowDialogModal'")
    closed = Event()
    def end_dialog(return_code):
        dlg.SetReturnCode(return_code)
        dlg.Hide()
        closed.set()
    async def on_button(event):
        # Same code as in wxwidgets:/src/common/dlgcmn.cpp:OnButton
        # to automatically handle OK, CANCEL, APPLY,... buttons 
        id = event.GetId()
        if id == dlg.GetAffirmativeId():
            if dlg.Validate() and dlg.TransferDataFromWindow():
                end_dialog(id)
        elif id == wx.ID_APPLY:
            if dlg.Validate():
                dlg.TransferDataFromWindow()
        elif id == dlg.GetEscapeId() or (id == wx.ID_CANCEL and dlg.GetEscapeId() == wx.ID_ANY):
            end_dialog(wx.ID_CANCEL)
        else:
            event.Skip()
    async def on_close(event):
        closed.set()
        dlg.Hide()
    AsyncBind(wx.EVT_CLOSE, on_close, dlg)
    AsyncBind(wx.EVT_BUTTON, on_button, dlg)
    dlg.Show()
    await closed.wait()
    return dlg.GetReturnCode()


async def AsyncShowDialogModal(dlg):
    if type(dlg) in [wx.html.HtmlHelpDialog, wx.FileDialog, wx.DirDialog, wx.FontDialog, wx.ColourDialog, wx.MessageDialog]:
        return await ShowModalInExecutor(dlg)
    else:
        frames = set(wx.GetTopLevelWindows()) - set([dlg])
        states = {frame: frame.IsEnabled() for frame in frames}
        try:
            for frame in frames:
                frame.Disable()
            return await AsyncShowDialog(dlg)
        finally:
            for frame in frames:
                frame.Enable(states[frame])
            parent = dlg.GetParent()
            if parent:
                parent.SetFocus()
                    
