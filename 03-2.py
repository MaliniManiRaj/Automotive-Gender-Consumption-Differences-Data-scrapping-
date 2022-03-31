import pickle
from glob import glob
import os
import urllib.request

# Some of the images link have thrown a 404 not found, this script fixes all such links

with open('scraped_static_data.pickle','rb') as f:
    scraped_static_data = pickle.load(f)

files = glob('./images/*')
downloaded_images = set(list(map(lambda x: x.split('/')[-1].split('.')[0], files)))

assert(len(files) == len(downloaded_images))

no_image_link = 'https://www.cars-data.com/design/images/no-image-170x113.jpg'

for key in scraped_static_data:
    if key in downloaded_images: continue
    image_link = scraped_static_data[key]
    filename = os.path.join('images', key + '.jpg')
    print(filename, image_link)
    try:
        urllib.request.urlretrieve(image_link, filename)
        print(f'[t#{i}] - Successfully saved to location: {filename}\n')
    except:
        print('Not found')
        scraped_static_data[key] = no_image_link
        urllib.request.urlretrieve(no_image_link, filename)

with open('scraped_static_data.pickle', 'wb') as f:
    pickle.dump(scraped_static_data, f)
