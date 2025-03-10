import openmdao.api as om
import numpy as np
import scipy.io


# from marnson.fast_oew_surrogate import FASTOEWSurrogate
from aviary.api import SubsystemBuilderBase, Aircraft, Mission

class UnifiedAirframeModel(om.ExplicitComponent):

    
    