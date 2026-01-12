from collections import deque
from source.classes import GATE_EXPRESSIONS, DBDot, Gate, Circuit
from source import sqd_manipulator
from sympy import symbols
from source import classes


def connect_2_gates(gate1, gate2, wire=None, wires=0, direction="left"):
    input_perturbers = []
    
    # Connect the output of gate1 to the input of gate2
    # Finds the perturber of gate 1 and connects gate 2 to it.
    n_shift = -2
    m_shift = -1

    current_perturber = None
    
    if direction == "left":
        current_perturber = sqd_manipulator.find_most_left_dot(gate1.input_perturbers)
    else:
        n_shift = 2
        current_perturber = sqd_manipulator.find_most_right_dot(gate1.input_perturbers)
        
    
    n = current_perturber.latcoord['n'] + n_shift
    m = current_perturber.latcoord['m'] + m_shift
    
    #step 1.2: add the amount of wire length to the shift. 
    #Keep in mind the pivot of the second gate is part of a wire as well.
    if(wires > 0):
        for i in range(wires):
            n += n_shift * 2
            m += m_shift * 2
    
    #step 1.3: shift the gate
    sqd_manipulator.shift_gate_dots(gate2, n, m)
    
    #step 1.4: add the wire dots.
    #it always goes 1 up, 2 to the side.
    m_pos = current_perturber.latcoord['m']
    n_pos = current_perturber.latcoord['n']
    for i in range(wires):
        for j in range(2):
            m_pos += m_shift
            n_pos += n_shift
            dbdot = DBDot(2, {'n': n_pos, 'm': m_pos, 'l': 0}, None, '0x000000')
            dbdot.recalculate_physloc()
            gate2.db_dots.append(dbdot)
    
    #step 2: get a list of the input perturbers of both gates (remaining).
    for perturber in gate1.input_perturbers:
        if(perturber != current_perturber):
            input_perturbers.append(perturber)
    
    gate2_perturbers = sqd_manipulator.get_input_perturbers(gate2.db_dots)
    
    for perturber in gate2_perturbers:
        input_perturbers.append(perturber)
    
    #step 3: get the pivot dot of gate 1
    pivot_dot = gate1.pivot_dot
    
    #step 4: build the circuit class
    circuit = Circuit([gate1, gate2], input_perturbers, pivot_dot)
    
    #step 5: return the circuit
    return circuit
    
    
def connect_3_gates(gate1, gate2, gate3, wires=2):
    # Connect the output of gate1 to the input of gate2
    # Connect the output of gate2 to the input of gate3
    
    input_perturbers = []
    
    #step 0: grab the perturbers of gate 2 and 3
    gate2_perturbers = sqd_manipulator.get_input_perturbers(gate2.db_dots)
    gate3_perturbers = sqd_manipulator.get_input_perturbers(gate3.db_dots)
    
    #step 1: connect gate 1 to gate 2
    circuit1 = connect_2_gates(gate1, gate2, wires=wires)
    
    #step 2: connect gate 2 to gate 3
    circuit2 = connect_2_gates(gate1, gate3, wires=wires, direction="right")
    
    #step 3 make a new circuit based on the two generated circuits
    input_perturbers1 = sqd_manipulator.get_input_perturbers(sqd_manipulator.circuit_to_gate(circuit1).db_dots)
    input_perturbers2 = sqd_manipulator.get_input_perturbers(sqd_manipulator.circuit_to_gate(circuit2).db_dots)
    input_perturbers = input_perturbers1 + input_perturbers2
    circuit = Circuit([gate1, gate2, gate3], input_perturbers, circuit1.pivot_dot)
    
    return circuit 

def calculate_max_depth(gates):
    depth = 1
    perturbers_remaining = 0
    perturber_aux = 0
    perturber_per_depth = []
    #first step: calculate the max depth with a virtual connection
    perturbers_remaining = len(gates[0].input_perturbers)
    perturber_per_depth.append(perturbers_remaining)
    gates_per_depth = []
    #On the first depth, only one gate can be placed.
    gates_per_depth.append(1)
    gates_per_depth_aux = 0

    for gate in gates[1:]:
        #On the first gate, grab its perturbers
        #On the next gates, subtract one perturber (the one being used to connect) and add the new perturbers on an aux list (next layer).
        # If the perturbers remaining is 0, increase depth and set the perturbers remaining to the aux list length.
        perturbers_remaining -= 1
        perturber_aux += len(gate.input_perturbers)
        gates_per_depth_aux += 1
        if perturbers_remaining == 0:
            depth += 1
            perturbers_remaining = perturber_aux
            perturber_per_depth.append(perturber_aux)
            perturber_aux = 0
            gates_per_depth.append(gates_per_depth_aux)
            gates_per_depth_aux = 0

    if perturber_aux > 0:
        perturber_per_depth.append(perturber_aux)
        gates_per_depth.append(gates_per_depth_aux)
    return depth, perturber_per_depth, gates_per_depth

