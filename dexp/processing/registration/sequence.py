from typing import List, Sequence

import numpy
from arbol import aprint, asection
from dask.array import Array

from dexp.processing.backends.backend import Backend
from dexp.processing.backends.numpy_backend import NumpyBackend
from dexp.processing.registration.model.sequence_registration_model import SequenceRegistrationModel
from dexp.processing.registration.model.translation_registration_model import TranslationRegistrationModel
from dexp.processing.registration.translation_nd_proj import register_translation_maxproj_nd
from dexp.processing.utils.center_of_mass import center_of_mass
from dexp.processing.utils.linear_solver import linsolve


def image_stabilisation(image: 'Array',
                        axis: int = 0,
                        internal_dtype=None,
                        **kwargs
                        ) -> SequenceRegistrationModel:
    """
    Computes a sequence stabilisation model for an image sequence indexed along a specified axis.


    Parameters
    ----------
    image: image to stabilise
    axis: sequence axis along which to stabilise image
    internal_dtype : internal dtype for computation
    **kwargs: argument passthrough to the pairwise registration method.

    Returns
    -------
    Sequence registration model

    """
    xp = Backend.get_xp_module()

    image = Backend.to_backend(image, dtype=internal_dtype)

    length = image.shape[axis]
    image_sequence = list(xp.take(image, axis=axis, indices=range(0, length)))

    return image_sequence_stabilisation(image_sequence=image_sequence,
                                        internal_dtype=internal_dtype,
                                        **kwargs)


