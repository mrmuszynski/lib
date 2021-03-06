#! /usr/bin/env python3
# H+
#	Title   : orbits.py
#	Author  : Matt Muszynski
#	Date    : 09/04/16
#	Synopsis: Functions for orbit stuff
# 
#
#	$Date$
#	$Source$
#  @(#) $Revision$
#	$Locker$
#
#	Revisions:
#
# H-
# U+
#	Usage   :
#	Example	:
#	Output  :
# U-
# D+
#
# D-
###############################################################################

from numpy import arctan2, dot, sqrt, sin, cos, sinh, cosh, pi, zeros
from numpy import sqrt, linspace, argmin, rad2deg, nan, array, deg2rad
from numpy import hstack, vstack, empty, einsum, ones, logical_and
from util import rx, rz

from numpy.linalg import norm
import pdb

###############################################################################
#
#	anomalies() is used to convert between mean, eccentric, and true anomaly
#		as well was time since perapse.
#
#	INPUTS
#		key
#			a string to tell the function which anomaly you are converting from
#			't' for time since periapse
#			'nu' for true anomaly
#			'M' for mean anomaly
#			'E' for eccentric anomaly
#		value
#			the value for the key that is passed
#			degrees for angles, seconds for time
#		a
#			semimajor axis of the orbit
#		e
#			eccentricity of the orbit
#		[mu]
#			gravitational parameter. By default, this uses the value for the
#			Earth with a satellite of negligible mass mu = 398600.4415
#
#	OUTPUTS
#		a dict of anomalies converted from the value passed in. Keys are the
#		same values that can be passed in. Values are the conversions.
#
#	The funciton is devided into four parts.
#
#	1. Command line checks
#		a. Check that the value entered is a number
#		b. Check that the key entered is a string associated
#		   with one of the anomalies
#
#	2. Conversions (single steps)
#		Convert between anomalies one step at a time so comming math can
#		be shared. We convert in the following order:
#
#		nu <-> E <-> M <-> t
#
#		This gives 6 conversion functions:
#		
#		nu2E(), E2M(), M2t(), t2M(), M2E(), E2nu()
#		
#	3. Conversions (full)
#		For each type of anomaly that can be passed in, convert to all the
#		others.
#		There are four functions here, each of which checks which type
#		of anomaly was passed into the main function, and then chains the 
#		partial conversion functions as appropriate to get to the desired
#		anomaly.
#
#	4. Return anomaly dictionary
#		Call the full conversions once per anomaly, return a dict with
#		strings as keys for each anomaly.
#
#
###############################################################################


def anomalies(key,value,a,e,**kwargs):
	#accept kwarg input for mu. If none is used, use that of Earth
	#with a satellite of negligably small mass.
	try:
		mu = kwargs['mu']
	except:
		mu = 398600.4415 #km^3/s^2

	try:
		silent = kwargs['silent']
	except:
		silent = 0

	#key is string for type of anomaly/time:
	#	'nu' for true anomaly
	#	'E' for eccentric anomaly
	#	'M' for mean anomaly
	#	't' for time since periapse
	#value is the value for the anomaly
	#	radians for angles
	#	seconds for time
	#e is eccentricity (dimensionless)
	#mu is gravitational parameter
	#a is semimajor axis
	#	units should match lenght unit of mu.
	#	398600.4415 km^3/2 for Earth

	import numpy as np
	import sys #so we can exit if the function is called wrong.
	
	###############################
	# PART 1. COMMAND LINE CHECKS #
	###############################

	#check that value is a number
	# if not(isinstance(value, int) or isinstance(value, float)):
	# 	print( '\nImproper call of orbits.anomalies.\n' + \
	# 	'Value must be number\n' + \
	# 	'Example: anomalies(\'nu\',np.pi(),.15,7000)\n')
	# 	sys.exit()

	#check that key is one of the anomalies
	if not(key == 'nu' or key == 'M' or key == 'E' or key == 't'):
		print( '\nImproper call of orbits.anomalies.\n' + \
		'Key must be \'nu\', \'M\', \'E\', or \'t\'\n' + \
		'Example: anomalies(\'nu\',np.pi(),.15,7000)\n')
		sys.exit()
	#calculate period in seconds so we can check if 
	#the time passed is more than an orbit after periapse.
	#
	#if it is, do a modulo to find out how long it is after
	#the most recent periapse.

	period = 2*np.pi*np.sqrt(a**3/mu)
	
	if key == 't' and value >= period:
		if silent == 0:
			print("orbits.anomalies warning: Time passed > period for some values.")
			print("Converting to time since periapse.")
			# print("orbits.anomalies warning: Time passed = " + str(value))
			# print("orbits.anomalies warning: Period = " + str(period))
			# print("orbits.anomalies warning: Finding time since most recent periapse.")
			# print("orbits.anomalies warning: Time since most recent periapse: " + str(value % period))
		value = value % period

	if key != 't':
		value = np.deg2rad(value)

	try:
		truth_val = sum(value >= 2*np.pi)
	except: 
		truth_val = sum([value >= 2*np.pi])

	if key != 't' and truth_val:
		if silent == 0:
			print("orbits.anomalies warning: Some angles greater than 2pi")
			print("orbits.anomalies warning: Performing modulo to get angle < 2pi")
		value = value % (2*np.pi)

	######################################
	# PART 2. CONVERSIONS (single steps) #
	######################################

	#convert true anomaly to eccentric anomaly
	def nu2E(nu):
		#a cancels , so we remove it rather than  
		#make the user pass it in.
		sin_E = (np.sin(nu)*np.sqrt(1-e**2))/(1+e*np.cos(nu))
		cos_E = (e+np.cos(nu))/(1+e*np.cos(nu))
		E = np.arctan2(sin_E,cos_E)
		if E < 0:
			E = E + 2*np.pi
		return E
	#convert eccentric anomaly to mean anomaly
	def E2M(E):
		M = E-e*np.sin(E)
		return M
	#convert mean anomaly to time since periapse
	def M2t(M):
		n = np.sqrt(mu/a**3)
		t = M/n
		return t
	#convert time since periapse to mean anomaly
	def t2M(t):
		n = np.sqrt(mu/a**3) # mean motion
		M = n*t
		return M
	#convert mean anomaly to eccentric anomaly
	def M2E(M):
		#Use Newton-Raphson iteration.
		E = M #initial E
		delta = (M-E+e*np.sin(E))/(1-e*np.cos(E))
		#this wastes a lot of cycles recomputing values
		#where delta is already small. There's probably
		#a smarter way to do this.
		try:
			maxval = max(abs(delta))
		except:
			maxval = abs(delta)

		while maxval > 1e-12:
			delta = (M-E+e*np.sin(E))/(1-e*np.cos(E))
			E = E + delta
			try:
				maxval = max(abs(delta))
			except:
				maxval = abs(delta)
		return E
	#convert eccentric anomaly to true anomaly
	def E2nu(E):
		sin_nu = (np.sin(E)*np.sqrt(1.-e**2.))/(1.-e*np.cos(E))
		cos_nu = (np.cos(E)-e)/(1.-e*np.cos(E))
		nu = np.arctan2(sin_nu,cos_nu)
		try:
			nu[nu < 0] = nu[nu < 0] + 2*np.pi
		except:
			if nu < 0:
				nu = nu + 2*np.pi
		return nu


	##############################
	# PART 3. CONVERSIONS (full) #
	##############################

	#this section converts to nu from whichever value is passed in
	def nu(key,value):
		if key == 'nu':
			nu = value
			return nu
		elif key == 'E':
			E = value
			nu = E2nu(E)
			return nu
		elif key == 'M':
			M = value
			E = M2E(M)
			nu = E2nu(E)
			return nu
		elif key == 't':
			t = value
			M = t2M(t)
			E = M2E(M)
			nu = E2nu(E)
			return nu

	#this section converts to M from whichever value is passed in
	def M(key,value):
		if key == 'nu':
			nu = value
			E = nu2E(nu)
			M = E2M(E)
			return M
		elif key == 'M':
			M = value
			return M
		elif key == 'E':
			E = value
			M = E2M(E)
			return M
		elif key == 't':
			t = value
			M = t2M(t)
			return M

	#this section converts to E from whichever value is passed in
	def E(key,value):
		if key == 'nu':
			nu = value
			E = nu2E(nu)
			return E
		elif key == 'M':
			M = value
			E = M2E(M)
			return E
		elif key == 'E':
			E = value
			return E
		elif key == 't':
			t = value
			M = t2M(t)
			E = M2E(M)
			return E

	#this section converts to t from whichever value is passed in
	def t(key,value):
		if key == 'nu':
			nu = value
			E = nu2E(nu)
			M = E2M(E)
			t = M2t(M)
			return t
		elif key == 'M':
			M = value
			t = M2t(M)
			return t
		elif key == 'E':
			E = value
			M = E2M(E)
			t = M2t(M)
			return t
		elif key == 't':
			t = value
			return t

	#######################
	# PART 4. RETURN DICT #
	#######################
	return {\
	'nu': nu(key,value)*360/(2*np.pi), \
	'M': M(key,value)*360/(2*np.pi), \
	'E': E(key,value)*360/(2*np.pi), \
	't': t(key,value)\
	}

