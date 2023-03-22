# -*- coding: utf-8 -*-
import dash
import os
import sys
import flask
import time
import folium
from figure_base import figure_base as fb
import numpy as np
import pandas as pd
from chatgpt_api import chatbot
from folium import plugins
from geopy.distance import distance, geodesic

from dash_iconify import DashIconify
import dash_mantine_components as dmc
from plotly import graph_objects as go
from plotly.subplots import make_subplots
import dash_leaflet as dl
from folium.plugins import MeasureControl
from dash import no_update
import dash_leaflet.express as dlx
from folium.plugins import MarkerCluster
import geopandas as gpd
from shapely import geometry
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, State, Input, Output
import dash_bootstrap_components as dbc
#from dash_bootstrap_components._components.Container import Container

import plotly.express as px

geo_df = pd.read_csv("earthquake.csv", index_col=0, low_memory=True)
geo_df.drop_duplicates(keep='first', inplace=True)
geo_df = geo_df.dropna(subset=['City'])
geo_df = geo_df.sort_values(by = 'City')
geo_df.reset_index(inplace=True, drop = True)
## downcasting loop
for column in geo_df:
    if geo_df[column].dtype == 'float64':
        geo_df[column]=pd.to_numeric(geo_df[column], downcast='float')
    if geo_df[column].dtype == 'int64':
        geo_df[column]=pd.to_numeric(geo_df[column], downcast='integer')

## dropping an unused column
geo_df = geo_df.drop('geometry',axis =1)

mapbox_access_token = 'pk.eyJ1IjoiY2V5aHVuMjA4NiIsImEiOiJjbGZiaTJ4MXoya2diM3RvMTBic3N3Y3A5In0._4OoIx3hlf1l0eEeiCnSRQ'


BS =[ "https://stackpath.bootstrapcdn.com/bootstrap/4.5.1/css/bootstrap.min.css",
    {
        'href': 'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
        'rel': 'stylesheet',
        'integrity': 'sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf',
        'crossorigin': 'anonymous'
    }
]

def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)
    return os.path.join(datadir, filename)


# graph capabilities
config = { 'displayModeBar': True,
           'scrollZoom': True,
           'displaylogo': False,
           'modeBarButtonsToAdd': [
               'drawopenpath',
               'drawcircle',
               'eraseshape',
               'select2d',
           ] }

# Initialize the app
app = dash.Dash(__name__,external_stylesheets=BS,suppress_callback_exceptions=True, assets_folder=find_data_file('assets/'),update_title='Loading...',
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=2.0, maximum-scale=1.2, minimum-scale=0.5'}],
                )
server = app.server

app.config.suppress_callback_exceptions = True

PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"




def darkModeToggle():
    return html.Div(
        dmc.Switch(
            offLabel=DashIconify(icon="radix-icons:moon", width=20),
            onLabel=DashIconify(icon="radix-icons:sun", width=20),
            size="xl",
            id='themeSwitch',
            sx={'paddingTop':'2px'},
            persistence=True,
            style={'marginLeft':'155px'}
        ),
    id='themeSwitchHolder')



search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(id = 'chatgptquestion',type="search", placeholder="Search")),
        dbc.Col(
            dbc.Button ("Search",id='search',
                 color="primary", className="ms-2", n_clicks=0
            ),


        width="auto",),
        html.Div (
            [
                dbc.Modal (
                    [
                        dbc.ModalHeader ("ChatGPT"),
                        dbc.ModalBody (
                            html.Div (
                                [dcc.Loading(id="loading-1",type="circle",children = [
                                    html.Div (id="conversation-container",children = [], className="conversation-container"),
                                    html.Div (
                                        [
                                            dcc.Input (
                                                id="user-input",
                                                type="text",
                                                placeholder="Chat with ChatGPT",
                                                style={'width': '43rem','height': '5rem', 'backgroundColor':'lightgray', 'textColor': 'Black'},
                                                className="user-input",
                                            ),
                                            dbc.Button ("Send", id="submit-button", color='primary', className="me-1"),
                                        ],
                                        className="input-container",
                                    ),

                                ])],
                                id = 'QA_values', className="chat-container",
                            )
                        ),
                    ],
                    id="modal-lg",
                    is_open=False,
                    size="lg",
                    style={'height': "60vh"},
                    scrollable=True
                ),
            ]
        ),
        dmc.MantineProvider ([

                                darkModeToggle (),
                            ],
                                id='themeHolder',
                                theme={ "colorScheme": "light" },
                                withNormalizeCSS=True,
                                withGlobalStyles=True,
                                withCSSVariables=True,


                            )

    ],
    className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                        dbc.Col(dbc.NavbarBrand("Turkish Earthquake Chart", className="ms-2")),


                    ],
                    align="center",
                    className="g-0",
                ),
                #href="https://plotly.com",
                style={"textDecoration": "none"},
            ),
            dbc.Collapse(
                search_bar,
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),



        ]
    ),
    color="dark",
    dark=True,
    style={'align': 'flex-start'}
)

