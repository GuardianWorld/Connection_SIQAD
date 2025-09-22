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

def estimate_max_depth(gates, inputs_per_gate=2):
    N = len(gates)
    max_depth = math.ceil(math.log(N, inputs_per_gate))
    return max_depth

def get_gate_boundaries(gate):
    min_n = min(dot.latcoord['n'] for dot in gate.db_dots)
    max_n = max(dot.latcoord['n'] for dot in gate.db_dots)
    return min_n, max_n

def boxes_overlap(box1, box2, padding=3):
    min_n1, max_n1 = box1
    min_n2, max_n2 = box2
    # Check for overlap with padding
    return not (max_n1 < min_n2 or max_n2 < min_n1)


def connect_n_gates_fifo(files, wires=2, min_horizontal_distance=7):
    gates = [sqd_manipulator.main_operator(file) for file in files]
    max_depth = estimate_max_depth(gates, inputs_per_gate=2)

    #Base Case: Only one gate
    if len(gates) == 1:
        return gates[0]
    #Base Case: Two gates
    #elif len(gates) == 2:
        #return connect_2_gates(gates[0], gates[1], wires=wires)
    #Base Case: Three gates
    #elif len(gates) == 3:
        #return connect_3_gates(gates[0], gates[1], gates[2], wires=wires)
    
    #Start with the first gate.
    circuit = gates[0]
    
    #FIFO queue the available input perturbers
    perturber_queue = [(p, circuit.pivot_dot) for p in circuit.input_perturbers]
    max_inputs_in_layer = 2
    inputs_in_layer = 2
    depth = 1

    for next_gate in gates[1:]:
        #Take the first available input from the queue
        current_perturber, parent_pivot = perturber_queue.pop(0)

        #Add Wire size to the depth, and, lower it.
        current_wire = wires

        n_shift = -2 if current_perturber.latcoord['n'] < parent_pivot.latcoord['n'] else 2
        m_shift = -1
        n = current_perturber.latcoord['n'] + n_shift
        m = current_perturber.latcoord['m'] + m_shift

        #collission-aware placement
        valid_position = False
        trial_wire = current_wire
        while not valid_position:
            n = current_perturber.latcoord['n'] + n_shift + trial_wire
            m = current_perturber.latcoord['m'] + m_shift + trial_wire

            sqd_manipulator.shift_gate_dots(next_gate, n, m)
            new_box = get_gate_boundaries(next_gate)

            too_close = False
            for existing_gate in circuit.gates if not isinstance(circuit, Gate) else [circuit]:
                existing_box = get_gate_boundaries(existing_gate)
                if boxes_overlap(new_box, existing_box, padding=min_horizontal_distance):
                    too_close = True
                    break

            if too_close:
                trial_wire += 1  # push further away
            else:
                valid_position = True


        """
        #add the amount of wire length to the shift.
        if(current_wire > 0):
            for i in range(current_wire):
                n += n_shift * 2
                m += m_shift * 2

        """
        #shift the gate
        sqd_manipulator.shift_gate_dots(next_gate, n, m)


        #add the wire dots.
        m_pos = current_perturber.latcoord['m']
        n_pos = current_perturber.latcoord['n']
        for i in range(current_wire):
            for j in range(2):
                m_pos += m_shift
                n_pos += n_shift
                dbdot = DBDot(2, {'n': n_pos, 'm': m_pos, 'l': 0}, None, '0x000000')
                dbdot.recalculate_physloc()
                next_gate.db_dots.append(dbdot)
        
        #merge the gates into a circuit
        circuit = Circuit(
            [circuit, next_gate] if isinstance(circuit, Gate) else circuit.gates + [next_gate], 
            input_perterbers=[p for p, _ in perturber_queue] + sqd_manipulator.get_input_perturbers(next_gate.db_dots),
            pivot_dot = circuit.pivot_dot
        )

        #update the perturber queue
        for p in sqd_manipulator.get_input_perturbers(next_gate.db_dots):
            perturber_queue.append((p, next_gate.pivot_dot))
        
        #update the inputs in the current layer
        inputs_in_layer -= 1
        print("Inputs left in layer:", inputs_in_layer)
        if inputs_in_layer == 0:
            print("Increasing depth to:", depth + 1)
            depth += 1
            inputs_in_layer = max_inputs_in_layer * 2
            max_inputs_in_layer *= 2

    return circuit
