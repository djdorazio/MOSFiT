import argparse
import os
import shutil

from mosfit import __version__
from mosfit.fitter import Fitter
from mosfit.utils import is_master, prompt, print_wrapped


def main():
    """First, parse command line arguments.
    """

    dir_path = os.path.dirname(os.path.realpath(__file__))

    parser = argparse.ArgumentParser(
        prog='MOSFiT',
        description='Fit astrophysical light curves using AstroCats data.')

    parser.add_argument(
        '--events',
        '-e',
        dest='events',
        default=[''],
        nargs='+',
        help=("List of event names to be fit, delimited by spaces. If an "
              "event name contains a space, enclose the event's name in "
              "double quote marks, e.g. \"SDSS-II SN 5944\"."))

    parser.add_argument(
        '--models',
        '-m',
        dest='models',
        default=['default'],
        nargs='+',
        help=("List of models to use to fit against the listed events. The "
              "model can either be a name of a model included with MOSFiT, or "
              "a path to a custom model JSON file generated by the user."))

    parser.add_argument(
        '--parameter-paths',
        '-P',
        dest='parameter_paths',
        default=[''],
        nargs='+',
        help=("Paths to parameter files corresponding to each model file; "
              "length of this list should be equal to the length of the list "
              "of models"))

    parser.add_argument(
        '--plot-points',
        dest='plot_points',
        default=100,
        help=("Set the number of plot points when producing light curves from "
              "models without fitting against any actual transient data."))

    parser.add_argument(
        '--max-time',
        dest='max_time',
        type=float,
        default=1000.,
        help=("Set the maximum time for model light curves to be plotted "
              "until."))

    parser.add_argument(
        '--band-list',
        '--extra-bands',
        dest='band_list',
        default=[],
        nargs='+',
        help=("List of additional bands to plot when plotting model light "
              "curves that are not being matched to actual transient data."))

    parser.add_argument(
        '--band-systems',
        '--extra-systems',
        dest='band_systems',
        default=[],
        nargs='+',
        help=("List of photometric systems corresponding to the bands listed "
              "in `--band-list`."))

    parser.add_argument(
        '--band-instruments',
        '--extra-instruments',
        dest='band_instruments',
        default=[],
        nargs='+',
        help=("List of instruments corresponding to the bands listed "
              "in `--band-list`."))

    parser.add_argument(
        '--band-bandsets',
        '--extra-bandsets',
        dest='band_bandsets',
        default=[],
        nargs='+',
        help=("List of bandsets corresponding to the bands listed "
              "in `--band-list`."))

    parser.add_argument(
        '--exclude-bands',
        dest='exclude_bands',
        default=[],
        nargs='+',
        help=("List of bands to exclude in fitting."))

    parser.add_argument(
        '--exclude-instruments',
        dest='exclude_instruments',
        default=[],
        nargs='+',
        help=("List of instruments to exclude in fitting corresponding to "
              "the bands listed in `--exclude-bands`."))

    parser.add_argument(
        '--iterations',
        '-i',
        dest='iterations',
        type=int,
        default=-1,
        help=("Number of iterations to run emcee for, including burn-in and "
              "post-burn iterations."))

    parser.add_argument(
        '--smooth-times',
        '-S',
        dest='smooth_times',
        type=int,
        const=0,
        default=-1,
        nargs='?',
        action='store',
        help=("Add this many more fictitious observations between the first "
              "and last observed times. Setting this value to `0` will "
              "guarantee that all observed bands/instrument/system "
              "combinations have a point at all observed epochs."))

    parser.add_argument(
        '--extrapolate-time',
        '-E',
        dest='extrapolate_time',
        type=float,
        default=0.0,
        nargs='*',
        help=(
            "Extend model light curves this many days before/after "
            "first/last observation. Can be a list of two elements, in which "
            "case the first element is the amount of time before the first "
            "observation to extrapolate, and the second element is the amount "
            "of time before the last observation to extrapolate. Value is set "
            "to `0.0` days if option not set, `100.0` days "
            "by default if no arguments are given."))

    parser.add_argument(
        '--limit-fitting-mjds',
        '-L',
        dest='limit_fitting_mjds',
        type=float,
        default=False,
        nargs=2,
        help=(
          "Only include observations with MJDs within the specified range, "
          "e.g. `-L 54123 54234` will exclude observations outside this "
          "range. If specified without an argument, any upper limit "
          "observations before the last upper limit before the first "
          "detection in a given band will not be included in the fitting."))

    parser.add_argument(
        '--suffix',
        '-s',
        dest='suffix',
        default='',
        help=("Append custom string to output file name to prevent overwrite"))

    parser.add_argument(
        '--num-walkers',
        '-N',
        dest='num_walkers',
        type=int,
        default=50,
        help=("Number of walkers to use in emcee, must be at least twice the "
              "total number of free parameters within the model."))

    parser.add_argument(
        '--num-temps',
        '-T',
        dest='num_temps',
        type=int,
        default=2,
        help=("Number of temperatures to use in the parallel-tempered emcee "
              "sampler. `-T 1` is equivalent to the standard "
              "EnsembleSampler."))

    parser.add_argument(
        '--no-fracking',
        dest='fracking',
        default=True,
        action='store_false',
        help=("Setting this flag will skip the `fracking` step of the "
              "optimization process."))

    parser.add_argument(
        '--quiet',
        dest='quiet',
        default=False,
        action='store_true',
        help=("Print minimal output upon execution. Don't display our "
              "amazing logo :-("))

    parser.add_argument(
        '--no-copy-at-launch',
        dest='copy',
        default=True,
        action='store_false',
        help=("Setting this flag will prevent MOSFiT from copying the user "
              "file hierarchy (models/modules/jupyter) to the current working "
              "directory before fitting."))

    parser.add_argument(
        '--force-copy-at-launch',
        dest='force_copy',
        default=False,
        action='store_true',
        help=("Setting this flag will force MOSFiT to overwrite the user "
              "file hierarchy (models/modules/jupyter) to the current working "
              "directory. User will be prompted before being allowed to run "
              "with this flag."))

    parser.add_argument(
        '--frack-step',
        '-f',
        dest='frack_step',
        type=int,
        default=20,
        help=("Perform `fracking` every this number of steps while in the "
              "burn-in phase of the fitting process."))

    parser.add_argument(
        '--post-burn',
        '-p',
        dest='post_burn',
        type=int,
        default=500,
        help=("Run emcee this many more iterations after the burn-in phase. "
              "The burn-in phase will thus be run for (i - p) iterations, "
              "where i is the total number of iterations set with `-i` and "
              "p is the value of this parameter."))

    parser.add_argument(
        '--travis',
        dest='travis',
        default=False,
        action='store_true',
        help=("Alters the printing of output messages such that a new line is "
              "generated with each message. Users are unlikely to need this "
              "parameter; it is included as Travis requires new lines to be "
              "produed to detected program output."))

    args = parser.parse_args()

    if (isinstance(args.extrapolate_time, list) and
            len(args.extrapolate_time) == 0):
        args.extrapolate_time = 100.0

    if len(args.band_list) and args.smooth_times == -1:
        print_wrapped('Enabling -S as extra bands were defined.')
        args.smooth_times = 0

    changed_iterations = False
    if args.iterations == -1:
        if len(args.events) == 1 and args.events[0] == '':
            changed_iterations = True
            args.iterations = 0
        else:
            args.iterations = 1000

    width = 100
    if is_master():
        # Print our amazing ASCII logo.
        if not args.quiet:
            with open(os.path.join(dir_path, 'logo.txt'), 'r') as f:
                logo = f.read()
                width = len(logo.split('\n')[0])
                aligns = '{:^' + str(width) + '}'
                print(logo)
            print((aligns + '\n').format('### MOSFiT -- version {} ###'.format(
                __version__)))
            print(aligns.format('Authored by James Guillochon & Matt Nicholl'))
            print(aligns.format('Released under the MIT license'))
            print((aligns + '\n').format(
                'https://github.com/guillochon/MOSFiT'))

        if changed_iterations:
            print("No events specified, setting iterations to 0.")

        # Create the user directory structure, if it doesn't already exist.
        if args.copy:
            print_wrapped(
                'Copying MOSFiT folder hierarchy to current working directory '
                '(disable with --no-copy-at-launch).', wrap_length=width)
            fc = False
            if args.force_copy:
                fc = prompt(
                    "The flag `--force-copy-at-launch` has been set. Do you "
                    "really wish to overwrite your local model/module/jupyter "
                    "file hierarchy? This action cannot be reversed.", width)
            if not os.path.exists('jupyter'):
                os.mkdir(os.path.join('jupyter'))
            if not os.path.isfile(os.path.join('jupyter',
                                               'mosfit.ipynb')) or fc:
                shutil.copy(
                    os.path.join(dir_path, 'jupyter', 'mosfit.ipynb'),
                    os.path.join(os.getcwd(), 'jupyter', 'mosfit.ipynb'))

            # Disabled for now as external modules don't work with MPI.
            # if not os.path.exists('modules'):
            #     os.mkdir(os.path.join('modules'))
            # module_dirs = next(os.walk(os.path.join(dir_path, 'modules')))[1]
            # for mdir in module_dirs:
            #     if mdir.startswith('__'):
            #         continue
            #     mdir_path = os.path.join('modules', mdir)
            #     if not os.path.exists(mdir_path):
            #         os.mkdir(mdir_path)

            if not os.path.exists('models'):
                os.mkdir(os.path.join('models'))
            model_dirs = next(os.walk(os.path.join(dir_path, 'models')))[1]
            for mdir in model_dirs:
                if mdir.startswith('__'):
                    continue
                mdir_path = os.path.join('models', mdir)
                if not os.path.exists(mdir_path):
                    os.mkdir(mdir_path)
                model_files = next(
                    os.walk(os.path.join(dir_path, 'models', mdir)))[2]
                for mfil in model_files:
                    fil_path = os.path.join(os.getcwd(), 'models', mdir, mfil)
                    if os.path.isfile(fil_path) and not fc:
                        continue
                    shutil.copy(
                        os.path.join(dir_path, 'models', mdir, mfil),
                        os.path.join(fil_path))

    # Then, fit the listed events with the listed models.
    fitargs = {
        'events': args.events,
        'models': args.models,
        'plot_points': args.plot_points,
        'max_time': args.max_time,
        'band_list': args.band_list,
        'band_systems': args.band_systems,
        'band_instruments': args.band_instruments,
        'band_bandsets': args.band_bandsets,
        'iterations': args.iterations,
        'num_walkers': args.num_walkers,
        'num_temps': args.num_temps,
        'parameter_paths': args.parameter_paths,
        'fracking': args.fracking,
        'frack_step': args.frack_step,
        'wrap_length': width,
        'travis': args.travis,
        'post_burn': args.post_burn,
        'smooth_times': args.smooth_times,
        'extrapolate_time': args.extrapolate_time,
        'limit_fitting_mjds': args.limit_fitting_mjds,
        'exclude_bands': args.exclude_bands,
        'exclude_instruments': args.exclude_instruments,
        'suffix': args.suffix
    }
    Fitter().fit_events(**fitargs)


if __name__ == "__main__":
    main()
