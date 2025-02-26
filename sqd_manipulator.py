import xml.etree.ElementTree as ET

class DBDot:
    def __init__(self, layer_id, latcoord, physloc, color):
        self.layer_id = layer_id
        self.latcoord = latcoord  # Dictionary with keys 'n', 'm', 'l'
        self.physloc = physloc    # Dictionary with keys 'x', 'y'
        self.color = color

    def __repr__(self):
        return (f"DBDot(layer_id={self.layer_id}, latcoord={self.latcoord}, "
                f"physloc={self.physloc}, color='{self.color}')")
    
    def recalculate_physloc(self):
        # Recalculate the physical location of the dot based on the latcoord
        x = self.latcoord['n'] * 3.84
        y = self.latcoord['m'] * 7.68 + self.latcoord['l'] * 2.25
        self.physloc = {'x': x, 'y': y}
        
class Gate:
    def __init__(self, db_dots, pivot_dot, input_perturbers):
        self.db_dots = db_dots
        self.pivot_dot = pivot_dot
        self.input_perturbers = input_perturbers
        self.gate_size = [0, 0]

    def __repr__(self):
        return (f"Gate(db_dots={self.db_dots}, pivot_dot={self.pivot_dot}, "
                f"input_perturbers={self.input_perturbers}, gate_size={self.gate_size})")
        
        
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

def set_dots_to_minimum(dots):
    # Get the perturber at the BOTTOM of the list (Lowest m)
    
    min_m = min(abs(dot.latcoord['m']) for dot in dots) #find the minimum value of m
    min_n = 0
    pivot_dot = None
    for dot in dots:
        if abs(dot.latcoord['m']) == min_m:
            print("Original Dot:", dot)
            min_n = dot.latcoord['n']
            min_m = dot.latcoord['m']
            pivot_dot = dot
    
    for dot in dots:
        dot.latcoord['m'] = dot.latcoord['m'] - min_m
        dot.latcoord['n'] = dot.latcoord['n'] - min_n
        dot.recalculate_physloc()
    
    return dots, pivot_dot
            
def get_input_perturbers(dots):
    perturbers = []
    max_m = max(abs(dot.latcoord['m']) for dot in dots)
    
    print("Max M:", max_m)
    for dot in dots:
        #Get the perturbers at the TOP of the list (Highest m) 
        #Since all are Y shaped, the perturber is on the TOP 99% of the time HOPEFULLY
        if abs(dot.latcoord['m']) == max_m:
            perturbers.append(dot)
        
    
    return perturbers   
    
        
