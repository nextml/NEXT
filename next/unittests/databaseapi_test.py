import pytest
import mock

from next.database_client.DatabaseAPI import to_db_fmt, from_db_fmt, DatabaseAPI

# IMPORTANT NOTE: only use the `app_data` database; it gets cleared after each test session
MONGO_HOST, MONGO_PORT = 'localhost', 27017


# === fixtures ===
@pytest.fixture(scope='module')
def db():
	db = DatabaseAPI(MONGO_HOST, MONGO_PORT)
	yield db
	db.client.drop_database('app_data')
	db.client.close()

# === basic tests ===
def test_connect(db):
	assert db.is_connected()

def test_reconnection(db):
	db.connect_mongo(MONGO_HOST, MONGO_PORT)
	assert db.is_connected()

# === test db functions ===
def test__bucket(db):
	assert db._bucket('foo') == db.client['app_data']['foo']

def test_exists(db):
	B = 'test_exists'

	doc_uid = db._bucket(B).insert_one({'a_key': 2}).inserted_id

	assert db.exists(B, doc_uid, 'a_key')
	assert not db.exists(B, doc_uid, 'a_nonexistent_key')
	assert not db.exists(B, 'ashkjfdbkjfns', 'a_key')

def test_get(db):
	B = 'test_get'

	doc_uid = db._bucket(B).insert_one({'a_key': 2, 'another_key': [1.0, 'f']}).inserted_id

	assert db.get(B, doc_uid, 'a_key') == 2
	assert db.get(B, doc_uid, 'another_key') == [1.0, 'f']
	assert not db.get(B, doc_uid, 'a_nonexistant_key')

def test_get_many(db):
	B = 'test_get_many'
	doc = {'a_key': 2, 'another_key': [1.0, 'f'], 'third_key': 'baz'}

	doc_uid = db._bucket(B).insert_one(doc).inserted_id

	assert db.get_many(B, doc_uid, ['another_key']) \
		== {'another_key': [1.0, 'f']}
	assert db.get_many(B, doc_uid, ['another_key', 'third_key']) \
		== {'another_key': [1.0, 'f'], 'third_key': 'baz'}

	assert db.get_many(B, doc_uid, ['totally_nonexistent_key', 'another_key']) \
		== {'totally_nonexistent_key': None, 'another_key': [1.0, 'f']}


# === test utils ===
def test_to_db_fmt():
	import cPickle
	import numpy as np
	from bson.binary import Binary

	# standard types should be passed through
	assert to_db_fmt(1) == 1
	assert to_db_fmt(4.2) == 4.2
	assert to_db_fmt('foobarbaz') == 'foobarbaz'
	assert to_db_fmt(1+2j) == 1+2j

	# lists and dicts should be recursively formatted
	assert to_db_fmt([1, 1+2j, 'foo', [1,2.3]]) == [1, 1+2j, 'foo', [1,2.3]]
	assert to_db_fmt({'a': 1, 'b': ['foo', 2]}) == {'a': 1, 'b': ['foo', 2]}

	# numpy arrays should be converted to lists
	assert to_db_fmt(np.array([1,2,3])) == [1,2,3]

	# objects should be pickled
	x = object()
	assert to_db_fmt(x) == Binary(cPickle.dumps(x, protocol=2))

def test_from_db_fmt():
	import cPickle
	import numpy as np

	def does_invert(x):
		return from_db_fmt(to_db_fmt(x)) == x

	# standard types should invert to the original
	assert does_invert(1)
	assert does_invert(4.2)
	assert does_invert('foobarbaz')
	assert does_invert(1+2j)

	# lists and dicts should invert 
	assert does_invert([1, 1+2j, 'foo', [1,2.3]])
	assert does_invert({'a': 1, 'b': ['foo', 2]})

	# numpy arrays invert to lists
	assert from_db_fmt(to_db_fmt(np.array([1,2,3]))) == [1,2,3]
