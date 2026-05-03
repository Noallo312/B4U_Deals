import os
import requests
import random
import traceback
import asyncio
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from functools import wraps
import threading

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session

# ========== CONFIG ==========
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [6976573567, 5174507979]
WEB_PASSWORD = os.getenv('WEB_PASSWORD')

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY', 'votre_secret_key_aleatoire_ici')
from flask_cors import CORS
CORS(app, origins=["https://Noallo312.github.io"], supports_credentials=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# ========== SERVICES_CONFIG ==========
SERVICES_CONFIG = {
    'netflix': {'name': '🎬 Netflix', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'standard': {'label': 'Netflix Premium', 'price': 9.00, 'cost': 1.50}}},
    'primevideo': {'name': '🎬 Prime Video', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'1_mois': {'label': 'Prime Video 1 mois', 'price': 5.00, 'cost': 1.50}, '6_mois': {'label': 'Prime Video 6 mois', 'price': 15.00, 'cost': 5.00}}},
    'hbo': {'name': '🎬 HBO Max', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'standard': {'label': 'HBO Max', 'price': 6.00, 'cost': 1.00}}},
    'crunchyroll': {'name': '🎬 Crunchyroll', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'standard': {'label': 'Crunchyroll', 'price': 5.00, 'cost': 1.00}}},
    'canal': {'name': '🎬 Canal+', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'standard': {'label': 'Canal+', 'price': 9.00, 'cost': 2.00}}},
    'disney': {'name': '🎬 Disney+', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'standard': {'label': 'Disney+', 'price': 6.00, 'cost': 1.00}}},
    'youtube': {'name': '▶️ YouTube Premium', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'1_mois': {'label': 'YouTube Premium 1 mois', 'price': 5.00, 'cost': 1.00}, '1_an': {'label': 'YouTube Premium 1 an', 'price': 20.00, 'cost': 4.00}}},
    'paramount': {'name': '🎬 Paramount+', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'standard': {'label': 'Paramount+', 'price': 7.00, 'cost': 1.50}}},
    'rakuten': {'name': '🎬 Rakuten Viki', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'standard': {'label': 'Rakuten Viki', 'price': 7.00, 'cost': 1.50}}},
    'molotov': {'name': '📺 Molotov TV', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'standard': {'label': 'Molotov TV', 'price': 9.00, 'cost': 2.00}}},
    'brazzers': {'name': '🔞 Brazzers', 'active': True, 'visible': True, 'category': 'streaming', 'plans': {'standard': {'label': 'Brazzers', 'price': 3.50, 'cost': 0.50}}},
    'ufc': {'name': '🥊 UFC Fight Pass', 'active': True, 'visible': True, 'category': 'sport', 'plans': {'standard': {'label': 'UFC Fight Pass', 'price': 5.00, 'cost': 1.00}}},
    'nba': {'name': '🏀 NBA League Pass', 'active': True, 'visible': True, 'category': 'sport', 'plans': {'standard': {'label': 'NBA League Pass', 'price': 5.00, 'cost': 1.00}}},
    'dazn': {'name': '⚽ DAZN', 'active': True, 'visible': True, 'category': 'sport', 'plans': {'standard': {'label': 'DAZN', 'price': 8.00, 'cost': 1.50}}},
    'spotify': {'name': '🎧 Spotify Premium', 'active': True, 'visible': True, 'category': 'music', 'plans': {'2_mois': {'label': 'Spotify Premium 2 mois', 'price': 10.00, 'cost': 2.00}, '1_an': {'label': 'Spotify Premium 1 an', 'price': 20.00, 'cost': 4.00}}},
    'deezer': {'name': '🎵 Deezer Premium', 'active': True, 'visible': True, 'category': 'music', 'plans': {'a_vie': {'label': 'Deezer Premium à vie', 'price': 8.00, 'cost': 1.50}}},
    'chatgpt': {'name': '🤖 ChatGPT+', 'active': True, 'visible': True, 'category': 'ai', 'plans': {'1_mois': {'label': 'ChatGPT+ 1 mois', 'price': 5.00, 'cost': 1.00}, '1_an': {'label': 'ChatGPT+ 1 an', 'price': 18.00, 'cost': 3.00}}},
    'basicfit': {'name': '🏋️ Basic-Fit', 'active': True, 'visible': True, 'category': 'fitness', 'plans': {'1_an': {'label': 'Basic-Fit Ultimate 1 an (garantie 2 mois)', 'price': 30.00, 'cost': 5.00}}},
    'fitnesspark': {'name': '💪 Fitness Park', 'active': True, 'visible': True, 'category': 'fitness', 'plans': {'1_an': {'label': 'Fitness Park 1 an', 'price': 30.00, 'cost': 5.00}}},
    'ipvanish': {'name': '🔒 IPVanish VPN', 'active': True, 'visible': True, 'category': 'vpn', 'plans': {'standard': {'label': 'IPVanish VPN', 'price': 5.00, 'cost': 1.00}}},
    'cyberghost': {'name': '👻 CyberGhost VPN', 'active': True, 'visible': True, 'category': 'vpn', 'plans': {'standard': {'label': 'CyberGhost VPN', 'price': 6.00, 'cost': 1.20}}},
    'expressvpn': {'name': '🚀 ExpressVPN', 'active': True, 'visible': True, 'category': 'vpn', 'plans': {'standard': {'label': 'ExpressVPN', 'price': 7.00, 'cost': 1.40}}},
    'nordvpn': {'name': '🛡️ NordVPN', 'active': True, 'visible': True, 'category': 'vpn', 'plans': {'standard': {'label': 'NordVPN', 'price': 8.00, 'cost': 1.60}}},
    'filmora': {'name': '🎥 Filmora Pro', 'active': True, 'visible': True, 'category': 'software', 'plans': {'standard': {'label': 'Filmora Pro', 'price': 4.00, 'cost': 0.80}}},
    'capcut': {'name': '✂️ CapCut Pro', 'active': True, 'visible': True, 'category': 'software', 'plans': {'standard': {'label': 'CapCut Pro', 'price': 4.00, 'cost': 0.80}}},
    'duolingo': {'name': '🦜 Duolingo Premium', 'active': True, 'visible': True, 'category': 'education', 'plans': {'standard': {'label': 'Duolingo Premium', 'price': 5.00, 'cost': 1.00}}},
    'appletv_music': {'name': '🍎 Apple TV + Music', 'active': True, 'visible': True, 'category': 'apple', 'plans': {'2_mois': {'label': 'Apple TV + Music 2 mois', 'price': 7.00, 'cost': 2.00}, '3_mois': {'label': 'Apple TV + Music 3 mois', 'price': 9.00, 'cost': 2.50}, '6_mois': {'label': 'Apple TV + Music 6 mois', 'price': 16.00, 'cost': 4.00}, '1_an': {'label': 'Apple TV + Music 1 an', 'price': 30.00, 'cost': 8.00}}},
}

