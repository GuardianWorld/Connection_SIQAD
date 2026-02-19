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

def downstream_metadata_entry(metadata, current_metadata, simulation_data):
    #The logic is the following:
    # We grab the Output of the current one (it should match with the input of another one)
    output_positions = current_metadata.get("output")
    metadata_collection = []
    for m in metadata:
        input_positions = m.get("inputs")
        for out in output_positions:
            for inp in input_positions:
                    #print("Checking input:", inp, " against output position:", out)
                    if inp == out:
                        print("Match found for downstream metadata entry.")
                        #We check if this metadata entry already has stabilizers, if it does, we skip it, otherwise, we add it to the collection of metadata to be corrected.
                        if len(m.get("stabilizers", [])) > 0:
                            print(f"Gate {m.get('name')} already has stabilizers applied, skipping correction.")
                            continue
                        metadata_collection.append(m)
                        
    
    return metadata_collection

def check_wires(metadata, current_metadata, simulation_data):
    current_index = metadata.index(current_metadata)

    
    #We need to select based on the inputs
    #First, we check which of the TOP inputs mismatch with the logic inputs (original_inputs)
    mismatched_inputs = []
    original_inputs = current_metadata.get("original_inputs", [])
    real_inputs = current_metadata.get("inputs", [])
    #Now, we have both, we need to check if the input on the left, is the same as the ORIGINAL input on the right, and the same for the right input
    print("Original Inputs:", original_inputs)
    print("Real Inputs:", real_inputs)
    index = 0
    for inp in real_inputs:
        print("Checking input:", inp, " at index:", index)
        if original_inputs[index] == inp:
            print("Input matches original input.")
            #This means this input is the SAME as the logic input, no wires, we skip
            continue
        else:
            #Now, we check the values of both inputs
            #First, we calculate the X,Y of the inputs
            inp_N, inp_M, inp_L = inp
            inp_x, inp_y = classes.calculate_xy(inp_N, inp_M, inp_L)
            log_N, log_M, log_L = original_inputs[index]
            log_x, log_y = classes.calculate_xy(log_N, log_M, log_L)

            print("Input X,Y:", inp_x, inp_y)
            print("Logic Input X,Y:", log_x, log_y)
            #Now, we check the simulation data to see if they are matching
            inp_value = 0
            log_value = 0
            for data in simulation_data[0]:
                if(data[0] == inp_x and data[1] == inp_y):
                    inp_value = data[2]
                if(data[0] == log_x and data[1] == log_y):
                    log_value = data[2]
            
            print("Input Value:", inp_value)
            print("Logic Input Value:", log_value)
            if inp_value != log_value:
                print("Input value mismatches logic input value.")
                mismatched_inputs.append(inp)
                #We know this input is mismatched, which means, this upstream gate or wire is the one causing the issue7
        index += 1
    return mismatched_inputs

