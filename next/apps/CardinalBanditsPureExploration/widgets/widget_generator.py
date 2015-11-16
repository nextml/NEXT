from jinja2 import Environment, FileSystemLoader
import json
import os
from next.api.widgets_library.widget_prototype import Widget
import next.broker.broker
from next.api.resource_manager import ResourceManager
from next.api.targetmapper import TargetMapper

# Use the current directory for widget templates
TEMPLATES_DIRECTORY = os.path.dirname(__file__)
loader = FileSystemLoader(TEMPLATES_DIRECTORY)
env = Environment(loader=loader)

resource_manager = ResourceManager()
broker = next.broker.broker.JobBroker()
targetmapper = TargetMapper() 


class WidgetGenerator(Widget):

    
    def getQuery(self, args):
        """
        Generates a getQuery widget. 
        
        Input: ::\n
        	(dict) args 
        
        Output: ::\n
		(str) getQuery widget.
        """
        exp_uid = args['exp_uid']
        app_id = args['app_id']
        if 'participant_uid' in args['args'].keys():
            args['args']['participant_uid'] = '{}_{}'.format(exp_uid,
                                                         args['args']['participant_uid'])
        args_json = json.dumps(args['args'])
        response_json,didSucceed,message = broker.applyAsync(app_id,
                                                             exp_uid,
                                                             'getQuery',
                                                             args_json)        
        response_dict = eval(response_json)
        print 'response_dict', response_dict

        index = response_dict['target_indices'][0]['index']
        query = {}
        query['context'] = response_dict['context']
        query['context_type'] = response_dict['context_type']
        query['target'] = targetmapper.get_target_data(exp_uid, index)                                                       
        template = env.get_template('getQuery_widget.html')

        rating_options = []
        rating_options.append({'target_id':1,
                                   'primary_description':"unfunny",
                                   'primary_type':'text',
                                   'alt_description':1,
                                   'alt_type':'text'})
        rating_options.append({'target_id':2,
                                   'primary_description':"somewhat funny",
                                   'primary_type':'text',
                                   'alt_description':2,
                                   'alt_type':'text'})
        rating_options.append({'target_id':3,
                                   'primary_description':"funny",
                                   'primary_type':'text',
                                   'alt_description':3,
                                   'alt_type':'text'})
            
        return {'html': template.render(query = query,
                                        rating_options = rating_options),
                'args': response_dict }


    
    def processAnswer(self,args):
        """
        Generates a processAnswer widget. Uses the args format as specified in::\n
    		/next_backend/next/learningLibs/apps/TupleBanditsPureExploration
        
        Input: ::\n
        	(dict) args 
        """
        exp_uid = args["exp_uid"]
        app_id = resource_manager.get_app_id(exp_uid)
        
        try:
            target_winner = args['args']['target_winner']
        except:
            return {'message':('Failed to specify all arguments '
                               'or misformed arguments'),
                    'code':400,
                    'status':'FAIL',
                    'base_error':('[target_winner]. Missing required parameter'
                                  'in the JSON body or the post body'
                                  'or the query string')}, 400
        
        target_reward = int(target_winner)
        # Set the index winner.
        args['args']['target_reward'] = target_reward

        # Args from dict to json type
        args_json = json.dumps(args['args']) 
        # Execute processAnswer 
        response_json,didSucceed,message = broker.applyAsync(app_id,
                                                             exp_uid,
                                                             'processAnswer',
                                                             args_json)
        return { 'html':'success'}


    
    def getStats(self,args):
        """
        Generates a getStats widget. Uses the args format as specified in::\n
        /next_backend/next/learningLibs/apps/TupleBanditsPureExploration

        Returns a JSON object with the appropriate stats. 
        Eventually modify to push the whole plot forward.
        Input: ::\n
        (dict) args 
        """
        
        exp_uid = args["exp_uid"]
        app_id = resource_manager.get_app_id(exp_uid)
        args_json = json.dumps(args["args"])
        
        response_json,didSucceed,message = broker.applyAsync(app_id,
                                                             exp_uid,
                                                             'getStats',
                                                             args_json)
        response_dict = json.loads(response_json,parse_float=lambda o:round(float(o),4))
        try:
            for d in response_dict['data']:
                try:
                    # If a datapoint (d) has a key, attach a target to that datapoint.
                    if 'index' in d.keys():
                        try:
                            d['target'] = targetmapper.get_target_data(exp_uid,
                                                                       d["index"])
                        except:
                            print 'failed to get target'
                except:
                    pass
        except:
            # e.g. response_dict does not contain key "data"
            pass
        return { 'json':response_dict }


    def getInfo(self,args):
        """
        Generates a getInfo widget. Uses the args format as specified in::\n
            /next_backend/next/learningLibs/apps/TupleBanditsPureExploration
        
        Input: ::\n
            (dict) args 
        """
        info = {}
        response = resource_manager.get_experiment(args['exp_uid'])
        instructions_string = ('Click on bottom target '
                              'that is most similar to the top.')
        info['instructions'] = response.get('instructions',
                                            instructions_string)
        info['debrief'] = response.get('debrief', 'Thanks for participating')
        info['num_tries'] = response.get('num_tries', 100)
        print info
        return {'response': info}

