import ipywidgets as widgets
import traitlets


class PlaySlider(widgets.HBox):
    """
    A combined Play / IntSlider widget.
    """

    max = traitlets.Integer(100)
    min = traitlets.Integer(0)
    value = traitlets.Integer(0)
    step = traitlets.Integer(1)
    interval = traitlets.Integer(500)

    def __init__(
        self,
        *args,
        min=0,
        max=100,
        value=100,
        step=1,
        interval=500,
        label="Value",
        continuous_update=True,
        **kwargs
    ):

        # initialise the hbox widget
        super().__init__(
            [
                widgets.Label(label + ": "),
                widgets.Play(min=min, max=max, value=value, interval=interval),
                widgets.IntSlider(
                    min=min,
                    max=max,
                    value=value,
                    step=step,
                    continuous_update=continuous_update,
                ),
            ]
        )
        for trait in ("min", "max", "value", "step"):
            # first the two control elements:
            widgets.link((self.children[1], trait), (self.children[2], trait))
            # then link the latter with self:
            widgets.link((self.children[2], trait), (self, trait))

        widgets.link((self.children[1], "interval"), (self, "interval"))
