# Hip Quips!
Standalone hip files (not packaged tools) showing various techniques. Provided as-is and individual files are not guaranteed future updates or bugfixes.

Please feel free to tip if any of these files help and you'd like to support me!  
https://www.paypal.me/conlenb

## Curve Coordinate System: Copy Circles + Lines
These files both use one of my favorite techniques -- building a coordinate system along a curve by copying circles along the curve and then lines along the circles. I originally learned this methodology from Eric Araujo, and have since expanded it for various usecases.

### [Volume noise along curves](./curve-coordinate-system-copy-circles-lines/volume-noise-along-curves/curve_rest_volume_noise_copy_circles_lines_v003.hipnc)

Shows 3 methods of creating a "rest" coordinate system from the curve copied circles + line technique that can then be used to sample noise, either via rasterizing rest to a vector volume or by sampling the geometry rest attribute from another volume. See the sticky notes in the hip file for more info and detail.

<img src="./curve-coordinate-system-copy-circles-lines/docs/curve_rest_noise_billowy_noise.gif" alt="Curve Rest Billowy Noise" height="300" />

| [Hip File](./curve-coordinate-system-copy-circles-lines/volume-noise-along-curves/curve_rest_volume_noise_copy_circles_lines_v003.hipnc) |
| --- |

### [Velocity pumps along curves](./curve-coordinate-system-copy-circles-lines/velocity-pumps-along-curves/CurveCopyCirclesLinesTricks_Pumps_v005.hipnc)

Shows a method for creating velocity fields from curves using the curve copied circles + line technique, where velocities along, around, and towards/away from the curve can be directed based on various controls. See the sticky notes in the hip file for more info and detail.

<img src="./curve-coordinate-system-copy-circles-lines/docs/ExamplePumpvel_01.gif" alt="Curve Pumpvel 01" height="300" />
<img src="./curve-coordinate-system-copy-circles-lines/docs/ExamplePumpvel_02.gif" alt="Curve Pumpvel 02" height="300" />

| [Hip File](./curve-coordinate-system-copy-circles-lines/velocity-pumps-along-curves/CurveCopyCirclesLinesTricks_Pumps_v005.hipnc) |
| --- |