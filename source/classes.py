
from sympy.logic.boolalg import Or, And, Not, Xor, Implies, Equivalent
from sympy import Symbol, srepr, symbols, sympify

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

    def to_dict(self):
        return {
            'layer_id': self.layer_id,
            'latcoord': self.latcoord,
            'physloc': self.physloc,
            'color': self.color,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            layer_id=data['layer_id'],
            latcoord=data['latcoord'],
            physloc=data['physloc'],
            color=data['color']
        )
        
class Gate:
    def __init__(self, db_dots, pivot_dot, input_perturbers, output_dot, name=None, expression=None, symbols=None):
        self.db_dots = db_dots
        self.pivot_dot = pivot_dot
        self.input_perturbers = input_perturbers
        self.name = name
        self.output_dot = output_dot
        self.input_symbols = symbols
        self.expression = expression  # Store the logical expression

    def __repr__(self):
        return (f"Gate(db_dots={self.db_dots}, pivot_dot={self.pivot_dot}, "
                f"input_perturbers={self.input_perturbers})")
    
    def print_gate(self):
        print("Name: ", self.name)
        print("Pivot Dot: ", self.pivot_dot)
        for perturber in self.input_perturbers:
            print("Perturber: ", perturber)
        print("DB Dots: ")
        for dot in self.db_dots:
            print(dot)
            
    def remove_dot(self, dot):
        self.db_dots.remove(dot)
    
    def find_dot(self, n, m, l):
        for dot in self.db_dots:
            if dot.latcoord['n'] == n and dot.latcoord['m'] == m and dot.latcoord['l'] == l:
                return dot
        return None
    
    def find_input_dot(self, n, m, l):
        for dot in self.input_perturbers:
            if dot.latcoord['n'] == n and dot.latcoord['m'] == m and dot.latcoord['l'] == l:
                return dot
        return None
    
    def remove_input(self, dot):
        dot_n = dot.latcoord['n']
        dot_m = dot.latcoord['m']
        dot_l = dot.latcoord['l']
        dot = self.find_dot(dot_n, dot_m, dot_l)
        input_dot = self.find_input_dot(dot_n, dot_m, dot_l)
        self.db_dots.remove(dot)
        self.input_perturbers.remove(input_dot)
    
    def color_inputs_orange(self):
        for dot in self.input_perturbers:
            dot.color = "orange"

    def to_dict(self):
        return {
            'db_dots': [dot.to_dict() for dot in self.db_dots],
            'pivot_dot': self.pivot_dot.to_dict(),
            'input_perturbers': [pert.to_dict() for pert in self.input_perturbers],
            'output_dot': self.output_dot.to_dict(),
            'input_symbols': [s.name for s in self.input_symbols] if self.input_symbols else None,
            'expression': srepr(self.expression) if self.expression else None,
            'name': self.name,
        }
    
    @classmethod
    def from_dict(cls, data):
        db_dots = [DBDot.from_dict(d) for d in data['db_dots']]
        pivot_dot = DBDot.from_dict(data['pivot_dot'])
        input_perturbers = [DBDot.from_dict(d) for d in data['input_perturbers']]
        output_dot = DBDot.from_dict(data['output_dot'])
        symbols_list = [Symbol(name) for name in data['input_symbols']] if data.get('input_symbols') else None
        gate = cls(db_dots, pivot_dot, input_perturbers, output_dot, data.get('name'), symbols=symbols_list)
        if data.get('expression'):
            gate.expression = sympify(data['expression'])
        else:
            gate.expression = None

        return gate
        
      
class Circuit:
    def __init__(self, gates, input_perturbers, pivot_dot, expression=None, symbols=None):
        self.gates = gates
        self.input_perturbers = input_perturbers
        self.pivot_dot = pivot_dot
        self.expression = expression  # Optional expression attribute
        self.input_symbols = symbols
        
    def print_circuit(self):
        #Prints the circuit
        print("\nCircuit: ")
        print("Pivot Dot: ", self.pivot_dot)
        print("Input Perturbers: ")
        for perturber in self.input_perturbers:
            print(perturber)
        print("Gates: ")
        for gate in self.gates:
            print(gate.name)
            
    def set_input_perturbers(self, input_perturbers):
        self.input_perturbers = input_perturbers
        
    
    
def extract_gates_from_name(name):
    parts = name.split('_')
    gates = []
    for part in parts:
        #Remove the Circuit part
        if part == "Circuit":
            continue
        #Remove any numbers at the end of a part
        gate = ''.join(filter(str.isalpha, part))
        if gate:  # Ensure it's not empty
            gates.append(gate)
    return gates

GATE_EXPRESSIONS = {
    "AND": lambda inputs: And(*inputs),            # inputs: list of sympy symbols
    "OR": lambda inputs: Or(*inputs),
    "NAND": lambda inputs: Not(And(*inputs)),
    "NOR": lambda inputs: Not(Or(*inputs)),
    "NOT": lambda inputs: Not(inputs[0]),          # single input
    "XOR": lambda inputs: Xor(*inputs),
    "XNOR": lambda inputs: Not(Xor(*inputs)),
    "MAJ": lambda inputs: (inputs[0] & inputs[1]) | (inputs[0] & inputs[2]) | (inputs[1] & inputs[2]),  # 3-input majority
}