import pandas as pd
import os
from sqlalchemy import create_engine
import logging 
import time

logging.basicConfig(filename = "logs/ingestion_db.log", 
                    level = logging.DEBUG, 
                    format = "%(asctime)s - %(levelname)s - %(message)s",
                    filemode = "a")

engine = create_engine("sqlite:///inventory.db")

def ingest_db_in_chunks(file_path, table_name, engine, chunksize=100000):
    '''The functions load the dataframes into the datatable'''
    for chunk in pd.read_csv(file_path, chunksize=chunksize)
        chunk.to_sql(table_name, con=engine, if_exists='append', index=False)

def load_raw_data():
    ''' The function load the chunk of csv into dataframe and ingest into db'''
    start = time.time()
    for file in os.listdir("data"):
        if file.endswith('.csv'):
            print(f"Processing: {file}")
            ingest_db_in_chunks('data/' + file, file[:-4], engine)
            print(f"Finished: {file}")
    end = time.time()
    total_time = (end-start)/60
    logging.info("---------------Ingestion complete---------------")
    logging.info(f"\nTotal Time{total_time} minutes")

if __name__ = "__main__":
    load_raw_data()