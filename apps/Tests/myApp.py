import next.apps.SimpleTargetManager
from apps.Tests.tests.test_api import get_alg, get_exp, set_and_get_exp


class MyApp:
    def __init__(self,db):
        self.app_id = 'Tests'
        self.TargetManager = next.apps.SimpleTargetManager.SimpleTargetManager(db)

    def initExp(self, butler, init_algs, args):
        set_and_get_exp(butler)
        init_algs({})
        return args

    def getQuery(self, butler, alg, args):
        get_exp(butler)
        assert alg() == "return_get_query"
        return {}

    def processAnswer(self, butler, alg, args):
        get_exp(butler)
        assert alg({}) == "return_process_answer"
        return {}

    def getModel(self, butler, alg, args):
        get_exp(butler)
        assert alg() == "return_get_model"
        return True


