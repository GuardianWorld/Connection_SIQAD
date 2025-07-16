import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io
import base64


def plot_NML(gate, viewport=None):
    fig = go.Figure()

    dot_size = 4
    x_coords = []
    y_coords = []
    hover_texts = []

    # Track invisible empty-row points
    ghost_x = []
    ghost_y = []

    if viewport is None:
        viewport = {
            "top": 10,
            "bottom": -10,
            "left": -10,
            "right": 10
        }

    left = viewport.get("left", -10)
    right = viewport.get("right", 10)
    top = viewport.get("top", 10)
    bottom = viewport.get("bottom", -10)

    

    for m in range(bottom, top + 1):  # M axis (rows)
        for n in range( left, right + 1):  # N axis (columns)

            for l in range(3):  # L = 0, 1, 2 (2 = visual gap)

                y_pos = m * 3 + l  # creates spacing between M rows

                if l == 2:
                    # Create ghost points (for visual spacing)
                    ghost_x.append(n)
                    ghost_y.append(-y_pos)
                    continue

                x_coords.append(n * 0.6)
                y_coords.append(-y_pos)
                hover_texts.append(f"N={n}, M={m}, L={l}")

    # Add actual visible lattice points
    fig.add_trace(go.Scattergl(
        x=x_coords,
        y=y_coords,
        mode='markers',
        marker=dict(size=dot_size, color='gray', symbol='circle'),
        text=hover_texts,
        opacity = 0.6,
        hoverinfo='skip',
        showlegend=False
    ))

    # Add invisible markers on "empty" rows to force spacing
    fig.add_trace(go.Scattergl(
        x=ghost_x,
        y=ghost_y,
        mode='markers',
        marker=dict(size=dot_size, color='rgba(0,0,0,0)'),  # fully transparent
        hoverinfo='skip',
        showlegend=False
    ))

    # Layout styling
    fig.update_layout(
        autosize=False,
        xaxis=dict(
            visible=False,
            range=[min(x_coords) - 1, max(x_coords) + 1],
        ),
        yaxis=dict(
            visible=False,
            range=[min(y_coords) - 1, max(y_coords) + 1],
        ),
        font=dict(color='white'),
        height=700,
        margin=dict(l=10, r=10, t=10, b=10),
    )

    # Add gate DBs.
    if not gate:
        return fig

    #print("Plotting gate:", gate.name)
    #print("Gate dots:", gate.db_dots)

    gate_x = []
    gate_y = []
    gate_texts = []


    for dot in gate.db_dots:
        n = dot.latcoord['n']
        m = dot.latcoord['m']
        l = dot.latcoord['l']

        x = n * 0.6
        y = m * 3 + l
        gate_x.append(x)
        gate_y.append(-y)
        gate_texts.append(f"N={n}, M={m}, L={l}")

    fig.add_trace(go.Scatter(
        x=gate_x,
        y=gate_y,
        mode='markers',
        marker=dict(size=10, color='black', symbol='circle-open', line=dict(width=2)),
        text=gate_texts,
        hoverinfo='text',
        name='Gate DBs',
        showlegend=False
    ))

    return fig

def get_viewport(gate):
    """
    Get the viewport for the gate based on its dots.
    """
    if not gate or not gate.db_dots:
        return None
    
    top_size = get_top_size(gate)
    bottom_size = get_bottom_size(gate)
    left_size = get_left_size(gate)
    right_size = get_right_size(gate)

    return {
        'top': top_size,
        'bottom': bottom_size,
        'left': left_size,
        'right': right_size
    }

def get_top_size(gate):
    """
    Get the top size of the gate based on its dots.
    """
    if not gate or not gate.db_dots:
        return 0
    
    top_size = 0
    for dot in gate.db_dots:
        if dot.latcoord['m'] > top_size:
            top_size = dot.latcoord['m']
    #print("Top size:", top_size)
    return top_size # 3 units per M, plus 2 for the L=2 gap

def get_bottom_size(gate):
    """
    Get the bottom size of the gate based on its dots.
    """
    if not gate or not gate.db_dots:
        return 0
    
    bottom_size = 0
    for dot in gate.db_dots:
        if dot.latcoord['m'] < bottom_size:
            bottom_size = dot.latcoord['m']
    #print("Bottom size:", bottom_size)
    return bottom_size # 3 units per M, plus 2 for the L=2 gap

def get_left_size(gate):
    """
    Get the left size of the gate based on its dots.
    """
    if not gate or not gate.db_dots:
        return 0
    
    left_size = 0
    for dot in gate.db_dots:
        if dot.latcoord['n'] < left_size:
            left_size = dot.latcoord['n']
    #print("Left size:", left_size)
    return left_size  # 0.6 units per N, plus 0.3 for the gap

def get_right_size(gate):
    """
    Get the right size of the gate based on its dots.
    """
    if not gate or not gate.db_dots:
        return 0
    
    right_size = 0
    for dot in gate.db_dots:
        if dot.latcoord['n'] > right_size:
            right_size = dot.latcoord['n']
    #print("Right size:", right_size)
    return right_size # 0.6 units per N, plus 0.3 for the gap

def viewport_size(viewport, l=False):
    """
    Calculate the size of the gate based on the viewport.
    """
    
    horizontal_size = (abs(viewport['left']) + abs(viewport['right']))
    vertical_size = (abs(viewport['top']) + abs(viewport['bottom']))
    
    #print("Gate Size:", horizontal_size, vertical_size)
    return "N x M : {} x {}".format(horizontal_size, vertical_size)