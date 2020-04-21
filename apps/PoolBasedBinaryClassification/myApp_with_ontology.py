import json
import next.utils as utils
import next.apps.SimpleTargetManager
import numpy as np
import time
import pandas as pd
import zipfile
import os
import cPickle as pickle
import ast
from io import BytesIO
from decorator import decorator
from line_profiler import LineProfiler
from onto_lib import general_ontology_tools as ob
import sys


@decorator
def profile_each_line(func, *args, **kwargs):
    profiler = LineProfiler()
    profiled_func = profiler(func)
    retval = None
    try:
        retval = profiled_func(*args, **kwargs)
    finally:
        profiler.print_stats()
    return retval

def df2bytes(df):
    with BytesIO() as f:
        df.to_pickle(f)
        df_bytes = f.getvalue()
    return df_bytes

def _set(cache, key, value):
    if isinstance(value, (pd.Series, pd.DataFrame)):
        with BytesIO() as f:
          value.to_pickle(f)
          df_bytes = f.getvalue()
        cache.set(key, df_bytes)
    else:
        cache.set(key, pickle.dumps(value))
    return True

def set(cache, key, value, verbose=True):
    try:
        _set(cache, key, value)

    except Exception as e:
        utils.debug_print("WARNING: failed to set {}\n".format(key) + "=" * 40)
        utils.debug_print(e)
        return False
    return True


class MyApp:
    def __init__(self,db):
        self.app_id = 'PoolBasedBinaryClassification'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def append(butler,row,key = "data"):
        butler.memory.cache.lpush(key, pickle.dumps(row))

    def df2bytes(df):
        with BytesIO() as f:
            df.to_pickle(f)
            df_bytes = f.getvalue()
        return df_bytes

    def getitem(butler,index,key = "data"):
        unlabelled_len = butler.algorithms.get(key="unlabelled_len")
        bytes_ = butler.memory.cache.lindex(key,unlabelled_len-index-1)
        row = pickle.loads(bytes_)
        return row


    def initExp(self, butler, init_algs, args):
        args['n']  = len(args['targets']['targetset'])
        # args["n"] = len(df)
        # Get the first target, extract it's feature vector and save this as the dimension

        dir_path = os.path.dirname(os.path.realpath(__file__))
        A = dir_path + '/../../local/data_1k.zip'
        utils.debug_print(A)
        archive = zipfile.ZipFile(A, 'r')

        train_filename = archive.extract('train.csv')
        train_df = pd.read_csv(train_filename)

        #utils.debug_print("unlabelled_readtime")
        unlabelled_filename = archive.extract('unlabelled.csv')
        unlabelled_df = pd.read_csv(unlabelled_filename)

        #utils.debug_print("study_readtime")
        study_filename = archive.extract('studies.csv')
        study_df = pd.read_csv(study_filename)

        #utils.debug_print("test_readtime")
        test_filename = archive.extract('test.csv')
        test_df = pd.read_csv(test_filename)

        # Set unlabelled data in mem
        set(butler.memory, "train_data", train_df)
        set(butler.memory,"test_data", test_df)
        set(butler.memory,"unlabelled_data", unlabelled_df)

        study_id_list = []
        for i,row in unlabelled_df.iterrows():

            set(butler.memory,str(i),row, verbose=i % 100 == 0)
            #utils.debug_print(str(i)+"setting in mem"+ str(sys.getsizeof(row_dump)/1024.0))
            study_id_list.append(row['sra_study_id'])

        for i,row in study_df.iterrows():
            set(butler.memory,row['sra_study_id'],row)

        set(butler.memory,"study_id_list",study_id_list)
        alg_data = {'n': args['n'],
                    'failure_probability': args['failure_probability'],
                    'd': args['d']}

        init_algs(alg_data)
        return args



    def getQuery(self, butler, alg, args):

        sttime = time.time()
        alg_response = alg({'participant_uid':args['participant_uid']})

        # Get Unlabelled Set

        unlabelled_row = butler.memory.get(str(alg_response))
        if unlabelled_row is None:
            utils.debug_print("No row was retrieved")
            return {}

        unlabelled_row = pickle.loads(unlabelled_row).replace(np.nan, "None")
        unlabelled_row_dict = unlabelled_row.to_dict()

        sra_study_id = unlabelled_row_dict.get('sra_study_id')

        key_value = unlabelled_row_dict.get('key_value')
        key_value_dict = ast.literal_eval(key_value)

        ontology_mapping = unlabelled_row_dict.get('ontology_mapping')
        ontology_mapping_list = ast.literal_eval(ontology_mapping)
        ont_mapping_dict = {}
        for ont in ontology_mapping_list:
            ont_org = ont
            return_link = ""
            ont = ont.replace(":", "_")

            if "CL" in ont:
                return_link = "https://www.ebi.ac.uk/ols/ontologies/cl/terms?short_form=" + ont
            elif "UBERON" in ont:
                return_link = "https://www.ebi.ac.uk/ols/ontologies/uberon/terms?short_form=" + ont
            elif "DOID" in ont:
                return_link = "https://www.ebi.ac.uk/ols/ontologies/doid/terms?short_form=" + ont
            elif "EFO" in ont:
                return_link = "https://www.ebi.ac.uk/ols/ontologies/efo/terms?short_form=" + ont
            elif "CVCL" in ont:
                return_link = "https://web.expasy.org/cellosaurus/" + ont

            ont_mapping_dict[ob.get_term_name(ont_org)] = return_link

        study_row_str = pickle.loads(butler.memory.get(sra_study_id)).replace(np.nan, "None")
        study_row_json = study_row_str.to_dict()

        #remove key value from other
        ret = {'target_indices':unlabelled_row_dict,'study':study_row_json , 'key_value':key_value_dict ,'ontology_mapping': ont_mapping_dict }

        return ret

    def processAnswer(self, butler, alg, args):
        query = butler.queries.get(uid=args['query_uid'])

        target = query['target_indices']
        target_label = args['target_label']

        num_reported_answers = butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])

        # make a getModel call ~ every n/4 queries - note that this query will NOT be included in the predict
        experiment = butler.experiment.get()
        d = experiment['args']['d']
        # if num_reported_answers % ((d+4)/4) == 0:
        #     butler.job('getModel', json.dumps({'exp_uid':butler.exp_uid,'args':{'alg_label':query['alg_label'], 'logging':True}}))
        alg({'target_index':target['index'],'target_label':target_label})
        return {'target_index':target['index'],'target_label':target_label}

    def getModel(self, butler, alg, args):

        return alg()

