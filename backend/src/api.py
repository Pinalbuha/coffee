import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from werkzeug.wrappers import response

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES

@app.after_request
def after_request(response):
    response.headers.add('Acess-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Acess-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    return response

'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=['GET'])
def get_drinks():
    alldrinks = Drink.query.all()
    drinks = [drink.short() for drink in alldrinks]
    
    if len(drinks) == 0:
        abort(404)
    return jsonify({
        'success': True,
        "drinks": drinks
    }),200
        
'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    alldrinks = Drink.query.all()
    drinks = [drink.long() for drink in alldrinks]
    if len(drinks) == 0:
        abort(404)
    return jsonify({
        "success": True,
        "drinks": drinks
    }),200
    
'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drink(payload):
    try:
        body = request.get_json()
        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)
        if (new_title is None) or (new_recipe is None):
            abort(422)
        if type(new_recipe) is not list:
            new_recipe = [new_recipe]
        drink = Drink(title=new_title, recipe=json.dumps(new_recipe))
        new_drinks = Drink.query.all()
        for newdrink in new_drinks:
            if (drink.title == newdrink.title) or (drink.recipe == newdrink.recipe):
                abort(422)
        drink.insert()
        return jsonify({
            'success': True,
            "drinks": [drink.long()]
        }),200
    except AuthError:
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, id):
    try:
        
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            abort(404)
        body = request.get_json()
        updated_title = body.get('title', None)
        updated_recipe = body.get('recipe', None)
        if updated_title is not None:
            drink.title = updated_title
        if updated_recipe is not None:
            if type(updated_recipe) is not list:
                updated_recipe = [updated_recipe]
            drink.recipe = json.dumps(updated_recipe)
        drink.update()
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        }),200
    except AuthError:
        abort(422)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink:
            drink.delete()
            return jsonify({
                'success': True,
                'delete': id
            }), 200
        else:
            abort(404)
    except Exception:
        abort(500)

# Error Handling
'''
Example error handling for unprocessable entity
'''

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': "resource not found"
    }), 404

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def autherror(error):
    return jsonify({
        "success":False,
        "error":error.status_code,
        "message":error.error
    }),error.status_code
    
