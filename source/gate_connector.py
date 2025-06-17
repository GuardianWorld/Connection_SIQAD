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
    
    