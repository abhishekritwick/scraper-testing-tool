import json
import os

DATA_SOURCE = os.path.join(os.path.dirname(__file__),'db-creds.json')

global _CONFIGS
with open(DATA_SOURCE) as data_file:
    _CONFIGS = json.load(data_file)

class DBManager():
    def __init__(self, client):
        self.client = client

    def getDbCredential(self):
        dbkey = self.client + "_competition"
        dbDetails = {}
        if dbkey in _CONFIGS:
            dbDetails = _CONFIGS[dbkey]
        else:
            raise Exception("No json config for given data :" , dbkey)

        return dbDetails




if __name__ == '__main__':
    x = DBManager('lowes')
    print(x.getDbCredential())