###############################################################################
#
#	rv2coe Translates a 1x3 velocity vector and a 1x3 position
#	vector in cartesian space into the 6 keplerian orbital elements
# 	There are two pairs of identical entries:
#		RAAN and OMEGA (Right ascension of the ascending note)
#		AoP and omega(Argument of Periapse)
#	Also outputs all of the anomalies and time since periapse.
#
#	INPUTS
#		[mu]
#			gravitational parameter. By default, this uses the value for the
#			Earth with a satellite of negligible mass mu = 398600.4415
#	OUTPUTS
#
###############################################################################

def rv2coe (r, v, **kwargs):
	import sys
	import pdb
	#accept kwarg input for mu. If none is used, use that of Earth
	#with a satellite of negligably small mass in km^3/s^2
	try:
		mu = kwargs['mu']
	except:
		mu = 398600.4415
	import numpy as np
	import numpy.linalg as LA

	i = [1,0,0]
	j = [0,1,0]
	k = [0,0,1]

	#find angular momentum vector
	h = np.cross(r,v)

	#i is the angle between h and k
	inc = np.arccos(np.dot(h, k)/LA.norm(h))

	#eccentricity from |(v x h)/mu - rhat|
	e_vector = np.cross(v,h)/mu - r/LA.norm(r)

	e = LA.norm(e_vector)
	#Right ascension of Ascending note
	n = np.cross(k,h)

	n_x = n[0]
	OMEGA = np.arccos(n_x/LA.norm(n))

	if n[1] < 0:
		OMEGA = 2*np.pi-OMEGA

	RAAN = OMEGA

	#Argument of periapse
	n = np.cross(k,h)
	cos_omega = np.dot(n,e_vector)/(LA.norm(n)*LA.norm(e_vector))
	omega = np.arccos(cos_omega)

	if e_vector[2] < 0:
		omega = 2*np.pi-omega

	AoP = omega
	
	#true anomaly
	cos_nu = np.dot(e_vector,r)/(e*LA.norm(r))
	nu = np.arccos(cos_nu)

	if np.dot(r,v) < 0:
		nu = 2*np.pi - nu

	#semimajor axis from vis-viva
	a = (2/LA.norm(r)-np.dot(v,v)/mu)**-1
	r_a = a*(1+e)
	r_p = a*(1-e)

	#have to call this with the mu kwarg in case user passes a different
	#mu than nominal
	anomaly_dict = anomalies('nu',np.rad2deg(nu),a,e,mu=mu,silent=1)

	M = anomaly_dict['M']
	E = anomaly_dict['E']
	t = anomaly_dict['t']

	#flight path angle
	fpa = np.arccos(LA.norm(h)/(LA.norm(r)*LA.norm(v)))

	#specific energy
	epsilon = mu/(2*a)

	return {\
	'a': a, \
	'r_a': r_a, \
	'r_p': r_p, \
	'e': e, \
	'epsilon': epsilon, \
	'i': inc*360/(2*np.pi), \
	'RAAN': RAAN*360/(2*np.pi), \
	'OMEGA': OMEGA*360/(2*np.pi), \
	'AoP': AoP*360/(2*np.pi), \
	'omega': omega*360/(2*np.pi), \
	'nu': nu*360/(2*np.pi), \
	'fpa': fpa*360/(2*np.pi), \
	#these have already been converted to degrees by anomalies()
	'M': M, \
	'E': E, \
	't': t \

	}



#------------------------------------------------------------------
# pqw2ijk() gives the matrix needed to convert from
# 	pqw coordinates (periapse frame) to ijk coordinates (eci frame)
#	This is one of the substeps of going from coe2rv
#
#Reference: lecture 6 ASEN 5050 CU Boulder, Fall 2016
#
#Inputs:
#	OMEGA: Right Ascension of the Ascending Node in radians
#	omega: Argument of Periapse in radians
#	i: inclination in radians
#Outputs:
#	pqw2ijk: a matrix to convert r or v form pqw to ijk
#------------------------------------------------------------------
def pqw2ijk (OMEGA, omega, i):
	import numpy as np
	from util import rx, rz
	#1. Rotate by -OMEGA about z
	#2. Rotate by -i about x
	#3. Rotate by -omega about z
	pqw2ijk = rz(-OMEGA)*rx(-i)*rz(-omega)
	return pqw2ijk

