from os import makedirs
from os.path import exists, join

import click
from PIL import Image
from arbol.arbol import aprint, asection
from joblib import delayed, Parallel

from dexp.cli.dexp_main import _default_workers_backend
from dexp.cli.utils import _parse_channels, _parse_slicing, _get_output_path, _parse_devices
from dexp.datasets.open_dataset import glob_datasets
from dexp.processing.backends.backend import Backend
from dexp.processing.backends.cupy_backend import CupyBackend
from dexp.processing.render.projection import project_image


@click.command()
@click.argument('input_paths', nargs=-1)
@click.option('--output_path', '-o', default=None, help='Output folder to store rendered PNGs. Default is: frames_<channel_name>')
@click.option('--channels', '-c', default=None, help='list of channels to render, all channels when ommited.')
@click.option('--slicing', '-s', default=None, help='dataset slice (TZYX), e.g. [0:5] (first five stacks) [:,0:100] (cropping in z).')
@click.option('--overwrite', '-w', is_flag=True, help='to force overwrite of target', show_default=True)  # , help='dataset slice'
@click.option('--axis', '-ax', type=int, default=0, help='Sets the projection axis: 0->Z, 1->Y, 2->X ', show_default=True)  # , help='dataset slice'
@click.option('--dir', '-d', type=int, default=-1, help='Sets the projection direction: -1 -> top to bottom, +1 -> bottom to top.', show_default=True)  # , help='dataset slice'
@click.option('--mode', '-m', type=str, default='colormax',
              help='Sets the projection mode: ‘max’: classic max projection, ‘colormax’: color max projection, i.e. color codes for depth, ‘maxcolor’ same as colormax but first does depth-coding by color and then max projects (acheives some level of transparency). ',
              show_default=True)
@click.option('--clim', '-cl', type=str, default=None, help='Sets the contrast limits, i.e. -cl 0,1000 sets the contrast limits to [0,1000]')
@click.option('--attenuation', '-at', type=float, default=0.1, help='Sets the projection attenuation coefficient, should be within [0, 1] ideally close to 0. Larger values mean more attenuation.',
              show_default=True)  # , help='dataset slice'
@click.option('--gamma', '-g', type=int, default=1, help='Sets the gamma coefficient pre-applied to the raw voxel values (before projection or any subsequent processing).', show_default=True)  # , help='dataset slice'
@click.option('--dlim', '-dl', type=str, default=None,
              help='Sets the depth limits. Depth limits. For example, a value of (0.1, 0.7) means that the colormap start at a normalised depth of 0.1, and ends at a normalised depth of 0.7, other values are clipped. Only used for colormax mode.',
              show_default=True)  # , help='dataset slice'
