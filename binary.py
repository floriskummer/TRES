from amuse.units import units, constants, quantities
import numpy as np

REPORT_BINARY_EVOLUTION = False
REPORT_FUNCTION_NAMES = False
REPORT_MASS_TRANSFER_STABILITY = False

#constants
numerical_error  = 1.e-6
minimum_eccentricity = 1.e-5

which_common_envelope = 2
#0 alpha + dce
#1 gamma + dce
#2 seba style
const_common_envelope_efficiency = 4.0 #1.0, 4 for now for easier testing with SeBa
const_envelope_structure_parameter = 0.5
const_common_envelope_efficiency_gamma = 1.75

stellar_types_compact_objects = [10,11,12,13,14]|units.stellar_type
stellar_types_giants = [2,3,4,5,6,8,9]|units.stellar_type
#q_crit = 3.
#q_crit_giants_conv_env = 0.9
nucleair_efficiency = 0.007 # nuc. energy production eff, Delta E = 0.007 Mc^2



    

#dictionaries
bin_type = {    
                'unknown': 'unknown',       
                'merger': 'merger', 
                'disintegrated': 'disintegrated', 
                'detached': 'detached',       
                'contact': 'contact',    
                'collision': 'collision',    
                'semisecular': 'semisecular',    
                  
                'rlof': 'rlof',   #only used for stopping conditions
                'stable_mass_transfer': 'stable_mass_transfer',
                 
                'common_envelope': 'common_envelope',     

                'common_envelope_energy_balance': 'common_envelope_energy_balance',     
                'ce_e': 'common_envelope_energy_balance',     
                'ce_alpha': 'common_envelope_energy_balance',     

                'common_envelope_angular_momentum_balance': 'common_envelope_angular_momentum_balance',
                'ce_J': 'common_envelope_angular_momentum_balance',
                'ce_gamma': 'common_envelope_angular_momentum_balance',

                'double_common_envelope': 'double_common_envelope',
                'dce': 'double_common_envelope',
                
            }            

#-------------------------
#general functions
def roche_radius_dimensionless(M, m):
    # Assure that the q is calculated in identical units.
    unit = M.unit
    # and that q itself has no unit
    q = M.value_in(unit)/m.value_in(unit)
    q13 =  q**(1./3.)
    q23 =  q13**2
    return  0.49*q23/(0.6*q23 + np.log(1 + q13))

def roche_radius(bin, primary, self):
    if not bin.is_star and primary.is_star:
        return bin.semimajor_axis * roche_radius_dimensionless(primary.mass, self.get_mass(bin)-primary.mass)

    print('Error: Roche radius can only be determined in a binary')
    exit(1)

#for comparison with kozai timescale
def stellar_evolution_timescale(star):
    if REPORT_FUNCTION_NAMES:
        print("Stellar evolution timescale")
        
    if star.stellar_type in [0,1,7]|units.stellar_type:
        return (0.1 * star.mass * nucleair_efficiency * constants.c**2 / star.luminosity).in_(units.Gyr)
    elif star.stellar_type in stellar_types_compact_objects:
        return np.inf|units.Myr 
    else:        
        return 0.1*star.age


#for mass transfer rate
def nuclear_evolution_timescale(star):
    if REPORT_FUNCTION_NAMES:
        print("Nuclear evolution timescale:")
        
    if star.stellar_type in [0,1,7]|units.stellar_type:
        return (0.1 * star.mass * nucleair_efficiency * constants.c**2 / star.luminosity).in_(units.Gyr)
    else: #t_nuc ~ delta t * R/ delta R, other prescription gave long timescales in SeBa which destables the mass transfer
        if star.time_derivative_of_radius <= (quantities.zero+numerical_error**2)|units.RSun/units.yr:
        #when star is shrinking
#            t_nuc = 0.1*main_sequence_time() # in SeBa
            t_nuc = 0.1*star.age         
        else: 
            t_nuc = star.radius / star.time_derivative_of_radius #does not include the effect of mass loss on R

        return t_nuc

def kelvin_helmholds_timescale(star):
    if REPORT_FUNCTION_NAMES:
        print("KH timescale:", (constants.G*star.mass**2/star.radius/star.luminosity).in_(units.Myr))
    return constants.G*star.mass**2/star.radius/star.luminosity

def dynamic_timescale(star):
    if REPORT_FUNCTION_NAMES:
        print("Dynamic timescale:", (np.sqrt(star.radius**3/star.mass/constants.G)[0]).in_(units.yr))
    return np.sqrt(star.radius**3/star.mass/constants.G)   
    
def corotating_spin_angular_frequency_binary(semi, m1, m2):
    return 1./np.sqrt(semi**3/constants.G / (m1+m2))

#Hurley, Pols en Tout 2000, eq 107-108
def lang_spin_angular_frequency(star):
    v_rot = 330*star.mass.value_in(units.MSun)**3.3/(15.0+star.mass.value_in(units.MSun)**3.45)
    w = 45.35 * v_rot/star.radius.value_in(units.RSun)
    return w|1./units.yr

def copy_outer_orbit_to_inner_orbit(bs, self):
    if REPORT_FUNCTION_NAMES:
        print('Copy_outer_orbit_to_inner_orbit')

    if self.is_triple():
        bs.semimajor_axis = self.triple.semimajor_axis
        bs.eccentricity = self.triple.eccentricity
        bs.argument_of_pericenter = self.triple.argument_of_pericenter
        bs.longitude_of_ascending_node = self.triple.longitude_of_ascending_node
        bs.mass_transfer_rate = self.triple.mass_transfer_rate
        bs.accretion_efficiency_mass_transfer, = self.triple.accretion_efficiency_mass_transfer,
        bs.accretion_efficiency_wind_child1_to_child2, = self.triple.accretion_efficiency_wind_child1_to_child2,
        bs.accretion_efficiency_wind_child2_to_child1, = self.triple.accretion_efficiency_wind_child2_to_child1,
        bs.specific_AM_loss_mass_transfer, = self.triple.specific_AM_loss_mass_transfer,
        bs.is_stable = self.triple.is_stable
    
        self.triple.semimajor_axis = 1e100|units.RSun
        self.triple.eccentricity = 0
        
