import os
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re


#Gets all .SQD files in the directory and its subdirectories

def clear_folders():
    if(os.name == 'posix'):
        clear_folder("./data/results")
        clear_folder("./data/combinations")
        clear_folder("./data/simulation")
        clear_folder("./data/temp")
        clear_folder("./data/xml")
    else:
        clear_folder("data\\results")
        clear_folder("data\\combinations")
        clear_folder("data\\simulation")
        clear_folder("data\\temp")
        clear_folder("data\\xml")

def make_file(file, content):
    with open(file, "w") as f:
        f.write(content)

def clear_folder(folder):
    #just delete the whole folder and have it remade
    if os.path.exists(folder):
        for root, dirs, files in os.walk(folder):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        make_dir(folder)
    else:
        make_dir(folder)

def make_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_files(directory, ending=".sqd"):
    files = []
    for root, dirs, file in os.walk(directory):
        for f in file:
            if f.endswith(ending):
                files.append(os.path.join(root, f))
    return files



def sqd_template_create(gate, prefix="", mode="save", parameters=None, sim_params_template=None):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if(sim_params_template is None and mode=="simulate"):
        print("No sim params template provided, please provide them on the folder [See Simanneal as an example]")
        return "Error", ""
    if(parameters is None or len(parameters) == 0) and mode=="simulate":
        print("No parameters provided, using default values")
    
    #Edit template with the parameters like XML
    #<anneal_cycles> something </anneal_cycles>



    sim_params = sim_params_template

    #substitute the params with the provided ones
    if parameters is not None and len(parameters) > 0:
        for key, value in parameters.items():
            #use regex to replace the value between the tags <key>value</key>
            pattern = f"(<{key}>)(.*?)(</{key}>)"
            if re.search(pattern, sim_params):
                sim_params = re.sub(pattern, lambda m: f"{m.group(1)}{value}{m.group(3)}", sim_params, flags=re.DOTALL)
            else:
                print(f"Parameter {key} not found in the template.")

    if(mode == "save"):
        header = f"""<?xml version="1.0" encoding="UTF-8"?>
    <siqad>
        <!--Program Flags-->
        <program>
            <file_purpose>save</file_purpose>
            <version>0.3.3</version>
            <date>{date}</date>
        </program>
        <!--GUI Flags-->
        <gui>
            <zoom>0.0396305</zoom>
            <displayed_region x1="-237.191" y1="-87.5589" x2="27.7564" y2="24.9808"/>
            <scroll x="-338" y="-931"/>
    </gui>"""
    else:
        header = f"""<?xml version="1.0" encoding="UTF-8"?>
    <siqad>
        <!--Program Flags-->
        <program>
        <file_purpose>simulation</file_purpose>
        <version>0.3.3</version>
        <date>{date}</date>
        </program>
        {sim_params}
        <gui>
            <zoom>0.0247393</zoom>
            <displayed_region x1="-163.707" y1="-62.6532" x2="260.718" y2="117.626"/>
            <scroll x="-146" y="-396"/>
        </gui>"""
    
    pre_middle = """<layers>
        <layer_prop>
            <name>Lattice</name>
            <type>Lattice</type>
            <role>Design</role>
            <zoffset>0</zoffset>
            <zheight>0</zheight>
            <visible>1</visible>
            <active>0</active>
            <lat_vec>
                <a1 x="3.84" y="0"/>
                <a2 x="0" y="7.68"/>
                <N>2</N>
                <b1 x="0" y="0"/>
                <b2 x="0" y="2.25"/>
            </lat_vec>
        </layer_prop>
        <layer_prop>
            <name>Screenshot Overlay</name>
            <type>Misc</type>
            <role>Overlay</role>
            <zoffset>0</zoffset>
            <zheight>0</zheight>
            <visible>1</visible>
            <active>0</active>
        </layer_prop>
        <layer_prop>
            <name>Surface</name>
            <type>DB</type>
            <role>Design</role>
            <zoffset>0</zoffset>
            <zheight>0</zheight>
            <visible>1</visible>
            <active>0</active>
        </layer_prop>
        <layer_prop>
            <name>Metal</name>
            <type>Electrode</type>
            <role>Design</role>
            <zoffset>1000</zoffset>
            <zheight>100</zheight>
            <visible>1</visible>
            <active>0</active>
        </layer_prop>
    </layers>
    <design>
        <!--Lattice-->
        <layer type="Lattice"/>
        <!--Screenshot Overlay-->
        <layer type="Misc"/>
        <!--Surface-->
        <layer type="DB">
"""

    bottom = """</layer>
    <!--Metal-->
    <layer type="Electrode"/>
    </design>
</siqad>
"""

    middle = ""
    for dot in gate.db_dots:
        middle += f"""
        <dbdot>
            <layer_id>2</layer_id>
            <latcoord n="{dot.latcoord['n']}" m="{dot.latcoord['m']}" l="{dot.latcoord['l']}"/>
            <physloc x="{dot.physloc['x']}" y="{dot.physloc['y']}"/>
            <color>{dot.color}</color>
        </dbdot>"""
    middle = middle[1:]
    if(mode == "save"):
        name = prefix + gate.name + ".sqd"
    else:
        name = prefix + gate.name + ".xml"
    
    return name , header + pre_middle + middle + bottom
    
