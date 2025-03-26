import os
from datetime import datetime

#Gets all .SQD files in the directory and its subdirectories

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

def get_files(directory):
    files = []
    for root, dirs, file in os.walk(directory):
        for f in file:
            if f.endswith(".sqd"):
                files.append(os.path.join(root, f))
    return files

def sqd_template_create(gate, prefix="", mode="save", mu=-0.28, eps_r=4.1, debye_length=1.8, anneal_cycles=10000):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        <sim_params>
            <T_e_inv_point>0.09995000064373016</T_e_inv_point>
            <T_init>500</T_init>
            <T_min>2</T_min>
            <T_schedule>exponential</T_schedule>
            <anneal_cycles>{anneal_cycles}</anneal_cycles>
            <debye_length>{debye_length}</debye_length>
            <eps_r>{eps_r}</eps_r>
            <hop_attempt_factor>5</hop_attempt_factor>
            <muzm>{mu}</muzm>
            <num_instances>-1</num_instances>
            <phys_validity_check_cycles>10</phys_validity_check_cycles>
            <reset_T_during_v_freeze_reset>false</reset_T_during_v_freeze_reset>
            <result_queue_size>0.10000000149011612</result_queue_size>
            <strategic_v_freeze_reset>false</strategic_v_freeze_reset>
            <v_freeze_end_point>0.4000000059604645</v_freeze_end_point>
            <v_freeze_init>-1</v_freeze_init>
            <v_freeze_reset>-1</v_freeze_reset>
            <v_freeze_threshold>4</v_freeze_threshold>
        </sim_params>
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
    

    