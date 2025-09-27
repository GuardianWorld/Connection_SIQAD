from collections import deque
from source.classes import DBDot, Gate, Circuit
from source import sqd_manipulator

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
    
def connect_n_gates(files, wires=2):
    if len(files) < 2:
        raise ValueError("At least two gates are required to connect.")
    
    # Load all gates from the provided files
    gates = [sqd_manipulator.main_operator(file) for file in files]

    # Start by connecting the first two gates
    direction = "left"
    current_circuit = connect_2_gates(gates[0], gates[1], wires=wires, direction=direction)
    
    # Iteratively connect the remaining gates
    for i in range(2, len(gates)):
        direction = "right" if (i % 2 == 0) else "left"
        current_gate = gates[i]
        merged_circuit = sqd_manipulator.circuit_to_gate(current_circuit)
        current_circuit = connect_2_gates(merged_circuit, current_gate, wires=wires, direction=direction)
    
    return current_circuit

def connect_n_gates_balanced(files, base_wires=2):
    # Load all gates from the provided files
    gates = [sqd_manipulator.main_operator(f) for f in files]

    def connect_group(group, depth=0, direction="left"):
        # Increase wire lenght with depth to avoid overlapping wires
        wires = base_wires + depth

        # Base case: single gate
        if len(group) == 1:
            return group[0]
        # Base case: two gates
        elif len(group) == 2:
            return connect_2_gates(group[0], group[1], wires=wires, direction=direction)
        
        # Recursive case: split into halves
        mid = len(group) // 2
        left_circuit = connect_group(group[:mid], depth + 1, direction="left")
        right_circuit = connect_group(group[mid:], depth + 1, direction="right")

        # Merge the two halves
        merge_direction = "left" if depth % 2 == 0 else "right"

        return connect_2_gates(
            sqd_manipulator.circuit_to_gate(left_circuit),
            sqd_manipulator.circuit_to_gate(right_circuit),
            wires=wires,
            direction=merge_direction
        )

    return connect_group(gates)

import math

def get_gate_boundaries(gate):
    min_n = min(dot.latcoord['n'] for dot in gate.db_dots)
    max_n = max(dot.latcoord['n'] for dot in gate.db_dots)
    return min_n, max_n

def boxes_overlap(box1, box2, padding=3):
    min_n1, max_n1 = box1
    min_n2, max_n2 = box2
    # Check for overlap with padding
    return not (max_n1 < min_n2 or max_n2 < min_n1)

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


def connect_n_gates_fifo(files, wires=2, min_horizontal_distance=7):
    gates = [sqd_manipulator.main_operator(file) for file in files]

    #Precompute max depth, gates per depth and perturbers per depth
    max_depth, perturbers_per_depth, gates_per_depth = calculate_max_depth(gates)

    # Precompute depth of each gate
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
    constant = 2
    # Start with the root gate
    circuit = gates[0]
    perturber_queue = [(p, circuit.pivot_dot) for p in circuit.input_perturbers]

    #Save the name of the gate, and the middle of its boundaries for name placement above its pivot
    gate_pos_name = []
    gate_pos_name.append((gates[0].name, gates[0].pivot_dot))

    for next_gate in gates[1:]:
        current_perturber, parent_pivot = perturber_queue.pop(0)

        # Longer wires for higher layers
        gate_depth = depth_map[next_gate]
        current_wire = max(1, wires * (max_depth - gate_depth + 1))
        if(gate_depth == max_depth):
            current_wire = 1

        n_shift = -2 if current_perturber.latcoord['n'] < parent_pivot.latcoord['n'] else 2
        m_shift = -1
        n = current_perturber.latcoord['n'] + n_shift
        m = current_perturber.latcoord['m'] + m_shift

        for _ in range(current_wire):
            n += n_shift * 2
            m += m_shift * 2

        sqd_manipulator.shift_gate_dots(next_gate, n, m)

        # Add the wire dots
        m_pos = current_perturber.latcoord['m']
        n_pos = current_perturber.latcoord['n']
        for _ in range(current_wire):
            for _ in range(2):
                m_pos += m_shift
                n_pos += n_shift
                dbdot = DBDot(2, {'n': n_pos, 'm': m_pos, 'l': 0}, None, '0x000000')
                dbdot.recalculate_physloc()
                next_gate.db_dots.append(dbdot)

        # Merge gates into circuit
        circuit = Circuit(
            [circuit, next_gate] if isinstance(circuit, Gate) else circuit.gates + [next_gate],
            input_perterbers=[p for p, _ in perturber_queue] + sqd_manipulator.get_input_perturbers(next_gate.db_dots),
            pivot_dot=circuit.pivot_dot
        )

        # Save gate name and position for labeling
        gate_pos_name.append((next_gate.name, next_gate.pivot_dot))

        # Add new perturbers to the queue
        for p in sqd_manipulator.get_input_perturbers(next_gate.db_dots):
            perturber_queue.append((p, next_gate.pivot_dot))

    #calculate all DBS in the circuit


    return circuit, gate_pos_name

