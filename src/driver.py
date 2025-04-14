import millenniumdb_driver

url = 'URL for the MillenniumDB server'
driver = millenniumdb_driver.driver(url)

session = driver.session()

query = 'MATCH (?from)-[:?type]->(?to) RETURN * LIMIT 10'
result = session.run(query)

driver.close()