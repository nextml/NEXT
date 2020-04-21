import numpy.random
import next.utils as utils
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import pandas as pd
from scipy.sparse import vstack
from io import BytesIO
import numpy as np
import time
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
import ast
from ..onto_lib import general_ontology_tools as ob
import unicodedata


class MyAlg:

    def append(self,butler,row,key = "data"):
        butler.memory.cache.lpush(key, pickle.dumps(row))

    def getitem(self, butler, index, key="data"):
        unlabelled_len = butler.algorithms.get(key="unlabelled_len")
        bytes_ = butler.memory.cache.lindex(key, unlabelled_len - index - 1)
        row = pickle.loads(bytes_)
        return row

    def df2bytes(self,df):
        with BytesIO() as f:
            df.to_pickle(f)
            df_bytes = f.getvalue()
        return df_bytes

    def bytes2df(self,bytes):
        with BytesIO(bytes) as f:
            df = pd.read_pickle(f)
        return df

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
                ancestors = ob.get_ancestors(ont)
                for ancestor in ancestors:
                    bag_of_words.append(ont)
                    str += ob.get_term_name(ancestor).encode('utf-8') + " "

            X_train_str.append(str)

        return X_train_str

    def create_dict(self,data_df,bag_of_words):
        X_train_str = []
        y_train = []
        #utils.debug_print(data_df)
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
            # y_train.append(row['label'])
            dict_tag_value = ast.literal_eval(dict_tag_value)

            for tag, val in dict_tag_value.items():

                str += tag + " "
                bag_of_words.append(tag)
                str += val + " "
                bag_of_words.append(val)

            flag = True
            for ont in ont_list:
                bag_of_words.append(ont)
                str += ont + " "
                ancestors = ob.get_ancestors(ont)

                for ancestor in ancestors:

                    bag_of_words.append(ont)
                    str += ob.get_term_name(ancestor).encode('utf-8') + " "

            X_train_str.append(str)

        return X_train_str,y_train

    def initExp(self, butler, n, d ,failure_probability):
        # Save the number of targets, dimension, and failure_probability to algorithm storage
        butler.algorithms.set(key='n', value=n)
        butler.algorithms.set(key='delta', value=failure_probability)
        butler.algorithms.set(key='d', value=d)
        # Initialize the weight to an empty list of 0's
        butler.algorithms.set(key='num_reported_answers', value=0)
        butler.algorithms.set(key='sample_list', value=[])

        #Train data form butler mem
        train_data_bytes = butler.memory.get("train_data")
        test_data_bytes = butler.memory.get("test_data")
        unlabelled_data_bytes = butler.memory.get("unlabelled_data")

        train_df = self.bytes2df(train_data_bytes)
        test_df = self.bytes2df(test_data_bytes)
        unlabelled_df = self.bytes2df(unlabelled_data_bytes)



        #Dict for encoding
        di = {"cell_line": 0 , "in_vitro_differentiated_cells": 1,"induced_pluripotent_stem_cells":2,
              "primary_cells":3,"stem_cells":4,"tissue":5}

        bag_of_words = []

        N = 2

        X_train_str,y_train = self.create_dict(train_df, bag_of_words)
        X_test_str, y_test = self.create_dict(test_df, bag_of_words)
        X_unlabelled_str = self.create_vector(unlabelled_df,bag_of_words)


        #Encode y_train and y_test
        y_train = pd.Series(y_train)
        y_train = y_train.replace(di)

        y_test = pd.Series(y_test)
        y_test = y_test.replace(di)

        # create the transform
        vectorizer = TfidfVectorizer(ngram_range=(1, N + 1), max_features=75,decode_error='ignore')
        # tokenize and build vocab
        try:
            vectorizer.fit(bag_of_words)
        except:
            utils.debug_print("It is lr vecotorizing issue")

        # encode document
        try:
            X_train = vectorizer.transform(X_train_str)
        except:
            utils.debug_print("It is lr train transform")

        try:
            X_test = vectorizer.transform(X_test_str)
        except:
            utils.debug_print("It is lr test transform")

        try:
            X_unlabelled = vectorizer.transform(X_unlabelled_str)
        except:
            utils.debug_print("It is lr unlabelled transform")

        lr_model = LogisticRegression(penalty='l1')
        lr_model.fit(X_train, y_train)

        study_id_list = pickle.loads(butler.memory.get("study_id_list"))

        y_pred = lr_model.predict(X_test)
        utils.debug_print("acc in init")
        utils.debug_print(accuracy_score(y_test,y_pred))

        butler.algorithms.set(key='lr_model', value=lr_model)
        butler.algorithms.set(key='X_train', value=X_train)
        butler.algorithms.set(key='y_train', value=y_train)
        butler.algorithms.set(key='X_test', value=X_test)
        butler.algorithms.set(key='y_test', value=y_test)
        utils.debug_print(len(unlabelled_df))
        butler.algorithms.set(key='unlabelled_len', value=len(unlabelled_df))
        butler.algorithms.set(key='unlabelled_list', value = range(0,len(unlabelled_df)))
        butler.algorithms.set(key='labelled_list', value=[])
        #Set X_unlabelled in memory
        butler.memory.set("X_unlabelled",pickle.dumps(X_unlabelled))

        # Set X_unlabelled in memory
        butler.algorithms.set(key='sample_list', value=[])
        return True


    def getQuery(self, butler, participant_uid):
        # Retrieve the number of targets and return the index of one at random

        sample_list = butler.algorithms.get(key='sample_list')
        d = butler.algorithms.get(key='d')
        X_unlabelled_len = butler.algorithms.get(key="unlabelled_len")
        num_reported_answers = butler.algorithms.increment(key='num_reported_answers')

        if(len(sample_list)==0):
            # Random sampling
            idx = numpy.random.choice(X_unlabelled_len)
            utils.debug_print("random sampling")
            utils.debug_print(idx)
        else:
            #Uncertainity Sampling
            idx = sample_list[num_reported_answers%int(d)]
            utils.debug_print("uncertainity sampling")
            utils.debug_print(idx)

        return idx

    def processAnswer(self, butler, target_index, target_label):
        # S maintains a list of labelled items. Appending to S will create it.
        butler.algorithms.append(key='S', value=(target_index, target_label))
        # Increment the number of reported answers by one.
        num_reported_answers = butler.algorithms.increment(key='num_reported_answers')
        # Run a model update job after every d answers
        d = butler.algorithms.get(key='d')
        if num_reported_answers % int(d) == 0:
            butler.job('full_embedding_update', {}, time_limit=100)
        return True

    def getModel(self, butler):
        # The model is simply the vector of weights and a record of the number of reported answers.
        utils.debug_print(butler.algorithms.get(key=['weights', 'num_reported_answers']))

        return butler.algorithms.get(key=['num_reported_answers'])


    def full_embedding_update(self, butler, args):
        utils.debug_print("inside update new lrmodel")
        # Main function to update the model.
        utils.debug_print("lr update")
        labelled_items = butler.algorithms.get(key='S')
        sra_study_id_list = butler.algorithms.get(key='sra_study_id_list')
        utils.debug_print("study list ")
        utils.debug_print(sra_study_id_list)
        #Get X_train,X_test and X_unlabelled

        X_test = butler.algorithms.get(key="X_test")
        y_test = butler.algorithms.get(key="y_test")

        X_train = butler.algorithms.get(key="X_train")
        y_train = butler.algorithms.get(key="y_train")

        utils.debug_print("inside full update")

        X_unlabelled = pickle.loads(butler.memory.get("X_unlabelled"))

        #Get unlabelled lists
        unlabelled_list = butler.algorithms.get(key = "unlabelled_list")
        labelled_list = butler.algorithms.get(key = "labelled_list")

        # Build a list of feature vectors and associated labels.

        X_unlabelled_list = list(X_unlabelled)


        X_labelled_list = []
        y_labelled = []
        labelled_index = []

        for index, label in labelled_items:

            X_labelled_list.append(X_unlabelled_list[index])
            y_labelled.append(label)
            labelled_index.append(index)
            labelled_item = butler.memory.get(str(index))
            labelled_list.append({labelled_item['sra_sample_id']:label})

        utils.debug_print("labelled_list")
        utils.debug_print(labelled_list)

        X_labelled = vstack(X_labelled_list)
        X_train = vstack([X_labelled,X_train])
        y_train = np.concatenate((y_labelled ,y_train))

        #Set new X_train and y_train in mem

        butler.algorithms.set(key="X_train",value = X_train)
        butler.algorithms.set(key="y_train", value= y_train)

        #Drop newly labelled data from unlabelled

        for curr_index in sorted(labelled_index, reverse=True):
            utils.debug_print("removing curr_index")
            utils.debug_print(curr_index)
            if (curr_index in unlabelled_list):
                utils.debug_print("curr_index exists")
                X_unlabelled_list.pop(unlabelled_list.index(curr_index))
                unlabelled_list.remove(curr_index)

        # Performing training
        lr_model = LogisticRegression(fit_intercept=True)
        lr_model.fit(X_train, y_train)
        y_pred = lr_model.predict(X_test)
        utils.debug_print("acc in update")
        utils.debug_print(accuracy_score(y_test,y_pred))

        #Set the new model
        utils.debug_print("Set model")
        butler.algorithms.set(key='lr_model',value=lr_model)
        utils.debug_print("done setting model")
        #Get d
        d = butler.algorithms.get(key='d')
        utils.debug_print("x unlabelled with changed index")
        study_id_list = pickle.loads(butler.memory.get("study_id_list"))

        X_unlabelled_list = []
        study_id_unlabelled = []

        for i in range(len(unlabelled_list)):

            X_unlabelled_list.append(X_unlabelled_list[i])
            study_id_unlabelled.append(study_id_list[i])

        X_unlabelled = vstack(X_unlabelled_list)
        log_prob = lr_model.predict_log_proba(X_unlabelled)
        prob = lr_model.predict_proba(X_unlabelled)

        entropy = -log_prob * prob
        entropy_sum = entropy.sum(axis=1)
        entropy_df = pd.DataFrame()
        entropy_df['index'] = unlabelled_list
        entropy_df['entropy_sum'] = entropy_sum
        entropy_df['study_id'] = study_id_unlabelled
        entropy_df = entropy_df.drop_duplicates(subset='study_id', keep="first")
        largest_val = entropy_df.nlargest(d,'entropy_sum')

        #Get queries with largest entropy
        sample_list = largest_val['index'].values
        sample_study_id_list = largest_val['study_id'].values

        utils.debug_print("sample list")
        utils.debug_print(sample_list)
        utils.debug_print("sample_study_id list")
        utils.debug_print(sample_study_id_list)

        #Set new list
        butler.algorithms.set(key='S', value = [])
        butler.algorithms.set(key='sample_list' , value=sample_list)
        butler.algorithms.set(key='labelled_list', value=labelled_list)


