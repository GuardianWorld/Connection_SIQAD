import dash
from dash import State, html, dcc, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from source.file_manager import get_simulators
from source.plotting import plot_NML
import os
from pages import mainpage

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server
app.title = "SIQAD Interconector"


app.layout = html.Div([
    dcc.Store(id='files-store'),
    dcc.Store(id='sim-store'),
    dcc.Store(id='current-sim-store'),
    dcc.Store(id='wire-lenght-store', data=1),
    dcc.Store(id='selected-gates-store'),
    dcc.Store(id='truth-table-store'),
    dcc.Store(id='simulated-states-store'),
    dcc.Store(id='gate-storage'),
    dcc.Store(id='log-trigger'),
    dcc.Store(id='algorithm-store', data='FIFO'),
    dcc.Store(id='specific-gate-data', data=[]),
    dcc.Interval(id='load-files', interval=1*1000, n_intervals=0, max_intervals=1),
    dcc.Store(id='placeholder-fig'),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='sim-dropdown',
                multi=False, placeholder='simanneal',
                style={'width': '100%', 'gap': '10px'}
            ),
        ], style={'flex': '0.8'}),
        html.Div([
            dcc.Dropdown(
                id='algorithm-dropdown',
                options=[
                    {'label': 'First in First out', 'value': 'FIFO'},
                    {'label': 'Corner Connection', 'value': 'CORNER'},
                    {'label': 'bottom-up', 'value': 'BOTTOMUP'},
                    {'label': '"Balanced"', 'value': 'BALANCED'},
                ],
                multi=False, value='FIFO',
                style={'width': '100%', 'gap': '10px'}
            ),
        ], style={'flex': '0.8'}),
        html.Div([
            html.H3("SiDB Interconector", style={'textAlign': 'center', 'color': '#ffffff', }),
        ], style={'flex': '2'}),
        html.Div([
            dbc.Button("🔵 Main", id="btn-main", color="primary", className="me-2", size="sm", disabled=False),
            dbc.Button("🟠 Input selector", id="btn-input", color="secondary", className="me-2", size="sm", disabled=False),
            dbc.Button("❓ Documentation", id="btn-info", color="secondary", className="me-2", size="sm"),
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),
    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),

    html.Hr(),
    #page "Main"
    html.Div([
        html.Div(mainpage.layout, id='main-page', style={'display': 'block'}),
        html.Div(id='input-page', style={'display': 'none'}),
        html.Div(id='info-page', style={'display': 'none'}),
    ]),

    html.Hr(),

    html.Div([
        html.Hr(),
        html.P("2025 SiDB Interconector, UFV", style={'textAlign': 'center', 'color': '#ffffff'}),
    ])


])

@app.callback(
    Output('btn-main', 'color'),
    Output('btn-input', 'color'),
    Output('btn-info', 'color'),
    Input('btn-main', 'n_clicks'),
    Input('btn-input', 'n_clicks'),
    Input('btn-info', 'n_clicks'),
)
def update_button_colors(main_clicks, input_clicks, info_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        triggered_id = 'btn-main'
    else:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'btn-main':
        return 'primary', 'secondary', 'secondary'
    elif triggered_id == 'btn-input':
        return 'secondary', 'primary', 'secondary'
    elif triggered_id == 'btn-info':
        return 'secondary', 'secondary', 'primary'

    return 'secondary', 'secondary', 'secondary'

@app.callback(
    Output('main-page', 'style'),
    Output('input-page', 'style'),
    Output('info-page', 'style'),
    Input('btn-main', 'n_clicks'),
    Input('btn-input', 'n_clicks'),
    Input('btn-info', 'n_clicks'),
)

def toggle_pages(main_clicks, input_clicks, info_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        triggered_id = 'btn-main'
    else:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    styles = {
        'btn-main': [{'display': 'block'}, {'display': 'none'}, {'display': 'none'}],
        'btn-input': [{'display': 'none'}, {'display': 'block'}, {'display': 'none'}],
        'btn-info': [{'display': 'none'}, {'display': 'none'}, {'display': 'none'}],
    }

    return styles.get(triggered_id, [{'display': 'block'}, {'display': 'none'}, {'display': 'none'}])

@app.callback(
    Output('sim-dropdown', 'options'),
    Output('sim-store', 'data'),
    Input('load-files', 'n_intervals'),
)
def update_sim_dropdown_options(_):
    simulators = get_simulators()
    sim_names = [os.path.basename(sim) for sim in simulators]
    sim_names = [name.replace(".physeng", "") for name in sim_names]
    return [{'label': name, 'value': name} for name in sim_names], simulators

@app.callback(
    Output('current-sim-store', 'data'),
    Input('sim-dropdown', 'value'),
    Input('sim-store', 'data')
)

def update_current_sim(selected_sim, sim_list):
    if not sim_list:
        return None
    if selected_sim is None:
        current_sim = None
        for sim in sim_list:
            if "simanneal" in sim:
                current_sim = sim
                return current_sim
    if selected_sim and sim_list:
        for sim in sim_list:
            if selected_sim in sim:
                return sim
    return None

@app.callback(
    Output('algorithm-store', 'data'),
    Input('algorithm-dropdown', 'value'),
)
def update_algorithm_store(selected_algorithm):
    if selected_algorithm is None:
        return 'FIFO'
    return selected_algorithm


if __name__ == '__main__':
    app.run(debug=True)
    #If needed to run in server:

    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    #app.run(host='0.0.0.0', debug=False)