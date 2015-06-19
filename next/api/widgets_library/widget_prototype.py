"""
A prototype class for widgets.
"""
from jinja2 import Environment, FileSystemLoader
import os


TEMPLATES_DIRECTORY = os.path.dirname(__file__)
loader = FileSystemLoader(TEMPLATES_DIRECTORY)
env = Environment(loader=loader)

class Widget:

    
    def getQuery(self, args):
        raise NotImplementedError

    def processAnswer(self, args):
        raise NotImplementedError
    
    def getStats(self,args):
        raise NotImplementedError
        
        
    def getInfo(self,args):
        raise NotImplementedError
        
    def get_widget(self,args):
        """
        Get the widget specified by args["name"].
        """
        
        widget = getattr(self, args['name'])
        return widget(args)

