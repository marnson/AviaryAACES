"""
This is a slightly more complex Aviary example of running a coupled aircraft design-mission optimization.
It runs the same mission as the `run_basic_aviary_example.py` script, but it uses the AviaryProblem class to set up the problem.
This exposes more options and flexibility to the user and uses the "Level 2" API within Aviary.

We define a `phase_info` object, which tells Aviary how to model the mission.
Here we have climb, cruise, and descent phases.
We then call the correct methods in order to set up and run an Aviary optimization problem.
This performs a coupled design-mission optimization and outputs the results from Aviary into the `reports` folder.

This is just the standard aviary example but with a custom OEW prediction used instead. this reduces the number of inputs that are required while also lowering fidelity
-max arnson

"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import aviary.api as av
from aviary.api import default_height_energy_phase_info as phase_info
import openmdao.api as om
from copy import deepcopy
from marnson.custom_models.mass.surrogate_oew import SurrogateWeightBuilder

prob = av.AviaryProblem()

# Load aircraft and options data from user
# Allow for user overrides here
phase_info = deepcopy(av.default_height_energy_phase_info)

phase_info['pre_mission']['external_subsystems'] = [SurrogateWeightBuilder(name = "FAST_OEW_External")]


prob.load_inputs('models/test_aircraft/aircraft_for_bench_FwFm.csv', phase_info)

# Preprocess inputs
prob.check_and_preprocess_inputs()

prob.add_pre_mission_systems()

prob.add_phases()

prob.add_post_mission_systems()

# Link phases and variables
prob.link_phases()

prob.add_driver("SLSQP", max_iter=100)

prob.add_design_variables()

# Load optimization problem formulation
# Detail which variables the optimizer can control
prob.add_objective()

prob.setup()

prob.set_initial_guesses()

prob.run_aviary_problem()

om.n2(prob)
