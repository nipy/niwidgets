from matplotlib import pyplot as plt
import ipywidgets


def get_cmap_dropdown(colormap):
    # set default colormap options & add them to the kwargs
    if colormap is None:
        options = (sorted(m for m in plt.cm.datad if not m.endswith("_r")))
        return ipywidgets.Dropdown(
            options=options, value='summer', description='Colormap:'
        )
    elif isinstance(colormap, (list, tuple)):
        return ipywidgets.Dropdown(
            options=colormap, value=colormap[0], description='Colormap:'
        )
    elif isinstance(colormap, str):
        return ipywidgets.fixed(colormap)
    else:
        raise ValueError('The colormap must be either a valid string, a list, '
                         'or None.')