#------------------------------------------------------------------
#
# coe2rv() converts from classical orbital elements to position
#	and velocity vectors in ECI space.
#
#Reference: lecture 6 ASEN 5050 CU Boulder, Fall 2016
#
#Inputs:
#	a: semimajor axis in km
#	e: eccentricity
#	i: inclination in degrees
#	OMEGA: Right Ascension at Ascending Node in degrees
#	omega: Argument of Perigee in degrees
#	nu: true anomaly in degrees
#
#Keywords
#	mu: gravitational parameter. defaults to Earth with a small
#		satellite. in km^3/s^2
#
#Outputs:
#	coe2rv: dict with 2 vectors
#		r_ijk: position vector
#		v_ijk: velocity vector
#------------------------------------------------------------------
def coe2rv(a, e, i, OMEGA, omega, nu, **kwargs):
	#accept kwarg input for mu. If none is used, use that of Earth
	#with a satellite of negligably small mass in km^3/s^2
	try:
		mu = kwargs['mu']
	except:
		mu = 398600.4415

	i = deg2rad(i)
	OMEGA = deg2rad(OMEGA)
	omega = deg2rad(omega)
	nu = deg2rad(nu)
	#define semipameter
	p = a*(1-e**2)

	try:
		length = len(i)
	except:
		length = 1

	#define r in the perifocal plane
	r_pqw = vstack([
		((p*cos(nu))/(1+e*cos(nu))),
		((p*sin(nu))/(1+e*cos(nu))),
		zeros(length)
		])

	#define v in the perifocal plane
	v_pqw = vstack([
		(-sqrt(mu/p)*sin(nu)),
		(sqrt(mu/p)*(e+cos(nu))),
		zeros(length)
		])

	if length == 1:
		pqw2ijk = rz(-OMEGA).dot(rx(-i).dot(rz(-omega)))
		r_ijk = pqw2ijk.dot(r_pqw)
		v_ijk = pqw2ijk.dot(v_pqw)
		X_ijk = vstack([r_ijk,v_ijk]).T[0]
	else:
		#keeping the code for how I used to do it in case the
		#einsum version goes bonkers

		# output = empty((0,6),float)
		# for j in range(0,length):
		# 	pqw2ijk = rz(-OMEGA[j]).dot(rx(-i[j]).dot(rz(-omega[j])))
		# 	r_ijk = pqw2ijk.dot(r_pqw[:,j])
		# 	v_ijk = pqw2ijk.dot(v_pqw[:,j])
		# 	X_ijk = hstack([r_ijk,v_ijk])
		# 	output = vstack([output,X_ijk])

		#this is ugly, but christ is it fast...
		r_tmp = r_pqw.T.reshape(-1,3,1)
		r_tmp = einsum('ijk,ikj->ji',rz(-omega),r_tmp).T.reshape(-1,3,1)
		r_tmp = einsum('ijk,ikj->ji',rx(-i),r_tmp).T.reshape(-1,3,1)
		r_ijk = einsum('ijk,ikj->ji',rz(-OMEGA),r_tmp)

		v_tmp = v_pqw.T.reshape(-1,3,1)
		v_tmp = einsum('ijk,ikj->ji',rz(-omega),v_tmp).T.reshape(-1,3,1)
		v_tmp = einsum('ijk,ikj->ji',rx(-i),v_tmp).T.reshape(-1,3,1)
		v_ijk = einsum('ijk,ikj->ji',rz(-OMEGA),v_tmp)
		X_ijk = vstack([r_ijk,v_ijk]).T
		#NOTE: Probably could have done this with matmul, too. But at
		#least this way I learned something about einsum.

	return X_ijk

#------------------------------------------------------------------
#
# tle2coe() converts a line from a celstrak TLE file into an array
# 	of the classical orbital elements.
#
#Source: http://www.celestrak.com/NORAD/documentation/tle-fmt.asp
#
#------------------------------------------------------------------

def tle2coe(string):
	import numpy as np
	data = string.split()
	#no kwarg for mu since TLEs are only made for small satellites
	#around earth.
	mu = 398600.4415

	#TLEs are stupid, and there's an assumed decimal point in the
	#eccentricity value. Here we make it explicit.
	data[4] = '.' + data[4]

	#TLEs are stupid, and there's no space between the last 3
	#values on the second line. This truncates the last entry
	#so only the mean motion is represented.
	n = data[7]
	data[7] = n[0:11]

	#convert all the strings to floats so we can do math on them
	for i in range(0,len(data)):
		data[i] =  float(data[i])

	if data[0] != 2:
		print("Error: tle2coe() only reads line 2 of a TLE.")
		return
	else:
		i = data[2]
		RAAN = data[3]
		e = data[4]
		AoP = data[5]
		n = data[7]
		#tle gives n in revs/day. convert to rev/s
		n = 2*np.pi*n/(24.*3600.)
		#convert n to a
		a = (mu/n**2.)**(1./3.)
		#convert M to nu
		M = data[6]
		anom = anomalies('M',M,a,e)
		nu = anom['nu']

	return \
		{ \
		'i' : i, \
		'RAAN': RAAN, \
		'OMEGA' : RAAN, \
		'e' : e, \
		'AoP' : AoP, \
		'omega' : AoP, \
		'nu' : nu, \
		'a' : a, \
		'M' : M, \
		'n': n \
		}

#------------------------------------------------------------------
#
# tle_epoch_time() converts a line from a celstrak TLE file into an array
# 	with values for the times encoded in it
#
#Source: http://www.celestrak.com/NORAD/documentation/tle-fmt.asp
#
#------------------------------------------------------------------

def tle_epoch_time(string):
	import numpy as np
	import mrm_time as t
	import pdb
	data = string.split()

	if data[0] != '1':
		print("Error: tle_time() only reads line 1 of a TLE.")
		return

	datetime = data[3]
	year = int(datetime[0:2]) + 2000
	doy = int(datetime[2:5]) #doy of year without decimals
	decimals = float(datetime[5:14])

	jd = t.time_convert([year,doy],'ydnhms','jd') + decimals
	utc = t.time_convert(jd,'jd','utc')
	ydnhms = t.time_convert(jd,'jd','ydnhms')

	return \
		{ \
		'jd': jd, \
		'utc': utc, \
		'ydnhms': ydnhms
		}



