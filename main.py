import xml.etree.ElementTree as ET
import os
from classes import DBDot, Gate
import sqd_manipulator
import gate_connector
import file_manager

def main():
    
    file_manager.make_dir("sqd")
    file_manager.make_dir("results")
    file_manager.make_dir("combinations")
    files = file_manager.get_files("sqd")
    gates = []
    wire_lenght = 1
    
    while(True):
        print("Gate Connector - Single Operation Menu\n")
        print("1. Connect 2 gates")
        print("2. Connect 3 gates")
        print("3. Test a gate or circuit file")
        print("4. Make all input combinations of a gate")
        print("5. Make simulation file for a circuit")
        print("6. Batch Menu")
        print(f"9. Change wire lenght | current: {wire_lenght}")
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
            
            circuit = gate_connector.connect_2_gates(gate1, gate2, wires=wire_lenght)
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
            
            circuit = gate_connector.connect_3_gates(gate1, gate2, gate3, wires=wire_lenght)
            circuit.print_circuit()
            
            file_name, template = file_manager.sqd_template_create(sqd_manipulator.circuit_to_gate(circuit))
            file_manager.make_file("results\\" + file_name, template)    

        elif(choice == "3"):
            all_files = files.copy()
            results_files = file_manager.get_files("results")
            all_files.extend(results_files)
            
            print("Choose a file to test")
            for i in range(len(all_files)):
                print(str(i) + ". " + all_files[i])
            
            try:
                file = all_files[int(input("File: "))]
                gate = sqd_manipulator.main_operator(file)
                gate.print_gate()
            except:
                print("Invalid input")
        elif(choice == "4"):
            all_files = files.copy()
            results_files = file_manager.get_files("results")
            all_files.extend(results_files)
            
            print("Choose a file")
            for i in range(len(all_files)):
                print(str(i) + ". " + all_files[i])
                
            try:
                file = all_files[int(input("File: "))]
                gate = sqd_manipulator.main_operator(file)
                gates = sqd_manipulator.combinators(gate)                

                for i in range(len(gates)):
                    file_name, template = file_manager.sqd_template_create(gates[i], prefix=f"combination_{i}_")
                    file_manager.make_file("combinations\\" + file_name, template)
            except:
                print("Invalid input")
    
        elif(choice == "9"):
            try:
                wire_lenght = int(input("New wire lenght: "))
            except:
                print("Invalid input")
        
        
if __name__ == "__main__":
    main()
        