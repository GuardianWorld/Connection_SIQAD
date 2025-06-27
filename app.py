import dash
from dash import State, html, dcc, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from source.plotting import plot_NML
import os
from pages import mainpage

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server
app.title = "SIQAD Interconector"


app.layout = html.Div([
    dcc.Store(id='files-store'),
    dcc.Store(id='wire-lenght-store', data=1),
    dcc.Store(id='selected-gates-store'),
    dcc.Interval(id='load-files', interval=1*1000, n_intervals=0, max_intervals=1),
    dcc.Store(id='placeholder-fig'),
    html.Div([
        html.Div([
            html.H3("SiDB Interconector", style={'textAlign': 'center', 'color': '#ffffff'}),
        ], style={'flex': '1'}),
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

if __name__ == '__main__':
    app.run(debug=True)

