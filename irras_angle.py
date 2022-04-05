import argparse
import re
import sys
from collections import namedtuple

import numpy as np
from matplotlib import pyplot as plt
# from scipy.interpolate import interp1d
# from scipy.optimize import nnls
# from scipy.stats import linregress


def parse_args():
    parser = argparse.ArgumentParser(description="""
        Fits calculated x. y and z components of IR spectrum to experimental
        ones and plot the results. Can also be used for plotting only.""")
    # capital_group = parser.add_mutually_exclusive_group()
    # capital_group.add_argument("-P". "--plot". action="store_true".
    #                            help="Plot Mode")
    # capital_group.add_argument("-F". "--fit". action="store_true".
    #                            help="Fit Mode")
    #
    parser.add_argument("-o", "--outfile", metavar="",
                        help="Name of the ORCA output file")
    parser.add_argument("-e", "--expfile", metavar="",
                        help="Name of the file containing the experimental "
                             "spectrum")
    # parser.add_argument("-p". "--paramfile". metavar="".
    #                     help="Name of the parameter file used for fitting")
    parser.add_argument("-lw", "--linewidth", metavar="", type=float,
                        default=15, help="Linewidth used for plotting and "
                                         "fitting")
    parser.add_argument("-x0", "--xmin", metavar="", type=float, default=500,
                        help="Minimum x value for plotting")
    parser.add_argument("-x1", "--xmax", metavar="", type=float, default=4000,
                        help="Maximum y value for plotting")
    parser.add_argument("-n", "--npoints", metavar="", type=float,
                        default=1024, help="Number of points used for plotting"
                                           " and fitting.")
    parser.add_argument("-bs", "--baselineshift", metavar="", type=float,
                        default=None, help="Absolute amount of baseline "
                                           "shifting for experimental "
                                           "spectrum")
    parser.add_argument("-sf", "--scalefactor", metavar="", type=float,
                        default=None, help="Scaling factor for the calculated "
                                           "spectrum which will also be used "
                                           "for fitting.")
    parser.add_argument("-x", "--plotx", action="store_true",
                        help="Plot x-polarized component of spectrum")
    parser.add_argument("-y", "--ploty", action="store_true",
                        help="Plot x-polarized component of spectrum")
    parser.add_argument("-z", "--plotz", action="store_true",
                        help="Plot x-polarized component of spectrum")
    parser.add_argument("-t", "--plottotal", action="store_false",
                        help=" Plot total IR Spectrum (Default = True)")
    return parser


def parse_outfile(outfile, scalefactor=1):
    """ This parses ORCA output (currently 5.0 dev version). Parse variable
    returns True only between the lines containing 'IR Spectrum' and the next
    line starting with an asterisk which includes only the IR transitions.
    Returns the wave number of the transition and T**2. x. y. z polarized
    values as arrays. Optional scaling factor included as command line arg.
    """
    try:
        with open(f"{outfile}", "r") as f:
            f_lines = f.readlines()
    except FileNotFoundError:
        sys.exit("Error! ORCA output file not found or not given! Exiting ...")

    wavenumber = []
    x = []
    y = []
    z = []
    t_sq = []
    pattern = re.compile(r"^\s*\d+:")
    parse = False
    for line in f_lines:
        matches = pattern.match(line)
        if "IR SPECTRUM" in line:
            parse = True
        if line.startswith("*"):
            parse = False
        if matches is not None and parse:
            line = line.replace("(", "")
            line = line.replace(")", "")
            splitline = re.split(r"\s+", line.strip())
            wavenumber.append(float(splitline[1]))
            t_sq.append(float(splitline[4]))
            x.append(float(splitline[5]) ** 2)
            y.append(float(splitline[6]) ** 2)
            z.append(float(splitline[7]) ** 2)

    wavenumber = np.multiply(wavenumber, scalefactor)

    if wavenumber.size == 0 or wavenumber.size != len(z):
        raise ValueError("Error! Invalid ORCA output file")
    else:
        calc_spectrum = namedtuple("Spectrum", ["wn", "t_sq", "x", "y", "z"])
        return calc_spectrum(wavenumber, t_sq, x, y, z)


def parse_exp(expfile, bls=0):
    """This can be used to parse any column-shaped text file (such as
    experimentally recorded spectra. The function returns the first two
    columns and offers baseline shifting (as optional arg) if desired.
    """
    try:
        with open(expfile, "r") as f:
            f_lines = f.readlines()
    except FileNotFoundError:
        sys.exit("Error! Experimental spectrum file not found! Exiting ...")
    except TypeError:
        sys.exit("Error! No experimental spectrum file was given! Exiting ...")

    pattern = re.compile(r"^\d")
    header_count = 0
    for line in f_lines:
        if pattern.match(line) is None:
            header_count += 1
        else:
            break

    with open(expfile, "w") as f:
        for line in f_lines:
            line = line.replace(".", ".")
            f.write(line)
    try:
        x, y, *_ = np.genfromtxt(expfile, skip_header=header_count, unpack=True)
    except ValueError:
        raise

    y = np.add(y, bls)
    exp_spectrum = namedtuple("Spectrum", ["x", "y"])
    return exp_spectrum(x, y)


