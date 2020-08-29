import os
import sys

import wx

import pyslip
import pyslip.gmt_local as tiles
from pubsub import pub


Tilesets = [
            ('BlueMarble tiles', 'blue_marble'),
            ('GMT tiles', 'gmt_local'),
            ('OpenStreetMap tiles', 'open_street_map'),
            ('Stamen Toner tiles', 'stamen_toner'),
            ('Stamen Transport tiles', 'stamen_transport'),
            ('Stamen Watercolor tiles', 'stamen_watercolor'),
           ]

# index into Tilesets above to set default tileset: GMT tiles


class TilesetManager:
    """A class to manage multiple tileset objects.

        ts = TilesetManager(source_list)  # 'source_list' is list of tileset source modules
        ts.get_tile_source(index)         # 'index' into 'source_list' of source to use

    Features 'lazy' importing, only imports when the tileset is used
    the first time.
    """

    def __init__(self, mod_list):
        """Create a set of tile sources.

        mod_list  list of module filenames to manage

        The list is something like: ['open_street_map.py', 'gmt_local.py']

        We can access tilesets using the index of the module in the 'mod_list'.
        """

        self.modules = []
        for fname in mod_list:
            self.modules.append([fname, os.path.splitext(fname)[0], None])

    def get_tile_source(self, mod_index):
        """Get an open tileset source for given name.

        mod_index  index into self.modules of tileset to use
        """

        tileset_data = self.modules[mod_index]
        (filename, modulename, tile_obj) = tileset_data
        if not tile_obj:
            # have never used this tileset, import and instantiate
            obj = __import__('pyslip', globals(), locals(), [modulename])
            tileset = getattr(obj, modulename)
            tile_obj = tileset.Tiles()
            tileset_data[2] = tile_obj
        return tile_obj


def init_tiles():
    """Initialize the tileset manager.

    Return a reference to the manager object.
    """

    modules = []
    for (action_id, (name, module_name)) in enumerate(Tilesets):
        modules.append(module_name)

    return TilesetManager(modules)


class Map(pyslip.pySlip):
    def __init__(self, parent, **kwargs):
        pyslip.pySlip.__init__(self, parent, **kwargs)
        pub.subscribe(self.onVenues, 'venues')
        pub.subscribe(self.onTeams, 'teams')
        pub.subscribe(self.onSelectedVenues, 'selected_venues')
        self.venues = None
        self.vis_venues = True

        self.ppi = wx.ScreenDC().GetPPI()[0]
        self.Bind(pyslip.EVT_PYSLIP_SELECT, self.onSingleSelect)

    def onSelectedVenues(self, venues):
        try:
            self.DeleteLayer(self.selected_venues)
        except:
            pass
        points = []
        for venue in venues:
            points.append((venue.lon, venue.lat, {'data':('Venue', venue.db_id, venue.name)}))

        radius = round(12 * self.ppi/120)
        self.selected_venues = self.AddPointLayer(points, map_rel=True, visible=True,
                        show_levels=None, selectable=True,
                        name='<selected_venues>', **{'radius':radius, 'color':'#4040FFFF'})
        self.PushLayerToBack(self.selected_venues)

    def onVenues(self, venues):
        points = []
        for venue in venues:
            points.append((venue.lon, venue.lat, {'data':('Venue', venue.db_id, venue.name)}))

        radius = round(6 * self.ppi/120)
        self.venues = self.AddPointLayer(points, map_rel=True, visible=True,
                        show_levels=None, selectable=True,
                        name='<venues>', **{'radius':radius, 'color':'#A0A0FF80'})

    def onTeams(self, teams):
        points = []
        for team in teams:
            if team.lon is not None:
                points.append((team.lon, team.lat, {'data':('Team', team.db_id, team.name)}))

        try:
            self.DeleteLayer(self.teams)
        except:
            pass
        radius = round(6 * self.ppi/120)
        self.teams = self.AddPointLayer(points, map_rel=True, visible=True,
                        show_levels=None, selectable=True,
                        name='<teams>', **{'radius':radius, 'color':'#C00000'})

    def onSingleSelect(self, event):
        pub.sendMessage("map_selection", selected=[event.data])