def upstream_metadata_entry(metadata, mismatched_inputs):
    #The logic is the following:
    # We grab the mismatched input, and we return the M that has that output.
                    
    metadata_collection = []
    for m in metadata:
        output_positions = m.get("output")
        for out in output_positions:
            for inp in mismatched_inputs:
                    #print("Checking mismatched input:", inp, " against output position:", out)
                    if inp == out:
                        print("Match found for upstream metadata entry.")
                        #We check if this metadata entry already has stabilizers, if it does, we skip it, otherwise, we add it to the collection of metadata to be corrected.
                        if len(m.get("stabilizers", [])) > 0:
                            print(f"Gate {m.get('name')} already has stabilizers applied, skipping correction.")
                            continue
                        metadata_collection.append(m)

    return metadata_collection


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
            metadata_collection = []
            print("Mismatch detected! Correcting gate...")

            #First step, check if any wires are mismatched upstream
            mismatched_inputs = check_wires(metadata, m, simulation_data)
            #print("Mismatched Inputs from Wires:", mismatched_inputs)
            if len(mismatched_inputs) > 0:
                #Multiple mismatched means we have to run correction on multiple gates.
                print("Mismatched wires detected.")
                metadata_collection = upstream_metadata_entry(metadata, mismatched_inputs)
            # now, we check if there is already stabilziers, if there are, we need to propagate the correction downstream

            if len(m.get("stabilizers", [])) > 0 and len(metadata_collection) == 0:
                print(f"Gate {name[0]} already has stabilizers applied, propagating correction.")
                # If it is sending 1, when it should be 0, we need to add stabilizers downstream;
                if int(expected_output) == 0 and int(sim_output_value) == 1:
                    #downstream correction
                    print("Applying downstream correction...")
                    metadata_collection = downstream_metadata_entry(metadata, m, simulation_data) #Need to get M for the PREVIOUS metadata entry below it, for now, we will keep it simple

            if(len(metadata_collection) == 0) and len(m.get("stabilizers", [])) == 0:
                metadata_collection.append(m) #If there are no mismatched wires, and no stabilizers, we just correct this gate, otherwise, we correct the collection of gates that we have found.
            print("Number of expected corrections to be applied:", len(metadata_collection))
            if len(metadata_collection) == 0:
                continue # It means that the gate was already corrected, but we could not fix anything, so, we allow the algorithm to continue
            else:
                for m in metadata_collection:
                    gate = correction_function(gate, m, expected_output, sim_output_value, boundaries)

            return gate, False
        #Compare the expected expression to the gate's expression

    return gate, True # It means that we already reached max correction.

def correction_function(gate, m, expected_output, sim_output_value, boundaries):
    name = m.get("name")
    name = classes.extract_gates_from_name(name)
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
    expected_output = 2 #Dummy value
    sim_output_value = 2 #Dummy value
        
    
    stabilizers = m.get("stabilizers", [])
    if len(stabilizers) > 0:
        print(f"Gate {name[0]} already has stabilizers applied, skipping correction.")
        return gate

    if name[0] == "AND":
        gate = AND_correction(gate, m, expected_output, sim_output_value, boundaries)
    elif name[0] == "OR":
        gate = OR_correction(gate, m, expected_output, sim_output_value, boundaries)
    elif name[0] == "NAND":
        gate = NAND_correction(gate, m, expected_output, sim_output_value, boundaries)
    else:
        print(f"No correction function defined for gate type: {name[0]}")
        return gate # Skip correction for undefined gate types
    return gate

def calculate_boundaries(positions):
    min_x = min(pos[0] for pos in positions)
    max_x = max(pos[0] for pos in positions)
    min_y = min(pos[1] for pos in positions)
    max_y = max(pos[1] for pos in positions)
    return (min_x, max_x, min_y, max_y)

##List of corrections to be applied
def up_correction(gate, metadata, gate_boundaries):
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
            M = metadata.get("original_inputs")[0][1] - 2
            gate.add_dot(NML=(N, M, L))
            print("Added stabilizer at N:", N, " M:", M, " L:", L)
            metadata["stabilizers"].append((N, M, L))
            return gate
        
def AND_correction(gate, metadata, expected_output, sim_output_value, gate_boundaries):
    #Here, we will analyze the gate and apply corrections specific to AND gates
    #Some situations have been found so far:
    # Under certain situations, such as AND on top or side, the input can be double activated.
    # Under certain situations, AND doesn't trigger at all.
    # Under some situations, AND overtriggers.
    #We will check each situation
    print(gate.name)
    if "stabilizers" not in metadata:
        metadata["stabilizers"] = []  # create the list if it doesn't exist

    #We first, check the situation of the last simulation data, to see what happened
    return up_correction(gate, metadata, gate_boundaries) #Temporary

    
    

def OR_correction(gate, metadata, expected_output, sim_output_value, gate_boundaries):
    #Or gate issues:
    # - Overtriggering when 0 inputs
    # - Not triggering when 1 input
    if "stabilizers" not in metadata:
        metadata["stabilizers"] = []  # create the list if it doesn't exist

    return up_correction(gate, metadata, gate_boundaries)

def NAND_correction(gate, metadata, expected_output, sim_output_value, gate_boundaries):
    print("NAND")
    if "stabilizers" not in metadata:
        metadata["stabilizers"] = []  # create the list if it doesn't exist

    return up_correction(gate, metadata, gate_boundaries)