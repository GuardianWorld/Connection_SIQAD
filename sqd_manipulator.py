import xml.etree.ElementTree as ET
from classes import DBDot, Gate
import os

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
    if os.name == 'posix':
        name = file.split("/")[-1]
    else:
        name = file.split("\\")[-1]
    name = name.split(".")[0]
    gate = Gate(dots, pivot_dot, perturbers, name)
    return gate
    
def circuit_to_gate(circuit):
    db_dots = []
    for gate in circuit.gates:
        for dot in gate.db_dots:
            db_dots.append(dot)
    
    pivot_dot = circuit.pivot_dot
    input_perturbers = circuit.input_perterbers
    name = "Circuit"
    for gate in circuit.gates:
        name += f"_{gate.name}"
    gate = Gate(db_dots, pivot_dot, input_perturbers, name)
    return gate