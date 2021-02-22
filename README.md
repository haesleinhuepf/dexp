## DEXP

Dataset Exploration and Processing Tool

DEXP let's you view both ClearControl and Zarr formats, and copy (convert) from ClearControl format to Zarr. You can select channels and slice which lets you crop arbitrarily in time and space. You can also query information for both
formats.

DEXP ZARR storage supports both directory and zip storage and different compression codecs. Expect a typicall factor 3 compression for raw data, 10x compression for deconvolved and/or denoised data, and up to 90x compression for sparse
expression. Substracting the backgroundlight level (~ around 100 for sCMOS cameras) brings compression from typically 3X on raw data to almost 10x.

DEXP currently supports fusion, registration, deconvolution, isonet, vieweing with napari, volumetric rendering, video compositing (merging channels), video export to mp4, export to tiff.

DEXP should be run ideally on very fast machines very close to the storage.

# Prerequisites:

Install Anaconda:
https://www.anaconda.com/distribution/

On windows, make sure to insatll CUDA 10.2 (exactly that version for the current version of dexp)

# Installation:

## Prerequisites:

### Install CUDA and other libraries
The following instructions are for Ubuntu 20.04 (recomended!)

### Remove all existing CUDA and NVIDIA packages:
```
sudo apt-get purge nvidia*
sudo apt-get autoremove
sudo apt-get autoclean
sudo rm -rf /usr/local/cuda*
```

### Install CUDA 11.2:
It is recomeneded to install the most recent packages that are still compatible with CUPY and its dependencies.
As of Feb 2021, this is a good choice:
```
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt-get update
sudo apt-get -y install cuda
```

### Install cutensor:
```
sudo add-apt-repository "deb http://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo apt update 
sudo apt -y install libcutensor1 libcutensor-dev libcutensor-doc
```

### Install nccl:
```
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt-get update
sudo apt install libnccl2=2.8.4-1+cuda11.2 libnccl-dev=2.8.4-1+cuda11.2
```

### Install cudnn:
```
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin 
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt-get update
sudo apt-get install libcudnn8=8.1.0.77-1+cuda11.2
```

### Install cub:
Nothing to do...


## Another way to install CUDA and other libraries:

If you want to target CUDA 11.2:
```
conda install -c conda-forge cudatoolkit=11.2
conda install -c conda-forge cudnn
conda install -c conda-forge cutensor
```

If you want to target CUDA 11.1:
```
conda install -c conda-forge cudatoolkit=11.1
conda install -c conda-forge cudnn
conda install -c conda-forge cutensor
```


## Important: tell CUPY to use cub and cutensor:

To benefit from the cub and cutensor libraries, set this env variable:
```
CUPY_ACCELERATORS=cub,cutensor
```
This can be done by opening the file: `/etc/environment`,
and adding the line:
```
CUPY_ACCELERATORS="cub,cutensor"
```

### Build/Install CUPY:

It is recomended to install cupy using the available wheels, 
if the correct wheels package for the given CUDA version and CUPY version are available:
```
pip install cupy-cuda111==9.0.0b2
```
Note: currently only `cupy-cuda111` is available, installing drivers for 11.2 is fine,
but you also want to also add the 11.1 toolkit. A lightweight approach is to simply use conda:
```
conda install -c conda-forge cudatoolkit=11.1
```
Once cupy fully supports 11.1 this won't be nescessary.

Another approach, which takes time and fails often is to build from source:
```
pip install -U setuptools pip
pip install cupy --no-cache-dir -vvvv
```

## DEXP setup:

### Clone dexp:

```
git clone https://github.com/royerlab/dexp.git
```

### Create conda environment:

```
conda create --name dexp python=3.8 
```

### Activate environment:

```
conda activate dexp
```

### Install dexp:

```
cd dexp
pip install -e .
```

# Usage:

Always make sure that you are in the correct environment:

```
source activate dexp
```

## DEXP commands:
There is currently 16 dexp commands:

```
Usage: dexp [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  add
  check
  copy
  deconv
  deskew
  fuse
  info
  isonet
  serve
  speedtest
  stabilize
  tiff
  view
```

Sytorage info & manipulation commands:
info check copy add 

