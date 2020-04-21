import random
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import pandas as pd
from scipy.sparse import vstack
from io import BytesIO
import numpy as np
import next.utils as utils
import time
import cPickle as pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import confusion_matrix
import ast
import json
import next.assistant.s3 as s3


def df2bytes(df):
    with BytesIO() as f:
        df.to_pickle(f)
        df_bytes = f.getvalue()
    return df_bytes


def bytes2df(bytes):
    with BytesIO(bytes) as f:
        df = pd.read_pickle(f)
    return df

def get_encode_dict():
    # Dict for encoding
    sample_dict = {"cell_line": 0, "in_vitro_differentiated_cells": 1, "induced_pluripotent_stem_cells": 2,
                   "primary_cells": 3, "stem_cells": 4, "tissue": 5}
    return sample_dict

def get_decode_list(label_list):
    decode_list = []
    for label in label_list:
        decoded_label = get_decode(label)
        decode_list.append(decoded_label)
    return decode_list

def get_decode(label):
    # Dict for encoding
    label = int(label)
    sample_dict = {0:"cell_line", 1:"in_vitro_differentiated_cells", 2:"induced_pluripotent_stem_cells",
                   3:"primary_cells", 4:"stem_cells", 5:"tissue"}
    return sample_dict.get(label)

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


def get_largest_values(X_unlabelled,lr_model,unlabelled_list,study_id_list,d):

    log_prob = lr_model.predict_log_proba(X_unlabelled)
    prob = lr_model.predict_proba(X_unlabelled)

    entropy = -log_prob * prob
    entropy_sum = entropy.sum(axis=1)
    entropy_df = pd.DataFrame()
    entropy_df['index'] = unlabelled_list
    entropy_df['prob'] = prob.tolist()
    entropy_df['entropy_sum'] = entropy_sum
    entropy_df['study_id'] = study_id_list

    entropy_df_sort = entropy_df.groupby(['study_id']).apply(lambda x: x.sort_values(['entropy_sum'], ascending=False))

    #BUFFER  = d
    #Removed buffer since d=8
    largest_val = entropy_df_sort.drop_duplicates(subset='study_id', keep='first').nlargest(d, 'entropy_sum')
    print(largest_val.head(5))
    return largest_val

def set_updated_acc(butler,X_train_len,acc_update):

    train_list = redis_mem_get(butler,'train_list')
    debug_print("train_list")
    debug_print(train_list)
    train_list.append(X_train_len)
    redis_mem_set(butler,'train_list', train_list)
    acc_list = redis_mem_get(butler,'acc_list')
    acc_list.append(acc_update)
    redis_mem_set(butler,'acc_list',acc_list)

def debug_print(print_item):
    utils.debug_print(print_item)

