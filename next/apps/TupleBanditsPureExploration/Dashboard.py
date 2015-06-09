"""
TupleBanditsPureExplorationDashboard 
author: Nick Glattard, n.glattard@gmail.com
last updated: 4/24/2015

######################################
TupleBanditsPureExplorationDashboard

"""


import json
import numpy
import numpy.random
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
from next.utils import utils
from next.apps.AppDashboard import AppDashboard

class TupleBanditsPureExplorationDashboard(AppDashboard):

    def __init__(self,db,ell):
        AppDashboard.__init__(self,db,ell)

    def get_app_supported_stats(self):
        """
        Returns a list of dictionaries describing the identifier (stat_id) and 
        necessary params inputs to be used when calling getStats

        Expected output (list of dicts, each with fields):
            (string) stat_id : the identiifer of the statistic
            (string) description : docstring of describing outputs
            (list of string) necessary_params : list where each string describes the type of param input like 'alg_label' or 'task'
        """
        stat_list = self.get_supported_stats()

        stat = {}
        stat['stat_id'] = 'most_current_ranking'
        stat['description'] = self.most_current_ranking.__doc__
        stat['necessary_params'] = ['alg_label']
        stat_list.append(stat)
        
        return stat_list


    def most_current_ranking(self,app_id,exp_uid,alg_label):
        """
        Description: Returns a ranking of arms in the form of a list of dictionaries, which is conveneint for downstream applications

        Expected input:
          (string) alg_label : must be a valid alg_label contained in alg_list list of dicts 

        The 'headers' contains a list of dictionaries corresponding to each column of the table with fields 'label' and 'field' where 'label' is the label of the column to be put on top of the table, and 'field' is the name of the field in 'data' that the column correpsonds to 

        Expected output (in dict):
          plot_type : 'columnar_table'
          headers : [ {'label':'Rank','field':'rank'}, {'label':'Target','field':'index'} ]  
          (list of dicts with fields) data (each dict is a row, each field is the column for that row): 
            (int) index : index of target
            (int) ranking : rank (0 to number of targets - 1) representing belief of being best arm
        """

        alg_list,didSucceed,message = self.db.get(app_id+':experiments',exp_uid,'alg_list')

        for algorithm in alg_list:
            if algorithm['alg_label'] == alg_label:
                alg_id = algorithm['alg_id']
                alg_uid = algorithm['alg_uid']
        
        list_of_log_dict,didSucceed,message = self.ell.get_logs_with_filter(app_id+':ALG-EVALUATION',{'alg_uid':alg_uid})
        list_of_log_dict = sorted(list_of_log_dict, key=lambda k: k['num_reported_answers'] )

        print didSucceed, message
        
        item = list_of_log_dict[-1]

        return_dict = {}
        return_dict['headers'] = [{'label':'Rank','field':'rank'},{'label':'Target','field':'index'},{'label':'Score','field':'score'},{'label':'Precision','field':'precision'}]
        return_dict['data'] = item['targets']
        return_dict['plot_type'] = 'columnar_table'

        return return_dict


