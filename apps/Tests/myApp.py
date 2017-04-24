import json
import next.utils as utils
import next.apps.SimpleTargetManager

class MyApp:
    def __init__(self,db):
        self.app_id = 'Tests'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, init_algs, args):

        butler.experiment.set(key='experiment_foo', value='experiment_bar')

        init_algs({})

        return args

    def getQuery(self, butler, alg, args):

        assert butler.experiment.get(key='experiment_foo') == 'experiment_bar'

        assert alg()

        return {}

    def processAnswer(self, butler, alg, args):

        assert alg({})

        assert butler.experiment.get(key='experiment_foo') == 'experiment_bar'

        return {}

    def getModel(self, butler, alg, args):

        assert alg()

        return True
