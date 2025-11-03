# **[Optimal Transport SOP HDA](./sop_cb_optimal_transport.1.0.hdanc)**
[`sop_cb_optimal_transport.1.0.hdanc`](./sop_cb_optimal_transport.1.0.hdanc)

A Houdini Digital Asset (HDA) for the SOP level that provides a convenient wrapper over my Optimal Transport Python scripts below.

## How To Use:
Import into Houdini with File > Import > Houdini Digital Asset.  
In a SOP context network, search for "Optimal Transport".  
Connect the source points to transport in the first input, and the target points to transport to in the second input.  

Select the compute type (GPU is only available if CuPy and NVIDIA CUDA Toolkit are installed; see the [GPU script description](#gpu-sinkhorn-based-log-domain-optimal-transport) for more info).

Tune parameters as needed:  
"Epsilon (smoothness)": Smoothness of the result, lower is more rigid, higher is more "blurred". Default 0.03.  
"Min Iterations": Minimum iterations for transport to converge. Default 3.  
"Max Iterations": Maximum iterations for transport to converge. Higher = more accurate, but slower to compute. Default 200.  
"Tolerance": A tolerance threshold for when the result is considered converged. The lower the value, the more accurate the result will be, but it will also have higher potential to reach max iterations. Default 1e-08.  
"Output Debug Attributes": Outputs the detail attributes `_ot_converge_type` and `_ot_iterations`. Iterations is the final number of iterations used. Converge type is the condition that was used to stop iterating (Error < Tolerance, Stagnation, or Max Iterations Reached). Default False.  

Outputs the attribute ot_pos on the source points, which is the position of each point after optimal transport.
<br><br><br>



# **[Sinkhorn-Based Log Domain Optimal Transport](./SinkhornBasedLogDomainOptimalTransportHoudini.py)**
[`SinkhornBasedLogDomainOptimalTransportHoudini.py`](./SinkhornBasedLogDomainOptimalTransportHoudini.py)

An implementation of Optimal Transport that is sinkhorn based and performed in the log domain.  
Based off of the algorithm outlined in Remark 4.23 "Computational Optimal Transport" (2019) by Gabriel Peyré & Marco Cuturi https://arxiv.org/abs/1803.00567

Heavily commented in the form of notes/documentation for myself as I was learning this.

## How To Use:
Place in a python SOP, and create the required parameters on the SOP:  
"epsilon" : float (Hard min: 1e-10; Soft Max: 0.2; Default: 0.03)  
"min_iterations" : int (Hard min: 0; Soft Max: 30; Default: 3)  
"max_iterations" : int (Hard min: 1; Soft Max: 500; Default: 200)  
"tolerance" : float (Hard min: 1e-12; Soft Max: 0.1; Default: 1e-8)  
"output_debug_attrs" : toggle (Default: False)

Note: The main code block below all definitions requires `__name__` == "builtins", which is `__name__` for the Python SOP in Houdini 20.5.

Plug in the source point cloud in the Python SOP's first input, and the target point cloud in the Python SOP's second input.

Outputs the attribute ot_flat_pos_array on the source points, which is a flattened list of the positions of each point after optimal transport.  
A point wrangle after the Python SOP can convert this to a per-point vector attribute with the following code:

    float ot_flat_pos_array[];
    ot_flat_pos_array = detail(0, "ot_flat_pos_array");

    vector ot_pos;

    int index = @ptnum * 3;

    ot_pos.x = ot_flat_pos_array[index];
    ot_pos.y = ot_flat_pos_array[index+1];
    ot_pos.z = ot_flat_pos_array[index+2];

    v@ot_pos = ot_pos;

This gets quite slow, try to limit yourself to a few thousand points if computed each step in a solver, and less than a hundred thousand if computed once, otherwise it gets quite slow.  
You could potentially interpolate the output ot_pos from a sparser point cloud to a denser point cloud.
<br><br><br>



# **[GPU Sinkhorn-Based Log Domain Optimal Transport](./GPUSinkhornBasedLogDomainOptimalTransportHoudini.py)**
[`GPUSinkhornBasedLogDomainOptimalTransportHoudini.py`](./GPUSinkhornBasedLogDomainOptimalTransportHoudini.py)

A GPU implementation of Optimal Transport using CuPy (GPU drop-in for Numpy) that is sinkhorn based and performed in the log domain.  
Based off of the algorithm outlined in Remark 4.23 "Computational Optimal Transport" (2019) by Gabriel Peyré & Marco Cuturi https://arxiv.org/abs/1803.00567

Assumes Cuda + CuPy version 13.x:  
Requires CuPy to be installed in the Houdini environment, can be done with this console command:  
"C:\Program Files\Side Effects Software\Houdini 20.5.684\bin\hython.exe" -m pip install cupy-cuda13x  
^Switch the Houdini version and cupy cuda version as needed

Requires the NVIDIA CUDA Toolkit matching your Cuda version eg. 13  
Houdini's path may need to append:  
PATH = "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.0/bin;&"  
CUDA_PATH = "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.0/bin;&"

Heavily commented in the form of notes/documentation for myself as I was learning this.

## How To Use:
Same as CPU implementation.