def copy_outer_star_to_accretor(self):
    if REPORT_FUNCTION_NAMES:
        print('Copy_outer_star_to_accretor')

    if self.is_triple():        
        if self.triple.child1.is_star:
            tertiary_star = self.triple.child1
            bs = self.triple.child2
        else:
            tertiary_star = self.triple.child2 
            bs = self.triple.child1
            

        if not bs.child1.is_donor:
            bs.child1 = tertiary_star
        else:
            bs.child2 = tertiary_star

    
#-------------------------

#-------------------------
# functions for mass transfer in a binary

def perform_inner_collision(self):
    if self.is_triple():
        if self.triple.child1.is_star:
            self.triple.child2
        else:
            self.triple.child1
        
        # smaller star is added to big star
        if bs.child1.radius >= bs.child2.radius:
            donor = bs.child1
            accretor = bs.child2
        else:
            donor = bs.child2
            accretor = bs.child1
    
        donor_in_stellar_code = donor.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]                
        accretor_in_stellar_code = accretor.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]                
    
        #no additional mass and Jspin loss from merged object for now
        J_spin_donor_previous = self.spin_angular_momentum(donor)
        J_spin_accretor_previous = self.spin_angular_momentum(accretor)
        J_orbit = self.orbital_angular_momentum(bs)
        J_spin_new = J_spin_donor_previous + J_spin_accretor_previous + J_orbit
    
        #merger
        donor_in_stellar_code.merge_with_other_star(accretor_in_stellar_code) 
        self.channel_from_stellar.copy_attributes(["age", "mass","envelope_mass", "core_mass", "radius", "core_radius", "convective_envelope_radius",  "convective_envelope_mass", "stellar_type", "luminosity", "wind_mass_loss_rate", "temperature"]) #"gyration_radius_sq"                           
              
        donor.moment_of_inertia_of_star = self.moment_of_inertia(donor)        
    
        #assuming conservation of total angular momentum of the inner binary
        spin_angular_frequency = J_spin_new / donor.moment_of_inertia_of_star                
        critical_spin_angular_frequency = np.sqrt(constants.G * donor.mass/donor.radius**3)
        donor.spin_angular_frequency = min(spin_angular_frequency, critical_spin_angular_frequency)

            
        self.stellar_code.particles.remove_particle(accretor)
        accretor.mass = 0|units.MSun # necessary for adjust_system_after_ce_in_inner_binary
    
        #adjust outer orbit, needs to be before the system becomes a binary
        #and copy to inner orbit 
        # weird structure necessary for secular code -> outer orbit is redundant
        adjust_system_after_ce_in_inner_binary(bs, self)                    
        copy_outer_orbit_to_inner_orbit(bs, self)
        copy_outer_star_to_accretor(self)
        #functions are skipped in binaries, needs to be checked if this works well
        
        self.secular_code.parameters.ignore_tertiary = True
        self.secular_code.parameters.check_for_dynamical_stability = False
        self.secular_code.parameters.check_for_outer_collision = False
        self.secular_code.parameters.check_for_outer_RLOF = False

        bs.bin_type = bin_type['collision']         
        self.save_snapshot() # just to note that it the system has merged
    
        self.check_for_RLOF()       
        if self.has_donor():
            print(self.triple.child2.child1.mass, self.triple.child2.child2.mass, self.triple.child2.semimajor_axis, self.triple.child2.eccentricity, self.triple.child2.child1.is_donor, self.triple.child2.child2.is_donor)
            print(self.triple.child1.mass, self.triple.semimajor_axis, self.triple.eccentricity, self.triple.child1.is_donor)
            print('after adjust_triple_after_ce_in_inner_binary: RLOF')
            exit(1)
            
        donor.is_donor = False
        bs.is_stable = True
        bs.bin_type = bin_type['detached']

        donor.spin_angular_frequency = corotating_spin_angular_frequency_binary(bs.semimajor_axis, bs.child1.mass, bs.child2.mass)


def perform_inner_merger(bs, donor, accretor, self):
    if REPORT_BINARY_EVOLUTION:
        print('Merger in inner binary through common envelope phase')

    donor_in_stellar_code = donor.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]                
    accretor_in_stellar_code = accretor.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]                
    
    #no additional mass and Jspin loss from merged object for now
    J_spin_donor_previous = self.spin_angular_momentum(donor)
    J_spin_accretor_previous = self.spin_angular_momentum(accretor)
    J_orbit = self.orbital_angular_momentum(bs)
    J_spin_new = J_spin_donor_previous + J_spin_accretor_previous + J_orbit
            
    #merger
    donor_in_stellar_code.merge_with_other_star(accretor_in_stellar_code) 
    self.channel_from_stellar.copy_attributes(["age", "mass","envelope_mass", "core_mass", "radius", "core_radius", "convective_envelope_radius",  "convective_envelope_mass", "stellar_type", "luminosity", "wind_mass_loss_rate", "temperature"]) #"gyration_radius_sq"                           
    
    donor.moment_of_inertia_of_star = self.moment_of_inertia(donor)        
    
    #assuming conservation of total angular momentum of the inner binary
    spin_angular_frequency = J_spin_new / donor.moment_of_inertia_of_star                
    critical_spin_angular_frequency = np.sqrt(constants.G * donor.mass/donor.radius**3)
    donor.spin_angular_frequency = min(spin_angular_frequency, critical_spin_angular_frequency)
        
    self.stellar_code.particles.remove_particle(accretor)
    accretor.mass = 0|units.MSun # necessary for adjust_system_after_ce_in_inner_binary
            
    #adjust outer orbit, needs to be before the system becomes a binary
    #and copy to inner orbit 
    # weird structure necessary for secular code -> outer orbit is redundant

    adjust_system_after_ce_in_inner_binary(bs, self)                    
    copy_outer_orbit_to_inner_orbit(bs, self)
    copy_outer_star_to_accretor(self)
    #functions are skipped in binaries, needs to be checked if this works well
    
    self.secular_code.parameters.ignore_tertiary = True
    self.secular_code.parameters.check_for_dynamical_stability = False
    self.secular_code.parameters.check_for_outer_collision = False
    self.secular_code.parameters.check_for_outer_RLOF = False
    bs.bin_type = bin_type['merger']         
    self.save_snapshot() # just to note that it the system has merged

    print(self.secular_code.give_roche_radii(self.triple),)
    print(roche_radius(self.triple.child2, self.triple.child2.child1, self), roche_radius(self.triple.child2, self.triple.child2.child2,  self))

    print(donor.spin_angular_frequency, corotating_spin_angular_frequency_binary(bs.semimajor_axis, bs.child1.mass, bs.child2.mass), critical_spin_angular_frequency)