SERVICES_CONFIG_IN_MEMORY = {}
user_states = {}

# ========== DATABASE ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, 'orders.db')
DATABASE_URL = os.getenv('DATABASE_URL') or f"sqlite:///{os.getenv('DB_PATH', DEFAULT_SQLITE_PATH)}"

connect_args = {}
if DATABASE_URL.startswith('sqlite'):
    connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, expire_on_commit=False))
Base = declarative_base()

class Service(Base):
    __tablename__ = 'services'
    service_key = Column(String, primary_key=True)
    display_name = Column(String)
    emoji = Column(String)
    category = Column(String)
    active = Column(Boolean, default=True)
    visible = Column(Boolean, default=True)
    plans = relationship("Plan", back_populates="service", cascade="all, delete-orphan")

class Plan(Base):
    __tablename__ = 'plans'
    service_key = Column(String, ForeignKey('services.service_key', ondelete='CASCADE'), primary_key=True)
    plan_key = Column(String, primary_key=True)
    label = Column(String)
    price = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    service = relationship("Service", back_populates="plans")

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    service = Column(String)
    plan = Column(String)
    price = Column(Float)
    cost = Column(Float)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    timestamp = Column(String)
    status = Column(String, default='en_attente')
    admin_id = Column(Integer, nullable=True)
    admin_username = Column(String, nullable=True)
    taken_at = Column(String, nullable=True)
    cancelled_by = Column(Integer, nullable=True)
    cancelled_at = Column(String, nullable=True)
    cancel_reason = Column(String, nullable=True)

class OrderMessage(Base):
    __tablename__ = 'order_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, index=True)
    admin_id = Column(Integer)
    message_id = Column(Integer)

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    first_seen = Column(String)
    last_activity = Column(String)
    total_orders = Column(Integer, default=0)

