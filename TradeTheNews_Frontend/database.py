from pymongo import MongoClient
from urllib.parse import quote as handle_with_special_characters

class Database:
    databaseIds = {
        'articles': ['url'],
        'stocks': ['ticker'],
        'week_history': ['ticker', 'date_week_monday']
    }
    '''
    creates simpler access to a mongo DB Database
    '''
    def __init__(self, username, password, host, port, database):
        self.mongo_url = f"mongodb://{handle_with_special_characters(username)}:{handle_with_special_characters(password)}@{host}:{port}/?authSource={database}"
        self.client = MongoClient(self.mongo_url)
        self.db = self.client["StockForecast"]
    
    def insert_to_collection(self, collection, item):
        '''
        This function inserts a Json Object into a certain collection
        But it makes sure that this object just can be once in the database
        '''
        collec = self.db[collection]
        search_filter = {}
        # look for same existing doc? -> repalce
        if collection in Database.databaseIds.keys():
            for key in Database.databaseIds[collection]:
                search_filter[key] = item[key]
            if self.search_for_item(collection, search_filter):
                print("Objekt war schon in der Datenbank und wird ersetzt", collection)
                collec.delete_many(search_filter)
        else:
            print('ERROR - Collection has no id-key?', collection)

        collec.insert_one(item)

    
    def read_something(self, collection):
        '''
        This function reads a Json Object from a certain collection
        '''
        collec = self.db[collection]
        return collec.find()[0]
    
    def search_for_item(self, collection, search_pattern):
        '''
        This function searches a Json Object with special properties from a certain collection.
        Furthermore only one object should be found, otherwise some kind of error will be returned
        '''
        list_possible_results = self.search_for_items(collection, search_pattern)
        if len(list_possible_results) > 1:
            print("! ERROR? multiple items found with pattern:", search_pattern)
        elif len(list_possible_results) == 0:
            return False
        return list_possible_results[0]
    
    def search_for_items(self, collection, search_pattern):
        '''
        This function searches multiple Json Object with special properties from a certain collection.
        '''
        collec = self.db[collection]
        list_possible_results = list(collec.find(search_pattern))
        return list_possible_results
    
    def close_connection(self):
        '''
        closes Databaseconnection
        '''
        self.client.close()