#    donor.spin_angular_frequency = corotating_spin_angular_frequency_binary(bs.semimajor_axis, bs.child1.mass, bs.child2.mass)



def common_envelope_efficiency(donor, accretor):
    return const_common_envelope_efficiency

def envelope_structure_parameter(donor):
    return const_envelope_structure_parameter
    
def common_envelope_efficiency_gamma(donor, accretor):
    return const_common_envelope_efficiency_gamma
    
    

# ang.mom balance: \Delta J = \gamma * J * \Delta M / M
# See Eq. 5 of Nelemans VYPZ 2000, 360, 1011 A&A
def common_envelope_angular_momentum_balance(bs, donor, accretor, self):
    if REPORT_FUNCTION_NAMES:
        print('Common envelope angular momentum balance')

    if REPORT_BINARY_EVOLUTION:
        if bs.eccentricity > 0.05:
            print('gamma common envelope in eccentric binary')
        print('Before common envelope angular momentum balance' )
        self.print_binary(bs) 

    bs.bin_type = bin_type['common_envelope_angular_momentum_balance']
    self.save_snapshot()        

    gamma = common_envelope_efficiency_gamma(donor, accretor)
    J_init = np.sqrt(bs.semimajor_axis) * (donor.mass * accretor.mass) / np.sqrt(donor.mass + accretor.mass) * np.sqrt(1-bs.eccentricity**2)
    J_f_over_sqrt_a_new = (donor.core_mass * accretor.mass) / np.sqrt(donor.core_mass + accretor.mass)
    J_lost = gamma * donor.envelope_mass * J_init/(donor.mass + accretor.mass)
    sqrt_a_new = max(0.|units.RSun**0.5, (J_init -J_lost)/J_f_over_sqrt_a_new)
    a_new = pow(sqrt_a_new, 2)

    Rl_donor_new = roche_radius_dimensionless(donor.core_mass, accretor.mass)*a_new
    Rl_accretor_new = roche_radius_dimensionless(accretor.mass, donor.core_mass)*a_new    
    if REPORT_BINARY_EVOLUTION:
        print('donor:', donor.radius, donor.core_radius, Rl_donor_new)
        print('accretor:', accretor.radius, accretor.core_radius, Rl_accretor_new)
       
    if (donor.core_radius > Rl_donor_new) or (accretor.radius > Rl_accretor_new):
        perform_inner_merger(bs, donor, accretor, self)                                                           
    else:
        donor_in_stellar_code = donor.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]
        #reduce_mass not subtrac mass, want geen adjust_donor_radius
        #check if star changes type     
        donor_in_stellar_code.change_mass(-1*donor.envelope_mass, 0.|units.yr)    
        self.channel_from_stellar.copy_attributes(["age", "mass","envelope_mass", "core_mass", "radius", "core_radius", "convective_envelope_radius",  "convective_envelope_mass", "stellar_type", "luminosity", "wind_mass_loss_rate", "temperature"]) #"gyration_radius_sq"                           
        donor.moment_of_inertia_of_star = self.moment_of_inertia(donor)        
        accretor.moment_of_inertia_of_star = self.moment_of_inertia(accretor)        

        bs.semimajor_axis = a_new
        bs.eccentricity = minimum_eccentricity

        #set to synchronization
        corotating_frequency = corotating_spin_angular_frequency_binary(a_new, donor.mass, accretor.mass)
        donor.spin_angular_frequency = corotating_frequency
        accretor.spin_angular_frequency = corotating_frequency
        
#        adjusting of stellar system
        adjust_system_after_ce_in_inner_binary(bs, self)                    


    self.check_for_RLOF()       
    if self.has_donor():
        print(self.triple.child2.child1.mass, self.triple.child2.child2.mass, self.triple.child2.semimajor_axis, self.triple.child2.eccentricity, self.triple.child2.child1.is_donor, self.triple.child2.child2.is_donor)
        print(self.triple.child1.mass, self.triple.semimajor_axis, self.triple.eccentricity, self.triple.child1.is_donor)
        print('after adjust_triple_after_ce_in_inner_binary: RLOF')
        exit(1)
        
    donor.is_donor = False
    bs.is_stable = True
    bs.bin_type = bin_type['detached']
    self.instantaneous_evolution = True #skip secular evolution                


    
#Following Webbink 1984
def common_envelope_energy_balance(bs, donor, accretor, self):
    if REPORT_FUNCTION_NAMES:
        print('Common envelope energy balance')

    if REPORT_BINARY_EVOLUTION:
        print('Before common envelope energy balance' )
        self.print_binary(bs) 

    bs.bin_type = bin_type['common_envelope_energy_balance']                
    self.save_snapshot()        

    alpha = common_envelope_efficiency(donor, accretor) 
    lambda_donor = envelope_structure_parameter(donor)

    Rl_donor = roche_radius(bs, donor, self)
    donor_radius = min(donor.radius, Rl_donor)

    orb_energy_new = donor.mass * donor.envelope_mass / (alpha * lambda_donor * donor_radius) + donor.mass * accretor.mass/2/bs.semimajor_axis
    a_new = donor.core_mass * accretor.mass / 2 / orb_energy_new