@app.callback(
    Output('themeHolder','theme'),
    Input('themeSwitch','checked'),
)
def darkMode(checked):
    if checked:
        return {"colorScheme": "dark"}
    else:
        return {"colorScheme": "light"}

# add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open



sidebar = html.Div(
    [
        html.Div(
            [
                html.H2("Parameters", style={"color": "white"}),
            ],
            className="sidebar-header",
        ),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="fas fa-home me-2"), html.Span("Dashboard")],
                    href="/",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-chart-bar fa-fw fa-lg"),
                        html.Span("Data"),
                    ],
                    href="/data",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-map fa-fw fa-lg"),
                        html.Span("Map"),
                    ],
                    href="/map",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fas fa-map-marker fa-fw fa-lg"),
                        html.Span("More Maps"),
                    ],
                    href="/more_maps",
                    active="exact",
                ),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    className="sidebar",
)

chart_type_options = ["satellite-streets","carto-darkmatter", "carto-positron", "open-street-map",
                      "stamen-terrain", "stamen-toner", "stamen-watercolor", "white-bg",
                      "basic", "streets", "outdoors", "light", "dark", "satellite",
                      ]

chart_type_folium = ["OpenStreetMap", "Stamen", "CartoDB" ]

# Layout design
app.layout = html.Div(
    children = [
        navbar,
        #sidebar,
        html.Div(id='textarea-output', style={'whiteSpace': 'pre-line', 'marginLeft':'35px'}),


        html.Div(
            [
                dash.page_container
            ],
            className="content",
        ),
        html.Div(id='blank-output', children = []),

        dcc.Loading (dcc.Store (id="store"), fullscreen=True, type="dot"),
        dbc.Row([
            dbc.Col (

                html.Div (id = 'mapbox1', children = [
                    html.Div(id='questions_val', children=[], style={'display': 'None'}),
                    html.Div(id='response_val', children=[], style={'display': 'None'}),
                    dcc.Dropdown (id='valcity',
                                  options=[{ 'label': i, 'value': i }
                                           for i in geo_df['City'].unique()],
                                  multi=False,
                                  style={ 'cursor': 'pointer', 'margin': '5px', 'borderRadius': '1rem','width' : '30rem' },
                                  clearable=True,
                                  searchable=True,
                                  placeholder='Select City ...',

                                  ),
                    dcc.Dropdown (id='valtown',
                                  options=[],
                                  multi=False,
                                  style={ 'cursor': 'pointer', 'margin': '5px', 'borderRadius': '1rem', 'width' : '30rem' },
                                  clearable=True,
                                  searchable=True,
                                  placeholder='Select Town ...',

                                  ),
                    dcc.Dropdown (id='radiograph',
                                  options=[{ 'label': i, 'value': i }
                                           for i in ['mapbox', 'density', 'folium']],
                                  value='mapbox',
                                  multi=False,
                                  style={ 'cursor': 'pointer', 'margin': '5px', 'borderRadius': '1rem', 'width' : '30rem' },
                                  clearable=True,
                                  searchable=True,
                                  placeholder='Select Map type ...',

                                  ),

                    html.Div(id = 'third_ligne_dd', children = [
                                  dcc.Dropdown (id='date_type',
                                  options=[],
                                  style={ 'cursor': 'pointer', 'margin':'2px', 'width' : '20rem', 'borderRadius': '1rem' },
                                  clearable=True,
                                  placeholder='Select datetime ...',
                                  ),
                        dcc.Dropdown (id='chart_type',
                                  options=[{ 'label': i, 'value': i }
                                           for i in chart_type_options],

                                  style={ 'cursor': 'pointer', 'margin':'2px', 'width' : '20rem', 'borderRadius': '1rem' },
                                  clearable=True,
                                  placeholder='Select chart type ...',
                                  ),
                        dcc.RadioItems(id="coordinate",
                               options=[
                                   {'label': 'Coordinate', 'value': 'coordinate'},
                                   ],
                               labelClassName='groupgraph2',
                               labelStyle={'margin': '10px'},
                               inputStyle={'margin': '10px'}
                               )

                    ], className='dropdown-header'),
                    dcc.Graph (id="graph1",config = config),
                    html.Div(id='folium_graph'),


                ]),
                width={ "size": 6 },
            ),
            dbc.Col ([
                html.Div (id = 'leaflet'),
                dcc.Graph(id="graph2",config = config)],
                width={ "size": 6 },style={'marginTop':'24vh', 'backgroundColor': 'black'}
            )
        ],
        )
    ],
)



