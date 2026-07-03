# Automatic SiDB Interconnection Toolkit

Automated generation, validation and analysis of Silicon Dangling Bond (SiDB) circuits.

---

# Overview
The Automatic SiDB Interconnection Toolkit is a research platform developed during my Master's degree for automating the design, validation and analysis of Silicon Dangling Bond (SiDB) circuits.

Instead of manually constructing and validating layouts inside SiQAD, the framework automates the complete workflow:

```
Circuit generation
        │
        ▼
Automatic interconnection
        │
        ▼
Simulation
        │
        ▼
Truth-table validation
        │
        ▼
Automatic correction
        │
        ▼
Result archival
```

The toolkit was designed to reduce the amount of repetitive manual work required when exploring large numbers of SiDB layouts while preserving both successful and failed simulations for later analysis.

---

# Features

- Automated SiDB layout generation
- Automatic gate interconnection
- Truth-table verification
- Batch execution
- Multiple simulation engine support
- Dash web interface
- Automatic report generation
- PNG export
- Truth table export
- Simulation archive
- Preservation of successful and failed layouts
- Modular architecture for new interconnection algorithms

---

# Motivation
Designing SiDB circuits manually is an iterative process involving repeated simulation, debugging and layout adjustments.

Most existing workflows focus on finding successful layouts as quickly as possible.

This project instead emphasizes exploration, preserving unsuccessful configurations alongside functional ones in order to better understand failure modes and develop improved interconnection strategies.

---

# Main Components
- Interactive Dash interface
- Simulation manager
- Interconnection engine
- Layout correction algorithms
- Batch execution system
- Result archival system
- Simulation engine abstraction layer

---

# Engineering Highlights
- Modular Python architecture
- Plugin-style simulation engine integration
- Automated file generation
- Large-scale batch processing
- Data visualization
- Research-oriented workflow automation

---

# Technologies
- Python
- Dash
- Plotly
- Flask
- Pandas
- NumPy
- SiQAD
- Scientific computing workflows

---

# Research
Developed as part of my Master's dissertation on automated Silicon Dangling Bond circuit generation and interconnection.

The framework focuses on large-scale exploration of circuit layouts while minimizing manual interaction and preserving simulation data for future analysis.

---

Paper: {To Be Published}

Thesis: {To Be Published}
