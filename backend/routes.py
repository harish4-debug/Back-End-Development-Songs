from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count")
def count():
    if songs_list:
        return {"count" : len(songs_list)}, 200

    return {"message": "Internal server error"}, 500

@app.route("/song", methods=["GET"])
def get_songs():
    try:
        return {"songs": parse_json(list(db.songs.find({})))}, 200
    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(e)
        }), 500

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    try:
        song = db.songs.find_one({"id": id})
        if not song:
            return {"message": "song with id not found"}, 404
        else:
            return parse_json(song), 200
    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(e)
        }), 500


@app.route("/song", methods=["POST"])
def create_song():
    try:
        new_song = request.get_json()
        if not new_song:
            return {"message": "Invalid input, no data provided"}, 400

        id = new_song['id']
        old_song = db.songs.find_one({"id": id})

        if not old_song:
            # Songes not exit.
            db.songs.insert_one(new_song)
            return parse_json(new_song), 201
        else:
            return jsonify({"Message":f"song with id {old_song['id']} already present"}), 302

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(e)
        }), 500

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    try:
        new_song = request.get_json()
        if not new_song:
            return {"message": "Invalid input, no data provided"}, 400

        old_song = db.songs.find_one({"id": id})

        if not old_song:
            # Song does not exit.
            return jsonify({"Message":"song not found"}), 302
        else:
            update_result = db.songs.update_one({"id": id}, {"$set": new_song}, upsert=False)
            if update_result.modified_count == 0:
                return {"message": "song found, but nothing updated"}, 200
            else:
                return parse_json(new_song), 200
            

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(e)
        }), 500


@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    try:
        deleted_count = db.songs.delete_one({"id": id})

        if deleted_count == 0:
            # Song does not exit.
            return jsonify({"message":"song not found"}), 404
        else:
            return jsonify({}), 204

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(e)
        }), 500