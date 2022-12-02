from ase.io import read,write
from ase.neb import NEB
#from pesexp.mep.neb import NEB
from ase.optimize import BFGS
import os
from deepmd.calculator import DP
from ase.atoms import Atoms
import numpy as np

def mkdir(dir_name):
    path = os.getcwd()
    if not os.path.exists('%s/%s'%(path,dir_name)):
        os.makedirs('%s/%s'%(path,dir_name))
loop = 0
model_number =4
while os.path.exists('iter.{}/02.label/Done'.format(str(loop+1).zfill(3))):
    loop += 1
mkdir('iter.{}/03.DP'.format(str(loop).zfill(3)))
if not os.path.exists('iter.{}/03.DP/000.pb'.format(str(loop).zfill(3))):
    os.system('cp -r train iter.{}/03.DP/'.format(str(loop).zfill(3)))
    for i in range(model_number):
        os.system('dp freeze -c train/00{}/ -o iter.{}/03.DP/00{}.pb'.format(i,str(loop).zfill(3),i))
if model_number == 2:
    dp_model_0 = 'iter.{}/03.DP/000.pb'.format(str(loop).zfill(3))
    dp_model_1 = 'iter.{}/03.DP/001.pb'.format(str(loop).zfill(3))
    calc_0 = DP(model = dp_model_0)
    calc_1 = DP(model = dp_model_1)
if model_number == 4:
    dp_model_0 = 'iter.{}/03.DP/000.pb'.format(str(loop).zfill(3))
    dp_model_1 = 'iter.{}/03.DP/001.pb'.format(str(loop).zfill(3))
    dp_model_2 = 'iter.{}/03.DP/002.pb'.format(str(loop).zfill(3))
    dp_model_3 = 'iter.{}/03.DP/003.pb'.format(str(loop).zfill(3))
    calc_0 = DP(model = dp_model_0)
    calc_1 = DP(model = dp_model_1)
    calc_2 = DP(model = dp_model_2)
    calc_3 = DP(model = dp_model_3)    
n_images=10
mkdir('iter.{}/01.neb'.format(str(loop+1).zfill(3)))
traj = 'iter.{}/01.neb/neb.traj'.format(str(loop+1).zfill(3))
images = read('iter.{}/01.neb/neb.traj@-{}:'.format(str(0).zfill(3),n_images+2))
neb = NEB(images, k=0.1,climb=False,method='improvedtangent',allow_shared_calculator=True)
#neb = NEB(images, k=0.1,climb=True,method='energyspring',allow_shared_calculator=True)
neb.set_calculators(calc_0)
optimizer = BFGS(neb, trajectory = traj)
optimizer.run(fmax=0.05,steps=100)  
images = read('{}@:{}:{}'.format(traj,n_images+2,n_images+1))
for i in range(1,len(read('{}@:'.format(traj)))//(n_images+2)):
    images.extend(read('{}@{}:{}'.format(traj,i*(n_images+2)+1,(i+1)*(n_images+2)-1)))
final_images = []
log = open('iter.{}/03.DP/model_devi.log'.format(str(loop).zfill(3)),'w')
tplt = '{0:^12}\t{1:^30}\t{2:^30}\t{3:^30}'
log.writelines(tplt.format('image_num','max_devi_f','min_devi_f','avg_devi_f(ev/A)')+'\n')
num = 0 ; accurate_num = 0 ; fail_num = 0
f_high = 0.5
f_low = 0.05
for image in images:
    num += 1
    all_f_list = []
    if model_number == 2:
        image.calc = calc_0
        all_f_list.append(image.get_forces()) #get_force
        image.calc = calc_1
        all_f_list.append(image.get_forces()) #get_force
    if model_number == 4:
        image.calc = calc_0
        all_f_list.append(image.get_forces()) #get_force
        image.calc = calc_1
        all_f_list.append(image.get_forces()) #get_force
        image.calc = calc_2
        all_f_list.append(image.get_forces()) #get_force
        image.calc = calc_3
        all_f_list.append(image.get_forces()) #get_force
    f_average = np.mean(np.array(all_f_list),axis=0) #force_mean
    norm_f_list = []
    for f in all_f_list:
        norm_f =[np.linalg.norm(i) for i in f-f_average] #norm of f-f_mean 
        norm_f_list.append(np.square(norm_f))
    devi_f_list = np.sqrt(np.mean(norm_f_list,axis=0)) #sqrt of mean (square of norm)
    max_devi_f = np.max(np.array(devi_f_list))
    min_devi_f = np.min(np.array(devi_f_list))
    avg_devi_f = np.mean(np.array(devi_f_list))
    log.writelines(tplt.format(str(num).zfill(4),max_devi_f, min_devi_f ,avg_devi_f)+'\n') 
    if f_low < abs(max_devi_f) < f_high:
        final_images.append(image) 
    elif abs(max_devi_f) > f_high:
        fail_num += 1
    else:
        accurate_num += 1
write(filename='iter.{}/01.neb/neb_images.xyz'.format(str(loop+1).zfill(3)),images=final_images,format='xyz')
write(filename='iter.{}/01.neb/neb_path.xyz'.format(str(loop+1).zfill(3)),images=read('iter.{}/01.neb/neb.traj@-{}:'.format(str(loop+1).zfill(3),n_images+2)),format='xyz')
print('初始结构来自：{}'.format('iter.{}/01.neb/neb.traj@-{}:'.format(str(0).zfill(3),n_images+2)))
print('NEB迭代次数为：{}'.format((len(images)-2)//n_images))
print('第{}轮产生结构数为：{}'.format(loop+1,len(images)),'准确结构数为：{}'.format(accurate_num),'失败结构数为：{}'.format(fail_num))
print('第{}轮加入结构数为：{}'.format(loop+1,len(final_images)))
