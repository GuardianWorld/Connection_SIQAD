import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from source import file_manager, sqd_manipulator, gate_connector, StreamCapture
from source.plotting import plot_NML, get_top_size, get_bottom_size, get_viewport, viewport_size
import os

layout = html.Div([
    dcc.Interval(id="log-updater", interval=1000, n_intervals=0),  # every 1s
    html.Div([
        dcc.Dropdown(
            id='gate-dropdown',
            multi=False, placeholder='Select a gate',
            style={'width': '100%', 'marginRight': '10px', 'marginBottom': '10px'}),
        dbc.Button("Connect", id="btn-connect", color="secondary", disabled=False, style={'width': '15%', 'marginRight': '10px', 'height': '35px'}),
        dbc.Button("Undo", id="btn-undo", color="secondary", disabled=False, style={'width': '15%', 'marginRight': '10px', 'height': '35px'}),
        dbc.Button("Clear", id="btn-clear", color="secondary", disabled=False, style={'width': '15%', 'marginRight': '10px', 'height': '35px'}),
    ], style={'display': 'flex'}),
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
])
    

placeholder_fig = plot_NML('')
if(os.name == 'posix'):
    simanneal = "data/simulators/simanneal"
    complete = "data/simulators/complete"
else:
    simanneal = "data\\simulators\\simanneal"
    complete = "data\\simulators\\complete"

#Callbacks
@callback(
    Output('gate-view-plot', 'figure'),
    Input('btn-connect', 'n_clicks'),
    Input('btn-undo', 'n_clicks'),
    Input('btn-clear', 'n_clicks'),
    Input('selected-gates-store', 'data'),
    State('files-store', 'data'),
    State('wire-lenght-store', 'data')
)
def update_gate_view(_,__, ___, selected_gates, files_data, wire_lenght):
    if not selected_gates or not files_data:
        return placeholder_fig
    fig = placeholder_fig
    
    #Print JUST the names
    gate_names = [os.path.basename(gate) for gate in selected_gates]
    print("Selected gates:", gate_names)

    if len(selected_gates) == 1:
        file1 = selected_gates[0]
        gate1 = sqd_manipulator.main_operator(file1)
        viewport = get_viewport(gate1)
        fig = plot_NML(gate1, viewport)
    if len(selected_gates) == 2:
        file1 = selected_gates[0]
        file2 = selected_gates[1]
        gate1 = sqd_manipulator.main_operator(file1)
        gate2 = sqd_manipulator.main_operator(file2)
        circuit = gate_connector.connect_2_gates(gate1, gate2, wires=wire_lenght)            
        gate = sqd_manipulator.circuit_to_gate(circuit)
        viewport = get_viewport(gate)
        fig = plot_NML(gate, viewport)
    if len(selected_gates) == 3:
        file1 = selected_gates[0]
        file2 = selected_gates[1]
        file3 = selected_gates[2]
        gate1 = sqd_manipulator.main_operator(file1)
        gate2 = sqd_manipulator.main_operator(file2)
        gate3 = sqd_manipulator.main_operator(file3)
        circuit = gate_connector.connect_3_gates(gate1, gate2, gate3, wires=wire_lenght)
        gate = sqd_manipulator.circuit_to_gate(circuit)
        viewport = get_viewport(gate)
        fig = plot_NML(gate, viewport)

    print(viewport_size(viewport))
    
    return fig
    

@callback(
    Output('specific-gate', 'figure'),
    Input('btn-connect', 'n_clicks'),
    Input('selected-gates-store', 'data'),
    State('files-store', 'data')
)

def update_specific_gate(button, selected_gates, files_data):
    if not selected_gates or not files_data:
        return placeholder_fig

        

@callback(
    Output('files-store', 'data'),
    Input('load-files', 'n_intervals'),
    Input('btn-main', 'n_clicks'),
)

def load_files(_, __):
    if os.name == 'posix':
        files = file_manager.get_files("./data/sqd")
    else:
        files = file_manager.get_files("data\\sqd")

    return files  # This will be a list of file paths

@callback(
    Output('gate-dropdown', 'options'),
    Input('files-store', 'data')
)
def populate_dropdown(file_list):
    if not file_list:
        return []
    return [{"label": os.path.basename(f), "value": f} for f in file_list]

@callback(
    Output('selected-gates-store', 'data'),
    Input('btn-connect', 'n_clicks'),
    Input('btn-undo', 'n_clicks'),
    Input('btn-clear', 'n_clicks'),
    State('gate-dropdown', 'value'),
    State('selected-gates-store', 'data'),
    prevent_initial_call=True
)
def store_selected_gate(button1, button2, button3, selected_gate, stored):
    ctx = dash.callback_context
    if stored is None:
        stored = []
    if not selected_gate:
        return stored
    if ctx.triggered:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id == 'btn-clear':
            stored = []
        elif triggered_id == 'btn-undo':
            if stored and len(stored) > 0:
                stored.pop()
        elif triggered_id == 'btn-connect':
            stored.append(selected_gate)
    return stored

@callback(
    Output("backend-log", "children"),
    Input("log-updater", "n_intervals")
)
def update_log(n):
    return StreamCapture.log_buffer.getvalue()