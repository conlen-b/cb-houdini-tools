# -*- coding: utf-8 -*-

"""
GPUSinkhornBasedLogDomainOptimalTransportHoudini.py
A GPU implementation of Optimal Transport using CuPy (GPU drop-in for Numpy) that is sinkhorn based and performed in the log domain.
Based off of the algorithm outlined in Remark 4.22 "Computational Optimal Transport" (2019) by Gabriel Peyré
& Marco Cuturi https://arxiv.org/abs/1803.00567

Assumes CuPy version 13.x
Requires CuPy to be installed in the Houdini environment, can be done with this console command:
"C:\Program Files\Side Effects Software\Houdini 20.5.684\bin\hython.exe" -m pip install cupy-cuda13x
^Switch the Houdini version and cupy cuda version as needed

Requires the NVIDIA CUDA Toolkit matching your Cuda version eg. 13
Houdini's path may need to append:
PATH = "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.0/bin;&"

Heavily commented in the form of notes/documentation for myself as I was learning this.
Updated 10/26/2025

Place in a python SOP, and create the required parameters on the SOP:
"epsilon" : float (Hard min: 1e-10; Soft Max: 0.2; Default: 0.03)
"min_iterations" : int (Hard min: 0; Soft Max: 30; Default: 3)
"max_iterations" : int (Hard min: 1; Soft Max: 500; Default: 200)
"tolerance" : float (Hard min: 1e-12; Soft Max: 0.1; Default: 1e-8)

Note: The main code block below all definitions requires __name__ == "builtins", which is __name__ for the Python
SOP in Houdini 20.5.

Plug in the source point cloud in the Python SOP's first input, and the target point cloud in the Python SOP's second
input.

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

This gets quite slow, try to limit yourself to a few thousand points if computed each step in a solver, and less than a
hundred thousand if computed once, otherwise it gets quite slow.
You could potentially interpolate the output ot_pos from a sparser point cloud to a denser point cloud

https://github.com/conlen-b/cb-houdini-tools/blob/main/sinkhorn-based-log-domain-optimal-transport/SinkhornBasedLogDomainOptimalTransportHoudini.py
"""

__author__ = "Conlen Breheny"
__copyright__ = "Copyright 2025, Conlen Breheny"
__version__ = "1.0.1" #Major.Minor.Patch

import cupy as cpy
from typing import Optional, Tuple, Dict


def _logsumexp(
    a: cpy.ndarray,
    axis: Optional[int] = None
) -> cpy.ndarray:
    """
    Cupy-only implementation of scipy.special import logsumexp.

    Logsumexp takes takes each log value and takes them back to linear space with linear_n = e^n. It then sums all of
    the linear values, and takes the log of that linear sum. This is not the same as summing all of the log values and
    then taking that sum of logs back to linear. (It is a log of a linear sum, not a sum of logs)

    :param a: cpy.ndarray of values in natural log (log base e) space.
    :param axis: optional integer specifying the axis along which to sum. If None, sum over all elements.
    :return: cpy.ndarray with log of summed exponentials along the specified axis.
    """

    """Find the maximum value along the specified axis that is being summed.
    Exponentiating very large/small numbers can over/underflow, so subtracting the max before then adding it back after
    keeps the numbers in a safe range. Full dimensions are kept for the computation"""
    a_max = cpy.max(a, axis=axis, keepdims=True)
    #Subtract the max, linearize, sum the linear, go back to log, add back the max
    res = a_max + cpy.log(cpy.sum(cpy.exp(a - a_max), axis=axis, keepdims=True))
    """Discard unecessary dimensions after computation, eg. if axis=1 for a (3,4) array, res is initially (3,1);
    squeeze makes it (3,)"""
    return cpy.squeeze(res, axis=axis)



