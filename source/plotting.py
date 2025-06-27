import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


def plot_NML(gate, size):
    fig = go.Figure()

    half = size // 2
    if size % 2 == 0:
        size += 1  # Ensure size is odd for symmetry

    dot_size = 4
    x_coords = []
    y_coords = []
    hover_texts = []

    # Track invisible empty-row points
    ghost_x = []
    ghost_y = []

    for m in range(-half, half + 1):  # M axis (rows)
        for n in range(-half * 2, 2 * half +1):  # N axis (columns)

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
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='markers',
        marker=dict(size=dot_size, color='gray', symbol='circle'),
        text=hover_texts,
        opacity = 0.6,
        hoverinfo='text',
        showlegend=False
    ))

    # Add invisible markers on "empty" rows to force spacing
    fig.add_trace(go.Scatter(
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
            range=[min(x_coords) - 0.5, max(x_coords) + 0.5],
        ),
        yaxis=dict(
            visible=False,
            range=[min(y_coords) - 0.5, max(y_coords) + 0.5],
        ),
        font=dict(color='white'),
        height=650,
        margin=dict(l=10, r=10, t=10, b=10),
    )

    # Add gate DBs.

    if gate:
        print("Plotting gate:", gate.name)
        print("Gate dots:", gate.db_dots)

    return fig

