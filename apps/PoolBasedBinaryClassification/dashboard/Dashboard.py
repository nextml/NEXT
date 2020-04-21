import json
import numpy
import numpy.random
from datetime import datetime
from datetime import timedelta
import next.utils as utils
from next.apps.AppDashboard import AppDashboard
import cPickle as pickle
# import next.database_client.DatabaseAPIHTTP as db
# import next.logging_client.LoggerHTTP as ell
import seaborn as sn
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import mpld3
import base64
from io import BytesIO

class MyAppDashboard(AppDashboard):

    def __init__(self,db,ell):
        AppDashboard.__init__(self, db, ell)

    def get_confusion_matrix(self,app,butler):
        lr_classes = pickle.loads(butler.memory.get('lr_classes'))
        confusion_matrix = pickle.loads(butler.memory.get("confusion_matrix"))
        df_cm = pd.DataFrame(confusion_matrix,columns=lr_classes,index=lr_classes)
        plt.figure(figsize=(10, 7))
        fig = sn.heatmap(df_cm, annot=True).get_figure()
        #tmpfile = BytesIO()
        fig.savefig('conf_heatmap', format='png')
        dict_fig = mpld3.fig_to_dict(fig)
        dict_html = mpld3.fig_to_html(fig)
        with open('cm.json', 'w') as f:
            json.dump(dict_fig, f)
        return dict_html

    def get_confusion_matrix_img(self,app,butler):
        lr_classes = pickle.loads(butler.memory.get('lr_classes'))
        confusion_matrix = pickle.loads(butler.memory.get("confusion_matrix"))
        df_cm = pd.DataFrame(confusion_matrix,columns=lr_classes,index=lr_classes)
        SMALL_SIZE = 6
        matplotlib.rc('font', size=SMALL_SIZE)
        matplotlib.rc('axes', titlesize=SMALL_SIZE)
        plt.savefig('eg1', format='png')
        plt.show()
        #plt.figure(figsize=(20, 15))
        fig = sn.heatmap(df_cm, annot=True).get_figure()
        plt.gcf().subplots_adjust(left=0.2, bottom=0.25)
        tmpfile = BytesIO()
        fig.savefig(tmpfile, format='png')
        encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
        return '<img src=\'data:image/png;base64,{}\'>'.format(encoded)

    def get_target_and_labels(self,app,butler):

        S_trial = json.loads(butler.memory.get("S_trial"))
        S_trial_dict = {}
        S_trial_dict['data'] = S_trial
        return S_trial

    def error_plot(self, app, butler):
        x = pickle.loads(butler.memory.get('train_list'))
        y = pickle.loads(butler.memory.get('acc_list'))
        utils.debug_print('error_plot')
        utils.debug_print(x)
        utils.debug_print(y)
        fig, ax = plt.subplots()
        ax.plot(x,y,marker='o')
        ax.set_xlabel("Number of train samples")
        ax.set_ylabel("Accuracy")
        fig.savefig("acc_plot",format='png')
        plot_dict = mpld3.fig_to_dict(fig)
        plt.close()

        return plot_dict


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