def analyze_gate_depths(gates):
    """
    Analyze the depth (FIFO order) of each gate in the circuit.

    Returns:
        depth_map: {gate: depth}
        max_depth: int
        gates_per_depth: dict[int, list[gate]]
        perturbers_per_depth: dict[int, list[perturber]]
    """

    max_depth, perturbers_per_depth, gates_per_depth = calculate_max_depth(gates=gates)
    depth_map = {}
    queue = [(0, gates[0])]  # (depth, gate)
    idx = 1
    while queue:
        depth, gate = queue.pop(0)
        depth_map[gate] = depth
        for _ in gate.input_perturbers:
            if idx < len(gates):
                queue.append((depth + 1, gates[idx]))
                idx += 1
    max_depth = max(depth_map.values())

    return depth_map, max_depth, gates_per_depth, perturbers_per_depth

def extract_gate_metadata(gates, depth_map, output_input_map):
    """
    Collect spatial and geometric metadata for each gate.

    Returns:
        List[Dict] of gate metadata.
    """
    gate_metadata = []
    for g in gates:
        has_output_as_input = False
        original_inputs = []
        try:
            center = (g.pivot_dot.latcoord['n'], g.pivot_dot.latcoord['m'], g.pivot_dot.latcoord['l'])
        except Exception:
            center = (0, 0)

        db_positions = []
        for d in getattr(g, 'db_dots', []):
            try:
                db_positions.append((d.latcoord['n'], d.latcoord['m'], d.latcoord['l']))
            except Exception:
                continue

        #Inputs and outputs can be derived from input_perturbers and output_dot
        input_coords = []
        output_coords = []
        for inp in g.input_perturbers:
            try:
                input_coords.append((inp.latcoord['n'], inp.latcoord['m'], inp.latcoord['l']))
                original_inputs.append((inp.latcoord['n'], inp.latcoord['m'], inp.latcoord['l']))

                #Check the output_input_map to see if this input is actually an output from another gate
                for out_dot, in_dot in output_input_map.items():
                    if inp == in_dot:
                        #print(f"Gate {g.name} input {inp.latcoord} is connected to output {out_dot.latcoord} of another gate.")
                        input_coords[-1] = (out_dot.latcoord['n'], out_dot.latcoord['m'], out_dot.latcoord['l'])
                        has_output_as_input = True
            except Exception:
                continue
        

        try:
            output_coords.append((g.output_dot.latcoord['n'], g.output_dot.latcoord['m'], g.output_dot.latcoord['l']))
        except Exception:
            output_coords = []
        gate_metadata.append({
            "name": g.name,
            "center": center,
            "db_positions": db_positions,
            "orientation": getattr(g, 'orientation', 0),
            "depth": depth_map.get(g, 0),
            "inputs": input_coords,
            "output": output_coords,
            "has_output_as_input": has_output_as_input,
            "original_inputs": original_inputs,
        })

    return gate_metadata

def initialize_circuit_and_symbols(gates):
    """
    Initialize the circuit, perturber queue, gate position names, and symbol map for the root gate.
    """
    circuit = gates[0]
    perturber_queue = [(p, circuit.pivot_dot) for p in circuit.input_perturbers]
    gate_pos_name = [(circuit.name, circuit.pivot_dot)]

    # --- LOGICAL EXPRESSION INITIALIZATION ---
    symbol_map = {}
    input_counter = 0
    for inp in circuit.input_perturbers:
        sym = symbols(f"x{input_counter}")
        symbol_map[inp] = sym
        input_counter += 1

    c_name = classes.extract_gates_from_name(circuit.name)[0]
    circuit.expression = GATE_EXPRESSIONS[c_name]([symbol_map[p] for p in circuit.input_perturbers])
    symbol_map[circuit.pivot_dot] = circuit.expression

    return circuit, perturber_queue, gate_pos_name, symbol_map, input_counter

