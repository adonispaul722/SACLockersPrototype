from datetime import datetime
from database import db
from enum import Enum
from models import RentTypes

class Status(Enum):
    PARTIAL = "Partial"
    RETURNED = "Returned"
    PAID = "Paid"
    OWED = "Owed"
    OVERDUE = "Overdue"

class Rent(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    student_id = db.Column (db.Integer, db.ForeignKey("student.student_id"), nullable= False)
    locker_id = db.Column(db.String, db.ForeignKey("locker.locker_code"), nullable= False)
    rent_type =  db.Column(db.Integer, db.ForeignKey("RentTypes.id"), nullable= False)
    rent_date_from =  db.Column(db.DateTime, nullable= False)
    rent_date_to = db.Column(db.DateTime, nullable= False)
    date_returned = db.Column(db.DateTime, nullable = True)
    amount_owed = db.Column(db.Float, nullable= False)
    status = db.Column(db.Enum(Status), nullable = False)
    Transactions = db.relationship('TransactionLog', backref='rent', lazy=True, cascade="all, delete-orphan")

    def __init__(self, student_id, locker_id, rent_type, rent_date_from, rent_date_to):
        self.student_id = student_id
        self.locker_id = locker_id
        self.rent_type =  rent_type
        self.rent_date_from =  datetime.strptime(rent_date_from,'%Y-%m-%dT%H:%M')
        self.rent_date_to  =  datetime.strptime(rent_date_to,'%Y-%m-%dT%H:%M')
        self.amount_owed = self.cal_amount_owed()
        self.status = self.check_status()
    
    def check_status(self):
        if not self.Transactions:
            if datetime.now() > self.rent_date_to:
                return Status.OVERDUE
            return Status.OWED
        else:
            amount = self.cal_transactions()
            if amount < self.cal_amount_owed():
                return Status.PARTIAL
            elif self.cal_amount_owed() == 0:
                if self.date_returned:
                    return Status.RETURNED
                return Status.PAID
            return Status.OWED

    def cal_transactions(self):
        if not self.Transactions:
            return 0
        amount = 0
        for t in self.Transactions:
            amount += float(t.amount)
        return amount
        
    def cal_amount_owed(self):
        type = RentTypes.query.filter_by(id = self.rent_type).first()

        if not type:
            return -1

        price = float(type.price)
        time = self.rent_date_to - self.rent_date_from
    
        return (price * time.days + self.late_fees()) - self.cal_transactions()
        
    
    def late_fees(self):
        type = RentTypes.query.filter_by(id = self.rent_type).first()
        
        if not type:
            return -1
        
        if self.date_returned:
            time = self.date_returned - self.rent_date_to
            return type.price - time.days
        elif datetime.now() > self.rent_date_to:
            time = datetime.now() - self.rent_date_to
            return type.price  *  time.days
        else:
            return 0.0
    
    def toJSON(self):
        return {
            "id":self.id,
            "student_id" : self.student_id,
            "locker_id":  self.locker_id,
            "rent_type": self.rent_type,
            "rent_date_from": self.rent_date_from,
            "rent_date_to": self.rent_date_to,
            "date_returned":self.date_returned,
            "amount_owed":self.cal_amount_owed(),
            "status":self.check_status()
        }