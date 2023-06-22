# -*- coding: utf-8 -*-
import dash
import os
import sys
import subprocess
import json
import flask
from dash import dash_table
import time
from figure_base import figure_base as fb
import numpy as np
import pandas as pd
from chatgpt_api import chatbot
from dash.long_callback import DiskcacheLongCallbackManager
from dash_iconify import DashIconify
import dash_mantine_components as dmc
import dash_leaflet as dl
from dash import no_update
import dash_deck
import pydeck as pdk
#import dash_leaflet.express as dlx
from dash.exceptions import PreventUpdate
from dash import Dash,dcc, html, State, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import re

# get data from csv file which was taken from http://www.koeri.boun.edu.tr/
geo_df = pd.read_csv("earthquake.csv", index_col=0, low_memory=True)
geo_df.drop_duplicates(keep='first', inplace=True)
geo_df = geo_df.sort_values(by = 'City')
geo_df.reset_index(inplace=True, drop = True)
geo_df['id'] = [i+1 for i in range(len(geo_df))]
geo_df['lon'] = geo_df['long']




## downcasting loop
for column in geo_df:
    if geo_df[column].dtype == 'float64':
        geo_df[column]=pd.to_numeric(geo_df[column], downcast='float')
    if geo_df[column].dtype == 'int64':
        geo_df[column]=pd.to_numeric(geo_df[column], downcast='integer')


mapbox_access_token = 'pk.eyJ1IjoiY2V5aHVuMjA4NiIsImEiOiJjbGZiaTJ4MXoya2diM3RvMTBic3N3Y3A5In0._4OoIx3hlf1l0eEeiCnSRQ'

## Diskcache
import diskcache
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)


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
           "responsive" : True,
           'modeBarButtonsToAdd': [
               'drawopenpath',
               'drawcircle',
               'eraseshape',
               'select2d',
           ] }

# Initialize the app
app = dash.Dash(__name__,external_stylesheets=BS,suppress_callback_exceptions=True, assets_folder=find_data_file('assets/'),update_title='Loading...',
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=2.0, maximum-scale=1.2, minimum-scale=0.5'}],
                long_callback_manager=long_callback_manager)
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

### LAYOUT
search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(id = 'chatgptquestion',type="search",inputMode=True, placeholder="Chat with CHATGPT")),
        dbc.Col(
            dbc.Button ("Start",id='search',
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
                                [
                                    html.Div (id="conversation-container",children = [], className="conversation-container"),

                                    html.Div (
                                        [
                                            dcc.Input (
                                                id="user-input",
                                                type="text",
                                                placeholder="Chat with ChatGPT",
                                                style={'width': '43rem','height': '5rem', 'backgroundColor':'black'},

                                                className="user-input",
                                            ),
                                            dbc.Col([dbc.Button ("Send", id="submit-button", color='primary', className="me-1"),
                                                     dbc.Button ("Run code in Python", id='run-py',
                                                        color="warning", className="me-1", n_clicks=0
                                                        ),], style={'display':'Flex', 'flexDirection': 'column'}),


                                        ],
                                        className="input-container",
                                    ),
                                    html.Div (id='textarea-container'),
                                ],
                                id = 'QA_values', className="chat-container",
                            ),
                        ),
                    ],
                    id="modal-lg",
                    is_open=False,
                    size="lg",
                    style={'height': "70vh"},
                    scrollable=True,

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
###########################################################################################


@app.callback(
    Output('textarea-container', 'children'),
    [Input('run-py', 'n_clicks')]
)
def show_textarea(n_clicks):
    if n_clicks > 0:
        return html.Div([
            dcc.Textarea(id='code-input', placeholder='Paste your Python code here...', rows=20, cols=80),
            dbc.Button('Run', id='run-code', color= 'success',n_clicks=0),
            html.Div(id='output-container')
        ])
    else:
        return html.Div()



# Define the callback to execute the code when the 'run-code' button is clicked
@app.callback(
    Output('output-container', 'children'),
    [Input('run-code', 'n_clicks')],
    [State('code-input', 'value')]
)
def execute_python_code(n_clicks, code):

    ctx = dash.callback_context
    button_click = ctx.triggered[0]["prop_id"].split (".")[0]

    if button_click== 'run-code' and code:
        try:
            result = subprocess.run(['python', '-c', code], capture_output=True, text=True)
            if result.returncode == 0:
                return html.Pre(result.stdout)
            else:
                return html.Pre(result.stderr)
        except Exception as e:
            return html.Pre(str(e))
    else:
        return html.Pre()







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
    [Output('themeHolder','theme'),Output('graph_theme','style')],
    Input('themeSwitch','checked'),
)
def darkMode(checked):
    if checked:
        return {"colorScheme": "dark"}, { 'backgroundColor': '#1a1b1e' }
    else:
        return {"colorScheme": "light"},{ 'backgroundColor': 'white' }

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




