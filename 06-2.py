import os
import sys
import time
import hashlib
from joblib import Parallel, delayed
import multiprocessing

import requests
from bs4 import BeautifulSoup
from copy import deepcopy as copy

import numpy as np
import pickle

DATA_DIR = 'html_data'

SUCCESS_CODE = 0
FAILURE_CODE = 1

SUCCESS_FILE = '06-2-success.txt'
FAILURE_FILE = '06-2-failure.txt'

success_logs = []
failure_logs = []

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

with open('scraped_specs_data_reduced.pickle','rb') as f:
    scraped_specs_data_reduced = pickle.load(f)

final_specs_data_reduced = {}
for data in scraped_specs_data_reduced:
    key = list(data.keys())[0]
    final_specs_data_reduced[key] = data[key]

def chunk(x, n):
    idx = 0
    while idx < len(x):
        yield x[idx : idx + n]
        idx += n

def write_soup_to_file(soup, file_name):
    with open(file_name + '.html', 'w') as file:
        file.write(str(soup))
    
def get_data_from_soup(soup):
    data = {}
    col7 = soup.find('div', class_='col-7')
    rows = col7.find_all('td')
    for i in range(0, len(rows), 2):
        data[rows[i].text] = rows[i + 1].text
    return data

def scrape_and_get_data(i, uid, link, details=True):
    main_retry_count = 5
    while main_retry_count:
        try:
            page = requests.get(link)
            soup = BeautifulSoup(page.content, 'html.parser')
            file_name = os.path.join(DATA_DIR, uid)
            write_soup_to_file(soup, file_name)
            data = get_data_from_soup(soup)
            detailed_data = {}
            if details:
                for category in ['tech', 'sizes', 'options']:
                    retry_count = 5
                    while retry_count:
                        try:
                            category_link = f'{link}/{category}'
                            page = requests.get(category_link)
                            soup = BeautifulSoup(page.content, 'html.parser')
                            write_soup_to_file(soup, file_name + '_tech')
                            detailed_data[category] = get_data_from_soup(soup)
                            break
                        except:
                            sys.stdout.write(f'Unable to scrape data for {link} for category {category}. Retrying...\n')
                            sys.stdout.flush()
                            retry_count -= 1
            output = {}
            output[uid] = {'link': link, 'data': data, 'detailed_data': detailed_data}
            return SUCCESS_CODE, f'[t#{i}] - Successfully scraped link: {link}\n', output
        except:
            main_retry_count -= 1
    return FAILURE_CODE, f'[t#{i}] - Error scraping link: {link}\n'

links_data = {}
with open('06-failure.txt', 'r') as f:
    for line in f.read().splitlines():
        link = line.split(' ')[-1]
        uid = hashlib.md5(link.encode('utf-8')).hexdigest()
        links_data[uid] = link

n_threads = 4
details = True
scraped_outputs = []

for data in chunk(list(links_data.items()), n_threads):
    sys.stdout.write('######## STARTED PARALLEL SCRAPING ########\n')
    start_time = time.time()
    results = Parallel(n_jobs=n_threads)(delayed(scrape_and_get_data)(idx, uid, link, details=details) for idx, (uid, link) in enumerate(data))
    for result in results:
        if result[0] == SUCCESS_CODE:
            _, log, output = result
            success_logs.append(log)
            scraped_outputs.append(output)
        else:
            failure_logs.append(result[1])
    end_time = time.time()
    time_taken = end_time - start_time
    sys.stdout.write('######## FINISHED PARALLEL SCRAPING ########\n')
    sys.stdout.write(f'######## Time taken: {time_taken:.2f} ########\n')
    sys.stdout.flush()

with open(SUCCESS_FILE, 'w') as success_file:
    success_file.writelines(success_logs)

with open(FAILURE_FILE, 'w') as failure_file:
    failure_file.writelines(failure_logs)

success_file.close()
failure_file.close()


for scraped_output in scraped_outputs:
    key = list(scraped_output.keys())[0]
    final_specs_data_reduced[key] = scraped_output[key]

with open('final_specs_data_reduced.pickle', 'wb') as f:
    pickle.dump(final_specs_data_reduced, f)
