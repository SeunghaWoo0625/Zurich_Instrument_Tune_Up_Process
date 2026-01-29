from laboneq.dsl.experiment.pulse_library import *

@register_pulse_functional
def test_custom_pulse_function(x,**_):
    return x
