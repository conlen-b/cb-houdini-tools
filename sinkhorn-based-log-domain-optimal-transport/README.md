# **[sinkhorn-based-log-domain-optimal-transport](./SinkhornBasedLogDomainOptimalTransportHoudini.py)**
An implementation of Optimal Transport that is sinkhorn based and performed in the log domain.
Based off of the algorithm outlined in Remark 4.22 "Computational Optimal Transport" (2019) by Gabriel Peyré
& Marco Cuturi https://arxiv.org/abs/1803.00567

Heavily commented in the form of notes/documentation for myself as I was learning this.

## How To Use:
Place in a python SOP, and create the required parameters on the SOP:
"epsilon" : float (Hard min: 1e-10; Soft Max: 0.2; Default: 0.03)
"min_iterations" : int (Hard min: 0; Soft Max: 30; Default: 3)
"max_iterations" : int (Hard min: 1; Soft Max: 500; Default: 200)
"tolerance" : float (Hard min: 1e-12; Soft Max: 0.1; Default: 1e-8)

Note: The main code block below all definitions requires `__name__` == "builtins", which is `__name__` for the Python
SOP in Houdini 20.5.

Plug in the source point cloud in the Python SOP's first input, and the target point cloud in the Python SOP's second
input.

Outputs the attribute ot_pos on the source points, which is the position of each point after optimal transport.

This gets quite slow, try to limit yourself to a few thousand points if computed each step in a solver, and less than a
hundred thousand if computed once, otherwise it gets quite slow.
You could potentially interpolate the output ot_pos from a sparser point cloud to a denser point cloud