chart_type_options = ["satellite-streets","carto-darkmatter", "carto-positron", "open-street-map",
                      "stamen-terrain", "stamen-toner", "stamen-watercolor", "white-bg",
                      "basic", "streets", "outdoors", "light", "dark", "satellite",
                      ]

chart_type_leaflet = ["OpenStreetMap"]

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

        dcc.Loading (dcc.Store (id="store"), fullscreen=True, type="dot"),
        dbc.Row([
            dbc.Col (

                html.Div (id = 'mapbox1', children = [
                    html.Div(id='questions_val', children=[], style={'display': 'None'}),
                    html.Div(id='response_val', children=[], style={'display': 'None'}),
                    html.Div (id='questions_val_file', children=[], style={ 'display': 'None' }),
                    html.Div (id='response_val_file', children=[], style={ 'display': 'None' }),
                    html.Div(id='leaflet_click_data', children=[], style={'display': 'None'}),
                    dcc.Dropdown (id='valcity',
                                  options=[{ 'label': i, 'value': i }
                                           for i in geo_df['City'].unique()],
                                  multi=False,
                                  style={ 'cursor': 'pointer', 'margin': '2px', 'borderRadius': '1rem','width' : '32rem' },
                                  clearable=True,
                                  searchable=True,
                                  placeholder='Select City ...',

                                  ),
                    dcc.Dropdown (id='valtown',
                                  options=[],
                                  multi=False,
                                  style={ 'cursor': 'pointer', 'margin': '2px', 'borderRadius': '1rem', 'width' : '32rem' },
                                  clearable=True,
                                  searchable=True,
                                  placeholder='Select Town ...',
                                  ),
                    dcc.Dropdown (id='date_type',
                                  options=[],
                                  style={ 'cursor': 'pointer', 'margin': '2px', 'borderRadius': '1rem',
                                          'width': '32rem' },
                                  clearable=True,
                                  placeholder='Select datetime ...',
                                      )

                ]),
                width={ "size": 3, 'offset':1 },
            ),]),
            dbc.Row([
                dbc.Col([
                        dcc.Dropdown (id='radiograph',
                                  options=[{ 'label': i, 'value': i }
                                           for i in ['scatter', 'density', 'hexagon_layer']],
                                  value='scatter',
                                  multi=False,
                                  style={ 'cursor': 'pointer', 'marginLeft': '5rem',
                                              'marginTop': '2px',
                                              'marginDown': '5px','width': '15rem',
                                              'borderRadius': '1rem' },
                                  clearable=True,
                                  searchable=True,
                                  placeholder='Select Map type ...',

                                  ),
                     ],width={ "size": 3, }),
                dbc.Col([
                        dcc.Dropdown (id='chart_type',
                                      options=[],

                                      style={ 'cursor': 'pointer', 'marginLeft': '-19px',
                                              'marginRight': '2px', 'marginTop': '2px',
                                              'marginDown': '5px', 'width': '15rem',
                                              'borderRadius': '1rem' },
                                      clearable=True,
                                      placeholder='Select chart type ...',
                                      ),


                ],width={ "size": 3,  }),

            ]),
            dbc.Row([
                    dbc.Col([
                        dcc.Slider (-180, +180,id='slider-bearing', value=-27,
                                    marks=None,tooltip={"placement": "bottom", "always_visible": True}, updatemode='drag')


                ],width={ "size": 3,  }),
                    dbc.Col([
                        dcc.Slider (-180, +180,id='slider-pitch', value=40,
                                    marks=None,tooltip={"placement": "bottom", "always_visible": True},updatemode='drag')


                ],width={ "size": 3,  })
            ]),
            dbc.Row([
                dbc.Col([dcc.Graph (id="graph1",config = config),
                        html.Div(id='leaflet_graph')],width={ "size": 6 }),
                dbc.Col (id = 'graph_theme',children = [
                    dcc.Graph(id="graph2",config = config, style={'visibility':'hidden'})],
                    width={ "size": 6})
        ],justify="around"),

    ],
)
#=============================================================================================================


