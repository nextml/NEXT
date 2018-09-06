from __future__ import print_function

class MyAlg:
    def initExp(self, butler):
        butler.algorithms.set(key='algorithms_foo', value='algorithms_bar')

        return True

    def getQuery(self, butler):

        assert butler.experiment.get(key='experiment_foo') == 'experiment_bar'
        assert butler.algorithms.get(key='algorithms_foo') == 'algorithms_bar'

        return True

    def processAnswer(self, butler):

        assert butler.experiment.get(key='experiment_foo') == 'experiment_bar'
        assert butler.algorithms.get(key='algorithms_foo') == 'algorithms_bar'

        return True

    def getModel(self, butler):

        return True
