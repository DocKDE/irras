from os.path import basename
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
import matplotlib.pyplot as plt
import numpy as np

import irras_angle


class MainApplication(tk.Frame):

    def __init__(self, master):
        self.master = master
        tk.Frame.__init__(self, self.master)

    def configure_gui(self):
        # Setup frames to put stuff in.
        self.status_frame = tk.Frame(self.master)
        self.graph_frame = tk.Frame(self.master)
        self.button_frame = tk.Frame(self.master)

        # This setup ensures that GUI scales correctly when window size is
        # changed. Only the Frame containing the graph is allowed to expand.
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        self.graph_frame.pack(side=tk.LEFT, fill="both", expand=True)
        self.button_frame.pack(side=tk.RIGHT, fill="both", expand=False)

    def create_widgets(self):
        # Define widget placement in frames. Actual creation of widgets
        # happens in each respective function called.
        self.create_menubar(self.master)
        self.create_statusbar(self.status_frame)
        self.draw_canvas(self.graph_frame)
        self.create_user_input(self.button_frame)

    def create_menubar(self, root):
        self.menu = tk.Menu(root)
        root.config(menu=self.menu)
        self.file_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_menu)

        self.expbutton = self.file_menu.add_command(label="Open exp file",
                                                    command=self.get_exp)
        self.calcbutton = self.file_menu.add_command(label="Open calc file",
                                                     command=self.get_calc)

    def get_exp(self):
        # askopenfilenames() allows selection of multiple files and returns
        # a tuple.
        self.expfiles = tk.filedialog.askopenfilenames()
        # Checking whether a file was actually selected. Would otherwise throw
        # error if "cancel" was pressed
        if self.expfiles:
            self.x_exp = []
            self.y_exp = []
            # Handling of errors from invalid files happens here. Much more
            # convenient than having that later on.
            try:
                for file in self.expfiles:
                    self.x_exp.append(irras_angle.parse_exp(file)[0])
                    self.y_exp.append(irras_angle.parse_exp(file)[1])
                self.draw_graph()
            except ValueError:
                # Can only be reached once the "file" local variable has already
                # been declared in the above for-loop so it's fine.
                tk.messagebox.showerror("Error", f"Invalid experimental file: {basename(file)}")
            else:
                self.update_expbar(self.expfiles)

    def get_calc(self):
        self.calcfile = tk.filedialog.askopenfilename()
        # see above
        if self.calcfile:
            # see above
            try:
                self.wn, self.t2, self.x_pol, self.y_pol, self.z_pol = \
                    irras_angle.parse_outfile(self.calcfile)
                self.draw_graph()
            except ValueError:
                tk.messagebox.showerror("Error", "Invalid ORCA output file")
            else:
                self.update_calcbar(self.calcfile)

    def update_expbar(self, pathtuple=None):
        # Default to pathtuple=None to reset status bar, e.g. after
        # clearing all plotted spectra.
        if pathtuple:
            basenames = [basename(path) for path in pathtuple]
            if len(pathtuple) > 1:
                self.status_var_exp.set(f"""Experimental spectra '{"', '".join(basenames)}' loaded""")
            elif len(pathtuple) == 1:
                self.status_var_exp.set(f"""Experimental spectrum '{basenames[0]}' loaded""")
            self.status_bar_exp.update()
        else:
            self.status_var_exp.set("No experimental spectrum loaded")

    def update_calcbar(self, path=None):
        # see above
        if path:
            self.status_var_calc.set(f"""ORCA output '{basename(path)}' loaded""")
        else:
            self.status_var_calc.set("No ORCA output loaded")
        self.status_bar_calc.update()

    def create_statusbar(self, root):
        self.status_var_exp = tk.StringVar(master=root)
        self.status_var_exp.set("No experimental spectrum loaded")
        self.status_bar_exp = tk.Label(master=root,
                                       textvariable=self.status_var_exp,
                                       padx=10, relief=tk.SUNKEN, anchor=tk.W)

        self.status_var_calc =tk.StringVar(master=root)
        self.status_var_calc.set("No ORCA output loaded")
        self.status_bar_calc = tk.Label(master=root,
                                        textvariable=self.status_var_calc,
                                        padx=10, relief=tk.SUNKEN, anchor=tk.E)

        self.status_bar_exp.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_bar_calc.pack(side=tk.RIGHT, fill=tk.X, expand=True)

    def create_user_input(self, root):
        # Creating of widgets for user input frame happens here in logical order
        self.generic_opt_label = tk.Label(text="General plotting options", master=root, font="bold")

        self.xmin_label = tk.Label(text="x Min.", master=root)
        self.xmin_default = tk.StringVar(value="500", master=root)
        self.xmin_entry = tk.Entry(textvariable=self.xmin_default, master=root)

        self.xmax_label = tk.Label(text="x Max.", master=root)
        self.xmax_default = tk.StringVar(value="4000", master=root)
        self.xmax_entry = tk.Entry(textvariable=self.xmax_default, master=root)

        self.exp_opt_label = tk.Label(text="Exp. spectrum parameters", master=root, font="bold")

        self.baseline_label = tk.Label(text="Baseline Shift", master=root)
        self.baseline_default = tk.StringVar(value="0.00", master=root)
        self.baseline_entry = tk.Entry(textvariable=self.baseline_default,
                                       master=root)

        self.calc_opt_label = tk.Label(text="Calc. spectrum parameters", master=root, font="bold")

        self.linewidth_label = tk.Label(text="Linewidth", master=root)
        self.linewidth_default = tk.StringVar(value="15", master=root)
        self.linewidth_entry = tk.Entry(textvariable=self.linewidth_default,
                                        master=root)

        self.scalefactor_label = tk.Label(text="Scale factor", master=root)
        self.scalefactor_default = tk.StringVar(value="1.00", master=root)
        self.scalefactor_entry = tk.Entry(
            textvariable=self.scalefactor_default, master=root)

        self.npoints_label = tk.Label(text="# of Points", master=root)
        self.npoints_default = tk.StringVar(value="", master=root)
        self.npoints_entry = tk.Entry(textvariable=self.npoints_default,
                                      master=root)

        self.draw_x = tk.BooleanVar()
        self.draw_x.set(False)
        self.draw_x_checkbox = tk.Checkbutton(text="x", var=self.draw_x,
                                              master=root)

        self.draw_y = tk.BooleanVar()
        self.draw_y.set(False)
        self.draw_y_checkbox = tk.Checkbutton(text="y", var=self.draw_y,
                                              master=root)

        self.draw_z = tk.BooleanVar()
        self.draw_z.set(False)
        self.draw_z_checkbox = tk.Checkbutton(text="z", var=self.draw_z,
                                              master=root)

        self.draw_tot = tk.BooleanVar()
        self.draw_tot.set(True)
        self.draw_tot_checkbox = tk.Checkbutton(text="Total",
                                                var=self.draw_tot, master=root)

        self.invert_x = tk.BooleanVar()
        self.invert_x.set(True)
        self.invert_x_checkbox = tk.Checkbutton(text="Invert x-axis",
                                                var=self.invert_x, master=root)

        self.invert_y = tk.BooleanVar()
        self.invert_y.set(False)
        self.invert_y_checkbox = tk.Checkbutton(text="Invert y-axis",
                                                var=self.invert_y, master=root)

        self.clear_exp_button = tk.Button(text="Clear Exp",
                                          command=self.clear_exp, master=root)
        self.clear_calc_button = tk.Button(text="Clear Calc",
                                           command=self.clear_calc, master=root)

        self.draw_button = tk.Button(text="Draw", command=self.draw_graph,
                                     master=root)

        # Placement of widgets happens here. self.row_counter is there to make adding,
        # removing or moving widgets in the grid less of a pain. Kinda ugly though.
        self.row_counter = 0
        self.generic_opt_label.grid(row=self.row_counter, columnspan=4, pady=(20, 0), sticky="w")
        self.row_counter += 1

        self.xmin_label.grid(row=self.row_counter, column=0, columnspan=2, padx=5, pady=5,
                             sticky="e")
        self.xmin_entry.grid(row=self.row_counter, column=2, columnspan=2, padx=20, pady=5)
        self.row_counter += 1

        self.xmax_label.grid(row=self.row_counter, column=0, columnspan=2, padx=5, pady=5,
                             sticky="e")
        self.xmax_entry.grid(row=self.row_counter, column=2, columnspan=2, padx=20, pady=5)
        self.row_counter += 1

        self.exp_opt_label.grid(row=self.row_counter, columnspan=4, pady=(20, 0), sticky="w")
        self.row_counter += 1

        self.baseline_label.grid(row=self.row_counter, column=0, columnspan=2, padx=5,
                                 pady=5, sticky="e")
        self.baseline_entry.grid(row=self.row_counter, column=2, columnspan=2, padx=20,
                                 pady=5)
        self.row_counter += 1

        self.calc_opt_label.grid(row=self.row_counter, columnspan=4, pady=(20, 0), sticky="w")
        self.row_counter += 1

        self.linewidth_label.grid(row=self.row_counter, column=0, columnspan=2, padx=5,
                                  pady=5, sticky="e")
        self.linewidth_entry.grid(row=self.row_counter, column=2, columnspan=2, padx=20,
                                  pady=5)
        self.row_counter += 1

        self.scalefactor_label.grid(row=self.row_counter, column=0, columnspan=2, padx=5,
                                    pady=5, sticky="e")
        self.scalefactor_entry.grid(row=self.row_counter, column=2, columnspan=2, padx=20,
                                    pady=5)
        self.row_counter += 1

        self.npoints_label.grid(row=self.row_counter, column=0, columnspan=2, padx=5, pady=5,
                                sticky="e")
        self.npoints_entry.grid(row=self.row_counter, column=2, columnspan=2, padx=20, pady=5)
        self.row_counter += 1

        self.draw_x_checkbox.grid(row=self.row_counter, column=0)
        self.draw_y_checkbox.grid(row=self.row_counter, column=1)
        self.draw_z_checkbox.grid(row=self.row_counter, column=2)
        self.draw_tot_checkbox.grid(row=self.row_counter, column=3)
        self.row_counter += 1

        self.invert_x_checkbox.grid(row=self.row_counter, column=0, columnspan=2, pady=20)
        self.invert_y_checkbox.grid(row=self.row_counter, column=3, columnspan=2, pady=20)
        self.row_counter += 1

        self.clear_exp_button.grid(row=self.row_counter, column=0, columnspan=2, padx=10,
                                   pady=20)
        self.clear_calc_button.grid(row=self.row_counter, column=3, columnspan=2, padx=10,
                                    pady=20)
        self.row_counter += 1

        self.draw_button.grid(row=self.row_counter, column=0, columnspan=4, pady=30)
        self.row_counter += 1

    def draw_canvas(self, root):
        # Create matplotlib figure and axis and put it on canvas
        self.fig, self.ax = plt.subplots(figsize=(10, 7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill="both",
                                         expand=True, padx=10, pady=5)
        self.toolbar = NavigationToolbar2Tk(self.canvas, root)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill="both",
                                         expand=True)

    def draw_graph(self):
        # Wrapper function for draw_calc and draw_exp which handle the actual drawing.
        # Logic when to draw what goes here. Includes cleanup of axis when called to
        # make multiple calls in one session more convenient.
        self.ax.clear()
        self.xmin, self.xmax = int(self.xmin_entry.get()),\
                               int(self.xmax_entry.get())

        # This seemed more straightforward than doing this with exceptions in
        # attempt to comply with the IEAPF paradigm
        if hasattr(self, "expfiles"):
            self.draw_exp()
        if hasattr(self, "calcfile"):
            self.draw_calc()
        if not hasattr(self, "expfiles") and not hasattr(self, "calcfile"):
            tk.messagebox.showerror("Error", "No file loaded for plotting")
        else:
            self.ax.set_xlabel("Wavenumber", weight="bold")
            self.ax.set_ylabel("Intensity / a.u.", weight="bold")
            plt.xlim(self.xmin, self.xmax)
            if self.invert_x.get():
                self.ax.invert_xaxis()
            if self.invert_y.get():
                self.ax.invert_yaxis()
            self.ax.legend()
            plt.tight_layout()
            self.canvas.draw()

    def draw_exp(self):
        # self.y_exp = irras_angle.norm_spec(self.y_exp)
        # self.y_exp_shift = np.add(self.y_exp, float(self.baseline_entry.get()))
        # self.exp_curve = self.ax.plot(self.x_exp, self.y_exp_shift,
        #                               linewidth=2, label="Exp. Spectrum")
        self.y_exp = [irras_angle.norm_spec(spec) for spec in self.y_exp]
        self.y_exp_shift = [np.add(y, float(self.baseline_entry.get())) for y in self.y_exp]
        self.exp_curves = [self.ax.plot(x, y, linewidth=2, label=f"{basename(file)}") for (x, y, file) in zip(self.x_exp, self.y_exp_shift, self.expfiles)]
        # self.exp_curve = []
        # for x, y, basename in zip(self.x_exp, self.y_exp_shift, self.basenames):
        #     self.exp_curve.append(self.ax.plot(x, y, linewidth=2, label=f"{basename}"))

    def draw_calc(self):
        if not self.npoints_entry.get():
            self.x_calc = np.linspace(self.xmin, self.xmax,
                                      int((self.xmax - self.xmin) / 4))
        else:
            self.x_calc = np.linspace(self.xmin, self.xmax,
                                      int(self.npoints_entry.get()))
        self.wn_scaled = np.multiply(self.wn,
                                     float(self.scalefactor_entry.get()))

        self.y4 = irras_angle.broaden_spec(self.x_calc, self.wn_scaled,
                                           self.t2,
                                           float(self.linewidth_entry.get()))
        # This is needed to ensure that x,y,z are scaled properly w.r.t Tot.
        # Just normalizing each will not work here.
        self.norm_factor = np.amax(self.y4)

        if self.draw_tot.get():
            self.y4_curve = self.ax.plot(self.x_calc, irras_angle.norm_spec(self.y4),
                                         "k", linewidth=2, label="Total Calc. Spectrum")
        if self.draw_x.get():
            self.y1 = irras_angle.broaden_spec(self.x_calc, self.wn_scaled,
                                               self.x_pol,
                                               float(self.linewidth_entry.get()))
            self.ax.plot(self.x_calc, np.divide(self.y1, self.norm_factor),
                         "b", linewidth=1, label="x-pol. Calc. Spectrum")
            plt.fill_between(self.x_calc, np.divide(self.y1, self.norm_factor),
                             alpha=0.3)
        if self.draw_y.get():
            self.y2 = irras_angle.broaden_spec(self.x_calc, self.wn_scaled,
                                               self.y_pol,
                                               float(self.linewidth_entry.get()))
            self.ax.plot(self.x_calc, np.divide(self.y2, self.norm_factor),
                         "r", linewidth=1, label="y-pol. Calc. Spectrum")
            plt.fill_between(self.x_calc, np.divide(self.y2, self.norm_factor),
                             alpha=0.3)
        if self.draw_z.get():
            self.y3 = irras_angle.broaden_spec(self.x_calc, self.wn_scaled,
                                               self.z_pol,
                                               float(self.linewidth_entry.get()))
            self.ax.plot(self.x_calc, np.divide(self.y3, self.norm_factor),
                         "y", linewidth=1, label="z-pol. Calc. Spectrum")
            plt.fill_between(self.x_calc, np.divide(self.y3, self.norm_factor),
                             alpha=0.3)

    def clear_exp(self):
        try:
            delattr(self, "expfiles")
            self.update_expbar()
        except AttributeError:
            pass
        else:
            # Remove exp trace and have it garbage-collected
            for curve in self.exp_curves:
                curve.pop(0).remove()
            self.ax.get_legend().remove()
            # This is needed in case a calcfile is present, otherwise legend
            # would indiscriminately be removed.
            if hasattr(self, "calcfile"):
                self.ax.legend()
            self.canvas.draw()

    def clear_calc(self):
        # It's easier to just redraw the graph from scratch if self.expfile is present than
        # trying to remove every component of draw_calc() it seems.
        try:
            delattr(self, "calcfile")
            self.update_calcbar()
        except AttributeError:
            pass
        else:
            if hasattr(self, "expfiles"):
                # Implies clearing of ax which is called in the beginning of
                # "draw_graph()"
                self.draw_graph()
            else:
                # Can't just call draw_graph() because no data is present to be plotted
                # giving an error message.
                self.ax.clear()
                self.canvas.draw()

    def close_app(self):
        self.quit()
        self.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Irrasman")

    main_app = MainApplication(root)
    main_app.configure_gui()
    main_app.create_widgets()

# This is necessary for the app to close properly when the window close button
# is pressed. Otherwise the process will keep on running in the background
    root.protocol("WM_DELETE_WINDOW", main_app.close_app)
    root.mainloop()
