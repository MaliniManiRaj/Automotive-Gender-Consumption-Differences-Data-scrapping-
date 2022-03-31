import numpy as np
import pickle
import urllib.request
import os
import time
import sys
from joblib import Parallel, delayed
import multiprocessing

# Download all the images and save them in a folder
# This takes a lot of time hence this process is done in parallel using multiple threads

with open('scraped_cars_data.pickle','rb') as f:
    scraped_cars_data = pickle.load(f)

with open('scraped_static_data.pickle','rb') as f:
    scraped_static_data = pickle.load(f)

dir = 'images'
if not os.path.exists(dir):
    os.makedirs(dir)

SUCCESS_FILE = '03-success.txt'
FAILURE_FILE = '03-failure.txt'

SUCCESS_CODE = 0
FAILURE_CODE = 1

failure_logs = []
success_logs = []

def chunk(x, n):
    idx = 0
    while idx < len(x):
        yield x[idx : idx + n]
        idx += n

def download_image(filename, image_link, i):
    filename = os.path.join('images', filename + '.jpg')
    try:
        if os.path.exists(filename):
            return SUCCESS_CODE, f'[t#{i}] - File with name {filename} already present\n'
        urllib.request.urlretrieve(image_link, filename)
        return SUCCESS_CODE, f'[t#{i}] - Successfully saved to location: {filename}\n'
    except:
        return FAILURE_CODE, f'[t#{i}] - Error saving file: {filename}\n'

n_threads = 16

image_data = list(zip(list(scraped_static_data.keys()), list(scraped_static_data.values())))

for data in chunk(image_data, n_threads):
    sys.stdout.write('######## STARTED PARALLEL DOWNLOADING ########\n')
    start_time = time.time()
    results = Parallel(n_jobs=n_threads)(delayed(download_image)(filename, image_link, idx) for idx, (filename, image_link) in enumerate(data))
    for result, log in results:
        if result == SUCCESS_CODE:
            success_logs.append(log)
        else:
            failure_logs.append(log)

    end_time = time.time()
    time_taken = end_time - start_time

    sys.stdout.write('######## FINISHED PARALLEL DOWNLOADING ########\n')
    sys.stdout.write(f'######## Time taken: {time_taken:.2f} ########\n')

with open(SUCCESS_FILE, 'w') as success_file:
    success_file.writelines(success_logs)

with open(FAILURE_FILE, 'w') as failure_file:
    failure_file.writelines(failure_logs)

success_file.close()
failure_file.close()
