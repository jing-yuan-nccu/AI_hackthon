from flask import jsonify

def make_error(msg, code=400):
    return jsonify({"error": msg}), code

def make_ok(data):
    return jsonify({"data": data}), 200
