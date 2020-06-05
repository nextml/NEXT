import random
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import pandas as pd
from scipy.sparse import vstack,hstack
from io import BytesIO
import numpy as np
import next.utils as utils
import time
import cPickle as pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import confusion_matrix
import ast
import json
import next.constants as constants
import next.assistant.s3 as s3
import os

#Creates vector from the custom rules specified in the metaSRA paper
def rules_vector(ontologies,key_value,cvcl_og):

    ontologies = set(ontologies)
    vector = {"not_tissue": 0, "not_cell_line": 0, "not_primary_cells": 0,
                      "not_in_vitro_differentiated_cells": 0,
                      "not_induced_pluripotent_stem_cells": 0, "not_stem_cells": 0}
    all_types = set([
          "cell_line",
          "in_vitro_differentiated_cells",
          "induced_pluripotent_stem_cells",
          "stem_cells",
          "tissue",
          "primary_cells"
        ])
    cellosaurus_subset_to_possible_types = {
      "Induced_pluripotent_stem_cell": [
        "in_vitro_differentiated_cells",
        "induced_pluripotent_stem_cells"
      ],
      "Cancer_cell_line": [
        "cell_line"
      ],
      "Transformed_cell_line": [
        "cell_line"
      ],
      "Finite_cell_line": [
        "cell_line"
      ],
      "Spontaneously_cell_line": [
        "cell_line"
      ],
      "Embryonic_stem_cell": [
        "stem_cells",
        "in_vitro_differentiated_cells"
      ],
      "Telomerase_cell_line": [
        "cell_line"
      ],
      "Conditionally_cell_line": [
        "cell_line"
      ],
      "Hybridoma": [
        "cell_line"
      ]
    }
    #initialize vector

    if "EFO:0003942" in ontologies:
      for typ in all_types:
        if typ is not "not_tissue":
            vector[typ] = 1
    else:

        # If the cell was passaged then we assert the sample is not a
        # tissue or primary cell sample
        is_passaged = False
        if "passage number" in key_value:
            is_passaged = True
            vector["not_tissue"] = 1
            if key_value["passage number"] > 0:
                vector["not_primary_cells"] = 1

        # Find the cell-line type in the Cellosaurus
        found_cell_line_type = False
        for ont in ontologies:
            if ont.split(":")[0] == "CVCL":
                for subset in cvcl_og.id_to_term[ont].subsets:
                    if subset in cellosaurus_subset_to_possible_types:
                        zero_types = all_types.difference(set(cellosaurus_subset_to_possible_types[subset]))
                        for typ in zero_types:
                            vector["not"+typ] = 1
                        found_cell_line_type = True
        # If the cell-line type is not found, then rule out possible
        # categories based on mapped ontology terms

        if not found_cell_line_type:
            # If 'stem cell' is mapped, then it can't be an immortalized
            # cell line, tissue, or primary cell sample
            if "CL:0000034" in ontologies:
                # print("Sample mapped to stem cell term CL:0000034"
                vector["not_cell_line"] = 1
                vector["not_tissue"] = 1
                vector["not_primary_cells"] = 1

            # If a specific cell-type is mapped, then it likely is
            # not a tissue sample
            elif "CL:0002371" in ontologies:
                # print("Sample mapped to a specific cell-type as indicated by mapped term CL:0002371" )
                vector["not_tissue"] = 1


            # If 'primary cultured cell'  is mapped, and the
            # cells have not been passaged, then it is likely
            # not tissue, iPSC, cell line, or in vitro
            # differentiated cell
            if "CL:0000001" in ontologies and not is_passaged:
              vector["not_tissue"] = 1
              vector["not_cell_line"] = 1
              vector["not_induced_pluripotent_stem_cells"] = 1
              vector["not_in_vitro_differentiated_cells"] = 1

    return vector


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

#Setting key,value in redis memory
def redis_mem_set(butler,key,value):
    # Butler.memory is essentially set in redis
    try:
        butler.memory.set(key,pickle.dumps(value))
    except Exception as e:
        debug_print("Could not set "+key+" in redis")

#Getting key,value from redis memory
def redis_mem_get(butler,key):
    # Butler.memory is essentially set in redis
    value = None
    try:
        value = pickle.loads(butler.memory.get(key))
    except Exception as e:
        debug_print("Could not get "+key+" from redis")
    return value

#Setting key,value in mongoDB
def mongo_mem_set(butler,key,value):
    #Butler.algorithms is essentially set in mongoDB
    try:
        butler.algorithms.set(key=key,value=value)
    except Exception as e:
        debug_print("Could not set "+key+" in mongodb")