@app.callback(
    [Output("chart_type", "options"),Output("chart_type", "value")],
    Input("radiograph", "value"),
)

def chart_options(value1):
    if value1 == None:
        raise PreventUpdate
    if value1 == 'mapbox' or value1 == 'density':
        return [{ 'label': i, 'value': i } for i in chart_type_options], 'satellite-streets'
    return [{ 'label': i, 'value': i } for i in chart_type_folium ],'OpenStreetMap'


@app.callback(
    Output("modal-lg", "is_open"),
    Input("search", "n_clicks"),
    State("modal-lg", "is_open"),
)

def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open

def create_modal(x,question, response):
    lis = []
    for i in range (x):

         lis.append(html.Div ([
                html.P (question[i], style={'color': 'black'}),
                html.Hr (),
                html.P (response[i], style={'width':'50rem','color': 'black'}),
                html.Hr () ]))
    return lis


@app.callback(
    [Output("conversation-container", "children"),Output("questions_val", "children"),Output("response_val", "children")],
    [Input("chatgptquestion", "value"),
    Input("search", "n_clicks"),Input("submit-button", "n_clicks")],
     [State("user-input", "value"), State("questions_val", "children"),State("response_val", "children"),State("modal-lg", "is_open")]
)

def chatgpt_conversation(value1, nc, nc2, value2, question, response, is_open ):
    ctx = dash.callback_context
    button_click = ctx.triggered[0]["prop_id"].split (".")[0]
    print(response)



    if button_click == 'search' :
        question.append(value1)
        response.append(chatbot(value1))

        x = len(question)
        return create_modal (x, question, response), question, response

    if button_click == 'submit-button' :


        question.append(value2)
        final_val = ''.join(i for i in question)

        response.append(chatbot (final_val))


        x = len(question)
        return create_modal (x, question, response), question, response

    else:
        raise PreventUpdate






@app.callback(Output("date_type", "options"),
              [Input("valcity", "value"),
               Input("valtown", "value")])
def update_graph(value1,value2):
    print('render4')


    if value1 == None and value2 == None :
        raise PreventUpdate

    if value1 != None and value2 != None :
        city_df = geo_df[geo_df['City'] == value1]
        town_df = city_df[city_df['Town'] == value2]
        date_df = town_df['date'].sort_values(ascending=False).unique()

    if value1 != None and value2 == None :
        city_df = geo_df[geo_df['City'] == value1]
        date_df = city_df['date'].sort_values(ascending=False).unique()
    return [{ 'label': i, 'value': i } for i in date_df]





@app.callback(Output("valtown", "options"),
              [Input("valcity", "value"),
               Input("date_type", "value")])
def update_graph2(value1,value2):
    print('render5')

    if value1 == None and value2 == None :
        raise PreventUpdate

    if value1 != None and value2 != None :
        city_df = geo_df[geo_df['City'] == value1]
        date_df = city_df[city_df['date'] == value2]
        town_df = date_df['Town'].sort_values(ascending=True).unique()

    if value1 != None and value2 == None :
        city_df = geo_df[geo_df['City'] == value1]
        town_df = city_df['Town'].sort_values(ascending=True).unique()
    return [{ 'label': i, 'value': i } for i in town_df]



@app.callback([Output("graph1", "figure"),Output("graph1", "style"),
               Output("folium_graph", "children"), Output("graph2", "figure")],
              [Input("valcity", "value"),
               Input("valtown", "value"),
               Input("date_type", "value"),
               Input("chart_type", "value"),
               Input("radiograph", 'value')])
