import dash
from dash import State, html, dcc, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from source.plotting import plot_NML

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server
app.title = "SIQAD Interconector"


app.layout = html.Div([
    dcc.Store(id='files-store'),
    dcc.Store(id='placeholder-fig'),
    html.Div([
        html.Div([
            html.H3("SiDB Interconector", style={'textAlign': 'center', 'color': '#ffffff'}),
        ], style={'flex': '1'}),
        html.Div([
            dbc.Button("🔵 Main", id="btn-main", color="secondary", className="me-2", size="sm", disabled=False),
            dbc.Button("🟠 Input selector", id="btn-input", color="secondary", className="me-2", size="sm", disabled=False),
            dbc.Button("❓ Documentation", id="btn-info", color="secondary", className="me-2", size="sm"),
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),
    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),

    html.Hr(),
    html.Div([
        dcc.Dropdown(id='gate-dropdown', multi=True, placeholder='Select gates', style={'width': '100%', 'marginRight': '10px', 'marginBottom': '10px'}),
        html.Div([
            html.Div([
                 dcc.Graph(id='gate-view-plot', style={'height': '700px'}),
            ], style={'width': '60%', 'paddingLeft': '10px'}),

            html.Div([
                html.Pre(id='backend-log', style={
                    'height': '700px',
                    'overflowY': 'scroll',
                    'backgroundColor': '#111',
                    'color': '#0f0',
                    'paddingleft': '10px',
                    'border': '1px solid #333',
                    'fontFamily': 'monospace',
                    'whiteSpace': 'pre-wrap'
                })
            ], style={
                'width': '40%',
                'paddingLeft': '10px',
                'justifyContent': 'flex-end'
            }),
        ], style={'display': 'flex', 'flexDirection': 'column'}, className='flex-row'),

        html.H1("Truth Table visualization", id='truth-table-label', style={'fontSize': '30px', 'marginTop': '40px', 'textAlign': 'center', 'color': '#ffffff', 'width': '100%'}),
        html.Div([
            html.Div([
                dcc.Graph(id='specific-gate', style={'height': '700px'}),
                dcc.Slider(
                    id='gate-slider',
                    min=0,
                    max=0,
                    step=1,
                    value=0,
                    tooltip={"placement": "bottom", "always_visible": False},
                    className='ppm-slider'
                ),
            ], style={'width': '50%', 'paddingLeft': '10px', 'display': 'flex', 'flexDirection': 'column'}),
            html.Div([
                dash_table.DataTable(
                    id='circuit-truth-table',
                    columns=[
                        {"name": "Result", "id": "result"},
                        {"name": "Expected", "id": "expected"},
                        {"name": "File_ID", "id": "file_id"},
                        {"name": "Energy", "id": "energy"},
                    ],
                    style_table={'overflowX': 'auto'},
                    style_header={'backgroundColor': '#1e1e1e', 'color': 'white'},
                    style_cell={'backgroundColor': '#111111', 'color': 'white'},
            )   
            ], style={
                'width': '50%',
                'paddingLeft': '10px',
                'justifyContent': 'flex-end'
            }),
        ], style={'display': 'flex', 'flexDirection': 'column'}, className='flex-row'),




    ]),

    html.Hr(),

    html.Div([
        html.Hr(),
        html.P("2025 SiDB Interconector, UFV", style={'textAlign': 'center', 'color': '#ffffff'}),
    ])


])

#Callbacks
@app.callback(
    Output('gate-view-plot', 'figure'),
    Input('gate-dropdown', 'value'),
    State('files-store', 'data')
)
def update_gate_view(selected_gates, files_data):
    if not selected_gates or not files_data:
        return plot_NML('', 20)

@app.callback(
    Output('specific-gate', 'figure'),
    Input('gate-dropdown', 'value'),
    State('files-store', 'data')
)

def update_specific_gate(selected_gates, files_data):
    if not selected_gates or not files_data:
        return plot_NML('', 20)

   


if __name__ == '__main__':
    app.run(debug=True)

