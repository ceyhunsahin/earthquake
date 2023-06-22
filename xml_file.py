import xmltodict
import urllib.request
import datetime
import json
import pandas as pd
import numpy as np
import functions as f
from bs4 import BeautifulSoup
from pandarallel import pandarallel

pandarallel.initialize(progress_bar=True)

current_year = datetime.datetime.now().year
current_month = datetime.datetime.now().month
start_year = 2020
urls = []

# loop through each year and month from March 2011 to current year and month
for year in range(2020, current_year+1):
    for month in range(1, 13):
        if year ==2023 and month >4 :
            break

        month_str = f'{month:02d}' # zero-padded month string
        url = f'http://udim.koeri.boun.edu.tr/zeqmap/xmlt/{year}{month_str}.xml'
        urls.append(url)
print(urls)

def get_xml():
    response_text = list()
    for url in urls :

        # make the GET request and retrieve the response data
        with urllib.request.urlopen(url) as response:
            response_text.append(response.read().decode('iso-8859-1', errors = 'ignore'))
    response_text = ''.join(response_text)
    response_text = response_text.replace('<?xml version="1.0" encoding="ISO-8859-1" ?>\r\n', '')\
        .replace('Ýlksel"', '"')

    return response_text

xml_string = get_xml()

soup = BeautifulSoup(xml_string, 'html.parser')

eqlist_tags = soup.find_all('eqlist')
inner_html_strings = [str(tag) for tag in eqlist_tags]

cumulated_eqlist = '<eqlist>' + ''.join(inner_html_strings) + '</eqlist>'

# Convert XML string to OrderedDict
xml_dict = xmltodict.parse(cumulated_eqlist)

# Convert OrderedDict to JSON string
json_string = json.dumps(xml_dict)

json_obj = json.loads(json_string )

# Convert JSON object to Python dictionary
earthquake_list = []

# Iterate over each dictionary in the 'earthquake' list and extract the 'depth' and 'lat' values
for eq in json_obj[['eqlist'][0]]['eqlist']:
    for ind in range(len(json_obj[['eqlist'][0]]['eqlist'])):
        for k in range(len(json_obj[['eqlist'][0]]['eqlist'][ind]['earhquake'])):
            earthquake_dict = {'depth': json_obj[['eqlist'][0]]['eqlist'][ind]['earhquake'][k]['@depth'], \
                               'lat': json_obj[['eqlist'][0]]['eqlist'][ind]['earhquake'][k]['@lat'], \
                               'long': json_obj[['eqlist'][0]]['eqlist'][ind]['earhquake'][k]['@lng'], \
                               'location': json_obj[['eqlist'][0]]['eqlist'][ind]['earhquake'][k]['@lokasyon'],\
                               'magnitude': json_obj[['eqlist'][0]]['eqlist'][ind]['earhquake'][k]['@mag'], \
                               'date_and_time': json_obj[['eqlist'][0]]['eqlist'][ind]['earhquake'][k]['@name'], \
                    }
            earthquake_list.append(earthquake_dict)

# Create a Pandas dataframe from the list of earthquake dictionaries
df = pd.DataFrame(earthquake_list)

def convert_datetime_type(dt_string):
    dt_formats = ['%Y.%m.%d %H:%M:%S', '%Y.%m.%d %H.%M.%S']
    for dt_format in dt_formats:
        try:
            dt_object = datetime.datetime.strptime(dt_string, dt_format)
            return dt_object.strftime('%Y.%m.%d %H:%M:%S')
        except ValueError:
            pass
    raise ValueError("Could not convert datetime string: {}".format(dt_string))

# apply the function to the DataFrame column
df['date_and_time'] = df['date_and_time'].apply(convert_datetime_type)

# convert the datetime column to datetime format
df['date_and_time'] = pd.to_datetime(df['date_and_time'])

# create new columns for date and time
df['date'] = df['date_and_time'].dt.date
df['time'] = df['date_and_time'].dt.time


# separate location with city and town

def separate_city(x):
    if len(x.split('(')) > 1 :
        x = x.strip()
        city = x.split('(')[1].replace('Ý', 'I').replace('Ð', 'G').replace('Þ', 'S').replace('i', 'I')
        if city[-1] == '-':
            city = city[:-1]
        if len(city.split(')')) > 1 :
            city = city.split (')')[0]
        if city[:4] in ['2011', '2012', '2013', '2014', '2015','2016', '2017','2018', '2019', '2020','2021','2022','2023'] :
            city = ''



        town = x.split('(')[0][:-1].replace('Ý', 'I').replace('Ð', 'G').replace('Þ', 'S')
        if town[-1] == '-':
            town = town[:-1]
        return pd.Series([city.strip(), town.strip()])
    else :
        x = x.strip().replace('Ý', 'I').replace('Ð', 'G').replace('Þ', 'S')
        return pd.Series([x, x])


df[['City','Town']] = df['location'].parallel_apply(separate_city)

df = df[df['City'] != '']

df = df[~df['City'].str.contains('Otomatik')]
df = df[~df['magnitude'].str.contains('-.-')]

df['City'] = df['City'].apply(lambda x : x.title())
df['Town'] = df['Town'].apply(lambda x : x.title())
df.to_csv('earthquake.csv')

print('Get value of Bou earthquake info et loaded pandas')



