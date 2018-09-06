from apps.Tests.tests.test_api import set_and_get_alg, get_alg, get_exp


class MyAlg:
    def initExp(self, butler, dummy):
        get_exp(butler)
        set_and_get_alg(butler)
        return "return_init_exp"

    def getQuery(self, butler):
        get_alg(butler)
        return "return_get_query"

    def processAnswer(self, butler):
        get_alg(butler)
        return "return_process_answer"

    def getModel(self, butler):
        get_alg(butler)
        return "return_process_answer"