def parse_params(paramfile):
    """Parses the param file which must contain the x values (wave numbers)
    of the experimental and calculated spectra in the first and second column
    respectively which are to be used for fitting.
    """
    try:
        with open(paramfile, "r") as f:
            f_lines = f.readlines()
    except FileNotFoundError:
        sys.exit("Error! Parameter file not found! Exiting ...")
    except TypeError:
        sys.exit("Error! No parameter file was given! Exiting ...")

    pattern = re.compile(r"^\d")
    header_count = 0
    for line in f_lines:
        if pattern.match(line) is None:
            header_count += 1
        else:
            break
    exp, calc = np.genfromtxt(paramfile, skip_header=header_count, unpack=True)
    return exp, calc


def gaussian(x, amp, cen, sigma):
    """Returns the y value of a Gaussian at position x with amplitude amp.
    centered at cen and linewidth of sigma.
    """
    y = amp * np.exp(-((x - cen) ** 2) / (2 * sigma ** 2))
    return y


def broaden_spec(xvals, stick_x, stick_y, lw):
    """This creates a broadened spectrum from a stick spectrum passed
    in as stick_x and stick_y. The xvals passed are a separate array
    defining the x-range of the final spectrum.
    """
    final_spec = []
    for x in xvals:
        total = 0
        for xpos, yval in zip(stick_x, stick_y):
            if abs(x - xpos) < 4 * lw:
                total += gaussian(x, yval, xpos, lw)
        final_spec.append(total)
    return final_spec


def norm_spec(y):
    """This normalizes an array y given as argument.
    """
    return np.divide(y, np.amax(y))


# def spec_fit(exp, calc):
#     """This determines the best fit of two spectra using scaling and
#     x-shifting given two arrays which are taken from the parameter file.
#     """
#     slope, intercept, *_ = linregress(calc, exp)
#     return slope, intercept


# def fit(outfile, expfile, paramfile):
#     """This is supposed to provide a solution to the least-squares fit of
#     two spectra. Currently this uses user provided x-axis values of
#     experimental and calculated spectra as parameters.
#     """
#     wn_calc, t2, x_pol, y_pol, z_pol = parse_outfile(outfile)
#     wn_exp, y_exp = parse_exp(expfile)
#     x_exp_fit, x_calc_fit = parse_params(paramfile)
#
#     y_exp = norm_spec(y_exp)
#     f_exp = interp1d(wn_exp, y_exp, kind="cubic")
#     f_x_calc = interp1d(wn_calc, x_pol, kind="cubic")
#     f_y_calc = interp1d(wn_calc, y_pol, kind="cubic")
#     f_z_calc = interp1d(wn_calc, z_pol, kind="cubic")
#
#     x_calc = np.array([f_x_calc(item) for item in x_calc_fit])
#     y_calc = np.array([f_y_calc(item) for item in x_calc_fit])
#     z_calc = np.array([f_z_calc(item) for item in x_calc_fit])
#
#     a = np.column_stack((x_calc, y_calc, z_calc))
#     b = np.array([f_exp(item) for item in x_exp_fit])
#     sol, *_ = nnls(a, b)
#     return sol


def main():
    wn, t2, x_pol, y_pol, z_pol = parse_outfile(args.outfile, args.scalefactor)
    if args.expfile:
        x_exp, y = parse_exp(args.expfile, args.baselineshift)
        y = norm_spec(y)
        plt.plot(x_exp, y, label="Experimental Spectrum")

    x_min, x_max = args.xmin, args.xmax
    x_calc = np.linspace(x_min, x_max, args.npoints)

    y1 = broaden_spec(x_calc, wn, x_pol, args.linewidth)
    y2 = broaden_spec(x_calc, wn, y_pol, args.linewidth)
    y3 = broaden_spec(x_calc, wn, z_pol, args.linewidth)
    y4 = broaden_spec(x_calc, wn, t2, args.linewidth)

    # if args.plot:
    norm_factor = np.amax(y4)
    if args.plotx:
        plt.plot(x_calc, np.divide(y1, norm_factor), "b", label="x-pol. Calc. Spectrum")
    if args.ploty:
        plt.plot(x_calc, np.divide(y2, norm_factor), "r", label="y-pol. Calc. Spectrum")
    if args.plotz:
        plt.plot(x_calc, np.divide(y3, norm_factor), "y", label="z-pol. Calc. Spectrum")
    if args.plottotal:
        plt.plot(x_calc, norm_spec(y4), "k", label="Total Calc. Spectrum")
    # elif args.fit:
    #     params = fit(args.outfile, args.expfile, args.paramfile)
    #     norm = np.linalg.norm(params)
    #     n_y1, n_y2, n_y3 = np.divide(params, norm)
    #     y5 = np.multiply(y1, n_y1) + np.multiply(y2, n_y2) + np.multiply(y3,
    #                                                                      n_y3)
    #     y5 = norm_spec(y5)
    #     plt.plot(x_calc, y5, "g", label=f"Fitted spectrum with\n{n_y1:.2f}"
    #                                     f" {n_y2:.2f} {n_y3:.2f}")
    # else:
    #     sys.exit(("Error! Neither plotting nor fitting was requested! Exiting"
    #               " ..."))

    plt.xlim(x_max, x_min)
    plt.legend()
    plt.show()


if __name__ == "__main__":
    args = parse_args().parse_args()
    main()
