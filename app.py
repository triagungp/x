from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for, make_response
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
from os.path import join, dirname
from dotenv import load_dotenv
from bson import ObjectId

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_PRODUK'] = './static/produk'

SECRET_KEY = 'SPARTA'
TOKEN_KEY = 'mytoken'


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]


@app.route('/', methods = ['GET'])
def main():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload =jwt.decode(
            token_receive, 
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({"email": payload["id"]})
        is_admin = user_info.get("category") == "admin"
        logged_in = True
        return render_template('homepage.html', user_info=user_info, logged_in = logged_in, is_admin = is_admin)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem logging you in'
    return render_template('homepage.html', msg=msg)


@app.context_processor
def inject_logged_in():
    token_receive = request.cookies.get(TOKEN_KEY)
    logged_in = False
    is_admin = None
    is_user = None
    email = None
    address = None

    if token_receive:
        try:
            payload = jwt.decode(
                token_receive,
                SECRET_KEY,
                algorithms=['HS256']
            )
            user_info = db.users.find_one({"email": payload["id"]})
            if user_info:
                logged_in = True
                is_admin = user_info.get("role") == "admin"
                is_user = user_info.get("role") == "customers"
                email = user_info.get("email")
                address = user_info.get("address")
        except jwt.ExpiredSignatureError:
            pass
        except jwt.exceptions.DecodeError:
            pass

    return {'logged_in': logged_in, 'is_admin': is_admin, 'is_user': is_user, 'email': email, 'address': address}

@app.route('/signup')
def signup():
    error_message = request.args.get('error_message', None)
    return render_template('register.html', error_message=error_message)

@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    name = request.form.get('name')
    email = request.form.get('email')
    address = request.form.get('address')
    password = request.form.get('password')
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    existing_user = db.users.find_one({'email': email})

    if existing_user:
        return redirect(url_for('signup', error_message='Email already registered'))
    doc = {
        "name": name,
        "email": email,
        "address": address,
        "role": 'customers',
        "password": password_hash
    }

    db.users.insert_one(doc)

    return redirect(url_for('signin'))

@app.route('/signin')
def signin():
    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect(url_for('signin')))
    response.delete_cookie(TOKEN_KEY)
    return response

@app.route('/sign_in', methods=['POST'])
def sign_in():
    email = request.form["email"]
    password = request.form["password"]
    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    result = db.users.find_one(
        {
            "email": email,
            "password": pw_hash,
        }
    )
    if result:
        payload = {
            "id": email,
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        response = make_response(redirect(url_for('main')))
        response.set_cookie(TOKEN_KEY, token)
        return response
    else:
        return jsonify(
            {
                "result": "fail",
                "msg": "We could not find a user with that id/password combination",
            }
        )


@app.route('/produk')
def show_produk():
    produk_list = db.produk.find()

    return render_template('produk.html', produk_list=produk_list)

@app.route('/edit', methods=['POST'])
def edit_produk():
    product_id = request.form.get('produk._id')
    nama_produk = request.form.get('nama_produk')
    harga_produk = request.form.get('harga_produk')
    deskripsi_produk = request.form.get('deskripsi_produk')
    kategori_produk = request.form['kategori_produk']


    existing_filename = request.form.get('existing_foto_produk', 'default.jpg')
    filename = existing_filename


    if 'foto_produk' in request.files:
        foto_produk = request.files['foto_produk']
        if foto_produk.filename != '':
            file_extension = foto_produk.filename.rsplit('.', 1)[1].lower() if '.' in foto_produk.filename else 'jpg'

            filename = secure_filename(f"{nama_produk}.{file_extension}")
            foto_produk.save(os.path.join(app.config['UPLOAD_PRODUK'], filename))

    db.produk.update_one(
        {'_id': ObjectId(product_id)},
        {
            '$set': {
                'nama_produk': nama_produk,
                'harga_produk': harga_produk,
                'deskripsi_produk': deskripsi_produk,
                'kategori_produk': kategori_produk

            }
        }
    )

    if filename != existing_filename:
        db.produk.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {'foto_produk': filename}}
        )

    return redirect(url_for('show_produk'))

@app.route('/add', methods=['POST'])
def add_product():
    nama_produk = request.form['nama_produk']
    harga_produk = request.form['harga_produk']
    deskripsi_produk = request.form['deskripsi_produk']
    kategori_produk = request.form['kategori_produk']


    foto_produk = request.files['foto_produk'] if 'foto_produk' in request.files else None

    if foto_produk and foto_produk.filename != '':
        file_extension = foto_produk.filename.rsplit('.', 1)[1].lower() if '.' in foto_produk.filename else 'jpg'

        filename = secure_filename(f"{nama_produk}.{file_extension}")
        foto_produk.save(os.path.join(app.config['UPLOAD_PRODUK'], filename))
    else:
        filename = 'default.jpg'

    produk_data = {
        'nama_produk': nama_produk,
        'foto_produk': filename,
        'harga_produk': harga_produk,
        'deskripsi_produk': deskripsi_produk,
        'kategori_produk': kategori_produk
    }

    db.produk.insert_one(produk_data)

    return redirect(url_for('show_produk'))

