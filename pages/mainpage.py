import csv
import dash
from dash import clientside_callback, html, dcc, callback, Input, Output, State, dash_table
import matplotlib
from matplotlib import pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from source import corrector
from source import file_manager, sqd_manipulator, gate_connector, StreamCapture, implementation
from source.plotting import plot_NML, get_top_size, get_bottom_size, get_viewport, viewport_size, plot_XY
import os
import time
from pages import configpage
from dash import ClientsideFunction
from pathlib import Path
from sympy.logic.boolalg import truth_table

matplotlib.use("Agg")
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
            placeholder='Wires',
            min=1,
            step=1,
            style={'width': '10%', 'marginRight': '10px', 'marginBottom': '10px', 'height': '35px'}
        ),
        dcc.Input(
            id='fixes-allowed',
            type='number',
            placeholder='Fixes',
            min=0,
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
    html.Button("Save as PNG", id='save-button', n_clicks=0, style={'width': '200px', 'height': '35px', 'marginTop': '20px'}),
    html.Button("Auto Batch", id='auto-batch-button', n_clicks=0, style={'width': '200px', 'height': '35px', 'marginTop': '20px'}),
    html.Button("Save gate", id='save-gate-button', n_clicks=0, style={'width': '200px', 'height': '35px', 'marginTop': '20px'})
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
    Output('fixes-allowed-store', 'data'),
    Input('fixes-allowed', 'value')
)
def update_fixes_allowed(value):
    if value is None or value < 0:
        return 0
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
    files = selected_gates
    #circuit = gate_connector.connect_n_gates(files, wires=wire_lenght)
    
    if(algorithm == "CORNER"):
        circuit = gate_connector.connect_n_gates(files, wires=wire_lenght)
    else:
        circuit, gate_pos_name, metadata = gate_connector.connect_n_gates(files, wires=wire_lenght, strategy=algorithm)
    gate = sqd_manipulator.circuit_to_gate(circuit)

    #Store the gate metadata in the gate
    gate.gate_metadata = metadata
        
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
    State('current-sim-store', 'data'),
    State('config-sim-store', 'data'),
    State('fixes-allowed-store', 'data'),
)
def simulate_circuit(n_clicks, gate, current_sim, config_sim, max_corrections=0, called_from_callback=True, max_mismatches=1):
    #print(max_corrections)
    if not gate:
        #Create a padded empty table
        blank_row = {"result": "", "expected": "", "file_id": "", "energy": ""}
        data = [blank_row.copy() for _ in range(20)]
        return data, []
    temp_string = str(data_temp)
    xml_string = str(data_xml)
    file_manager.clear_folder(temp_string)
    file_manager.clear_folder(xml_string)

    if(isinstance(gate, dict)):
        gate = sqd_manipulator.Gate.from_dict(gate)
        
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
    applied_corrections = 0

    max_possible_corrections = len(gate.gate_metadata)
    if(max_corrections > max_possible_corrections):
        max_corrections = max_possible_corrections
    print(f"Simulator: {sim}, gate: {gate.name}")
    while(True):
        Results, specific_gate_data, corrections_needed = simulate_internal(gate, sim, config_sim, expected, max_mismatches=max_mismatches, called_from_callback=called_from_callback)
        if(corrections_needed and applied_corrections < max_corrections):
            print("⚠️ Corrections needed, applying corrections...")
            gate = corrector.main_correction(gate, gate.gate_metadata, specific_gate_data)
            applied_corrections += 1
        elif(corrections_needed and applied_corrections >= max_corrections):
            print("⚠️ Maximum corrections applied, stopping further corrections.")
            break
        else:
            break

    #for m in gate.gate_metadata:
    #    print(m)
    #    print("")
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

    separate_results = False
    for item in data:
        result_val = str(item["result"])
        #clean result_Val from ["0"] to 0
        if result_val.startswith('[') and result_val.endswith(']'):
            result_val = result_val.strip('[]')
            result_val = result_val.strip().strip("'").strip('"')
        expected_val = str(item["expected"])
        
        if expected_val != "N/A" and result_val != expected_val:
            item["expected"] = f"{expected_val} 🔴"
            separate_results = True

    def pad_table_data(data, page_size=20):
        # If there are fewer rows than page size, fill with blanks
        rows_to_add = page_size - len(data) % page_size
        if rows_to_add > 0:
            blank_row = {col: "" for col in data[0].keys()} if data else {"result": "", "expected": "", "file_id": "", "energy": ""}
            data += [blank_row.copy() for _ in range(rows_to_add)]
        return data
    
    data = pad_table_data(data, page_size=20)

    if called_from_callback:
        print("Simulation completed.")
        return data, specific_gate_data
    else:
        print("Simulation completed (not from callback).")
        return data, specific_gate_data, separate_results, False

