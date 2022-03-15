from wx import TextEntryDialog
from wxasync import AsyncShowDialog, WxAsyncApp
import asyncio
import wx

async def opendialog():
    """ This functions demonstrate the use of 'AsyncShowDialog' to Show a 
        any wx.Dialog asynchronously, and wait for the result.
    """
    dlg = TextEntryDialog(None, "Please enter some text:")
    return_code = await AsyncShowDialog(dlg)
    print ("The ReturnCode is %s and you entered '%s'" % (return_code, dlg.GetValue()))
    app = wx.App.Get()
    app.ExitMainLoop()


if __name__ == '__main__':
    async def main():            
        app = WxAsyncApp()
        asyncio.create_task(opendialog())
        await app.MainLoop()
        
    
    asyncio.run(main())
