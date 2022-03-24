""" Example server using asyncio streams
"""
from wxasync import WxAsyncApp, StartCoroutine
import asyncio
import wx


class TestFrame(wx.Frame):
    def __init__(self, parent=None):
        super(TestFrame, self).__init__(parent, title="Server Example")
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.logctrl =  wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY)
        vbox.Add(self.logctrl, 1, wx.EXPAND|wx.ALL)
        self.SetSizer(vbox)
        self.Layout()
        StartCoroutine(self.run_server, self)

    def log(self, text):
        self.logctrl.AppendText(text + "\r\n")
        
    async def handle_connection(self, reader, writer):
        while True:
            try:
                data = await reader.read(100)
                if not data:
                    break
                message = data.decode()
                addr = writer.get_extra_info('peername')
                self.log(f"Received {message!r} from {addr!r}")
                self.log(f"Send: {message!r}")
                writer.write(data)
                await writer.drain()
            except ConnectionError:
                break
        self.log("Close the connection")
        writer.close()


    async def run_server(self):
        server = await asyncio.start_server(self.handle_connection, '127.0.0.1', 8888)
    
        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        self.log(f'Serving on {addrs}')
    
        async with server:
            await server.serve_forever()


async def main():            
    app = WxAsyncApp()
    frame = TestFrame()
    frame.Show()
    app.SetTopWindow(frame)
    await app.MainLoop()


asyncio.run(main())

