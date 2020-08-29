import wx
import sys

from main import MainFrame

APP_NAME = 'Schedules'

DEFAULTS = (('screenwidth' , 1000),
            ('screenheight', 600),
            ('posx',  -1),
            ('posy',  -1),
           )
MAP_DEFAULTS = (('lat', 32.8407),
                ('lon', -83.6324),
                ('level', 8)
               )
class MyApp(wx.App):
    def OnInit(self):
        wx.GetApp().SetAppName(APP_NAME)
        config = wx.Config(APP_NAME)
        params = []
        for attr, default in DEFAULTS:
            params.append(config.ReadInt('/LastRun/'+attr, default))
        extras = {}
        for attr, default in MAP_DEFAULTS:
            key = '/LastRun/'+attr
            try:
                extras[attr] = config.ReadFloat(key, default)
            except:
                extras[attr] = config.ReadInt(key, default)

        self.frame = MainFrame(None, size=(params[0], params[1]), pos=(params[2], params[3]), title=APP_NAME, **extras)
        self.SetTopWindow(self.frame)
        self.frame.SetIcon(wx.Icon("app.ico"))
        self.frame.Show(True)
        return True

app = MyApp(redirect=False)
app.MainLoop()

