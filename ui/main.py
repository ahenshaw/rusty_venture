# third-part modules
import wx
import wx.aui
from pubsub import pub
import pyslip
from math import radians
# custom modules
from map import init_tiles, Map
import database
from venues import VenueWindow
from teams  import TeamsWindow

VERSION = '1.0'

DefaultTilesetIndex = 3

class MainFrame(wx.Frame):
    def __init__(self, parent, id=wx.ID_ANY, title=None, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE, lat=None, lon=None, level=None):

        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        self.app_config = wx.Config(title)
        self.db = database.get_db()

        self.menubar = self.CreateMenuBar()
        self.SetMenuBar(self.menubar)
        self.ConfigureToolbar()
        self.mgr = wx.aui.AuiManager()
        self.mgr.SetManagedWindow(self)

        self.tileset_manager = init_tiles()
        self.tile_source = self.tileset_manager.get_tile_source(DefaultTilesetIndex)
        self.map = Map(self, start_level=4, tile_src=self.tile_source, style=wx.SIMPLE_BORDER)
        self.map.Freeze()
        wx.CallLater(0, self.final_setup, int(level), (lon, lat))

        self.statusbar = SchedulesStatusBar(self)
        self.SetStatusBar(self.statusbar)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.teamWindow = TeamsWindow(self, self.db)
        self.venueWindow = VenueWindow(self, self.db)

        self.mgr.AddPane(self.map,
                         wx.aui.AuiPaneInfo().
                         Name("Map").
                         CaptionVisible(False).
                         Center().
                         Position(0).
                         CloseButton(False))

        self.mgr.AddPane(self.teamWindow,
                         wx.aui.AuiPaneInfo().
                         Name("Teams").
                         Caption("Teams").
                         CaptionVisible(True).
                         Right().
                         Position(0).
                         MinSize(wx.Size(100, -1)).
                         BestSize(wx.Size(200, -1)).
                         CloseButton(False))
        self.mgr.AddPane(self.venueWindow,
                         wx.aui.AuiPaneInfo().
                         Name("Venues").
                         Caption("Venues").
                         CaptionVisible(True).
                         Left().
                         Position(0).
                         MinSize(wx.Size(100, -1)).
                         BestSize(wx.Size(200, -1)).
                         CloseButton(False))

        perspective = self.app_config.Read('/LastRun/perspective', '')
        if perspective:
            self.mgr.LoadPerspective(perspective)
        self.mgr.Update()

    def final_setup(self, level, position):
        self.map.GotoLevelAndPosition(level, position)
        self.map.Thaw()

    def OnConfigClose(self, message):
        self.mgr.GetPane('Config').Show(False)
        self.config_menu_item.Check(False)

    def OnConfigToggle(self, event):
        self.mgr.GetPane('Config').Show(event.IsChecked())
        self.mgr.Update()

    def OnClose(self, event):
        # save the current layout into the config
        width, height = self.GetSize()
        pt = self.GetScreenPosition()
        self.app_config.WriteInt('/LastRun/screenwidth', width)
        self.app_config.WriteInt('/LastRun/screenheight', height)
        self.app_config.WriteInt('/LastRun/posx', pt.x)
        self.app_config.WriteInt('/LastRun/posy', pt.y)

        level, geo = self.map.GetLevelAndPosition()
        self.app_config.WriteFloat('/LastRun/lat', geo[1])
        self.app_config.WriteFloat('/LastRun/lon', geo[0])
        self.app_config.WriteInt('/LastRun/level', level)
        self.app_config.Write('/LastRun/perspective', self.mgr.SavePerspective())
        # self.app_config.Write('/LastRun/perspective', '')

        self.mgr.UnInit()
        event.Skip()

    def OnAbout(self, event):
        msg = '''Schedules\nVersion %s\n\ncopyright 2020 Andrew Henshaw''' % VERSION

        dlg = wx.MessageDialog(self, msg, "Schedules", wx.OK | wx.ICON_INFORMATION)
        #~ dlg.SetFont(wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, False, "Verdana"))
        dlg.ShowModal()
        dlg.Destroy()

    def CreateMenuBar(self, with_window=False):
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(wx.ID_OPEN,   "&Open...")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT,   "&Exit")

        sm = wx.Menu()
        self.Bind(wx.EVT_MENU, self.onMakePairings,    sm.Append(-1, "Make Pairings..."))
        self.Bind(wx.EVT_MENU, self.onBalancePairings, sm.Append(-1, "Balance Pairings"))
        self.Bind(wx.EVT_MENU, self.onMakeCalendar,    sm.Append(-1, "Make Calendar"))


        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "&About")

        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(sm,        "&Scheduling")
        menu_bar.Append(help_menu, "&Help")

        self.Bind(wx.EVT_MENU, self.OnAbout,  id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.onExit,  id=wx.ID_EXIT)
        return menu_bar

    def onMakePairings(self, event):
        print('make pairings', flush=True)

    def onBalancePairings(self, event):
        print('balance pairings', flush=True)

    def onMakeCalendar(self, event):
        print('make calendar', flush=True)


    def onExit(self, event):
        self.Close()

    def ConfigureToolbar(self):
        cursor = self.db.cursor()
        cursor.execute('SELECT label FROM division')
        divisions = [x[0] for x in cursor.fetchall()]

        cursor.execute('SELECT id FROM season ORDER BY startdate DESC')
        seasons = [x[0] for x in cursor.fetchall()]

        self.tb = wx.ToolBar(self)
        self.tb.SetToolBitmapSize((48, 48))

        self.seasons   = wx.ComboBox(self.tb, -1, value=seasons[0], choices=seasons, style=wx.CB_READONLY)
        self.divisions = wx.ComboBox(self.tb, -1, value='', choices=divisions, style=wx.CB_READONLY)

        self.tb.AddControl(wx.StaticText(self.tb, -1, ' Season: '))
        self.tb.AddControl(self.seasons)

        self.tb.AddControl(wx.StaticText(self.tb, -1, ' Division: '))
        self.tb.AddControl(self.divisions)

        self.tb.Realize()
        self.SetToolBar(self.tb)
        self.divisions.Bind(wx.EVT_COMBOBOX, self.onDivisions)

    def onDivisions(self, event):
        pub.sendMessage('division', division=self.divisions.GetStringSelection())


class SchedulesStatusBar(wx.StatusBar):
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, style=wx.SB_SUNKEN)
        self.SetFieldsCount(2, [200, -1])
        pub.subscribe(self.onMapSelect, "map_selection")

    def onMapSelect(self, selected):
        print('--', flush=True)
        if not selected:
            self.SetStatusText('', 0)
            self.SetStatusText('', 0)

        for record in selected:
            print(repr(record), flush=True)
            if record is not None:
                label, db_id, name = record
                self.SetStatusText(name, label=='Team')

