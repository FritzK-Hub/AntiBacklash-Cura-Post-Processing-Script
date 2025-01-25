# AntiBacklash Cura Post Processing Script
 Cura Post-Processing script to compensate 3D-Printer motor backlash.

## Installation
- Move the script into "%appdata%\cura\{CURA VERSION}\scripts"
- Restart Cura
- In Cura, goto "Extensions/Post Processing/Modify G-Code"
- Press "Add a script" and choose AntibacklashCura

## Credits
This script is based on "Backlash Compensation: Test and gcode Compensation Program" 
by steaksndwich on Thingiverse:
https://www.thingiverse.com/steaksndwich/designs

The Program and a model to test you prints can be found here:
https://www.thingiverse.com/thing:3060573

This script is free software. It comes without any warranty
Antibacklash can help you to compensate Backlash issues if there is no way to resolve it on the Hardware
(e.g. tighten Belts, Pulleys, Steppermount etc.)
Antibacklash is meant to be used for cartesian FDM Printers.
Only use it with Absolute Positioning (G90 must be in start gcode)