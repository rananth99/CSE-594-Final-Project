import shutil

import pydeck as pdk
import pandas as pd
import subprocess, os
from pathlib import Path
from flask import Flask, request, jsonify, make_response, send_file

app = Flask(__name__, static_url_path="/static")


def Phase_1(jsonFile, MinLat, MinLon, MaxLat, MaxLon, MinTime, MaxTime, MinLat_1, MinLon_1, MaxLat_1, MaxLon_1, KNN_ID,
            KNN_K):
    if os.path.exists('data/output/get-spatiotemporal-range'):
        shutil.rmtree('data/output/get-spatiotemporal-range')
    if os.path.exists('data/output/get-knn'):
        shutil.rmtree('data/output/get-knn')
    if os.path.exists('data/output/get-spatial-range'):
        shutil.rmtree('data/output/get-spatial-range')
    if (MinTime == "" or MaxTime == "" or MinLat_1 == "" or MaxLat_1 == "" or MaxLon_1 == "" or MinLon_1 == "") and (
            KNN_K == "" or KNN_ID == ""):
        command = "spark-submit phase1/SDSE-Phase-1-assembly-0.1.jar data/output datafile {} get-spatial-range {} {} {} {}".format(
            jsonFile, MinLat, MinLon, MaxLat, MaxLon)
    elif (MinLat == "" or MaxLat == "" or MinLon == "" or MaxLon == "") and (KNN_K == "" or KNN_ID == ""):
        print("------------", MinLat)
        command = "spark-submit phase1/SDSE-Phase-1-assembly-0.1.jar data/output datafile {} get-spatiotemporal-range {} {} {} {} {} {}".format(
            jsonFile, MinTime, MaxTime, MinLat_1, MinLon_1, MaxLat_1, MaxLon_1)
    elif (MinLat == "" or MaxLat == "" or MinLon == "" or MaxLon == "") and (
            MinTime == "" or MaxTime == "" or MinLat_1 == "" or MaxLat_1 == "" or MaxLon_1 == "" or MinLon_1 == ""):
        command = "spark-submit phase1/SDSE-Phase-1-assembly-0.1.jar data/output datafile {} get-knn {} {}".format(
            jsonFile, KNN_ID, KNN_K)
    else:
        command = "spark-submit phase1/SDSE-Phase-1-assembly-0.1.jar data/output datafile {} get-spatial-range {} {} {} {} get-spatiotemporal-range {} {} {} {} {} {} get-knn {} {}".format(
            jsonFile, MinLat, MinLon, MaxLat, MaxLon, MinTime, MaxTime, MinLat_1, MinLon_1, MaxLat_1, MaxLon_1, KNN_ID,
            KNN_K)
    p = subprocess.Popen(command, shell=True)
    p.wait()


def getJsonPath(folder):
    for path in Path(folder).rglob('*.json'):
        return path


def MapLayers(data, colors):
    layers = []
    with open(data) as fp:
        for line in fp:
            df = pd.read_json(line)
            minimum_timestamp = df['timestamp'].min().timestamp()

            new_df = pd.DataFrame()

            new_df["coordinates"] = [[[location[1], location[0]] for location in df["location"]]]
            new_df["timestamps"] = [[int(timestamp.timestamp() - minimum_timestamp) for timestamp in df["timestamp"]]]
            print(new_df)

            layers.append(pdk.Layer(
                "TripsLayer",
                new_df,
                get_path="coordinates",
                get_timestamps="timestamps",
                get_color=colors,
                opacity=0.8,
                width_min_pixels=10,
                rounded=True,
                trail_length=600,
                current_time=500,

            ))

    return layers


@app.route('/', methods=['GET'])
def index():
    return send_file('main.html')


@app.route('/data', methods=['GET'])
def getData():
    return send_file(request.args.get(''))