def image_sequence_stabilisation(image_sequence: Sequence['Array'],
                                 preload_images: bool = True,
                                 mode: str = 'translation',
                                 scales: Sequence[int] = None,
                                 min_confidence: float = 0.3,
                                 enable_com: bool = True,
                                 quantile: float = 0.5,
                                 bounding_box: bool = False,
                                 tolerance: float = 1e-7,
                                 order_error: float = 1.0,
                                 order_reg: float = 2.0,
                                 alpha_reg: float = 1e-1,
                                 debug_output: bool = True,
                                 internal_dtype=None,
                                 **kwargs
                                 ) -> SequenceRegistrationModel:
    """
    Computes a sequence stabilisation model for an image sequence.


    Parameters
    ----------
    image: image to stabilise
    axis: sequence axis along which to stabilise image
    mode: registration mode. For now only 'translation' is available.
    scales: Sequence of integers representing the distances between timepoints to consider for pairwise registrations.
    min_confidence: minimal confidence to accept a pairwise registration
    enable_com: enable center of mass fallback when standard registration fails.
    quantile: quantile to cut-off background in center-of-mass calculation
    bounding_box: if True, the center of mass of the bounding box of non-zero pixels is returned.
    tolerance: tolerance for linear solver.
    order_error: order for linear solver error term.
    order_reg: order for linear solver regularisation term.
    alpha_reg: multiplicative coefficient for regularisation term.
    internal_dtype : internal dtype for computation
    **kwargs: argument passthrough to the pairwise registration method.

    Returns
    -------
    Sequence registration model

    """
    xp = Backend.get_xp_module()
    sp = Backend.get_sp_module()

    image_sequence = list(image_sequence)

    if preload_images:
        with asection(f"Preloading images to backend..."):
            image_sequence = list(Backend.to_backend(image) for image in image_sequence)

    length = len(image_sequence)

    if scales is None:
        gr = 1.618033988749895
        scales = list(int(round(gr ** i)) for i in range(32) if gr ** i < length)

    aprint(f"Scales: {scales}")

    with asection(f"Registering image sequence of length: {length}"):

        ndim = image_sequence[0].ndim

        uv_set = set()
        with asection(f"Enumerating pairwise registrations needed..."):

            for scale_index, scale in enumerate(scales):
                for offset in range(0, scale):
                    for u in range(offset, length, scale):
                        v = u + scale
                        if v >= length:
                            continue
                        atuple = tuple((u, v))
                        if atuple not in uv_set:
                            # aprint(f"Pair: ({u}, {v}) added")
                            uv_set.add(atuple)
                        else:
                            aprint(f"Pair: ({u}, {v}) already considered, that's all good just info...")

        pairwise_models = []
        with asection(f"Computing pairwise registrations for {len(uv_set)} (u,v) pairs..."):
            for u, v in uv_set:
                image_u = image_sequence[u]
                image_v = image_sequence[v]
                model = _pairwise_registration(u, v,
                                               image_u, image_v,
                                               mode,
                                               min_confidence,
                                               enable_com,
                                               quantile,
                                               bounding_box,
                                               internal_dtype,
                                               **kwargs)
                pairwise_models.append(model)

        nb_models = len(pairwise_models)
        aprint(f"Number of models obtained: {nb_models} for a sequence of length:{length}")

        if debug_output:
            with asection(f"Generating debug output: 'stabilisation_confidence_matrix.pdf' "):
                import matplotlib.pyplot as plt
                import seaborn as sns
                sns.set_theme()
                plt.clf()
                plt.cla()

                array = numpy.zeros((length, length))
                for tp, model in enumerate(pairwise_models):
                    u = model.u
                    v = model.v
                    array[u, v] = model.overall_confidence()
                sns.heatmap(array)

                plt.savefig("stabilisation_confidence_matrix.pdf")

        with asection(f"Solving for optimal sequence registration"):
            with NumpyBackend():
                xp = Backend.get_xp_module()
                sp = Backend.get_sp_module()

                if mode == 'translation':

                    # prepares list of models:
                    translation_models: List[TranslationRegistrationModel] = list(TranslationRegistrationModel(xp.zeros((ndim,), dtype=internal_dtype)) for _ in range(length))

                    # initialise count for average:
                    for model in translation_models:
                        model.count = 0

                    for d in range(ndim):

                        # instantiates system to solve with zeros:
                        a = xp.zeros((nb_models + 1, length), dtype=xp.float32)
                        y = xp.zeros((nb_models + 1,), dtype=xp.float32)

                        # iterates through all pairwise registrations:
                        zero_vector = None
                        for tp, model in enumerate(pairwise_models):
                            u = model.u
                            v = model.v
                            confidence = model.overall_confidence()

                            if tp == 0:
                                # we make sure that all shifts are relative to the first timepoint:
                                zero_vector = model.shift_vector[d].copy()

                            vector = model.shift_vector[d] - zero_vector

                            # Each pairwise registration defines a constraint that is added to the matrix:
                            y[tp] = vector.copy()
                            a[tp, u] = +1
                            a[tp, v] = -1

                            # For each time point we collect the average confidence of all the pairwise_registrations:
                            translation_models[u].confidence += confidence
                            translation_models[u].count += 1
                            translation_models[v].confidence += confidence
                            translation_models[v].count += 1

                        # Forces solution to have no displacement for first time point:
                        y[-1] = 0
                        a[-1, 0] = 1

                        # move matrix to sparse domain (much faster!):
                        a = sp.sparse.coo_matrix(a)

                        # solve system:
                        x_opt = linsolve(a, y,
                                         tolerance=tolerance,
                                         order_error=order_error,
                                         order_reg=order_reg,
                                         alpha_reg=alpha_reg)

                        # sets the shift vectors for the resulting sequence reg model, and compute average confidences:
                        for tp in range(length):
                            translation_models[tp].shift_vector[d] = -x_opt[tp]
                            translation_models[tp].confidence /= translation_models[tp].count

                    return SequenceRegistrationModel(model_list=translation_models)


                else:
                    raise ValueError(f"Unsupported sequence stabilisation mode: {mode}")

            # if not image_a.dtype == image_b.dtype:
            #     raise ValueError("Arrays must have the same dtype")
            #
            # if internal_dtype is None:
            #     internal_dtype = image_a.dtype
            #
            # if type(Backend.current()) is NumpyBackend:
            #     internal_dtype = xp.float32
            #
            # image_a = Backend.to_backend(image_a, dtype=internal_dtype)
            # image_b = Backend.to_backend(image_b, dtype=internal_dtype)


def _pairwise_registration(u, v,
                           image_u, image_v,
                           mode,
                           min_confidence,
                           enable_com,
                           quantile,
                           bounding_box,
                           internal_dtype,
                           **kwargs):
    image_u = Backend.to_backend(image_u, dtype=internal_dtype)
    image_v = Backend.to_backend(image_v, dtype=internal_dtype)

    if mode == 'translation':
        model = register_translation_maxproj_nd(image_u, image_v,
                                                _display_phase_correlation=False,
                                                **kwargs)
        confidence = model.overall_confidence()

        if enable_com and (confidence < min_confidence):
            # aprint(f"Warning: low confidence ({confidence}) for pair: ({u}, {v}) falling back to center-of-mass calculation")
            offset_mode = f'p={quantile * 100}'
            com_u = center_of_mass(image_u, mode='full', projection_type='max-min', offset_mode=offset_mode, bounding_box=bounding_box)
            com_v = center_of_mass(image_v, mode='full', projection_type='max-min', offset_mode=offset_mode, bounding_box=bounding_box)
            model = TranslationRegistrationModel(shift_vector=com_u - com_v, confidence=min_confidence)

        model.u = u
        model.v = v

    else:
        raise ValueError(f"Unsupported sequence stabilisation mode: {mode}")

    return model