## CHART TYPE DROPDOWN
@app.callback(
    [Output("chart_type", "options"),Output("chart_type", "value")],
    Input("radiograph", "value"),
)

def chart_options(value1):
    if value1 == None:
        raise PreventUpdate
    if value1 == 'scatter' or value1 == 'density':
        return [{ 'label': i, 'value': i } for i in chart_type_options], 'satellite-streets'
    return [],[]
#=============================================================================================================


@app.callback(
    Output("modal-lg", "is_open"),
    Input("search", "n_clicks"),
    State("modal-lg", "is_open"),
)

def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open


# CHATGPT CONVERSATION

def create_modal(x, question, response):
    lis = []



        # Add your logic here to determine whether the response should be displayed as code or explanation

    for i in range(2, x):

        # Define the regex pattern
        pattern = r"code:\n(.*?)\n| ```python:\n(.*?)\n```"
        code = ''


        response_html = dcc.Loading ([
                            html.Div(
                                children=[
                                    # Explanation as plain text
                                    html.Div(
                                        children=html.Code(response[i]), style={'white-space': 'pre-wrap', 'overflow': 'auto','width': '60vh','padding': '10px','margin': '10px'}
                                    ),
                                    # Code as code snippet
                                    html.Div(
                                        children=html.Code(html.Pre(children=code,

                                            style={ 'background-color': '#f8f8f8', 'padding': '10px','margin': '10px',
                                                    'border': '1px solid #ddd', 'display': 'none' } if code== '' else {
                                                    'background-color': '#f8f8f8', 'margin': '10px',
                                                    'border': '1px solid #ddd' }),
                                        )
                                    )
                                ], className='response_html_design'
                            )])

        lis.append(html.Div([
            html.P("Q: " + question[i], style={'color': 'black','overflow': 'auto'}),
            html.Hr(),
            response_html,
            html.Hr(),


        ], className='conversation-container'))

    return lis


@app.callback(
    Output('user-input', 'value'),
    Input("submit-button", "n_clicks"),
    State('user-input', 'value')
)
def clear_input(n_clicks , value):
    if n_clicks != None and n_clicks > 0:
        return ''
    else: value

@app.callback(
    [Output("conversation-container", "children"),Output("questions_val", "children"),Output("response_val", "children")],
    [Input("chatgptquestion", "value"),
     Input("search", "n_clicks"),Input("submit-button", "n_clicks")],
    [State("user-input", "value"), State("questions_val", "children"),State("response_val", "children"),State("modal-lg", "is_open")]
)

def chatgpt_conversation(value1, nc, nc2, value2, question, response, is_open ):
    ctx = dash.callback_context
    button_click = ctx.triggered[0]["prop_id"].split (".")[0]

    def generate_table(dataframe):
        return html.Table ([
                html.Thead (
                    html.Tr ([html.Th (col) for col in dataframe.columns])
                ),
                html.Tbody ([
                    html.Tr ([
                        html.Td (dataframe.iloc[i][col]) for col in dataframe.columns
                    ]) for i in range (len (dataframe))
                ])
            ], className="fl-table")

    dicts = "{'depth': 'float64','lat': 'float64', 'long': 'float64',\
             'location': 'object', 'magnitude': 'float64',\
             'date_and_time': 'object', 'date': 'object', 'time': 'object',\
             'geometry': 'object', 'City': 'object', 'Town': 'object',\
             'id': 'int64', 'lon': 'float64'}"

    val1 = 'You are a Python tutor teaching me the Pandas library. I will be asking you how to do ' \
           'a particular task with Pandas and expecting you to explain it to me. ' \
           'Also show me the code along with your explanation. '
    val2 = 'Let me first tell you about the DataFrame I have. Then, I will start asking questions. ' \
           'The columns and their data types are given below as a Python dictionary with ' \
           f'keys showing column names and values showing the data types.{dicts} ' \
            'my file name is earthquake.csv and always use this file as pd.read_csv(earthquake.csv)' \
           'The responds will be always code without # explanation, i dont want you to show me the information except my data' \
           ' when i say manisa city this means that city name is manisa. When i want you to give me a table ' \
           'use table format as mentioned as above generate_table' \





    if is_open==False :
        question.append(val1)
        response.append (chatbot (val1))
        question.append (val2)
        response.append (chatbot (val2))



    if button_click == 'search' :

        question.append(value1.capitalize()) # add search bar question to question list ===>   ['']

        return_val = chatbot(value1) # add response, response of the search chat ===>  ['']
        response.append(return_val)


        x = len(question)

        return create_modal (x, question, response), question, response

    if button_click == 'submit-button' :



        final_val = ''.join (i for i in question)

        question.append (value2)

        return_val = chatbot (final_val)
        response.append (return_val)



        x = len(question)
        return create_modal (x, question, response), question, response

    else:
        raise PreventUpdate
