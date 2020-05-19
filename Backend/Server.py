from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse

from keras.models import load_model
from keras.wrappers.scikit_learn import KerasClassifier
from tensorflow.keras.models import Sequential
from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing
import numpy as np
import pandas as pd
from numpy import array
import requests
import json
import time
from datetime import datetime
import pymongo
from sklearn.externals.joblib import dump, load
import pickle as cPickle
from bson import ObjectId

app = Flask(__name__)
MODEL = load_model('./NeuronN_model_Standard.h5')
Scalers = load('./std_scaler.bin')

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
dblist = myclient.list_database_names()
if "pillow" in dblist:
    mydb = myclient["pillow"]
    print("The database exists.")
    collist = mydb.list_collection_names()
    if "data" in collist:
        mycol = mydb["data"]
        print("The collection exists.")

mydb = myclient["pillow"]
mycol = mydb["data"]
collection_data = mycol.find_one({})


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def calculated(first, last):
    countSupine = 0
    countLeft = 0
    countRight = 0
    countNotSleep = 0
    for i in range(first, last):
        print(collection_data['dataList'][i]['date'],
              collection_data['dataList'][i]['requestdata'])
        print(collection_data['dataList'][i]['predict'])
        if collection_data['dataList'][i]['predict'] == 0:
            countSupine += 1
        if collection_data['dataList'][i]['predict'] == 1:
            countLeft += 1
        if collection_data['dataList'][i]['predict'] == 2:
            countRight += 1
        if collection_data['dataList'][i]['predict'] == 3:
            countNotSleep += 1
    if(countSupine == countLeft or countSupine == countRight or countSupine == countNotSleep or countLeft == countRight or
       countLeft == countNotSleep or countRight == countNotSleep):
        for i in range(int(last-3), last):
            if collection_data['dataList'][i]['predict'] == 0:
                countSupine += 1
            if collection_data['dataList'][i]['predict'] == 1:
                countLeft += 1
            if collection_data['dataList'][i]['predict'] == 2:
                countRight += 1
            if collection_data['dataList'][i]['predict'] == 3:
                countNotSleep += 1
        return [np.argmax([countSupine, countLeft, countRight, countNotSleep])]
    else:
        return np.argmax([countSupine, countLeft, countRight, countNotSleep])


def check_result(results_count):
    current = results_count
    print(current)
    pastFiveMins = results_count-5
    print(pastFiveMins)
    past10Mins = results_count-10
    print(past10Mins)
    if pastFiveMins < -2:
        return ['3', '3']
    elif (pastFiveMins >= -2 and past10Mins < 0):
        maxResult_pastFiveMinsToCurrent = calculated(pastFiveMins, current)
        return ['3', maxResult_pastFiveMinsToCurrent]
    # elif past10Mins < 0:
    #     maxResult_pastFiveMinsToCurrent = calculated(pastFiveMins, current)
    #     return ['3', maxResult_pastFiveMinsToCurrent]
    else:
        maxResult_past10MinTopastFiveMins = calculated(
            past10Mins, pastFiveMins)
        maxResult_pastFiveMinsToCurrent = calculated(pastFiveMins, current)
        return [maxResult_past10MinTopastFiveMins, maxResult_pastFiveMinsToCurrent]


@app.route("/predict", methods=["POST"])
def predict():
    dateTimeObj = datetime.now()
    timeStamp = round(datetime.timestamp(dateTimeObj))
    print(request.json['data'])
    reqdata = request.json['data']
    a = np.array(request.json['data']).reshape(1, -1)
    normalizedX = Scalers.transform(a)
    print(normalizedX)
    normalizedX = normalizedX.reshape(1, 9)
    predict = MODEL.predict_classes(normalizedX)
    print("predict : ", predict)
    if mycol.find_one({}) == None:
        predictDoc = {"dataList": [
            {"date": timeStamp, "requestdata": reqdata, "predict": predict.tolist()[0]}]}
        mycol.insert(predictDoc)
    else:
        mycol.update_one(
            {}, {"$push": {"dataList": {"date": timeStamp, "requestdata": reqdata, "predict": predict.tolist()[0]}}})
    return jsonify(
        json.dumps(predict.tolist()[0])
    ), 201


@app.route("/getdata", methods=["GET"])
def getdata():
    global collection_data
    collection_data = mycol.find_one({})
    if collection_data == None:
        results_count = 0
        predictCurrent = 3
    else:
        results_count = len(collection_data['dataList'])
        print(results_count)
        predictCurrent = collection_data['dataList'][results_count-1]['predict']
        # TimeStampCurrent = collection_data['dataList'][results_count-1]['date']
    result10Mins, result5Mins = check_result(results_count)
    resultDict = {
        "result10Mins": str(result10Mins[0]),
        "result5Mins": str(result5Mins[0]),
        "predictCurrent": str(predictCurrent)
        # "TimeStampCurrent": str(TimeStampCurrent)
    }
    print(resultDict)
    return JSONEncoder().encode(resultDict)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