def simulate_internal(gate, sim, config_sim, expected, max_mismatches=1, called_from_callback=True):
    corrections_needed = False
    Results = []
    specific_gate_data = []
    gates = sqd_manipulator.combinators(gate)
    if called_from_callback:
        print(f"Total simulations to run: {len(gates)}")
    percentage_print = max(1, len(gates) // 8)

    print("Progress: [", end='', flush=True)
    sim_template = file_manager.gen_simulator_sim_template(simulator_path=sim)
    if sim_template is None:
        sim_template = file_manager.get_simulator_sim_template(sim)
    if sim_template is None:
        print("No sim template found, Aborting.")
        return [], []

    max_retries = 3
    retry_sleep = 5

    mismatches_found = 0
    for i in range(len(gates)):
        attempts = 0
        if mismatches_found >= max_mismatches:
            break
        while attempts < max_retries:
            try:
                file_name, template = file_manager.sqd_template_create(gates[i], prefix=f"combination_{i}_", mode="simulation", sim_params_template=sim_template, parameters=config_sim)
                file_path = str(data_temp / file_name)
                file_manager.make_file(file_path, template)
                result_name = "result_" + file_name
                #print(">>>>>", result_name)
                result_path = implementation.call_sim(file_path, result_name, simulator=sim, simmaneal_default_path=simmanneal_default_path)
                #print("Result path: " + result_path)
                #print(f"\nReading result for simulation {i} from {result_path}...")
                #print(gate)
                symbol_table, energy = sqd_manipulator.read_result(result_path, gate)
                specific_gate_data.append(sqd_manipulator.read_result_plusXY(result_path, gate))
                Results.append([symbol_table, i, energy])
                symbol_value = int(symbol_table[0])
                expected_value = expected[i]
                if symbol_value != expected_value:
                    mismatches_found += 1
                break
            except Exception as e:
                attempts += 1
                print(f"\n ⚠️ Error reading result for simulation {i}: {e}")
                if attempts < max_retries:
                    print(f"Retrying ({attempts}/{max_retries}) after {retry_sleep} seconds...")
                    time.sleep(retry_sleep)
                else:
                    print(f"Max retries reached for simulation {i}. Skipping this simulation.")
                    symbol_table, energy = "Error", "Error"
                    Results.append([symbol_table, i, energy])
                    if called_from_callback:
                        blank_row = {"result": "", "expected": "", "file_id": "", "energy": ""}
                        data = [blank_row.copy() for _ in range(20)]
                        return data, []
                    else:
                        return [], [], True, True  # Indicate failure
        if i % percentage_print == 0:
                print(f"#", end='', flush=True)
    
    print("]")    
    if mismatches_found >= max_mismatches:
        print(f"⚠️ Maximum mismatches reached ({max_mismatches}). Stopping further simulations.")
        corrections_needed = True

    return Results, specific_gate_data, corrections_needed

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

@callback(
    Input('save-button', 'n_clicks'),
    State('circuit-truth-table', 'data'),
    State('specific-gate-data', 'data'),
    State('gate-storage', 'data'),
    State('current-sim-store', 'data'),
    State('config-sim-store', 'data'),
    prevent_initial_call=True
)

def save_current(n_clicks, table_data, specific_gate_data, gate_storage, sim_store, config_sim_store):
    if n_clicks is None or n_clicks <= 0:
        return

    if not table_data or not specific_gate_data:
        print("⚠️ No data to save.")
        return
    
    #Get a name for the gate and make a folder for it on data/saved
    gate = sqd_manipulator.Gate.from_dict(gate_storage)
    gate_name = gate.name if gate.name else "unnamed_gate"
    save_folder = Path("data") / "saved" / gate_name
    save_folder.mkdir(parents=True, exist_ok=True)

    # Save truth table as PNG
    circuit_name = gate_name + "_truth_table"
    expression_name = gate.expression 
    simulator_name = sim_store if sim_store else "default_simanneal"
    df = pd.DataFrame(table_data)
    fig, ax = plt.subplots(figsize=(len(df.columns)*1.5, len(df)/2))
    ax.axis('off')
    ax.axis('tight')

    # Add a title with the circuit and expression names
    plt.title(f"Circuit: {circuit_name}\nExpression: {expression_name}", fontsize=14, pad=20)
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)

    plt.savefig(save_folder / "truth_table.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ Truth table saved: {save_folder / 'truth_table.png'}")

    # Save specific gate data plot as PNG
    for i, gate_info in enumerate(specific_gate_data):
        # Convert plot_XY data manually
        x_coords = [dot[0] for dot in gate_info]
        y_coords = [dot[1] for dot in gate_info]
        colors = ['black' if dot[2] == '0' else 'blue' for dot in gate_info]
        markers = ['o' if dot[2] == '1' else 'o' for dot in gate_info]

        plt.figure(figsize=(6, 6))
        for x, y, c in zip(x_coords, y_coords, colors):
            plt.scatter(x, y, color=c, s=60, edgecolors='none')
        plt.gca().invert_yaxis()
        plt.axis('off')
        plt.tight_layout()

        plt.savefig(save_folder / f"specific_gate_{i}.png", dpi=300, bbox_inches='tight')
        plt.close()
    print(f"✅ Gate data plots saved under {save_folder}")

    #Save the configuration used for the simulation
    config_file_path = save_folder / "simulation_config.txt"
    with open(config_file_path, "w") as f:
        f.write(f"Simulator: {simulator_name}\n")
        f.write(f"Configuration Parameters:\n")
        for key, value in config_sim_store.items():
            f.write(f"{key}: {value}\n")
    print(f"✅ Simulation configuration saved: {config_file_path}")