Lightsheet data processing commands:
deskew fuse deconv stabilize isonet

Network commands:
serve

Video rendering commands:
render blend stack mp4

Export commnads:
tiff

Viewing commands (opens napari):
view

Miscellaneous:
speedtest



### info:

Collects information about a given dataset:

```
Usage: dexp info [OPTIONS] [INPUT_PATHS]...

Options:
  --help  Show this message and exit.
```

### check:

Checks the integrity of a dataset:
```
sage: dexp check [OPTIONS] [INPUT_PATHS]...

Options:
  -c, --channels TEXT  List of channels, all channels when ommited.
  --help               Show this message and exit.
```

### view:

Views a dataset with napari

```
Usage: dexp view [OPTIONS] INPUT_PATH

  Opens dataset for viewing using napari.

Options:
  -c, --channels TEXT  list of channels, all channels when ommited.
  -s, --slice TEXT     dataset slice (TZYX), e.g. [0:5] (first five stacks)
                       [:,0:100] (cropping in z).
  -v, --volume         to view with volume rendering (3D ray casting)
  --help               Show this message and exit.
```

### copy:

Copies a dataset from one file/folder to another file/folder. The destination is _always_ in ZARR format (dir ort zip). Prefer 'zip' for fully processed datasets (<200GB) to be able to convenienytly copy a single file instead of a gazillion
files.

```
Usage: dexp copy [OPTIONS] [INPUT_PATHS]...

Options:
  -o, --output_path TEXT
  -c, --channels TEXT          List of channels, all channels when ommited.
  -s, --slicing TEXT           Dataset slice (TZYX), e.g. [0:5] (first five
                               stacks) [:,0:100] (cropping in z)

  -st, --store TEXT            Zarr store: ‘dir’, ‘ndir’, or ‘zip’  [default:
                               dir]

  -z, --codec TEXT             Compression codec: zstd for ’, ‘blosclz’,
                               ‘lz4’, ‘lz4hc’, ‘zlib’ or ‘snappy’   [default:
                               zstd]

  -l, --clevel INTEGER         Compression level  [default: 3]
  -w, --overwrite              Forces overwrite of target  [default: False]
  -wk, --workers INTEGER       Number of worker threads to spawn.  [default:
                               -1]

  -wkb, --workersbackend TEXT  What backend to spawn workers with, can be
                               ‘loky’ (multi-process) or ‘threading’ (multi-
                               thread)   [default: threading]

  -ck, --check TEXT            Checking integrity of written file.  [default:
                               True]

  --help                       Show this message and exit.

```

### add:

Adds a channel from one dataset to another (possibly not yet existant) ZARR file/folder. Channels can be renamed as they are copied.

```
Usage: dexp add [OPTIONS] [INPUT_PATHS]...

Options:
  -o, --output_path TEXT
  -c, --channels TEXT     List of channels, all channels when ommited.
  -rc, --rename TEXT      You can rename channels: e.g. if channels are
                          ‘channel1,anotherc’ then ‘gfp,rfp’ would rename the
                          ‘channel1’ channel to ‘gfp’, and ‘anotherc’ to ‘rfp’

  -st, --store TEXT       Zarr store: ‘dir’, ‘ndir’, or ‘zip’  [default: dir]
  -w, --overwrite         Forces overwrite of target  [default: False]
  --help                  Show this message and exit.
```

### Deskew:

```
Usage: dexp deskew [OPTIONS] [INPUT_PATHS]...

Options:
  -o, --output_path TEXT
  -c, --channels TEXT             list of channels for the view in standard
                                  order for the microscope type (C0L0, C0L1,
                                  C1L0, C1L1,...)

  -s, --slicing TEXT              dataset slice (TZYX), e.g. [0:5] (first five
                                  stacks) [:,0:100] (cropping in z)

  -st, --store TEXT               Zarr store: ‘dir’, ‘ndir’, or ‘zip’
                                  [default: dir]

  -z, --codec TEXT                compression codec: ‘zstd’, ‘blosclz’, ‘lz4’,
                                  ‘lz4hc’, ‘zlib’ or ‘snappy’

  -l, --clevel INTEGER            Compression level  [default: 3]
  -w, --overwrite                 to force overwrite of target  [default:
                                  False]

  -zl, --zerolevel INTEGER        ‘zero-level’ i.e. the pixel values in the
                                  restoration (to be substracted)  [default:
                                  110]

  -ch, --cliphigh INTEGER         Clips voxel values above the given value, if
                                  zero no clipping is done  [default: 1024]

  -dhs, --dehaze_size INTEGER     Filter size (scale) for dehazing the final
                                  regsitered and fused image to reduce effect
                                  of scattered and out-of-focus light. Set to
                                  zero to deactivate.  [default: 65]

  -ddt, --dark_denoise_threshold INTEGER
                                  Threshold for denoises the dark pixels of
                                  the image -- helps increase compression
                                  ratio. Set to zero to deactivate.  [default:
                                  0]

  -k, --workers INTEGER           Number of worker threads to spawn, if -1
                                  then num workers = num devices  [default:
                                  -1]

  -wkb, --workersbackend TEXT     What backend to spawn workers with, can be
                                  ‘loky’ (multi-process) or ‘threading’
                                  (multi-thread)   [default: threading]

  -d, --devices TEXT              Sets the CUDA devices id, e.g. 0,1,2 or
                                  ‘all’  [default: 0]

  -ck, --check TEXT               Checking integrity of written file.
                                  [default: True]

  --help                          Show this message and exit.
```


### Fusion (& registration):

Fuses and registers stacks acquired on a multi-view lightsheet microscope. Right now we have only support for SimView type lightsheet microscope with 2 detection arms and 2 illmination arms. Channels must be named:
'C0L0', 'C0L1', 'C1L0', 'C1L1'. The result has a single channel called 'fused'.

```
Usage: dexp fuse [OPTIONS] [INPUT_PATHS]...

Options:
  -o, --output_path TEXT
  -c, --channels TEXT             list of channels for the view in standard
                                  order for the microscope type (C0L0, C0L1,
                                  C1L0, C1L1,...)

  -s, --slicing TEXT              dataset slice (TZYX), e.g. [0:5] (first five
                                  stacks) [:,0:100] (cropping in z)

  -st, --store TEXT               Zarr store: ‘dir’, ‘ndir’, or ‘zip’
                                  [default: dir]

  -z, --codec TEXT                compression codec: ‘zstd’, ‘blosclz’, ‘lz4’,
                                  ‘lz4hc’, ‘zlib’ or ‘snappy’

  -l, --clevel INTEGER            Compression level  [default: 3]
  -w, --overwrite                 to force overwrite of target  [default:
                                  False]

  -m, --microscope TEXT           Microscope objective to use for computing
                                  psf, can be: simview or mvsols  [default:
                                  simview]

  -eq, --equalise / -neq, --no-equalise
                                  Equalise intensity of views before fusion,
                                  or not.  [default: True]

  -eqm, --equalisemode TEXT       Equalisation modes: compute correction
                                  ratios only for first time point: ‘first’ or
                                  for all time points: ‘all’.  [default:
                                  first]

  -zl, --zerolevel INTEGER        ‘zero-level’ i.e. the pixel values in the
                                  restoration (to be substracted)  [default:
                                  110]

  -ch, --cliphigh INTEGER         Clips voxel values above the given value, if
                                  zero no clipping is done  [default: 1024]

  -f, --fusion TEXT               Fusion mode, can be: ‘tg’ or ‘dct’.
                                  [default: tg]

  -fbs, --fusion_bias_strength <FLOAT FLOAT>...
                                  Fusion bias strength for illumination and
                                  detection ‘fbs_i fbs_d’, set to ‘0 0’) if
                                  fusing a cropped region  [default: 0.5,
                                  0.02]

  -dhs, --dehaze_size INTEGER     Filter size (scale) for dehazing the final
                                  regsitered and fused image to reduce effect
                                  of scattered and out-of-focus light. Set to
                                  zero to deactivate.  [default: 65]

  -ddt, --dark_denoise_threshold INTEGER
                                  Threshold for denoises the dark pixels of
                                  the image -- helps increase compression
                                  ratio. Set to zero to deactivate.  [default:
                                  0]

  -zpa, --zpadapodise <INTEGER INTEGER>...
                                  Pads and apodises the views along z before
                                  fusion: ‘pad apo’, where pad is a padding
                                  length, and apo is apodisation length, both
                                  in voxels. If pad=apo, no original voxel is
                                  modified and only added voxels are apodised.
                                  [default: 8, 96]

  -lr, --loadreg                  Turn on to load the registration parameters
                                  from a previous run  [default: False]

  -wri, --warpregiter INTEGER     Number of iterations for warp registration
                                  (if applicable).  [default: 4]

  -mc, --minconfidence FLOAT      Minimal confidence for registration
                                  parameters, if below that level the
                                  registration parameters for previous time
                                  points is used.  [default: 0.3]

  -md, --maxchange FLOAT          Maximal change in registration parameters,
                                  if above that level the registration
                                  parameters for previous time points is used.
                                  [default: 16]

  -hd, --hugedataset              Use this flag to indicate that the the
                                  dataset is _huge_ and that memory allocation
                                  should be optimised at the detriment of
                                  processing speed.  [default: False]

  -k, --workers INTEGER           Number of worker threads to spawn, if -1
                                  then num workers = num devices  [default:
                                  -1]

  -wkb, --workersbackend TEXT     What backend to spawn workers with, can be
                                  ‘loky’ (multi-process) or ‘threading’
                                  (multi-thread)   [default: threading]

  -d, --devices TEXT              Sets the CUDA devices id, e.g. 0,1,2 or
                                  ‘all’  [default: 0]

  -ck, --check TEXT               Checking integrity of written file.
                                  [default: True]

  --help                          Show this message and exit.

```