#Getting key,value from mongoDB
def mongo_mem_get(butler,key):
    # Butler.algorithms is essentially set in mongoDB
    value = None
    try:
        value = butler.algorithms.get(key=key)
    except Exception as e:
        debug_print("Could not get "+key+" from Mongodb")
    return value

#This function calculates the entropy of all queries and chooses d+BUFFER most
#uncertain queries
def get_largest_values(X_unlabelled,lr_model,unlabelled_list,study_id_list,d):

    log_prob = lr_model.predict_log_proba(X_unlabelled)
    prob = lr_model.predict_proba(X_unlabelled)
    # calculating entropy (to measure uncertainity)
    entropy = -log_prob * prob
    entropy_sum = entropy.sum(axis=1)
    entropy_df = pd.DataFrame()
    entropy_df['index'] = unlabelled_list
    entropy_df['prob'] = prob.tolist()
    entropy_df['entropy_sum'] = entropy_sum
    entropy_df['study_id'] = study_id_list
    # grouping entropy based on study id and then taking the top from each group
    #This is to avoid samples from same study to be asked in same batch
    entropy_df_sort = entropy_df.groupby(['study_id']).apply(lambda x: x.sort_values(['entropy_sum'], ascending=False))
    #Buffer so that NEXT does not run out of queries to ask
    BUFFER  = d
    largest_val = entropy_df_sort.drop_duplicates(subset='study_id', keep='first').nlargest(d+BUFFER, 'entropy_sum')
    #print(largest_val.head(5))
    return largest_val

#This function sets the updated accuracy.This functionality is used
#for setting data used in acc plot in the dashboard
def set_updated_acc(butler,X_train_len,acc_update):

    train_list = mongo_mem_get(butler,'train_list')
    if train_list is None:
        train_list = []
    debug_print("train_list")
    debug_print(train_list)
    train_list.append(X_train_len)
    mongo_mem_set(butler,'train_list', train_list)
    acc_list = mongo_mem_get(butler,'acc_list')
    if acc_list is None:
        acc_list = []
    acc_list.append(acc_update)
    mongo_mem_set(butler,'acc_list',acc_list)

def debug_print(print_item):
    utils.debug_print(print_item)

#Creates vector from the key-value in metadata and ontologies
def create_word_vector(data_df,is_label,bag_of_words,ob,cvcl_og):
    X_train_str = []
    y_train = []
    rules_vector_dict_list = []
    for i, row in data_df.iterrows():
        # Adding key value pairs
        dict_tag_value = row['key_value']
        cur_ont = row['ontology_mapping']
        if is_label:
            y_train.append(row['label'])
        if cur_ont is '' or pd.isnull(cur_ont):
            ont_list = []
        else:
            ont_list = ast.literal_eval(cur_ont)

        str = ""
        # y_train.append(row['label'])
        dict_tag_value = ast.literal_eval(dict_tag_value)
        #Adding tag, values to the str and also appending to bag of words
        for tag, val in dict_tag_value.items():
            str = str+" "+tag + " " + val + " "
            bag_of_words.append(tag)
            bag_of_words.append(val)

        full_ont_list = []
        for ont in ont_list:
            bag_of_words.append(ont)
            str += ont + " "
            full_ont_list.append(ont)
            #Getting ancestors of each on ontology in the list
            ancestors = ob.get_ancestors(ont)
            for ancestor in ancestors:
                # debug_print(ancestor)
                bag_of_words.append(ancestor)
                full_ont_list.append(ancestor)
                str += ancestor.encode('utf-8') + " "
        X_train_str.append(str)
        rules_vector_dict_list.append(rules_vector(full_ont_list, dict_tag_value,cvcl_og))
    return X_train_str, y_train,rules_vector_dict_list