class CumulativeStats(Base):
    __tablename__ = 'cumulative_stats'
    id = Column(Integer, primary_key=True)
    total_revenue = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    last_updated = Column(String, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        cs = db.get(CumulativeStats, 1)
        if not cs:
            cs = CumulativeStats(id=1, total_revenue=0.0, total_profit=0.0, last_updated=datetime.now().isoformat())
            db.add(cs)
            db.commit()
        services_count = db.query(Service).count()
        if services_count == 0:
            for sk, sd in SERVICES_CONFIG.items():
                name = sd.get('name', '')
                parts = name.split(' ', 1)
                emoji = parts[0] if len(parts) > 1 else ''
                display_name = parts[1] if len(parts) > 1 else name or sk
                svc = Service(service_key=sk, display_name=display_name, emoji=emoji, category=sd.get('category', ''), active=sd.get('active', True), visible=sd.get('visible', True))
                db.add(svc)
                for pk, pd in sd.get('plans', {}).items():
                    plan = Plan(service_key=sk, plan_key=pk, label=pd.get('label', pk), price=float(pd.get('price', 0.0) or 0.0), cost=float(pd.get('cost', 0.0) or 0.0))
                    svc.plans.append(plan)
            db.commit()
        if os.getenv('OVERWRITE_DB_FROM_CONFIG', 'false').lower() in ('1', 'true', 'yes'):
            db.query(Plan).delete()
            db.query(Service).delete()
            db.commit()
            for sk, sd in SERVICES_CONFIG.items():
                name = sd.get('name', '')
                parts = name.split(' ', 1)
                emoji = parts[0] if len(parts) > 1 else ''
                display_name = parts[1] if len(parts) > 1 else name or sk
                svc = Service(service_key=sk, display_name=display_name, emoji=emoji, category=sd.get('category', ''), active=sd.get('active', True), visible=sd.get('visible', True))
                db.add(svc)
                for pk, pd in sd.get('plans', {}).items():
                    plan = Plan(service_key=sk, plan_key=pk, label=pd.get('label', pk), price=float(pd.get('price', 0.0) or 0.0), cost=float(pd.get('cost', 0.0) or 0.0))
                    svc.plans.append(plan)
            db.commit()
    except Exception as e:
        db.rollback()
        traceback.print_exc()
    finally:
        db.close()
    load_services_from_db()

def load_services_from_db():
    global SERVICES_CONFIG_IN_MEMORY
    db = SessionLocal()
    try:
        services = {}
        for s in db.query(Service).all():
            services[s.service_key] = {
                'name': f"{(s.emoji or '').strip()} {s.display_name}".strip(),
                'active': bool(s.active),
                'visible': bool(s.visible),
                'category': s.category or '',
                'plans': {}
            }
        for p in db.query(Plan).all():
            if p.service_key in services:
                services[p.service_key]['plans'][p.plan_key] = {
                    'label': p.label,
                    'price': float(p.price or 0.0),
                    'cost': float(p.cost or 0.0)
                }
        SERVICES_CONFIG_IN_MEMORY = services
        print(f"=== {len(services)} services chargés depuis DB ===")
    except Exception as e:
        traceback.print_exc()
    finally:
        db.close()

init_db()

# ========== HELPERS ==========
def update_user_activity(user_id, username, first_name, last_name):
    db = SessionLocal()
    now = datetime.now().isoformat()
    try:
        user = db.get(User, user_id)
        if user:
            user.last_activity = now
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
        else:
            user = User(user_id=user_id, username=username, first_name=first_name, last_name=last_name, first_seen=now, last_activity=now, total_orders=0)
            db.add(user)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

def delete_other_admin_notifications(order_id, keeping_admin_id):
    if not BOT_TOKEN:
        return
    db = SessionLocal()
    try:
        rows = db.query(OrderMessage).filter(OrderMessage.order_id == order_id, OrderMessage.admin_id != keeping_admin_id).all()
        for om in rows:
            try:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage", json={"chat_id": om.admin_id, "message_id": om.message_id}, timeout=10)
            except Exception:
                pass
        db.query(OrderMessage).filter(OrderMessage.order_id == order_id, OrderMessage.admin_id != keeping_admin_id).delete()
        db.commit()
    except Exception:
        pass
    finally:
        db.close()

def edit_admin_notification(order_id, admin_id, new_text):
    if not BOT_TOKEN:
        return
    db = SessionLocal()
    try:
        row = db.query(OrderMessage).filter(OrderMessage.order_id == order_id, OrderMessage.admin_id == admin_id).first()
        if row:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText", json={"chat_id": admin_id, "message_id": row.message_id, "text": new_text, "parse_mode": "Markdown"}, timeout=10)
    except Exception:
        pass
    finally:
        db.close()

def edit_all_admin_notifications(order_id, new_text):
    if not BOT_TOKEN:
        return
    db = SessionLocal()
    try:
        rows = db.query(OrderMessage).filter(OrderMessage.order_id == order_id).all()
        for om in rows:
            try:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText", json={"chat_id": om.admin_id, "message_id": om.message_id, "text": new_text, "parse_mode": "Markdown"}, timeout=10)
            except Exception:
                pass
    except Exception:
        pass
    finally:
        db.close()

def resend_order_to_all_admins(order_id):
    if not BOT_TOKEN:
        return
    db = SessionLocal()
    try:
        o = db.get(Order, order_id)
        if not o:
            return
        admin_text = f"🔔 *COMMANDE #{order_id} REMISE EN LIGNE*\n\n"
        admin_text += f"👤 @{o.username}\n" if o.username else f"👤 ID: {o.user_id}\n"
        admin_text += f"📦 {o.service}\n📋 {o.plan}\n💰 {o.price}€\n💵 Coût: {o.cost}€\n📈 Bénéf: {(o.price or 0) - (o.cost or 0)}€\n\n"
        admin_text += f"👤 {o.first_name} {o.last_name}\n📧 {o.email}\n"
        if o.payment_method:
            admin_text += f"💳 {o.payment_method}\n"
        admin_text += f"\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        keyboard = [[{"text": "✋ Prendre", "callback_data": f"admin_take_{order_id}"}, {"text": "❌ Annuler", "callback_data": f"admin_cancel_{order_id}"}]]
        for admin_id in ADMIN_IDS:
            try:
                response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": admin_id, "text": admin_text, "parse_mode": "Markdown", "reply_markup": {"inline_keyboard": keyboard}}, timeout=10)
                result = response.json()
                if result.get('ok'):
                    om = OrderMessage(order_id=order_id, admin_id=admin_id, message_id=result['result']['message_id'])
                    db.add(om)
            except Exception:
                pass
        db.commit()
    except Exception:
        pass
    finally:
        db.close()

async def resend_order_to_all_admins_async(context, order_id, service_name, plan_label, price, cost, username, user_id, first_name, last_name, email, payment_method):
    admin_text = f"🔔 *COMMANDE #{order_id} REMISE EN LIGNE*\n\n"
    admin_text += f"👤 @{username}\n" if username else f"👤 ID: {user_id}\n"
    admin_text += f"📦 {service_name}\n📋 {plan_label}\n💰 {price}€\n💵 Coût: {cost}€\n📈 Bénéf: {price - cost}€\n\n"
    admin_text += f"👤 {first_name} {last_name}\n📧 {email}\n"
    if payment_method:
        admin_text += f"💳 {payment_method}\n"
    admin_text += f"\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✋ Prendre", callback_data=f"admin_take_{order_id}"), InlineKeyboardButton("❌ Annuler", callback_data=f"admin_cancel_{order_id}")]])
    db = SessionLocal()
    try:
        for admin_id in ADMIN_IDS:
            try:
                msg = await context.bot.send_message(chat_id=admin_id, text=admin_text, parse_mode='Markdown', reply_markup=keyboard)
                db.add(OrderMessage(order_id=order_id, admin_id=admin_id, message_id=msg.message_id))
            except Exception:
                pass
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

