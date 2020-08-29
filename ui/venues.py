import wx
from ObjectListView import ObjectListView, ColumnDefn
from pubsub import pub

class Venue:
    def __init__(self, record):
        self.db_id, self.name, self.lat, self.lon = record

class VenueWindow(wx.Panel):
    def __init__(self, parent, db=None):
        wx.Panel.__init__(self, parent, -1)
        self.listview = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.listview, 1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        if db:
            self.load(db)
        # pub.subscribe(self.onMapSelect, "map_selection")
        self.listview.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect)

    def OnSelect(self, event):
        pub.sendMessage('selected_venues', venues=self.listview.GetSelectedObjects())

    def load(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT id, name, lat, lon FROM venue ORDER BY name")
        self.venues = dict([(x[0], Venue(x)) for x in cursor.fetchall()])
        self.listview.SetColumns([
            ColumnDefn("ID",    "left", -1, "db_id"),
            ColumnDefn("Venue", "left", -1, "name"),
        ])
        # self.listview.CreateCheckStateColumn()
        self.listview.SetObjects(list(self.venues.values()))
        pub.sendMessage('venues', venues=list(self.venues.values()))



if __name__ == '__main__':
    import database
    db = database.get_db()
    app = wx.App(redirect=False)
    frame = wx.Frame(None)
    test = VenueWindow(frame, db)
    app.SetTopWindow(frame)
    frame.Show(True)
    app.MainLoop()