#=============================================================================================================#

# CITY/ TOWN/ DATE  DROPDOWN
@app.callback(Output("date_type", "options"),
              [Input("valcity", "value"),
               Input("valtown", "value")])
def update_graph(value1,value2):

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
#=============================================================================================================




# MAP GRAPH
@app.long_callback(
              [Output("graph1", "figure"),
               Output("graph1", "style"),
               Output("leaflet_graph", "children"),
               Output("graph2", "figure"),
               Output("graph2", "style")],
              [Input("valcity", "value"),
               Input("valtown", "value"),
               Input("date_type", "value"),
               Input("chart_type", "value"),
               Input("radiograph", 'value'),
               Input('themeSwitch','checked'),
               Input('slider-pitch','value'),
               Input('slider-bearing','value')])
def update_graph3(value1,value2, value3, value4, radio, checked, pitch, bearing):

    time.sleep(3)

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
    #df['City'] = df['City'].apply(lambda c: c.capitalize())
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
                color_continuous_scale='rainbow',
                zoom=4,
                radius=25,
                height=440,
            )

        fig.update_layout (mapbox_style=value4)
        fig.update_layout (margin={ "r": 0, "t": 0, "l": 0, "b": 0 },)
        fig.update_layout (mapbox_bounds={ "west": 20, "east": 48, "south": 30, "north": 45 })

        return fig,{'visibility':'visible'},{},fb(df, value1, checked),{'visibility':'visible'}

    if radio == 'scatter' :
        fig = px.scatter_mapbox (
            df,
            lat="lat",
            lon="long",
            hover_name="City",
            hover_data=["date", "time", "magnitude"],
            range_color=[min, max],
            color_discrete_sequence=["fuchsia"],
            zoom=4,
            height=440,
        )

        fig.update_layout (mapbox_style=value4)
        fig.update_layout (margin={ "r": 0, "t": 0, "l": 0, "b": 0 }, )
        fig.update_layout (mapbox_bounds={ "west": 20, "east": 48, "south": 30, "north": 45 })

        return fig,{'visibility':'visible'}, {}, fb(df, value1,checked),{'visibility':'visible'}

    if radio == 'hexagon_layer':

        from tqdm.auto import tqdm, trange
        from time import sleep


            # Can also use bar.write()
        # Define a layer to display on a map
        layer = pdk.Layer (
            "HexagonLayer",
            df[['lat', 'long']],
            get_position=["long", "lat"],
            auto_highlight=True,
            elevation_scale=50,
            pickable=True,
            elevation_range=[0, 1000],
            extruded=True,
            coverage=1,
        )

        # Set the viewport location
        view_state = pdk.ViewState (
            longitude=35,
            latitude = 38,
            zoom=6,
            min_zoom=5,
            max_zoom=15,
            pitch=pitch,
            bearing=bearing,
        )

        r = pdk.Deck (layers=[layer], initial_view_state=view_state, map_provider='mapbox')

        fig = dash_deck.DeckGL(r.to_json(), id="deck-gl",tooltip={"text": "{position}\nMagnitude: {magnitude}"},
                               mapboxKey=mapbox_access_token,style={"width": "50vw", "height": "40vh"})



        return {},{'display': 'None' },fig,fb(df, value1,checked),{'visibility':'visible'}

    else: no_update


@app.callback ([Output ("layer", "children")],
               [Input ("map", "click_lat_lng"),])
def map_click(click_lat_lng):
    if click_lat_lng ==None:
        raise PreventUpdate

    icon = {'iconUrl': app.get_asset_url('pngegg.png'),
            'iconSize': [50, 50]}
    res = [dl.Marker (position=click_lat_lng, icon= icon, children=dl.Tooltip ("({:.3f}, {:.3f})".format (*click_lat_lng)))]
    return res




if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8050)