# Stringer How-To guide

## This file outlines how to use the stringer class of the graph ops pipeline

### 1. Background

We generate designs according to a BNF string grammar which encodes component types, relative locations, and connection patterns (a design string currently does not things encode things like connection angles or component instances). Generated design strings are written to a text file one per line. 

### 2. Working with GraphOps

The `StringerBuilder` class in GraphOps is intended to interpret a design string, identify the substructures that satisfy the string (e.g. 2 forks, and a crossbar) which means there are enough terminal locations to hold the number of propellers specified
in the design string. The default will be to use the set of structures that minimizes the total number of connectors used.

After the set of substructures is obtained from the design string, the construction of the vehicle proceeds using the `Cursor` object which is a singleton member of a `StringerBuilder` instance. At any point in time during the construction of a design, the cursor has a current instance and current connection that it is associated with. By updating the location of the `Cursor` during construction, it is possible to attach pre-defined substructures at specific orientations on the vehicle. Currently there are 'fork' and 'tbar' substructures for the UAM corpus. Note that for the UAV corpus, there are hubs predefined for tubing which make things easier.

A design construction can be specified by an ordered sequence of step where each step includes a call to the `Cursor`'s `update_location()` function as well as a structure to attach starting at the `Cursor` object's updated location. 