class MyAlg:
    # Data files stored inside NEXT/local
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    #Remove hardcode in future
    FILE_PATH = os.path.join(DIR_PATH ,'..',constants.PATH_FROM_myApp)
    utils.debug_print("LR "+FILE_PATH)

    def initExp(self, butler, n, d ,failure_probability):

        # Importing here as myApp gets initialized many times during
        #course of experiment
        from ..onto_lib import general_ontology_tools as ob
        from ..onto_lib import load_ontology
        #This is needed for rules_vector
        ONT_IDS = ["4"]
        OGS = [load_ontology.load(ont_id)[0] for ont_id in ONT_IDS]
        cvcl_og = OGS[0]

        mongo_mem_set(butler,'n',n)
        mongo_mem_set(butler,'delta', failure_probability)
        mongo_mem_set(butler,'d', d)
        # Initialize the weight to an empty list of 0's
        mongo_mem_set(butler,'num_reported_answers', 0)

        #Train data form butler mem

        train_df = redis_mem_get(butler,"train_data")
        test_df = redis_mem_get(butler,"test_data")
        unlabelled_df = redis_mem_get(butler,"unlabelled_data")
        #Initializing rules
        #Rules are negated as all custom rules were based on a sample being NOT of certain type
        rules_dict = {"not_tissue": 0, "not_cell_line": 0, "not_primary_cells": 0,
                      "not_in_vitro_differentiated_cells": 0,
                      "not_induced_pluripotent_stem_cells": 0, "not_stem_cells": 0}
        bag_of_words = []
        #Creating string so that it can be vectorized later
        X_train_str,y_train,train_rules = create_word_vector(train_df,True,bag_of_words,ob,cvcl_og)
        X_test_str, y_test,test_rules = create_word_vector(test_df,True,bag_of_words,ob,cvcl_og)
        X_unlabelled_str,empty_y_unlabelled,unlabelled_rules = create_word_vector(unlabelled_df,False,bag_of_words,ob,cvcl_og)

        #Encode y_train and y_test
        y_train = pd.Series(y_train)
        sample_dict = get_encode_dict()
        y_train = y_train.replace(sample_dict).values

        y_test = pd.Series(y_test)
        y_test = y_test.replace(sample_dict).values

        # create the transform
        #This vectorizer is used to vectorize key-value pairs,
        #ontologies and ancestors of each of the ontology
        word_vectorizer = TfidfVectorizer(decode_error='ignore',binary=True,max_features=75)
        # This vectorizer is used to vectorize custom rules
        rules_vectorizer = DictVectorizer()

        # transform word and rule vectors
        # Concatenate both vectors
        word_vectorizer.fit(bag_of_words)
        rules_vectorizer.fit([rules_dict])

        #DEBUG
        # utils.debug_print("word feature name")
        # utils.debug_print(word_vectorizer.get_feature_names())
        # utils.debug_print("rules feature name")
        # utils.debug_print(rules_vectorizer.get_feature_names())
        X_train_word = word_vectorizer.transform(X_train_str)
        X_test_word = word_vectorizer.transform(X_test_str)
        X_unlabelled_word = word_vectorizer.transform(X_unlabelled_str)

        X_train_rules = rules_vectorizer.transform(train_rules)
        X_test_rules = rules_vectorizer.transform(test_rules)
        X_unlabelled_rules = rules_vectorizer.transform(unlabelled_rules)
        #Combining bot vectors
        X_train = hstack([X_train_word,X_train_rules],format="csr")
        X_test = hstack([X_test_word, X_test_rules],format="csr")
        X_unlabelled = hstack([X_unlabelled_word, X_unlabelled_rules],format="csr")

        #DEBUG
        # utils.debug_print("size")
        # utils.debug_print(X_train_word)
        # utils.debug_print(X_test_word)
        # utils.debug_print(X_unlabelled_word)
        #
        # utils.debug_print(X_train_rules)
        # utils.debug_print(X_test_rules)
        # utils.debug_print(X_unlabelled_rules)
        #
        # utils.debug_print("the matrices")
        # utils.debug_print(X_train)
        # utils.debug_print(X_test)
        # utils.debug_print(X_unlabelled)

        lr_model = LogisticRegression(solver='sag')
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
        sample_list = largest_val['index'].tolist()
        sample_probs = largest_val['prob'].tolist()

        #DEBUG
        # debug_print("largest val init")
        # debug_print(largest_val)
        # debug_print("sample prob init")
        # debug_print(sample_probs)

        lr_classes = get_decode_list(lr_model.classes_)
        # Print model parameters - the names and coefficients are in same order
        utils.debug_print(lr_model.coef_)
        mongo_mem_set(butler,'lr_classes', lr_classes)
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
        redis_mem_set(butler,'sample_probs', sample_probs)
        redis_mem_set(butler,'sample_list', sample_list)
        mongo_mem_set(butler,"S_trial",json.dumps({}))
        cm = confusion_matrix(y_test,y_pred)
        mongo_mem_set(butler,"confusion_matrix",cm)
        return True


    def getQuery(self, butler, participant_uid):
        # Retrieve the number of targets and return the index of one at random

        sample_list = redis_mem_get(butler,'sample_list')
        sample_probs = redis_mem_get(butler,'sample_probs')
        #DEBUG
        # utils.debug_print("inside query")
        # utils.debug_print(sample_list)
        # utils.debug_print(sample_probs)
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

        #DEBUG
        debug_print(idx)
        debug_print(cur_confidence)
        redis_mem_set(butler,'sample_list',sample_list)
        redis_mem_set(butler,'sample_probs',sample_probs)
        redis_mem_set(butler,'cur_confidence',cur_confidence)
        return idx

    def processAnswer(self, butler, target_index, target_label):

        # CONSTANTS
        UNLABELLED = -1
        # S maintains a list of labelled items. Appending to S will create it.
        if target_label != UNLABELLED:
            butler.algorithms.append(key='S', value=(target_index, target_label))
            S_trial_dict = json.loads(mongo_mem_get(butler,"S_trial"))
            #Change for dashboard display
            S_trial_dict[target_index] = get_decode(target_label)
            mongo_mem_set(butler, 'S_trial', json.dumps(S_trial_dict))
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

    #Update occurs for every d queries(this value is specified in init.yaml)
    def full_embedding_update(self, butler, args):
        debug_print("inside update new lrmodel")
        # Main function to update the model.
        labelled_items = mongo_mem_get(butler,'S')
        X_test = mongo_mem_get(butler,"X_test")
        y_test = mongo_mem_get(butler,"y_test")
        #DEBUG
        # debug_print("X_test")
        # debug_print(X_test)
        X_train = mongo_mem_get(butler,"X_train")
        y_train = mongo_mem_get(butler,"y_train")
        #DEBUG
        # debug_print("X_train")
        # debug_print(X_train)
        debug_print("inside full update")
        X_unlabelled = redis_mem_get(butler,"X_unlabelled")

        #Get unlabelled lists
        unlabelled_list = redis_mem_get(butler,"unlabelled_list")
        labelled_list = mongo_mem_get(butler,"labelled_list")

        # Build a list of feature vectors and associated labels.
        utils.debug_print(X_unlabelled)
        X_unlabelled_list = list(X_unlabelled)
        X_labelled_list = []
        y_labelled = []
        labelled_index = []
        bucket_id = redis_mem_get(butler,"bucket_id")
        batch_no = redis_mem_get(butler,"batch_no")
        #Use this if you need to integrate with Amazon s3
        # s3.modify_csv_contents(bucket_id, 'Labels.csv', labelled_items,batch_no)
        #Modify contents - getting labels df
        labels_filename = os.path.join(self.FILE_PATH ,"Labels.csv")
        labels_df = pd.read_csv(labels_filename)
        redis_mem_set(butler,"batch_no",batch_no+1)

        #Iterate through the labelled items and change labels file
        for index, label in labelled_items:
            X_labelled_list.append(X_unlabelled_list[index])
            y_labelled.append(label)
            labelled_index.append(index)
            labelled_row = redis_mem_get(butler,str(index))
            if labelled_row is not None:
                labelled_list.append({labelled_row['sra_sample_id']:label})
                #Updating labels file
                labels_df.loc[index, 'label'] = get_decode(label)
                labels_df.loc[index, 'dataset_type'] = 'train'
                labels_df.loc[index, 'batch_no'] = batch_no

        labels_df.to_csv(labels_filename,index=False)
        debug_print("X_labelled_list")
        debug_print(X_labelled_list)
        X_labelled = vstack(X_labelled_list)
        #Combine X_train and newly labelled vector
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
                #unlabelled_list consist of indices that are unlabelles
                #Remove indices that currently got labelled from this list
                #Remove from lists parallel to this which are X_unlabelled_list and study_id_list
                curr_index_pos = unlabelled_list.index(curr_index)
                X_unlabelled_list.pop(curr_index_pos)
                unlabelled_list.pop(curr_index_pos)
                study_id_list.pop(curr_index_pos)

                if (curr_index in unlabelled_list):
                    utils.debug_print("index did not get removed oops")

        # Performing training (Retraining model along with newly labelled samples)
        lr_model = LogisticRegression(solver='sag')
        utils.debug_print("X_train_len")
        utils.debug_print(X_train.shape[0])
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
        sample_list = redis_mem_get(butler,"sample_list")
        #Get queries with largest entropy
        if(len(sample_list)<= 2*d):

            X_unlabelled = vstack(X_unlabelled_list)
            largest_val = get_largest_values(X_unlabelled,lr_model,unlabelled_list,study_id_list,d)
            sample_probs = redis_mem_get(butler,"sample_probs")
            #Contains next set of queries to be asked
            sample_list = sample_list + largest_val['index'].tolist()
            # Contains probabilities of the next set of queries to be asked
            sample_probs = sample_probs + largest_val['prob'].tolist()
            #DEBUG
            debug_print("sample_list")
            debug_print(sample_list)
            redis_mem_set(butler,'sample_list',sample_list)
            redis_mem_set(butler,'sample_probs', sample_probs)

        mongo_mem_set(butler,'S', [])
        mongo_mem_set(butler,'labelled_list',labelled_list)


