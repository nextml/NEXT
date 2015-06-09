#!/usr/bin/python
import time
import traceback
import next.utils as utils

import next.broker.broker
broker = next.broker.broker.JobBroker()

while(1):
	
	timestamp = utils.datetime2str(utils.datetimeNow())
	try:
		broker.refresh_domain_hashes()
	except Exception, err:
		error = traceback.format_exc()
		print error

	# wait 
	time.sleep(2)
