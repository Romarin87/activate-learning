import os
def mkdir(dir_name):
    path = os.getcwd()    
    if not os.path.exists('%s/%s'%(path,dir_name)):
        os.makedirs('%s/%s'%(path,dir_name))
def create_gaussian_inp(xyzs_file,folder_name = 'inp_gaussian'):
    mkdir(folder_name)
    xyzs = open(xyzs_file).readlines()
    num = int(xyzs[0].strip().split()[0])
    index = len(xyzs)//(num+2)
    run_g16 = open('%s/g16.sh'%(folder_name),'w')
    for i in range(index):
        if i%100==0 :
            g16sh = open('%s/g16_%s.sh'%(folder_name,i//100),'w')
            if i//100==0:
                run_g16.writelines('sh g16_%s.sh'%(i//100))
            else:
                run_g16.writelines(' & sh g16_%s.sh'%(i//100))
        g16sh.writelines('g16 image%s.gjf'%(i)+'\n')
        inp = open('%s/image%s.gjf'%(folder_name,i),'w')
        inp.writelines('#P M062X/def2TZVP nosymm '+'\n')
        inp.writelines('force'+'\n\n')
        inp.writelines('xyz form image%s'%(i)+'\n\n')
        inp.writelines('0 1'+'\n')
        for n in range(2,num+2):
            inp.writelines(xyzs[i*(num+2)+n])
        inp.writelines('\n')
    inp.close
loop = 0
while os.path.exists('iter.{}/01.neb/neb_images.xyz'.format(str(loop+1).zfill(3))):
    loop += 1
gaussian_inp='iter.{}/02.label/inp_gaussian'.format(str(loop).zfill(3))
mkdir(gaussian_inp)
create_gaussian_inp(xyzs_file = 'iter.{}/01.neb/neb_images.xyz'.format(str(loop).zfill(3)),folder_name = gaussian_inp)
print('产生的高斯输入文件目录：{}'.format(gaussian_inp))
