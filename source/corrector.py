import os
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
from source.classes import GATE_EXPRESSIONS, DBDot, Gate, Circuit
import source.classes as classes
from sympy import symbols
import re
from sympy.logic.boolalg import truth_table

def truth_table_index(input_values):
    """
    Convert list of 0/1 input bits into truth table row index.
    Example: [0,1] -> 1
             [1,0] -> 2
             [1,1] -> 3
    """
    index = 0
    
    for bit in input_values:
        index = (index << 1) | int(bit)
    return index

def main_correction(gate, metadata, simulation_data):
    # Apply corrections based on metadata
    #print(metadata)
    print("Starting correction process...")
    #We need to use only the LAST simulation data, as it is where the mismatches will be found
    simulation_data = simulation_data[-1:]
    #First, check every gate, top to botton, if it needs correction
    for m in metadata:
        # check every gate individually for its: 
        # expression
        # position
        # input/output
        # expected behavior
        #grab name
        name = m.get("name")
        name = classes.extract_gates_from_name(name)

        #Make the INPUT symbols. Gotta generate them from scratch
        input_symbols = []
        for i in range(len(m.get("inputs"))):
            input_symbols.append(symbols(f'x{i+1}'))
        
        #Generate the expected expression
        expected_expression = GATE_EXPRESSIONS.get(name[0])(input_symbols)
        #print("Expected Expression: ", expected_expression)
        expected = []
        for values, output in truth_table(expected_expression, input_symbols):
            expected.append(int(bool(output)))
        #print("Expected Truth Table: ", expected)

        #Now, we grab the gate OUTPUT position from the metadata
        output_position = m.get("output")
        #We calculate the X and Y from the NML
        N,M,L = output_position[0]
        x,y = classes.calculate_xy(N, M, L)
        #print("Output Position from Metadata: ", output_position)
        #print("Output X: ", x, " Output Y: ", y)

        #Now, we grab the simulation data output VALUE (3rd value) at that position
        sim_output_value = None
        for data in simulation_data[0]:
            if(data[0] == x and data[1] == y):
                sim_output_value = data[2]
                break
        #for data in simulation_data:
        #print("Simulated Output Value at Position: ", sim_output_value)

        #Check the inputs to see where in the truth table we are
        input_values = []
        found_inputs = []
        for inp in m.get("inputs"):
            inp_N, inp_M, inp_L = inp
            inp_x, inp_y = classes.calculate_xy(inp_N, inp_M, inp_L)
            print("Input Position x: ", inp_x, " Input Position y: ", inp_y)

            #If they do not exist, we use 0, else, we use the value at that position
            inp_value = 0
            for data in simulation_data[0]:
                if(data[0] == inp_x and data[1] == inp_y):
                    inp_value = data[2]
                    found_inputs.append(data)
                    break
            input_values.append(inp_value)
        #print("Input Values at Positions: ", input_values)

        #Now, we find the expected output from the truth table
        tt_index = truth_table_index(input_values)
        expected_output = expected[tt_index]
            
        #If they do not match, we need to correct the gate
        #Calculate boundaries first, we will need it.
        gate_boundaries = []
        for pos in m.get("inputs"):
            N, M, L = pos
            x, y = classes.calculate_xy(N, M, L)
            gate_boundaries.append((x,y))
        
        #Get the pivot
        N, M, L = m.get("center")
        x, y = classes.calculate_xy(N, M, L)
        gate_boundaries.append((x,y))
        boundaries = calculate_boundaries(gate_boundaries)
        print(f"Current Gate: {name[0]}, Expected Output from Truth Table: {expected_output}, Simulated Output: {sim_output_value}")
        if(int(expected_output) != int(sim_output_value)):
            print("Mismatch detected! Correcting gate...")
            #print(f"Current Gate: {name[0]}, Expected Output from Truth Table: {expected_output}, Simulated Output: {sim_output_value}")
            stabilizers = m.get("stabilizers", [])
            #print(f"Current stabilizers for gate {name[0]}: {stabilizers}")

            if len(stabilizers) > 0:
                #print(f"Gate {name[0]} already has stabilizers applied, skipping correction.")
                continue

            if name[0] == "AND":
                gate = AND_correction(gate, m, found_inputs, simulation_data, tt_index, expected_output, sim_output_value, boundaries)
            elif name[0] == "OR":
                gate = OR_correction(gate, m, found_inputs, simulation_data, tt_index, expected_output, sim_output_value, boundaries)
            else:
                print(f"No correction function defined for gate type: {name[0]}")
                continue
            return gate
        #Compare the expected expression to the gate's expression

    return gate

def calculate_boundaries(positions):
    min_x = min(pos[0] for pos in positions)
    max_x = max(pos[0] for pos in positions)
    min_y = min(pos[1] for pos in positions)
    max_y = max(pos[1] for pos in positions)
    return (min_x, max_x, min_y, max_y)

##List of corrections to be applied
def up_correction(gate, metadata, found_inputs, gate_boundaries):
        #We could check if the gate is triggering when only one input is active, this is also easier to check
        #print("Gate Boundaries:", gate_boundaries)
        min_x, max_x, min_y, max_y = gate_boundaries
        #Check if there are any DBs on top of the gate boundaries
        dbs_in_area = []
        for dot in gate.db_dots:
            if dot.physloc['x'] < min_x and dot.physloc['x'] > max_x and dot.physloc['y'] < min_y and dot.physloc['y'] > max_y:
                dbs_in_area.append(dot)
        #print("DBs in Gate Area:", dbs_in_area)
        # If there are DBs in the area, we have to add to the side, otherwise, we add on top
        if len(dbs_in_area) > 0:
            print("Adding stabilizers to the side of the gate.")
            #Add stabilizers to one side of the gate.
        elif len(dbs_in_area) == 0:
            print("Adding stabilizers on top of the gate.")
            #Add stabilizers on top of the gate, in the middle. At least one in the middle.
            N, M, L = metadata.get("center")
            L = 0
            #Shift up until after the inputs
            M = metadata.get("inputs")[0][1] - 2
            gate.add_dot(NML=(N, M, L))
            print("Added stabilizer at N:", N, " M:", M, " L:", L)
            metadata["stabilizers"].append((N, M, L))
            return gate
        
def AND_correction(gate, metadata, found_inputs, simulation_data, tt_index, expected_output, sim_output_value, gate_boundaries):
    #Here, we will analyze the gate and apply corrections specific to AND gates
    #Some situations have been found so far:
    # Under certain situations, such as AND on top or side, the input can be double activated.
    # Under certain situations, AND doesn't trigger at all.
    # Under some situations, AND overtriggers.
    #We will check each situation

    print("AND?")
    if "stabilizers" not in metadata:
        metadata["stabilizers"] = []  # create the list if it doesn't exist

    def situation_1(gate, metadata, found_inputs):
        pass
    #We first, check the situation of the last simulation data, to see what happened
    if(int(expected_output) == 1 and int(sim_output_value) == 0):
        return up_correction(gate, metadata, found_inputs, gate_boundaries) #Temporary
    elif(int(expected_output) == 0 and int(sim_output_value) == 1):
        return up_correction(gate, metadata, found_inputs, gate_boundaries)

    
    

def OR_correction(gate, metadata, found_inputs, simulation_data, tt_index, expected_output, sim_output_value, gate_boundaries):
    #Or gate issues:
    # - Overtriggering when 0 inputs
    # - Not triggering when 1 input
    print("OR?")
    if "stabilizers" not in metadata:
        metadata["stabilizers"] = []  # create the list if it doesn't exist

    return up_correction(gate, metadata, found_inputs, gate_boundaries)

