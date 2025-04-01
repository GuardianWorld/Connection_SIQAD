import xml.etree.ElementTree as ET
import os
from classes import DBDot, Gate
import sqd_manipulator
import gate_connector
import file_manager
import implementation

#defines
if(os.name == 'posix'):
    simanneal = "simulators/simanneal"
    complete = "simulators/complete"
else:
    simanneal = "simulators\\simanneal"
    complete = "simulators\\complete"

def batch_menu():
    global wire_lenght
    simulator_used = simanneal
    while(True):
        files = file_manager.get_files("sqd")
        gates = []
        gate = None
        
        print("Gate Connector - Batch Menu\n")
        print(f"Simulator: {simulator_used}")
        print("1. Connect 2 gates + operations")
        print("2. Connect 3 gates + operations")
        print("3. Do Operations on Any files.")
        print("8. Change simulator (Simanneal/Complete)")
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
            gate = sqd_manipulator.circuit_to_gate(circuit)
        if(choice == "2"):
            print("Choose 3 files to connect")
            file1 = files[int(input("File 1: "))]
            file2 = files[int(input("File 2: "))]
            file3 = files[int(input("File 3: "))]
            
            gate1 = sqd_manipulator.main_operator(file1)
            gate2 = sqd_manipulator.main_operator(file2)
            gate3 = sqd_manipulator.main_operator(file3)
            
            circuit = gate_connector.connect_3_gates(gate1, gate2, gate3, wires=wire_lenght)            
            gate = sqd_manipulator.circuit_to_gate(circuit)
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
            except:
                print("Invalid input")
                pass
        elif(choice == "8"):
            if(simulator_used == simanneal):
                simulator_used = complete
            else:
                simulator_used = simanneal
        elif(choice == "9"):
            try:
                wire_lenght = int(input("New wire lenght: "))
            except:
                print("Invalid input")
                
        #continue operations that are common to many choices
        if(choice == "1" or choice == "2" or choice == "3"):
            #Clean the TEMP folder
            file_manager.clear_folder("temp")
            gate.print_gate()
            
            #Make all combinations
            gates = sqd_manipulator.combinators(gate)
            for i in range(len(gates)):
                file_name, template = file_manager.sqd_template_create(gates[i], prefix=f"combination_{i}_", mode="simulation")
                file_path = None
                if(os.name == 'posix'):
                    file_path = "temp/" + file_name
                    file_manager.make_file(file_path, template)
                else:
                    file_path = "temp\\" + file_name
                    file_manager.make_file(file_path, template)
                
                result_name = "result_" + file_name
                implementation.call_simmaneal(file_path, result_name)
                    
            #Run the simulator
            
            
                    
        
def main():
    global wire_lenght
    wire_lenght = 1
    file_manager.make_dir("sqd")
    file_manager.make_dir("results")
    file_manager.make_dir("combinations")
    file_manager.make_dir("simulation")
    file_manager.make_dir("temp")
    file_manager.make_dir("xml")
    
    #batch_menu()
    
    while(True):
        files = file_manager.get_files("sqd")
        gates = []
        
        print("Gate Connector - Single Operation Menu\n")
        print("1. Connect 2 gates")
        print("2. Connect 3 gates")
        print("3. Test a gate or circuit file")
        print("4. Make all input combinations of a gate")
        print("5. Make simulation file for a circuit")
        print("6. Load a gate and find the output perturber")
        print("8. Batch Menu")
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
            if(os.name == 'posix'):
                file_manager.make_file("results/" + file_name, template)
            else:
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
                    if(os.name == 'posix'):
                        file_manager.make_file("combinations/" + file_name, template)
                    else:
                        file_manager.make_file("combinations\\" + file_name, template)
            except:
                print("Invalid input")
        elif(choice == "5"):
            all_files = files.copy()
            results_files = file_manager.get_files("results")
            all_files.extend(results_files)
            
            print("Choose a file")
            for i in range(len(all_files)):
                print(str(i) + ". " + all_files[i])
                
            try:
                file = all_files[int(input("File: "))]
                gate = sqd_manipulator.main_operator(file)
                file_name, template = file_manager.sqd_template_create(gate, mode="simulation")
                if(os.name == 'posix'):
                    file_manager.make_file("simulation/" + file_name, template)
                else:
                    file_manager.make_file("simulation\\" + file_name, template)
            except:
                print("Invalid input")
        elif(choice == "6"):
            all_files = files.copy()
            results_files = file_manager.get_files("results")
            all_files.extend(results_files)
            
            print("Choose a file")
            for i in range(len(all_files)):
                print(str(i) + ". " + all_files[i])
                
            try:
                file = all_files[int(input("File: "))]
                gate = sqd_manipulator.main_operator(file)
                print(gate.output_dot)
            except:
                print("Invalid input")
        elif(choice == "8"):
            batch_menu()
        elif(choice == "9"):
            try:
                wire_lenght = int(input("New wire lenght: "))
            except:
                print("Invalid input")
        
        
if __name__ == "__main__":
    main()
        