import re
from fnmatch import fnmatch
from os import listdir, cpu_count
from os.path import join

import numcodecs
import numpy
from cachey import Cache
from dask import array, delayed
from numcodecs.blosc import Blosc
from numpy import uint16, frombuffer
from zarr import open_group

from dexp.datasets.base_dataset import BaseDataset

numcodecs.blosc.use_threads = True
numcodecs.blosc.set_nthreads(cpu_count() // 2)


class CCDataset(BaseDataset):

    def __init__(self, folder, cache_size=8e9):

        self.folder = folder
        self._channels = []
        self._index_files = {}

        all_files = list(listdir(folder))
        # print(all_files)

        for file in all_files:
            if fnmatch(file, '*.index.txt'):
                if not file.startswith('._'):
                    channel = file.replace('.index.txt', '')
                    self._channels.append(channel)
                    self._index_files[channel] = join(folder, file)

        # print(self._channels)
        #print(self._index_files)

        self._nb_time_points = {}
        self._times_sec = {}
        self._shapes = {}
        self._time_points = {}

        for channel in self._channels:
            self._parse_channel(channel)

        self.cache = Cache(cache_size)  # Leverage two gigabytes of memory

    def channels(self):
        return list(self._channels)

    def shape(self, channel, time_point=0):
        if (channel, time_point) in self._shapes:
            return self._shapes[(channel, time_point)]
        else:
            return ()

    def info(self, channel=None):
        if channel:
            info_str = f"Channel: '{channel}', nb time points: {self.nb_timepoints(channel)}, shape: {self.shape(channel)} "
            return info_str
        else:
            info_str = f"CC dataset at: {self.folder}"
            info_str += "\n\n"
            info_str += "Channels: \n"
            for channel in self.channels():
                info_str += "  └──" + self.info(channel) + "\n"

            return info_str

    def nb_timepoints(self, channel):
        return self._nb_time_points[channel]

    def get_stacks(self, channel, per_z_slice=True):

        if False:

            # For some reason this is slower, should have been faster!:

            # Construct a small Dask array for every lazy value:
            arrays = [self.get_stack(channel, time_point, per_z_slice) for time_point in self._time_points[channel]]

            stacked_array = array.stack(arrays, axis=0)  # Stack all small Dask arrays into one

            return stacked_array

        else:
            # Lazy and memorized version of get_stack:
            lazy_get_stack = delayed(self.cache.memoize(self.get_stack), pure=True)

            # Lazily load each stack for each time point:
            lazy_stacks = [lazy_get_stack(channel, time_point, per_z_slice) for time_point in self._time_points[channel]]

            # Construct a small Dask array for every lazy value:
            arrays = [array.from_delayed(lazy_stack,
                                         dtype=uint16,
                                         shape=self._shapes[(channel, 0)])
                      for lazy_stack in lazy_stacks]

            stacked_array = array.stack(arrays, axis=0)  # Stack all small Dask arrays into one

            return stacked_array

    def get_stack(self, channel, time_point, per_z_slice=True):

        file_name = self._get_stack_file_name(channel, time_point)
        shape = self._shapes[(channel, time_point)]

        if per_z_slice:

            lazy_get_slice_array_for_stack_file_and_z = delayed(self.cache.memoize(self._get_slice_array_for_stack_file_and_z), pure=True)

            # Lazily load each stack for each time point:
            lazy_stacks = [lazy_get_slice_array_for_stack_file_and_z(file_name, shape, z) for z in range(0, shape[0])]

            arrays = [array.from_delayed(lazy_stack,
                                         dtype=uint16,
                                         shape=shape[1:])
                      for lazy_stack in lazy_stacks]

            stack = array.stack(arrays, axis=0)

        else:
            stack = self._get_array_for_stack_file(file_name, shape=shape)

        return stack



    def _parse_channel(self, channel):

        index_file = self._index_files[channel]

        with open(index_file) as f:
            lines = f.readlines()

        lines = [line.strip() for line in lines]

        lines = [re.split(r'\t+', line) for line in lines]

        self._time_points[channel] = []

        for line in lines:
            time_point = int(line[0])
            time_sec = float(line[1])
            shape = eval('(' + line[2] + ')')[::-1]

            self._times_sec[(channel, time_point)] = time_sec
            self._shapes[(channel, time_point)] = shape

            self._time_points[channel].append(time_point)

        self._nb_time_points[channel] = len(self._time_points[channel])

    def _get_stack_file_name(self, channel, time_point):

        return join(self.folder, 'stacks', channel, str(time_point).zfill(6) + '.raw')

    def _get_array_for_stack_file(self, file_name, shape=None):

        try:
            with open(file_name, 'rb') as my_file:
                print(f"Accessing file: {file_name}")
                buffer = my_file.read()

                dt = numpy.dtype(uint16)
                dt = dt.newbyteorder('L')

                array = frombuffer(buffer, dtype=dt)

            if not shape is None:
                array = array.reshape(shape)

            return array

        except FileNotFoundError:
            print(f"Could  not find file: {file_name} for array of shape: {shape}")
            return numpy.zeros(shape, dtype=uint16)

    def _get_slice_array_for_stack_file_and_z(self, file_name, shape, z):

        try:
            with open(file_name, 'rb') as file:
                print(f"Accessing file: {file_name} at z={z}")

                length = shape[1] * shape[2] * numpy.dtype(uint16).itemsize
                offset = z * length

                file.seek(offset)

                buffer = file.read(length)
                array = frombuffer(buffer, dtype=uint16)

                array = array.reshape(shape[1:])
                return array

        except FileNotFoundError:
            print(f"Could  not find file: {file_name} for array of shape: {shape} at z={z}")
            return numpy.zeros(shape[1:], dtype=uint16)
