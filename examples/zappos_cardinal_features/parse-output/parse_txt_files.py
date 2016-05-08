
import os
import pickle
import numpy as np
from scipy.io import loadmat, savemat

output_dir_name = 'parse-output'
picture_dir = 'AllShoes'

os.system('mkdir ' + output_dir_name)

with open('FileName.txt') as f:
    filenames = [name[:-2] for name in f.readlines()]
    n = len(filenames) // 10
    m, n = 20, 100
    filenames = filenames[:n]
    pickle.dump(filenames, open(output_dir_name + '/filenames.pkl', 'wb'))

# Choosing a certain number of shoes
os.system('mkdir ' + output_dir_name + '/' + picture_dir)
for file_ in filenames:
    name = picture_dir + '/' + file_
    os.system('cp ' + name + ' ' + output_dir_name + '/' + name)


X = loadmat('./Zappos_Caffe_Layer8-2.mat')['X']
X = X.T
X = X[:m, :n]

savemat(output_dir_name + '/Zappos_Caffe_Layer8.mat', {'X': X})
