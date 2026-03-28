# **[POP Interaction Forces HDA](./dop_cb_pop_interaction_forces.1.0.hdanc)**
[`dop_cb_pop_interaction_forces.1.0.hdanc`](./dop_cb_pop_interaction_forces.1.0.hdanc)  
An HDA implementation of DreamWorks Animation's paper ["Shaping Particle Simulations with Interaction Forces"](https://dl.acm.org/doi/10.1145/2614106.2614121) (Can Yuksel et al.).

This tool enables complex and art-directable particle motion and shaping derived from the existing intrinsic qualities of the particle field.

https://github.com/user-attachments/assets/a5bbffb9-a720-41a4-aec8-65c09296b3a3

## How To Use:
Example .hip file here:  
[`POP_Interaction_Forces_Chain_Fluid_DreamWorks_v020.hipnc`](./example-hip/POP_Interaction_Forces_Chain_Fluid_DreamWorks_v020.hipnc)

### Theory
To use this tool effectively, it is helpful to broadly understand how it works under the hood.
#### Local Axes
First, each point in the point cloud looks at all of its neighbors within a given radius.  
<img src="./docs/explainer-01.jpg" alt="Explainer 01" height="180" />
<img src="./docs/explainer-02.jpg" alt="Explainer 02" height="180" />
<img src="./docs/explainer-03.jpg" alt="Explainer 03" height="180" />

Next, the average/mean of all of the neighbors is marked as the "LDNP center"/center of mass.  
<img src="./docs/explainer-04.jpg" alt="Explainer 04" height="200" />

Then, the local axes of the cluster is calculated so that the X/U axis is aligned down the longest part of the cluster, the Y/V axis is aligned to the second longest, and the Z/W axis is aligned to the shortest part of the cluster.  
<img src="./docs/explainer-05.jpg" alt="Explainer 05" height="200" />

After that, the local axes are "stabilized" to prevent flipping between frames. The X axis is stabilized so that it points more towards the velocity vector of the point than it does away from it, the Y axis is stabilized to a user defined "Eigen Y Target" vector, and the Z axis is reconstructed from those.  
<img src="./docs/explainer-06.jpg" alt="Explainer 06" height="200" />
<img src="./docs/explainer-07.jpg" alt="Explainer 07" height="200" />

#### Forces
Once the local axes have been found and stabilized, they can be used to create custom forces based on user parameters.

The first force option is "To Center", which is simply a force that directs the particle towards the center of mass of its neighbors.  
<img src="./docs/explainer-08.jpg" alt="Explainer 08" height="200" />

The next force is "Along Axes", which allows you to push/pull particles in the direction (or the opposite direction) of each local axis.  
<img src="./docs/explainer-09.jpg" alt="Explainer 09" height="180" />
<img src="./docs/explainer-10.jpg" alt="Explainer 10" height="180" />
<img src="./docs/explainer-11.jpg" alt="Explainer 11" height="180" />

"To Axes" allows you to move particles towards (or away from) the nearest point on the local axis from the LDNP center.
<img src="./docs/explainer-12.jpg" alt="Explainer 12" height="180" />
<img src="./docs/explainer-13.jpg" alt="Explainer 13" height="180" />
<img src="./docs/explainer-14.jpg" alt="Explainer 14" height="180" />

The final force, "Around Axes", moves the particles so that they orbit around the local axes.  
<img src="./docs/explainer-15.jpg" alt="Explainer 15" height="180" />
<img src="./docs/explainer-16.jpg" alt="Explainer 16" height="180" />
<img src="./docs/explainer-17.jpg" alt="Explainer 17" height="180" />

### Parameters
<img src="./docs/ui.png" alt="UI Window" height="400" />
<br/><br/>

> **Group:** The point group to apply the forces to.
>
> **Solve Objects on Creation Frame:** Whether the internal SOP solver DOP should solve objects on creation frame.
>
> **Radius:** The radius that each particle should use to construct its local cluster.
>
>**Global Scale:** A global multipler on the force applied.
>
>**Treat As Wind:** Instead of adding force, the targetv and airresist attributes are used as a "wind speed" to be matched by the particle. This causes the particle to be dragged to the goal speed, reducing overshoot.
>
>**Air Resistance:** How much particles are to be influenced by this wind field.
>
>**Internal Reduction Percent:** As an optimization, what percent of the particles are ignored when calculating the local axes internally.

>#### Interaction Forces
>**Eigen Y Target**:

*Docs are work in progress/unfinished*