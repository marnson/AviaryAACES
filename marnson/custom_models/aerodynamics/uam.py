import openmdao.api as om
import numpy as np
import scipy.io


# from marnson.fast_oew_surrogate import FASTOEWSurrogate
from aviary.api import SubsystemBuilderBase, Aircraft, Mission

class UAM_Geometry(om.ExplicitComponent):


    def setup(self):

        # add inputs
        self.add_input('Span')
        self.add_input('RootChord')

        # wing geometry input. these all must be the same length: 5, first index is aircraft centerline
        self.add_input('RibChord') # as a percentage of the root chord
        self.add_input('RibXLocation') # as a percentage of the root chord
        self.add_input('RibYLocation', val = np.array([0, 0.15, 0.3, 0.45, 1 ])) # as a percentage of span
        self.add_input('RibTC') # thickness to chord ratio of the ribs

        # add inputs for minimum area and fuel volume checks?

        # outputs
        self.add_output('AspectRatio')
        self.add_output('FuelVolume')
        self.add_output('CabinArea')

    def compute(self,inputs,outputs):

        chords = inputs['RootChord'][0] * inputs['RibChord'][:]
        ylocations = inputs['Span'][0] * inputs['RibYLocation']
        heights = ylocations[1:] - ylocations[:-1]

        
        area = np.zeros(np.size(heights))
        fuelvols = np.zeros(np.size(heights))
        cabinareas = np.zeros(np.size(heights))


        for ii in range(np.size(inputs['RibChord'])-1):
            area[ii] = 0.75 * (chords[ii] + chords[ii + 1])/2 * heights[ii]
            thickness = (chords[ii] * inputs['RibTC'][ii] + chords[ii+1] * inputs['RibTC'][ii+1]) / 2

            if ii <= 1:
                fuelvols[ii] = 0
                cabinareas[ii] = area[ii]
            else:
                fuelvols[ii] = 0.75 * area[ii] * thickness
                cabinareas[ii] = 0

        outputs['FuelVolume'] = np.sum(fuelvols)
        outputs['CabinArea'] = np.sum(cabinareas)
        outputs['AspectRatio'] = inputs['Span'][0]**2 / np.sum(area)

    


class UAM_Drag(om.ExplicitComponent):

    def setup(self):
        placeholder

class UAM(om.Group):

    def setup(self):
        placeholder