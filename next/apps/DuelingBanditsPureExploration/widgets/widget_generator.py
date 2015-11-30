import os
import json

from jinja2 import Environment, FileSystemLoader

import next.broker.broker
from next.api.targetmapper import TargetMapper
from next.api.resource_manager import ResourceManager

# Use the current directory for widget templates
TEMPLATES_DIRECTORY = os.path.dirname(__file__)
env = Environment(loader=FileSystemLoader(TEMPLATES_DIRECTORY))

resource_manager = ResourceManager()
broker = next.broker.broker.JobBroker()
targetmapper = TargetMapper() 

class WidgetGenerator():
    def getQuery(self, args):
        """
        Generates a getQuery widget. 
        Uses the args format as specified in::\n
        /next_backend/next/learningLibs/apps/DuelingBanditsPureExploration
        
        Input: ::\n
        	(dict) args 
        
        Output: ::\n
		(str) getQuery widget.
        """
        exp_uid = args["exp_uid"]
        app_id = args["app_id"]
        if 'participant_uid' in args['args'].keys():
            args['args']['participant_uid'] = '{}_{}'.format(exp_uid,
                                                             args['args']['participant_uid'])
        args_json = json.dumps(args['args'])
        response_json,didSucceed,message = broker.applyAsync(app_id,
                                                             exp_uid,
                                                             'getQuery'
                                                             ,args_json)        
        response_dict = json.loads(response_json)
        for target_index in response_dict['target_indices']:
            target_index['target'] = targetmapper.get_target_data(exp_uid,
                                                                  target_index['index'])


        # parse out left and right targets accordingly
        query = {}
        for target in response_dict['target_indices']:
            query[target['label']] = target['target']

        # add context to query
        query['context_type'] = response_dict['context_type']
        query['context'] = response_dict['context']

        template = env.get_template('getQuery_widget.html')

        return {'html': template.render(query = query), 'args': response_dict }


    
    def processAnswer(self,args):
        """
        Generates a processAnswer widget. Uses the args format as specified in::\n
    		/next_backend/next/learningLibs/apps/DuelingBanditsPureExploration
        
        Input: ::\n
        	(dict) args 
        """
        exp_uid = args['exp_uid']
        app_id = resource_manager.get_app_id(exp_uid)
        
        try:
            target_winner = args['args']['target_winner']
        except:
            return {'message':('Failed to specify all arguments'
                               'or misformed arguments'),
                    'code':400,
                    'status':'FAIL',
                    'base_error':('[target_winner]. Missing required parameter'
                                  'in the JSON body or the post body or the'
                                  'query string')} , 400
                    
        
        index_winner = int(targetmapper.get_index_given_targetID(exp_uid,
                                                                 target_winner))
        
        # Set the index winner.
        args['args']["index_winner"] = index_winner

        # Args from dict to json type
        args_json = json.dumps(args["args"]) 
        # Execute processAnswer 
        response_json,didSucceed,message = broker.applyAsync(app_id,
                                                             exp_uid,
                                                             'processAnswer',
                                                             args_json)

        return {'html': 'success'}


    def getStats(self,args):
        """
        Generates a getStats widget. Uses the args format as specified in::\n
        /next_backend/next/learningLibs/apps/DuelingBanditsPureExploration

        Returns a JSON object with the appropriate stats. 
        Eventually modify to push the whole plot forward.
        
        Input: ::\n
        (dict) args 
        """
        exp_uid = args['exp_uid']
        app_id = resource_manager.get_app_id(exp_uid)
        args_json = json.dumps(args["args"])
        
        response_json,didSucceed,message = broker.applyAsync(app_id,
                                                             exp_uid,
                                                             'getStats',
                                                             args_json)
        response_dict = json.loads(response_json,
                                   parse_float=lambda o:round(float(o),4))
        try:
            for d in response_dict['data']:
                try:
                    # If a datapoint (d) has a key, attach a target to that datapoint.
                    if 'index' in d.keys():
                        try:
                            d['target'] = targetmapper.get_target_data(exp_uid, d["index"])
                        except:
                            print 'failed to get target'
                except:
                    pass
        except:
            # e.g. response_dict does not contain key "data"
            pass

        return {'json': response_dict}


    def getInfo(self,args):
        """
        Generates a getInfo widget. Uses the args format as specified in::\n
        /next_backend/next/learningLibs/apps/DuelingBanditsPureExploration
        
        Input: ::\n
        (dict) args 
        """
        info = {}
        response = resource_manager.get_experiment(args['exp_uid'])
        info['instructions'] = response.get('instructions',
                                            ('Click on bottom target that is'
                                             'most similar to the top.'))
        info['debrief'] = response.get('debrief', 'Thanks for participating.')
        info['num_tries'] = response.get('num_tries', 100)
        return {'response': info}