#------------------------------------------------------------------
# eci2ecef() converts from ECI position to ECEF position given the
# Greenwich Sidereal Time.
#
#Reference: lecture 7 ASEN 5050 CU Boulder, Fall 2016
#
#Inputs:
#	r_ijk: position vector in ECI coordinates as vertical python
#		3x1 matrix in whichever units are passed in
#	theta_GST: Greenwich Sideral Time in degreens
#
#Outputs:
#	r_ecef: Earth Centered Earth Fixed position coordinates
#------------------------------------------------------------------
def eci2ecef(r_ijk, theta_GST):
	import numpy as np
	from util import r3

	if r_ijk.shape == (1,3):
		r_ijk = np.transpose(r_ijk)

	theta_GST = np.deg2rad(theta_GST)
	#r_z rotation matrix (aka r3) is defined in the function r3()
	r_ecef = r3(theta_GST)*r_ijk

	return r_ecef

#------------------------------------------------------------------
# ecef2geocentric() converts from ECEF position to geocentric
# position given the Greenwich Sidereal Time.
#
#Reference: lecture 7 ASEN 5050 CU Boulder, Fall 2016
#
#Inputs:
#	r_ecef: position vector in ECEF coordinates as vertical python
#		3x1 matrix
#
#Outputs:
#	geocentric: dictionary with geocentric coordinates
#		r: geocentric radius in whatever as passed in
#		phi: geocentric latitude in degrees
#		lambda: geocentric longitude in degrees		
#
#------------------------------------------------------------------
def ecef2geocentric(r_ecef):
	import numpy as np
	import numpy.linalg as la

	#length of r
	r = la.norm(r_ecef)

	#assume spherical earth, subtract off radius from lenght of
	#r to get altitude
	alt = r - 6378.1363

	#separate column vector into components
	x = r_ecef[0][0]
	y = r_ecef[1][0]
	z = r_ecef[2][0]

	#because phi (latitude) is only defined from -180 to 180, 
	#we can get away without using arctan2
	#z = r*sin(phi)
	phi = np.arcsin(z/r)

	#but lambda (longitude) is defined from 0-360, so we need 
	#to use arctan2.
	#x = r*cos(phi)*cos(lambda)
	#y = r*cos(phi)*sin(lambda)
	cos_lam = x/(r*np.cos(phi))
	sin_lam = y/(r*np.cos(phi))
	lam = np.arctan2(sin_lam, cos_lam)

	geocentric = { \
		'alt' : alt, \
		'phi' : np.rad2deg(float(phi)), \
		'lambda' : np.rad2deg(float(lam)) \
		}

	return geocentric


#------------------------------------------------------------------
# geocentric2ecef() converts from geocentric position to Earth
# Centered Earth Fixed
#
#Reference: lecture 7 ASEN 5050 CU Boulder, Fall 2016
#
#Inputs:
#	r: geocentric radius in whatever as passed in
#	phi: geocentric latitude in degrees
#	lam: geocentric longitude in degrees	
#
#Outputs:
#	r_ecef: Earth Centered Earth Fixed position coordinates
#------------------------------------------------------------------

def geocentric2ecef(r,phi,lam):
	import numpy as np

	phi = np.deg2rad(phi)
	lam = np.deg2rad(lam)

	x = r * np.cos(phi) * np.cos(lam)
	y = r * np.cos(phi) * np.sin(lam)
	z = r * np.sin(phi)

	r_ecef = np.matrix([[x],[y],[z]])

	return r_ecef

#------------------------------------------------------------------
# ecef2eci() converts from ECEF position to ECI position given the
# Greenwich Sidereal Time.
#
#Reference: lecture 7 ASEN 5050 CU Boulder, Fall 2016
#
#Inputs:
#	r_ecef: position vector in ECEF coordinates as vertical python
#		3x1 matrix in whichever units are passed in
#	theta_GST: Greenwich Sideral Time in degreens
#
#Outputs:
#	r_ijk: ECI position coordinates
#------------------------------------------------------------------
def ecef2eci(r_ecef, theta_GST):
	import numpy as np
	from util import r3
	theta_GST = np.deg2rad(theta_GST)

	#r3 is the z rotation matrix. 
	#this is exactly the same as eci2ecef except we pass in the
	#negative angle to r3()
	r_ijk = r3(-theta_GST)*r_ecef
	return r_ijk

#------------------------------------------------------------------
# ecef2topo() converts from ECEF position to topographical 
#	(SEZ) position.
#
#Reference: lecture 7 ASEN 5050 CU Boulder, Fall 2016
#
#Inputs:
#	r_ecef: position vector of satellite in ECEF coordinates 
#		as vertical python 3x1 matrix in whichever 
#		units are passed in
#	lat: latitude of station in degrees
#	lon: longitude of station in degrees
#	alt: altitude of station in km
#
#Outputs:
#	topo: A dictionary with topographic coordinates.
#		r_sez: SEZ position coordinates
#		az:
#		el:
#		range:
#------------------------------------------------------------------
def ecef2topo(r_ecef, lat, lon, alt):
	import numpy as np
	import numpy.linalg as la
	from util import r2, r3
	#convert lat, lon, and alt to radians
	lat = np.deg2rad(lat)
	lon = np.deg2rad(lon)

	#find radius between station and center of earth for ecef
	#representation.
	station_r = alt + 6378.1363
	#find the station's ecef coordinates
	station_ecef = np.matrix([ \
		[station_r*np.cos(lat)*np.cos(lon)], \
		[station_r*np.cos(lat)*np.sin(lon)], \
		[station_r*np.sin(lat)] \
		])

	#find slant-range vector
	rho_ecef = r_ecef-station_ecef

	#convert from ECEF to SEZ
	rho_sez = r2(np.pi/2-lat)*r3(lon)*rho_ecef
	#range is norm of the SEZ position vector
	rho = la.norm(rho_sez)

	#decompose rho_sez into S, E, and Z components.
	rho_s = rho_sez[0][0]
	rho_e = rho_sez[1][0]
	rho_z = rho_sez[2][0]
	
	#rho_s = -rho*cos(el)*cos(alt)
	#rho_e =  rho*cos(el)*sin(alt)
	#rho_z =  rho*sin(el)


	#From the above relations, we can derive these:

	#find el
	sin_el = rho_z/rho
	cos_el = np.sqrt(rho_s**2+rho_e**2)/rho
	el = np.arctan2(sin_el,cos_el)

	#find az
	sin_az = rho_e/np.sqrt(rho_s**2+rho_e**2)
	cos_az = -rho_s/np.sqrt(rho_s**2+rho_e**2)
	az = np.arctan2(sin_az,cos_az)

	#convert az, and el to degrees for final reporting
	az = np.rad2deg(az)
	el = np.rad2deg(el)


	topo = { \
		'rho_sez' : rho_sez, \
		'az': az, \
		'el': el, \
		'range': rho \
	}

	return topo