#    a_new = bs.semimajor_axis * (donor.core_mass/donor.mass) / (1. + (2.*donor.envelope_mass*bs.semimajor_axis/(alpha_lambda*donor_radius*accretor.mass)))
    
    Rl_donor_new = roche_radius_dimensionless(donor.core_mass, accretor.mass)*a_new
    Rl_accretor_new = roche_radius_dimensionless(accretor.mass, donor.core_mass)*a_new    
    if REPORT_BINARY_EVOLUTION:
        print('donor:', donor.radius, donor.core_radius, Rl_donor_new)
        print('accretor:', accretor.radius, accretor.core_radius, Rl_accretor_new)
    
    if (donor.core_radius > Rl_donor_new) or (accretor.radius > Rl_accretor_new):
        perform_inner_merger(bs, donor, accretor, self)
    else:
        donor_in_stellar_code = donor.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]
        #reduce_mass not subtrac mass, want geen adjust_donor_radius
        #check if star changes type     
        donor_in_stellar_code.change_mass(-1*donor.envelope_mass, 0.|units.yr)    
        self.channel_from_stellar.copy_attributes(["age", "mass","envelope_mass", "core_mass", "radius", "core_radius", "convective_envelope_radius",  "convective_envelope_mass", "stellar_type", "luminosity", "wind_mass_loss_rate", "temperature"]) #"gyration_radius_sq"                           
        donor.moment_of_inertia_of_star = self.moment_of_inertia(donor)        
        accretor.moment_of_inertia_of_star = self.moment_of_inertia(accretor)        

        bs.semimajor_axis = a_new
        bs.eccentricity = minimum_eccentricity

        #set to synchronization
        corotating_frequency = corotating_spin_angular_frequency_binary(a_new, donor.mass, accretor.mass)
        donor.spin_angular_frequency = corotating_frequency
        accretor.spin_angular_frequency = corotating_frequency

#        adjusting of stellar system
        adjust_system_after_ce_in_inner_binary(bs, self)                    

    self.check_for_RLOF()       
    if self.has_donor():
        print(self.triple.child2.child1.mass, self.triple.child2.child2.mass, self.triple.child2.semimajor_axis, self.triple.child2.eccentricity, self.triple.child2.child1.is_donor, self.triple.child2.child2.is_donor)
        print(self.triple.child1.mass, self.triple.semimajor_axis, self.triple.eccentricity, self.triple.child1.is_donor)
        print('after adjust_triple_after_ce_in_inner_binary: RLOF')
        exit(1)
        
    donor.is_donor = False
    bs.is_stable = True
    bs.bin_type = bin_type['detached']
    self.instantaneous_evolution = True #skip secular evolution                
            

# See appendix of Nelemans YPZV 2001, 365, 491 A&A
def double_common_envelope_energy_balance(bs, donor, accretor, self):
    if REPORT_FUNCTION_NAMES:
        print('Double common envelope energy balance')

    if REPORT_BINARY_EVOLUTION:
        print('Before double common envelope energy balance' )
        self.print_binary(bs) 

    bs.bin_type = bin_type['double_common_envelope']                
    self.save_snapshot()        

    alpha = common_envelope_efficiency(donor, accretor)
    lambda_donor = envelope_structure_parameter(donor) 
    lambda_accretor = envelope_structure_parameter(accretor)

    Rl_donor = roche_radius(bs, donor, self)
    donor_radius = min(donor.radius, Rl_donor)
    accretor_radius = accretor.radius
    
    orb_energy_new = donor.mass * donor.envelope_mass / (alpha * lambda_donor * donor_radius) + accretor.mass * accretor.envelope_mass / (alpha * lambda_accretor * accretor_radius) + donor.mass * accretor.mass/2/bs.semimajor_axis
    a_new = donor.core_mass * accretor.core_mass / 2 / orb_energy_new

    Rl_donor_new = roche_radius_dimensionless(donor.core_mass, accretor.core_mass)*a_new
    Rl_accretor_new = roche_radius_dimensionless(accretor.core_mass, donor.core_mass)*a_new    
    if REPORT_BINARY_EVOLUTION:
        print('donor:', donor.radius, donor.core_radius, Rl_donor_new)
        print('accretor:', accretor.radius, accretor.core_radius, Rl_accretor_new)
    
    if (donor.core_radius > Rl_donor_new) or (accretor.core_radius > Rl_accretor_new):
        perform_inner_merger(bs, donor, accretor, self)
    else:
        #reduce_mass not subtrac mass, want geen adjust_donor_radius
        #check if star changes type     

        donor_in_stellar_code = donor.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]
        donor_in_stellar_code.change_mass(-1*donor.envelope_mass, 0.|units.yr)    
        accretor_in_stellar_code = accretor.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]
        accretor_in_stellar_code.change_mass(-1*accretor.envelope_mass, 0.|units.yr)    
        self.channel_from_stellar.copy_attributes(["age", "mass","envelope_mass", "core_mass", "radius", "core_radius", "convective_envelope_radius",  "convective_envelope_mass", "stellar_type", "luminosity", "wind_mass_loss_rate", "temperature"]) #"gyration_radius_sq"                           
        donor.moment_of_inertia_of_star = self.moment_of_inertia(donor)        
        accretor.moment_of_inertia_of_star = self.moment_of_inertia(accretor)        

        bs.semimajor_axis = a_new
        bs.eccentricity = minimum_eccentricity

        #set to synchronization
        corotating_frequency = corotating_spin_angular_frequency_binary(a_new, donor.mass, accretor.mass)
        donor.spin_angular_frequency = corotating_frequency
        accretor.spin_angular_frequency = corotating_frequency

#        adjusting of stellar system
        adjust_system_after_ce_in_inner_binary(bs, self)                    

            
    self.check_for_RLOF()       
    if self.has_donor():
        print(self.triple.child2.child1.mass, self.triple.child2.child2.mass, self.triple.child2.semimajor_axis, self.triple.child2.eccentricity, self.triple.child2.child1.is_donor, self.triple.child2.child2.is_donor)
        print(self.triple.child1.mass, self.triple.semimajor_axis, self.triple.eccentricity, self.triple.child1.is_donor)
        print('after adjust_triple_after_ce_in_inner_binary: RLOF')            
        exit(1)
        
    donor.is_donor = False
    bs.is_stable = True
    bs.bin_type = bin_type['detached']
    self.instantaneous_evolution = True #skip secular evolution                


