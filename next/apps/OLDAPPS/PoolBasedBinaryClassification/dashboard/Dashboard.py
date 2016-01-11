import json
import numpy
from datetime import datetime
from datetime import timedelta
from next.utils import utils
from next.dashboard.AppDashboard import AppDashboard

class PoolBasedBinaryClassificationDashboard(AppDashboard):

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
        stat['stat_id'] = 'test_error_multiline_plot'
        stat['description'] = self.test_error_multiline_plot.__doc__
        stat['necessary_params'] = ['alg_label']
        stat_list.append(stat)
        
        return stat_list


    def test_error_multiline_plot(self,app_id,exp_uid):
        """
        Description: Returns multiline plot where there is a one-to-one mapping lines to 
        algorithms and each line indicates the error on the validation set with respect to number of reported answers

        Expected input:
          None

        Expected output (in dict):
          mpld3 plot object
        """

        # get list of algorithms associated with project
        alg_list,didSucceed,message = self.db.get(app_id+':experiments',exp_uid,'alg_list')

        x_min = numpy.float('inf')
        x_max = -numpy.float('inf')
        y_min = numpy.float('inf')
        y_max = -numpy.float('inf')
        list_of_alg_dicts = []

        for algorithm in alg_list:
            alg_id = algorithm['alg_id']
            alg_uid = algorithm['alg_uid']
            alg_label = algorithm['alg_label']

            list_of_log_dict,didSucceed,message = self.ell.get_logs_with_filter(app_id+':ALG-EVALUATION',{'alg_uid':alg_uid})
            list_of_log_dict = sorted(list_of_log_dict, key=lambda item: utils.str2datetime(item['timestamp']) )

            x = []
            y = []
            for item in list_of_log_dict:
                num_reported_answers = item['num_reported_answers']
                err = item['error']
                x.append(num_reported_answers)
                y.append(err)

        
            alg_dict = {}
            alg_dict['legend_label'] = alg_label
            alg_dict['x'] = x
            alg_dict['y'] = y
            try:
                x_min = min(x_min,min(x))
                x_max = max(x_max,max(x))
                y_min = min(y_min,min(y))
                y_max = max(y_max,max(y))
            except:
                pass

            list_of_alg_dicts.append(alg_dict)

        import matplotlib.pyplot as plt
        import mpld3
        fig, ax = plt.subplots(subplot_kw=dict(axisbg='#EEEEEE'))
        for alg_dict in list_of_alg_dicts:
            ax.plot(alg_dict['x'],alg_dict['y'],label=alg_dict['legend_label'])
        ax.set_xlabel('Number of answered triplets')
        ax.set_ylabel('Error on hold-out set')
        ax.set_xlim([x_min,x_max])
        ax.set_ylim([y_min,y_max])
        ax.grid(color='white', linestyle='solid')
        ax.set_title('Triplet Test Error', size=14)
        legend = ax.legend(loc=2,ncol=3,mode="expand")
        for label in legend.get_texts():
          label.set_fontsize('small')
        plot_dict = mpld3.fig_to_dict(fig)
        plt.close()

        return plot_dict