### Deconvolution:

Deconvolves stacks using a simulated PSF. Right now we only support the optics of our SimVew type light sheet (0.8 NA objectives wth custom magnfication.)

```
Usage: dexp deconv [OPTIONS] [INPUT_PATHS]...

Options:
  -o, --output_path TEXT
  -c, --channels TEXT           list of channels, all channels when ommited.
  -s, --slicing TEXT            dataset slice (TZYX), e.g. [0:5] (first five
                                stacks) [:,0:100] (cropping in z)

  -st, --store TEXT             Zarr store: ‘dir’, ‘ndir’, or ‘zip’  [default:
                                dir]

  -z, --codec TEXT              compression codec: ‘zstd’, ‘blosclz’, ‘lz4’,
                                ‘lz4hc’, ‘zlib’ or ‘snappy’   [default: zstd]

  -l, --clevel INTEGER          Compression level  [default: 3]
  -w, --overwrite               to force overwrite of target  [default: False]
  -cs, --chunksize INTEGER      Chunk size for tiled computation  [default:
                                512]

  -m, --method TEXT             Deconvolution method: for now only lr (Lucy
                                Richardson)  [default: lr]

  -i, --iterations INTEGER      Number of deconvolution iterations. More
                                iterations takes longer, will be sharper, but
                                might also be potentially more noisy depending
                                on method. The default number of iterations
                                depends on the other parameters, in particular
                                it depends on the choice of backprojection
                                operator. For ‘wb’ as little as 3 iterations
                                suffice.

  -mc, --maxcorrection INTEGER  Max correction in folds per iteration. By
                                default there is no limit

  -pw, --power FLOAT            Correction exponent, default for standard LR
                                is 1, set to >1 for acceleration.  [default:
                                1.0]

  -bs, --blindspot INTEGER      Blindspot based noise reduction. Provide size
                                of kernel to use, must be an odd number:
                                3(recommended), 5, 7. 0 means no blindspot.
                                [default: 0]

  -bp, --backprojection TEXT    Back projection operator, can be: ‘tpsf’
                                (transposed PSF = classic) or ‘wb’ (Wiener-
                                Butterworth =  accelerated)   [default: tpsf]

  -obj, --objective TEXT        Microscope objective to use for computing psf,
                                can be: nikon16x08na or olympus20x10na
                                [default: nikon16x08na]

  -dxy, --dxy FLOAT             Voxel size along x and y in microns  [default:
                                0.485]

  -dz, --dz FLOAT               Voxel size along z in microns  [default: 1.94]
  -sxy, --xysize INTEGER        PSF size along xy in voxels  [default: 31]
  -sz, --zsize INTEGER          PSF size along z in voxels  [default: 31]
  -d, --downscalexy2 TEXT       Downscales along x and y for faster
                                deconvolution (but worse quality of course)

  -k, --workers INTEGER         Number of worker threads to spawn, if -1 then
                                num workers = num devices  [default: -1]

  -wkb, --workersbackend TEXT   What backend to spawn workers with, can be
                                ‘loky’ (multi-process) or ‘threading’ (multi-
                                thread)   [default: threading]

  -d, --devices TEXT            Sets the CUDA devices id, e.g. 0,1,2 or ‘all’
                                [default: 0]

  -ck, --check TEXT             Checking integrity of written file.  [default:
                                True]

  --help                        Show this message and exit.
```

