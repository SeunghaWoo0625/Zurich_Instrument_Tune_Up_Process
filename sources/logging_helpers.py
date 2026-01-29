# logging_helpers.py

import os
import datetime
import json
from laboneq.simple import *



BASE_DIR = "experiment_results/database.db"
my_db = DataStore(file_path=BASE_DIR)


def data_logger(results, key_prefix, timestamp, qubit_index, author, qubit_parameters, exp_parameters):

    my_db.store(
    results,
    key=key_prefix+timestamp+'Q'+str(qubit_index),
    metadata={
        "author": author,
        "time": timestamp,
        "qubit_parameters": json.dumps(qubit_parameters),
        "exp_parameters": json.dumps(exp_parameters)
    })
    

def metadata_logger(key_prefix, date, timestamp, qubit_index, author, qubit_parameters, exp_parameters):
    
    date_str = date
    timestamp_str = timestamp
    exp_dir = os.path.join(BASE_DIR, date_str, timestamp_str)
    os.makedirs(exp_dir, exist_ok=True)
    
    filename=key_prefix+timestamp+'Q'+str(qubit_index)+".json"
    
    metadata={
        "author": author,
        "time": timestamp,
        "qubit_parameters": qubit_parameters,
        "exp_parameters": exp_parameters,
    }
    
    metadata_path = os.path.join(exp_dir, filename)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    
    
def figure_logger(fig, key_prefix, date, timestamp, qubit_index):
    
    date_str = date
    timestamp_str = timestamp
    exp_dir = os.path.join(BASE_DIR, date_str, timestamp_str)
    os.makedirs(exp_dir, exist_ok=True)
    
    filename=key_prefix+timestamp+'Q'+str(qubit_index)+".png"
    fig_path = os.path.join(exp_dir, filename)
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    