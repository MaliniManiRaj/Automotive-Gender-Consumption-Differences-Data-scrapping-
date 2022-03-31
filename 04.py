from glob import glob

with open('03-failure.txt', 'r') as f:
	total_failed_links = len(f.readlines())

total_images = len(glob('./images/*'))

print(f'Total number of failed links fixed = {total_failed_links}')
print(f'Total number of images present: {total_images}')