import traceback, random

from hashlib import sha256
from Config import Config

class User(object):

    def __init__(self, col):
        self.col = col
        self.config = Config()

    def hashPasswd(self, passwd):
        return sha256(str(passwd + self.config.salt).encode('utf-8')).hexdigest()

    def randomPasswd(self):
        randPasswd = ''
        for each in range(0, 8):
            select = random.randrange(1, 37)
            randPasswd += chr(64 + select) if select <= 26 else str(select - 26)
        return self.hashPasswd(randPasswd)

    def addAdmin(self, email, name, passwd):
        try:
            if self.col.find({ 'email': email }).count() != 0:
                return False
            self.col.insert_one({
                'email': email,
                'name': name,
                'passwd': self.hashPasswd(passwd),
                'admin': True
            })
            return True
        except:
            traceback.print_exc()
            return False

    def addJudge(self, data):
        try:
            if self.col.find(data).count() != 0:
                return False
            data['passwd'] = self.hashPasswd()
            self.col.insert_one(data)
            return True
        except:
            return False

    def fetchOne(self, data):
        try:
            return self.col.find_one(data)
        except:
            traceback.print_exc()
            return None

    def fetch(self, data):
        try:
            return self.col.find(data)
        except:
            traceback.print_exc()
            return None

