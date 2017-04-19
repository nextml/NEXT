import pytest
import datetime

from next.logging_client.LoggerAPI import LoggerAPI
import next.utils as utils

# IMPORTANT NOTE: only uses the `test_logger_data` database; it gets cleared after each test session
MONGO_HOST, MONGO_PORT = 'localhost', 27017
MONGO_DB = 'test_logger_data'

# === fixtures ===
@pytest.fixture(scope='module')
def lapi():
    lapi = LoggerAPI(MONGO_HOST, MONGO_PORT, MONGO_DB)
    yield lapi
    lapi.client.drop_database(MONGO_DB)
    lapi.client.close()

# === tests ===
def test_log(lapi):
    B = 'test_log'

    now = utils.datetimeNow()
    log_entry = {'a': 2, 'timestamp': now}

    lapi.log(B, log_entry)
    assert lapi._bucket(B).find_one({'timestamp': now}).get('a') == 2

def test_get_logs_with_filter(lapi):
    B = 'test_get_logs_with_filter'

    now = utils.datetimeNow()
    log_entry = {'a': 2, 'timestamp': now}

    lapi.log(B, log_entry)
    retrieved_entry = lapi.get_logs_with_filter(B, {'timestamp': now})
    assert len(retrieved_entry) == 1
    assert retrieved_entry[0].get('a') == 2

def test_delete_logs_with_filter(lapi):
    B = 'test_delete_logs_with_filter'

    lapi._bucket(B).insert_many([{'a': 2}, {'a': 2, 'b': 3}, {'a': 6}])

    lapi.delete_logs_with_filter(B, {'a': 2})

    logs = [{k:v for k, v in d.items() if k != '_id'} for d in lapi._bucket(B).find()]
    assert logs == [{'a': 6}]