def common_envelope_phase(bs, donor, accretor, self):
    if REPORT_FUNCTION_NAMES:
        print('Common envelope phase', which_common_envelope)
        print('donor:', donor.stellar_type)
        print('accretor:', accretor.stellar_type)

    if donor.stellar_type not in stellar_types_giants and accretor.stellar_type not in stellar_types_giants:
#        possible options: MS+MS, MS+remnant, remnant+remnant,
#                          HeMS+HeMS, HeMS+MS, HeMS+remnant
        bs.bin_type = bin_type['common_envelope']                
        self.save_snapshot()        
        perform_inner_merger(bs, donor, accretor, self)                                              

        self.check_for_RLOF()       
        if self.has_donor():
            print(self.triple.child2.child1.mass, self.triple.child2.child2.mass, self.triple.child2.semimajor_axis, self.triple.child2.eccentricity, self.triple.child2.child1.is_donor, self.triple.child2.child2.is_donor)
            print(self.triple.child1.mass, self.triple.semimajor_axis, self.triple.eccentricity, self.triple.child1.is_donor)
            print(self.triple.child2.child1.radius, self.triple.child2.child2.radius,self.triple.child1.radius)
            print(self.secular_code.give_roche_radii(self.triple))
            print('binary Roche lobe radii:', roche_radius(bs, bs.child1, self), roche_radius(bs, bs.child2, self))
            print('after adjust_triple_after_ce_in_inner_binary: RLOF')
            exit(1)
            
        donor.is_donor = False
        bs.is_stable = True
        bs.bin_type = bin_type['detached']
        self.instantaneous_evolution = True #skip secular evolution                

        return
    

        
    if which_common_envelope == 0:
        if donor.stellar_type in stellar_types_giants and accretor.stellar_type in stellar_types_giants:
           double_common_envelope(bs, donor, accretor, self)
        else:
            common_envelope_energy_balance(bs, donor, accretor, self)
    elif which_common_envelope == 1:
        if donor.stellar_type in stellar_types_giants and accretor.stellar_type in stellar_types_giants:
            double_common_envelope(bs, donor, accretor, self)
        else:
            common_envelope_angular_momentum_balance(bs, donor, accretor, self)
    elif which_common_envelope == 2:
        Js_d = self.spin_angular_momentum(donor)
        Js_a = self.spin_angular_momentum(accretor)        
        Jb = self.orbital_angular_momentum(bs)
        Js = max(Js_d, Js_a)
#        print("Darwin Riemann instability? donor/accretor:", Js_d, Js_a, Jb, Jb/3.)
        if donor.stellar_type in stellar_types_giants and accretor.stellar_type in stellar_types_giants:
            #giant+giant
            double_common_envelope_energy_balance(bs, donor, accretor, self)
        elif donor.stellar_type in stellar_types_compact_objects or accretor.stellar_type in stellar_types_compact_objects:
            #giant+remnant
            common_envelope_energy_balance(bs, donor, accretor, self)
        elif Js >= Jb/3. :            
            #darwin riemann instability
            common_envelope_energy_balance(bs, donor, accretor, self)
        else:
            #giant+normal(non-giant, non-remnant)
            common_envelope_angular_momentum_balance(bs, donor, accretor, self)   



def contact_system(bs, star1, star2, self):
    if REPORT_FUNCTION_NAMES:
        print("Contact system")

    bs.bin_type = bin_type['contact']                
    self.save_snapshot()        

    #for now no W Ursae Majoris evolution
    #so for now MS-MS contact binaries merge in common_envelope_phase
    #if stable mass transfer is implemented, then also the timestep needs to be adjusted
    if star1.mass >= star2.mass:
        common_envelope_phase(bs, star1, star2, self)  
    else:
        common_envelope_phase(bs, star2, star1, self)  

def adiabatic_expansion_due_to_mass_loss(a_i, Md_f, Md_i, Ma_f, Ma_i):

    d_Md = Md_f - Md_i #negative mass loss rate
    d_Ma = Ma_f - Ma_i #positive mass accretion rate  

    Mt_f = Md_f + Ma_f
    Mt_i = Md_i + Ma_i

    if d_Md < 0|units.MSun and d_Ma >= 0|units.MSun:
        eta = d_Ma / d_Md
        a_f = a_i * ((Md_f/Md_i)**eta * (Ma_f/Ma_i))**-2 * Mt_i/Mt_f
        return a_f
    return a_i
   
       
def adjust_system_after_ce_in_inner_binary(bs, self):
    # Assumption: Unstable mass transfer (common-envelope phase) in the inner binary, affects the outer binary as a wind. 
    # Instanteneous effect
    if REPORT_FUNCTION_NAMES:
        print('Adjust system after ce in inner binary')

    if self.is_triple():
        M_com_after_ce = self.get_mass(bs)
        M_com_before_ce = bs.previous_mass
        
        if self.triple.child1.is_star:
            tertiary_star = self.triple.child1
        else:
            tertiary_star = self.triple.child2 
        # accretion_efficiency
        M_accretor_before_ce = tertiary_star.mass 
        M_accretor_after_ce = tertiary_star.mass 
        
        a_new = adiabatic_expansion_due_to_mass_loss(self.triple.semimajor_axis, M_com_after_ce, M_com_before_ce, M_accretor_after_ce, M_accretor_before_ce)
        self.triple.semimajor_axis = a_new
        print('outer orbit', a_new)
    

# nice but difficult to update self.triple       
#    system = bs
#    while True:
#        try:    
#            system = system.parent
#            if not system.child1.is_star and system.child2.is_star:
#                system = adjust_triple_after_ce_in_inner_binary(system, system.child1, system.child2, self)                
#            elif not system.child2.is_star and system.child1.is_star:
#                system = adjust_triple_after_ce_in_inner_binary(system, system.child2, system.child1, self)                            
#            else:
#                print('adjust_system_after_ce_in_inner_binary: type of system unknown')
#                exit(2)
#                                        
#        except AttributeError:
#            #when there is no parent
#            break
#


