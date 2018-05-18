# Rather Robust Video Server (RRVS)

## Install

To install the package, and all of its dependencies:

    make install # <-- preferably do this within a virtualenv
    
This will install rrvs and associated dependencies to your current python environment. Performing this command from within a virtual env will localize all installed packeges to that virtualenv.

## Getting Started with RRVS

To run a camera that is locally connected to your system:

    python -m rrvs.utils.test_camera 0 # <--- displays video feed from device at /dev/video0
    
To stream video over a network:

    # ensure that at least one camera is connected to your system
    python -m rrvs.ctrl assign            # follow the wizards instructions
    python -m rrvs.ctrl restart_server    # server will update with new assignments
    python -m rrvs.ctrl watch localhost <name-of-feed>
    
    
## Compatibility Notes

The rrvs module was written with python 3 in mind, but should always be backwards compatible with python 2.7. If any issues with running this code within python 2.7 are discovered, feel free to let me know by posting about it in the issues section.
