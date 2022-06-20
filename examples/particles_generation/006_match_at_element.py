# copyright ############################### #
# This file is part of the Xpart Package.   #
# Copyright (c) CERN, 2021.                 #
# ######################################### #

import json
import numpy as np

import xpart as xp
import xtrack as xt
import xobjects as xo

ctx = xo.context_default
ctx = xo.ContextPyopencl()

# Load machine model (from pymask)
filename = ('../../../xtrack/test_data/lhc_no_bb/line_and_particle.json')
with open(filename, 'r') as fid:
    input_data = json.load(fid)
tracker = xt.Tracker(_context=ctx, line=xt.Line.from_dict(input_data['line']),
                     reset_s_at_end_turn=False)
assert not tracker.iscollective
tracker.line.particle_ref = xp.Particles.from_dict(input_data['particle'])

# Check matching of a one-sigma circle in ip2
r_sigma = 1
theta = np.linspace(0, 2*np.pi, 1000)

at_element = 'ip2'
particles = xp.build_particles(tracker=tracker, _context=ctx,
                   x_norm=r_sigma*np.cos(theta), px_norm=r_sigma*np.sin(theta),
                   scale_with_transverse_norm_emitt=(2.5e-6, 2.5e-6),
                   at_element=at_element)

tw = tracker.twiss(at_elements=[at_element])

particles._move_to(_context=xo.context_default) # To easily do the checks with numpy
assert np.isclose(
    np.sqrt(tw['betx'][0]*2.5e-6/particles.beta0[0]/particles.gamma0[0]),
    np.max(np.abs(particles.x - np.mean(particles.x))), rtol=1e-3, atol=0)
particles._move_to(_context=ctx)

# Check that tracking starts from the right place
tracker.track(particles, turn_by_turn_monitor='ONE_TURN_EBE')
mon = tracker.record_last_track
i_ele_start = tracker.line.element_names.index(at_element)
assert np.all(mon.at_element[:, :i_ele_start] == 0)
assert np.all(mon.at_element[:, i_ele_start] == i_ele_start)
assert np.all(mon.at_element[:, -1] == len(tracker.line.element_names) -1)

# Check that distribution is matched at the end of the turn
tw0 = tracker.twiss(at_elements=[0])
particles._move_to(_context=xo.context_default)
assert np.isclose(
    np.sqrt(tw0['betx'][0]*2.5e-6/particles.beta0[0]/particles.gamma0[0]),
    np.max(np.abs(particles.x - np.mean(particles.x))), rtol=2e-3, atol=0)

# Check multiple turns
at_element = 'ip2'
particles = xp.build_particles(tracker=tracker, _context=ctx,
                   x_norm=r_sigma*np.cos(theta), px_norm=r_sigma*np.sin(theta),
                   scale_with_transverse_norm_emitt=(2.5e-6, 2.5e-6),
                   at_element=at_element)

tw = tracker.twiss(at_elements=[at_element])

particles._move_to(_context=xo.context_default)
assert np.isclose(
    np.sqrt(tw['betx'][0]*2.5e-6/particles.beta0[0]/particles.gamma0[0]),
    np.max(np.abs(particles.x - np.mean(particles.x))), rtol=1e-3, atol=0)
particles._move_to(_context=ctx)

tracker.track(particles, num_turns=3)

tw0 = tracker.twiss(at_elements=[0])
particles._move_to(_context=xo.context_default)
assert np.isclose(
    np.sqrt(tw0['betx'][0]*2.5e-6/particles.beta0[0]/particles.gamma0[0]),
    np.max(np.abs(particles.x - np.mean(particles.x))), rtol=2e-3, atol=0)
assert np.all(particles.at_turn==3)
assert np.allclose(particles.s, 3*tracker.line.get_length(), rtol=0, atol=1e-7)

# Check collective case
import pdb; pdb.set_trace()
line_w_collective = xt.Line.from_dict(input_data['line'], _context=ctx)
for ip in range(8):
    line_w_collective.element_dict[f'ip{ip+1}'].iscollective = True
tracker = xt.Tracker(_context=ctx, line=line_w_collective,
                     reset_s_at_end_turn=False)
assert tracker.iscollective
tracker.line.particle_ref = xp.Particles.from_dict(input_data['particle'])
assert len(tracker._parts) == 16

at_element = 'ip2'
particles = xp.build_particles(tracker=tracker, _context=ctx,
                   x_norm=r_sigma*np.cos(theta), px_norm=r_sigma*np.sin(theta),
                   scale_with_transverse_norm_emitt=(2.5e-6, 2.5e-6),
                   at_element=at_element)

tw = tracker.twiss(at_elements=[at_element])

particles._move_to(_context=xo.context_default)
assert np.isclose(
    np.sqrt(tw['betx'][0]*2.5e-6/particles.beta0[0]/particles.gamma0[0]),
    np.max(np.abs(particles.x - np.mean(particles.x))), rtol=1e-3, atol=0)
particles._move_to(_context=ctx)

tracker.track(particles, num_turns=3)

tw0 = tracker.twiss(at_elements=[0])
particles._move_to(_context=xo.context_default)
assert np.isclose(
    np.sqrt(tw0['betx'][0]*2.5e-6/particles.beta0[0]/particles.gamma0[0]),
    np.max(np.abs(particles.x - np.mean(particles.x))), rtol=2e-3, atol=0)
assert np.all(particles.at_turn==3)
assert np.allclose(particles.s, 3*tracker.line.get_length(), rtol=0, atol=1e-7)

# Check match_at_s
at_element = 'ip6'
particles = xp.build_particles(tracker=tracker, _context=ctx,
                   x_norm=r_sigma*np.cos(theta), px_norm=r_sigma*np.sin(theta),
                   scale_with_transverse_norm_emitt=(2.5e-6, 2.5e-6),
                   at_element=at_element,
                   match_at_s=tracker.line.get_s_position('ip6') + 100
                   )

tw = tracker.twiss(at_elements=[at_element])

particles._move_to(_context=xo.context_default)
assert np.isclose(
    np.sqrt(tw['betx'][0]*2.5e-6/particles.beta0[0]/particles.gamma0[0]),
    np.max(np.abs(particles.x - np.mean(particles.x))), rtol=1e-3, atol=0)
assert np.allclose(particles.s, tw['s'][0], atol=1e-8, rtol=0)

phasex_first_part = np.angle(particles.x[0] / np.sqrt(tw['betx'][0]) -
            1j*(particles.x[0]  * tw['alfx'][0] / np.sqrt(tw['betx'][0]) +
                    particles.px[0] * np.sqrt(tw['betx'][0])))

mu_at_s = tracker.twiss(at_s=tracker.line.get_s_position('ip6') + 100)['mux'][0]
mu_at_element = tracker.twiss(at_elements=[at_element])['mux'][0]

assert np.isclose(phasex_first_part, (mu_at_element - mu_at_s)*2*np.pi,
                  atol=0, rtol=0.02)
particles._move_to(_context=ctx)

tracker.track(particles, num_turns=3)

tw0 = tracker.twiss(at_elements=[0])
particles._move_to(_context=xo.context_default)
assert np.isclose(
    np.sqrt(tw0['betx'][0]*2.5e-6/particles.beta0[0]/particles.gamma0[0]),
    np.max(np.abs(particles.x - np.mean(particles.x))), rtol=2e-3, atol=0)
assert np.all(particles.at_turn==3)
assert np.allclose(particles.s, 3*tracker.line.get_length(), rtol=0, atol=1e-7)

