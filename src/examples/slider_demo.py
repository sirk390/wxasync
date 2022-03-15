import wx
from wxasync import WxAsyncApp, AsyncBind
import asyncio
from asyncio.events import get_event_loop

SLIDERS_COUNT = 5           # number of sliders to display.
MAX_VALUE = 100             # maximum value of sliders.
DELAY = 0.05                # delay between updating slider positions.

class TestFrame(wx.Frame):
    def __init__(self, parent=None):
        super(TestFrame, self).__init__(parent)

        # Add a button.
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.button =  wx.Button(self, label="Press to Run")
        vbox.Add(self.button, 1, wx.CENTRE)

        # Add N sliders.
        self.sliders =  []
        for i in range(SLIDERS_COUNT):
            s = wx.Slider(self)
            self.sliders.append(s)
            vbox.Add(s, 1, wx.EXPAND|wx.ALL)

        # Layout the gui elements in the frame.
        self.SetSizer(vbox)
        self.Layout()

        # bind an asyncio coroutine to the button event.
        AsyncBind(wx.EVT_BUTTON, self.async_slider_demo, self.button)

    async def async_slider_demo(self, event):
        # Update button properties.
        self.button.Enabled = False

        for i in range(5):
            dots = "." * i
            label = "Initialising" + dots
            self.button.Label = label
            # Add a delay so we can see the button properites change.
            # (allows the wx MainLoop async coroutine to run)
            await asyncio.sleep(0.5)

        # initilase sliders and increment values for each slider.
        inc = []
        for i,s  in enumerate(self.sliders):
            s.Value = 0
            inc.append(i+1)
        check = 0

        # Update button properties.
        self.button.Label = "Running..."

        # Using asyncio.sleep will yield here and return ASAP.
        # (allows the wx MainLoop to run and show button changes)
        await asyncio.sleep(0)

        # increment and update each slider, if it hasn't finished yet.
        while check < SLIDERS_COUNT:
            for i, s in enumerate(self.sliders):
                if i < check:
                    continue            # skip updating this slider.
                val = s.Value + inc[i]
                if val > MAX_VALUE:
                    val = MAX_VALUE
                    inc[i] = -inc[i]    # change direction (decrease)
                elif val < 0:
                    val = 0
                    inc[i] = -inc[i]    # change direction (increase)
                s.Value = val

            # check next slider if current slider has finished.
            if self.sliders[check].Value == MAX_VALUE:
                check += 1

            # async sleep will delay and yield this async coroutine.
            # (allows the wx MainLoop async coroutine to run)
            await asyncio.sleep(DELAY)

        # Update button properties.
        self.button.Label = "Run again"
        self.button.Enabled = True

if __name__ == '__main__':
    
    async def main():            
        app = WxAsyncApp()
        frame = TestFrame()
        frame.Show()
        app.SetTopWindow(frame)
        await app.MainLoop()
        
    
    asyncio.run(main())
