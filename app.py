import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from sanic import Sanic
from sanic.response import json as jsonRes
from sanic_cors import CORS, cross_origin

mongo = MongoClient('mongodb://localhost:27017')
db = mongo['YonglinContestJudge']
app = Sanic(__name__)
cors = CORS(app, resources={ r'/api/*': { 'origins': '*' } })

@app.route('/')
async def index(request):
    return jsonRes({ 'hello': 'world' })

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

@app.route('/api/contest/info', methods=['GET'])
async def ContestInfo(request):
    try:
        data = db.Contest.find_one({ 'info.contestName': request.query_string }, { '_id': False })
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
            db.User.insert_one(each)
        return jsonRes({'status': 'success'})
    except Exception as e:
        return jsonRes({'status': 'failed', 'detail': e })

@app.route('/api/judge/info', methods=['GET'])
async def JudgeInfo(request):
    try:
        data = db.User.find_one({ 'email': request.query_string }, { '_id': False })
        return jsonRes({ 'status': 'success', 'data': data })
    except Exception as e:
        return jsonRes({ 'status': 'failed', 'detail': e })

if __name__ == '__main__':
    app.run(host='0.0.0.0')

