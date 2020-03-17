import json
import requests
import mysql.connector
try:
	from acds import configuration
except:
	import configuration


def db_model_search(query):
    try:
        conn = mysql.connector.connect(host=configuration.FIRE_HOST, database=configuration.FIRE_DB, user=configuration.FIRE_USER, password=configuration.FIRE_PASS)
    except Exception as e:
        print(e)
        return
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchall()
        return row
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

def db_insert(query):
    try:
        conn = mysql.connector.connect(host=configuration.FIRE_HOST, database=configuration.FIRE_DB, user=configuration.FIRE_USER, password=configuration.FIRE_PASS)
    except Exception as e:
        return str(e)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        lastid = cursor.lastrowid
        conn.commit()
        return lastid
    except Exception as e:
        return str(e)
    finally:
        cursor.close()
        conn.close()



def fias_suggest(query):
	url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"
	headers = {"Authorization": f"Token {getattr(configuration, 'DADATA_TOKEN')}", "Content-Type": "application/json"}
	data = {"query": query, "count": 1, "geoLocation": "True"}
	suggestions = requests.post(url, data=json.dumps(data), headers=headers)
	suggestions = suggestions.json()

	if suggestions['suggestions']:
		suggestions = (suggestions['suggestions'][0]['data'])
	else:
		suggestions = 'error'
	return suggestions

def fire_fias_insert(fireid,fire_address):
	
	fias_data = fias_suggest(fire_address)

	if fias_data != 'error':
	
		region_fias_id = fias_data['region_fias_id']
		region_with_type = fias_data['region_with_type']
		region_type_full = fias_data['region_type_full']
		region = fias_data['region']
		area_fias_id = fias_data['area_fias_id']
		area_with_type = fias_data['area_with_type']
		area_type_full = fias_data['area_type_full']
		area = fias_data['area']
		city_fias_id = fias_data['city_fias_id']
		city_with_type = fias_data['city_with_type']
		city_type_full = fias_data['city_type_full']
		city = fias_data['city']
		settlement_fias_id = fias_data['settlement_fias_id']
		settlement_with_type = fias_data['settlement_with_type']
		settlement_type_full = fias_data['settlement_type_full']
		settlement = fias_data['settlement']
		street_fias_id = fias_data['street_fias_id']
		street_with_type = fias_data['street_with_type']
		street_type_full = fias_data['street_type_full']
		street = fias_data['street']
		house_fias_id = fias_data['house_fias_id']
		house_type_full = fias_data['house_type_full']
		house = fias_data['house']
		block_type_full = fias_data['block_type_full']
		block = fias_data['block']
		fias_id = fias_data['fias_id']
		sum_data = {}
		sum_data[fireid] = {
			'region_fias_id': region_fias_id, 
			'region_with_type': region_with_type, 
			'region_type_full': region_type_full, 
			'region': region, 
			'area_fias_id': area_fias_id, 
			'area_with_type': area_with_type, 
			'area_type_full': area_type_full, 
			'area': area, 
			'city_fias_id': city_fias_id, 
			'city_with_type': city_with_type, 
			'city_type_full': city_type_full, 
			'city': city, 
			'settlement_fias_id': settlement_fias_id, 
			'settlement_with_type': settlement_with_type, 
			'settlement_type_full': settlement_type_full, 
			'settlement': settlement, 
			'street_fias_id': street_fias_id, 
			'street_with_type': street_with_type, 
			'street_type_full': street_type_full, 
			'street': street, 
			'house_fias_id': house_fias_id, 
			'house_type_full': house_type_full, 
			'house': house, 
			'block_type_full': block_type_full, 
			'block':block, 
			'fias_id': fias_id,
		}
		
		columns = ['region_fias_id', 'area_fias_id', 'city_fias_id', 'settlement_fias_id', 'street_fias_id', 'house_fias_id', 'fias_id']
		keys = [values for values in columns if sum_data[fireid][values]]
		
		db_columns = ', '.join(keys)
		db_values = '\', \''.join([sum_data[fireid][values] for values in keys])
		
	
		db_region = db_model_search(f"""SELECT region_fias_id from FireSupressor.FireFias_region WHERE region_fias_id like '{region_fias_id}'""")
		if not db_region and region_fias_id:
			db_insert(f"""INSERT into FireSupressor.FireFias_region (region_fias_id, region_with_type, region_type_full, region) VALUES ('{region_fias_id}', '{region_with_type}', '{region_type_full}', '{region}')""")

		db_area = db_model_search(f"""SELECT area_fias_id from FireSupressor.FireFias_area WHERE area_fias_id like '{area_fias_id}'""")
		if not db_area and area_fias_id:
			db_insert(f"""INSERT into FireSupressor.FireFias_area (area_fias_id, area_with_type, area_type_full, area) VALUES ('{area_fias_id}', '{area_with_type}', '{area_type_full}', '{area}')""")
	
		db_city = db_model_search(f"""SELECT city_fias_id from FireSupressor.FireFias_city WHERE city_fias_id like '{city_fias_id}'""")
		if not db_city and city_fias_id:
			db_insert(f"""INSERT into FireSupressor.FireFias_city (city_fias_id, city_with_type, city_type_full, city) VALUES ('{city_fias_id}', '{city_with_type}', '{city_type_full}', '{city}')""")
	
		db_settlement = db_model_search(f"""SELECT settlement_fias_id from FireSupressor.FireFias_settlement WHERE settlement_fias_id like '{settlement_fias_id}'""")
		if not db_settlement and settlement_fias_id:
			db_insert(f"""INSERT into FireSupressor.FireFias_settlement (settlement_fias_id, settlement_with_type, settlement_type_full, settlement) VALUES ('{settlement_fias_id}', '{settlement_with_type}', '{settlement_type_full}', '{settlement}')""")
	
		db_street = db_model_search(f"""SELECT street_fias_id from FireSupressor.FireFias_street WHERE street_fias_id like '{street_fias_id}'""")
		if not db_street and street_fias_id:
			db_insert(f"""INSERT into FireSupressor.FireFias_street (street_fias_id, street_with_type, street_type_full, street) VALUES ('{street_fias_id}', '{street_with_type}', '{street_type_full}', '{street}')""")
	
		db_house = db_model_search(f"""SELECT house_fias_id from FireSupressor.FireFias_house WHERE house_fias_id like '{house_fias_id}'""")
		if not db_house and house_fias_id:
			columns_house = ['house_fias_id', 'house_type_full', 'house', 'block_type_full', 'block']
			keys_house = [values for values in columns_house if sum_data[fireid][values]]
	
			db_columns_house = ', '.join(keys_house)
			db_values_house = '\', \''.join([sum_data[fireid][values] for values in keys_house])
	
			db_insert(f"""INSERT into FireSupressor.FireFias_house ({db_columns_house}) VALUES ('{db_values_house}')""")
	
	

		db_insert(f"""INSERT into FireSupressor.FireFias (id, {db_columns}) VALUES ('{fireid}', '{db_values}')""")
	

		return 'ok'
		
	else:
		return fias_data
