import dpdata
import os

def mkdir(dir_name):
    path = os.getcwd()
    if not os.path.exists('%s/%s'%(path,dir_name)):
        os.makedirs('%s/%s'%(path,dir_name))
def gaussian_to_dp(xyzs_file,folder_name = 'inp_gaussian',dataset = 'data_000'):

    xyzs = open(xyzs_file).readlines()
    num = int(xyzs[0].strip().split()[0])
    index = len(xyzs)//(num+2)    
    gauss_data = dpdata.LabeledSystem('%s/image%s.log'%(folder_name,0),fmt='gaussian/log')
    for i in range(1,index):
        gauss_data += dpdata.LabeledSystem('%s/image%s.log'%(folder_name,i),fmt='gaussian/log')
    gauss_data.to_deepmd_npy('03.data/{}'.format(dataset))
loop = 0
model_number =4
while os.path.exists('iter.{}/02.label/inp_gaussian'.format(str(loop+1).zfill(3))):
    loop += 1
gaussian_inp='iter.{}/02.label/inp_gaussian'.format(str(loop).zfill(3))
gaussian_to_dp('iter.{}/01.neb/neb_images.xyz'.format(str(loop).zfill(3)),folder_name = gaussian_inp ,dataset = 'data_{}'.format(str(loop).zfill(3)))
mkdir('iter.{}/02.label/Done'.format(str(loop).zfill(3)))
mkdir('train')
for i in range(model_number):
    mkdir('train/00{}'.format(i))
if not os.path.exists('train/000/input.json'):
    for i in range(model_number):
        os.system('cp input.json train/00{}'.format(i))
print('将{}的数据转化为数据集到{}'.format(gaussian_inp ,'03.data/data_{}'.format(str(loop).zfill(3))))