# ========== TELEGRAM HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    update_user_activity(user.id, user.username or f"User_{user.id}", user.first_name or "Utilisateur", user.last_name or "")
    keyboard = [
        [InlineKeyboardButton("🎬 Streaming", callback_data="cat_streaming")],
        [InlineKeyboardButton("⚽ Sport", callback_data="cat_sport")],
        [InlineKeyboardButton("🎧 Musique", callback_data="cat_music")],
        [InlineKeyboardButton("🤖 IA", callback_data="cat_ai")],
        [InlineKeyboardButton("🏋️ Fitness", callback_data="cat_fitness")],
        [InlineKeyboardButton("🔒 VPN", callback_data="cat_vpn")],
        [InlineKeyboardButton("💻 Logiciels", callback_data="cat_software")],
        [InlineKeyboardButton("📚 Éducation", callback_data="cat_education")],
        [InlineKeyboardButton("🍎 Apple Services", callback_data="cat_apple")]
    ]
    welcome_text = (
        "🎯 *Bienvenue sur B4U Deals !*\n\n"
        "Profite de nos offres premium à prix réduits :\n"
        "• Comptes streaming (Netflix, Prime Video, Canal+...)\n"
        "• Sport (NBA, UFC, DAZN)\n"
        "• Abonnements musique\n"
        "• Services IA\n"
        "• Abonnements fitness\n"
        "• VPN sécurisés\n"
        "• Logiciels professionnels\n"
        "• Services Apple (TV + Music)\n\n"
        "Choisis une catégorie pour commencer :"
    )
    try:
        image_url = "https://raw.githubusercontent.com/Noallo312/serveur_express_bot/refs/heads/main/514B1CC0-791F-47CA-825C-F82A4100C02E.png"
        await update.message.reply_photo(photo=image_url, caption=welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    user_id = user.id
    username = user.username or f"User_{user_id}"
    first_name = user.first_name or "Utilisateur"
    last_name = user.last_name or ""
    update_user_activity(user_id, username, first_name, last_name)

    if data.startswith("cat_"):
        category = data.replace("cat_", "")
        keyboard = []
        for sk, sd in SERVICES_CONFIG_IN_MEMORY.items():
            if sd['active'] and sd.get('visible', True) and sd['category'] == category:
                keyboard.append([InlineKeyboardButton(sd['name'], callback_data=f"service_{sk}")])
        keyboard.append([InlineKeyboardButton("⬅️ Retour au menu", callback_data="back_to_menu")])
        cat_labels = {'streaming': '🎬 Streaming', 'sport': '⚽ Sport', 'music': '🎧 Musique', 'ai': '🤖 Intelligence Artificielle', 'fitness': '🏋️ Fitness', 'vpn': '🔒 VPN', 'software': '💻 Logiciels', 'education': '📚 Éducation', 'apple': '🍎 Apple Services'}
        await query.edit_message_caption(caption=f"*{cat_labels.get(category, category)}*\n\nChoisis ton service :", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("service_"):
        service_key = data.replace("service_", "")
        service = SERVICES_CONFIG_IN_MEMORY[service_key]
        keyboard = [[InlineKeyboardButton(f"{pd['label']} - {pd['price']}€", callback_data=f"plan_{service_key}_{pk}")] for pk, pd in service['plans'].items()]
        keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data=f"cat_{service['category']}")])
        await query.edit_message_caption(caption=f"*{service['name']}*\n\nChoisis ton abonnement :", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("plan_"):
        parts = data.replace("plan_", "").split("_")
        service_key = parts[0]
        plan_key = "_".join(parts[1:])
        service = SERVICES_CONFIG_IN_MEMORY[service_key]
        plan = service['plans'][plan_key]
        user_states[user_id] = {'service': service_key, 'plan': plan_key, 'service_name': service['name'], 'plan_label': plan['label'], 'price': plan['price'], 'cost': plan['cost'], 'step': 'waiting_payment'}
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 PayPal", callback_data=f"pay_paypal_{service_key}_{plan_key}")],
            [InlineKeyboardButton("₿ Bitcoin (BTC)", callback_data=f"pay_btc_{service_key}_{plan_key}")],
            [InlineKeyboardButton("⟠ Ethereum (ETH)", callback_data=f"pay_eth_{service_key}_{plan_key}")],
            [InlineKeyboardButton("Ł Litecoin (LTC)", callback_data=f"pay_ltc_{service_key}_{plan_key}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data=f"service_{service_key}")]
        ])
        await query.message.reply_text(f"✅ *{plan['label']} — {plan['price']}€*\n\n💳 Choisis ton mode de paiement :", parse_mode='Markdown', reply_markup=keyboard)
        return

    if data.startswith("pay_"):
        parts = data.split("_")
        method = parts[1].capitalize()
        service_key = parts[2]
        plan_key = "_".join(parts[3:])
        state = user_states.get(user_id)
        if not state:
            await query.message.reply_text("❌ Session expirée. Recommence depuis /start.")
            return
        db = SessionLocal()
        try:
            order = Order(user_id=user_id, username=username, service=state['service_name'], plan=state['plan_label'], price=state['price'], cost=state['cost'], first_name=first_name, last_name=last_name, email=None, payment_method=method, timestamp=datetime.now().isoformat(), status='en_attente')
            db.add(order)
            db.flush()
            order_id = order.id
            user_obj = db.get(User, user_id)
            if user_obj:
                user_obj.total_orders = (user_obj.total_orders or 0) + 1
            db.commit()
        except Exception as e:
            db.rollback()
            await query.message.reply_text("❌ Erreur lors de la création de la commande.")
            db.close()
            return
        finally:
            db.close()

        PAYPAL_EMAIL = os.getenv('PAYPAL_EMAIL', 'votre@paypal.com')
        BTC_WALLET = os.getenv('BTC_WALLET', '1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf4Na')
        ETH_WALLET = os.getenv('ETH_WALLET', '0x0000000000000000000000000000000000000000')
        LTC_WALLET = os.getenv('LTC_WALLET', 'LZ1DPGnXnHMHDqBqDeBiYpNqJRB3TDsGpB')

        try:
            resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,litecoin&vs_currencies=eur", timeout=5)
            prices = resp.json()
            btc_rate = prices['bitcoin']['eur']
            eth_rate = prices['ethereum']['eur']
            ltc_rate = prices['litecoin']['eur']
        except Exception:
            btc_rate, eth_rate, ltc_rate = 85000, 2000, 90

        price_eur = state['price']
        if method == 'Paypal':
            instructions = f"💳 *Paiement PayPal*\n\n📦 {state['service_name']}\n📋 {state['plan_label']}\n💰 {price_eur}€\n📌 Commande #{order_id}\n\n1️⃣ Connecte-toi à PayPal\n2️⃣ Envoie *{price_eur}€* à : `{PAYPAL_EMAIL}`\n3️⃣ ⚠️ ENVOIE EN TANT QU'AMI / PROCHE\n4️⃣ Note : `{user_id}-{order_id}`\n5️⃣ Envoie la capture ici 📸\n\n⏱️ Livraison dès validation admin"
        elif method == 'Btc':
            amt = round(price_eur / btc_rate, 8)
            instructions = f"₿ *Paiement Bitcoin (BTC)*\n\n📦 {state['service_name']}\n📋 {state['plan_label']}\n💰 {price_eur}€ = `{amt}` BTC\n📈 Taux : 1 BTC = {btc_rate:,.0f}€\n📌 Commande #{order_id}\n\nAdresse BTC :\n`{BTC_WALLET}`\n\n1️⃣ Envoie exactement `{amt}` BTC\n2️⃣ Envoie la capture ici 📸\n\n⚠️ Livraison après validation admin"
        elif method == 'Eth':
            amt = round(price_eur / eth_rate, 6)
            instructions = f"⟠ *Paiement Ethereum (ETH)*\n\n📦 {state['service_name']}\n📋 {state['plan_label']}\n💰 {price_eur}€ = `{amt}` ETH\n📈 Taux : 1 ETH = {eth_rate:,.0f}€\n📌 Commande #{order_id}\n\nAdresse ETH :\n`{ETH_WALLET}`\n\n1️⃣ Envoie exactement `{amt}` ETH\n2️⃣ Envoie la capture ici 📸\n\n⚠️ Livraison après validation admin"
        else:
            amt = round(price_eur / ltc_rate, 6)
            instructions = f"Ł *Paiement Litecoin (LTC)*\n\n📦 {state['service_name']}\n📋 {state['plan_label']}\n💰 {price_eur}€ = `{amt}` LTC\n📈 Taux : 1 LTC = {ltc_rate:,.0f}€\n📌 Commande #{order_id}\n\nAdresse LTC :\n`{LTC_WALLET}`\n\n1️⃣ Envoie exactement `{amt}` LTC\n2️⃣ Envoie la capture ici 📸\n\n⚠️ Livraison après validation admin"

        await query.message.reply_text(instructions, parse_mode='Markdown')
        user_states.pop(user_id, None)
        return

    if data == "back_to_menu":
        keyboard = [[InlineKeyboardButton("🎬 Streaming", callback_data="cat_streaming")], [InlineKeyboardButton("⚽ Sport", callback_data="cat_sport")], [InlineKeyboardButton("🎧 Musique", callback_data="cat_music")], [InlineKeyboardButton("🤖 IA", callback_data="cat_ai")], [InlineKeyboardButton("🏋️ Fitness", callback_data="cat_fitness")], [InlineKeyboardButton("🔒 VPN", callback_data="cat_vpn")], [InlineKeyboardButton("💻 Logiciels", callback_data="cat_software")], [InlineKeyboardButton("📚 Éducation", callback_data="cat_education")], [InlineKeyboardButton("🍎 Apple Services", callback_data="cat_apple")]]
        await query.edit_message_caption(caption="🎯 *B4U Deals*\n\nChoisis une catégorie :", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("admin_take_"):
        order_id = int(data.replace("admin_take_", ""))
        admin_id = query.from_user.id
        admin_username = query.from_user.username or f"Admin_{admin_id}"
        db = SessionLocal()
        try:
            order = db.get(Order, order_id)
            if not order:
                await query.answer("❌ Commande introuvable", show_alert=True); db.close(); return
            if order.status != 'en_attente':
                await query.answer("❌ Commande déjà prise", show_alert=True); db.close(); return
            order.status = 'en_cours'
            order.admin_id = admin_id
            order.admin_username = admin_username
            order.taken_at = datetime.now().isoformat()
            db.commit()
            o = order
        except Exception:
            db.rollback(); await query.answer("❌ Erreur", show_alert=True); db.close(); return
        finally:
            db.close()

        delete_other_admin_notifications(order_id, admin_id)
        taken_text = f"🔒 *COMMANDE #{order_id} — PRISE EN CHARGE*\n\n"
        taken_text += f"👤 @{o.username}\n" if o.username else f"👤 ID: {o.user_id}\n"
        taken_text += f"📦 {o.service}\n📋 {o.plan}\n💰 {o.price}€\n💵 Coût: {o.cost}€\n📈 Bénéf: {o.price - o.cost}€\n\n"
        taken_text += f"👤 {o.first_name} {o.last_name}\n📧 {o.email}\n"
        if o.payment_method:
            taken_text += f"💳 {o.payment_method}\n"
        taken_text += f"\n✅ Pris en charge par @{admin_username}\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Terminer", callback_data=f"admin_complete_{order_id}"), InlineKeyboardButton("❌ Annuler", callback_data=f"admin_cancel_{order_id}")], [InlineKeyboardButton("🔄 Remettre", callback_data=f"admin_restore_{order_id}")]])
        await query.edit_message_text(text=taken_text, parse_mode='Markdown', reply_markup=keyboard)
        await query.answer("✅ Commande prise en charge")
        return

    if data.startswith("admin_complete_"):
        order_id = int(data.replace("admin_complete_", ""))
        db = SessionLocal()
        try:
            order = db.get(Order, order_id)
            if not order:
                await query.answer("❌ Commande introuvable", show_alert=True); db.close(); return
            if order.status == 'terminee':
                await query.answer("⚠️ Commande déjà terminée", show_alert=True); db.close(); return
            price = order.price or 0.0
            cost = order.cost or 0.0
            cs = db.get(CumulativeStats, 1)
            if cs:
                cs.total_revenue = (cs.total_revenue or 0.0) + price
                cs.total_profit = (cs.total_profit or 0.0) + (price - cost)
                cs.last_updated = datetime.now().isoformat()
            order.status = 'terminee'
            db.commit()
        except Exception:
            db.rollback(); await query.answer("❌ Erreur", show_alert=True); db.close(); return
        finally:
            db.close()
        edit_all_admin_notifications(order_id, f"✅ *COMMANDE #{order_id} — TERMINÉE*\n\nTerminée par @{query.from_user.username or 'Admin'}\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        await query.answer("✅ Commande terminée")
        return

    if data.startswith("admin_cancel_"):
        order_id = int(data.replace("admin_cancel_", ""))
        db = SessionLocal()
        try:
            order = db.get(Order, order_id)
            if not order:
                await query.answer("❌ Commande introuvable", show_alert=True); db.close(); return
            order.status = 'annulee'
            order.cancelled_by = query.from_user.id
            order.cancelled_at = datetime.now().isoformat()
            db.commit()
        except Exception:
            db.rollback(); await query.answer("❌ Erreur", show_alert=True); db.close(); return
        finally:
            db.close()
        edit_all_admin_notifications(order_id, f"❌ *COMMANDE #{order_id} — ANNULÉE*\n\nAnnulée par @{query.from_user.username or 'Admin'}\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        await query.answer("❌ Commande annulée")
        return

    if data.startswith("admin_restore_"):
        order_id = int(data.replace("admin_restore_", ""))
        db = SessionLocal()
        try:
            order = db.get(Order, order_id)
            if not order:
                await query.answer("❌ Commande introuvable", show_alert=True); db.close(); return
            o = order
            order.status = 'en_attente'
            order.admin_id = None
            order.admin_username = None
            order.taken_at = None
            db.query(OrderMessage).filter(OrderMessage.order_id == order_id).delete()
            db.commit()
        except Exception:
            db.rollback(); await query.answer("❌ Erreur", show_alert=True); db.close(); return
        finally:
            db.close()
        await resend_order_to_all_admins_async(context, order_id, o.service, o.plan, o.price, o.cost, o.username, o.user_id, o.first_name, o.last_name, o.email, o.payment_method)
        await query.answer("🔄 Commande remise en ligne")
        return

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Utilise /start pour commencer une commande.")

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return
    user = update.effective_user
    user_id = user.id
    username = user.username or f"User_{user_id}"
    db = SessionLocal()
    try:
        pending_orders = db.query(Order).filter(Order.user_id == user_id, Order.status == 'en_attente').order_by(Order.id.desc()).all()
    finally:
        db.close()
    if not pending_orders:
        await update.message.reply_text("⚠️ Aucune commande en attente trouvée.\nCommence une commande avec /start avant d'envoyer ta preuve.")
        return
    order = pending_orders[0]
    recap = f"📋 *PREUVE DE PAIEMENT REÇUE*\n\n━━━━━━━━━━━━━━━━━━\n👤 Client : @{username}\n🆔 ID : {user_id}\n\n📦 {order.service}\n📋 {order.plan}\n💰 {order.price}€\n💳 {order.payment_method or 'N/A'}\n📌 Commande #{order.id}\n━━━━━━━━━━━━━━━━━━"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Valider", callback_data=f"admin_complete_{order.id}"), InlineKeyboardButton("❌ Annuler", callback_data=f"admin_cancel_{order.id}")], [InlineKeyboardButton("✋ Prendre en charge", callback_data=f"admin_take_{order.id}")]])
    db = SessionLocal()
    try:
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.forward_message(chat_id=admin_id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
                msg = await context.bot.send_message(chat_id=admin_id, text=recap, parse_mode='Markdown', reply_markup=keyboard)
                db.add(OrderMessage(order_id=order.id, admin_id=admin_id, message_id=msg.message_id))
            except Exception:
                pass
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    await update.message.reply_text(f"✅ *Preuve reçue !*\n\n📌 Commande #{order.id}\n⏱️ Un admin va valider ton paiement rapidement !", parse_mode='Markdown')

# ========== ROUTES FLASK ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == WEB_PASSWORD:
            session['logged_in'] = True
            return redirect('/')
        return render_template('login.html', error="Mot de passe incorrect")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

def check_token():
    token = request.args.get('token') or request.headers.get('X-Auth-Token')
    return token == WEB_PASSWORD

@app.route('/api/dashboard')
@login_required
def api_dashboard():
    db = SessionLocal()
    try:
        orders_q = db.query(Order).order_by(Order.id.desc()).all()
        orders = [{'id': o.id, 'username': o.username, 'service': o.service, 'plan': o.plan, 'price': o.price, 'cost': o.cost, 'first_name': o.first_name, 'last_name': o.last_name, 'email': o.email, 'payment_method': o.payment_method, 'status': o.status, 'admin_id': o.admin_id, 'admin_username': o.admin_username, 'timestamp': o.timestamp} for o in orders_q]
        total = db.query(func.count(Order.id)).scalar()
        pending = db.query(func.count(Order.id)).filter(Order.status == 'en_attente').scalar()
        inprogress = db.query(func.count(Order.id)).filter(Order.status == 'en_cours').scalar()
        completed = db.query(func.count(Order.id)).filter(Order.status == 'terminee').scalar()
        cumul = db.get(CumulativeStats, 1)
        return jsonify({'orders': orders, 'stats': {'total_orders': total, 'pending_orders': pending, 'inprogress_orders': inprogress, 'completed_orders': completed, 'revenue': cumul.total_revenue if cumul else 0, 'profit': cumul.total_profit if cumul else 0}})
    finally:
        db.close()

@app.route('/api/users')
@login_required
def api_users():
    db = SessionLocal()
    try:
        total_users = db.query(func.count(User.user_id)).scalar()
        active_users = db.query(func.count(User.user_id)).filter(User.total_orders > 0).scalar()
        conversion_rate = (active_users / total_users * 100) if total_users else 0
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        new_users = db.query(func.count(User.user_id)).filter(User.first_seen >= seven_days_ago).scalar()
        users = [{'user_id': u.user_id, 'username': u.username or 'N/A', 'first_name': u.first_name or 'Inconnu', 'last_name': u.last_name or '', 'first_seen': u.first_seen, 'last_activity': u.last_activity, 'total_orders': u.total_orders} for u in db.query(User).order_by(User.last_activity.desc()).all()]
        return jsonify({'stats': {'total_users': total_users, 'active_users': active_users, 'conversion_rate': round(conversion_rate, 1), 'new_users': new_users}, 'users': users})
    finally:
        db.close()

@app.route('/api/services', methods=['GET'])
@login_required
def api_services_list():
    services = []
    for sk, sd in SERVICES_CONFIG_IN_MEMORY.items():
        plans = [{'plan_key': pk, 'label': pd.get('label', pk), 'price': pd.get('price', 0.0), 'cost': pd.get('cost', 0.0)} for pk, pd in sd.get('plans', {}).items()]
        name_parts = sd.get('name', '').split(' ', 1)
        emoji = name_parts[0] if len(name_parts) > 1 else ''
        display_name = name_parts[1] if len(name_parts) > 1 else sd.get('name') or sk
        services.append({'service_key': sk, 'emoji': emoji, 'display_name': display_name, 'active': sd.get('active', True), 'visible': sd.get('visible', True), 'category': sd.get('category', ''), 'plans': plans})
    return jsonify({'services': services})

@app.route('/api/services', methods=['POST'])
@login_required
def api_create_service():
    data = request.get_json(force=True)
    service_key = data.get('service_key')
    if not service_key:
        return jsonify({'error': 'service_key_required'}), 400
    db = SessionLocal()
    try:
        if db.get(Service, service_key):
            return jsonify({'error': 'service_exists'}), 409
        svc = Service(service_key=service_key, display_name=data.get('display_name') or service_key, emoji=data.get('emoji') or '', category=data.get('category') or '', active=bool(data.get('active', True)), visible=bool(data.get('visible', True)))
        db.add(svc)
        db.commit()
    except Exception as e:
        db.rollback(); return jsonify({'error': str(e)}), 500
    finally:
        db.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/services/<service_key>', methods=['PUT'])
@login_required
def api_update_service(service_key):
    data = request.get_json(force=True)
    db = SessionLocal()
    try:
        svc = db.get(Service, service_key)
        if not svc:
            return jsonify({'error': 'not_found'}), 404
        svc.display_name = data.get('display_name') or ''
        svc.emoji = data.get('emoji') or ''
        svc.category = data.get('category') or ''
        svc.active = bool(data.get('active', True))
        svc.visible = bool(data.get('visible', True))
        db.commit()
    except Exception as e:
        db.rollback(); return jsonify({'error': str(e)}), 500
    finally:
        db.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/services/<service_key>', methods=['DELETE'])
@login_required
def api_delete_service(service_key):
    db = SessionLocal()
    try:
        svc = db.get(Service, service_key)
        if not svc:
            return jsonify({'error': 'not_found'}), 404
        db.delete(svc)
        db.commit()
    except Exception as e:
        db.rollback(); return jsonify({'error': str(e)}), 500
    finally:
        db.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/services/<service_key>/plans', methods=['POST'])
@login_required
def api_create_plan(service_key):
    data = request.get_json(force=True)
    plan_key = data.get('plan_key')
    if not plan_key:
        return jsonify({'error': 'plan_key_required'}), 400
    db = SessionLocal()
    try:
        if not db.get(Service, service_key):
            return jsonify({'error': 'service_not_found'}), 404
        if db.query(Plan).filter_by(service_key=service_key, plan_key=plan_key).first():
            return jsonify({'error': 'plan_exists'}), 409
        db.add(Plan(service_key=service_key, plan_key=plan_key, label=data.get('label') or plan_key, price=float(data.get('price', 0) or 0), cost=float(data.get('cost', 0) or 0)))
        db.commit()
    except Exception as e:
        db.rollback(); return jsonify({'error': str(e)}), 500
    finally:
        db.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/services/<service_key>/plans/<plan_key>', methods=['DELETE'])
@login_required
def api_delete_plan(service_key, plan_key):
    db = SessionLocal()
    try:
        plan = db.query(Plan).filter_by(service_key=service_key, plan_key=plan_key).first()
        if not plan:
            return jsonify({'error': 'not_found'}), 404
        db.delete(plan)
        db.commit()
    except Exception as e:
        db.rollback(); return jsonify({'error': str(e)}), 500
    finally:
        db.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/order/<int:order_id>/take', methods=['POST'])
@login_required
def take_order(order_id):
    db = SessionLocal()
    try:
        o = db.get(Order, order_id)
        if o:
            o.status = 'en_cours'; o.admin_id = 999999; o.admin_username = 'web_admin'; o.taken_at = datetime.now().isoformat()
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    return jsonify({'success': True})

@app.route('/api/order/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_order(order_id):
    db = SessionLocal()
    try:
        o = db.get(Order, order_id)
        if o:
            if o.status != 'terminee':
                cs = db.get(CumulativeStats, 1)
                if cs:
                    cs.total_revenue = (cs.total_revenue or 0.0) + (o.price or 0.0)
                    cs.total_profit = (cs.total_profit or 0.0) + ((o.price or 0.0) - (o.cost or 0.0))
                    cs.last_updated = datetime.now().isoformat()
            o.status = 'terminee'
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    try:
        edit_all_admin_notifications(order_id, f"✅ *COMMANDE #{order_id} — TERMINÉE*\n\nTerminée via dashboard\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    except Exception:
        pass
    return jsonify({'success': True})

@app.route('/api/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    db = SessionLocal()
    try:
        o = db.get(Order, order_id)
        if o:
            o.status = 'annulee'; o.cancelled_at = datetime.now().isoformat()
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    try:
        edit_all_admin_notifications(order_id, f"❌ *COMMANDE #{order_id} — ANNULÉE*\n\nAnnulée via dashboard\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    except Exception:
        pass
    return jsonify({'success': True})

@app.route('/api/order/<int:order_id>/restore', methods=['POST'])
@login_required
def restore_order(order_id):
    db = SessionLocal()
    try:
        o = db.get(Order, order_id)
        if o:
            o.status = 'en_attente'; o.admin_id = None; o.admin_username = None; o.taken_at = None; o.cancelled_by = None; o.cancelled_at = None
            db.query(OrderMessage).filter(OrderMessage.order_id == order_id).delete()
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    try:
        resend_order_to_all_admins(order_id)
    except Exception:
        pass
    return jsonify({'success': True})

@app.route('/api/order/<int:order_id>/send_link', methods=['POST'])
@login_required
def send_link_route(order_id):
    data = request.get_json(force=True)
    link = data.get('link', '').strip()
    if not link:
        return jsonify({'error': 'link_required'}), 400
    db = SessionLocal()
    try:
        o = db.get(Order, order_id)
        if not o:
            return jsonify({'error': 'not_found'}), 404
        user_id = o.user_id
    finally:
        db.close()
    try:
        async def _send():
            from telegram import Bot
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(chat_id=user_id, text=f"🔗 Voici votre lien :\n{link}")
        asyncio.run(_send())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'success': True})

@app.route('/api/reload_services', methods=['POST'])
@login_required
def api_reload_services():
    try:
        load_services_from_db()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== BOT TELEGRAM ==========
def run_bot():
    if not BOT_TOKEN:
        print("BOT_TOKEN non défini")
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.PHOTO, handle_payment_proof))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    print("🤖 Bot Telegram démarré")
    application.run_polling(drop_pending_updates=True, stop_signals=None)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.getenv('PORT', 10000))
    print(f"🌐 Flask démarré sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
