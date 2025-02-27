import xml.etree.ElementTree as ET
from classes import DBDot, Gate
import sqd_manipulator
import gate_connector
import file_manager

def main():
    
    file_manager.make_dir("sqd")
    files = file_manager.get_files("sqd")
    gates = []
    for file in files:
        gate = sqd_manipulator.main_operator(file)
        #gate.print_gate()
        #print("\n")
        gates.append(gate)

    print("Gates: ", len(gates))
    print("Avaliable: ")
    for gate in gates:
        print(gate.name)
        
    #Connect the gates
    
    circuit = gate_connector.connect_3_gates(gates[0], gates[1], gates[2], wires=2)
    circuit.print_circuit()
    
    file_name, template = file_manager.sqd_template_create(sqd_manipulator.circuit_to_gate(circuit))
    
    #print("Template:\n", template)
    
    #Write the template to a file
    file_manager.make_file("results\\" + file_name, template)
    
        
    

    
        
if __name__ == "__main__":
    main()
        