def _sinkhorn_log_domain(
    src_pts: cpy.ndarray,
    tgt_pts: cpy.ndarray,
    src_wgts: Optional[cpy.ndarray] = None,
    tgt_wgts: Optional[cpy.ndarray] = None,
    epsilon: float = 0.05,
    min_iterations: int = 3,
    max_iterations: int = 200,
    tolerance: float = 1e-12,
    verbose: bool = False
) -> Tuple[cpy.ndarray, Dict[str, object]]:
    """
    Compute the Sinkhorn optimal transport matrix in the log-domain (for numerical stability).

    :param src_pts: cpy.ndarray of shape (n, d) representing the source point positions.
    :param tgt_pts: cpy.ndarray of shape (m, d) representing the target point positions.
    :param src_wgts: optional cpy.ndarray of shape (n,) representing source point weights (sum to 1).
        If None, uniform weights are used.
    :param tgt_wgts: optional cpy.ndarray of shape (m,) representing target point weights (sum to 1).
        If None, uniform weights are used.
    :param epsilon: float, entropic regularization parameter (larger = smoother/blurrier matching).
    :param min_iterations: int, minimum number of Sinkhorn iterations before checking for convergence.
    :param max_iterations: int, maximum number of Sinkhorn iterations to perform.
    :param tolerance: float, early stopping threshold based on marginal error.
    :param verbose: bool, if True, prints convergence information every ~32 iterations.

    Returns
    -------
    transport_matrix : cpy.ndarray, shape (n, m)
        The optimal transport plan between source and target points.
    info : dict
        Dictionary with convergence info (iterations, epsilon, converge_type).
    """
    
    num_sources = src_pts.shape[0] #.shape returns (rows,columns); .shape[0] returns row count
    num_targets = tgt_pts.shape[0]
    
    # Assign uniform weights if not provided
    if src_wgts is None:
        #cpy.ones initializes a new array filled with 1.0 values, so uniform weight is created here
        src_wgts = cpy.ones(num_sources) / num_sources
    if tgt_wgts is None:
        tgt_wgts = cpy.ones(num_targets) / num_targets

    # Ensure float64 precision
    src_wgts = src_wgts.astype(cpy.float64)
    tgt_wgts = tgt_wgts.astype(cpy.float64)
    # Make array sum to 1.0 (normalize)
    src_wgts /= src_wgts.sum()
    tgt_wgts /= tgt_wgts.sum()

    """Compute cost matrix (squared Euclidean distance)
    cost[i, j] = ||src_pts[i] - tgt_pts[j]||²

    cpy.sum axis arg can sum either all the rows or all of the columns, axis=1 collapses columns and therefore sums
    each row, returning an array of the sum of each row"""
    source_squared = cpy.sum(src_pts**2, axis=1)[:, None] 
    target_squared = cpy.sum(tgt_pts**2, axis=1)[None, :]
    """
    [None, :] and [:, None] reshape the 1D array into a 2D matrix. The source points are made into a vertical matrix
    (n rows, 1 column), and the target points are made into a horizontal matrix (1 row, n columns). The None value is
    so that when added they can be broadcast, which means that the data is repeated into the other dimension so that
    addition can happen between differently sized matrices, eg.
    source_squared (3x1)      target_squared (1x2)
    [[s1]]                     [[t1, t2]]
    [[s2]]    + broadcast ->   [[t1, t2]] repeated
    [[s3]]                     [[t1, t2]] repeated

    Result when added in the cost matrix:
    [[s1+t1, s1+t2],
     [s2+t1, s2+t2],
     [s3+t1, s3+t2]]

    cpy.matmul is matrix multiplication. .T switches the rows and columns of a matrix, flipping it over the diagonal.
    The addition requres the flipped rows/columns from the alternating [:, None] and [None, :], but the multiplication
    requires the transpose."""
    cost_matrix = source_squared + target_squared - 2.0 * cpy.matmul(src_pts,tgt_pts.T) 
    """The cost matrix dimensions are row_count: num_src_pts, column_count: num_tgt_pts. Each entry corresponds to the
    distance between the source and target points described by the index eg. [src_pt, tgt_pt]"""

    """Compute log of kernel: log(K) = -C / ε. The non-log kernel is K = e^(-C/ε), but log of e^(n) results in n, so
    the log of K results in -C / ε. log_kernel has shape (num_sources, num_targets) and stores log(K_ij) = -C_ij / ε"""
    log_kernel = -cost_matrix / float(epsilon)

    # Initialize scaling factors (log_u, log_v)
    log_u = cpy.zeros(num_sources, dtype=cpy.float64)
    log_v = cpy.zeros(num_targets, dtype=cpy.float64)

    """Convert weights to log domain.
    1e-256 is added to prevent taking the logarithm of zero which is negative infinity or an error. 1e-256 is chosen to
    be safely above underflow for double precision, but small enough not to affect the computation significantly."""

    log_src_wgts = cpy.log(src_wgts + 1e-256)
    log_tgt_wgts = cpy.log(tgt_wgts + 1e-256)

    """Initialize error as infinity, because all subsequent iterations will have lower error than infinity so it won't
    terminate. The error checks for convergence, or when the error is less than the tolerance."""
    previous_error = cpy.inf
    converge_type = ""

    """
    Sinkhorn iterative updates - converge towards the u and v scaling factors that balance out the K matrix so that the
    source and target weights work as desired.
    In practice, what happens is:
    If a source is in a crowded area, its K[ij] values will be high, so u becomes smaller so it sends less per neighbor
    If a source is more isolated, its K[ij] row sum is low, so u becomes larger, so it sends more per neighbor
    The same logic applies to targets with v
    """
    for iteration in range(max_iterations):
        # Step 1: Update source scaling (u)
        """
        log_v[None, :] reshapes log_v to (1, num_targets) so it can broadcast along the rows. Broadcasting is where
        numpy pretends that the data is repeated so that addition can take place, eg.
        log_kernel = [[k11, k12, k13],
                      [k21, k22, k23]]

        log_v[None, :] = [[v1, v2, v3]]   # 1 row, 3 columns
        broadcast -> [[v1, v2, v3],       # repeated for each row
                      [v1, v2, v3]]

        log_kernel + log_v[None, :] = [[k11+v1, k12+v2, k13+v3],
                                       [k21+v1, k22+v2, k23+v3]]

        Logsumexp takes takes each log value and takes them back to linear space with linear_n = e^n. It then sums all
        of the linear values, and takes the log of that linear sum. This is not the same as summing all of the log
        values and then taking that sum of logs back to linear.
        (It is a log of a linear sum, not a sum of logs)

        Overall, adds v values to the kernel and computes the log sum.

        In the first pass, log_v is 1 everywhere, so this is the assumption that the algorithm starts with and it
        converges as more iterations are ran.
        """
        log_kernel_v = _logsumexp(log_kernel + log_v[None, :], axis=1)
        log_u = log_src_wgts - log_kernel_v #Update log_u so that the rows of the scaled kernel sum to the source weight

        # Update target scaling (v)
        log_kernel_t_u = _logsumexp((log_kernel + log_u[:, None]).T, axis=1)
        #Update log_v so that the columns of the scaled kernel sum to the target weight
        log_v = log_tgt_wgts - log_kernel_t_u

        """Check convergence every ~32 iterations (or final). & 31 is equal to % 32, it is a bitwise operation that runs
        faster than modulo since it is 32 so it is an optimization."""
        if (iteration & 31) == 0 or iteration == max_iterations - 1:
            """Add the scaling factors to the kernel and sum the columns (targets), to next check if we have converged
            on the target weights"""
            log_col_sums = _logsumexp(log_u[:, None] + log_kernel + log_v[None, :], axis=0)
            """Compute how close the columns (targets) of the scaled kernel are to the target weights.
            Currently, target weights (columns) is all that is checked for convergence, not source weights."""
            marginal_error = cpy.max(cpy.abs(cpy.exp(log_col_sums) - tgt_wgts))

            if verbose:
                #:4d prints an integer with minimum 4 digits, so space padding is added to <4 digit integers
                #.3e prints the float as scientific/exponential notation with 3 digits after the decimal point
                print(f"[Sinkhorn] Iter {iteration:4d} | Max marginal error = {marginal_error:.3e}")

            if iteration >= min_iterations:
                #If the error is less than the tolerance, consider it converged and the solution to our OT
                if marginal_error < tolerance:
                    converge_type = "Error < tolerance"
                    break

                """If the error has barely changed between the current and previous iteration, consider it converged
                due to stagnation"""
                if abs(previous_error - marginal_error) < 1e-12:  #stagnation check
                    converge_type = "Stagnation"
                    break

            #Save out the previous error for the stagnation check
            previous_error = marginal_error

    #Compute final transport matrix after convergence: P = exp(log_u + logK + log_v)
    log_transport = log_u[:, None] + log_kernel + log_v[None, :] #Add computed scaling values to kernel
    transport_matrix = cpy.exp(log_transport) #Convert from natural log to linear

    """The weights were normalized to sum to 1 before Sinkhorn. Due to floating point precision, it may now sum slightly
    less or more than 1. This normalization makes it sum exactly to 1 based on the source weights so that each source
    distributes 100% of its mass."""
    transport_matrix /= (transport_matrix.sum(axis=1)[:, None] + 1e-300)

    info = {
        "iterations": iteration + 1,
        "epsilon": epsilon,
        "converge_type": converge_type
    }

    return transport_matrix, info #Return the transport plan and metadata.



