import openmdao.api as om
import numpy as np
import scipy.io


# from marnson.fast_oew_surrogate import FASTOEWSurrogate
from aviary.api import SubsystemBuilderBase, Aircraft, Mission

class FASTOEWSurrogate(om.ExplicitComponent):
    
    # setup input variables for the Gaussian process regression
    # TODO: add OpenMDAO or aviary variable paths here 
    def setup(self):

        # run the helperfunction to initialize the fast inputs from the files
        self.read_data_from_mat_files()

        # model inputs
        self.add_input('PropulsionWeight',units='kg')
        self.add_input('Payload',units='kg')
        self.add_input('Range',units='m')
        self.add_input('MTOW',units='kg')
        self.add_input('SLS_Thrust',units='N')

        # model output
        self.add_output('OEW',units='kg')

        # partial derivatives
        self.declare_partials('*','*', method = 'fd') # change later, actually have the partials for these (very easy to calculate)


    # Read in FAST data sets, which will be used for a Gaussian process regression
    # These were precomputed using FAST for a single OEW regression
    def read_data_from_mat_files(self):
        RegressionData   = scipy.io.loadmat('marnson/RegressionData.mat')

        # Values stored in the .mat file
        self.DataMatrix  = RegressionData['DataMatrix' ]
        self.HyperParams = RegressionData['HyperParams']
        self.InverseTerm = RegressionData['InverseTerm']
        self.Mu0         = RegressionData['Mu0'        ]

        # Ybar is just the airframe data from the datamatrix
        self.Ybar        = self.DataMatrix[:,-1]


    def compute(self,inputs,outputs):
    

        # extract size of data matrix
        N = np.size(self.DataMatrix,0) # N = 243 in this case but might change slightly if there is an update to FAST database

        # create current target (this will be the same each time this operation can be moved outside of the loop)
        Target = np.tile(np.array([inputs['Payload'][0], inputs['Range'][0], inputs['MTOW'][0], inputs['SLS_Thrust'][0]]),(N,1)) # size 243 by 4

        # Need to repmat the hyperparameters so they are the same size as the data and the repeated target
        RepHyperParams = np.tile(self.HyperParams[:,:-1],(N,1)) # same size as target

        # return the kernel value for the target compared to every row in the data matrix
        Kstarbar = self.HyperParams[0,-1] * np.exp( -0.3*np.sum((Target-self.DataMatrix[:,:-1])**2 / RepHyperParams,axis=1)) # shave off the last column of DataMatrix as that is not relevant to the input space
                             
        # Multiply Matrices to get the output
        Posterior = self.Mu0 + Kstarbar @ self.InverseTerm @ np.transpose(self.Ybar - self.Mu0)

        # Assign ouput
        outputs['OEW'] = Posterior + inputs['PropulsionWeight']

class SurrogateWeightBuilder(SubsystemBuilderBase):

    """
    
    subsystem override for the OEW (really oew - propulsion) mass in aviary
    
    
    """

    def __init__(self, name='OEW_minus_propulsion'):
        super().__init__(name)

    def build_pre_mission(self, aviary_inputs):

        surrogate_oew = om.Group()
        surrogate_oew.add_subsystem("SurrogateOEW",FASTOEWSurrogate(),
                                        promotes_inputs=
                                            [
                                            ('PropulsionWeight', Aircraft.Propulsion.MASS),
                                            ('Payload', Aircraft.CrewPayload.TOTAL_PAYLOAD_MASS),
                                            ('Range', Mission.Design.RANGE),
                                            ('MTOW', Mission.Design.GROSS_MASS),
                                            ('SLS_Thrust', Aircraft.Propulsion.TOTAL_SCALED_SLS_THRUST),
                                            ],
                                        promotes_outputs= [('OEW', Aircraft.Design.EMPTY_MASS)]
                                    )

        return surrogate_oew
    







# # component testing
# if __name__ == '__main__':
#     prob = om.Problem(reports=None)
#     prob.model.add_subsystem('oew_surrogate', FASTOEWSurrogate(), promotes=['*'])

#     prob.setup()
#     prob.set_val('PropulsionWeight', 0)
#     prob.set_val('Payload', 20000)
#     prob.set_val('Range', 3e6)
#     prob.set_val('MTOW', 100e3)
#     prob.set_val('SLS_Thrust', 100e3)


    
#     prob.run_model()
#     print(prob.get_val('OEW'))


