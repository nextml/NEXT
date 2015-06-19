# Online Learning App prototype for Next.Discovery
# author: Kevin Jamieson, kevin.g.jamieson@gmail.com
# last updated: 11/20/2014
# 
#######################################
# serves as a prototype for all the adaptive and online learning applications on next.dicovery.
# all valid application inherit this class and thus must implement these methods
#
#######################################

class AppPrototype(object):
  def __init__(self):
    self.app_id = None
    return NotImplementedError
    
  def initExp(self,db_api,exp_uid,args):
    return NotImplementedError

  def getQuery(self,db_api,exp_uid,args):
    return NotImplementedError

  def processAnswer(self,db_api,exp_uid,args):
    return NotImplementedError

  def predict(self,db_api,exp_uid,args):
    return NotImplementedError
    
  def getStats(self,db_api,exp_uid,args):
    return NotImplementedError     

    
