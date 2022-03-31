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

with open('scraped_cars_data.pickle','rb') as f:
    scraped_cars_data = pickle.load(f)

DATA_DIR = 'html_data'

SUCCESS_CODE = 0
FAILURE_CODE = 1

SUCCESS_FILE = '06-success.txt'
FAILURE_FILE = '06-failure.txt'

success_logs = []
failure_logs = []

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

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
    try:
        page = requests.get(link)
        soup = BeautifulSoup(page.content, 'html.parser')
        file_name = os.path.join(DATA_DIR, uid)
        write_soup_to_file(soup, file_name)
        data = get_data_from_soup(soup)
        detailed_data = {}
        if details:
            for category in ['tech', 'sizes', 'options']:
                category_link = f'{link}/{category}'
                page = requests.get(category_link)
                soup = BeautifulSoup(page.content, 'html.parser')
                write_soup_to_file(soup, file_name + f'_{category}')
                detailed_data[category] = get_data_from_soup(soup)
        output = {}
        output[uid] = {'link': link, 'data': data, 'detailed_data': detailed_data}
        return SUCCESS_CODE, f'[t#{i}] - Successfully scraped link: {link}\n', output
    except:
        return FAILURE_CODE, f'[t#{i}] - Error scraping link: {link}\n'


links_data = {}
for model_name in scraped_cars_data.keys():
    for model in scraped_cars_data[model_name]:
        for year, year_info in model['years'].items():
            if int(year) < 1995 or int(year) > 2013: continue
            type_info = year_info['types'][0]
            info = copy(type_info)
            link = type_info['link']
            uid = hashlib.md5(link.encode('utf-8')).hexdigest()
            if uid in links_data: continue
            links_data[uid] = link

print(len(links_data))

n_threads = 16
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
with open('scraped_specs_data_reduced.pickle', 'wb') as f:
    pickle.dump(scraped_outputs, f)