@click.option('--colormap', '-cm', type=str, default='viridis', help='sets colormap, e.g. viridis, gray, magma, plasma, inferno. Use a rainbow colormap such as bmy, turbo, or rainbow for color-coded depth modes. ', show_default=True)
@click.option('--rgbgamma', '-cg', type=float, default=1.0, help='Gamma correction applied to the resulting RGB image. Usefull to brighten image', show_default=True)
@click.option('--transparency', '-t', is_flag=True, help='Enables transparency output when possible, use only if you are sure of what you are doing.', show_default=True)
@click.option('--legendsize', '-lsi', type=float, default=1.0, help='Multiplicative factor to control size of legend. If 0, no legend is generated.', show_default=True)
@click.option('--legendscale', '-lsc', type=float, default=1.0, help='Float that gives the scale in some unit of each voxel (along the projection direction). Only in color projection modes.', show_default=True)
@click.option('--legendtitle', '-lt', type=str, default='color-coded depth (voxels)', help='Title for the color-coded depth legend.', show_default=True)
@click.option('--legendposition', '-lp', type=str, default='bottom_left', help='Position of the legend in pixels in natural order: x,y. Can also be a string: bottom_left, bottom_right, top_left, or top_right.', show_default=True)
@click.option('--legendalpha', '-la', type=float, default=1, help='Transparency for legend (1 means opaque, 0 means completely transparent)', show_default=True)
@click.option('--step', '-sp', type=int, default=1, help='Process every ‘step’ frames.', show_default=True)
@click.option('--workers', '-k', type=int, default=-1, help='Number of worker threads to spawn, if -1 then num workers = num devices', show_default=True)  #
@click.option('--workersbackend', '-wkb', type=str, default=_default_workers_backend, help='What backend to spawn workers with, can be ‘loky’ (multi-process) or ‘threading’ (multi-thread) ', show_default=True)  #
@click.option('--devices', '-d', type=str, default='0', help='Sets the CUDA devices id, e.g. 0,1,2 or ‘all’', show_default=True)  #
def projrender(input_paths,
               output_path,
               channels,
               slicing,
               overwrite,
               axis,
               dir,
               mode,
               clim,
               attenuation,
               gamma,
               dlim,
               colormap,
               rgbgamma,
               transparency,
               legendsize,
               legendscale,
               legendtitle,
               legendposition,
               legendalpha,
               step,
               workers,
               workersbackend,
               devices,
               stop_at_exception=True
               ):
    input_dataset, input_paths = glob_datasets(input_paths)
    channels = _parse_channels(input_dataset, channels)
    slicing = _parse_slicing(slicing)
    devices = _parse_devices(devices)

    output_path = _get_output_path(input_paths[0], output_path, f"_{mode}_projection")
    makedirs(output_path, exist_ok=True)

    dlim = None if dlim is None else tuple(float(strvalue) for strvalue in dlim.split(','))

    if ',' in legendposition:
        legendposition = tuple(float(strvalue) for strvalue in legendposition.split(','))

    aprint(f"Projection rendering of: {input_paths} to {output_path} for channels: {channels}, slicing: {slicing} ")

    for channel in channels:

        with asection(f"Channel '{channel}' shape: {input_dataset.shape(channel)}:"):
            aprint(input_dataset.info(channel))

        array = input_dataset.get_array(channel, wrap_with_dask=True)
        dtype = array.dtype

        if slicing:
            array = array[slicing]

        aprint(f"Rendering array of shape={array.shape} and dtype={array.dtype} for channel '{channel}'.")

        nbframes = array.shape[0]

        with asection("Rendering:"):

            def process(tp, _clim, device):
                try:
                    with asection(f"Rendering Frame     : {tp:05}"):

                        filename = join(output_path, f"frame_{tp:05}.png")

                        if overwrite or not exists(filename):

                            with asection("Loading stack..."):
                                stack = array[tp].compute()

                            with CupyBackend(device, exclusive=True, enable_unified_memory=True):
                                if _clim is not None:
                                    aprint(f"Using provided min and max for contrast limits: {_clim}")
                                    min_value, max_value = (float(strvalue) for strvalue in _clim.split(','))
                                    _clim = (min_value, max_value)

                                with asection(f"Projecting image of shape: {stack.shape} "):
                                    projection = project_image(stack,
                                                               axis=axis,
                                                               dir=dir,
                                                               mode=mode,
                                                               attenuation=attenuation,
                                                               attenuation_min_density=0.002,
                                                               attenuation_filtering=4,
                                                               gamma=gamma,
                                                               clim=_clim,
                                                               cmap=colormap,
                                                               dlim=dlim,
                                                               rgb_gamma=rgbgamma,
                                                               transparency=transparency,
                                                               legend_size=legendsize,
                                                               legend_scale=legendscale,
                                                               legend_title=legendtitle,
                                                               legend_position=legendposition,
                                                               legend_alpha=legendalpha)

                                with asection(f"Saving frame {tp} as: {filename}"):
                                    projection = Backend.to_numpy(projection)
                                    image = Image.fromarray(projection)
                                    image.save(filename)

                except Exception as error:
                    aprint(error)
                    aprint(f"Error occurred while processing time point {tp} !")
                    import traceback
                    traceback.print_exc()

                    if stop_at_exception:
                        raise error

            if workers == -1:
                workers = len(devices)
            aprint(f"Number of workers: {workers}")

            if workers > 1:
                Parallel(n_jobs=workers, backend=workersbackend)(delayed(process)(tp, clim, devices[tp % len(devices)]) for tp in range(0, nbframes, step))
            else:
                for tp in range(0, nbframes, step):
                    process(tp, clim, devices[0])

    input_dataset.close()
    aprint("Done!")
