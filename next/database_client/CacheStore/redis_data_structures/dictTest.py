import redisDictionary
import time

from redisDictionary import *

def main():
    
    expId = 0
    subId = 'D'
    
    d = {'sape': 4139, 'jack': 4098, 'guido': 4127}
    d2 = {'one': 1, 'two': 2, 'three': 3}
    
    dict = Dictionary(expId, subId, d)
    dict2 = Dictionary(expId, subId, d2)

    print 'dict1 = %s' % dict
    print 'dict2 ='
    A = dict.getDictionary()
    A['sape'] = '2'
    l = ['sape', 'guido']
#     print dict._getValues(l)
#     print dictionary['sape']
#     print type(dict2)
    
#     x = dictionary['jack']
# #     print type(x)
#     
#     print dictionary
#     print dict
#     print len(dict)
# #     keys = ['one', 'two', 'three']
# #     values = [1, 2, 3]
# #     dict._setValues(dictionary2)
# #     print dict.getDictionary()
# #     dict._setValues2(keys, values)
#     print dict.getDictionary()
# #     
#     print dict['sape', 'jack']
#     print dict.get('ju', 'Cola')
# #     print dict
# #     dict.clear()
#     
# #     del dict['sape', 'jack']
# #     del dict
#     print dict.getDictionary()
# #     dict[['set', 'hola']] = [1]
#     print dict.getDictionary()
#     del dict['sape']

    
#     print dict
#     for i in dict:
#         print 'Key: %s, Value: %s' % (i, dict[i])
#        
#     print '\niteritems' 
#     for i in dict.iteritems():
#         print i
#     
#     print '\niterkeys'
#     for i in dict.iterkeys():
#         print i
#       
#     print '\nitervalues'  
#     for i in dict.itervalues():
#         print i

if __name__ == "__main__": main()