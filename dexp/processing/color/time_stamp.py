from typing import Union, Tuple, Sequence, Generator, Any

from dexp.processing.backends.backend import Backend
from dexp.processing.color.blend import blend_color_images
from dexp.processing.color.cairo_utils import get_array_for_cairo_surface


def insert_time_stamp(images: Union[Generator[Any, Any, None], Sequence[Any]],
                      start_time: float = 0,
                      time_interval: float = 1,
                      margin: float = 1,
                      translation: Union[str, Sequence[Tuple[Union[int, float], ...]]] = 'top_right',
                      color: Tuple[float, float, float, float] = None,
                      number_format: str = '{:.1f}',
                      font_name: str = "Helvetica",
                      font_size: float = 32,
                      unit: str = 's',
                      mode: str = 'max',
                      alpha: float = 1):
    """
    Inserts a scale bar into an image.

    Parameters
    ----------
    images: Image into which to insert the scale bar.
    start_time: Start time for time stamp
    time_interval: Time interval inn units of time between consecutive images.
    margin: margin around bar expressed in units relative to the text height
    translation: Positions of the time stamp in pixels in natural order: (x, y). Can also be a string: 'bottom_left', 'bottom_right', 'top_left', 'top_right'.
    color: Color of the bar and text as tuple of 4 values: (R, G, B, A)
    number_format: Format string to represent the start and end values.
    font_name: Font name.
    font_size: Font size in pixels.
    unit: Unit name.
    mode: Blending mode. See function 'blend_color_images' for available blending modes.
    alpha: Inset transparency.

    Returns
    -------
    Image with inserted scale bar.

    """

    xp = Backend.get_xp_module()
    sp = Backend.get_sp_module()

    if color is None:
        color = (1, 1, 1, 1)

    # Turn sequence or generator into list, and move to backend:
    images = list(Backend.to_backend(image) for image in images)

    # Check that there is at least one image in the image list:
    if len(images) == 0:
        raise ValueError(f"Blending requires at least one image!")

    # Verify that all images are of the same shape:
    for image in images:
        if images[0].ndim != image.ndim or images[0].shape[:-1] != image.shape[:-1]:
            raise ValueError("All images in sequence must have the same number of dimensions and shape!")

    # verify that the images are 2D RGB(A) images:
    if images[0].ndim != 3 or not images[0].shape[2] in (3, 4):
        raise ValueError("Images must be 2D RGB(A) images!")

    # Image shape:
    height, width = images[0].shape[:-1]

    # Dummy surface just for computing text width and height:
    import cairo
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(surface)
    context.scale(1, 1)

    # Configure text rendering:
    context.select_font_face(font_name,
                             cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_NORMAL)
    context.set_font_size(font_size)

    # longest text to be rendered:
    end_time = start_time + len(images) * time_interval
    time_text = number_format.format(end_time)
    text = f"{time_text} {unit}"

    # determine text height and width:
    text_width = context.text_extents(text)[2]
    text_height = context.text_extents(text)[3]
    end_time_text_width = context.text_extents(time_text + 'x')[2]

    # Margins:
    margin_height = margin * text_height
    margin_width = margin * text_height

    # Set the position of the time stamp
    if 'top' in translation:
        y = margin_height + text_height
    elif 'bottom' in translation:
        y = height - (margin_height + text_height)
    if 'left' in translation:
        x = margin_width
    elif 'right' in translation:
        x = width - (margin_width + text_width)

    def generate_time_stamp(timepoint: int):
        # Create surface:
        import cairo
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        context = cairo.Context(surface)
        context.scale(1, 1)

        # Configure text rendering:
        context.select_font_face(font_name,
                                 cairo.FONT_SLANT_NORMAL,
                                 cairo.FONT_WEIGHT_NORMAL)
        context.set_font_size(font_size)

        # First we turn off antialiasing, works better:
        context.set_antialias(cairo.ANTIALIAS_NONE)

        # Turn off alpha blending and clears the image:
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.set_source_rgba(0, 0, 0, 0)
        context.rectangle(0, 0, 1, 1)
        context.fill()

        # Turn on antialiasing for text:
        context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)

        # Turn back on alpha blending:
        context.set_operator(cairo.OPERATOR_OVER)

        # Set text color:
        context.set_source_rgba(*color)

        # Text to be rendered:
        time = start_time + timepoint * time_interval
        time_text = f"{number_format.format(time)}"
        time_width = context.text_extents(time_text + 'x')[2]
        unit_text = unit

        # draw text at correct location:
        context.move_to(x + end_time_text_width - time_width, y)
        context.show_text(time_text)
        context.move_to(x + end_time_text_width, y)
        context.show_text(unit_text)

        # Get array from surface:
        time_stamp = get_array_for_cairo_surface(surface)

        return time_stamp

    # Apply time stamp to each image:
    images_with_time_stamps = []
    for tp, image in enumerate(images):
        time_stamp = generate_time_stamp(tp)
        # Blend images:
        image_with_time_stamp = blend_color_images(images=(image, time_stamp),
                                                   alphas=(1, alpha),
                                                   modes=('max', mode))

        images_with_time_stamps.append(image_with_time_stamp)

    return images_with_time_stamps
