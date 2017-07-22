import json
import numpy
import numpy.random
from datetime import datetime
from datetime import timedelta
import next.utils as utils
from next.apps.AppDashboard import AppDashboard
# import next.database_client.DatabaseAPIHTTP as db
# import next.logging_client.LoggerHTTP as ell

class MyAppDashboard(AppDashboard):

    def __init__(self,db,ell):
        AppDashboard.__init__(self, db, ell)

    def test_error_multiline_plot(self,app, butler):
        """
        Description: Returns multiline plot where there is a one-to-one mapping lines to
        algorithms and each line indicates the error on the validation set with respect to number of reported answers

        Expected input:
          None

        Expected output (in dict):
          (dict) MPLD3 plot dictionary
        """
        args = butler.experiment.get(key='args')
        alg_list = args['alg_list']
        test_alg_label = alg_list[0]['test_alg_label']

        test_queries = butler.db.get_docs_with_filter(app.app_id+':queries',{'exp_uid':app.exp_uid, 'alg_label':test_alg_label})

        test_S = [(query['target_index'], query['target_label']) 
                            for query in test_queries
                            if 'target_index' in query.keys()]

        targets = butler.targets.get_targetset(app.exp_uid)
        targets = sorted(targets,key=lambda x: x['target_id'])
        target_features = []

        for target_index in range(len(targets)):
            target_vec = targets[target_index]['meta']['features']
            target_vec.append(1.)
            target_features.append(target_vec)

        x_min = numpy.float('inf')
        x_max = -numpy.float('inf')
        y_min = numpy.float('inf')
        y_max = -numpy.float('inf')
        list_of_alg_dicts = []

        for algorithm in alg_list:
            alg_label = algorithm['alg_label']
            list_of_log_dict = self.ell.get_logs_with_filter(app.app_id+':ALG-EVALUATION',{'exp_uid':app.exp_uid, 'alg_label':alg_label})
            list_of_log_dict = sorted(list_of_log_dict, key=lambda item: utils.str2datetime(item['timestamp']) )
            x = []
            y = []
            for item in list_of_log_dict:
                num_reported_answers = item['num_reported_answers']
                weights = item['weights']

                err = 0.
                for q in test_S:
                    estimated_label = numpy.sign(numpy.dot( numpy.array(target_features[q[0]]), numpy.array(weights) ))
                    err += estimated_label*q[1]<0. #do the labels agree or not

                m = float(len(test_S))
                err = err/m
                x.append(num_reported_answers)
                y.append(err)

            x = numpy.argsort(x)
            x = [x[i] for i in x]
            y = [y[i] for i in x]
        
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
        ax.set_xlabel('Number of answered queries')
        ax.set_ylabel('Error on hold-out set')
        ax.set_xlim([x_min,x_max])
        ax.set_ylim([y_min,y_max])
        ax.grid(color='white', linestyle='solid')
        ax.set_title('Test Error', size=14)
        legend = ax.legend(loc=2,ncol=3,mode="expand")
        for label in legend.get_texts():
            label.set_fontsize('small')
        plot_dict = mpld3.fig_to_dict(fig)
        plt.close()

        return plot_dict



