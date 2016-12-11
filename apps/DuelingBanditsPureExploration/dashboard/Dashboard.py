import json
import next.utils as utils
from next.apps.AppDashboard import AppDashboard

class MyAppDashboard(AppDashboard):
    def __init__(self,db,ell):
        AppDashboard.__init__(self,db,ell)

    def most_current_ranking(self,app, butler, alg_label):
        """
        Description: Returns a ranking of arms in the form of a list of dictionaries, which is conveneint for downstream applications

        Expected input:
          (string) alg_label : must be a valid alg_label contained in alg_list list of dicts 

        The 'headers' contains a list of dictionaries corresponding to each column of the table with fields 'label' and 'field' 
        where 'label' is the label of the column to be put on top of the table, and 'field' is the name of the field in 'data' that the column correpsonds to 

        Expected output (in dict):
          plot_type : 'columnar_table'
          headers : [ {'label':'Rank','field':'rank'}, {'label':'Target','field':'index'} ]  
          (list of dicts with fields) data (each dict is a row, each field is the column for that row): 
            (int) index : index of target
            (int) ranking : rank (0 to number of targets - 1) representing belief of being best arm
        """
        item = app.getModel(json.dumps({'exp_uid':app.exp_uid, 'args': {'alg_label':alg_label}}))
        return_dict = {}
        return_dict['headers'] = [{'label':'Rank','field':'rank'},
                                  {'label':'Target','field':'index'},
                                  {'label':'Score','field':'score'},
                                  {'label':'Precision','field':'precision'}]
        for target in item['targets']:
            for key in ['score', 'precision']:
                target[key] = '{:0.5f}'.format(target[key])
        return_dict['data'] = item['targets']
        return_dict['plot_type'] = 'columnar_table'
        return return_dict


