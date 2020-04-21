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
import sys
import csv
import next.assistant.s3 as s3
import io

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

def bytes2df(bytes):
    with BytesIO(bytes) as f:
        df = pd.read_pickle(f)
    return df


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


def set_debug(cache, key, value,i, verbose):
    try:
        _set(cache, key, value)
        if(verbose):
            print("setting"+str(key)+str(i))

    except Exception as e:
        utils.debug_print("WARNING: failed to set {}\n".format(key) + "=" * 40)
        utils.debug_print(e)
        return False
    return True

def redis_mem_set(butler,key,value):
    # Butler.memory is essentially set in redis
    butler.memory.set(key,pickle.dumps(value))

def redis_mem_get(butler,key):
    # Butler.memory is essentially set in redis
    value = pickle.loads(butler.memory.get(key))
    return value

def mongo_mem_set(butler,key,value):
    #Butler.algorithms is essentially set in mongoDB
    butler.algorithms.set(key=key,value=value)

def mongo_mem_get(butler,key):
    # Butler.algorithms is essentially set in mongoDB
    value = butler.algorithms.get(key=key)
    return value

def get_decode(label):
    label = int(label)
    sample_dict = {0: "cell_line", 1: "in_vitro_differentiated_cells", 2: "induced_pluripotent_stem_cells",
                   3: "primary_cells", 4: "stem_cells", 5: "tissue"}
    return sample_dict.get(label)

def get_decode_list(label_list):

    class_list = []
    for label in label_list:
        class_list.append(get_decode(label))
    return class_list

