from ase.io import read,write
from ase.neb import NEB
from ase.optimize import BFGS
import os
def mkdir(dir_name):
    path = os.getcwd()
    if not os.path.exists('%s/%s'%(path,dir_name)):
        os.makedirs('%s/%s'%(path,dir_name))
mkdir('iter.000/01.neb')
path_file='r3'
n_images=10
initial = read('%s_react.xyz'%(path_file))
final = read('%s_prod.xyz'%(path_file))
images = [initial]
images += [initial.copy() for i in range(n_images)]
images += [final]
neb = NEB(images, k=0.1,parallel=True,method='improvedtangent')
print(len(images),images[0])
neb.interpolate()
traj = 'iter.000/01.neb/neb.traj'
neb.idpp_interpolate(fmax=0.05,optimizer=BFGS,traj=traj, log='iter.000/01.neb/neb.log')
images = read('{}@:{}:{}'.format(traj,n_images+2,n_images+1))
for i in range(1,len(read('{}@:'.format(traj)))//(n_images+2)):
    images.extend(read('{}@{}:{}'.format(traj,i*(n_images+2)+1,(i+1)*(n_images+2)-1)))
write(filename='iter.000/01.neb/neb_images.xyz',images=images,format='xyz')
print('初始结构数为：{}'.format(len(images)))