class MyAlg:


    def create_vector(self,data_df,bag_of_words):
        X_train_str = []

        for i, row in data_df.iterrows():
            # Adding key value pairs

            dict_tag_value = row['key_value']
            cur_ont = row['ontology_mapping']

            if cur_ont is '' or pd.isnull(cur_ont):
                ont_list = []
            else:
                ont_list = ast.literal_eval(cur_ont)

            str = ""

            # y_train.append(row['label'])
            dict_tag_value = ast.literal_eval(dict_tag_value)
            for tag, val in dict_tag_value.items():
                str += tag + " "
                bag_of_words.append(tag)
                str += val + " "
                bag_of_words.append(val)

            for ont in ont_list:
                bag_of_words.append(ont)
                str += ont + " "

            X_train_str.append(str)
        return X_train_str


    def create_dict(self,data_df,bag_of_words):
        X_train_str = []
        y_train = []
        #debug_print(data_df)
        for i, row in data_df.iterrows():
            # Adding key value pairs

            dict_tag_value = row['key_value']
            cur_ont = row['ontology_mapping']
            y_train.append(row['label'])

            if cur_ont is '' or pd.isnull(cur_ont):
                ont_list = []
            else:
                ont_list = ast.literal_eval(cur_ont)

            str = ""
            dict_tag_value = ast.literal_eval(dict_tag_value)

            for tag, val in dict_tag_value.items():

                str += tag + " "
                bag_of_words.append(tag)
                str += val + " "
                bag_of_words.append(val)

            for ont in ont_list:
                bag_of_words.append(ont)
                str += ont + " "

            X_train_str.append(str)

        return X_train_str,y_train

    def initExp(self, butler, n, d ,failure_probability):
        # Save the number of targets, dimension, and failure_probability to algorithm storage

        mongo_mem_set(butler,'n',n)
        mongo_mem_set(butler,'delta', failure_probability)
        mongo_mem_set(butler,'d', d)
        # Initialize the weight to an empty list of 0's
        mongo_mem_set(butler,'num_reported_answers', 0)
        mongo_mem_set(butler,'sample_list', [])

        #Train data form butler mem

        train_df = redis_mem_get(butler,"train_data")
        test_df = redis_mem_get(butler,"test_data")
        unlabelled_df = redis_mem_get(butler,"unlabelled_data")

        bag_of_words = []
        N = 2

        X_train_str,y_train = self.create_dict(train_df, bag_of_words)
        X_test_str, y_test = self.create_dict(test_df, bag_of_words)
        X_unlabelled_str = self.create_vector(unlabelled_df,bag_of_words)

        #Encode y_train and y_test
        y_train = pd.Series(y_train)
        sample_dict = get_encode_dict()
        y_train = y_train.replace(sample_dict).values

        y_test = pd.Series(y_test)
        y_test = y_test.replace(sample_dict).values

        # create the transform
        vectorizer = TfidfVectorizer(ngram_range=(1, N + 1), max_features=75,decode_error='ignore')
        # tokenize and build vocab
        try:
            vectorizer.fit(bag_of_words)
        except Exception as e:
            debug_print(e)

        # encode document
        try:
            X_train = vectorizer.transform(X_train_str)
        except Exception as e:
            debug_print(e)

        try:
            X_test = vectorizer.transform(X_test_str)
        except Exception as e:
            debug_print(e)

        try:
            X_unlabelled = vectorizer.transform(X_unlabelled_str)
        except Exception as e:
           debug_print(e)

        lr_model = LogisticRegression(penalty='l1')
        lr_model.fit(X_train, y_train)
        y_pred = lr_model.predict(X_test)
        acc_init = accuracy_score(y_test,y_pred)
        debug_print("acc in init")
        debug_print(acc_init)
        set_updated_acc(butler,X_train.shape[0],acc_init)
        unlabelled_list = redis_mem_get(butler,"unlabelled_list")
        study_id_list = redis_mem_get(butler,"study_id_list")
        largest_val = get_largest_values(X_unlabelled, lr_model, unlabelled_list, study_id_list, d)

        debug_print(largest_val)
        d = mongo_mem_get(butler,'d')
        debug_print("new d")
        debug_print(d)
        sample_list = largest_val['index'].tolist()
        # sample_study_id_list = largest_val['prob'].values
        sample_probs = largest_val['prob'].tolist()

        #DEBUG

        debug_print("largest val init")
        debug_print(largest_val)
        debug_print("sample prob init")
        debug_print(sample_probs)
        lr_classes = get_decode_list(lr_model.classes_)
        redis_mem_set(butler,'lr_classes', lr_classes)
        mongo_mem_set(butler,'X_train', X_train)
        mongo_mem_set(butler,'y_train', y_train)
        mongo_mem_set(butler,'X_test', X_test)
        mongo_mem_set(butler,'y_test', y_test)
        debug_print(len(unlabelled_df))
        mongo_mem_set(butler,'unlabelled_len',len(unlabelled_df))
        mongo_mem_set(butler,'labelled_list', [])
        redis_mem_set(butler,"X_unlabelled",X_unlabelled)
        #Setting sample list and probability
        mongo_mem_set(butler,'sample_probs', sample_probs)
        mongo_mem_set(butler,'sample_list', sample_list)
        #TODO
        butler.memory.set("S_trial", json.dumps({}))
        cm = confusion_matrix(y_test,y_pred)
        redis_mem_set(butler,"confusion_matrix",cm)
        return True


    def getQuery(self, butler, participant_uid):
        # Retrieve the number of targets and return the index of one at random

        sample_list = mongo_mem_get(butler,'sample_list')
        sample_probs = mongo_mem_get(butler,'sample_probs')
        unlabelled_list =  redis_mem_get(butler,"unlabelled_list")
        cur_confidence = []

        if(len(sample_list)==0):
            # Random sampling
            idx = random.sample(unlabelled_list,1)[0]
            debug_print("random sampling")

        else:
            #Uncertainity Sampling
            idx = sample_list.pop(0)
            cur_confidence = sample_probs.pop(0)
            debug_print("uncertainity sampling")

        debug_print(idx)
        debug_print(cur_confidence)
        mongo_mem_set(butler,'sample_list',sample_list)
        mongo_mem_set(butler,'sample_probs',sample_probs)
        redis_mem_set(butler,'cur_confidence',cur_confidence)
        return idx

    def processAnswer(self, butler, target_index, target_label):

        # CONSTANTS
        UNLABELLED = -1
        # S maintains a list of labelled items. Appending to S will create it.
        if target_label != UNLABELLED:
            butler.algorithms.append(key='S', value=(target_index, target_label))
            S_trial_dict = json.loads(butler.memory.get("S_trial"))
            #Change for dashboard display
            S_trial_dict[target_index] = get_decode(target_label)
            butler.memory.set("S_trial", json.dumps(S_trial_dict))

            # Increment the number of reported answers by one.
            num_reported_answers = butler.algorithms.increment(key='num_reported_answers')
            # Run a model update job after every d answers
            d = mongo_mem_get(butler,'d')
            if num_reported_answers % int(d) == 0:
                butler.job('full_embedding_update', {}, time_limit=100)
        return True

    def getModel(self, butler):
        # The model is simply the vector of weights and a record of the number of reported answers.
        debug_print(mongo_mem_get(butler,['weights', 'num_reported_answers']))

        return mongo_mem_get(butler,['num_reported_answers'])


    def full_embedding_update(self, butler, args):
        debug_print("inside update new lrmodel")
        # Main function to update the model.
        labelled_items = mongo_mem_get(butler,'S')
        X_test = mongo_mem_get(butler,"X_test")
        y_test = mongo_mem_get(butler,"y_test")

        X_train = mongo_mem_get(butler,"X_train")
        y_train = mongo_mem_get(butler,"y_train")

        debug_print("inside full update")
        X_unlabelled = redis_mem_get(butler,"X_unlabelled")


        #Get unlabelled lists
        unlabelled_list = redis_mem_get(butler,"unlabelled_list")
        labelled_list = mongo_mem_get(butler,"labelled_list")

        # Build a list of feature vectors and associated labels.
        X_unlabelled_list = list(X_unlabelled)
        X_labelled_list = []
        y_labelled = []
        labelled_index = []

        bucket_id = redis_mem_get(butler,"bucket_id")
        batch_no = redis_mem_get(butler,"batch_no")
        s3.modify_csv_contents(bucket_id, 'Labels.csv', labelled_items,batch_no)
        redis_mem_set(butler,"batch_no",batch_no+1)

        for index, label in labelled_items:

            X_labelled_list.append(X_unlabelled_list[index])
            y_labelled.append(label)
            labelled_index.append(index)
            labelled_row = redis_mem_get(butler,str(index))
            labelled_list.append({labelled_row['sra_sample_id']:label})

        debug_print("X_labelled_list")
        debug_print(X_labelled_list)
        X_labelled = vstack(X_labelled_list)
        X_train = vstack([X_labelled,X_train])
        y_train = np.concatenate((y_labelled ,y_train))

        mongo_mem_set(butler,"X_train", X_train)
        mongo_mem_set(butler,"y_train", y_train)
        study_id_list = redis_mem_get(butler,"study_id_list")
        #Drop newly labelled data from unlabelled

        for curr_index in sorted(labelled_index, reverse=True):
            debug_print("removing curr_index")
            debug_print(curr_index)
            if (curr_index in unlabelled_list):
                debug_print("curr_index exists")
                curr_index_pos = unlabelled_list.index(curr_index)
                X_unlabelled_list.pop(curr_index_pos)
                unlabelled_list.pop(curr_index_pos)
                study_id_list.pop(curr_index_pos)

        # Performing training
        lr_model = LogisticRegression(fit_intercept=True)
        lr_model.fit(X_train, y_train)
        lr_classes = get_decode_list(lr_model.classes_)
        redis_mem_set(butler,'lr_classes',lr_classes)

        y_pred = lr_model.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        redis_mem_set(butler,"confusion_matrix",cm)
        acc_update = accuracy_score(y_test,y_pred)
        debug_print("acc in update")
        debug_print(acc_update)
        set_updated_acc(butler, X_train.shape[0], acc_update)
        #Get d
        d = mongo_mem_get(butler,'d')
        sample_list = mongo_mem_get(butler,"sample_list")
        #Get queries with largest entropy
        if(len(sample_list)<= 2*d):

            X_unlabelled = vstack(X_unlabelled_list)
            largest_val = get_largest_values(X_unlabelled,lr_model,unlabelled_list,study_id_list,d)
            sample_probs = mongo_mem_get(butler,"sample_probs")
            sample_list = sample_list + largest_val['index'].tolist()
            sample_probs = sample_probs + largest_val['prob'].tolist()
            #DEBUG
            debug_print("sample_list")
            debug_print(sample_list)
            mongo_mem_set(butler,'sample_list',sample_list)
            mongo_mem_set(butler,'sample_probs', sample_probs)


        mongo_mem_set(butler,'S', [])
        mongo_mem_set(butler,'labelled_list',labelled_list)


