import wx
from wxasync import WxAsyncApp, AsyncBind, StartCoroutine, AsyncShowDialog
from asyncio import get_event_loop
import asyncio
import time
from wx._core import TextEntryDialog, FontDialog, MessageDialog, DefaultPosition, DefaultSize
from wx._html import HtmlHelpDialog, HF_DEFAULT_STYLE
from wx._adv import PropertySheetDialog


class TestFrame(wx.Frame):
    def __init__(self, parent=None):
        super(TestFrame, self).__init__(parent, size=(600,800))
        vbox = wx.BoxSizer(wx.VERTICAL)
        button1 =  wx.Button(self, label="ColourDialog")
        button2 =  wx.Button(self, label="DirDialog")
        button3 =  wx.Button(self, label="FileDialog")
        # FindReplaceDialog is always modless
        button5 =  wx.Button(self, label="FontDialog")
        # GenericProgressDialog does not input data
        button7 =  wx.Button(self, label="HtmlHelpDialog")
        button8 =  wx.Button(self, label="MessageDialog")
        button9 =  wx.Button(self, label="MultiChoiceDialog")
        button10 =  wx.Button(self, label="NumberEntryDialog")
        button12 =  wx.Button(self, label="PrintAbortDialog")
        button13 =  wx.Button(self, label="PropertySheetDialog")
        button14 =  wx.Button(self, label="RearrangeDialog")
        button16 =  wx.Button(self, label="SingleChoiceDialog")
        button18 =  wx.Button(self, label="TextEntryDialog")
        
        self.edit_timer =  wx.StaticText(self, style=wx.ALIGN_CENTRE_HORIZONTAL|wx.ST_NO_AUTORESIZE)
        vbox.Add(button1, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button2, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button3, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button5, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button7, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button8, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button9, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button10, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button12, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button13, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button14, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button16, 2, wx.EXPAND|wx.ALL)
        vbox.Add(button18, 2, wx.EXPAND|wx.ALL)

        AsyncBind(wx.EVT_BUTTON, self.on_ColourDialog, button1)
        AsyncBind(wx.EVT_BUTTON, self.on_DirDialog, button2)
        AsyncBind(wx.EVT_BUTTON, self.on_FileDialog, button3)
        AsyncBind(wx.EVT_BUTTON, self.on_FontDialog, button5)
        AsyncBind(wx.EVT_BUTTON, self.on_HtmlHelpDialog, button7)
        AsyncBind(wx.EVT_BUTTON, self.on_MessageDialog, button8)
        AsyncBind(wx.EVT_BUTTON, self.on_MultiChoiceDialog, button9)
        AsyncBind(wx.EVT_BUTTON, self.on_NumberEntryDialog, button10)
        AsyncBind(wx.EVT_BUTTON, self.on_PrintAbortDialog, button12)
        AsyncBind(wx.EVT_BUTTON, self.on_PropertySheetDialog, button13)
        AsyncBind(wx.EVT_BUTTON, self.on_RearrangeDialog, button14)
        AsyncBind(wx.EVT_BUTTON, self.on_SingleChoiceDialog, button16)
        AsyncBind(wx.EVT_BUTTON, self.on_TextEntryDialog, button18)
        
        
        button5 =  wx.Button(self, label="FontDialog")
        button7 =  wx.Button(self, label="HtmlHelpDialog")
        button8 =  wx.Button(self, label="MessageDialog")
        button9 =  wx.Button(self, label="MultiChoiceDialog")
        button10 =  wx.Button(self, label="NumberEntryDialog")
        button12 =  wx.Button(self, label="PrintAbortDialog")
        button13 =  wx.Button(self, label="PropertySheetDialog")
        button14 =  wx.Button(self, label="RearrangeDialog")
        button16 =  wx.Button(self, label="SingleChoiceDialog")
        button18 =  wx.Button(self, label="TextEntryDialog")
        
        self.SetSizer(vbox)
        self.Layout()
        vbox.AddStretchSpacer(1)
        vbox.Add(self.edit_timer, 1, wx.EXPAND|wx.ALL)
        self.SetSizer(vbox)
        self.Layout()
        StartCoroutine(self.update_clock, self)

    async def ShowDialog(self, dlg):
        response  = await AsyncShowDialog(dlg)
        NAMES = {wx.ID_OK : "ID_OK", wx.ID_CANCEL: "ID_CANCEL"}        
        print (NAMES.get(response, response))
        
    async def update_clock(self):
        while True:
            self.edit_timer.SetLabel(time.strftime('%H:%M:%S'))
            await asyncio.sleep(0.5)
        
    async def on_ColourDialog(self, event):
        data = wx.ColourData()
        data.SetColour(wx.BLACK)
        dlg = wx.ColourDialog(self, data)
        await self.ShowDialog(dlg)
                
    async def on_DirDialog(self, event):
        dlg = wx.DirDialog (None, "Choose input directory", "", wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        await self.ShowDialog(dlg)
                                
    async def on_FileDialog(self, event):
        dlg =  wx.FileDialog(self, "Save XYZ file", wildcard="XYZ files (*.xyz)|*.xyz", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        await self.ShowDialog(dlg)

    async def on_FontDialog(self, event):
        dlg = FontDialog(self)
        await self.ShowDialog(dlg)
                
    async def on_HtmlHelpDialog(self, event):
        dlg = HtmlHelpDialog(self, id=wx.ID_ANY, title="", style=HF_DEFAULT_STYLE, data=None)
        await self.ShowDialog(dlg)
                
    async def on_MessageDialog(self, event):
        dlg = MessageDialog(self, "message", caption="Caption", style=wx.OK|wx.CENTRE, pos=wx.DefaultPosition)
        await self.ShowDialog(dlg)
                
    async def on_MultiChoiceDialog(self, event):
        dlg = wx.MultiChoiceDialog(self, "message", "caption", ["One", "Two", "Three"], style=wx.CHOICEDLG_STYLE, pos=wx.DefaultPosition)                
        await self.ShowDialog(dlg)
        
    async def on_NumberEntryDialog(self, event):
        dlg = wx.NumberEntryDialog(self, "message", "prompt", "caption", 100, 0, 1000, pos=DefaultPosition)
        await self.ShowDialog(dlg)
                        
    async def on_PrintAbortDialog(self, event):
        dlg = wx.PrintAbortDialog(self, "documentTitle", pos=DefaultPosition, size=DefaultSize, style=wx.DEFAULT_DIALOG_STYLE, name="dialog")                
        await self.ShowDialog(dlg)
        
    async def on_PropertySheetDialog(self, event):
        dlg = PropertySheetDialog(self, id=wx.ID_ANY, title="", pos=DefaultPosition, size=DefaultSize, style=wx.DEFAULT_DIALOG_STYLE, name="DialogNameStr")                
        await self.ShowDialog(dlg)
        
    async def on_RearrangeDialog(self, event):
        dlg = wx.RearrangeDialog(None,
                                 "You can also uncheck the items you don't like "
                                 "at all.",
                                 "Sort the items in order of preference",
                                 [3, 0, 1, 2], ["meat", "fish", "fruits", "beer"])                
        await self.ShowDialog(dlg)
        
    async def on_SingleChoiceDialog(self, event):
        dlg = wx.SingleChoiceDialog(self, "message", "caption", ["One", "Two", "Three"], style=wx.CHOICEDLG_STYLE, pos=wx.DefaultPosition)                
        await self.ShowDialog(dlg)
                
    async def on_TextEntryDialog(self, event):
        dlg = TextEntryDialog(self, "Please enter some text:")
        return_code = await AsyncShowDialog(dlg)
        print ("The ReturnCode is %s and you entered '%s'" % (return_code, dlg.GetValue()))


if __name__ == "__main__":        
    app = WxAsyncApp()
    frame = TestFrame()
    frame.Show()
    app.SetTopWindow(frame)
    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
