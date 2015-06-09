import redismatrix
import numpy
import time

from numpy import *
from numpy.random import *
from redismatrix import *

def main():
    file = open('T[i][j].txt', 'w')
    
    n = 1000
    m = 100
   
    T = zeros((n, m))
    for i in range(n):
        print '\nCreating Matrix %s' % i
        
        # Creating random matrix
        X = randn(1000, 1000)
        
        # Allocating new matrix 1000*1000 on Redis
        A_i = Matrix(i, 'E', X)
        
        for j in range(m):
            k = random.random_integers(0,i)
            ell = random.random_integers(0,n-1)
            # Calculating time for retrieving a row
            start = time.time()
            A_k = Matrix(k,'E')
            A_k = A_k[ell]
            t_j = time.time() - start
            
            T[i][j] = t_j
            file.write('%s\n' % T[i][j])
    savetxt('T (numpy_array).txt',T)
    file.close()

    A_i.deleteAll()                       # Deleting all keys from redis


if __name__ == "__main__": main()