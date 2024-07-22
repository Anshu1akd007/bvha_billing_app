from flask import Flask, render_template, request, redirect, send_file, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bills.db'
db = SQLAlchemy(app)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now(datetime.timezone.ist).date())
    items = db.relationship('Item', backref='bill', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

@app.route('/')
def index():
    bills = Bill.query.order_by(Bill.id.desc()).all()
    return render_template('index.html', bills=bills)

@app.route('/bill/<int:bill_id>')
def bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    items = Item.query.filter_by(bill_id=bill.id).all()
    
    # Calculate grand total
    grand_total = sum(item.total_price for item in items)
    
    return render_template('bill.html', bill=bill, items=items, grand_total=grand_total)

@app.route('/bill/<int:bill_id>/pdf')
def bill_pdf(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    items = Item.query.filter_by(bill_id=bill.id).all()
    
    # Calculate grand total
    grand_total = sum(item.total_price for item in items)
    
    # pdf_filename = f"{bill.name}_{bill.date.strftime('%d_%m_%Y')}.pdf"
    
    # Create PDF in memory
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x_offset=50
    #Add top
    p.drawImage("BVHA Letterhead1.jpg",x= 0, y= height-200,width=width,preserveAspectRatio=True, mask='auto')

    # Add bottom image
    p.drawImage("BVHA Letterhead bottom.jpg", 0, 0, width=width,preserveAspectRatio=True, mask='auto')

    #bill details

    p.setFont("Helvetica", 12)
    p.drawString(x_offset, height - 125, f"Bill ID: {bill.id}")
    p.drawString(x_offset+400, height - 125, f"Date: {bill.date.strftime('%d-%m-%Y')}")
    p.drawString(x_offset, height - 150, f"Name: {bill.name}")
    p.drawString(x_offset, height - 175, f"Event From: {bill.from_date.strftime('%d-%m-%Y')}")
    p.drawString(x_offset + 200, height - 175, f"To: {bill.to_date.strftime('%d-%m-%Y')}")
    #address

    #Table Headers
    y_offset = height-220
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x_offset, height - 200, "Items:")
    p.drawString(x_offset, y_offset, "Description")
    p.drawString(x_offset+280, y_offset, "Unit Price")
    p.drawString(x_offset+350, y_offset, "Quantity")
    p.drawString(x_offset+405, y_offset, "Days")
    p.drawString(width-100, y_offset, "Total Price")

    p.setFont("Helvetica", 12)
    for item in items:
        y_offset -= 1 * cm
        p.drawString(x_offset, y_offset, item.description)
        p.drawString(x_offset+280, y_offset, f"{item.unit_price:.2f}")
        p.drawString(x_offset+360, y_offset, str(item.quantity))
        p.drawString(x_offset+408, y_offset, str(item.days))
        p.drawString(width-100, y_offset, f"{item.total_price:.2f}")

    y_offset -= 1.5* cm
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x_offset, y_offset, f"Grand Total: {grand_total:.2f}")
    p.setFont("Helvetica", 8)
    p.drawString(500,100,"(Authorized Signature)")

    p.showPage()
    p.save()

    buffer.seek(0)

    filename = f"{bill.name}_{bill.from_date.strftime('%d-%m-%Y')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    from_date = request.form['from_date']
    to_date = request.form['to_date']
    descriptions = request.form.getlist('description')
    unit_prices = request.form.getlist('unit_price')
    quantities = request.form.getlist('quantity')
    days_list = request.form.getlist('days')

    bill = Bill(name=name, from_date=datetime.strptime(from_date, '%Y-%m-%d').date(), to_date=datetime.strptime(to_date, '%Y-%m-%d').date())
    db.session.add(bill)
    db.session.commit()

    for description, unit_price, quantity, days in zip(descriptions, unit_prices, quantities, days_list):
        if description and unit_price and quantity and days:
            total_price = float(unit_price) * int(quantity) * int(days)
            item = Item(
                bill_id=bill.id,
                description=description,
                unit_price=float(unit_price),
                quantity=int(quantity),
                days=int(days),
                total_price=total_price
            )
            db.session.add(item)
    db.session.commit()

    return redirect(url_for('index'))
if __name__ == '__main__':
    with app.app_context():
        # db.drop_all() # use this to drop prevous database
        db.create_all()
    app.run(debug=True)
