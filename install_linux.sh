# Run this to create a new env:
#conda deactivate; conda env remove --name dexp; conda create -y --name dexp python=3.8; conda activate dexp; ./install_linux.sh

conda config --add channels anaconda
conda install -y -c anaconda numpy #"libblas=*=*mkl"
conda install -y -c anaconda scipy
conda install -y -c anaconda numba
conda install -y -c anaconda numcodecs
conda install -y -c anaconda scikit-image
conda install -y -c anaconda tifffile
conda install -y -c anaconda numexpr
conda install -y -c anaconda joblib
conda install -y -c anaconda pytest
conda install -y -c anaconda graphviz
conda install -y -c anaconda click
conda install -y -c anaconda dask
conda install -y -c anaconda dask-image
conda install -y -c anaconda distributed
conda install -y -c anaconda zarr

source /apps/GCC-6.5.0/setup.GCC-6.5.0
pip install cupy-cuda111==9.0.0b2 --no-cache-dir

pip install --upgrade pip
pip install napari[all] --upgrade
pip install cachey --upgrade
pip install spimagine --upgrade
pip install gputil gpustat --upgrade
pip install arbol colorama ansicolors --upgrade
pip install simple-zarr-server requests aiohttp --upgrade
pip install colorcet --upgrade
pip install python-telegram-bot --upgrade
pip install PyYAML --upgrade

sudo apt install libcairo2-dev pkg-config python3-dev
pip install pycairo==1.11.1

pip install -e .