#------------------------------------------------------------------
# cw() relative position and velocity of two spacecraft using the
#	Clohessy Wiltshire Equations
#	
#	ASSUMES CIRCULAR ORBITS (so kinda useless, yeah?)
#
#Reference: lecture 11 ASEN 5050 CU Boulder, Fall 2016
#
#Inputs:
#	r_0: Initial displacement vector
#		as nx1 colunm vector
#	v_0: Initial relative velocity vector
#		as nx1 column vector
#	omega_tgt: the angular velocity of the target
#	delta_t: time to step forward in s
#Outputs:
#	r: displacement at time delta_t
#	v: relative velocity vector at time delta_t
#------------------------------------------------------------------

def cw(r_0,v_0,omega_tgt,delta_t):
	import numpy as np

	x_0 = r_0[0][0]
	y_0 = r_0[1][0]
	z_0 = r_0[2][0]

	v_x_0 = v_0[0][0]
	v_y_0 = v_0[1][0]
	v_z_0 = v_0[2][0]

	x = v_x_0/omega_tgt*np.sin(omega_tgt*delta_t) - \
		(3*x_0+2*v_y_0/omega_tgt)*np.cos(omega_tgt*delta_t) + \
		(4*x_0+2*v_y_0/omega_tgt)

	y = (6*x_0+4*v_y_0/omega_tgt)*np.sin(omega_tgt*delta_t) + \
		2*v_x_0/omega_tgt*np.cos(omega_tgt*delta_t) - \
		(6*omega_tgt*x_0 + 3*v_y_0)*delta_t + \
		(y_0-2*v_x_0/omega_tgt)

	z = z_0*np.cos(omega_tgt*delta_t) + \
		v_z_0/omega_tgt*np.sin(omega_tgt*delta_t)

	v_x = v_x_0*np.cos(omega_tgt*delta_t) + \
		(3*omega_tgt*x_0+2*v_y_0)*np.sin(omega_tgt*delta_t)

	v_y = (6*omega_tgt*x_0+4*v_y_0)*np.cos(omega_tgt*delta_t) - \
		2*v_x_0*np.sin(omega_tgt*delta_t) - \
		(6*omega_tgt*x_0+3*v_y_0)

	v_z = -z_0*omega_tgt*np.sin(omega_tgt*delta_t) + \
		v_z_0*np.cos(omega_tgt*delta_t)

	print(np.sqrt(v_x[0]**2+v_y[0]**2+v_z[0]**2))
	return ''


#------------------------------------------------------------------
# theta_gmst() 
#	
#
#Reference: Vallado, 4ed p 187-189
#
#Inputs:
#	jd: the time for desired theta gst in jd
#Outputs:
#	r: displacement at time delta_t
#	v: relative velocity vector at time delta_t
#------------------------------------------------------------------

def theta_gmst(jd):
	import mrm_time as t
	J2000_jd = t.time_convert([2000,1,12],'ydnhms','jd')

	#centuries since J2000 
	T_UT1 = (jd - J2000_jd)/365.25/100

	theta_gmst = 67310.54841+(876600*3600+8640184.812866)*T_UT1 + \
		0.093104*T_UT1**2 - 6.e-6*T_UT1**3

	theta_gmst = (theta_gmst%86400)/240

	return theta_gmst

#------------------------------------------------------------------
# ground_track_plot() plot a ground track given tle information
#	that's been parsed by tle_epoch_time() and tle2coe(), a 
#	start time, and a propogation duration
#	
#
#Reference: lecture 11 ASEN 5050 CU Boulder, Fall 2016
#			Homework 6, too.
#
#Inputs:
#	epoch: tle output of tle_epoch_time
#	coe: tle output of tle2coe
#	start_time: start time for propogation in jd
#	duration: time to propogate for in minutes
#Outputs:
#	ground track plot
#------------------------------------------------------------------
def ground_track_plot(iss_epoch, iss_coe, start_time, duration):
	import mrm_time as t
	import numpy as np
	import matplotlib.pyplot as plt

	map_latitude = []
	map_longitude = []

	for line in open('worldmap2384.dat', 'r'):
		split_line = line.split()
		map_latitude.append(split_line[0])
		map_longitude.append(split_line[1])

	#find delta between epoch and desired start time (in days).
	epoch2start_jd = start_time-iss_epoch['jd']
	#convert to seconds
	epoch2start = epoch2start_jd*3600*24

	#find all anomalies at epoch
	iss_epoch_anomalies = anomalies('M',iss_coe['M'],iss_coe['a'],iss_coe['e'])
	#initialize latitude and longitude arrays
	iss_latitude = []
	iss_longitude = []

	#find initial thete_gst in degrees
	theta_gst_initial = theta_gmst(start_time)
	#convert it to radians
	theta_gst_initial = np.deg2rad(theta_gst_initial)

	#propogate once a minute for passed duration
	for i in range(0,duration+1):
		#find new anomalies epoch2start after epoch
		iss_anomalies = \
			anomalies(\
			't',iss_epoch_anomalies['t'] + epoch2start + i*60 \
			,iss_coe['a'],iss_coe['e'],silent=1)
		# print(t.time_convert(i*60/3600/24 +iss_epoch['jd'],'jd','utc'))
		eci = coe2rv(
			iss_coe['a'], 
			iss_coe['e'], \
			iss_coe['i'], \
			iss_coe['OMEGA'], \
			iss_coe['omega'], \
			iss_anomalies['nu'])
		#ECEF takes a column vector. Convert to a column vector
		transpose_r_ijk = np.matrix.transpose(np.matrix(eci['r_ijk']))

		#convert to ecef
		theta_gst = theta_gst_initial + i*60*7.2921158553e-5
		ecef = eci2ecef(transpose_r_ijk, np.rad2deg(theta_gst))
		#convert to geocentric
		geocentric = ecef2geocentric(ecef)
		#append to lat and lon lists
		iss_latitude.append(geocentric['phi'])
		iss_longitude.append(geocentric['lambda'])

	plt.figure(num=None, figsize=(15, 8.5))
	plt.ylim([-90,90])
	plt.xlim([-180,180])
	plt.plot(map_latitude, map_longitude, 'black')
	plt.plot(iss_longitude, iss_latitude, 'bo')
	plt.show()

	return

