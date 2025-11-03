import dash
from dash import clientside_callback, html, dcc, callback, Input, Output, State, dash_table, ctx, ALL
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from source import file_manager, sqd_manipulator, gate_connector, StreamCapture, implementation
from source.plotting import plot_NML, get_top_size, get_bottom_size, get_viewport, viewport_size, plot_XY
import os
import time
from dash import ClientsideFunction
from pathlib import Path

layout = html.Div([
    dcc.Store(id='config-sim-store', data={}),
    dcc.Store(id='config-current-sim-store'),

    #html.H4("Configuration", style={'textAlign': 'center', 'color': '#ffffff', }),
    #html.Hr(),
    html.Div(id='general-config-div'),
    html.Div([
        html.Hr(),
        html.Button("Apply", id="apply-config", n_clicks=0, style={'width': '49%', 'height': '35px', 'marginRight': '1%'}),
        html.Button("Close", id="close-config", n_clicks=0, style={'width': '49%', 'height': '35px', 'marginLeft': '1%'}),
    ]),    
])


def build_config_ui(params):
    children = []
    for pid, info in params.items():
        input_type = dcc.Input if info['type'] in ['int', 'float'] else dcc.Dropdown
        step = 1 if info['type'] == 'int' else 0.01
        children.append(html.Div([
            html.Label(f"{info['label']}", title=info['tip']),
            dcc.Input(
                id={'type': 'sim-param', 'index': pid},
                type='number',
                value=float(info['val']),
                step=step,
                style={'width': '100%'}
            )
        ], style={'marginBottom': '10px'}))
    return children

@callback(
    Output('general-config-div', 'children'),
    Input('current-sim-store', 'data')
)
def update_config_ui(file):
    #Check if the current sim has a Custom_sim_params.xml file, if so load it and return it.
    if file is None:
        return html.Div("No simulator selected.")
    #print(file)
    # Parse the physeng file to get the parameters
    params = file_manager.parse_physeng(file)

    # Load existing custom_sim_params.xml if it exists
    current_sim_folder = Path(file).parent
    config_file_path = current_sim_folder / "custom_sim_params.xml"
    custom_params = {}
    if config_file_path.is_file():
        try:
            with open(config_file_path, "r") as f:
                content = f.read()
                custom_params = eval(content)
        except Exception as e:
            print(f"Error reading custom_sim_params.xml: {e}")
            custom_params = {}

    # Override default values with custom ones
    for key, value in custom_params.items():
        if key in params:
            params[key]['val'] = value

    children = []
    row_children = []
    for pid, info in params.items():
        param_type = info['type']
        default_val = info['val']
        if param_type in ['int', 'float']:
            if param_type == 'float':
                dp = int(info['dp'] if 'dp' in info else 1)
                step = 10 ** (-dp)
            else:
                step = 1

            try:
                value = float(default_val)
            except (ValueError, TypeError):
                value = None
            comp = dcc.Input(
                id={'type': 'sim-param', 'index': pid},
                type='number',
                value=value,
                step=step,
                style={'width': '100%'}
            )
        else:
            # fallback to text input for strings / enums
            comp = dcc.Input(
                id={'type': 'sim-param', 'index': pid},
                type='text',
                value=default_val,
                style={'width': '100%'}
            )

        row_children.append(
            html.Div([
                html.Label(info.get('label', pid), title=info.get('label', ''), style={'maxWidth': '80%', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'whiteSpace': 'nowrap'}),
                comp,
                html.Small(info.get('tip', ''), style={'display': 'block', 'color': '#aaa', 'fontSize': '12px', 'boxSizing': 'border-box', 'minWidth': '0', 'flex': '1'})
            ], style={'flex': '1','marginBottom': '10px', 'alignItems': 'center'})
        )

    for i in range(0, len(row_children), 3):
        pair = row_children[i:i + 3]
        children.append(
            html.Div(pair, style={'display': 'flex', 'gap': '10px'})
        )


    return children
    
@callback(
    Output('config-sim-store', 'data'),
    Input('apply-config', 'n_clicks'),
    State({'type': 'sim-param', 'index': ALL}, 'value'),
    State({'type': 'sim-param', 'index': ALL}, 'id'),
    Input('current-sim-store', 'data'),
    Input('sim-dropdown', 'value')
)
def apply_config(n_clicks, values, ids, current_sim, sim_value):
    if not n_clicks:
        #Check if the current sim has a Custom_sim_params.xml file, if so load it and return it.
        if current_sim is None:
            return {}
        current_sim_folder = Path(current_sim).parent
        config_file_path = current_sim_folder / "custom_sim_params.xml"
        if config_file_path.is_file():
            with open(config_file_path, "r") as f:
                content = f.read()
                try:
                    config = eval(content)
                except Exception as e:
                    print(f"Error reading custom_sim_params.xml: {e}")
                    config = {}
        else:
            config = {}
        return config

    # Build dictionary of {parameter_name: value}
    config = {item['index']: val for item, val in zip(ids, values)}

    print("Changes Applied")  # for debugging

    #Save changes in a file in the simulator folder as custom_sim_params.xml, just save the dict.
    current_sim_folder = Path(current_sim).parent
    config_file_path = current_sim_folder / "custom_sim_params.xml"
    with open(config_file_path, "w") as f:
        f.write(str(config))
    return config