def connect_n_gates_bottom_up(files, wires=2, min_horizontal_distance=7):
    gates = [sqd_manipulator.main_operator(f) for f in files]

    # Step 1: Calculate max depth, perturbers, and gates per depth
    max_depth, perturbers_per_depth, gates_per_depth = calculate_max_depth(gates)
    print("Max Depth:", max_depth)
    print("Gates per depth:", gates_per_depth)
    print("Perturbers per depth:", perturbers_per_depth)

    # Step 2: Assign gates to layers
    layers = []
    idx = 0
    for num_gates in gates_per_depth:
        layer = gates[idx:idx + num_gates]
        layers.append(layer)
        idx += num_gates

    # Step 3: Horizontal placement of leaves
    positions = {}  # gate -> (n, m)
    current_x = 0
    leaf_layer = layers[-1]
    for gate in leaf_layer:
        positions[gate] = (current_x, max_depth)  # x = current_x, y = depth
        current_x += min_horizontal_distance

    # Step 4: Bottom-up placement for parents
    for depth in reversed(range(max_depth)):
        layer = layers[depth]
        for i, gate in enumerate(layer):
            # Children are gates in the next layer that this gate connects to
            children = layers[depth + 1] if depth + 1 < len(layers) else []
            # Find which children this parent connects to
            gate_children = [c for c in children if gate in c.input_perturbers]
            if gate_children:
                # Parent n = midpoint of its children
                min_x = min(positions[c][0] for c in gate_children)
                max_x = max(positions[c][0] for c in gate_children)
                parent_x = (min_x + max_x) / 2
            else:
                parent_x = 0
            positions[gate] = (parent_x, depth)

    # Step 5: Apply positions and create wires
    for gate in gates:
        n_pos, m_pos = positions[gate]
        n_shift = n_pos - gate.pivot_dot.latcoord['n']
        m_shift = m_pos - gate.pivot_dot.latcoord['m']
        sqd_manipulator.shift_gate_dots(gate, n_shift, m_shift)

        # Connect wires from parent(s) to this gate
        for p_gate in gates:
            if gate in p_gate.input_perturbers:
                parent_n, parent_m = positions[p_gate]
                # Simple straight-line wires
                n_step = 1 if n_pos > parent_n else -1
                m_step = 1 if m_pos > parent_m else -1
                n_wire, m_wire = parent_n, parent_m
                while n_wire != n_pos or m_wire != m_pos:
                    if n_wire != n_pos:
                        n_wire += n_step
                    if m_wire != m_pos:
                        m_wire += m_step
                    dbdot = DBDot(2, {'n': n_wire, 'm': m_wire, 'l': 0}, None, '0x000000')
                    dbdot.recalculate_physloc()
                    gate.db_dots.append(dbdot)

    # Step 6: Merge all gates into a circuit
    circuit = Circuit(
        gates,
        input_perterbers=[p for g in gates for p in g.input_perturbers],
        pivot_dot=gates[0].pivot_dot
    )

    return circuit