#------------------------------------------------------------------
# geodetic2geocentric() Convert geocentric latitude to geodetic
#	latitude
#
#Reference: lecture 11 ASEN 5050 CU Boulder, Fall 2016
#
#Inputs:
#	lat: geodetic latitude in degrees
#	e: ellipticity of the body we care about
#Outputs:
#	lat: geocentric latitude
#------------------------------------------------------------------
def geodetic2geocentric(lat, e):
	import numpy as np
	lat_geocentric = np.arctan(np.tan(np.deg2rad(lat))*(1-(e)**2))
	lat_geocentric = np.rad2deg(lat_geocentric)

	return lat_geocentric

#------------------------------------------------------------------
# lambert() 
#
#Reference: 
#	http://ccar.colorado.edu/imd/2015/documents/LambertHandout.pdf
#
#Inputs:
#	X_0: initial state vector; velocities required to calculate C3
#		and vInf
#	X_f: final state vector; velocities required to calculate C3
#		and vInf
#	dt_0: transfer time in seconds
#keywords:
#	DM: direction of motion (if you want to force it. It is 
#		nominaly calculated by the script.)
#Outputs:
#	
#------------------------------------------------------------------

def multiLambert(X_0, X_f, dt_0, **kwargs):
	import pdb

	#accept kwarg input for mu. If none is used, use that of Earth
	#with a satellite of negligably small mass.
	try:
		mu = kwargs['mu']
	except:
		mu = 398600.4415 #km^3/s^2
	
	try:
		transferType = kwargs['type']
	except:
		transferType = 1

	try:
		revs = kwargs['revs']
	except:
		revs = 0

	try:
		iterations = kwargs['iterations']
	except:
		iterations = 100 #km^3/s^2

	r_0 = X_0[:,0:3]
	r_f = X_f[:,0:3]
	r0 = sqrt(X_0[:,0,None]**2+X_0[:,1,None]**2+X_0[:,2,None]**2)
	n0 = r_0/r0
	rf = sqrt(X_f[:,0,None]**2+X_f[:,1,None]**2+X_f[:,2,None]**2)
	nf = r_f/rf

	# n0 = X_0[0:3]/norm(X_0[0:3])
	# nf = X_f[0:3]/norm(X_f[0:3])
	# r0 = norm(X_0[0:3])
	# rf = norm(X_f[0:3])
	sqrtMu = sqrt(mu)
