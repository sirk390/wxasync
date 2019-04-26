# wxasync
## asyncio support for wxpython

wxasync it a library for using python 3 asyncio (async/await) with wxpython.
 It does GUI message polling every 5ms and runs the asyncio message loop the rest of the time. 
 The polling doesn't have a noticable effect on CPU usage (still 0% when idle). 
 
You can install it using: 
```sh
pip install wxasync
```

To use it, just create a **WxAsyncApp** instead of a **wx.App**

```python
app = WxAsyncApp()
```

and use **AsyncBind** to bind an event to a coroutine. 
```python
async def async_callback():
    (...your code...)
    
AsyncBind(wx.EVT_BUTTON, async_callback, button1)
```
You can still use wx.Bind together with AsyncBind.

If you don't want to wait for an event, you just use **StartCoroutine** and it will be executed immediatly. 
```
StartCoroutine(update_clock_coroutine, frame)
```
Any coroutine started using **AsyncBind** or using **StartCoroutine** is attached to a wx Window. It is automatically cancelled when the Window is destroyed. This makes it easier to use, as you don't need to take care of cancelling them yourselve. 

To show a Dialog, use **AsyncShowDialog** instead of dlg.Show(). This allows
to use 'await' to wait until the dialog completes. Don't use ShowModal() as it would block the event loop.

You start the application using:
```python
loop.run_until_complete(app.MainLoop())
```

Below is full example with AsyncBind, WxAsyncApp, and StartCoroutine:

```python
import wx
from wxasync import AsyncBind, WxAsyncApp, StartCoroutine
import asyncio
from asyncio.events import get_event_loop
import time

class TestFrame(wx.Frame):
    def __init__(self, parent=None):
        super(TestFrame, self).__init__(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)
        button1 =  wx.Button(self, label="Submit")
        self.edit =  wx.StaticText(self, style=wx.ALIGN_CENTRE_HORIZONTAL|wx.ST_NO_AUTORESIZE)
        self.edit_timer =  wx.StaticText(self, style=wx.ALIGN_CENTRE_HORIZONTAL|wx.ST_NO_AUTORESIZE)
        vbox.Add(button1, 2, wx.EXPAND|wx.ALL)
        vbox.AddStretchSpacer(1)
        vbox.Add(self.edit, 1, wx.EXPAND|wx.ALL)
        vbox.Add(self.edit_timer, 1, wx.EXPAND|wx.ALL)
        self.SetSizer(vbox)
        self.Layout()
        AsyncBind(wx.EVT_BUTTON, self.async_callback, button1)
        StartCoroutine(self.update_clock, self)
        
    async def async_callback(self, event):
        self.edit.SetLabel("Button clicked")
        await asyncio.sleep(1)
        self.edit.SetLabel("Working")
        await asyncio.sleep(1)
        self.edit.SetLabel("Completed")

    async def update_clock(self):
        while True:
            self.edit_timer.SetLabel(time.strftime('%H:%M:%S'))
            await asyncio.sleep(0.5)
            
app = WxAsyncApp()
frame = TestFrame()
frame.Show()
app.SetTopWindow(frame)
loop = get_event_loop()
loop.run_until_complete(app.MainLoop())
```

## Performance

Below is view of the performances (on windows Core I7-7700K 4.2Ghz):

| Scenario      |Latency  |  Latency (at max throughput)| Max Throughput(msg/s) |
| ------------- |--------------|---------------------------------|-------------|
| asyncio only (for reference)  |0ms             |17ms                               |571 325|
| wx only (for reference)       |0ms             |19ms                               |94 591|
| wxasync (GUI) | 5ms            |19ms                               |52 304|
| wxasync (GUI+asyncio)| 5ms GUI / 0ms asyncio |24ms GUI / 12ms asyncio |40 302 GUI + 134 000 asyncio|


The performance tests are included in the 'test' directory.
