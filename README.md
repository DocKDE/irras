# IRRAS

This repo provides a utility program to overlay experimental and calculated IR
or IRRA spectra. Only spectra calculated with ORCA are supported, however.

`irras_angle.py` provides a command line tool, `irras_gui.py` is a GUI with both
having the same functionality. The GUI is the recommended way of interaction.

Features:
- Baseline shifting of experimental spectra
- Scaling factors for calculated spectra
- Variable linewidth for calculated spectra
- Variable number of points for calculated spectra
- Displaying x-, y- and z-polarized components of calculated spectra
- Saving plot to file

![IRRAS example usage](/examples/example.png)