### Isonet:

Provides support for Isonet deep learning based axial deconvolution:
https://arxiv.org/abs/1704.01510

```
Usage: dexp isonet [OPTIONS] [INPUT_PATHS]...

Options:
  -o, --output_path TEXT
  -s, --slicing TEXT        dataset slice (TZYX), e.g. [0:5] (first five
                            stacks) [:,0:100] (cropping in z)

  -st, --store TEXT         Zarr store: ‘dir’, ‘ndir’, or ‘zip’  [default:
                            dir]

  -z, --codec TEXT          compression codec: ‘zstd’, ‘blosclz’, ‘lz4’,
                            ‘lz4hc’, ‘zlib’ or ‘snappy’   [default: zstd]

  -l, --clevel INTEGER      Compression level  [default: 3]
  -w, --overwrite           to force overwrite of target  [default: False]
  -c, --context TEXT        IsoNet context name  [default: default]
  -m, --mode TEXT           mode: 'pta' -> prepare, train and apply, 'a' just
                            apply    [default: pta]

  -e, --max_epochs INTEGER  to force overwrite of target  [default: 50]
  -ck, --check TEXT         Checking integrity of written file.  [default:
                            True]

  --help                    Show this message and exit.

```


## Video commands

DEXP has a series of video commands that let you render datasets and compose complex videos:
```
Usage: video [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  blend
  mp4
  projrender
  stack
  volrender
```


### Volume rendering:

Simple but effective volume rendering. By default should produce nice rotating views, but lots of parameters can be configured!
This command produces video frames as individual PNG files in a subfolder (frames). To make a movie, blend channels together, or stich panels together, use the blend, stack and mp4 commands.

```
Usage: dexp render [OPTIONS] INPUT_PATH

Options:
  -o, --output_path TEXT     Output folder to store rendered PNGs. Default is:
                             frames_<channel_name>

  -c, --channels TEXT        list of channels to render, all channels when
                             ommited.

  -s, --slicing TEXT         dataset slice (TZYX), e.g. [0:5] (first five
                             stacks) [:,0:100] (cropping in z).

  -w, --overwrite            to force overwrite of target  [default: False]
  -a, --aspect FLOAT         sets aspect ratio e.g. 4  [default: 4]
  -cm, --colormap TEXT       sets colormap, e.g. viridis, gray, magma, plasma,
                             inferno   [default: magma]

  -rs, --rendersize INTEGER  Sets the frame render size. i.e. -ws 400 sets the
                             window to 400x400  [default: 2048]

  -cl, --clim TEXT           Sets the contrast limits, i.e. -cl 0,1000 sets
                             the contrast limits to [0,1000]

  -opt, --options TEXT       Render options, e.g: 'gamma=1.2,box=True'.
                             Important: no white spaces!!! Complete list with
                             defaults will be displayed on first run

  --help                     Show this message and exit.

```

### Video compositing:

Takes frames and blend them together. Typically used for merging channels, but can also be used to add text -- if you provide a folder with a single PNG image of correct dimensions

