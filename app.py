import hashlib, json, traceback
from pymongo import MongoClient
from bson.objectid import ObjectId
from sanic import Sanic
from sanic.response import json as jsonRes
from sanic_cors import CORS, cross_origin

from Config import Config
from User import User


mongo = MongoClient('mongodb://localhost:27017')
db = mongo['YonglinContestJudge']
app = Sanic(__name__)
cors = CORS(app, resources={ r'/api/*': { 'origins': '*' } })

config = Config()
user = User(col=db['User'])

@app.route('/')
async def index(request):
    return jsonRes({ 'hello': 'world' })

@app.route('/api/login', methods=['POST'])
async def Login(request):
    try:
        email = request.raw_args['account']
        hashPasswd = user.hashPasswd(request.raw_args['passwd']) 
        data = db.User.find_one({ 'email': email, 'passwd': hashPasswd }, projection={ '_id': False})
        del data['passwd']
        return jsonRes({ 'status': 'success', 'data': data })
    except Exception as e:
        return jsonRes({ 'status': 'failed', 'detail': e })

@app.route('/api/contest/check-duplicate', methods=['POST'])
async def ContestCheck(request):
    try:
        data = db.Contest.find(request.raw_args, projection={ '_id': False })
        return jsonRes({ 'status': 'success', 'data': data })
    except Exception as e:
        return jsonRes({ 'status': 'failed', 'detail': e })

@app.route('/api/contest/list', methods=['GET'])
async def ContestList(request):
    try:
        res = {}
        res['contest-lists'] = db.Contest.find(projection={'info':True, '_id': False})
        return jsonRes({ 'status': 'success', 'data': res })
    except Exception as e:
        return jsonRes({ 'status': 'failed', 'detail': e })

@app.route('/api/contest/mark', methods=['POST'])
async def ContestMark(request):
    try:
        judgeEmail = request.raw_args['judgeEmail']
        contest = json.loads(request.raw_args['contest'])
        mark = request.raw_args['mark']
        data = db.Contest.find_one({'info.contestName': contest['info']['contestName']}, { '_id': False })
        data['mark'] = {
            judgeEmail: json.loads(mark)
        }
        db.Contest.update({'info.contestName': contest['info']['contestName']}, data, upsert=False)
        judgeData = db.User.find_one({'email': judgeEmail}, { '_id': False })
        del judgeData['cache']
        db.User.update({'email': judgeEmail}, judgeData, upsert=False)
        return jsonRes({ 'status': 'success' })
    except Exception as e:
        return jsonRes({ 'status': 'failed', 'detail': e })


@app.route('/api/contest/info', methods=['POST'])
async def ContestInfo(request):
    try:
        data = db.Contest.find_one({ 'info.contestName': request.raw_args['selected'] }, { '_id': False })
        return jsonRes({ 'status': 'success', 'data': data })
    except Exception as e:
        return jsonRes({'status': 'failed', 'detail': e })

@app.route('/api/contest/create', methods=['POST'])
async def ContestCreate(request):
    try:
        jsonObj = request.raw_args
        for (key, val) in jsonObj.items():
            jsonObj[key] = json.loads(val)
        db.Contest.insert_one(jsonObj)
        for each in jsonObj['judge']['judges']:
            userData = db.User.find_one({ 'email': each['email'] }) or each
            
            if userData != each: # Old User
                userData['contests'][jsonObj['info']['contestName']] = each['term']
            else: # New User
                global user
                userData['passwd'] = user.randomPasswd()
                userData['contests'] = { jsonObj['info']['contestName']: each['term'] }
                del userData['term']
            db.User.update({ 'email': each['email'] }, userData, upsert=True)
        return jsonRes({ 'status': 'success' })
    except Exception as e:
        traceback.print_exc()
        return jsonRes({ 'status': 'failed', 'detail': e })

@app.route('/api/judge/info', methods=['POST'])
async def JudgeInfo(request):
    try:
        data = db.User.find_one({ 'email': request.raw_args['selected'] }, { '_id': False })
        return jsonRes({ 'status': 'success', 'data': data })
    except Exception as e:
        return jsonRes({ 'status': 'failed', 'detail': e })

@app.route('/api/judge/cache', methods=['POST'])
async def JudgeCache(request):
    try:
        judgeEmail = request.raw_args['judgeEmail']
        userData = db.User.find_one({ 'email': judgeEmail }, { '_id': False })
        insertData = request.raw_args
        del insertData['judgeEmail']
        insertData['contest'] = json.loads(insertData['contest'])
        insertData['mark'] = json.loads(insertData['mark'])
        userData['cache'] = insertData
        db.User.update({ 'email': judgeEmail }, userData, upsert=False)
        return jsonRes({ 'status': 'success' })
    except Exception as e:
        traceback.print_exc()
        return jsonRes({ 'status': 'failed', 'detail': e })

def backendStatus():
    try:
        if db.User.find({}).count() == 0:
            print('New Backend, create admin account with passwd admin.')
            global user
            user.addAdmin(config.adminMail, name='管理員', passwd='admin')
    except Exception as e:
        traceback.print_exc()

if __name__ == '__main__':
    backendStatus()
    app.run(host='0.0.0.0')

