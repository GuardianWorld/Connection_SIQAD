import xml.etree.ElementTree as ET
import os
from classes import DBDot, Gate
import sqd_manipulator
import gate_connector
import file_manager

def main():
    
    file_manager.make_dir("sqd")
    files = file_manager.get_files("sqd")
    gates = []
    
    while(True):
        print("Gate Connector\n")
        print("1. Connect 2 gates")
        print("2. Connect 3 gates")
        print("0. Exit")
        
        choice = input("Choice: ")
        
        if(choice == "0"):
            break
        
        if(choice == "1" or choice == "2"):
            print("Avaliable files: ")
            for i in range(len(files)):
                print(str(i) + ". " + files[i])
                
        if(choice == "1"):
            print("Choose 2 files to connect")
            file1 = files[int(input("File 1: "))]
            file2 = files[int(input("File 2: "))]
            
            gate1 = sqd_manipulator.main_operator(file1)
            gate2 = sqd_manipulator.main_operator(file2)
            
            circuit = gate_connector.connect_2_gates(gate1, gate2, wires=0)
            circuit.print_circuit()
            
            file_name, template = file_manager.sqd_template_create(sqd_manipulator.circuit_to_gate(circuit))
            print(file_name)
            if(os.name == 'posix'):
                file_manager.make_file("results/" + file_name, template)
            else:
                file_manager.make_file("results\\" + file_name, template)
            
        if(choice == "2"):
            print("Choose 3 files to connect")
            file1 = files[int(input("File 1: "))]
            file2 = files[int(input("File 2: "))]
            file3 = files[int(input("File 3: "))]
            
            gate1 = sqd_manipulator.main_operator(file1)
            gate2 = sqd_manipulator.main_operator(file2)
            gate3 = sqd_manipulator.main_operator(file3)
            
            circuit = gate_connector.connect_3_gates(gate1, gate2, gate3, wires=0)
            circuit.print_circuit()
            
            file_name, template = file_manager.sqd_template_create(sqd_manipulator.circuit_to_gate(circuit))
            file_manager.make_file("results\\" + file_name, template)    
        
if __name__ == "__main__":
    main()
        