def _zspc_sbld_optimal_transport():
    """
    The main code block for this implementation of Sinkhorn Based Log Domain Optimal Transport.

    Outputs the attribute ot_pos on the source points, which is the position of each point after optimal transport.
    
    :return: Void
    """
    node = hou.pwd()
    geo = node.geometry()
    geo_1 = node.inputs()[1].geometry()   # assumes you wired target points into input 1

    #Get parameters
    epsilon_parm_value = node.parm("epsilon").eval()
    min_iterations_parm_value = node.parm("min_iterations").eval()
    max_iterations_parm_value = node.parm("max_iterations").eval()
    tolerance_parm_value = node.parm("tolerance").eval()

    # get source points A (e.g. previous-frame webbing points for WDAS Druun setup)
    src_pts = cpy.array([p.position() for p in geo.points()], dtype=cpy.float64)

    tgt_pts = cpy.array([p.position() for p in geo_1.points()], dtype=cpy.float64)

    """optional weights - None results in uniform weights, otherwise pass in an array of weights
    (eg. read from an attribute)"""
    src_wgts = None
    tgt_wgts = None

    transport_matrix, info = _sinkhorn_log_domain(src_pts,
                                                    tgt_pts,
                                                    src_wgts=src_wgts,
                                                    tgt_wgts=tgt_wgts,
                                                    epsilon=epsilon_parm_value,
                                                    min_iterations=min_iterations_parm_value,
                                                    max_iterations=max_iterations_parm_value,
                                                    tolerance=tolerance_parm_value,
                                                    verbose=False)

    """Applying the transport matrix to the target points results in the optimally transported/mapped source point
    positions.
    The source point positions are the weighted average of the influencing target points based on their influence/mass
    (a barycenter)"""
    transported_src_pts = cpy.matmul(transport_matrix, tgt_pts)
    transported_src_pts_cpu = cpy.asnumpy(transported_src_pts)

    #Construct flat array of floats for Houdini as detail vector arrays not supported in Houdini 20.5.
    transported_src_pts_flat = transported_src_pts_cpu.flatten().tolist()

    #Write to detail array attribute instead of point attribute to avoid for each loop API calls -- optimization.
    if geo.findPointAttrib("ot_flat_pos_array") is None:
        geo.addArrayAttrib(hou.attribType.Global, "ot_flat_pos_array", hou.attribData.Float, len(src_pts) * 3)

    geo.setGlobalAttribValue("ot_flat_pos_array", transported_src_pts_flat)

if (__name__ == "builtins"): #Houdini Python SOP __name__
    _zspc_sbld_optimal_transport()