@app.route('/delete', methods=['POST'])
def delete_product():
    product_id = request.form['produk._id']
    db.produk.delete_one({'_id': ObjectId(product_id)})

    return redirect(url_for('show_produk'))

@app.route('/buy', methods=['POST'])
def buy_product():
    product_id = request.form['produk._id']

    email_pemesan = request.form['email_pemesan']
    nama_produk = request.form['nama_produk']
    alamat = request.form['alamat']
    foto_produk= request.form['foto_produk']
    status_pemesanan = 'Pending' 
    harga_produk= int(request.form['harga_produk'])

    quantity_key = f'jumlah_pesanan_{product_id}'
    jumlah_pesanan = int(request.form.get(quantity_key))
    total_harga = harga_produk*jumlah_pesanan

    pesanan_data = {
        'email_pemesan': email_pemesan,
        'nama_produk': nama_produk,
        'jumlah_pesanan': jumlah_pesanan,
        'alamat': alamat,
        'status_pemesanan': status_pemesanan,
        'foto_produk':foto_produk,
        'total_harga':total_harga
    }

    db.pesanan.insert_one(pesanan_data)
    return redirect(url_for('riwayat_pesanan'))

@app.route('/cart', methods=['POST'])
def add_to_cart():
    product_id = request.form['produk._id']
    harga_produk = int(request.form['harga_produk']) 
    foto_produk = request.form['foto_produk']
    email_pemesan = request.form['email_pemesan']
    nama_produk = request.form['nama_produk']
    alamat = request.form['alamat']
    status_pemesanan = 'In Cart' 

    quantity_key = f'insert_cart_{product_id}'
    jumlah_pesanan = int(request.form.get(quantity_key))

    total_harga = harga_produk * jumlah_pesanan

    pesanan_data = {
        'email_pemesan': email_pemesan,
        'nama_produk': nama_produk,
        'jumlah_pesanan': jumlah_pesanan,
        'alamat': alamat,
        'foto_produk': foto_produk,
        'harga_produk': harga_produk,
        'total_harga': total_harga,
        'status_pemesanan': status_pemesanan
    }

    db.pesanan.insert_one(pesanan_data)

    return redirect(url_for('show_produk'))

@app.route('/keranjang')
def keranjang():
    cart_items_cursor = db.pesanan.find({'status_pemesanan': 'In Cart'})
    cart_items = list(cart_items_cursor)

    return render_template('keranjang.html', cart_items=cart_items)

@app.route('/delete_cart_item', methods=['POST'])
def delete_cart_item():
    cart_item_id = request.form['cart_item_id']
    
    db.pesanan.delete_one({'_id': ObjectId(cart_item_id)})
    print(f"Deleted cart item with ID: {cart_item_id}")
    return redirect(url_for('keranjang'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        user_info = db.users.find_one({"email": payload["id"]})
    except jwt.ExpiredSignatureError:
        user_info = None

    edit_mode = bool(request.args.get('edit_mode', False))

    if request.method == 'POST':
        if edit_mode:
            new_name = request.form.get('name')
            new_address = request.form.get('address')

            db.users.update_one(
                {'email': user_info['email']},
                {'$set': {'name': new_name, 'address': new_address}}
            )

            user_info = db.users.find_one({"email": payload["id"]})

        return redirect(url_for('profile', edit_mode=int(edit_mode)))

    return render_template('profile.html', user_info=user_info, edit_mode=edit_mode)


@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if request.method == 'POST':
        token_receive = request.cookies.get(TOKEN_KEY)

        try:
            payload = jwt.decode(
                token_receive,
                SECRET_KEY,
                algorithms=['HS256']
            )
            user_info = db.users.find_one({"email": payload["id"]})
        except jwt.ExpiredSignatureError:
            user_info = None

        if user_info:
            new_name = request.form.get('name')
            new_address = request.form.get('address')
            new_email = request.form.get('email')

            if 'profile_picture' in request.files:
                profile_picture = request.files['profile_picture']
                if profile_picture.filename != '':
                    filename = secure_filename(profile_picture.filename)
                    profile_picture.save(os.path.join(app.config['UPLOAD_PROFILE'], filename))

                    db.users.update_one(
                        {'email': user_info['email']},
                        {'$set': {'profile_picture': filename}}
                    )

            db.users.update_one(
                {'email': user_info['email']},
                {'$set': {'name': new_name, 'address': new_address, 'email': new_email}}
            )

            return redirect(url_for('profile'))
        return render_template('profile.html', user_info=None)

@app.route('/riwayat-pesanan')
def riwayat_pesanan():
    riwayat_pesanan= db.pesanan.find()
    return render_template('riwayat-pesanan.html',riwayat_pesanan=riwayat_pesanan)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)