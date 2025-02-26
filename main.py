import xml.etree.ElementTree as ET
from sqd_manipulator import DBDot, Gate, main_operator
import file_manager

def main():
    
    file_manager.make_dir("sqd")
    files = file_manager.get_files("sqd")
    print("Files:")
    for file in files:
        gate = main_operator(file)
        gate.print_gate()
        print("\n")
    
        
if __name__ == "__main__":
    main()
        