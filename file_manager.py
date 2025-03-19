import os
from datetime import datetime

#Gets all .SQD files in the directory and its subdirectories

def make_file(file, content):
    with open(file, "w") as f:
        f.write(content)


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

def sqd_template_create(gate, prefix=""):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    header = """<?xml version="1.0" encoding="UTF-8"?>
    <siqad>
        <!--Program Flags-->
        <program>
            <file_purpose>save</file_purpose>
            <version>0.3.3</version>
            <date>2025-02-26 21:36:59</date>
        </program>
        <!--GUI Flags-->
        <gui>
            <zoom>0.0396305</zoom>
            <displayed_region x1="-237.191" y1="-87.5589" x2="27.7564" y2="24.9808"/>
            <scroll x="-338" y="-931"/>
    </gui>
    <layers>
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
    name = prefix + gate.name + ".sqd"
    
    return name , header + middle + bottom
    
        
    