def stable_mass_transfer(bs, donor, accretor, self):
    # orbital evolution is being taken into account in secular_code        
    if REPORT_FUNCTION_NAMES:
        print('Stable mass transfer')

    if bs.bin_type != bin_type['stable_mass_transfer']:
        bs.bin_type = bin_type['stable_mass_transfer']                
        self.save_snapshot()        
    else:
        bs.bin_type = bin_type['stable_mass_transfer']                

    self.secular_code.parameters.check_for_inner_RLOF = False
    self.secular_code.parameters.include_spin_radius_mass_coupling_terms_star1 = False
    self.secular_code.parameters.include_spin_radius_mass_coupling_terms_star2 = False

    Md = donor.mass
    Ma = accretor.mass
    
    dt = self.time - self.previous_time
    dm_desired = bs.mass_transfer_rate * dt
    if REPORT_FUNCTION_NAMES:
        print(bs.mass_transfer_rate, dt, dm_desired)
    donor_in_stellar_code = donor.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]
    donor_in_stellar_code.change_mass(dm_desired, dt)
    
    # dm != dm_desired e.g. when the envelope of the star becomes empty
    dm = donor_in_stellar_code.mass - Md
    bs.part_dt_mt = 1.
    if dm - dm_desired > numerical_error|units.MSun:
#        print('WARNING:the envelope is empty, mass transfer rate should be lower or dt should be smaller... ')
        bs.part_dt_mt = dm/dm_desired
        
    # there is an implicit assumption in change_mass that the accreted mass is of solar composition (hydrogen)
    accretor_in_stellar_code = accretor.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]
#    accretor_in_stellar_code.change_mass(dm, dt)
    # for now, only conservative mass transfer   
    accretor_in_stellar_code.change_mass(-1.*dm, -1.*dt)
    #if you want seba to determine the accretion efficiency, use 
    #accretor_in_stellar_code.change_mass(-1.*dm, dt)
    #note doesnt work perfectly, as seba is oblivious to the roche lobe radius
    

    #to adjust radius to mass loss and increase  
    self.stellar_code.evolve_model(self.time)
    self.channel_from_stellar.copy_attributes(["age", "mass","envelope_mass", "core_mass", "radius", "core_radius", "convective_envelope_radius",  "convective_envelope_mass", "stellar_type", "luminosity", "wind_mass_loss_rate", "temperature"]) #"gyration_radius_sq"  
    self.update_stellar_parameters()
            
    Md_new = donor.mass
    Ma_new = accretor.mass
    accretion_efficiency = (Ma_new-Ma)/(Md-Md_new)
    if abs(accretion_efficiency - 1.0) > numerical_error and abs(Md-Md_new - -1.*(Ma-Ma_new)) > numerical_error |units.MSun:
        print('stable_mass_transfer: non conservative mass transfer')
        print(Md, Ma, donor.previous_mass, accretor.previous_mass)
        print(Md_new, Ma_new, Md-Md_new, Ma-Ma_new, accretion_efficiency)
        print(donor.stellar_type, accretor.stellar_type)
        exit(1)
        
    bs.accretion_efficiency_mass_transfer = accretion_efficiency

    corotation_spin = corotating_spin_angular_frequency_binary(bs.semimajor_axis, donor.mass, accretor.mass)
    donor.spin_angular_frequency = corotation_spin
    accretor.spin_angular_frequency = corotation_spin


    
def semi_detached(bs, donor, accretor, self):
#only for binaries (consisting of two stars)
    if REPORT_FUNCTION_NAMES:
        print('Semi-detached')
        print(bs.semimajor_axis, donor.mass, accretor.mass, donor.stellar_type, accretor.stellar_type)
        

    if bs.is_stable:
        stable_mass_transfer(bs, donor, accretor, self)
        #adjusting triple is done in secular evolution code
    else:        
        common_envelope_phase(bs, donor, accretor, self)
           
    #possible problem if companion or tertiary accretes significantly from this
#    self.update_previous_stellar_parameters() #previous_mass, previous_radius for safety check
#-------------------------

#-------------------------
#functions for mass transfer in a multiple / triple

def triple_stable_mass_transfer(bs, donor, accretor, self):
    # orbital evolution is being taken into account in secular_code        
    if REPORT_FUNCTION_NAMES:
        print('Triple stable mass transfer')

    if bs.bin_type != bin_type['stable_mass_transfer']:
        bs.bin_type = bin_type['stable_mass_transfer']                
        self.save_snapshot()        
    else:
        bs.bin_type = bin_type['stable_mass_transfer']                
    
    #implementation is missing

def triple_mass_transfer(bs, donor, accretor, self):
#only for stellar systems consisting of a star and a binary
    if REPORT_FUNCTION_NAMES:
        print('Triple mass transfer')
        bs.semimajor_axis, donor.mass, self.get_mass(accretor), donor.stellar_type


    if bs.is_stable:
        triple_stable_mass_transfer(bs, donor, accretor, self)
        
        # possible the outer binary needs part_dt_mt as well. 
        #adjusting triple is done in secular evolution code
    else:        
        if REPORT_FUNCTION_NAMES:
            print('triple_mass_transfer: unstable mass transfer in outer binary')
        bs.bin_type = bin_type['common_envelope_energy_balance']                
        self.save_snapshot()        
        
        #implementation is missing
        #snapshot

#-------------------------

#-------------------------
#Functions for detached evolution
## Calculates stellar wind velocoty.
## Steller wind velocity is 2.5 times stellar escape velocity
#def wind_velocity(star):
#    v_esc2 = constants.G * star.mass / star.radius
#    return 2.5*np.sqrt(v_esc2)
#}
#
#
## Bondi, H., and Hoyle, F., 1944, MNRAS 104, 273 (wind accretion.
## Livio, M., Warner, B., 1984, The Observatory 104, 152.
#def accretion_efficiency_from_stellar_wind(accretor, donor):
#velocity needs to be determined -> velocity average?
# why is BH dependent on ecc as 1/np.sqrt(1-e**2)

#    alpha_wind = 0.5
#    v_wind = wind_velocity(donor)
#    acc_radius = (constants.G*accretor.mass)**2/v_wind**4
#    
#    wind_acc = alpha_wind/np.sqrt(1-bs.eccentricity**2) / bs.semimajor_axis**2
#    v_factor = 1/((1+(velocity/v_wind)**2)**3./2.)
#    mass_fraction = acc_radius*wind_acc*v_factor
#
#    print('mass_fraction:', mass_fraction)
##    mass_fraction = min(0.9, mass_fraction)
#



