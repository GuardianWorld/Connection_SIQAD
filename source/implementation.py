import subprocess
import sys
import os
from tabulate import tabulate

##Do all the things you need over here for gate permutation
##Make SQD file, txt with the coordinates you want to permutate and outputs and the file with truth table;

##Make function that calls a pipe witch simply calls the main.py with the right arguments

def call_analysis():
    sqd_file = "AND-AND.sqd"
    coordinates_file = "AND-AND.txt"
    truth_table_file = "AND-AND_table.txt"
    #command = ["python3", "main.py", sqd_file, coordinates_file, truth_table_file] Will use -1 as the default value for num_instances
    command = ["python3", "main.py", sqd_file, coordinates_file, truth_table_file, "100"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        if(stdout[0] == "1"):
            print("Success, table matches, gate works")
        elif(stdout[0] == "0"):
            print("Table does not match, gate does not work")
            print(stdout[1:])
        else:
            print("Something went wrong")
    else:
        print("ERROR!")
        print(stderr)
    
    command = ["python3", "main.py", "-clean"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
## After this, it could be possible to grab the analysis and check what is going on with the outputs, example:
## - If in ONE case of the inputs, the output of the FIRST gate is 0 when it should be 1, you could try to: 
## -> Move it closer to the booster
## -> Add a DB to the output of the gate (8-10 distance)
## -> If the first DB after the booster (Lets call it Output-MID) is being checked and it also gives a wrong result
## -> Move the gate closer to the booster, or further away from the booster, etc.

def make_table(headers, rows):
    cleaned_data = [[cell[0] if isinstance(cell, list) else cell for cell in row] for row in rows]
    return tabulate(cleaned_data, headers=headers, tablefmt="grid")
    

def call_simmaneal(file, result_name):    
    if(os.name == 'posix'):
        sim = "./data/simulators/simanneal/simanneal"
        result_path = "./data/xml/" + result_name
    else:
        sim = "data\\simulators\\simanneal\\simanneal.exe"
        result_path = "data\\xml\\" + result_name
        
    command = sim + " " + file + " " + result_path
    print("Calling Simanneal for file: " + file + " please wait!", end='\r')
    print(command)
    sys.stdout.flush()
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result_path