####################################################################
#	Approximate delta nu.
#
#	This section assumes that the transfer orbit is in the 
#	ecliptic. Since we only use it to find DM, it's a good enough
#	approximation for reasonable transfers.
#
####################################################################

	nu_0 = arctan2(n0[:,1],n0[:,0])
	nu_f = arctan2(nf[:,1],nf[:,0])
	delta_nu = nu_f - nu_0

	delta_nu[delta_nu < 0] += 2*pi
	delta_nu[delta_nu > 2*pi] -= 2*pi
	# if delta_nu < 0:
	# 	delta_nu += 2*pi
	# if delta_nu > 2*pi:
	# 	delta_nu -= 2*pi

	try:
		DM = kwargs['DM']
	except:
		DM = zeros(len(delta_nu)) - 1
		DM[delta_nu < pi] = 1
		DM = DM.reshape(-1,1)
		# if abs(delta_nu) < pi:
		# 	DM = 1
		# else:
		# 	DM = -1

	#this delta nu is NOT an approximiation 
	#since it uses the dot product

	#it's ugly, but I think it's right
	
	
	cos_delta_nu = sum((n0*nf).T).reshape(-1,1)

	A = DM * sqrt(r0*rf*(1+cos_delta_nu))

	canBeSolved = zeros(len(delta_nu)).reshape(-1,1)

	#if delta_nu or A == 0, flag as cannot be solved
	canBeSolved[delta_nu == 0] = -1
	canBeSolved[A == 0] = -1
	# if delta_nu == 0 or A == 0:
	# 	print('Trajectory Cannot be Computed')
	# 	return



	#This block of commented-out code is stuff from the single lambert
	#funciton. It's only necessary if we're doing a multi-rev solution
	#ATM, I have no reason to do multi rev solutions with the multi
	#lambert, so I'm leaving it out. I will leave the commented out
	#lines in though, so I have them as a starting point if I decide
	#that I need to do multirev in multiLambert

	# if revs == 0:
	# 	psi = 0
	# 	psi_up = 4*pi**2
	# 	psi_low = -4*pi**2
	# else:
	# 	psi_up = (2*(revs + 1)*pi)**2 - 0.01
	# 	psi_low = (2*revs*pi)**2 + 0.01
	# 	psi = (psi_up + psi_low)/2

	# 	#define a function for calculating TOF from psi quickly
	# 	def TOF(psi):
	# 		sqrtPsi = sqrt(psi)
	# 		c2 = (1 - cos(sqrtPsi))/psi
	# 		sqrtC2 = sqrt(c2)
	# 		c3 = (sqrtPsi - sin(sqrtPsi))/sqrtPsi**3
	# 		y = r0 + rf + A*(psi*c3-1)/sqrtC2
	# 		xi = sqrt(y/c2)
	# 		sqrtY = sqrt(y)
	# 		TOF = (xi**3*c3+A*sqrtY)/sqrtMu
	# 		return TOF

	# 	#find psi associated with minimum TOF so we know where the
	# 	#cutoff between type III and type IV is
	# 	testPsi = linspace(psi_low + 0.01,psi_up - 0.01,15)
	# 	testTOF = TOF(testPsi)
	# 	sortTOF = sorted(testTOF)
	# 	while sortTOF[1] - sortTOF[0] > 1e-6:
	# 		testPsi = linspace(
	# 			testPsi[argmin(testTOF)-1],
	# 			testPsi[argmin(testTOF)+1],
	# 			15)
	# 		testTOF = TOF(testPsi)
	# 		sortTOF = sorted(testTOF)
	# 		minimizingPsi = testPsi[argmin(testTOF)]
	# 		# print(testTOF - min(testTOF))

	# 	minimumTOF = TOF(minimizingPsi)
		
	# 	#if there are no solutions for this TOF, exit the function
	# 	#and return values so the thing calling this doesn't break
	# 	if minimumTOF > dt_0:
	# 		return \
	# 			{ 
	# 				'v_0' : nan,
	# 				'v_f': nan,
	# 				'DM': nan,
	# 				'vInfDepart': array([nan,nan,nan]),
	# 				'vInfArrive': array([nan,nan,nan]),
	# 				'magVInfArrive': nan,
	# 				'C3': nan,
	# 				'delta_nu': nan,
	# 				'i': nan,
	# 				'psi': nan,
	# 				'minTOF': minimumTOF,
	# 				'minimizingPsi': minimizingPsi
	# 			}			


	# 	if transferType == 3:
	# 		psi_up = minimizingPsi
	# 	else:
	# 		psi_low = minimizingPsi

	# 	psi = (psi_low + psi_up)/2
		
	#initialize dt to make sure we always walk through the loop
	c2 = zeros(len(canBeSolved)).reshape(-1,1) + 1./2.
	c3 = zeros(len(canBeSolved)).reshape(-1,1) +  1./6.
	psi = zeros(len(canBeSolved)).reshape(-1,1) 
	psi_up = zeros(len(canBeSolved)).reshape(-1,1) + 4*pi**2
	psi_low = zeros(len(canBeSolved)).reshape(-1,1) - 4*pi**2

	dt_0 = dt_0.reshape(-1,1)
	dt = zeros(len(canBeSolved)).reshape(-1,1) + dt_0+0.0001
	

	i = 0

	if transferType == 3:
		def dtCheck(dt,dt_0):
			return dt >= dt_0
	else:
		def dtCheck(dt,dt_0):
			return dt <= dt_0

	ind = DM != 0
	while max(abs(dt - dt_0)) > 1e-6 and i<iterations:
		i += 1

		ind = abs(dt - dt_0) > 1e-6
		sqrtC2 = sqrt(c2)
		y = r0 + rf + A*(psi*c3 - 1)/sqrtC2
		
		# if A > 0 and y < 0:
		# 	while y < 0:
		# 		psi = psi + 0.1
		# 		y = r0 + rf + A*(psi*c3 - 1)/sqrtC2

		if sum(logical_and(A > 0, y < 0)) > 0:
			while min(y) < 0:
				psi[y < 0] += 0.1
				y[y < 0] = r0 + rf + A*(psi*c3 - 1)/sqrtC2
		# o.multiLambert(earthState,marsState,TOFs,mu=sun.mu)
		# o.multiLambert(earthState[0:1],marsState[0:1],TOFs[0:1],mu=sun.mu)
		# o.multiLambert(earthState[1:2],marsState[0:2],TOFs[1:2],mu=sun.mu)
		# o.lambert(earthState[0],marsState[0],TOFs[0],mu=sun.mu)

		sqrtY = sqrt(y)
		xi = sqrtY/sqrtC2
		dt = (xi**3*c3+A*sqrtY)/sqrtMu

		
		check = dtCheck(dt,dt_0)
		psi_low[check] = psi[check]
		psi_up[~check] = psi[~check]
		# if dtCheck(dt,dt_0):
		# 	psi_low = psi
		# else:
		# 	psi_up = psi
		psi = (psi_up + psi_low)/2.

		sqrtPsi = sqrt(psi[psi > 1e-6])
		c2[psi > 1e-6] = (1-cos(sqrtPsi))/psi[psi > 1e-6]
		c3[psi > 1e-6] = (sqrtPsi-sin(sqrtPsi))/sqrtPsi**3
		
		sqrtPsi = sqrt(-psi[psi < -1e-6])
		c2[psi < -1e-6] = (1-cosh(sqrtPsi))/psi[psi < -1e-6]
		c3[psi < -1e-6] = (sqrtPsi-sinh(sqrtPsi))/sqrtPsi**3

		c2[logical_and(c2 > -1e-6,c2 < 1e-6)] = 1./2.
		c3[logical_and(c3 > -1e-6,c3 < 1e-6)] = 1./6.

		# yFinished = y[abs(dt - dt_0) <= 1e-6]
		# r0Finished = r0[abs(dt - dt_0) <= 1e-6]
		# rfFinished = rf[abs(dt - dt_0) <= 1e-6]

		# if psi > 1e-6:
		# 	sqrtPsi = sqrt(psi)
		# 	c2 = (1-cos(sqrtPsi))/psi
		# 	c3 = (sqrtPsi-sin(sqrtPsi))/sqrtPsi**3

		# elif psi < -1e-6:
		# 	sqrtNegPsi = sqrt(-psi)
		# 	c2 = (1-cosh(sqrtNegPsi))/psi
		# 	c3 = (sinh(sqrtNegPsi)-sqrtNegPsi)/sqrtNegPsi**3
		
		# else:
		# 	c2 = 1./2.
		# 	c3 = 1./6.

	if i == iterations: print("max iterations reached")

	f = 1 - y/r0
	g_dot = 1 - y/rf
	g = A*sqrtY/sqrtMu

	v_0 = (rf*nf - f*r0*n0)/g
	v_f = (g_dot*rf*nf - r0*n0)/g

	# try:
	# 	minTOF = TOF(minimizingPsi)
	# except:
	# 	minTOF = nan
	# 	minimizingPsi = nan
	vInfDepart = v_0 - X_0[:,3:6]
	vInfArrive = v_f - X_f[:,3:6]
	magVInfArrive = sqrt(sum((vInfArrive**2).T))
	C3 = sum((vInfDepart**2).T)
	return \
		{ 
			'v_0' : v_0,
			'v_f': v_f,
			'DM': DM,
			'vInfDepart': vInfDepart,
			'vInfArrive': vInfArrive,
			'magVInfArrive': magVInfArrive,
			'C3': C3,
			'delta_nu': delta_nu,
			'i': i,
			'psi': psi,
		}

#------------------------------------------------------------------
# lambert() 
#
#Reference: 
#	http://ccar.colorado.edu/imd/2015/documents/LambertHandout.pdf
#
#Inputs:
#	X_0: initial state vector; velocities required to calculate C3
#		and vInf
#	X_f: final state vector; velocities required to calculate C3
#		and vInf
#	dt_0: transfer time in seconds
#keywords:
#	DM: direction of motion (if you want to force it. It is 
#		nominaly calculated by the script.)
#Outputs:
#	
#------------------------------------------------------------------
def lambert(X_0, X_f, dt_0, **kwargs):
	#accept kwarg input for mu. If none is used, use that of Earth
	#with a satellite of negligably small mass.
	try:
		mu = kwargs['mu']
	except:
		mu = 398600.4415 #km^3/s^2
	
	try:
		transferType = kwargs['type']
	except:
		transferType = 1

	try:
		revs = kwargs['revs']
	except:
		revs = 0

	r_0 = X_0[0:3]
	r_f = X_f[0:3]
	n0 = X_0[0:3]/norm(X_0[0:3])
	nf = X_f[0:3]/norm(X_f[0:3])
	r0 = norm(X_0[0:3])
	rf = norm(X_f[0:3])
	sqrtMu = sqrt(mu)
