from wx import TextEntryDialog
from wxasync import AsyncShowDialog, WxAsyncApp
from asyncio.events import get_event_loop

async def main():
    """ This functions demonstrate the use of 'AsyncShowDialog' to Show a 
        any wx.Dialog asynchronously, and wait for the result.
    """
    dlg = TextEntryDialog(None, "Please enter some text:")
    return_code = await AsyncShowDialog(dlg)
    print ("The ReturnCode is %s and you entered '%s'" % (return_code, dlg.GetValue()))
    app.ExitMainLoop()

if __name__ == '__main__':
    app = WxAsyncApp()
    loop = get_event_loop()
    loop.create_task(main())
    loop.run_until_complete(app.MainLoop())
    