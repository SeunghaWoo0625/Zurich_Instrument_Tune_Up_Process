# logging_helpers.py
import datetime
import json
from laboneq.simple import *


my_db = DataStore()

def data_logger(results, key_prefix, timestamp, author, qubit_parameters, exp_parameters):
    my_db.store(
    results,
    key=key_prefix+timestamp,
    metadata={
        "author": author,
        "time": timestamp,
        "qubit_parameters": json.dumps(qubit_parameters),
        "exp_parameters": json.dumps(exp_parameters)
    },
)
    
def figure_logger(results, key_prefix, timestamp):
    