@callback(
    Input('auto-batch-button', 'n_clicks'),
    State('files-store', 'data'),
    State('current-sim-store', 'data'),
    State('config-sim-store', 'data'),
    prevent_initial_call=True
)

def auto_batch_simulation(n_clicks, files_data, current_sim, config_sim_store):
    from itertools import product
    import csv
    from datetime import datetime


    if n_clicks is None or n_clicks <= 0:
        return

    if not files_data or len(files_data) == 0:
        print("⚠️ No files to process for auto batch.")
        return

    print("Starting auto batch simulation for all gates...")

    #Prepare CSV
    summary_csv_path = Path("data/auto_batch_results") / "summary.csv"
    summary_csv_path.parent.mkdir(parents=True, exist_ok=True)

    wire_length = 1  # Default wire length
    last_num_gates = 1
    all_combos = []
    for r in range(4, 7):  
        all_combos.extend(list(product(files_data, repeat=r)))

    def normalize_combo(combo):
        """Return tuple of just the gate filenames (order preserved)."""
        return tuple(os.path.basename(g) for g in combo)
    
    seen = set()
    unique_combos = []
    for combo in all_combos:
        norm = normalize_combo(combo)
        if norm not in seen:
            seen.add(norm)
            unique_combos.append(combo)

    group_sizes = []
    for combo in unique_combos:
        while len(group_sizes) < len(combo):
            group_sizes.append(0)
        group_sizes[len(combo)-1] += 1

    for size, count in enumerate(group_sizes):
        print(f"Total {size+1}-gate combinations: {count}")
    current_group = 0

    #all_combos = single_gates + two_gate_combos + three_gate_combos + four_gate_combos + five_gate_combos
    print(f"Total combinations to simulate: {len(unique_combos)}")

    file_exists = summary_csv_path.exists()
    with open(summary_csv_path, mode='a', newline='') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=['RowType', 'Combination', 'Expression', 'Num_Gates', 'Mismatch', 'Timestamp', 'Runtime_s'])
        if not file_exists:
            csv_writer.writeheader()
        total_combinations = 0
        total_mismatches = 0
        completed_combos = set()
        if(file_exists):
            with open(summary_csv_path, mode='r') as read_file:
                csv_reader = csv.DictReader(read_file)
                for row in csv_reader:
                    if not row.get('RowType'):
                        continue
                    if row['RowType'] != 'DATA':
                        continue
                    combo_name = row.get('Combination', '').strip()
                    if not combo_name:
                        continue
                    completed_combos.add(combo_name)
                    total_combinations += 1
                    if row['Mismatch'] == 'TRUE':
                        total_mismatches += 1

            print(f"❗ Found {len(completed_combos)} completed combinations. Resuming from last progress... ❗")
            print(f"Total combinations so far: {total_combinations}, with mismatches: {total_mismatches}")
            mismatch_percentage = (total_mismatches / total_combinations * 100) if total_combinations > 0 else 0
            print(f"Mismatch percentage so far: {mismatch_percentage:.2f}%")
        else:
            print("Starting fresh auto batch simulation.")

        #Time storage for calculations
        avg_time = 0
        expected_runtime = 0

        for combo in unique_combos:  
            if(len(combo) != last_num_gates):
                print(f"❗ Now processing {len(combo)}-gate combinations ❗")
                csv_file.flush()
                last_num_gates = len(combo)    
                avg_time = 0
                current_group += 1
            selected_gates = combo

            combo_name = "_".join([os.path.basename(g) for g in selected_gates])
            if combo_name in completed_combos:
                print(f"⚠️ Skipping already completed combination: {combo_name}")
                group_sizes[current_group] -= 1
                continue

            starting_time = time.time()

            # Connect gates using FIFO algorithm
            #print("DEBUG: selected_gates:", selected_gates)
            circuit, gate_pos_name, gate_metadata = gate_connector.connect_n_gates(selected_gates, wires=wire_length)
            gate = sqd_manipulator.circuit_to_gate(circuit)
            gate.gate_metadata = gate_metadata

            # Simulate the gate
            data, specific_gate_data, separate_results, failed = simulate_circuit(None, gate, current_sim, config_sim_store,max_corrections=5, called_from_callback=False, max_mismatches=1)
            
            #Write summary to CSV
            total_combinations += 1
            if separate_results:
                total_mismatches += 1

            end_time = time.time()
            runtime_s = end_time - starting_time
            csv_row = {
                'RowType': 'DATA' if not failed else 'ERROR',
                'Combination': "_".join([os.path.basename(g) for g in selected_gates]),
                'Expression': str(gate.expression) if not failed else "N/A",
                'Num_Gates': len(selected_gates),
                'Mismatch': 'TRUE' if separate_results else 'FALSE',
                'Timestamp': datetime.now().isoformat(),
                'Runtime_s': f"{runtime_s:.2f}"
            }



            csv_writer.writerow(csv_row)
            csv_file.flush()

            #Time calculations
            if avg_time == 0:
                avg_time = runtime_s
            else:
                avg_time = (avg_time + runtime_s) / 2.0
            expected_runtime = avg_time * group_sizes[current_group]
            group_sizes[current_group] = group_sizes[current_group] - 1
            #print(group_sizes[current_group])
            minutes = int(expected_runtime // 60)
            seconds = int(expected_runtime % 60)
            if group_sizes[current_group] <= 0:
                minutes = 0
                seconds = 0
            formatted_time = f"{minutes}:{seconds:02d}"

            # Save results just like the save_current function
            gate_name = gate.name if gate.name else f"unnamed_gate{str(combo)}"
            #Get the number of gates

            if separate_results:
                num_gates = f"{len(selected_gates)}_with_mismatches"
            else:
                num_gates = str(len(selected_gates))
                
            save_folder = Path("data") / "auto_batch_results" / f"{num_gates}" / gate_name
            save_folder.mkdir(parents=True, exist_ok=True)

            # Save truth table as PNG
            circuit_name = gate_name + "_truth_table"
            expression_name = gate.expression
            simulator_name = current_sim if current_sim else "default_simanneal"
            df = pd.DataFrame(data)
            fig, ax = plt.subplots(figsize=(len(df.columns)*1.5, len(df)/2))
            ax.axis('off')
            ax.axis('tight')

            # Add a title with the circuit and expression names
            plt.title(f"Circuit: {circuit_name}\nExpression: {expression_name}", fontsize=14, pad=20)
            table = ax.table(
                cellText=df.values,
                colLabels=df.columns,
                loc='center',
                cellLoc='center'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.2)

            plt.savefig(save_folder / f"{circuit_name}_truth_table.png", dpi=300, bbox_inches='tight')
            plt.close(fig)
            #print(f"✅ Truth table saved: {save_folder / f'{circuit_name}_truth_table.png'}")

            # Save specific gate data plot as PNG
            for i, gate_info in enumerate(specific_gate_data):
                # Convert plot_XY data manually
                x_coords = [dot[0] for dot in gate_info]
                y_coords = [dot[1] for dot in gate_info]
                colors = ['black' if dot[2] == '0' else 'blue' for dot in gate_info]
                markers = ['o' if dot[2] == '1' else 'o' for dot in gate_info]

                plt.figure(figsize=(6, 6))
                for x, y, c in zip(x_coords, y_coords, colors):
                    plt.scatter(x, y, color=c, s=60, edgecolors='none')
                plt.gca().invert_yaxis()
                plt.axis('off')
                plt.tight_layout()

                plt.savefig(save_folder / f"specific_gate_{i}.png", dpi=300, bbox_inches='tight')
                plt.close()
            #print(f"✅ Gate data plots saved under {save_folder}")

            config_file_path = save_folder / "simulation_config.txt"
            with open(config_file_path, "w") as f:
                f.write(f"Simulator: {simulator_name}\n")
                f.write(f"Configuration Parameters:\n")
                for key, value in config_sim_store.items():
                    f.write(f"{key}: {value}\n")
            #print(f"✅ Simulation configuration saved: {config_file_path}")
            if separate_results:
                print(f"✅ Completed simulation and saving for combination: {[os.path.basename(g) for g in selected_gates]} ⚠️ mismatch found")
            else:
                print(f"✅ Completed simulation and saving for combination: {[os.path.basename(g) for g in selected_gates]}")
            
            time_to_sleep = max(0.5, len(selected_gates) - 1)
            time_to_sleep = min(time_to_sleep, 4.0)
            time.sleep(time_to_sleep)  # Sleep to avoid overloading the simulator
            final_runtime = time.time() - starting_time
            print(f"⏲ Runtime: {final_runtime:<.2f}s, Estimated time remaining for group: {formatted_time}")
            


        # After all combinations, calculate mismatch statistics
        mismatch_percentage = (total_mismatches / total_combinations * 100) if total_combinations > 0 else 0
        csv_writer.writerow({'RowType': 'SUMMARY', 'Combination': 'TOTAL_COMBINATIONS', 'Num_Gates': total_combinations, 'Mismatch': False})
        csv_writer.writerow({'RowType': 'SUMMARY', 'Combination': 'TOTAL_MISMATCHES',   'Num_Gates': total_mismatches,   'Mismatch': False})
        csv_writer.writerow({'RowType': 'SUMMARY', 'Combination': 'MISMATCH_PERCENTAGE','Num_Gates': f"{mismatch_percentage:.2f}%", 'Mismatch': False})

  

    print("✅ Auto batch simulation completed for all gates.")

@callback(
    Input('save-gate-button', 'n_clicks'),
    State('gate-storage', 'data'),
    prevent_initial_call=True   
)

def save_gate(button, gate):
    if button is None or button <= 0:
        return

    if not gate or len(gate) == 0:
        print("⚠️ No files to select for saving gate.")
        return

    if(isinstance(gate, dict)):
        gate = sqd_manipulator.Gate.from_dict(gate)

    gate_name = gate.name if gate.name else "unnamed_gate"
    save_folder = Path("data") / "saved_gates"
    save_folder.mkdir(parents=True, exist_ok=True)
    gate_file_path = save_folder / f"{gate_name}.sqd"
    with open(gate_file_path, "w") as f:
        name, template = file_manager.sqd_template_create(gate, prefix=gate_name + "_", mode="save")
        #print(template)
        f.write(template)
    print(f"✅ Gate saved: {gate_file_path}")
    
