from classes import DBDot, Gate, Circuit
import sqd_manipulator



def connect_2_gates_left(gate1, gate2, wire=None, wires=0):
    
    input_perturbers = []
    
    # Connect the output of gate1 to the input of gate2
    # Finds the firstmost perturber of gate 1 and connects gate 2 to it.
    
    #wire: x - - 
    #      - - - 
    #      - - x 
    
    #step 1: shifts the second gate position to place the pivot of it near the input perturber of gate 2 (+- some differences of course)
    leftmost_perturber = sqd_manipulator.find_most_left_dot(gate1.input_perturbers)
    n = leftmost_perturber.latcoord['n'] - 2
    m = leftmost_perturber.latcoord['m'] - 1
    
    #step 1.2: add the amount of wire length to the shift. 
    #Keep in mind the pivot of the second gate is part of a wire as well.
    if(wires > 0 and wire != None):
        for i in range(wires):
            if i == 0:
                n -= 3
            else:
                n -= 4
            m -= 4
    
    #step 1.3: shift the gate
    sqd_manipulator.shift_gate_dots(gate2, n, m)
    
    #step 2: get a list of the input perturbers of both gates (remaining).
    for perturber in gate1.input_perturbers:
        if(perturber != gate1.input_perturbers[0]):
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
    
    
    
    
    
    
    
    
    