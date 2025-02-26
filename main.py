import xml.etree.ElementTree as ET
from sqd_manipulator import DBDot, Gate, parse_sqd_file, set_dots_to_minimum, get_input_perturbers

def main():
    sqd_file_path = "sqd/OR0.28.sqd"
    dots = parse_sqd_file(sqd_file_path)
    for dot in dots:
        print(dot)
        
    dots, pivot_dot = set_dots_to_minimum(dots)
    perturbers = get_input_perturbers(dots)
    
    gate = Gate(dots, pivot_dot, perturbers)
    
    print(gate)
    
        
if __name__ == "__main__":
    main()
        