from aviary.utils.aviary_values import AviaryValues
import numpy as np

from aviary.variable_info.enums import SpeedType, Verbosity, AlphaModes
from aviary.mission.gasp_based.phases.time_integration_phases import SGMGroundroll, \
    SGMRotation, SGMAscentCombined, SGMAccel, SGMClimb, SGMCruise, SGMDescent
from aviary.variable_info.variables import Aircraft, Mission, Dynamic

# defaults for 2DOF based forward in time integeration phases

cruise_alt = 35e3,
cruise_mach = .8,

ascent_phases = {
    'groundroll': {
        'builder': SGMGroundroll,
        'user_options': {
            # special case
            'attr:VR_value': ('SGMGroundroll_velocity_trigger', 'kn'),
        },
        'initial_guesses': {
        }
    },
    'rotation': {
        'builder': SGMRotation,
        'user_options': {
        },
        'initial_guesses': {
        }
    },
    'ascent': {
        'builder': SGMAscentCombined,
        'user_options': {
            't_init_gear': (10000, 's'),
            't_init_flaps': (10000, 's'),
            # special case
            'rotation.start_rotation': (10000, 's'),
            # special case
            'attr:fuselage_angle_max': (Aircraft.Design.MAX_FUSELAGE_PITCH_ANGLE, 'deg'),
        },
        'initial_guesses': {
        }
    },
    'accel': {
        'builder': SGMAccel,
        'user_options': {
        },
        'initial_guesses': {
        }
    },
    'climb1': {
        'kwargs': dict(
            input_speed_type=SpeedType.EAS,
            input_speed_units='kn',
            speed_trigger_units='unitless',
        ),
        'builder': SGMClimb,
        'user_options': {
            'alt_trigger': (10000, 'ft'),
            'EAS': (250, 'kn'),
            'speed_trigger': (cruise_mach, 'unitless'),
        },
        'initial_guesses': {
        }
    },
    'climb2': {
        'kwargs': dict(
            input_speed_type=SpeedType.EAS,
            input_speed_units='kn',
            speed_trigger_units='unitless',
        ),
        'builder': SGMClimb,
        'user_options': {
            'alt_trigger': (cruise_alt, 'ft'),
            'EAS': (270, 'kn'),
            'speed_trigger': (cruise_mach, 'unitless'),
        },
        'initial_guesses': {
        }
    },
    'climb3': {
        'kwargs': dict(
            input_speed_type=SpeedType.MACH,
            input_speed_units='unitless',
            speed_trigger_units='kn',
        ),
        'builder': SGMClimb,
        'user_options': {
            'alt_trigger': (cruise_alt, 'ft'),
            'mach': (cruise_mach, 'unitless'),
            'speed_trigger': (0, 'kn'),
        },
        'initial_guesses': {
        }
    },
}
cruise_phase = {
    'cruise': {
        'kwargs': dict(
            input_speed_type=SpeedType.MACH,
            input_speed_units="unitless",
            alpha_mode=AlphaModes.REQUIRED_LIFT,
        ),
        'builder': SGMCruise,
        'user_options': {
            'mach': (cruise_mach, 'unitless'),
            'attr:mass_trigger': ('SGMCruise_mass_trigger', 'lbm')
        },
        'initial_guesses': {
        }
    },
}
descent_phases = {
    'desc1': {
        'kwargs': dict(
            input_speed_type=SpeedType.MACH,
            input_speed_units='unitless',
            speed_trigger_units='kn',
        ),
        'builder': SGMDescent,
        'user_options': {
            'alt_trigger': (10000, 'ft'),
            'mach': (cruise_mach, 'unitless'),
            'speed_trigger': (350, 'kn'),
        },
        'initial_guesses': {
        }
    },
    'desc2': {
        'kwargs': dict(
            input_speed_type=SpeedType.EAS,
            input_speed_units='kn',
            speed_trigger_units='kn',
        ),
        'builder': SGMDescent,
        'user_options': {
            'alt_trigger': (10000, 'ft'),
            'EAS': (350, 'kn'),
            'speed_trigger': (0, 'kn'),
        },
        'initial_guesses': {
        }
    },
    'desc3': {
        'kwargs': dict(
            input_speed_type=SpeedType.EAS,
            input_speed_units='kn',
            speed_trigger_units='kn',
        ),
        'builder': SGMDescent,
        'user_options': {
            'alt_trigger': (1000, 'ft'),
            'EAS': (250, 'kn'),
            'speed_trigger': (0, 'kn'),
        },
        'initial_guesses': {
        }
    },
}

phase_info = {
    **ascent_phases,
    **cruise_phase,
    **descent_phases,
}


def phase_info_parameterization(phase_info, post_mission_info, aviary_inputs: AviaryValues):
    """
    Modify the values in the phase_info dictionary to accomodate different values
    for the following mission design inputs: cruise altitude, cruise mach number,
    cruise range, design gross mass.

    Parameters
    ----------
    phase_info : dict
        Dictionary of phase settings for a mission profile
    aviary_inputs : <AviaryValues>
        Object containing values and units for all aviary inputs and options

    Returns
    -------
    dict
        Modified phase_info that has been changed to match the new mission
        parameters
    """

    range_cruise = aviary_inputs.get_item(Mission.Design.RANGE)
    alt_cruise = aviary_inputs.get_item(Mission.Design.CRUISE_ALTITUDE)
    gross_mass = aviary_inputs.get_item(Mission.Design.GROSS_MASS)
    mach_cruise = aviary_inputs.get_item(Mission.Design.MACH)

    phase_info['climb1']['user_options']['speed_trigger'] = mach_cruise

    phase_info['climb2']['user_options']['alt_trigger'] = alt_cruise
    phase_info['climb2']['user_options']['speed_trigger'] = mach_cruise

    phase_info['climb3']['user_options']['alt_trigger'] = alt_cruise
    phase_info['climb3']['user_options']['mach'] = mach_cruise

    phase_info['cruise']['user_options']['mach'] = mach_cruise

    phase_info['desc1']['user_options']['mach'] = mach_cruise

    return phase_info, post_mission_info
