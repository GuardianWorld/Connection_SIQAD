import dash
from dash import clientside_callback, html, dcc, callback, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from source import file_manager, sqd_manipulator, gate_connector, StreamCapture, implementation
from source.plotting import plot_NML, get_top_size, get_bottom_size, get_viewport, viewport_size, plot_XY
import os
import time
from pages import configpage
from dash import ClientsideFunction
from pathlib import Path
from sympy.logic.boolalg import truth_table

data_temp = Path("data") / "temp"
data_xml = Path("data") / "xml"
data_simulators = Path("data") / "simulators"
data_sqd = Path("data") / "sqd"
data_results = Path("data") / "results"
simmanneal_default_path = data_simulators / "simanneal"


layout = html.Div([
    dcc.Interval(id="log-updater", interval=500, n_intervals=0),  # every 0.5s
    html.Div([
        dcc.Dropdown(
            id='gate-dropdown',
            multi=False, placeholder='Select a gate',
            style={'width': '100%', 'marginRight': '10px', 'marginBottom': '10px'}),
        dcc.Input(
            id='wire-length-input',
            type='number',
            placeholder='Wire Length (default 1)',
            value=1,
            min=1,
            step=1,
            style={'width': '10%', 'marginRight': '10px', 'marginBottom': '10px', 'height': '35px'}
        ),
        html.Div([
            html.Button("⚙", 
            id="toggle-config", 
            n_clicks=0, 
            style={'width': '100%', 'gap': '10px', 'height': '35px'}
        ),
        ], style={'flex': '0.1', 'marginRight': '10px'}),
        dbc.Button("Connect", id="btn-connect", color="secondary", disabled=False, style={'width': '15%', 'marginRight': '10px', 'height': '35px'}),
        dbc.Button("Undo", id="btn-undo", color="secondary", disabled=False, style={'width': '15%', 'marginRight': '10px', 'height': '35px'}),
        dbc.Button("Clear", id="btn-clear", color="secondary", disabled=False, style={'width': '15%', 'marginRight': '10px', 'height': '35px'}),
        dbc.Button("Simulate", id="btn-simulate", color="primary", disabled=False, style={'width': '15%', 'marginRight': '10px', 'height': '35px'}),
    ], style={'display': 'flex'}),
    html.Div([
        html.Div([
                dcc.Graph(id='gate-view-plot', style={'height': '700px'}),
        ], style={'width': '50%', 'paddingLeft': '10px'}),

        html.Div([
            html.Div(configpage.layout, id='config-page', style={'display': 'none'}),
            html.Pre(id='backend-log', style={
                'height': '700px',
                'overflowY': 'scroll',
                'backgroundColor': '#111',
                'color': '#0f0',
                'paddingleft': '10px',
                'border': '1px solid #333',
                'fontFamily': 'monospace',
                'whiteSpace': 'pre-wrap'
            }),
        ], style={
            'width': '50%',
            'paddingLeft': '10px',
            'justifyContent': 'flex-end'
        }),
    ], style={'display': 'flex', 'flexDirection': 'column'}, className='flex-row'),

    html.H1("Truth Table visualization", id='truth-table-label', style={'fontSize': '30px', 'marginTop': '40px', 'textAlign': 'center', 'color': '#ffffff', 'width': '100%'}),
    html.Div([
        html.Div([
            dcc.Graph(id='specific-gate', style={'height': '700px'}),
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
                page_size=20,
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
        dcc.Slider(
        id='gate-slider',
        min=0,
        max=0,
        step=1,
        value=0,
        tooltip={"placement": "bottom", "always_visible": False},
        className='ppm-slider'
    ),
])
    

placeholder_fig = plot_NML('')
placeholder_fig.update_layout(
    title="Select a gate to view",
    height=700,
)

#Callbacks

@callback(
    Output('config-page', 'style'),
    Output('backend-log', 'style'),
    Input('toggle-config', 'n_clicks'),
    State('config-page', 'style'),
    Input('apply-config', 'n_clicks'),
    Input('close-config', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_config(n_clicks, current_style, apply_click, close_click):
    if n_clicks is None:
        return current_style or {'display': 'none'}
    if current_style is None or current_style.get('display') == 'none':
        return {'display': 'block', 'marginTop': '20px'}, {'height': '400px', 'overflowY': 'scroll', 'backgroundColor': '#111', 'color': '#0f0', 'paddingleft': '10px', 'border': '1px solid #333', 'fontFamily': 'monospace', 'whiteSpace': 'pre-wrap', 'display': 'none'}
    else:
        return {'display': 'none'}, {'height': '700px', 'overflowY': 'scroll', 'backgroundColor': '#111', 'color': '#0f0', 'paddingleft': '10px', 'border': '1px solid #333', 'fontFamily': 'monospace', 'whiteSpace': 'pre-wrap', 'display': 'block'}
@callback(
    Output('wire-lenght-store', 'data'),
    Input('wire-length-input', 'value')        
)
def update_wire_length(value):
    if value is None or value < 1:
        return 1
    return value

@callback(
    Output('gate-view-plot', 'figure'),
    Output('gate-storage', 'data'),
    Input('btn-connect', 'n_clicks'),
    Input('btn-undo', 'n_clicks'),
    Input('btn-clear', 'n_clicks'),
    Input('selected-gates-store', 'data'),
    State('files-store', 'data'),
    Input('wire-lenght-store', 'data'),
    Input('algorithm-store', 'data')
)
def update_gate_view(_,__, ___, selected_gates, files_data, wire_lenght, algorithm):
    if not selected_gates or not files_data:
        return placeholder_fig, None
    fig = placeholder_fig
    
    #Print JUST the names
    gate_names = [os.path.basename(gate) for gate in selected_gates]
    gate_pos_name = None
    """"
    if len(selected_gates) == 1:
        file1 = selected_gates[0]
        gate = sqd_manipulator.main_operator(file1)
    if len(selected_gates) == 2:
        file1 = selected_gates[0]
        file2 = selected_gates[1]
        gate1 = sqd_manipulator.main_operator(file1)
        gate2 = sqd_manipulator.main_operator(file2)
        circuit = gate_connector.connect_2_gates(gate1, gate2, wires=wire_lenght)            
        gate = sqd_manipulator.circuit_to_gate(circuit)
    if len(selected_gates) == 3:
        file1 = selected_gates[0]
        file2 = selected_gates[1]
        file3 = selected_gates[2]
        gate1 = sqd_manipulator.main_operator(file1)
        gate2 = sqd_manipulator.main_operator(file2)
        gate3 = sqd_manipulator.main_operator(file3)
        circuit = gate_connector.connect_3_gates(gate1, gate2, gate3, wires=wire_lenght)
        gate = sqd_manipulator.circuit_to_gate(circuit)
    """
    files = selected_gates
    #circuit = gate_connector.connect_n_gates(files, wires=wire_lenght)
    if(algorithm == "FIFO"):
        circuit, gate_pos_name = gate_connector.connect_n_gates_fifo(files, wires=wire_lenght)
    elif(algorithm == "CORNER"):
        circuit = gate_connector.connect_n_gates(files, wire_lenght)
    elif(algorithm == "BALANCED"):
        circuit = gate_connector.connect_n_gates_balanced(files, wire_lenght)
    elif(algorithm == "BOTTOMUP"):
        circuit = gate_connector.connect_n_gates_bottom_up(files, wire_lenght)
    gate = sqd_manipulator.circuit_to_gate(circuit)
        
    viewport = get_viewport(gate)
    fig = plot_NML(gate, viewport, len(selected_gates), gate_pos_name)
    print(f"Selected gates: {gate_names}, Wire length: {wire_lenght}, {viewport_size(viewport)}")
    print(f"Gate expression: {gate.expression}")
    
    return fig, gate.to_dict()        

@callback(
    Output('files-store', 'data'),
    Input('load-files', 'n_intervals'),
    Input('btn-main', 'n_clicks'),
)

def load_files(_, __):
    file_path_string = str(data_sqd)
    files = file_manager.get_files(file_path_string)

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
    Output('circuit-truth-table', 'data'),
    Output('specific-gate-data', 'data'),
    Input('btn-simulate', 'n_clicks'),
    State('gate-storage', 'data'),
    State('sim-store', 'data'),
    State('current-sim-store', 'data'),
    State('config-sim-store', 'data')
)
def simulate_circuit(n_clicks, gate, simulator_path, current_sim, config_sim):
    if not gate:
        #Create a padded empty table
        blank_row = {"result": "", "expected": "", "file_id": "", "energy": ""}
        data = [blank_row.copy() for _ in range(20)]
        return data, []
    temp_string = str(data_temp)
    xml_string = str(data_xml)
    file_manager.clear_folder(temp_string)
    file_manager.clear_folder(xml_string)

    gate = sqd_manipulator.Gate.from_dict(gate)
    print(gate.expression)
    expected = []

    for values, output in truth_table(gate.expression, gate.input_symbols):
        expected.append(int(bool(output)))

    if current_sim is None:
        sim = simmanneal_default_path
    else:
        sim = current_sim

    # cleanup sim
    if(os.name == 'posix'):
        sim = sim.replace(".physeng", "")
    elif(os.name == 'nt'):
        sim = sim.replace(".physeng", ".exe")

    print("Simulator: ", sim)
    print("Simulating gate:", gate.name)

    Results = []
    specific_gate_data = []
    gates = sqd_manipulator.combinators(gate)
    print(f"Total simulations: {len(gates)}")
    percentage_print = max(1, len(gates) // 8)
    if len(gates) > 16:
        print("Large number of simulations, this might take a while...")

    print("Progress: [", end='', flush=True)
    sim_template = file_manager.gen_simulator_sim_template(simulator_path=sim)
    if sim_template is None:
        sim_template = file_manager.get_simulator_sim_template(sim)
    if sim_template is None:
        print("No sim template found, Aborting.")
        return [], []
    for i in range(len(gates)):
        file_name, template = file_manager.sqd_template_create(gates[i], prefix=f"combination_{i}_", mode="simulation", sim_params_template=sim_template, parameters=config_sim)
        file_path = str(data_temp / file_name)
        file_manager.make_file(file_path, template)
        
        result_name = "result_" + file_name
        #print(">>>>>", result_name)
        result_path = implementation.call_sim(file_path, result_name, simulator=sim, simmaneal_default_path=simmanneal_default_path)
        #print("Result path: " + result_path)
        symbol_table, energy = sqd_manipulator.read_result(result_path, gate)
        specific_gate_data.append(sqd_manipulator.read_result_plusXY(result_path, gate))

        Results.append([symbol_table, i, energy])
        if i % percentage_print == 0:
            print(f"#", end='', flush=True)
    
    print("]")    
    #print(implementation.make_table(["Result", gate.name, "Energy"], Results))

    columns = ["Result", "Expected", "File_ID", "Energy"]

    def clean(val):
        if isinstance(val, (int, float, str, bool)) or val is None:
            return val
        return str(val)  # fallback to string

    data = [
    {
        "result": clean(row[0]),
        "expected": "N/A" if row[1] >= len(expected) else clean(expected[row[1]]),
        "file_id": clean(row[1]),
        "energy": clean(row[2]),
    }
    for row in Results
    ]

    def pad_table_data(data, page_size=20):
        # If there are fewer rows than page size, fill with blanks
        rows_to_add = page_size - len(data) % page_size
        if rows_to_add > 0:
            blank_row = {col: "" for col in data[0].keys()} if data else {"result": "", "expected": "", "file_id": "", "energy": ""}
            data += [blank_row.copy() for _ in range(rows_to_add)]
        return data
    
    data = pad_table_data(data, page_size=20)

    
    return data, specific_gate_data


@callback(
    Output('gate-slider', 'max'),
    Output('gate-slider', 'value'),
    Input('specific-gate-data', 'data'),
)
def update_slider(specific_gate_data):
    if not specific_gate_data:
        return 0, 0

    max_value = len(specific_gate_data) - 1
    return max_value, 0

@callback(
    Output('specific-gate', 'figure'),
    Input('specific-gate-data', 'data'),
    Input('gate-slider', 'value'),
)
def update_specific_gate(specific_gate_data, slider_value):
    if specific_gate_data is None:
        return placeholder_fig
    
    if slider_value < 0 or slider_value >= len(specific_gate_data):
        return placeholder_fig

    gate_info = specific_gate_data[slider_value]
    fig = plot_XY(gate_info)

    return fig




@callback(
    Output("backend-log", "children"),
    Output("log-trigger", "data"),  # trigger for JS
    Input("log-updater", "n_intervals")
)
def update_log(n):
    return StreamCapture.log_buffer.getvalue(), time.time()


clientside_callback(
    """
    function(trigger) {
        const logElement = document.getElementById('backend-log');
        if (!logElement) {
            return window.dash_clientside.no_update;
        }

        const threshold = 50; // pixels from bottom considered "at bottom"
        const atBottom = logElement.scrollHeight - logElement.scrollTop - logElement.clientHeight < threshold;

        if (atBottom) {
            logElement.scrollTop = logElement.scrollHeight;
        }

        return window.dash_clientside.no_update;
    }
    """,
    Output("log-trigger", "data", allow_duplicate=True),  # dummy output, won't change
    Input("log-trigger", "data"),
    prevent_initial_call=True
)