```
Usage: dexp blend [OPTIONS] [INPUT_PATHS]...

Options:
  -o, --output_path TEXT  Output folder for blended frames.
  -b, --blending TEXT     Blending mode: max, add, addclip, adderf (add stands
                          for addclip).  [default: max]

  -w, --overwrite         to force overwrite of target  [default: False]
  -k, --workers INTEGER   Number of worker threads to spawn, set to -1 for
                          maximum number of workers  [default: -1]

  --help                  Show this message and exit.

```

### Video stacking:

In addition to blending frames you can also stack frames horyzontally or vertically to make multi-panel videos. Again, here we just manipulate folders of PNG files.

```
Usage: dexp stack [OPTIONS] [INPUT_PATHS]...

Options:
  -o, --output_path TEXT  Output folder for blended frames.
  -r, --orientation TEXT  Stitching mode: horiz, vert  [default: horiz]
  -w, --overwrite         to force overwrite of target  [default: False]
  -k, --workers INTEGER   Number of worker threads to spawn, set to -1 for
                          maximum number of workers  [default: -1]

  --help                  Show this message and exit.

```

### Conversion from frame sequences to mp4 file:

Takes a folder of PNG files and makes it into a MP4 file.

```
Usage: dexp mp4 [OPTIONS] INPUT_PATH

Options:
  -o, --output_path TEXT     Output file path for movie
  -fps, --framerate INTEGER  Sets the framerate in frames per second
                             [default: 30]

  -w, --overwrite            to force overwrite of target  [default: False]
  --help                     Show this message and exit.

```



# Examples:

The folowing examples can be tested on existing datasets:

Gathers info on the dataset '2019-07-03-16-23-15-65-f2va.mch7' with napari:

```
dexp info 2019-07-03-16-23-15-65-f2va.mch7
```

Copies a z-max-projection for the first 10n timepoints (-s [0:10]) from scope acquisition '2019-07-03-16-23-15-65-f2va.mch7' to Zarr folder '~/Downloads/local.zarr', and overwrites whatever is there (-w).

```
dexp copy -w -p 1 -s '[0:10]' 2019-07-03-16-23-15-65-f2va.mch7 -o ~/Downloads/local.zarr
```

Views the first 100 times points '2019-07-03-16-23-15-65-f2va.mch7' with napari:

```
dexp view -s '[0:100]' 2019-07-03-16-23-15-65-f2va.mch7
```

# Technical notes:

- You can pass arguments in any order for bash but not for all shells, i.e. zsh.
- You can pass string arguments as non string in bash but not in all shells.

# Pro Tips

## redirect to file and to standard output:

You can send the output to a log file and still be able to see the output by using the following postfix:

```
2>&1 | tee logfile.txt
```

Example:

```
dexp ... dexp parameters ... 2>&1 | tee logfile.txt
```

## use tmux to keep track of long runing jobs

Why tmux? When you connect via network adn SSH, you can start a process on a remote machine, but it often occurs that closing the terminal or loosing the network connection will kill the running process. Even if one figures out how to keep
the processs running, you rarely can see again the log outputs - unless you have explictely redirected to a file. tmux greatly simplifies all this by providing persistent terminal sessions.

First make sure that tmux is instaled on your system:

```
sudo apt-get install tmux
```

Connect to your machine using, for example, ssh:

```
ssh username@machine
```

Create the session in which you want to run your long-running process:

```
tmux new -s dexp
```

Once in your session you can activate the dexp environment, and start dexp, etc...

Important: You can leave a session by pressing the keys: CTRL+B then D

To come back to a session, you reattach:

```
tmux attach -t dexp
```

Once a session is created, it will remain active until you close it, no need to create it again (unless you have closed it!). You can disconnect your SSH session, loose network connection, close your computer, and still be able to reconnect
to your session and have everything as if you had kept everything open.

In doubt, you can list all active sessions:

```
tmux ls
```

To close a session:
First kill, if needed, the running process within the session by pressing CTRL+C or/and CTRL+Z, and then, simply type the command exit in the termnal within the session.

Note: you might encounter problems in tmux with text coloring. A solution is to change the default xterm setting:

First, generate a default configuration file for tmux:

```
tmux show -g | cat > ~/.tmux.conf
```

Add the following line at the end of that file (~/.tmux.conf):

```
set -g default-terminal "screen-256color"
```




  
 




  
  






