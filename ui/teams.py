import wx
from ObjectListView import ObjectListView, ColumnDefn
from pubsub import pub
from pymysql.cursors import DictCursor

class Team:
    def __init__(self, dict_record):
        self.__dict__.update(dict_record)

class TeamsWindow(wx.Panel):
    def __init__(self, parent, db=None):
        wx.Panel.__init__(self, parent, -1)
        self.listview = ObjectListView(self, wx.ID_ANY, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.listview, 1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.db = db
        pub.subscribe(self.onDivision, 'division')

    def onDivision(self, division):
        cursor = self.db.cursor(DictCursor)
        cursor.execute('''SELECT team.id as db_id, team.name, flt_pos, clubname, venue_id, lat, lon, venue.name as vname
                          FROM team
                          LEFT JOIN division ON division_id=division.id
                          LEFT JOIN venue ON venue_id=venue.id
                          WHERE division.label = %s
                          ORDER BY clubname, name''', division)
        self.teams = dict([(x['db_id'], Team(x)) for x in cursor.fetchall()])
        self.listview.SetColumns([
            ColumnDefn("ID", "left", -1, "flt_pos"),
            ColumnDefn("Team Name", "left", -1, "name"),
            ColumnDefn("Club Name", "left", -1, "clubname"),
            ColumnDefn("Venue", "left", -1, "vname"),
        ])
        self.listview.CreateCheckStateColumn()
        self.listview.SetObjects(list(self.teams.values()))
        pub.sendMessage('teams', teams=self.teams.values())

    def onMapSelect(self, selected):
        if not selected:
            print('No selection', flush=True)
            return
        selection = []
        for x in selected:
            if x is not None:
                label, db_id, name = x
                if label == 'Venue':
                    self.listview.Check(self.venues[db_id])
        self.listview.Update()


if __name__ == '__main__':
    import database
    db = database.get_db()
    app = wx.App(redirect=False)
    frame = wx.Frame(None)
    test = VenueWindow(frame, db)
    app.SetTopWindow(frame)
    frame.Show(True)
    app.MainLoop()
