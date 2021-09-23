from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow, fields
from marshmallow import Schema, fields, post_load, ValidationError, validates
import math
from datetime import date
import datetime
import os
from pprint import pprint

# Init app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
basedir = os.path.abspath(os.path.dirname(__file__))

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialise db
db = SQLAlchemy(app)

# Iniitialise Ma
ma = Marshmallow(app)

# Models
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(100))
    despatch_date = db.Column(db.String(100))
    contents_declaration = db.Column(db.String(100))
    insurance_required = db.Column(db.Boolean)
    tracking_reference = db.Column(db.String(100))
    sender = db.relationship('Sender', backref='order', uselist=False)
    recipient = db.relationship('Recipient', backref='order', uselist=False)
    order_url = db.Column(db.String(100))
    accepted_at = db.Column(db.DateTime)
    insurance_provided = db.Column(db.Boolean)
    total_insurance_charge = db.Column(db.Float)
    ipt_included_in_charge = db.Column(db.Float)

class Sender(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    street_address = db.Column(db.String(100))
    city = db.Column(db.String(100))
    country_code = db.Column(db.String(10))
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))


class Recipient(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    street_address = db.Column(db.String(100))
    city = db.Column(db.String(100))
    country_code = db.Column(db.String(10))
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

# Schemas (with field validation)
class OrderSchema(ma.Schema):
    value = fields.String(required=True)
    despatch_date = fields.String(required=True)
    contents_declaration = fields.String(required=True)
    insurance_required = fields.String(required=True)
    tracking_reference = fields.String(required=True)
    order_url = fields.String(required=True)
    accepted_at = fields.DateTime(required=True)
    insurance_provided = fields.String(required=True)
    total_insurance_charge = fields.Float(required=True)
    ipt_included_in_charge = fields.Float(required=True)

    class Meta:
        fields = ('id','value', 'despatch_date', 'contents_declaration', 'insurance_required', 'tracking_reference')
    
    @validates('despatch_date')
    def validate_despatch_date(self, despatch_date):
        try:
            datetime.datetime.strptime(despatch_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError("Incorrect data format, should be YYYY-MM-DD")

    @validates('insurance_required')
    def valitdate_insurance_required(self, insurance_required):
        if insurance_required != "true" or "false":
            ValidationError("Insurance required not selected properly")


class SenderSchema(ma.Schema):
    name = fields.String(required=True)
    street_address = fields.String(required=True)
    city = fields.String(required=True)
    country_code = fields.String(required=True)

    class Meta:
        fields = ('name', 'street_address', 'city', 'country_code')

class RecipientSchema(ma.Schema):
    name = fields.String(required=True)
    street_address = fields.String(required=True)
    city = fields.String(required=True)
    country_code = fields.String(required=True)

    class Meta:
        fields = ('name', 'street_address', 'city', 'country_code')

# Init Schemas
order_schema = OrderSchema()

sender_schema = SenderSchema()

recipient_schema = RecipientSchema()

# Create an Order 
@app.route('/orders', methods=['PUT'])
def add_order():

    # Obtain values from request
    value = request.json['value']
    despatch_date = request.json['despatch_date']
    contents_declaration = request.json['contents_declaration']
    insurance_required = request.json['insurance_required']
    tracking_reference = request.json['tracking_reference']

    # Validate Request 
    order_data = {'value':value, 'despatch_date':despatch_date, 'contents_declaration':contents_declaration, 'insurance_required':insurance_required, 'tracking_reference':tracking_reference}
    
    try:
        validate_order_data = order_schema.load(order_data)

        # If validation passed, change insurance_required from string to boolean 

        if insurance_required == "true":
            insurance_required = True
        elif insurance_required == "false":
            insurance_required = False
            
    except ValidationError as err:
        print(err)
        print(err.valid_data)

        return Response(f"Order fields not submitted correctly: {err}", status=400)

    # Check if tracking reference already exists. 
    exists = db.session.query(db.exists().where(Order.tracking_reference == tracking_reference)).scalar()
    if exists:
        
        return Response("This Tracking reference already exists. Please use a different reference to make a new order", status=400)

    # Check if despatch date is today or tomorrow 
    today = date.today()
    tomorrow = today + datetime.timedelta(days=1)
    despatch_date_datetime = datetime.date.fromisoformat(despatch_date) # Converts string to date format

    if today != despatch_date_datetime and tomorrow != despatch_date_datetime: 
        return "You can't send a package on this date. Your order has not been processed. Please select an adequate despatch date (today or tomorrow).", 400
    
    # Add order details to db
    new_order = Order(value=value, despatch_date=despatch_date, contents_declaration=contents_declaration, insurance_required=insurance_required, tracking_reference=tracking_reference)
    db.session.add(new_order)
    db.session.commit()

    # Get sender details from request and add to db
    sender_name = request.json['sender']['name']
    sender_street_address = request.json['sender']['street_address']
    sender_city = request.json['sender']['city']
    sender_country_code = request.json['sender']['country_code']

    # Validate Request (Sender detials)
    sender_data = {'name':sender_name, 'street_address': sender_street_address, 'city': sender_city, 'country_code':sender_country_code}
    
    try:
        validate_sender_data = sender_schema.load(sender_data)
    except ValidationError as err:
        print(err)
        print(err.valid_data)

        return f"Sender fields not submitted correctly: {err}", 400

    new_sender = Sender(name=sender_name, street_address=sender_street_address, city=sender_city, country_code=sender_country_code, order=new_order)
    db.session.add(new_sender)
    db.session.commit()
    
    # Get recipient details from ruquest and add to db
    recipient_name = request.json['recipient']['name']
    recipient_street_address = request.json['recipient']['street_address']
    recipient_city = request.json['recipient']['city']
    recipient_country_code = request.json['recipient']['country_code']

    # Validate Request (Recipient detials)
    recipient_data = {'name':recipient_name, 'street_address': recipient_street_address, 'city': recipient_city, 'country_code':recipient_country_code}
    
    try:
        validate_recipient_data = recipient_schema.load(recipient_data)
    except ValidationError as err:
        print(err)
        print(err.valid_data)

        return f"Recipient fields not submitted correctly: {err}", 400

    new_recipient = Recipient(name=recipient_name, street_address=recipient_street_address, city=recipient_city, country_code=recipient_country_code, order=new_order)
    db.session.add(new_recipient)
    db.session.commit()
    

    if insurance_required == False:
        insurance_provided = False

        # Save to database without needing insurance. Return to user.
        new_order.order_url = f"http://127.0.0.1:5000/order/{new_order.id}"
        new_order.accepted_at = datetime.datetime.now()
        new_order.insurance_provided = insurance_provided
        new_order.total_insurance_charge = None
        new_order.ipt_included_in_charge = None

        # Commit changes to database
        db.session.commit()
    
        # Serialize model data
        serialized_sender = sender_schema.dump(new_sender)
        serialized_recipient = recipient_schema.dump(new_recipient)
        serialized_order = order_schema.dump(new_order)
        
        return {
            "package": {
                "sender": serialized_sender,
                "recipient": serialized_recipient,
                "order" : serialized_order
            },
        }
    
    elif insurance_required == True:

        # Check value of package
        if float(value) > 10000: 
            insurance_provided = False

            # Delete order, sender and recipient from db. (The user wants insurance but we can't provide it, so we can't process this order)
            db.session.delete(new_order)
            db.session.delete(new_recipient)
            db.session.delete(new_sender)
            db.session.commit()

            return "Sorry, we cannot insure a package worth more than 10,000. Your order has not been processed. Try again with a less valuable package or select 'no insurance required' ", 400

        # Initialise insurance charge
        total_insurance_charge = None

        # Check Insurance charge by country 
        one_percent_charge = ["UK"]
        one_point_five_percent_charge = ["FR", "DE", "NL", "BE"]

        if recipient_country_code in one_percent_charge: 

            total_insurance_charge = (1/100) * float(value)

        elif recipient_country_code in one_point_five_percent_charge: 

            total_insurance_charge = (1.5/100) * float(value)
        
        else: 

            total_insurance_charge = (4/100) * float(value)
        
        # Round insurance charge
        total_insurance_charge = round(total_insurance_charge / 0.01) * 0.01

        # Check if Insurance charge less than £9 then round to 9. 
        if total_insurance_charge < 9: 
            total_insurance_charge = 9
        
        # Calculate and Round Insurance Premium Tax (IPT)
        ipt_included_in_charge = total_insurance_charge - (total_insurance_charge / 1.12)
        ipt_included_in_charge = round(ipt_included_in_charge / 0.01) * 0.01

        # Set insurance provided to true
        insurance_provided = True

        # Save Insurance calculations to order model
        new_order.order_url = f"http://127.0.0.1:5000/order/{new_order.id}"
        new_order.accepted_at = datetime.datetime.now()
        new_order.insurance_provided = insurance_provided
        new_order.total_insurance_charge = total_insurance_charge
        new_order.ipt_included_in_charge = ipt_included_in_charge

        # Commit changes to database
        db.session.commit()
    
        # Serialize model data
        serialized_sender = sender_schema.dump(new_sender)
        serialized_recipient = recipient_schema.dump(new_recipient)
        serialized_order = order_schema.dump(new_order)

    return {
            "package": {
                "sender": serialized_sender,
                "recipient": serialized_recipient,
                "order" : serialized_order, 
            },
    }

# Get individual Orders
@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get(order_id)
    sender = Sender.query.filter_by(order_id=order_id).first()
    recipient = Recipient.query.filter_by(order_id=order_id).first()

    serialized_order = order_schema.dump(order)
    serialized_sender = sender_schema.dump(sender)
    serialized_recipient = recipient_schema.dump(recipient)

    return {
            "package": {
                "sender": serialized_sender,
                "recipient": serialized_recipient,
                "order" : serialized_order, 
            },
            "order_url": order.order_url,
            "accepted_at": order.accepted_at,
            "insurance_provided": order.insurance_provided,
            "total_insurance_charge": order.total_insurance_charge,
            "ipt_included_in_charge": order.ipt_included_in_charge
    }



# Run server
if __name__ == '__main__':
    app.run(debug=True)