import redismatrix
import numpy
import time
import matplotlib.pyplot as plot

from numpy import *
from numpy.random import *
from redismatrix import *
from matplotlib.font_manager import FontProperties

def main():
    file2 = open('T[i][j].txt', 'w')
    file3 = open('test.txt', 'w')
      
    n = 100   											# 
    m = 10 												# 
      
    startC = 0
    deltaC = 0
    totalC = 0
    total = 0
    averageR = 0
    
    T = zeros((n, m))
    Y = zeros((n, 1))
    
    for i in range(n):
        file3.write('\nCreating Matrix %s\n' % i)
        print '\nCreating Matrix %s' % i
          
        X = randn(1000, 1000)                           # Creating random matrix
        startC = time.time()
        A_i = Matrix(i, 'E', X)                         # Allocating new matrix 1000*1000 on Redis
        deltaC = time.time() - startC                   # Calculating time for a matrix creation
          
        totalC += deltaC                                # Calculating time taken for creation of n matrices
        file3.write('Time: {}\n'.format(deltaC))
        total = 0
        for j in range(m):
            k = random.random_integers(0,i)             # Selecting random matrix
            ell = random.random_integers(0,n-1)         # Selecting random index
            file3.write('\tMatrix %s, row %s\n' % (k, ell))
            
            start = time.time()
            A_k = Matrix(k,'E')
            A_k = A_k[ell]
            t_j = time.time() - start                   # Calculating time taken to retrieve row
            
            file3.write('Row %s: %s\n' % (ell, A_k))
#             print A_k
#             print t_j
            total += t_j                                # Calculating total time taken for retrieving all rows
            T[i][j] = t_j
            file2.write('%s\n' % T[i][j])
        Y[i] = (1.0/m)*total                            # Calculating average time taken to retrieve m rows
        averageR += Y[i][0]                             # Calculating total time taken to retrieve a row for n matrices
        file3.write('Time retrieving row from matrix %s: %s\n' % (i, Y[i][0]))
        
    savetxt('T (numpy_array).txt', T)                   
    averageC = totalC/i                                 # Calculating average time taken to create a matrix
    averageR /=i                                        # Calculating average time taken to retrieve a row for n matrices
    file3.write('\nAverage time creating matrices: %s s\n' % averageC)
    file3.write('\nAverage time retrieving rows: %s s\n' % averageR)
      
    file2.close()
    file3.close()
    
    A_i.deleteAll()                                     # Deleting all keys from redis
    
    # Making a plot from results
    X = loadtxt("T (numpy_array).txt")
    X = X.reshape(n,m)
# list = []
    file = open('max.txt', 'w') 
# for i in range(1000):
#     l = X[i]
# #     print l
#     list.append(max(l))
#     print list[i]
#     file.write('%s \t%s\n' % (i, list[i]))
# legend = []
# for i in range(1000):
#     legend.append('Matrix {}'.format(i))
    
    plot.plot(X, linewidth=2.0, marker='o')
    plot.title('Time VS Matrices')
    plot.xlabel('Matrices')
    plot.ylabel('Time (seconds)')
    plot.show()

if __name__ == "__main__": main()