def update_graph3(value1,value2, value3, value4, radio):
    print('render6')

    #if value1 == None or value2 == None or value3 == None or value4 == None:
        #raise PreventUpdate

    if value1 != None and value2 != None and value3 != None :
        df = geo_df[geo_df['City'] == value1]
        df = df[df['Town'] == value2]
        df = df[df['date'] == value3]

    if value1 != None and value2 == None and value3 != None :
        df = geo_df[geo_df['City'] == value1]
        #df = df[df['Town'] == value2]
        df = df[df['date'] == value3]

    if value1 != None and value2 != None and value3 == None :
        df = geo_df[geo_df['City'] == value1]
        df = df[df['Town'] == value2]
        #df = df[df['date'] == value3]

    if value1 != None and value2 == None and value3 == None :
        df = geo_df[geo_df['City'] == value1]
        #df = df[df['Town'] == value2]
        #df = df[df['date'] == value3]

    if value1 == None and value2 == None and value3 != None :
        df = geo_df[geo_df['date'] == value1]
        #df = df[df['Town'] == value2]
        #df = df[df['date'] == value3]


    if value1 == None and value2 == None and value3 == None :
        df = geo_df


    min = abs(float(df['magnitude'].min()))

    max = float(df['magnitude'].max())



    px.set_mapbox_access_token (mapbox_access_token)

    if radio == 'density':

        fig = px.density_mapbox (
                df,
                lat="lat",
                lon="long",
                hover_name="City",
                hover_data=["date","time", "magnitude"],
                range_color= [min, max],
                color_continuous_scale=px.colors.sequential.Viridis,
                zoom=8,
                radius=25,
                height=440,

            )

        fig.update_layout (mapbox_style=value4)
        fig.update_layout (margin={ "r": 0, "t": 0, "l": 0, "b": 0 },)
        fig.update_layout (mapbox_bounds={ "west": 20, "east": 48, "south": 30, "north": 45 })


        return fig,{'visibility':'visible'},{},fb(df, value1)

    if radio == 'mapbox' :
        fig = px.scatter_mapbox (
            df,
            lat="lat",
            lon="long",
            hover_name="City",
            hover_data=["date", "time", "magnitude"],
            range_color=[min, max],
            color_continuous_scale=px.colors.sequential.Viridis,
            zoom=8,
            height=440,

        )

        fig.update_layout (mapbox_style=value4)
        fig.update_layout (margin={ "r": 0, "t": 0, "l": 0, "b": 0 }, )
        fig.update_layout (mapbox_bounds={ "west": 20, "east": 48, "south": 30, "north": 45 })

        return fig,{'visibility':'visible'}, {}, fb(df, value1)



    if radio == 'folium':
        my_coordinates = [(row['lat'], row['long']) for index, row in df.iterrows ()][0]
        m = folium.Map([39.849, 32.849], zoom_start=5, tiles=value4, attr='my_own_folium')

        print(my_coordinates)





        from jinja2 import Template
        from folium.map import Marker

        tmpldata = """<!-- monkey patched Marker template -->
        {% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.marker(
                {{ this.location|tojson }},
                {{ this.options|tojson }}
            ).addTo({{ this._parent.get_name() }}).on('click', onClick);
        {% endmacro %}
        """

        Marker._mytemplate = Template (tmpldata)

        def myMarkerInit(self, *args, **kwargs):
            self.__init_orig__ (*args, **kwargs)
            self._template = self._mytemplate

        Marker.__init_orig__ = Marker.__init__
        Marker.__init__ = myMarkerInit


            # add a marker for each city

        from folium.plugins import MarkerCluster

        # create a feature group for markers
        marker_group = MarkerCluster ()

        # loop through the first 10 rows of the dataframe
        try :

            for index, row in df.head (10).iterrows ():
                marker1 = folium.Marker (location=[row['lat'], row['long']], popup=row['City'],
                                        icon=folium.Icon (color='red'))
                marker1.add_to (marker_group)
        except RecursionError as err:
            if err.args[0] != 'maximum recursion depth exceeded in comparison':
                # different type of runtime error
                raise
            print ('Sorry but this marker was not able to finish '
                   'analyzing: {}'.format (err.args[0]))

        # add the marker group to the map
        marker_group.add_to (m)

        el = folium.MacroElement ().add_to (m)
        el._template = Template ("""
            {% macro script(this, kwargs) %}
            function copy(text) {
                var input = document.createElement('textarea');
                input.innerHTML = text;
                document.body.appendChild(input);
                input.select();
                var result = document.execCommand('copy');
                document.body.removeChild(input);
                return result;
            };

            function getInnerText( sel ) {
                var txt = '';
                $( sel ).contents().each(function() {
                    var children = $(this).children();
                    txt += ' ' + this.nodeType === 3 ? this.nodeValue : children.length ? getInnerText( this ) : $(this).text();
                });
                return txt;
            };

            function onClick(e) {
               var popup = e.target.getPopup();
               var content = popup.getContent();
               text = getInnerText(content);
  
               copy(text);
            };
            {% endmacro %}
        """)

        plugins.MiniMap ().add_to (m)
        plugins.Geocoder ().add_to (m)

        # mesafeyi hesaplama
        #if marker1 is not None and marker2 is not None:
        #    dist = geodesic ((marker1.location[0], marker1.location[1]), (marker2.location[0], marker2.location[1])).km
        #    print (f"Mesafe: {dist:.2f} km")



        marker2 = folium.Marker (
            location=[38.0, 40.0],
            popup=f'<p id="latlon">{38.0}, {40.0}</p>',
            className='leaflet-marker-draggable',

            draggable=True
            ).add_to (m)

        el1 = folium.MacroElement ().add_to (m)
        el1._template = Template ("""
            {% macro script(this, kwargs) %}
            function copy(text) {
                var input = document.createElement('textarea');
                input.innerHTML = text;
                document.body.appendChild(input);
                input.select();
                var result = document.execCommand('copy');
                document.body.removeChild(input);
                return result;
            };

            function onClick(e) {
               var lat = e.latlng.lat; 
               var lng = e.latlng.lng;
               var newContent = '<p id="latlon">' + lat + ', ' + lng + '</p>';
               e.target.setPopupContent(newContent);
               e.target.setLatLng([lat,lng]);
               lat, lng = e.target.location;
               
               copy(lat + ', ' + lng);
            };
            {% endmacro %}
        """)

        # İşaretçinin konumunu güncellemek için bir fonksiyon oluşturun
        def update_marker_location(e):
            lat, lng = e['target']['_latlng']
            marker2.set_location ([lat, lng])

        # İşaretçinin sürükleme olayına bir dinleyici ekleyin
        marker2.add_child (folium.Popup ("Initial location: {}, {}".format (marker2.location[0], marker2.location[1])))
        m.get_root ().html.add_child (folium.Element ("""
        <script>
            var marker = document.getElementsByClassName('leaflet-marker-draggable')[0];
            marker.addEventListener('dragend', function(e) {
                window.dispatchEvent(new CustomEvent('markerMoved', { detail: e }));
            });
        </script>
        """))

        # İşaretçinin sürükleme olayı tamamlandığında tetiklenecek özel bir etkinlik oluşturun
        m.get_root ().html.add_child (folium.Element ("""
        <script>
            window.addEventListener('markerMoved', function(e) {
                var eventDetail = e.detail;
                updateMarkerLocation(eventDetail);
            });
        </script>
        """))

        from folium.plugins import MousePosition

        formatter = "function(num) {return L.Util.formatNum(num, 3) + ' º ';};"
        MousePosition (
            position="topright",
            separator=" | ",
            empty_string="NaN",
            lng_first=True,
            num_digits=20,
            prefix="Coordinates:",
            lat_formatter=formatter,
            lng_formatter=formatter,
        ).add_to (m)

        print(marker2.location[0])


        m.save ('ceyhun.html')





        return {},{'display': 'None' },html.Div(html.Iframe (id='map',
               srcDoc=open ('ceyhun.html', 'r').read (), width='750rem', height='400rem'), style={'marginTop':'2px'}),fb(df, value1)

    else: no_update








@app.callback(Output('blank-output', 'children'), [Input("graph1", "clickData")])
def display_click_data(click):
    if click:
        lat = click['points'][0]['lat']
        lon = click['points'][0]['lon']
        print("Tıklanan noktanın enlemi: ", click['points'][0]['lat'])
        print("Tıklanan noktanın boylamı: ", click['points'][0]['lon'])
        return (lat,lon)

@app.callback(
    Output('textarea-output', 'children'),
    Input('blank-output', 'children')
)
def update_coordinate_output(value):
    return 'You have entered: \n{}'.format(value)

if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8050)