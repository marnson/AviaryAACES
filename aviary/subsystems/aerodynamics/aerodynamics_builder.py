"""
Define subsystem builder for Aviary core aerodynamics.

Classes
-------
AerodynamicsBuilderBase : the interface for an aerodynamics subsystem builder.

CoreAerodynamicsBuilder : the interface for Aviary's core aerodynamics subsystem builder
"""
import numpy as np

import openmdao.api as om
from dymos.utils.misc import _unspecified

from aviary.variable_info.variables import Aircraft, Mission, Dynamic

from aviary.subsystems.subsystem_builder_base import SubsystemBuilderBase
from aviary.subsystems.aerodynamics.flops_based.aero_report import AeroReport
from aviary.subsystems.aerodynamics.flops_based.design import Design
from aviary.subsystems.aerodynamics.gasp_based.premission_aero import PreMissionAero
from aviary.subsystems.aerodynamics.gasp_based.gaspaero import CruiseAero
from aviary.subsystems.aerodynamics.gasp_based.gaspaero import LowSpeedAero
from aviary.subsystems.aerodynamics.gasp_based.table_based import TabularCruiseAero
from aviary.subsystems.aerodynamics.gasp_based.table_based import TabularLowSpeedAero
from aviary.subsystems.aerodynamics.flops_based.computed_aero_group import \
    ComputedAeroGroup
from aviary.subsystems.aerodynamics.flops_based.takeoff_aero_group import \
    TakeoffAeroGroup
from aviary.subsystems.aerodynamics.flops_based.solved_alpha_group import \
    SolvedAlphaGroup
from aviary.subsystems.aerodynamics.flops_based.tabular_aero_group import \
    TabularAeroGroup
from aviary.utils.named_values import NamedValues
from aviary.variable_info.enums import LegacyCode
from aviary.variable_info.variable_meta_data import _MetaData


GASP = LegacyCode.GASP
FLOPS = LegacyCode.FLOPS

_default_name = 'aerodynamics'


class AerodynamicsBuilderBase(SubsystemBuilderBase):
    def __init__(self, name=None, meta_data=None):
        if name is None:
            name = _default_name

        super().__init__(name=name, meta_data=meta_data)

    def mission_inputs(self, **kwargs):
        return ['*']

    def mission_outputs(self, **kwargs):
        return ['*']


