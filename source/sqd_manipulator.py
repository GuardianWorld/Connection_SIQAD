import math
import xml.etree.ElementTree as ET
from xmlrpc.client import MAXINT
from source.classes import DBDot, Gate
import os
import itertools
from copy import deepcopy

def parse_sqd_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    dots = []
    for dbdot in root.findall(".//dbdot"):
        layer_id = int(dbdot.find("layer_id").text)
        latcoord = {
            'n': int(dbdot.find("latcoord").attrib['n']),
            'm': int(dbdot.find("latcoord").attrib['m']),
            'l': int(dbdot.find("latcoord").attrib['l'])
        }
        physloc = {
            'x': float(dbdot.find("physloc").attrib['x']),
            'y': float(dbdot.find("physloc").attrib['y'])
        }
        color = dbdot.find("color").text

        dot = DBDot(layer_id, latcoord, physloc, color)
        dots.append(dot)
        
    return dots

def get_input_perturbers(dots):
    perturbers = []
    max_m = max(abs(dot.latcoord['m']) for dot in dots)
    
    for dot in dots:
        #Get the perturbers at the TOP of the list (Highest m) 
        #Since all are Y shaped, the perturber is on the TOP 99% of the time HOPEFULLY
        if abs(dot.latcoord['m']) == max_m:
            perturbers.append(dot)
    
    return perturbers   
    

def set_dots_to_minimum(dots):
    # Get the perturber at the BOTTOM of the list (Lowest m)
    
    min_m = min(abs(dot.latcoord['m']) for dot in dots) #find the minimum value of m
    min_n = 0
    pivot_dot = None
    for dot in dots:
        if abs(dot.latcoord['m']) == min_m:
            min_n = dot.latcoord['n']
            min_m = dot.latcoord['m']
            pivot_dot = dot
    
    for dot in dots:
        dot.latcoord['m'] = dot.latcoord['m'] - min_m
        dot.latcoord['n'] = dot.latcoord['n'] - min_n
        dot.recalculate_physloc()
    
    return dots, pivot_dot

def find_most_left_dot(dots):
    min_n = min(dot.latcoord['n'] for dot in dots)
    min_m = 0
    left_dot = None
    for dot in dots:
        if dot.latcoord['n'] == min_n:
            min_n = dot.latcoord['n']
            left_dot = dot
    
    return left_dot

def find_most_right_dot(dots):
    max_n = max(dot.latcoord['n'] for dot in dots)
    max_m = 0
    right_dot = None
    for dot in dots:
        if dot.latcoord['n'] == max_n:
            max_n = dot.latcoord['n']
            right_dot = dot
    
    return right_dot

def find_pivot_dot(dots):
    # Get the perturber at the BOTTOM of the list (Lowest m)
    
    min_m = min(abs(dot.latcoord['m']) for dot in dots) #find the minimum value of m
    min_n = 0
    pivot_dot = None
    for dot in dots:
        if abs(dot.latcoord['m']) == min_m:
            min_n = dot.latcoord['n']
            min_m = dot.latcoord['m']
            pivot_dot = dot
    
    return pivot_dot

def find_output_dot(dots, pivot_dot):
    closest_dot = None
    closest_m = MAXINT
    closest_n = MAXINT
    for dot in dots:
        #Get the nearest dot to 0, 0
        
        if abs(dot.latcoord['m']) <= abs(closest_m) and abs(dot.latcoord['n']) <= abs(closest_n):
            if(dot.latcoord['m'] == pivot_dot.latcoord['m'] and dot.latcoord['n'] == pivot_dot.latcoord['n']):
                continue
            closest_m = dot.latcoord['m']
            closest_n = dot.latcoord['n']
            closest_dot = dot
    
    return closest_dot

def shift_gate_dots(gate, shiftn, shiftm):
    for dot in gate.db_dots:
        dot.latcoord['n'] = dot.latcoord['n'] + shiftn
        dot.latcoord['m'] = dot.latcoord['m'] + shiftm
        dot.recalculate_physloc()
        
    return gate
    
        