def get_simulators():
    directory = Path("data") / "simulators"
    ending = ".physeng"

    simulators = [str(p) for p in directory.rglob(f"*{ending}") if p.is_file()]
    return simulators


def gen_simulator_sim_template(simulator_path=None):
    if(simulator_path is None):
        directory = Path("data") / "simulators" / "simanneal"
    else:
        directory = Path(simulator_path).parent
    physeng_file = None
    for file in directory.iterdir():
        if file.suffix == ".physeng":
            physeng_file = file
            break
    if physeng_file is None:
        print("No .physeng file found in the simulator directory.")
        return None

    #Open Physeng with Elemental Trees and generate a template file.
    tree = ET.parse(physeng_file)
    root = tree.getroot()
    sim_params = root.find('sim_params')
    if sim_params is None:
        print("No <sim_params> found in the .physeng file.")
        return None
    
    simplified_params = ET.Element('sim_params')
    for param in sim_params:
        param_name = param.tag
        val_elem = param.find('val')
        val_text = val_elem.text if val_elem is not None else ''

        new_elem = ET.SubElement(simplified_params, param_name)
        new_elem.text = val_text    
    
    def pretty_xml(element):
        rough_string = ET.tostring(element, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        xml_str = reparsed.toprettyxml(indent="    ")
        lines = xml_str.splitlines()
        return "\n".join(line for line in lines if line.strip() and not line.startswith("<?xml"))

    simplified_params = pretty_xml(simplified_params)
    #print(simplified_params)
    return simplified_params
    


def get_simulator_sim_template(simulator_path=None):
    #print(simulator_path)
    if simulator_path is None:
        directory = Path("data") / "simulators" / "simanneal"
    else:
        directory = Path(simulator_path).parent

    #print(directory)
    file_name = "template.txt"
    sim_template_path = Path(directory) / file_name
    #print(sim_template_path)
    if sim_template_path.is_file():
        #open file and return contents
        with open(sim_template_path, "r") as f:
            return f.read()
    else:
        print("No template.txt file found in the simulator directory.")
        return None

def parse_physeng(file_path):
    if not os.path.isfile(file_path):
        print(f"File {file_path} does not exist.")
        return None

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        params = {}

        for p in root.find('sim_params'):
            param_id = p.tag
            param_type = p.find('T').text
            param_val = p.find('val').text
            label = p.find('label').text if p.find('label') is not None else param_id
            tip = p.find('tip').text if p.find('tip') is not None else ''
            dp = p.find('dp').text if p.find('dp') is not None else 1
            params[param_id] = {
                'type': param_type,
                'val': param_val,
                'label': label,
                'tip': tip,
                'dp': dp
            }
            #print(param_id, param_val)
        
        return params

    except ET.ParseError as e:
        print(f"Error parsing XML file {file_path}: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None