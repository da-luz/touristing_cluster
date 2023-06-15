import os

WARNING = 'You already have a copy of "places.csv" file. \nRecreating that file will demand both a Bing Maps and HERE API keys. \nDo you want to proceed? \n\tPress 0 if you do not want to continue (default) \n\tAnd 1 if you want to proceed \n'

if 'places.csv' in os.listdir(): 
    go = 0
    go = int(input(WARNING))
    if not go: exit()
else:
    pass
    
print('Importing packages...')
import sys
import pandas as pd
from datetime import datetime
from geopy.geocoders import Bing, HereV7

from selenium.webdriver.common.by import By
from selenium.webdriver import Edge as WD # WebDriver
from webdriver_manager.microsoft import EdgeChromiumDriverManager as DM #Driver Manager
import selenium.webdriver.edge as swd # selenium web driver

init = datetime.now()

print('Driver starting...')
init_sp = datetime.now()
Service = swd.service.Service
Options = swd.options.Options
opt = Options()
opt.add_argument('--headless')
opt.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = WD(service = Service(DM().install()), options = opt)

print('Gathering online data...')
driver.get('https://www.holidify.com/collections/best-places-in-the-world')
holidify = list(map(lambda x: x.text, driver.find_elements(By.CLASS_NAME, 'card-heading')))

driver.get('https://www.forbes.com/sites/laurabegleybloom/2019/09/04/bucket-list-travel-the-top-50-places-in-the-world')
forbes = list(map(lambda x: x.text, driver.find_elements(By.TAG_NAME, 'strong')))

driver.get('https://www.boredpanda.com/amazing-places-to-see-before-you-die-2/')
boredpanda = list(map(lambda x: x.text, driver.find_elements(By.TAG_NAME, 'h2')))

driver.quit()
print(f'Driver quitted in {datetime.now() - init_sp}')

places = []

print('Treating data...')
init_sp = datetime.now()
for item in holidify:
    #Format: <N>. <Local>, [<Country> - <Title>]
    #Target: <Local>, [<Country>]
    item = item[item.find(' ') + 1:item.rfind(' - ')]\
        if item.rfind(' - ') > 0 else item[item.find(' ') + 1:]
    places.append(item)
    
for item in forbes:
    #Format: <N>. <Local>, [<Country>]:
    #Target: <Local>, [<Country>]
    places.append(item[item.find(' ') + 1:item.rfind(':')])
    
for item in boredpanda:
    #Format: <N>. [<Place> in] <Local>[: <Title>, <Country>/<Shared countries>]
    #Target: [<Place> in] <Local>[, <Country>]
    both = item.split(', ')
    pa = both[0].rfind(':') if both[0].rfind(':') > 0 else len(both[0])
    a = both[0][both[0].find(' ') + 1:pa]
    b = both[-1].split('/')[1] if both[-1].find('/') > 0 else both[-1]
    places.append(a + ', ' + b)
    
places = pd.DataFrame(places, columns = ['queries'])
print(f'Treatment finished in {datetime.now() - init_sp}')

print('Geopy configuration...')
here = input('Insert your HERE API key...\t')
bing = input('Insert your Bing Maps API key...\t')

geoHERE = HereV7(apikey = here, timeout = None) if here else None

geoBing = Bing(api_key = bing, timeout = None) if bing else None

print('Performing geocoding...')
lines = []
init_sp = datetime.now()
u = 40/(e := len(places.queries) -1)
for i, place in enumerate(places.queries):
    if not 'Hey, ' in place:
        #For dealing with one polution in data scrapped
        #"Hey, wait, there are only 39 places here! Can you suggest a 40th?"
        #Geocoding this raise an error for there is no such place with a name like this
        try:
            #HERE API brings the closest points despite less info about the place
            code = geoHERE.geocode(place.replace(' ', '+'), language = 'en-US')
            country = code.raw.get('address').get('countryName')if code else None
            local = code.raw.get('address').get('city') if code else None
            local = local if local else country
            if bing: assert country == place.split(', ')[-1]
        except:
            #Bing stays as a backup
            code = geoBing.geocode(place.replace(' ', '+'), culture = 'US')
            country = code.raw.get('address').get('countryRegion') if code else None
            local = code.raw.get('address').get('adminDistrict') if code else None
            local = local if local else country
        latitude = code.latitude if code else None
        longitude = code.longitude if code else None
        lines.append((local, country, latitude, longitude))
    else: lines.append((None, None, None, None)) #Also None when the data is polluted
    
    #Printing progress bar
    sys.stdout.write('\r')
    sys.stdout.write(
        f'{i} out of {e} [{"="*round(i * u)}{" "*round((e - i) * u)}] {round((i / e) * 100)}%\
        Elapsed: {(ela := datetime.now() - init_sp)} ETA: {(ela / (i + 1)) * e}'
    )
    sys.stdout.flush()
print(f'\nGeocoding done in {datetime.now() - init_sp}')
    
print('Consolidating and exporting data...')
places.loc[:, ['local', 'country', 'lat', 'lon']] = lines

#Getting rid of pollution
places.drop_duplicates(subset = ['lat', 'lon'], inplace = True)
places.dropna(inplace = True)

places.to_csv('places.csv', index = False)
print(f'Process done in {datetime.now() - init}')
input('Press \'Enter\' to exit...')
