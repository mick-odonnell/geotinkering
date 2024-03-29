"""
This is a dummy to try and get a gis gui up and running
"""
from GUI_1 import MyShape
import json
from collections import defaultdict
from tkinter import *
from tkinter import ttk
from descartes.patch import PolygonPatch
import shapely
import shapely.geometry as geometry
from shapely.ops import cascaded_union
import matplotlib.pyplot as plt
import fiona
from fiona.crs import from_epsg
import os

"""
thanks to this url for plotting ->  https://gist.github.com/urschrei/6436526
"""


def main():
    with open("cso_counties.txt", 'r') as f1:
        cty_str = f1.read()

    with open("geonames_pop.txt",'r') as f2:
        pop_str = f2.read()


    cty_polygons = json.loads(cty_str)
    places_pts = json.loads(pop_str)
    stack = []
    stack.append([cty_polygons, 'countyname', 'counties'])
    stack.append([places_pts, 'asciiname', 'towns'])
    gis_data = defaultdict()
    if stack:
        for obj in stack:
            gis_data[obj[2]] = MyShape(obj[0], obj[1])
    root = Tk()
    MicksGis(root, gis_data)
    root.mainloop()


class MicksGis:
        """
        This class will construct the gis gui.
        We pass in the collection of MyShape objects.
        """
        def __init__(self, master, datasets):
            with open("provinces.txt",'r') as f2:
                prov_str = f2.read()
            prov_polygons = json.loads(prov_str)
            provs = []
            for f in prov_polygons['features']:
                provs.append(geometry.asShape(f['geometry']))
            self.bg = cascaded_union(provs)
            self.master = master
            self.datasets = datasets
            self.current_dataset = ""
            self.op_counter = 0
            self.op_stack = {}
            self.operation = 'N' # this holds a value to tell which operation is currently in progress
                                # M = Merge, I = Intermediate, G = Geocode, N = None
            self.master.title("SIMPLE GIS")

            # Set Button style
            s = ttk.Style()
            s.configure('Wait.TButton',foreground = 'red', state = 'disabled')
            s.configure('Go.TButton', foreground = 'green', state = 'active')

            # Declaring variables
            self.cb_datasets_source = []
            self.cb_datasets_source = [d for d in self.datasets]
            self.cb_op_data_source = []
            self.lb_features_source = StringVar()
            self.lb_feature_data_source = StringVar()
            self.dialog_text = StringVar()
            self.dialog_text.set('Messages will appear here.')

            # widget declarations
            self.frm_mainframe = ttk.Frame(self.master,
                                       )
            self.lbl_message = ttk.Label(self.master,
                                         font = ('Helvetica', 16),
                                         foreground = 'blue',
                                         textvariable = self.dialog_text)

            # Set up frames
            self.frm_data_pane_top = ttk.LabelFrame(self.frm_mainframe,
                                                    text = 'Dataset Explorer',
                                                    width = 40)
            self.frm_data_pane_middle = ttk.LabelFrame(self.frm_mainframe,
                                                       text = 'Feature Explorer',
                                                       width = 40)
            self.frm_data_pane_bottom = ttk.LabelFrame(self.frm_mainframe,
                                                       text = 'Feature Data',
                                                       width = 40)
            self.frm_functions = ttk.LabelFrame(self.frm_mainframe,
                                                text = 'Functions')

            #Set up widgets
                # Data selection and viewing
            self.lbl_ip_data = ttk.Label(self.frm_data_pane_top,
                                         text = 'Input Data:')
            self.cb_datasets = ttk.Combobox(self.frm_data_pane_top,
                                            height = 5,
                                            values = self.cb_datasets_source,
                                            width = 40)
            self.lbl_op_data = ttk.Label(self.frm_data_pane_top,
                                         text = 'Output Data:')
            self.cb_op_data = ttk.Combobox(self.frm_data_pane_top,
                                           height = 5,
                                           values = self.cb_op_data_source,
                                           width = 40,
                                           state = 'disabled')
            self.lb_features = Listbox(self.frm_data_pane_middle,
                                       height = 10,
                                       listvariable = self.lb_features_source,
                                       width = 40,
                                       state = 'disabled')
            self.lb_feature_data = Listbox(self.frm_data_pane_bottom,
                                           height = 10,
                                           listvariable = self.lb_feature_data_source,
                                           width = 40)
                # Functions
            self.btn_feature_display = ttk.Button(self.frm_data_pane_middle,
                                                  text = 'DISPLAY SELECTED',
                                                  style = 'Wait.TButton',
                                                  command = lambda: self.display(feature_name =
                                                                    self.lb_features.get(
                                                                    self.lb_features.curselection())))
            self.btn_confirm = ttk.Button(self.frm_data_pane_middle,
                                          text = 'CONFIRM SELECTED',
                                          style = 'Wait.TButton',
                                          state = 'disabled',
                                          command = lambda: self.confirm(self.lb_features.curselection()))
            self.btn_merge_polygons = ttk.Button(self.frm_functions,
                                                 width = 20,
                                                 cursor = 'hand1',
                                                 text = 'MERGE',
                                                 style = 'Wait.TButton',
                                                 command = self.merge_polys)
            self.btn_points_within_poly = ttk.Button(self.frm_functions,
                                                 width = 20,
                                                 cursor = 'hand1',
                                                 text = 'Ps in POLY',
                                                 style = 'Wait.TButton',
                                                 command = self.points_within_poly)
            self.btn_centroid = ttk.Button(self.frm_functions,
                                                 width = 20,
                                                 cursor = 'hand1',
                                                 text = 'CENTROID',
                                                 style = 'Wait.TButton',
                                                 command = self.centroid)
            self.btn_make_shp = ttk.Button(self.frm_functions,
                                                 width = 20,
                                                 cursor = 'hand1',
                                                 text = 'MAKE .SHP',
                                                 style = 'Wait.TButton',
                                                 command = self.make_shp)
            self.geocode = ttk.Button(self.frm_functions,
                                                 width = 20,
                                                 cursor = 'hand1',
                                                 text = 'GEOCODE',
                                                 style = 'Wait.TButton',
                                                 command = self.geocode)




            # widget placement
            self.lbl_message.grid(row = 0, column = 0)

            self.frm_mainframe.grid(row = 1, column = 0)
            self.frm_data_pane_top.grid(row = 0, column = 0, sticky = 'w')
            self.lbl_ip_data.grid(row = 0, column = 0, sticky = 'new')
            self.cb_datasets.grid(row = 0, column = 1, sticky = 'ew')
            self.lbl_op_data.grid(row = 0, column = 2, sticky = 'nw')
            self.cb_op_data.grid(row = 0, column = 3, sticky = 'new')

            self.frm_data_pane_middle.grid(row = 1, column = 0, sticky = 'ew')
            self.lb_features.grid(row = 0, column = 0, sticky = 'ew')
            self.btn_feature_display.grid(row = 1, column = 0, sticky = 'ew')
            self.btn_confirm.grid(row = 2, column = 0, sticky = 'ew')

            self.frm_data_pane_bottom.grid(row = 2, column = 0, sticky = 'ew')
            self.lb_feature_data.grid(row = 0, column = 0, sticky = 'ew')

            self.frm_functions.grid(row = 3, column = 0,
                                    columnspan = 1)
            self.btn_merge_polygons.grid(row = 0, column = 0)
            self.btn_points_within_poly.grid(row = 0, column = 1)
            self.btn_centroid.grid(row = 0, column = 2)
            self.btn_make_shp.grid(row = 0, column = 3)
            self.geocode.grid(row = 0, column = 4)

            # event handling
            _ = self.cb_datasets.bind("<<ComboboxSelected>>", self.dataset_cb_newselection)
            _ = self.lb_features.bind("<<ListboxSelect>>", self.feature_lb_newselection)
            _ = self.frm_functions.bind("<<Button1>>", self.check_op_stack)


            # functions
        def check_op_stack(self):
            if self.op_stack:
                self.cb_op_data.configure(state = 'normal')

        def display(self, feature_name = None, *args):
            # allows function to be used by multiple processes, first option (when a feature_name is passed)
            # is for viewing data, second option is for viewing created geometries
            if feature_name:
                geom = self.datasets[self.current_dataset].features[feature_name][0]
                if geom.geom_type != ('Polygon' or 'MultiPolygon'):
                    self.dialog_text.set('This geometry is invalid. Please use a different dataset')
                    pass
                geom = cascaded_union(geom) #to dissolve multipolygons
                geom_bdry = geom.boundary
                minx, miny, maxx, maxy = self.bg.bounds
                w, h = maxx - minx, maxy - miny
                fig = plt.figure(1, figsize = (5, 5), dpi = 180, frameon = False)
                ax = fig.add_subplot(111)
                ax.set_xlim(minx,maxx)
                ax.set_ylim(miny,maxy)
                for poly in self.bg:
                    bg_patch = PolygonPatch(poly, fc = 'lightsage', ec = 'k', alpha = 1)
                    ax.add_patch(bg_patch)

                if geom.geom_type == 'MultiPolygon':
                    for poly in geom:
                        patch = PolygonPatch(poly, fc= 'teal', ec='navy', alpha = 0.5)
                        ax.add_patch(patch)
                else:
                    patch = PolygonPatch(geom, fc='teal', ec='navy', alpha = 0.5)
                    ax.add_patch(patch)
                plt.show()
            else:
                geom = args[0]
                name = args[1]
                geom = cascaded_union(geom) #to dissolve multipolygons
                minx, miny, maxx, maxy = self.bg.bounds
                w, h = maxx - minx, maxy - miny
                fig = plt.figure(1, figsize = (5, 5), dpi = 180, frameon = False)
                ax = fig.add_subplot(111)
                ax.set_xlim(minx,maxx)
                ax.set_ylim(miny,maxy)
                for poly in self.bg:
                    bg_patch = PolygonPatch(poly, fc = 'lightsage', ec = 'k', alpha = 1)
                    ax.add_patch(bg_patch)
                if geom.geom_type == 'MultiPolygon':
                    for poly in geom:
                        patch = PolygonPatch(poly, fc= 'teal', ec='navy', alpha = 0.5)
                        ax.add_patch(patch)
                else:
                    patch = PolygonPatch(geom, fc='teal', ec='navy', alpha = 0.5)
                    ax.add_patch(patch)
                plt.title(name)
                plt.show()

        def dataset_cb_newselection(self, event):
            self.lb_feature_data_source.set([]) # wipe the feature data source
            self.current_dataset = event.widget.get()
            self.dialog_text.set("You have chosen - " + self.current_dataset.capitalize())
            self.update_feature_explorer(self.current_dataset)

        def update_feature_explorer(self, dataset_name):
            item_list = list(self.datasets[dataset_name].features.keys())
            self.lb_features_source.set(item_list)
            self.lb_features.configure(state = 'normal')

        def feature_lb_newselection(self, event):
            owner = event.widget
            if self.operation != 'N':
                pass
            else:
                self.value_of_combo = owner.get(owner.curselection())
                self.dialog_text.set("You have chosen - " + self.value_of_combo.capitalize())
                self.update_feature_data_explorer(self.value_of_combo)

        def update_feature_data_explorer(self, feature_name):
            properties = self.datasets[self.current_dataset].features[feature_name][1]
            op_list = ["{} : {}".format(k,v) for k, v in properties.items()]
            self.lb_feature_data_source.set(op_list)
            self.lb_feature_data.configure(state = 'normal')

        def confirm(self, data_lines): # this acts as a confirm for selection of data, and returns to
                                 # origin function with the data selected
            if self.operation == 'M':
                items = [self.lb_features.get(i) for i in data_lines]
                data = [self.datasets[self.current_dataset].features[feature_name][0]
                        for feature_name in items]
                self.merge_polys(data, items)
            #elif

        def merge_polys(self, data = None, *args):
            # allows the feature listbox to become enabled for multiple selections
            # and waits for items to be selected and confirmed
            if data == None:
                self.lb_feature_data_source.set([])
                self.btn_feature_display.configure(state = 'disabled')
                self.lb_features.configure(selectmode = 'multiple')
                self.operation = 'M'
                self.btn_confirm.configure(state = 'normal')
                self.dialog_text.set('Please confirm when you have selected your items')
                pass
            else: # this is the return from the confirm button
                merged_geom = cascaded_union(data)
                name = 'merged' + str(self.op_counter)
                self.display(None, merged_geom, name)
                self.make_merged_shp(merged_geom, name = args[0]) # this makes a shapefile
                self.btn_confirm.configure(state = 'disabled')
                self.lb_features.configure(selectmode = 'single')
                self.btn_feature_display.configure(state = 'normal')
                self.btn_confirm.configure(state = 'disabled')
                self.points_within_poly(merged_geom)
                self.centroid(merged_geom)


        def points_within_poly(self, poly):
            if 'dit:geonames_pop_5000' in self.datasets.keys():
                self.current_dataset = 'dit:geonames_pop_500'
            elif 'dit:geonames_populated' in self.datasets.keys():
                self.current_dataset = 'towns'
            else:
                self.dialog_text.set('Please return to last GUI and pick a point dataset:')
                pass
            points = self.datasets[self.current_dataset].features
            print(len(points))
            contained_points = {}
            for k,v in points.items():
                if poly.contains(v[0]):
                    contained_points[k] = v
            print(len(contained_points))

        def centroid(self, geom):
            pass

        def make_shp(self):
            pass


        def make_merged_shp(self, data, name, crs = None):
            self.op_counter += 1
            geom_type = data.geom_type
            a_schema = {'geometry': geom_type,
                        'properties': {'name':'str'}
                       }
            filename = 'merged' + str(self.op_counter) + ".shp"
            path = os.path.join('op_data',filename)
            obj_name = 'merged' + str(self.op_counter)
            if not crs:
                my_crs = self.datasets[self.current_dataset].crs
                crs = from_epsg(my_crs['properties']['code'])
            with fiona.open(path,
                            'w',
                            driver= 'ESRI Shapefile',
                            crs= crs,
                            schema= a_schema) as c:
                c.write({
                    'properties':{'name':obj_name},
                      'geometry':geometry.mapping(data)})



        def geocode(self):
            pass


if __name__ == main():
    main()







