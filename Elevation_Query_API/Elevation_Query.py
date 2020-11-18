import os
from flask import Flask, request
from flask_restful import Api, Resource, reqparse
import numpy as np
import json

SAMPLES = 1201 # Change this to 3601 for SRTM1
HGTDIR = '/Users/sunzhenyu/Documents/Projects/Geospatial-Data-Analysis/data/elevation_data/SRTM3'
hgt_dict = dict()
for sub_folder_name in os.listdir(HGTDIR):
    try:
        filename_list = os.listdir(os.path.join(HGTDIR, sub_folder_name))
        for filename in filename_list:
            hgt_dict[filename]=sub_folder_name
    except:
        pass

app = Flask(__name__)
api = Api(app)

def get_file_name(lon, lat, hgt_dict):
        """
        Returns filename such as N27E086.hgt, concatenated
        with HGTDIR where these 'hgt' files are kept
        """

        if lat >= 0:
            ns = 'N'
        elif lat < 0:
            ns = 'S'

        if lon >= 0:
            ew = 'E'
        elif lon < 0:
            ew = 'W'

        hgt_file = "%(ns)s%(lat)02d%(ew)s%(lon)03d.hgt" % {'lat': abs(np.floor(lat)), 'lon': abs(np.floor(lon)), 'ns': ns, 'ew': ew}
        if hgt_file in hgt_dict.keys():
            print(hgt_dict[hgt_file])
            hgt_file_path = os.path.join(HGTDIR, hgt_dict[hgt_file], hgt_file)
            if os.path.isfile(hgt_file_path):
                return hgt_file_path
            else:
                return None
        else:
            return None
    
def read_elevation_from_file(hgt_file_path, lon, lat):
    with open(hgt_file_path, 'rb') as hgt_data:
        # Each data is 16bit signed integer(i2) - big endian(>)
        elevations = np.fromfile(hgt_data, np.dtype('>i2'), SAMPLES*SAMPLES)\
                                .reshape((SAMPLES, SAMPLES))

        lat_row = int(round((lat - int(np.floor(lat))) * (SAMPLES - 1), 0))
        lon_row = int(round((lon - int(np.floor(lon))) * (SAMPLES - 1), 0))


        return elevations[SAMPLES - 1 - lat_row, lon_row].astype(int)
    
def get_elevation(lon, lat):
    hgt_file_path = get_file_name(lon, lat, hgt_dict)
    if hgt_file_path:
        return read_elevation_from_file(hgt_file_path, lon, lat)
    # Treat it as data void as in SRTM documentation
    # if file is absent
    return -32768   

class Elevation_Query(Resource):
    
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("lat", type=float)
        parser.add_argument("lon", type=float)
        args = parser.parse_args()
        hgt_file_path = get_file_name(lon=args["lon"], lat=args["lat"], hgt_dict=hgt_dict)
        if hgt_file_path:
            result = {"elevation":int(read_elevation_from_file(hgt_file_path=hgt_file_path, lon=args["lon"], lat=args["lat"]))}
            # print(result)
            return result, 200
        return {"elevation":"NA"}, 404


api.add_resource(Elevation_Query,"/elevation")
if __name__ == "__main__":
    app.run(debug=True, port=5050)