class MyApp:

    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    FILE_PATH = DIR_PATH + '/../../local/data_new_design'
    utils.debug_print(FILE_PATH)
    #train_filename = FILE_PATH + "/train.csv"
    # train_df = pd.read_csv(self.FILE_PATH+"/train.csv")


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
        # utils.debug_print("bucket_id")
        #bucket_id = butler.experiment.get(key='bucket_id')
        #utils.debug_print(bucket_id)
        # args["n"] = len(df)
        # Get the first target, extract it's feature vector and save this as the dimension
        UNLABELLED_TAG = 'unlabelled'
        TRAIN_TAG = 'train'
        TEST_TAG = 'test'

        '''dir_path = os.path.dirname(os.path.realpath(__file__))
        A = dir_path + '/../../local/data_final.zip'
        #utils.debug_print(A)
        archive = zipfile.ZipFile(A, 'r')
        train_filename = archive.extract('train.csv')'''
        bucket_id = args['bucket_id']
        key_id = args['key_id']
        secret_key = args['secret_key']

        file_name_list = ['samples.csv','Labels.csv','studies.csv']
        csv_content_dict = s3.get_csv_content_dict(bucket_id,file_name_list)
        for filename,content in csv_content_dict.items():
            if filename is 'samples.csv':
                samples_df =  pd.read_csv(io.BytesIO(content))
            elif filename is 'Labels.csv':
                labels_df = pd.read_csv(io.BytesIO(content))
            elif filename is 'studies.csv':
                study_df = pd.read_csv(io.BytesIO(content))

        #set(butler.memory, "samples_filename", samples_df)
        experiment = butler.experiment.get()
        #bucket_id = experiment['args']['bucket_id']

        set(butler.memory, "bucket_id", bucket_id)
        set(butler.memory, "key_id", key_id)
        set(butler.memory, "secret_key", secret_key)

        df_sort = labels_df.groupby(['dataset_type'])
        for dataset_type, df_cur in df_sort:
            if (dataset_type == UNLABELLED_TAG):
                unlabelled_indices = df_cur['index'].tolist()
            elif (dataset_type == TRAIN_TAG):
                train_indices = df_cur['index'].values
            elif (dataset_type == TEST_TAG):
                test_indices = df_cur['index'].values

        batch_no = labels_df['batch_no'].max()

        if pd.isnull(batch_no):
            batch_no = 0

        butler.memory.set("batch_no",pickle.dumps(batch_no+1))

        train_df =   samples_df.loc[samples_df['index'].isin(train_indices)]
        train_df['label'] = labels_df.loc[labels_df['index'].isin(train_indices),'label']

        test_df = samples_df.loc[samples_df['index'].isin(test_indices)]
        test_df['label'] = labels_df.loc[labels_df['index'].isin(test_indices), 'label']

        unlabelled_df = samples_df.loc[samples_df['index'].isin(unlabelled_indices)]
        study_id_list = unlabelled_df['sra_study_id'].tolist()

        for i,row in unlabelled_df.iterrows():
            set_debug(butler.memory, str(row['index']), row,i, verbose=i % 100 == 0)

        utils.debug_print("done setting unlabelled")

        for i,row in study_df.iterrows():
            set(butler.memory,row['sra_study_id'],row)

        train_list = []
        acc_list = []
        set(butler.memory,"study_id_list",study_id_list)
        # Set  data in mem
        set(butler.memory, "train_data", train_df)
        set(butler.memory, "test_data", test_df)
        set(butler.memory, "unlabelled_data", unlabelled_df[['key_value','ontology_mapping']])
        set(butler.memory, "label_data", labels_df)
        set(butler.memory, "unlabelled_list", unlabelled_indices)
        butler.memory.set("train_list", pickle.dumps(train_list))
        butler.memory.set("acc_list", pickle.dumps(acc_list))

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
        sra_sample_id = unlabelled_row_dict.get('sra_sample_id')
        key_value = unlabelled_row_dict.get('key_value')
        key_value_dict = ast.literal_eval(key_value)

        ontology_mapping = unlabelled_row_dict.get('ontology_mapping')
        ontology_mapping_list = ast.literal_eval(ontology_mapping)
        ont_mapping_dict = {}
        for ont in ontology_mapping_list:
            ont_org = ont
            return_link = ""
            ont = ont.replace(":", "_")

            '''
            "DOID": "DOID.17-01-30.obo",
            "UBERON": "UBERON.17-01-30.obo",
            "CL": "CL.18-11-13.obo",
            "CVCL": "CVCL.17-01-30.obo",
            "UO": "UO.17-01-30.obo",
            "EFO": "EFO.17-01-30.obo",
            "CHEXBI": "CHEBI.17-01-30.obo",
            "GO": "GO.19-01-18.obo"   '''

            #TODO: Other terms link
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


            ont_mapping_dict[ont_org] = return_link

        study_row_str = pickle.loads(butler.memory.get(sra_study_id)).replace(np.nan, "None")
        study_row_json = study_row_str.to_dict()
        #confidence = pickle.loads(butler.memory.get("class_confidence"))
        #utils.debug_print("cur_confidence")
        cur_confidence = pickle.loads(butler.memory.get("cur_confidence"))
        #utils.debug_print(cur_confidence)
        lr_classes = pickle.loads(butler.memory.get("lr_classes"))

        #remove key value from other
        ret = {'target_indices':unlabelled_row_dict,'study':study_row_json , 'key_value':key_value_dict ,'ontology_mapping': ont_mapping_dict,
               'cur_confidence':cur_confidence,'lr_classes':lr_classes,'sra_sample_id':sra_sample_id}

        return ret

    def processAnswer(self, butler, alg, args):
        query = butler.queries.get(uid=args['query_uid'])

        target = query['target_indices']
        target_label = args['target_label']
        utils.debug_print("type(target_label)")
        utils.debug_print(type(target_label))

        num_reported_answers = butler.experiment.increment(key='num_reported_answers_for_' + query['alg_label'])

        labelled_row = pickle.loads(butler.memory.get(str(target['index'])))
        if labelled_row is None:
            utils.debug_print("Labelled row doesnt exist")
            return {}
        # make a getModel call ~ every n/4 queries - note that this query will NOT be included in the predict
        experiment = butler.experiment.get()
        d = experiment['args']['d']
        # if num_reported_answers % ((d+4)/4) == 0:
        #     butler.job('getModel', json.dumps({'exp_uid':butler.exp_uid,'args':{'alg_label':query['alg_label'], 'logging':True}}))
        alg({'target_index':target['index'],'target_label':target_label})
        return {'target_index':target['index'],'target_label':target_label}

    def getModel(self, butler, alg, args):

        return alg()

