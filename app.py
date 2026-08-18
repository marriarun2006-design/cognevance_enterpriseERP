
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from sqlalchemy import func
import os

app=Flask(__name__)
app.config["SECRET_KEY"]=os.environ.get("SECRET_KEY","change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"]=os.environ.get("DATABASE_URL","sqlite:///erp.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
db=SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(150),unique=True,nullable=False)
    password_hash=db.Column(db.String(255),nullable=False)
    role=db.Column(db.String(30),default="employee")

class Employee(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    department=db.Column(db.String(100),default="")
    position=db.Column(db.String(100),default="")
    salary=db.Column(db.Float,default=0)
    email=db.Column(db.String(150),default="")

class Inventory(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(120),nullable=False)
    sku=db.Column(db.String(50),unique=True,nullable=False)
    quantity=db.Column(db.Integer,default=0)
    price=db.Column(db.Float,default=0)

class Sale(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    item=db.Column(db.String(120),nullable=False)
    quantity=db.Column(db.Integer,default=1)
    amount=db.Column(db.Float,default=0)
    sold_at=db.Column(db.DateTime,default=datetime.utcnow)

class Finance(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    kind=db.Column(db.String(30),nullable=False) # income/expense
    category=db.Column(db.String(100),default="")
    amount=db.Column(db.Float,default=0)
    note=db.Column(db.String(255),default="")
    created_at=db.Column(db.DateTime,default=datetime.utcnow)

with app.app_context(): db.create_all()

def auth(f):
    @wraps(f)
    def wrap(*a,**kw):
        if "user_id" not in session:return redirect(url_for("login"))
        return f(*a,**kw)
    return wrap

def admin(f):
    @wraps(f)
    def wrap(*a,**kw):
        if session.get("role") not in ("admin","manager"):return "Forbidden",403
        return f(*a,**kw)
    return wrap

@app.route("/")
@auth
def dashboard():
    revenue=db.session.query(func.coalesce(func.sum(Sale.amount),0)).scalar()
    expenses=db.session.query(func.coalesce(func.sum(Finance.amount),0)).filter(Finance.kind=="expense").scalar()
    inventory=Inventory.query.count()
    employees=Employee.query.count()
    recent=Sale.query.order_by(Sale.sold_at.desc()).limit(5).all()
    return render_template("dashboard.html",revenue=revenue,expenses=expenses,inventory=inventory,employees=employees,recent=recent)

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        email=request.form["email"].lower().strip()
        if User.query.filter_by(email=email).first(): return "Email already exists",400
        u=User(name=request.form["name"],email=email,role=request.form.get("role","employee"),
               password_hash=generate_password_hash(request.form["password"]))
        if u.role not in ("employee","manager","admin"):u.role="employee"
        db.session.add(u);db.session.commit();return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=User.query.filter_by(email=request.form["email"].lower().strip()).first()
        if u and check_password_hash(u.password_hash,request.form["password"]):
            session.update(user_id=u.id,name=u.name,role=u.role);return redirect(url_for("dashboard"))
        return render_template("login.html",error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():session.clear();return redirect(url_for("login"))

@app.route("/employees",methods=["GET","POST"])
@auth
@admin
def employees():
    if request.method=="POST":
        db.session.add(Employee(name=request.form["name"],department=request.form["department"],position=request.form["position"],salary=float(request.form["salary"] or 0),email=request.form["email"]))
        db.session.commit()
    return render_template("employees.html",employees=Employee.query.order_by(Employee.id.desc()).all())

@app.route("/inventory",methods=["GET","POST"])
@auth
@admin
def inventory():
    if request.method=="POST":
        db.session.add(Inventory(name=request.form["name"],sku=request.form["sku"],quantity=int(request.form["quantity"]),price=float(request.form["price"])))
        db.session.commit()
    return render_template("inventory.html",items=Inventory.query.order_by(Inventory.id.desc()).all())

@app.route("/sales",methods=["GET","POST"])
@auth
def sales():
    if request.method=="POST":
        item=request.form["item"]; qty=int(request.form["quantity"]); amount=float(request.form["amount"])
        db.session.add(Sale(item=item,quantity=qty,amount=amount))
        db.session.commit()
    return render_template("sales.html",sales=Sale.query.order_by(Sale.sold_at.desc()).all())

@app.route("/finance",methods=["GET","POST"])
@auth
@admin
def finance():
    if request.method=="POST":
        db.session.add(Finance(kind=request.form["kind"],category=request.form["category"],amount=float(request.form["amount"]),note=request.form["note"]))
        db.session.commit()
    records=Finance.query.order_by(Finance.created_at.desc()).all()
    income=sum(x.amount for x in records if x.kind=="income")
    expense=sum(x.amount for x in records if x.kind=="expense")
    return render_template("finance.html",records=records,income=income,expense=expense)

@app.route("/analytics")
@auth
def analytics():
    by_kind=db.session.query(Finance.kind,func.sum(Finance.amount)).group_by(Finance.kind).all()
    by_item=db.session.query(Sale.item,func.sum(Sale.amount)).group_by(Sale.item).all()
    return render_template("analytics.html",by_kind=by_kind,by_item=by_item)

@app.route("/api/summary")
@auth
def api_summary():
    revenue=db.session.query(func.coalesce(func.sum(Sale.amount),0)).scalar()
    expense=db.session.query(func.coalesce(func.sum(Finance.amount),0)).filter(Finance.kind=="expense").scalar()
    return jsonify({"revenue":revenue,"expenses":expense,"profit":revenue-expense,"employees":Employee.query.count(),"inventory_items":Inventory.query.count()})

if __name__=="__main__":app.run(debug=True)