class CoreAerodynamicsBuilder(AerodynamicsBuilderBase):
    def __init__(self, name=None, meta_data=None, code_origin=None):
        if name is None:
            name = 'core_aerodynamics'

        if code_origin not in (FLOPS, GASP):
            raise ValueError('Code origin is not one of the following: (FLOPS, GASP)')

        self.code_origin = code_origin

        super().__init__(name=name, meta_data=meta_data)

    def build_pre_mission(self, aviary_inputs):
        code_origin = self.code_origin

        if code_origin is GASP:
            aero_group = PreMissionAero(aviary_options=aviary_inputs)

        elif code_origin is FLOPS:
            aero_group = om.Group()
            aero_group.add_subsystem(
                'design', Design(aviary_options=aviary_inputs),
                promotes_inputs=['*'],
                promotes_outputs=['*'])

            aero_group.add_subsystem(
                'aero_report', AeroReport(aviary_options=aviary_inputs),
                promotes_inputs=['*'],
                promotes_outputs=['*'])

        return aero_group

    def build_mission(self, num_nodes, aviary_inputs, **kwargs):
        try:
            method = kwargs.pop('method')
        except KeyError:
            method = None
        if self.code_origin is FLOPS:
            if method is None:
                aero_group = ComputedAeroGroup(num_nodes=num_nodes,
                                               aviary_options=aviary_inputs)

            elif method == 'computed':
                aero_group = ComputedAeroGroup(num_nodes=num_nodes,
                                               aviary_options=aviary_inputs,
                                               **kwargs)

            elif method == 'low_speed':
                aero_group = TakeoffAeroGroup(num_nodes=num_nodes,
                                              aviary_options=aviary_inputs,
                                              **kwargs)

            # TODO solved alpha belongs in the GASP side, rolled into tabular aero
            #      It is currently only here because it is not possible to define
            #      per-subsystem code origins in AviaryProblem yet
            elif method == 'solved_alpha':
                aero_group = SolvedAlphaGroup(num_nodes=num_nodes,
                                              aero_data=kwargs.pop('aero_data'),
                                              **kwargs)

            elif method == 'tabular':
                aero_group = TabularAeroGroup(num_nodes=num_nodes,
                                              CD0_data=kwargs.pop('CD0_data'),
                                              CDI_data=kwargs.pop('CDI_data'),
                                              **kwargs)

            else:
                raise ValueError('FLOPS-based aero method is not one of the following: '
                                 '(computed, low_speed, solved_alpha, tabular)')

        elif self.code_origin is GASP:
            if method is None:
                aero_group = CruiseAero(num_nodes=num_nodes,
                                        aviary_options=aviary_inputs)

            elif method == 'cruise':
                if 'aero_data' in kwargs:
                    aero_group = TabularCruiseAero(num_nodes=num_nodes,
                                                   aviary_options=aviary_inputs,
                                                   aero_data=kwargs.pop('aero_data'),
                                                   **kwargs)
                else:
                    aero_group = CruiseAero(num_nodes=num_nodes,
                                            aviary_options=aviary_inputs,
                                            **kwargs)

            elif method == 'low_speed':
                if any(key in kwargs for key in ['free_aero_data',
                                                 'free_flaps_data',
                                                 'free_ground_data']) in kwargs:
                    aero_group = TabularLowSpeedAero(num_nodes=num_nodes,
                                                     free_aero_data=kwargs.pop(
                                                         'free_aero_data'),
                                                     free_flaps_data=kwargs.pop(
                                                         'free_flaps_data'),
                                                     free_ground_data=kwargs.pop(
                                                         'free_ground_data'),
                                                     **kwargs)

                else:
                    aero_group = LowSpeedAero(num_nodes=num_nodes,
                                              aviary_options=aviary_inputs,
                                              **kwargs)

            else:
                raise ValueError('GASP-based aero method is not one of the following: '
                                 '(cruise, low_speed)')

        return aero_group

    def mission_inputs(self, **kwargs):
        method = kwargs['method']
        promotes = ['*']

        if self.code_origin is FLOPS:
            if method == 'computed':
                promotes = [Dynamic.Mission.STATIC_PRESSURE,
                            Dynamic.Mission.MACH,
                            Dynamic.Mission.TEMPERATURE,
                            Dynamic.Mission.MASS,
                            'aircraft:*', 'mission:*']

            elif method == 'solved_alpha':
                promotes = [Dynamic.Mission.ALTITUDE,
                            Dynamic.Mission.MACH,
                            Dynamic.Mission.MASS,
                            Dynamic.Mission.STATIC_PRESSURE,
                            'aircraft:*']

            elif method == 'low_speed':
                promotes = ['angle_of_attack',
                            Dynamic.Mission.ALTITUDE,
                            Dynamic.Mission.FLIGHT_PATH_ANGLE,
                            Mission.Takeoff.DRAG_COEFFICIENT_MIN,
                            Aircraft.Wing.ASPECT_RATIO,
                            Aircraft.Wing.HEIGHT,
                            Aircraft.Wing.SPAN,
                            Dynamic.Mission.DYNAMIC_PRESSURE,
                            Aircraft.Wing.AREA]

            elif method == 'tabular':
                promotes = [Dynamic.Mission.ALTITUDE,
                            Dynamic.Mission.MACH,
                            Dynamic.Mission.MASS,
                            Dynamic.Mission.VELOCITY,
                            Dynamic.Mission.DENSITY,
                            'aircraft:*']

            else:
                raise ValueError('FLOPS-based aero method is not one of the following: '
                                 '(computed, low_speed, solved_alpha, tabular)')

        elif self.code_origin is GASP:
            if method == 'low_speed':
                promotes = ['*',
                            ("airport_alt", Mission.Takeoff.AIRPORT_ALTITUDE),
                            ("CL_max_flaps", Mission.Takeoff.LIFT_COEFFICIENT_MAX),
                            ("dCL_flaps_model", Mission.Takeoff.LIFT_COEFFICIENT_FLAP_INCREMENT),
                            ("dCD_flaps_model", Mission.Takeoff.DRAG_COEFFICIENT_FLAP_INCREMENT),
                            ("flap_defl", Aircraft.Wing.FLAP_DEFLECTION_TAKEOFF)]

            elif method == 'cruise':
                if 'output_alpha' in kwargs:
                    if kwargs['output_alpha']:
                        promotes = ['*', ("lift_req", "weight")]

            else:
                raise ValueError('GASP-based aero method is not one of the following: '
                                 '(low_speed, cruise)')

        return promotes

    def mission_outputs(self, **kwargs):
        method = kwargs['method']
        promotes = ['*']

        if self.code_origin is FLOPS:
            promotes = [Dynamic.Mission.DRAG, Dynamic.Mission.LIFT]

        elif self.code_origin is GASP:
            if method == 'low_speed':
                promotes = [Dynamic.Mission.DRAG,
                            Dynamic.Mission.LIFT,
                            'CL', 'CD', 'flap_factor', 'gear_factor']

            elif method == 'cruise':
                if 'output_alpha' in kwargs:
                    if kwargs['output_alpha']:
                        promotes = [Dynamic.Mission.DRAG,
                                    Dynamic.Mission.LIFT,
                                    'alpha']
                else:
                    promotes = [Dynamic.Mission.DRAG,
                                Dynamic.Mission.LIFT,
                                'CL_max']

            else:
                raise ValueError('GASP-based aero method is not one of the following: '
                                 '(low_speed, cruise)')

        return promotes

    def get_parameters(self, aviary_inputs=None, phase_info=None):
        """
        Return a dictionary of fixed values for the subsystem.

        Optional, used if subsystems have fixed values.

        Used in the phase builders (e.g. cruise_phase.py) when other parameters are added to the phase.

        This is distinct from `get_design_vars` in a nuanced way. Design variables
        are variables that are optimized by the problem that are not at the phase level.
        An example would be something that occurs in the pre-mission level of the problem.
        Parameters are fixed values that are held constant throughout a phase, but if
        `opt=True`, they are able to change during the optimization.

        Parameters
        ----------
        phase_info : dict
            The phase_info subdict for this phase.

        Returns
        -------
        fixed_values : dict
            A dictionary where the keys are the names of the fixed variables
            and the values are dictionaries with the following keys:

            - 'value': float or array
                The fixed value for the variable.
            - 'units': str
                The units for the fixed value (optional).
            - any additional keyword arguments required by OpenMDAO for the fixed
              variable.
        """
        num_engine_type = len(aviary_inputs.get_val(Aircraft.Engine.NUM_ENGINES))
        params = {}

        if self.code_origin is FLOPS:
            try:
                aero_opt = phase_info['subsystem_options'][self.name]
                method = aero_opt['method']
            except KeyError:
                method = 'computed'

            if phase_info is not None:
                # Only solved_alpha has connectable inputs.
                if method == 'solved_alpha':
                    aero_data = aero_opt['aero_data']

                    if isinstance(aero_data, NamedValues):
                        altitude = aero_data.get_item('altitude')[0]
                        mach = aero_data.get_item('mach')[0]
                        angle_of_attack = aero_data.get_item('angle_of_attack')[0]

                        n1 = altitude.size
                        n2 = mach.size
                        n3 = angle_of_attack.size
                        n1u = np.unique(altitude).size

                        if n1 > n1u:
                            # Data is free-format instead of pre-formatted.
                            n1 = n1u
                            n2 = np.unique(mach).size
                            n3 = np.unique(angle_of_attack).size

                        shape = (n1, n2, n3)

                        if aviary_inputs is not None and Aircraft.Design.LIFT_POLAR in aviary_inputs:
                            lift_opts = {'val': aviary_inputs.get_val(Aircraft.Design.LIFT_POLAR),
                                         'static_target': True}
                        else:
                            lift_opts = {'shape': shape,
                                         'static_target': True}

                        if aviary_inputs is not None and Aircraft.Design.DRAG_POLAR in aviary_inputs:
                            drag_opts = {'val': aviary_inputs.get_val(Aircraft.Design.DRAG_POLAR),
                                         'static_target': True}
                        else:
                            drag_opts = {'shape': shape,
                                         'static_target': True}

                        params[Aircraft.Design.LIFT_POLAR] = lift_opts
                        params[Aircraft.Design.DRAG_POLAR] = drag_opts

            if method == 'computed':

                # Parameters for drag computation.
                core_inputs = [
                    Aircraft.Design.BASE_AREA,
                    Aircraft.Design.LIFT_DEPENDENT_DRAG_COEFF_FACTOR,
                    Aircraft.Design.SUBSONIC_DRAG_COEFF_FACTOR,
                    Aircraft.Design.SUPERSONIC_DRAG_COEFF_FACTOR,
                    Aircraft.Design.ZERO_LIFT_DRAG_COEFF_FACTOR,
                    Aircraft.Fuselage.CHARACTERISTIC_LENGTH,
                    Aircraft.Fuselage.CROSS_SECTION,
                    Aircraft.Fuselage.DIAMETER_TO_WING_SPAN,
                    Aircraft.Fuselage.FINENESS,
                    Aircraft.Fuselage.LAMINAR_FLOW_LOWER,
                    Aircraft.Fuselage.LAMINAR_FLOW_UPPER,
                    Aircraft.Fuselage.LENGTH_TO_DIAMETER,
                    Aircraft.Fuselage.WETTED_AREA,
                    Aircraft.HorizontalTail.CHARACTERISTIC_LENGTH,
                    Aircraft.HorizontalTail.FINENESS,
                    Aircraft.HorizontalTail.LAMINAR_FLOW_LOWER,
                    Aircraft.HorizontalTail.LAMINAR_FLOW_UPPER,
                    Aircraft.HorizontalTail.WETTED_AREA,
                    Aircraft.VerticalTail.CHARACTERISTIC_LENGTH,
                    Aircraft.VerticalTail.FINENESS,
                    Aircraft.VerticalTail.LAMINAR_FLOW_LOWER,
                    Aircraft.VerticalTail.LAMINAR_FLOW_UPPER,
                    Aircraft.VerticalTail.WETTED_AREA,
                    Aircraft.Wing.AREA,
                    Aircraft.Wing.ASPECT_RATIO,
                    Aircraft.Wing.CHARACTERISTIC_LENGTH,
                    Aircraft.Wing.FINENESS,
                    Aircraft.Wing.LAMINAR_FLOW_LOWER,
                    Aircraft.Wing.LAMINAR_FLOW_UPPER,
                    Aircraft.Wing.MAX_CAMBER_AT_70_SEMISPAN,
                    Aircraft.Wing.SPAN_EFFICIENCY_FACTOR,
                    Aircraft.Wing.SWEEP,
                    Aircraft.Wing.TAPER_RATIO,
                    Aircraft.Wing.THICKNESS_TO_CHORD,
                    Aircraft.Wing.WETTED_AREA,
                    Mission.Design.GROSS_MASS,
                    Mission.Design.LIFT_COEFFICIENT,
                    Mission.Design.MACH,
                ]

                for var in core_inputs:

                    meta = _MetaData[var]

                    val = meta['default_value']
                    if val is None:
                        val = _unspecified
                    units = meta['units']

                    if var in aviary_inputs:
                        try:
                            val = aviary_inputs.get_val(var, units)
                        except TypeError:
                            val = aviary_inputs.get_val(var)

                    params[var] = {'val': val,
                                   'static_target': True}

                # These parameters are sized by number of engine models.
                engine_sized_vars = [Aircraft.Nacelle.CHARACTERISTIC_LENGTH,
                                     Aircraft.Nacelle.FINENESS,
                                     Aircraft.Nacelle.LAMINAR_FLOW_LOWER,
                                     Aircraft.Nacelle.LAMINAR_FLOW_UPPER,
                                     Aircraft.Nacelle.WETTED_AREA]

                for var in engine_sized_vars:
                    params[var] = {'shape': (num_engine_type, ), 'static_target': True}

        return params

    def report(self, prob, reports_folder, **kwargs):
        """
        Generate the report for Aviary core aerodynamics analysis

        Parameters
        ----------
        prob : AviaryProblem
            The AviaryProblem that will be used to generate the report
        reports_folder : Path
            Location of the subsystems_report folder this report will be placed in
        """
        if self.code_origin is FLOPS:
            # FLOPS aero report goes here
            return
        elif self.code_origin is GASP:
            # GASP aero report goes here
            return
