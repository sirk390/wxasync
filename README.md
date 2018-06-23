# wxasync
## asyncio support for wxpython

wxasync it a library for using python 3 asyncio (async/wait) with wxpython.
 It does GUI message polling every 5ms and runs the asyncio message loop the rest of the time.

The library defines **WxAsyncApp**, **AsyncBind** and **StartCoroutine**.

Just create a **WxAsyncApp** instead of a **wx.App**, and use **AsyncBind** when you want
to bind an event to a coroutine. 
For background jobs, you can use **StartCoroutine**, to start and attach coroutines to a wx object.

When completed, start the application using loop.run_until_complete(app.MainLoop()).

Below is a simple example:

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

| Scenario      |Latency  |  Latency (max throughput)| Throughput(msg/s) |
| ------------- |--------------|---------------------------------|-------------|
| asyncio only (for reference)  |0ms             |17ms                               |571 325|
| wx only (for reference)       |0ms             |19ms                               |94 591|
| wxasync (GUI) | 5ms            |19ms                               |52 304|
| wxasync (GUI+asyncio)| 5ms GUI / 0ms asyncio |24ms GUI / 12ms asyncio |40 302 GUI + 134 000 asyncio|


The performance tests are included in the 'test' directory.