def main_operator(file):
    dots = parse_sqd_file(file)
        
    dots, pivot_dot = set_dots_to_minimum(dots)
    perturbers = get_input_perturbers(dots)
    output_dot = find_output_dot(dots, pivot_dot)
    if os.name == 'posix':
        name = file.split("/")[-1]
    else:
        name = file.split("\\")[-1]
    name = name.split(".")[0]
    gate = Gate(dots, pivot_dot, perturbers,output_dot, name)
    return gate
    
def circuit_to_gate(circuit):
    db_dots = []
    try:
        for gate in circuit.gates:
            for dot in gate.db_dots:
                db_dots.append(dot)
        
        pivot_dot = circuit.pivot_dot
        input_perturbers = circuit.input_perturbers
        output_dot = circuit.gates[0].output_dot
        name = "Circuit"
        for gate in circuit.gates:
            name += f"_{gate.name}"
        new_gate = Gate(db_dots, pivot_dot, input_perturbers,output_dot, name, circuit.expression, circuit.input_symbols)
        return new_gate
    except AttributeError as a:
        return circuit



# Tester

def combinators(gate):
    perturbers = gate.input_perturbers
    num_perturbers = len(perturbers)    
    gates = []
    
    for combination in itertools.product([True, False], repeat=num_perturbers):
        selected_perturbers = [perturbers[i] for i in range(num_perturbers) if combination[i]]
        new_gate = deepcopy(gate)
        for perturber in selected_perturbers:
            new_gate.remove_input(perturber)
        gates.append(new_gate)
    
    return gates
        
    
## Results

def read_result_plusXY(file, gate):
    tree = ET.parse(file)
    root = tree.getroot()
    DB_list = []
    final_list = []

    i = 0

    
    biggest = []
    lowest_energy = math.inf

    for dbdot in root.findall(".//dbdot"):
        x = float(dbdot.get("x"))
        y = float(dbdot.get("y"))

        DB_list.append([x, y])

    for dist in root.findall(".//dist"):
        energy = float(dist.get("energy"))
        count = int(dist.get("count"))
        physically_valid = int(dist.get("physically_valid")) == 1
        state_count = int(dist.get("state_count"))
        symbol = dist.text
        if not physically_valid:
            continue

        if energy < lowest_energy:
            biggest = [energy, count, physically_valid, state_count, symbol]
            lowest_energy = energy

    symbol = biggest[4]

    symbol = symbol.replace("-", "1")

    for i in range(len(DB_list)):
        x = DB_list[i][0]
        y = DB_list[i][1]
        final_list.append([x, y, symbol[i]])

    #for db in final_list:
        #print(f"DB: {db[0]}, {db[1]}, Symbol: {db[2]}")

    return final_list


def read_result(file, gate):
    #print("file: " + file)

    tree = ET.parse(file)
    root = tree.getroot()
    indexes = []

    i = 0
    for dbdot in root.findall(".//dbdot"):
        x = float(dbdot.get("x"))
        y = float(dbdot.get("y"))
        
        #print(f"dbdot: {x}, {y}")
    
        if x == gate.output_dot.physloc['x'] and y == gate.output_dot.physloc['y']:
            #print("Found output dot")
            #print(f"dbdot: {x}, {y} == output dot: {gate.output_dot.physloc['x']}, {gate.output_dot.physloc['y']}")
            #print(gate.db_dots[i])
            #print(i)
            indexes.append(i)
        
        i = i + 1

    biggest = []
    lowest_energy = math.inf

    for dist in root.findall(".//dist"):
        energy = float(dist.get("energy"))
        count = int(dist.get("count"))
        physically_valid = int(dist.get("physically_valid")) == 1
        state_count = int(dist.get("state_count"))
        symbol = dist.text
        if not physically_valid:
            continue

        if energy < lowest_energy:
            biggest = [energy, count, physically_valid, state_count, symbol]
            lowest_energy = energy
    
    symbol = biggest[4]
    symbol_list = []

    for index in indexes:
        symbol_list.append(symbol[index])
    #print("Symbol list: " + str(symbol_list))

    for symbol in symbol_list:
        if symbol == "-":
            symbol_list[symbol_list.index(symbol)] = "1"

    return symbol_list, energy
    
