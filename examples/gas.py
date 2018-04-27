# A model of an ideal gas with hard-sphere collisions
#
## Based on gas.py by Bruce Sherwood for a cube as a container
## Sligthly modified by Andrey Antonov for a torus.
## Adapted by M. Musy for vtkPlotter

from __future__ import division, print_function
from random import random
import plotter
import numpy as np

#############################################################
Natoms = 400        # change this to have more or fewer atoms
Nsteps = 350        # nr of steps in the simulation
Matom = 4E-3/6E23   # helium mass
Ratom = 0.025       # wildly exaggerated size of helium atom
RingThickness=0.3   # thickness of the toroid
RingRadius=1

k = 1.4E-23         # Boltzmann constant
T = 300             # room temperature
dt = 1E-5

#############################################################

def reflection(p, pos):
    n = vp.norm(pos)
    return np.dot(np.identity(3)-2*n*n[:,np.newaxis], p)

vp = plotter.vtkPlotter(title='gas in toroid', verbose=0, axes=0)
vp.ring(c='g', radius=RingRadius, thickness=RingThickness, alpha=.1, wire=1) ### <--

Atoms = []
poslist = []
plist, mlist, rlist = [],[],[]
mass = Matom*Ratom**3/Ratom**3
pavg = np.sqrt(2.*mass*1.5*k*T) # average kinetic energy p**2/(2mass) = (3/2)kT

for i in range(Natoms):
    alpha = 2*np.pi*random()
    x = RingRadius*np.cos(alpha)*.9
    y = RingRadius*np.sin(alpha)*.9
    z = 0
    Atoms = Atoms + [vp.sphere(pos=(x,y,z), r=Ratom, c=i)]                   ### <--
    theta = np.pi*random()
    phi   = 2*np.pi*random()
    px = pavg*np.sin(theta)*np.cos(phi)
    py = pavg*np.sin(theta)*np.sin(phi)
    pz = pavg*np.cos(theta)
    poslist.append((x,y,z))
    plist.append((px,py,pz))
    mlist.append(mass)
    rlist.append(Ratom)

pos = np.array(poslist)
poscircle = pos
p = np.array(plist)
m = np.array(mlist)
m.shape = (Natoms, 1) 
radius = np.array(rlist)
r = pos-pos[:, np.newaxis] # all pairs of atom-to-atom vectors

ds = (p/m)*(dt/2.)
if 'False' not in np.less_equal(vp.mag(ds), radius).tolist():
    pos = pos+(p/mass)*(dt/2.) # initial half-step
vp.show()

pb = vp.ProgressBar(0,Nsteps, c=1)
for i in pb.range():

    # Update all positions
    ds = vp.mag((p/m)*(dt/2.))
    if 'False' not in np.less_equal(ds, radius).tolist(): 
        pos = pos+(p/m)*dt

    r = pos-pos[:,np.newaxis]                # all pairs of atom-to-atom vectors
    rmag = np.sqrt(np.sum(np.square(r), -1)) # atom-to-atom scalar distances
    hit = np.less_equal(rmag, radius+radius[:, None]) - np.identity(Natoms)
    hitlist = np.sort(np.nonzero(hit.flat)[0]).tolist() # i,j encoded as i*Natoms+j

    # If any collisions took place:
    for ij in hitlist:
        i, j = divmod(ij,Natoms)             # decode atom pair
        hitlist.remove(j*Natoms+i)           # remove symmetric j,i pair from list
        ptot = p[i]+p[j]
        mi = m[i,0]
        mj = m[j,0]
        vi = p[i]/mi
        vj = p[j]/mj
        ri = Ratom
        rj = Ratom
        a = vp.mag(vj-vi)**2
        if a == 0: continue                  # exactly same velocities
        b = 2*np.dot(pos[i]-pos[j], vj-vi)
        c = vp.mag(pos[i]-pos[j])**2-(ri+rj)**2
        d = b**2-4.*a*c
        if d < 0: continue                   # something wrong; ignore this rare case
        deltat = (-b+np.sqrt(d))/(2.*a)      # t-deltat is when they made contact
        pos[i] = pos[i]-(p[i]/mi)*deltat     # back up to contact configuration
        pos[j] = pos[j]-(p[j]/mj)*deltat
        mtot = mi+mj
        pcmi = p[i]-ptot*mi/mtot             # transform momenta to cm frame
        pcmj = p[j]-ptot*mj/mtot
        rrel = vp.norm(pos[j]-pos[i])
        pcmi = pcmi-2*np.dot(pcmi,rrel)*rrel # bounce in cm frame
        pcmj = pcmj-2*np.dot(pcmj,rrel)*rrel
        p[i] = pcmi+ptot*mi/mtot             # transform momenta back to lab frame
        p[j] = pcmj+ptot*mj/mtot
        pos[i] = pos[i]+(p[i]/mi)*deltat     # move forward deltat in time
        pos[j] = pos[j]+(p[j]/mj)*deltat

    # Bounce off the boundary of the torus
    for j in range(Natoms):
        poscircle[j] = vp.norm(pos[j])*RingRadius*[1,1,0]
    outside = np.greater_equal(vp.mag(poscircle-pos),RingThickness-2*Ratom)

    for k in range(len(outside)):
        if outside[k]==1 and np.dot(p[k], pos[k]-poscircle[k])>0:
            p[k] = reflection(p[k],pos[k]-poscircle[k])
            
    # then update positions of display objects
    for i in range(Natoms): Atoms[i].pos(pos[i])                           ### <--
    outside = np.greater_equal(vp.mag(pos), RingRadius+RingThickness)

    vp.render(resetcam=1)                                                  ### <--
    vp.camera.Azimuth(.5)
    vp.camera.Elevation(.1)
    pb.print()

vp.show()

