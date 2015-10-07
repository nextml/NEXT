"""
PoolBasedTripletMDS app of the Online Learning Library for Next.Discovery
author: Kevin Jamieson, kevin.g.jamieson@gmail.com
last updated: 1/17/2015

PoolBasedTripletMDSPrototype

This interface must be implemented by an app that solves the pool-based non-metric multidimensional scaling problem. Algorithms solving this problem are managed by PoolBasedTripletMDS.py
"""


class PoolBasedTripletMDSPrototype(object):
  def __init__(self): 
    self.app_id = 'PoolBasedTripletMDS'

  def initExp(self,db,n=0,d=0,failure_probability=0.05):
    """
    initialize the experiment 

    Expected input:
      (next.database.DatabaseClient) db : database client, can cell db.set(key,value), value=db.get(key) 
      (int) n : number of objects
      (int) d : desired dimension
      (float) failure_probability : confidence

    Expected output (comma separated):
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError


  def getQuery(self,db):
    """
    A request to ask which triplet to ask next

    Expected input:
      (next.database.DatabaseClient) db : database client, can cell db.set(key,value), value=db.get(key) 

    Expected output: 
      (int) index_center : index of arm must be in {0,1,2,...,n-1}
      (int) index_left : index of arm must be in {0,1,2,...,n-1} - index_center
      (int) index_right : index of arm must be in {0,1,2,...,n-1} - index_center - index_left
    """
    return NotImplementedError

  
  def processAnswer(self,db,index=0,reward=0.5):
    """
    reporting back the reward of pulling the arm suggested by getQuery

    Expected input:
      (next.database.DatabaseClient) db : database client, can cell db.set(key,value), value=db.get(key) 
      (int) index_center : index of center object
      (int) index_left : index of left object
      (int) index_right : index of right object
      (int) index_winner : index of winner object, index_winner in {index_left,index_right}

    Expected output (comma separated): 
      (boolean) didSucceed : did everything execute correctly
    """
    return NotImplementedError

  def predict(self,db):
    """
     
    """
    return NotImplementedError

    
  def getStats(self,db):
    """
    reports statistics on the experiment model or process

    Expected input:
      (next.database.DatabaseClient) db : database client, can cell db.set(key,value), value=db.get(key) 
      
    Expected output: 
      (float[n][d]) X : n-by-d embedding formatted of an n-length list of d-length lists of floats
      (float[n][2]) X : n-by-2 embedding formatted of an n-length list of 2-length lists of floats
    """
    return NotImplementedError