def detached(bs, self):
    # orbital evolution is being taken into account in secular_code        
    if REPORT_FUNCTION_NAMES:
        print('Detached')

    if bs.bin_type == bin_type['detached'] or bs.bin_type == bin_type['unknown']:
        bs.bin_type = bin_type['detached']
    else:
        bs.bin_type = bin_type['detached']
        self.save_snapshot()        
    
    # wind mass loss is done by stellar_code
    # wind accretion here:
    # update accretion efficiency of wind mass loss
    if self.is_binary(bs):
            
        bs.accretion_efficiency_wind_child1_to_child2 = 0.0
        bs.accretion_efficiency_wind_child2_to_child1 = 0.0

#        child1_in_stellar_code = bs.child1.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]
#        child2_in_stellar_code = bs.child2.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]
#
#        dt = self.time - self.previous_time
#        dm_child1_to_child2 = -1 * child1.wind_mass_loss_rate * bs.accretion_efficiency_wind_child1_to_child2 * dt
#        child2_in_stellar_code.change_mass(dm_child1_to_child2, -1*dt)
#        dm_child12to_child1 = -1 * child2.wind_mass_loss_rate * bs.accretion_efficiency_wind_child2_to_child1 * dt
#        child1_in_stellar_code.change_mass(dm_child2_to_child1, -1*dt)
# check if this indeed is accreted conservatively        


    elif bs.child1.is_star and self.is_binary(bs.child2):
        #Assumption: an inner binary is not effected by wind from an outer star
        bs.accretion_efficiency_wind_child1_to_child2 = 0.0

        bs.accretion_efficiency_wind_child2_to_child1 = 0.0
        
#        child1_in_stellar_code = bs.child1.as_set().get_intersecting_subset_in(self.stellar_code.particles)[0]
#        dt = self.time - self.previous_time
        
         #effect of wind from bs.child2.child1 onto bs.child1
#        mtr_w_in1_1 =  bs.child2.child1.wind_mass_loss_rate * (1-bs.child2.accretion_efficiency_wind_child1_to_child2)       
#        beta_w_in1_1 = 0.0
#        dm_in1_1 = -1 * mtr_w_in1_1 * beta_w_in1_1 * dt
#        
         #effect of wind from bs.child2.child2 onto bs.child1
#        mtr_w_in2_1 =  bs.child2.child2.wind_mass_loss_rate * (1-bs.child2.accretion_efficiency_wind_child2_to_child1)       
#        beta_w_in2_1 = 0.0
#        dm_in2_1 = -1 * mtr_w_in2_1 * beta_w_in2_1 * dt
#                    
#        dm = dm_in1_1 + dm_in2_1  
#        mtr = mtr_w_in1_1 + mtr_w_in2_1)


         #effect of mass transfer in the binary bs.child2 onto bs.child1
#        if bs.child2.child1.is_donor and bs.child2.child2.is_donor:
#            print('contact binary in detached...')
#            exit(1)
#        elif bs.child2.child1.is_donor or bs.child2.child2.is_donor:
#            #Assumption:
#            #Stable mass transfer in the inner binary, affects the outer binary as a wind.
#            mtr_rlof_in_1 = bs.child2.mass_transfer_rate * (1-bs.child2.accretion_efficiency_mass_transfer)
#            beta_rlof_in_1 = 0.0
#            dm_rlof_in_1 = -1 * mtr_rlof_in_1 * beta_rlof_in_1 * dt
#            dm += dm_rlof_in_1
#            mtr += mtr_rlof_in_1 

#        bs.accretion_efficiency_wind_child2_to_child1 = dm / ( mtr* -1 * dt)
            
#        child1_in_stellar_code.change_mass(dm, dt)
# check if this indeed is accreted conservatively        

    else:
        print('detached: type of system unknown')
        print( bs.child1.is_star, bs.child2.is_star)
        exit(2)                    
              
    #reset parameters after mass transfer
#    bs.mass_transfer_rate = 0.0 | units.MSun/units.yr

#    return bs
#-------------------------

#-------------------------
def resolve_binary_interaction(bs, self):
   if REPORT_FUNCTION_NAMES:
        print('Resolve binary interaction')
    
   if not bs.is_star and bs.child1.is_star:
        if REPORT_BINARY_EVOLUTION:
            Rl1 = roche_radius(bs, bs.child1, self)
            print("Check for RLOF:", bs.child1.mass, bs.child1.previous_mass)
            print("Check for RLOF:", Rl1, bs.child1.radius)
                
        if bs.child2.is_star:
            if REPORT_BINARY_EVOLUTION:
                Rl2 = roche_radius(bs, bs.child2, self)
                print("Check for RLOF:", bs.child2.mass, bs.child2.previous_mass)
                print("Check for RLOF:", Rl2, bs.child2.radius)
                
            if bs.child1.is_donor or bs.child2.is_donor:
                print("start mt")
                exit(0)
                
                
                

            if bs.child1.is_donor and bs.child2.is_donor:
                contact_system(bs, bs.child1, bs.child2, self)
            elif bs.child1.is_donor and not bs.child2.is_donor:
                semi_detached(bs, bs.child1, bs.child2, self)
            elif not bs.child1.is_donor and bs.child2.is_donor:
                semi_detached(bs, bs.child2, bs.child1, self)
            else:
                detached(bs, self)
                                        
        elif not bs.child2.is_star:
            if REPORT_BINARY_EVOLUTION:
                print(self.get_mass(bs), bs.child1.mass, self.get_mass(bs.child2))
    
            if bs.child1.is_donor:
                if bs.child2.child1.is_donor or bs.child2.child2.is_donor:
                    triple_mass_transfer(bs, bs.child1, bs.child2, self)
            else:
                detached(bs, self)
                
        else:
            print('resolve binary interaction: type of system unknown')
            print(bs.is_star, bs.child1.is_star, bs.child2.is_star)
            exit(2) 
                               
   else:
        print('resolve binary interaction: type of system unknown')
        print(bs.is_star, bs.child1.is_star, bs.child1.is_donor)
        exit(2)      
        