def connect_fifo_gates(
    gates, circuit, symbol_map, perturber_queue, depth_map, max_depth, wires, input_counter
):
    """
    Connect gates sequentially in FIFO order, updating both physical layout and logical expressions.
    """
    gate_pos_name = [(circuit.name, circuit.pivot_dot)]

    #Connect all outputs of every single gate
    output_input_map = {}
    for next_gate in gates[1:]:
        current_perturber, parent_pivot = perturber_queue.pop(0)

        # --- PHYSICAL CONNECTION ---
        gate_depth = depth_map[next_gate]
        current_wire = max(1, wires * (max_depth - gate_depth + 1))
        if gate_depth == max_depth:
            current_wire = wires

        n_shift = -2 if current_perturber.latcoord["n"] < parent_pivot.latcoord["n"] else 2
        m_shift = -1
        n = current_perturber.latcoord["n"] + n_shift
        m = current_perturber.latcoord["m"] + m_shift

        for _ in range(current_wire):
            n += n_shift * 2
            m += m_shift * 2

        sqd_manipulator.shift_gate_dots(next_gate, n, m)

        # Add wire dots
        m_pos = current_perturber.latcoord["m"]
        n_pos = current_perturber.latcoord["n"]
        for _ in range(current_wire):
            for _ in range(2):
                m_pos += m_shift
                n_pos += n_shift
                dbdot = DBDot(2, {"n": n_pos, "m": m_pos, "l": 0}, None, "0x000000")
                dbdot.recalculate_physloc()
                next_gate.db_dots.append(dbdot)

        # --- LOGICAL CONNECTION ---
        gate_inputs = []
        for p in next_gate.input_perturbers:
            if p in symbol_map:
                gate_inputs.append(symbol_map[p])
            else:
                sym = symbols(f"x{input_counter}")
                symbol_map[p] = sym
                gate_inputs.append(sym)
                input_counter += 1

        next_c_name = classes.extract_gates_from_name(next_gate.name)[0]
        next_gate.expression = GATE_EXPRESSIONS[next_c_name](gate_inputs)
        symbol_map[next_gate.pivot_dot] = next_gate.expression

        # Replace used perturber expression
        symbol_to_replace = symbol_map[current_perturber]
        for k in list(symbol_map.keys()):
            symbol_map[k] = symbol_map[k].subs(symbol_to_replace, next_gate.expression)
        del symbol_map[current_perturber]

        # Merge gates
        circuit = Circuit(
            [circuit, next_gate] if isinstance(circuit, Gate) else circuit.gates + [next_gate],
            input_perturbers=[p for p, _ in perturber_queue] + sqd_manipulator.get_input_perturbers(next_gate.db_dots),
            pivot_dot=circuit.pivot_dot,
        )

        gate_pos_name.append((next_gate.name, next_gate.pivot_dot))

        # Add new perturbers
        for p in sqd_manipulator.get_input_perturbers(next_gate.db_dots):
            perturber_queue.append((p, next_gate.pivot_dot))

        #collect output from the top gate just connected
        output_input_map[next_gate.output_dot] = current_perturber

    # Finalize expression
    circuit.expression = max(symbol_map.values(), key=lambda v: len(str(v)))
    circuit.input_symbols = [symbol_map[p] for p in circuit.input_perturbers]


    return circuit, gate_pos_name, symbol_map, output_input_map


def connect_n_gates(files, wires=2, strategy="FIFO"):
    gates = [sqd_manipulator.main_operator(file) for file in files]
    depth_map, max_depth, gates_per_depth, perturbers_per_depth = analyze_gate_depths(gates)
    circuit, perturber_queue, gate_pos_name, symbol_map, input_counter = initialize_circuit_and_symbols(gates)
    if strategy == "FIFO":
        circuit, gate_pos_name, symbol_map, output_input_map = connect_fifo_gates(
            gates,
            circuit,
            symbol_map,
            perturber_queue,
            depth_map,
            max_depth,
            wires,
            input_counter,
        )
    else:
        raise ValueError(f"Unknown connection strategy: {strategy}")
        
    gate_metadata = extract_gate_metadata(gates, depth_map, output_input_map)
    

    return circuit, gate_pos_name, gate_metadata