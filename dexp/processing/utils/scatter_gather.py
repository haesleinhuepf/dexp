from typing import Tuple, Union

import numpy

from dexp.processing.backends.backend import Backend
from dexp.processing.utils.nd_slice import nd_split_slices, remove_margin_slice


def scatter_gather(backend: Backend,
                   function,
                   image,
                   chunks: Union[int, Tuple[int, ...]],
                   margins: Union[int, Tuple[int, ...]] = None,
                   to_numpy: bool = True,
                   internal_dtype=None):
    """
    'Scatters' computation of a given unary function by splitting the input array into chunks, computing using a given backend,
    and reassembling the chunks into a single array that is backed by the same backend than that of the input image.

    Parameters
    ----------
    backend : Backend to use for computation
    function : unary function
    image : imnput image
    chunks : chunks to cut input image into, can be a single integer or a tuple of integers.
    margins : margins to add to each chunk, can be a single integer or a tuple of integers.
    to_numpy : should the result be a numpy array?
    internal_dtype : internal dtype for computation

    Returns
    -------
    Result of applying the unary function to the input image, if to_numpy==True then the image is

    """
    if internal_dtype is None:
        internal_dtype = image.dtype

    if type(chunks) == int:
        chunks = (chunks,) * image.ndim

    if type(margins) == int:
        margins = (margins,) * image.ndim

    if to_numpy:
        result = numpy.empty_like(image)
    else:
        result = backend.get_xp_module(image).empty_like(image)

    # image shape:
    shape = image.shape

    # We compute the slices objects to cut the input and target images into batches:
    chunk_slices = list(nd_split_slices(shape, chunks=chunks, margins=margins))
    chunk_slices_no_margins = list(nd_split_slices(shape, chunks=chunks))

    # Zipping together slices with and without margins:
    slices = zip(chunk_slices, chunk_slices_no_margins)

    # Number of tiles:
    number_of_tiles = len(chunk_slices)

    if number_of_tiles == 1:
        # If there is only one tile, let's not be complicated about it:
        return function(image)
    else:
        counter = 1
        for chunk_slice, chunk_slice_no_margins in slices:
            image_chunk = image[chunk_slice]
            image_chunk = backend.to_backend(image_chunk, dtype=internal_dtype)
            image_chunk = function(image_chunk)
            if to_numpy:
                image_chunk = backend.to_numpy(image_chunk, dtype=image.dtype)
            else:
                image_chunk = backend.to_backend(image_chunk, dtype=image.dtype)

            remove_margin_slice_tuple = remove_margin_slice(
                shape, chunk_slice, chunk_slice_no_margins
            )
            image_chunk = image_chunk[remove_margin_slice_tuple]

            result[chunk_slice_no_margins] = image_chunk

    return result

# def scatter_gather_dask(backend: Backend,
#                         function,
#                         image,
#                         chunks,
#                         margins=None):
#     boundary=None
#     trim=True
#     align_arrays=True
#
#     image_d = from_array(image, chunks=chunks, asarray=False)
#
#     def function_numpy(_image):
#         print(_image.shape)
#         return backend.to_numpy(function(_image))
#
#     #func, *args, depth=None, boundary=None, trim=True, align_arrays=True, **kwargs
#     computation= map_overlap(function_numpy,
#                 image_d,
#                 depth=margins,
#                 boundary=boundary,
#                 trim=trim,
#                 align_arrays=align_arrays,
#                 dtype=image.dtype
#                 )
#
#     #computation.visualize(filename='transpose.png')
#     result = computation.compute()
#
#     return result