#-------------------------
        
#-------------------------
#functions for the stability of mass transfer
def q_crit(star):
    #following Hurley, Tout, Pols 2002
    if star.stellar_type in [9]|units.stellar_type:
#    if star.stellar_type in [8,9]|units.stellar_type:
        return 0.784
    elif star.stellar_type in [3,4,5,6]|units.stellar_type:
        x=0.3
        return (1.67-x+2*(star.core_mass/star.mass)**5)/2.13
    elif star.stellar_type == 0|units.stellar_type:
        return 0.695
    elif star.stellar_type == 1|units.stellar_type:
        return 1./0.625 #following claeys et al. 2014 based on de mink et al 2007
    elif star.stellar_type in stellar_types_compact_objects:#eventhough ns & bh shouldn't be donors... 
        return 0.628
    else: #stellar type 2, and 8
        return 3 #SILVIA this seems awfully high for hg
        
    

def mass_transfer_stability(binary, self):
    if REPORT_FUNCTION_NAMES:
        print('Mass transfer stability')

    if self.is_binary(binary):
        Js_1 = self.spin_angular_momentum(binary.child1)
        Js_2 = self.spin_angular_momentum(binary.child2)        
        Jb = self.orbital_angular_momentum(binary)
        if REPORT_MASS_TRANSFER_STABILITY:
            print("Mass transfer stability: Binary ")
            print(binary.semimajor_axis, binary.child1.mass, binary.child2.mass, binary.child1.stellar_type, binary.child2.stellar_type)
            print(binary.child1.spin_angular_frequency, binary.child2.spin_angular_frequency)
            print(Js_1, Js_2, Jb, Jb/3.   )
        
        Js = max(Js_1, Js_2)
        if Js >= Jb/3. :
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Darwin Riemann instability", Js_1, Js_2, Jb, Jb/3.)
            mt1 = -1.* binary.child1.mass / dynamic_timescale(binary.child1)
            mt2 = -1.* binary.child2.mass / dynamic_timescale(binary.child2)  
            binary.mass_transfer_rate = min(mt1, mt2) # minimum because mt<0
            binary.is_stable = False
            
        elif binary.child1.is_donor and binary.child2.is_donor:
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Contact")
            mt1 = -1.* binary.child1.mass / dynamic_timescale(binary.child1)
            mt2 = -1.* binary.child2.mass / dynamic_timescale(binary.child2)  
            binary.mass_transfer_rate = min(mt1, mt2) # minimum because mt<0
            binary.is_stable = False    

        elif binary.child1.is_donor and binary.child1.mass > binary.child2.mass*q_crit(binary.child1):
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Mdonor1>Macc*q_crit ")
            binary.mass_transfer_rate = -1.* binary.child1.mass / dynamic_timescale(binary.child1)
            binary.is_stable = False
        elif binary.child2.is_donor and binary.child2.mass > binary.child1.mass*q_crit(binary.child2):
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Mdonor2>Macc*q_crit ")
            binary.mass_transfer_rate= -1.* binary.child2.mass / dynamic_timescale(binary.child2) 
            binary.is_stable = False
            
            
        elif binary.child1.is_donor:
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Donor1 stable ")
            binary.mass_transfer_rate = -1.* binary.child1.mass / mass_transfer_timescale(binary, binary.child1)         
            binary.is_stable = True
        elif binary.child2.is_donor:
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Donor2 stable")
            binary.mass_transfer_rate = -1.* binary.child2.mass / mass_transfer_timescale(binary, binary.child2)         
            binary.is_stable = True
            
        else:     
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Detached")
            #detached system
            mt1 = -1.* binary.child1.mass / mass_transfer_timescale(binary, binary.child1)
            mt2 = -1.* binary.child2.mass / mass_transfer_timescale(binary, binary.child2)  
            binary.mass_transfer_rate = min(mt1, mt2) # minimum because mt<0
            binary.is_stable = True

    else:
        if binary.child1.is_star and not binary.child2.is_star:
            star = binary.child1
            companion = binary.child2
        elif binary.child2.is_star and not binary.child1.is_star:
            star = binary.child2
            companion = binary.child1
        else: 
            print('resolve binary interaction: type of system unknown')
            print(bs.is_star, bs.child1.is_star, bs.child2.is_star)
            exit(2) 

        
            
        if REPORT_MASS_TRANSFER_STABILITY:
            print("Mass transfer stability: Binary ")
            print(binary.semimajor_axis, self.get_mass(companion), star.mass, star.stellar_type)
    
        Js = self.spin_angular_momentum(star)
        Jb = self.orbital_angular_momentum(binary)
        
        if Js >= Jb/3. :
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Darwin Riemann instability: ", Js, Jb, Jb/3.)
            binary.mass_transfer_rate = -1.* star.mass / dynamic_timescale(star)
            binary.is_stable = False          
            
        elif star.is_donor and star.mass > self.get_mass(companion)*q_crit(star):
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Mdonor1>Macc*q_crit")
            binary.mass_transfer_rate = -1.* star.mass / dynamic_timescale(star)
            binary.is_stable = False
            
            
        elif star.is_donor:
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Donor1 stable ")
            binary.mass_transfer_rate = -1.* star.mass / mass_transfer_timescale(binary, star)         
            binary.is_stable = True
            
        else:                     
            if REPORT_MASS_TRANSFER_STABILITY:
                print("Mass transfer stability: Detached")
            #detached system
            binary.mass_transfer_rate = -1.* star.mass / mass_transfer_timescale(binary, star)
            binary.is_stable = True
                        
            
       
       
def mass_transfer_timescale(binary, star):
    if REPORT_FUNCTION_NAMES:
        print('Mass transfer timescale')
    
    if not star.is_star:
        print('mass transfer timescale: type of system unknown')
        print('donor star is not a star')
        exit(2)
    
    #For now thermal timescale donor
    mtt = kelvin_helmholds_timescale(star)
#    mtt = nuclear_evolution_timescale(star)
    return mtt
#-------------------------
        
        
    