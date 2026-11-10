from flask import Flask, redirect, render_template_string, request, session, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sohel_master_10_cards.db'
app.config['SECRET_KEY'] = 'sohel_master_secure_key_2026'
db = SQLAlchemy(app)


# Database for Cards
class NFCCard(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  card_no = db.Column(db.String(20), unique=True, nullable=False)
  target_url = db.Column(db.String(500), nullable=False)
  clicks = db.Column(db.Integer, default=0)


# Database for Admin Settings (Username & Password Storage)
class AdminSettings(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(50), nullable=False)
  password = db.Column(db.String(50), nullable=False)


with app.app_context():
  db.create_all()

  # Automatically create 10 Demo Cards (Card 1 to Card 10)
  for i in range(1, 11):
    c_name = f'card{i}'
    existing = NFCCard.query.filter_by(card_no=c_name).first()
    if not existing:
      new_c = NFCCard(card_no=c_name, target_url='https://google.com')
      db.session.add(new_c)

  # Set default admin credentials if not already set
  admin_check = AdminSettings.query.first()
  if not admin_check:
    default_admin = AdminSettings(username='admin', password='sohel123')
    db.session.add(default_admin)

  db.session.commit()


@app.route('/')
def home_redirect():
  return redirect(url_for('admin_dashboard'))


# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    u_input = request.form.get('username', '').strip()
    p_input = request.form.get('password', '').strip()

    admin_cred = AdminSettings.query.first()
    if admin_cred and u_input == admin_cred.username and p_input == admin_cred.password:
      session['logged_in'] = True
      return redirect(url_for('admin_dashboard'))
    else:
      return "<script>alert('Invalid Username or Password!'); window.location='/login';</script>"

  return """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sign In | NFC Master Portal</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4">
        <div class="relative bg-slate-900/90 border border-slate-800 p-8 sm:p-10 rounded-3xl shadow-2xl w-full max-w-md">
            <div class="text-center mb-8">
                <div class="inline-flex items-center justify-center bg-indigo-600 text-white p-3.5 rounded-2xl text-2xl mb-4 shadow-lg">⚡</div>
                <h2 class="text-3xl font-extrabold text-white">Admin Login</h2>
                <p class="text-slate-400 text-sm mt-2">Manage your 10 demo cards & settings</p>
            </div>
            <form method="POST" class="space-y-5">
                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Username</label>
                    <input type="text" name="username" placeholder="admin" required 
                        class="w-full px-4 py-3.5 bg-slate-950 border border-slate-800 rounded-xl focus:outline-none focus:border-indigo-500 text-white font-medium">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Password</label>
                    <input type="password" name="password" placeholder="••••••••" required 
                        class="w-full px-4 py-3.5 bg-slate-950 border border-slate-800 rounded-xl focus:outline-none focus:border-indigo-500 text-white font-medium">
                </div>
                <button type="submit" 
                    class="w-full py-4 px-4 bg-indigo-600 hover:bg-indigo-500 font-bold rounded-xl shadow-lg transition text-white mt-3">
                    Sign In
                </button>
            </form>
        </div>
    </body>
    </html>
    """


@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  return redirect(url_for('login'))


# Master Dashboard (Cards 1 to 10 + Settings)
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
  if not session.get('logged_in'):
    return redirect(url_for('login'))

  action = request.form.get('action')

  # 1. Update Card Link Action
  if action == 'update_card':
    c_no = request.form.get('card_no')
    new_url = request.form.get('target_url', '').strip()
    card_item = NFCCard.query.filter_by(card_no=c_no).first()
    if card_item and new_url:
      card_item.target_url = new_url
      db.session.commit()
    return redirect(url_for('admin_dashboard'))

  # 2. Update Admin Credentials Action
  if action == 'update_settings':
    new_user = request.form.get('new_username', '').strip()
    new_pass = request.form.get('new_password', '').strip()
    if new_user and new_pass:
      admin_cred = AdminSettings.query.first()
      admin_cred.username = new_user
      admin_cred.password = new_pass
      db.session.commit()
    return redirect(url_for('admin_dashboard'))

  cards = NFCCard.query.order_by(NFCCard.id).all()
  total_clicks = sum(c.clicks for c in cards)
  admin_cred = AdminSettings.query.first()
  host_url = request.host_url.rstrip('/')

  cards_html = ''
  for card in cards:
    full_link = f'{host_url}/{card.card_no}'
    qr_img_url = (
        f'https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={full_link}'
    )

    cards_html += f"""
        <tr class="hover:bg-slate-50/80 transition border-b border-slate-100">
            <td class="py-4 px-6 font-bold text-indigo-600 text-base uppercase">
                🏷️ {card.card_no}
            </td>
            <td class="py-4 px-6 font-mono text-sm text-slate-700">
                <a href="{full_link}" target="_blank" class="hover:underline text-indigo-600 font-semibold">{full_link} ↗</a>
            </td>
            <td class="py-4 px-6 text-center">
                <div class="inline-block p-1 bg-white border border-slate-200 rounded-xl shadow-sm">
                    <img src="{qr_img_url}" alt="QR" class="w-14 h-14 object-contain rounded-lg">
                </div>
            </td>
            <td class="py-4 px-6">
                <form method="POST" class="flex gap-2 items-center">
                    <input type="hidden" name="action" value="update_card">
                    <input type="hidden" name="card_no" value="{card.card_no}">
                    <input type="text" name="target_url" value="{card.target_url}" required 
                        class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold px-3.5 py-2 rounded-lg transition whitespace-nowrap">
                        Save
                    </button>
                </form>
            </td>
            <td class="py-4 px-6 text-center font-bold text-slate-700">
                <span class="bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full text-xs border border-emerald-200">
                    {card.clicks} scans
                </span>
            </td>
            <td class="py-4 px-6 text-right">
                <a href="{qr_img_url}" download="{card.card_no}_qr.png" target="_blank" 
                   class="bg-slate-900 hover:bg-indigo-600 text-white text-xs font-semibold px-3 py-2 rounded-xl transition shadow">
                    📥 Download QR
                </a>
            </td>
        </tr>
        """

  html_template = f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NFC Master Dashboard (10 Cards)</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 text-slate-800 min-h-screen">
        <nav class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
            <div class="max-w-7xl mx-auto px-6 h-16 flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <div class="bg-indigo-600 text-white font-bold p-2.5 rounded-xl text-sm shadow">⚡</div>
                    <span class="text-lg font-extrabold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">NFC Cloud Manager (10 Cards)</span>
                </div>
                <a href="/logout" class="bg-rose-50 text-rose-600 hover:bg-rose-100 px-4 py-2 rounded-xl text-sm font-semibold transition border border-rose-100">Logout</a>
            </div>
        </nav>

        <main class="max-w-7xl mx-auto px-6 py-8">
            <!-- Top Grid Stats & Settings -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <!-- Stats Box -->
                <div class="bg-indigo-900 text-white p-6 rounded-2xl shadow-lg flex flex-col justify-between">
                    <div>
                        <h3 class="text-lg font-bold mb-1">System Status</h3>
                        <p class="text-indigo-200 text-xs">All 10 demo cards (Card 1 to Card 10) are active and ready to deploy.</p>
                    </div>
                    <div class="mt-4 flex justify-between items-center bg-white/10 px-4 py-3 rounded-xl border border-white/10">
                        <span class="text-sm font-medium">Total Global Scans:</span>
                        <span class="text-2xl font-extrabold">{total_clicks}</span>
                    </div>
                </div>

                <!-- Admin Credentials Change Box -->
                <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                    <h3 class="text-base font-bold text-slate-900 mb-1">🔐 Admin Security Settings</h3>
                    <p class="text-xs text-slate-500 mb-4">Change your portal login username and password anytime.</p>
                    <form method="POST" class="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
                        <input type="hidden" name="action" value="update_settings">
                        <div>
                            <label class="block text-xs font-bold uppercase text-slate-600 mb-1">New Username</label>
                            <input type="text" name="new_username" value="{admin_cred.username}" required 
                                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm">
                        </div>
                        <div>
                            <label class="block text-xs font-bold uppercase text-slate-600 mb-1">New Password</label>
                            <input type="text" name="new_password" value="{admin_cred.password}" required 
                                class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm">
                        </div>
                        <button type="submit" class="bg-slate-900 hover:bg-indigo-600 text-white font-semibold py-2.5 px-4 rounded-xl text-sm transition">
                            Update Credentials
                        </button>
                    </form>
                </div>
            </div>

            <!-- Cards Table -->
            <div class="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
                <div class="p-6 border-b border-slate-100 flex justify-between items-center">
                    <h3 class="text-lg font-bold text-slate-900">Active Demo Cards (1 to 10)</h3>
                    <span class="text-xs text-slate-400 font-medium">Ready for QR Print</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-slate-50 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-100">
                                <th class="py-4 px-6 font-bold">Card ID</th>
                                <th class="py-4 px-6 font-bold">Short Link</th>
                                <th class="py-4 px-6 font-bold text-center">QR Preview</th>
                                <th class="py-4 px-6 font-bold">Target Destination URL (Live Edit)</th>
                                <th class="py-4 px-6 font-bold text-center">Scans</th>
                                <th class="py-4 px-6 font-bold text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cards_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </body>
    </html>
    """
  return render_template_string(html_template)


# Redirect Engine
@app.route('/<short_code>')
def redirect_link(short_code):
  card = NFCCard.query.filter_by(card_no=short_code).first()
  if card:
    card.clicks += 1
    db.session.commit()
    return redirect(card.target_url)

  return (
      """
    <!doctype html>
    <html lang="en">
    <head><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-slate-50 flex items-center justify-center min-h-screen p-4">
        <div class="text-center p-8 bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full">
            <h1 class="text-xl font-bold text-slate-900 mb-1">Card Not Found</h1>
            <p class="text-slate-500 text-sm mb-6">This card does not exist in the database.</p>
            <a href="/admin" class="inline-block bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-semibold text-sm">Go to Dashboard</a>
        </div>
    </body>
    </html>
    """,
      404,
  )


if __name__ == '__main__':
  app.run(debug=True)