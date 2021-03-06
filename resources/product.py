from flask_restful import Resource, reqparse
from models.Product import ProductModel
from models.User import UserModel
from common.db import db
from crawler.SpiderifyWrapper import SpiderifyWrapper
from flask import jsonify, Response, json


class Product(Resource):
    def get(self, username, asin):
        # db.session.query(UserModel).join(ProductModel).filter(username, asin)
        # product = ProductModel.query.filter_by(asin=asin)
        # return
        pass

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


class ProductList(Resource):
    def get(self):
        pass


class FakeProduct(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('url', type=str, required=True,
                        help="This Is The Base Product URL")

    def post(self):
        data = FakeProduct.parser.parse_args()
        spider = SpiderifyWrapper(str(data["url"]))
        spider_data = spider.start_amazon_spider()
        message = json.dumps(spider_data)
        resp = Response(message, status=200, mimetype='application/json')
        return resp