@app.route('/Queries', methods=['POST', 'GET'])
def plot():
    if (request.method == 'GET'):
        return send_file('Queries.html')
    data = request.get_json(force=True)
    jsonFile = data['jsonFile']
    print(jsonFile)
    MinLat = data['MinLat']
    MinLon = data['MinLon']
    MaxLat = data['MaxLat']
    MaxLon = data['MaxLon']
    MinTime = data['MinTime']
    MaxTime = data['MaxTime']
    MinLat_1 = data['MinLat_1']
    MinLon_1 = data['MinLon_1']
    MaxLat_1 = data['MaxLat_1']
    MaxLon_1 = data['MaxLon_1']
    KNN_ID = data['KNN_ID']
    KNN_K = data['KNN_K']
    Phase_1(jsonFile, MinLat, MinLon, MaxLat, MaxLon, MinTime, MaxTime, MinLat_1, MinLon_1, MaxLat_1, MaxLon_1, KNN_ID,
            KNN_K)
    SpatialRangePath = getJsonPath("data/output/get-spatial-range")
    SpatioTemporalRangePath = getJsonPath("data/output/get-spatiotemporal-range")
    KNNPath = getJsonPath("data/output/get-knn")

    map_layers = []
    map_layers.append(MapLayers(SpatialRangePath, colors=[0, 0, 255]))
    map_layers.append(MapLayers(SpatioTemporalRangePath, colors=[255, 0, 0]))
    map_layers.append(MapLayers(KNNPath, colors=[0, 255, 0]))

    State = pdk.ViewState(latitude=33.4255, longitude=-111.9400, zoom=10, bearing=0, pitch=45)
    output = pdk.Deck(layers=map_layers, initial_view_state=State)

    render_HTML = output.to_html(as_string=True)
    response = make_response(jsonify({"html": render_HTML}), 201)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/SRQ', methods=['POST', 'GET'])
def SRQ():
    if (request.method == 'GET'):
        return send_file('SRQ.html')

    data = request.get_json(force=True)
    jsonFile = data['jsonFile']
    print(jsonFile)
    MinLat = data['MinLat']
    MinLon = data['MinLon']
    MaxLat = data['MaxLat']
    MaxLon = data['MaxLon']
    Phase_1(jsonFile, MinLat, MinLon, MaxLat, MaxLon, "", "", "", "", "", "", "", "")
    SpatialRangePath = getJsonPath("data/output/get-spatial-range")

    map_layers = []
    map_layers.append(MapLayers(SpatialRangePath, colors=[0, 0, 255]))

    State = pdk.ViewState(latitude=33.4255, longitude=-111.9400, zoom=10, bearing=0, pitch=45)
    output = pdk.Deck(layers=map_layers, initial_view_state=State)

    render_HTML = output.to_html(as_string=True)
    response = make_response(jsonify({"html": render_HTML}), 201)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/STRQ', methods=['POST', 'GET'])
def STRQ():
    if (request.method == 'GET'):
        return send_file('STRQ.html')
    data = request.get_json(force=True)
    jsonFile = data['jsonFile']
    print(jsonFile)
    MinTime = data['MinTime']
    MaxTime = data['MaxTime']
    MinLat_1 = data['MinLat_1']
    MinLon_1 = data['MinLon_1']
    MaxLat_1 = data['MaxLat_1']
    MaxLon_1 = data['MaxLon_1']
    Phase_1(jsonFile, "", "", "", "", MinTime, MaxTime, MinLat_1, MinLon_1, MaxLat_1, MaxLon_1, "", "")
    SpatioTemporalRangePath = getJsonPath("data/output/get-spatiotemporal-range")

    map_layers = []
    map_layers.append(MapLayers(SpatioTemporalRangePath, colors=[255, 0, 0]))

    State = pdk.ViewState(latitude=33.4255, longitude=-111.9400, zoom=10, bearing=0, pitch=45)
    output = pdk.Deck(layers=map_layers, initial_view_state=State)

    render_HTML = output.to_html(as_string=True)
    response = make_response(jsonify({"html": render_HTML}), 201)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/KNN', methods=['POST', 'GET'])
def KNN():
    if (request.method == 'GET'):
        return send_file('KNN.html')

    data = request.get_json(force=True)
    jsonFile = data['jsonFile']
    print(jsonFile)
    KNN_ID = data['KNN_ID']
    KNN_K = data['KNN_K']
    Phase_1(jsonFile, "", "", "", "", "", "", "", "", "", "", KNN_ID, KNN_K)
    KNNPath = getJsonPath("data/output/get-knn")

    map_layers = [MapLayers(KNNPath, colors=[0, 255, 0])]

    State = pdk.ViewState(latitude=33.4255, longitude=-111.9400, zoom=10, bearing=0, pitch=45)
    output = pdk.Deck(layers=map_layers, initial_view_state=State, )

    render_HTML = output.to_html(as_string=True)
    response = make_response(jsonify({"html": render_HTML}), 201)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


if __name__ == '__main__':
    app.run("localhost", port=8080, debug=True)
