# **[Copy Parms to Other Node](./CopyParmsToOtherNode.py)**
A script to copy a parm or all parms in source parm folder from source node to the destination node.

## Installation
1. Download the folder `copy-parms-to-other-node`.
2. Move the files to Houdini's `packages` folder:
   - Copy the `copy-parms-to-other-node` folder into Houdini's `packages` directory
   - Inside the `copy-parms-to-other-node` folder, copy the `copy-parms-to-other-node.json` file and place it directly into Houdini's `packages` directory
        - On Windows `C:\Users\[USERNAME]\Documents\Houdini[VERSION]\packages`
3. Install QtPy:
   - Open Command Prompt
   - Run the following command (edit the `[PROGRAM_FILES_PATH]` and `[VERSION]` to the path to your program files and the correct Houdini version respectively):  
        ```sh
        "[PROGRAM_FILES_PATH]\Side Effects Software\Houdini [VERSION]\bin\hython.exe" -m pip install QtPy
        ```

## Shelf Button Creation
1. In the Houdini interface, go to the **Shelf** area
2. **Right-click** on an empty space in the Shelf and select **New Tool...**
3. In the **Edit tool** window, in the **Script** tab, paste in the following Python code:
    ```python  
   from copyParmsToOtherNode import CopyParmsUI

    copy_parms_ui = CopyParmsUI()
    copy_parms_ui.display()
    ```
4. Click **Accept** to save the new button on the Shelf

## How To Use:
IN PROGRESS