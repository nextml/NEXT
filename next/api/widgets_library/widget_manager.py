import next.apps.TupleBanditsPureExploration.widgets
import next.apps.DuelingBanditsPureExploration
import next.apps.PoolBasedTripletMDS


class widgetManager:
    """
    Class to manage the packaging and distribution of widgets. 
    
    Inputs: ::\n
    	(dict) args: parsed dictionary of a json request for the widget

    """
    def get_widget(self, args):
        """
        Given the args for a widget returns the widget. Otherwise returns a null error message. 
        
        Inputs: ::\n
            (dict) args

        Output: ::\n
        String representing the HTML or None if the code does not successfully get generated.
        """
        app = self.get_app(args['app_id'])
        return app.get_widget(args)        

    def get_app(self, app_id):
        """
        Given an app_id, get the associated widget app class.
        """
        # sometimes input is unicode formatted which causes error
        app_id = str(app_id) 
        app_module = __import__('next.apps.{}.widgets'.format(app_id),
                                fromlist=[app_id])
  
        app_class = getattr(app_module, "WidgetGenerator")
        return app_class()
