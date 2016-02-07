# TODO:
# o implement the functions below.
# o change the algorithm definitions (and what they return?)
# o look at diffs
# o explore the dashboard, see what you need to change
# - look at the butler code. Butler is another database wrapper
# x modify the tests to delete exp_key
# x check if daemonProcess still needed (I don't think it is)
# x Implement the .yaml file
#   modify the widgets?

class DuelingBanditsPureExploration(object):
    def initExp(self, exp_uid, args_json, db, ell):
        pass
    def getQuery(self, exp_uid, args_json, db, ell):
        pass
    def processAnswer(self, exp_uid, args_json, db, ell):
        pass
    def getStats(self, exp_uid, args_json, db, ell):
        pass
    def getModel(self, exp_uid, args_json, db, ell):
        pass