####################################################################
#	Approximate delta nu.
#
#	This section assumes that the transfer orbit is in the 
#	ecliptic. Since we only use it to find DM, it's a good enough
#	approximation for reasonable transfers.
#
####################################################################

	nu_0 = arctan2(n0[1],n0[0])
	nu_f = arctan2(nf[1],nf[0])
	delta_nu = nu_f - nu_0

	if delta_nu < 0:
		delta_nu += 2*pi
	if delta_nu > 2*pi:
		delta_nu -= 2*pi

	try:
		DM = kwargs['DM']
	except:
		if abs(delta_nu) < pi:
			DM = 1
		else:
			DM = -1

	#this delta nu is NOT an approximiation 
	#since it uses the dot product
	cos_delta_nu = n0.dot(nf)
	A = DM * sqrt(r0*rf*(1+cos_delta_nu))
	if delta_nu == 0 or A == 0:
		print('Trajectory Cannot be Computed')
		return

	c2 = 1./2.
	c3 = 1./6.


	if revs == 0:
		psi = 0
		psi_up = 4*pi**2
		psi_low = -4*pi**2
	else:
		psi_up = (2*(revs + 1)*pi)**2 - 0.01
		psi_low = (2*revs*pi)**2 + 0.01
		psi = (psi_up + psi_low)/2

		#define a function for calculating TOF from psi quickly
		def TOF(psi):
			sqrtPsi = sqrt(psi)
			c2 = (1 - cos(sqrtPsi))/psi
			sqrtC2 = sqrt(c2)
			c3 = (sqrtPsi - sin(sqrtPsi))/sqrtPsi**3
			y = r0 + rf + A*(psi*c3-1)/sqrtC2
			xi = sqrt(y/c2)
			sqrtY = sqrt(y)
			TOF = (xi**3*c3+A*sqrtY)/sqrtMu
			return TOF

		#find psi associated with minimum TOF so we know where the
		#cutoff between type III and type IV is
		testPsi = linspace(psi_low + 0.01,psi_up - 0.01,15)
		testTOF = TOF(testPsi)
		sortTOF = sorted(testTOF)
		while sortTOF[1] - sortTOF[0] > 1e-6:
			testPsi = linspace(
				testPsi[argmin(testTOF)-1],
				testPsi[argmin(testTOF)+1],
				15)
			testTOF = TOF(testPsi)
			sortTOF = sorted(testTOF)
			minimizingPsi = testPsi[argmin(testTOF)]


		minimumTOF = TOF(minimizingPsi)
		
		#if there are no solutions for this TOF, exit the function
		#and return values so the thing calling this doesn't break
		if minimumTOF > dt_0:
			return \
				{ 
					'v_0' : nan,
					'v_f': nan,
					'DM': nan,
					'vInfDepart': array([nan,nan,nan]),
					'vInfArrive': array([nan,nan,nan]),
					'magVInfArrive': nan,
					'C3': nan,
					'delta_nu': nan,
					'i': nan,
					'psi': nan,
					'minTOF': minimumTOF,
					'minimizingPsi': minimizingPsi
				}			


		if transferType == 3:
			psi_up = minimizingPsi
		else:
			psi_low = minimizingPsi

		psi = (psi_low + psi_up)/2
		
	#initialize dt to make sure we always walk through the loop
	dt = dt_0+0.0001

	i = 0

	if transferType == 3:
		def dtCheck(dt,dt_0):
			return dt >= dt_0
	else:
		def dtCheck(dt,dt_0):
			return dt <= dt_0


	while abs(dt - dt_0) > 1e-6 and i<1000:
		i += 1
		sqrtC2 = sqrt(c2)
		y = r0 + rf + A*(psi*c3 - 1)/sqrtC2

		if A > 0 and y < 0:
			while y < 0:
				psi = psi + 0.1
				y = r0 + rf + A*(psi*c3 - 1)/sqrtC2

		sqrtY = sqrt(y)
		xi = sqrtY/sqrtC2
		dt = (xi**3*c3+A*sqrtY)/sqrtMu


		if dtCheck(dt,dt_0):
			psi_low = psi
		else:
			psi_up = psi

		psi = (psi_up + psi_low)/2.

		if psi > 1e-6:
			sqrtPsi = sqrt(psi)
			c2 = (1-cos(sqrtPsi))/psi
			c3 = (sqrtPsi-sin(sqrtPsi))/sqrtPsi**3

		elif psi < -1e-6:
			sqrtNegPsi = sqrt(-psi)
			c2 = (1-cosh(sqrtNegPsi))/psi
			c3 = (sinh(sqrtNegPsi)-sqrtNegPsi)/sqrtNegPsi**3
		
		else:
			c2 = 1./2.
			c3 = 1./6.

	if i == 1000: print("max iterations reached")

	f = 1 - y/r0
	g_dot = 1 - y/rf
	g = A*sqrtY/sqrtMu

	v_0 = (rf*nf - f*r0*n0)/g
	v_f = (g_dot*rf*nf - r0*n0)/g

	try:
		minTOF = TOF(minimizingPsi)
	except:
		minTOF = nan
		minimizingPsi = nan

	return \
		{ 
			'v_0' : v_0,
			'v_f': v_f,
			'DM': DM,
			'vInfDepart': v_0 - X_0[3:6],
			'vInfArrive': v_f - X_f[3:6],
			'magVInfArrive': sqrt((v_f - X_f[3:6]).dot(v_f - X_f[3:6])),
			'C3': (v_0 - X_0[3:6]).dot(v_0 - X_0[3:6]),
			'delta_nu': delta_nu,
			'i': i,
			'psi': psi,
			'minTOF': minTOF,
			'minimizingPsi': minimizingPsi
		}


def hill_frame(theta, inc, OMEGA):
	from numpy import sin, cos, array
	return array([
		[
		cos(theta)*cos(OMEGA)-sin(theta)*cos(inc)*sin(OMEGA),
		cos(theta)*sin(OMEGA)+sin(theta)*cos(inc)*cos(OMEGA),
		sin(theta)*sin(inc)
		],
		[
		-sin(theta)*cos(OMEGA)-cos(theta)*cos(inc)*sin(OMEGA),
		-sin(theta)*sin(OMEGA)+cos(theta)*cos(inc)*cos(OMEGA),
		cos(theta)*sin(inc)
		],
		[
		sin(inc)*sin(OMEGA),
		-sin(inc)*cos(OMEGA),
		cos(inc)
		]
		])









