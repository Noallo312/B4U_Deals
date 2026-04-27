# Full app.py - Dashboard Utilisateurs + Gestion commandes Telegram + Stats cumulatives + Manager React
# MODIFICATIONS PRINCIPALES:
# - Les infos restent visibles quand on prend une commande
# - Tous les nouveaux services ajoutés et organisés par catégorie
# - Catégories: Streaming, Sport, Musique, IA, Fitness, VPN, Logiciels, Éducation

import os
import requests
import random
import traceback
import asyncio
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect, session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from functools import wraps
import threading

# SQLAlchemy imports
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Float, Boolean, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [6976573567, 5174507979]
WEB_PASSWORD = os.getenv('WEB_PASSWORD')

app = Flask(__name__)
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

# ========== SERVICES_CONFIG COMPLET - Tous les services organisés par catégorie ==========
SERVICES_CONFIG = {
    # ========== CATÉGORIE STREAMING ==========
    'netflix': {
        'name': '🎬 Netflix',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            'standard': {'label': 'Netflix Premium', 'price': 9.00, 'cost': 1.50}
        }
    },
    'primevideo': {
        'name': '🎬 Prime Video',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            '1_mois': {'label': 'Prime Video 1 mois', 'price': 5.00, 'cost': 1.50},
            '6_mois': {'label': 'Prime Video 6 mois', 'price': 15.00, 'cost': 5.00}
        }
    },
    'hbo': {
        'name': '🎬 HBO Max',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            'standard': {'label': 'HBO Max', 'price': 6.00, 'cost': 1.00}
        }
    },
    'crunchyroll': {
        'name': '🎬 Crunchyroll',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            'standard': {'label': 'Crunchyroll', 'price': 5.00, 'cost': 1.00}
        }
    },
    'canal': {
        'name': '🎬 Canal+',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            'standard': {'label': 'Canal+', 'price': 9.00, 'cost': 2.00}
        }
    },
    'disney': {
        'name': '🎬 Disney+',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            'standard': {'label': 'Disney+', 'price': 6.00, 'cost': 1.00}
        }
    },
    'youtube': {
        'name': '▶️ YouTube Premium',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            '1_mois': {'label': 'YouTube Premium 1 mois', 'price': 5.00, 'cost': 1.00},
            '1_an': {'label': 'YouTube Premium 1 an', 'price': 20.00, 'cost': 4.00}
        }
    },
    'paramount': {
        'name': '🎬 Paramount+',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            'standard': {'label': 'Paramount+', 'price': 7.00, 'cost': 1.50}
        }
    },
    'rakuten': {
        'name': '🎬 Rakuten Viki',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            'standard': {'label': 'Rakuten Viki', 'price': 7.00, 'cost': 1.50}
        }
    },
    'molotov': {
        'name': '📺 Molotov TV',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            'standard': {'label': 'Molotov TV', 'price': 9.00, 'cost': 2.00}
        }
    },
    'brazzers': {
        'name': '🔞 Brazzers',
        'active': True,
        'visible': True,
        'category': 'streaming',
        'plans': {
            'standard': {'label': 'Brazzers', 'price': 3.50, 'cost': 0.50}
        }
    },
    
    # ========== CATÉGORIE SPORT ==========
    'ufc': {
        'name': '🥊 UFC Fight Pass',
        'active': True,
        'visible': True,
        'category': 'sport',
        'plans': {
            'standard': {'label': 'UFC Fight Pass', 'price': 5.00, 'cost': 1.00}
        }
    },
    'nba': {
        'name': '🏀 NBA League Pass',
        'active': True,
        'visible': True,
        'category': 'sport',
        'plans': {
            'standard': {'label': 'NBA League Pass', 'price': 5.00, 'cost': 1.00}
        }
    },
    'dazn': {
        'name': '⚽ DAZN',
        'active': True,
        'visible': True,
        'category': 'sport',
        'plans': {
            'standard': {'label': 'DAZN', 'price': 8.00, 'cost': 1.50}
        }
    },
    
    # ========== CATÉGORIE MUSIQUE ==========
    'spotify': {
        'name': '🎧 Spotify Premium',
        'active': True,
        'visible': True,
        'category': 'music',
        'plans': {
            '2_mois': {'label': 'Spotify Premium 2 mois', 'price': 10.00, 'cost': 2.00},
            '1_an': {'label': 'Spotify Premium 1 an', 'price': 20.00, 'cost': 4.00}
        }
    },
    'deezer': {
        'name': '🎵 Deezer Premium',
        'active': True,
        'visible': True,
        'category': 'music',
        'plans': {
            'a_vie': {'label': 'Deezer Premium à vie', 'price': 8.00, 'cost': 1.50}
        }
    },
    
    # ========== CATÉGORIE IA ==========
    'chatgpt': {
        'name': '🤖 ChatGPT+',
        'active': True,
        'visible': True,
        'category': 'ai',
        'plans': {
            '1_mois': {'label': 'ChatGPT+ 1 mois', 'price': 5.00, 'cost': 1.00},
            '1_an': {'label': 'ChatGPT+ 1 an', 'price': 18.00, 'cost': 3.00}
        }
    },
    
    # ========== CATÉGORIE FITNESS ==========
    'basicfit': {
        'name': '🏋️ Basic-Fit',
        'active': True,
        'visible': True,
        'category': 'fitness',
        'plans': {
            '1_an': {'label': 'Basic-Fit Ultimate 1 an (garantie 2 mois)', 'price': 30.00, 'cost': 5.00}
        }
    },
    'fitnesspark': {
        'name': '💪 Fitness Park',
        'active': True,
        'visible': True,
        'category': 'fitness',
        'plans': {
            '1_an': {'label': 'Fitness Park 1 an', 'price': 30.00, 'cost': 5.00}
        }
    },
    
    # ========== CATÉGORIE VPN ==========
    'ipvanish': {
        'name': '🔒 IPVanish VPN',
        'active': True,
        'visible': True,
        'category': 'vpn',
        'plans': {
            'standard': {'label': 'IPVanish VPN', 'price': 5.00, 'cost': 1.00}
        }
    },
    'cyberghost': {
        'name': '👻 CyberGhost VPN',
        'active': True,
        'visible': True,
        'category': 'vpn',
        'plans': {
            'standard': {'label': 'CyberGhost VPN', 'price': 6.00, 'cost': 1.20}
        }
    },
    'expressvpn': {
        'name': '🚀 ExpressVPN',
        'active': True,
        'visible': True,
        'category': 'vpn',
        'plans': {
            'standard': {'label': 'ExpressVPN', 'price': 7.00, 'cost': 1.40}
        }
    },
    'nordvpn': {
        'name': '🛡️ NordVPN',
        'active': True,
        'visible': True,
        'category': 'vpn',
        'plans': {
            'standard': {'label': 'NordVPN', 'price': 8.00, 'cost': 1.60}
        }
    },
    
    # ========== CATÉGORIE LOGICIELS ==========
    'filmora': {
        'name': '🎥 Filmora Pro',
        'active': True,
        'visible': True,
        'category': 'software',
        'plans': {
            'standard': {'label': 'Filmora Pro', 'price': 4.00, 'cost': 0.80}
        }
    },
    'capcut': {
        'name': '✂️ CapCut Pro',
        'active': True,
        'visible': True,
        'category': 'software',
        'plans': {
            'standard': {'label': 'CapCut Pro', 'price': 4.00, 'cost': 0.80}
        }
    },
    
    # ========== CATÉGORIE ÉDUCATION ==========
    'duolingo': {
        'name': '🦜 Duolingo Premium',
        'active': True,
        'visible': True,
        'category': 'education',
        'plans': {
            'standard': {'label': 'Duolingo Premium', 'price': 5.00, 'cost': 1.00}
        }
    },
    
    # ========== CATÉGORIE APPLE ==========
    'appletv_music': {
        'name': '🍎 Apple TV + Music',
        'active': True,
        'visible': True,
        'category': 'apple',
        'plans': {
            '2_mois': {'label': 'Apple TV + Music 2 mois', 'price': 7.00, 'cost': 2.00},
            '3_mois': {'label': 'Apple TV + Music 3 mois', 'price': 9.00, 'cost': 2.50},
            '6_mois': {'label': 'Apple TV + Music 6 mois', 'price': 16.00, 'cost': 4.00},
            '1_an': {'label': 'Apple TV + Music 1 an', 'price': 30.00, 'cost': 8.00}
        }
    }
}
SERVICES_CONFIG_IN_MEMORY = {}
user_states = {}
HTML_LOGIN = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - B4U Deals</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
        }
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 30px;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🎯 B4U Deals Admin</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="Mot de passe" required>
            <button type="submit">Se connecter</button>
        </form>
    </div>
</body>
</html>
'''

HTML_DASHBOARD = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - B4U Deals</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header-actions {
            display: flex;
            gap: 10px;
        }
        .header-actions a, .header-actions button {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            text-decoration: none;
            cursor: pointer;
        }
        .container {
            max-width: 1400px;
            margin: 20px auto;
            padding: 0 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            border-left: 5px solid #667eea;
        }
        .stat-card h3 {
            color: #666;
            font-size: 13px;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        .orders-section {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .order-card {
            background: #f9fafb;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 15px;
            border-left: 5px solid #ddd;
        }
        .order-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .action-btn {
            padding: 10px 18px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            color: white;
        }
        .btn-take { background: #3b82f6; }
        .btn-complete { background: #10b981; }
        .btn-cancel { background: #ef4444; }
        .btn-restore { background: #f59e0b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 B4U Deals - Dashboard</h1>
        <div class="header-actions">
            <a href="/manager">🎛️ Manager</a>
            <a href="/users">👥 Utilisateurs</a>
            <a href="/simulate">🎲 Simuler</a>
            <a href="/logout">Déconnexion</a>
        </div>
    </div>
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📦 Total Commandes</h3>
                <div class="value" id="total-orders">0</div>
            </div>
            <div class="stat-card">
                <h3>⏳ En Attente</h3>
                <div class="value" id="pending-orders">0</div>
            </div>
            <div class="stat-card">
                <h3>💰 CA Total</h3>
                <div class="value" id="revenue">0€</div>
            </div>
            <div class="stat-card">
                <h3>💵 Bénéfice Total</h3>
                <div class="value" id="profit">0€</div>
            </div>
        </div>
        <div class="orders-section">
            <h2>📋 Commandes</h2>
            <div id="orders-container"></div>
        </div>
    </div>
    <script>
        async function loadData() {
            const response = await fetch('/api/dashboard');
            const data = await response.json();
            document.getElementById('total-orders').textContent = data.stats.total_orders;
            document.getElementById('pending-orders').textContent = data.stats.pending_orders;
            document.getElementById('revenue').textContent = data.stats.revenue.toFixed(0) + '€';
            document.getElementById('profit').textContent = data.stats.profit.toFixed(0) + '€';
            displayOrders(data.orders);
        }
        function displayOrders(orders) {
            const container = document.getElementById('orders-container');
            if (orders.length === 0) {
                container.innerHTML = '<p>Aucune commande</p>';
                return;
            }
            container.innerHTML = orders.slice(0, 20).map(o => `
                <div class="order-card">
                    <strong>#${o.id}</strong> - ${o.service} - ${o.price}€<br>
                    <small>${o.first_name} ${o.last_name} - ${o.email}</small><br>
                    <span>Statut: ${o.status}</span>
                    <div class="order-actions">
                        ${o.status === 'en_attente' ? `<button class="action-btn btn-take" onclick="takeOrder(${o.id})">Prendre</button>` : ''}
                        ${o.status === 'en_cours' ? `<button class="action-btn btn-complete" onclick="completeOrder(${o.id})">Terminer</button>` : ''}
                        <button class="action-btn btn-cancel" onclick="cancelOrder(${o.id})">Annuler</button>
                    </div>
                </div>
            `).join('');
        }
        async function takeOrder(id) {
            await fetch('/api/order/' + id + '/take', {method: 'POST'});
            loadData();
        }
        async function completeOrder(id) {
            await fetch('/api/order/' + id + '/complete', {method: 'POST'});
            loadData();
        }
        async function cancelOrder(id) {
            await fetch('/api/order/' + id + '/cancel', {method: 'POST'});
            loadData();
        }
        loadData();
        setInterval(loadData, 15000);
    </script>
</body>
</html>
'''

HTML_USERS = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Utilisateurs - B4U Deals</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
        }
        .container {
            max-width: 1400px;
            margin: 20px auto;
            background: white;
            padding: 25px;
            border-radius: 15px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f9fafb;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>👥 Utilisateurs</h1>
        <a href="/dashboard" style="color:white;text-decoration:none">← Dashboard</a>
    </div>
    <div class="container">
        <h2>Liste des Utilisateurs</h2>
        <table id="usersTable">
            <thead>
                <tr>
                    <th>Utilisateur</th>
                    <th>Telegram</th>
                    <th>Commandes</th>
                    <th>Première visite</th>
                </tr>
            </thead>
            <tbody id="users-body"></tbody>
        </table>
    </div>
    <script>
        async function loadUsers() {
            const response = await fetch('/api/users');
            const data = await response.json();
            const tbody = document.getElementById('users-body');
            tbody.innerHTML = data.users.map(u => `
                <tr>
                    <td><strong>${u.first_name} ${u.last_name}</strong></td>
                    <td>@${u.username}</td>
                    <td><strong>${u.total_orders}</strong></td>
                    <td>${new Date(u.first_seen).toLocaleDateString()}</td>
                </tr>
            `).join('');
        }
        loadUsers();
    </script>
</body>
</html>
'''

HTML_REACT_MANAGER = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Manager - B4U Deals</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 16px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            margin-bottom: 12px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
        }
        input {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 6px;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎛️ Bot Manager</h1>
        <a href="/dashboard" style="color:white">← Dashboard</a>
    </div>
    <div id="content">
        <div class="card">
            <h2>Gestion des Services</h2>
            <p>Utilisez l'API pour gérer les services</p>
            <button onclick="location.reload()">Recharger</button>
        </div>
    </div>
</body>
</html>
'''

# DB config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, 'orders.db')
DATABASE_URL = os.getenv('DATABASE_URL') or f"sqlite:///{os.getenv('DB_PATH', DEFAULT_SQLITE_PATH)}"

connect_args = {}
if DATABASE_URL.startswith('sqlite'):
    connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, expire_on_commit=False))
Base = declarative_base()
# Models SQLAlchemy
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
    user_id = Column(BigInteger, nullable=True)
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
    admin_id = Column(BigInteger, nullable=True)
    admin_username = Column(String, nullable=True)
    taken_at = Column(String, nullable=True)
    cancelled_by = Column(BigInteger, nullable=True)
    cancelled_at = Column(String, nullable=True)
    cancel_reason = Column(String, nullable=True)

class OrderMessage(Base):
    __tablename__ = 'order_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, index=True)
    admin_id = Column(BigInteger)
    message_id = Column(Integer)

class User(Base):
    __tablename__ = 'users'
    user_id = Column(BigInteger, primary_key=True)
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

# Initialisation de la DB
def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        cs = session.get(CumulativeStats, 1)
        if not cs:
            cs = CumulativeStats(id=1, total_revenue=0.0, total_profit=0.0, last_updated=datetime.now().isoformat())
            session.add(cs)
            session.commit()

        services_count = session.query(Service).count()
        if services_count == 0:
            for sk, sd in SERVICES_CONFIG.items():
                name = sd.get('name', '')
                parts = name.split(' ', 1)
                emoji = parts[0] if len(parts) > 1 else ''
                display_name = parts[1] if len(parts) > 1 else name or sk
                svc = Service(service_key=sk, display_name=display_name, emoji=emoji, category=sd.get('category', ''), active=sd.get('active', True), visible=sd.get('visible', True))
                session.add(svc)
                for pk, pd in sd.get('plans', {}).items():
                    plan = Plan(service_key=sk, plan_key=pk, label=pd.get('label', pk), price=float(pd.get('price', 0.0) or 0.0), cost=float(pd.get('cost', 0.0) or 0.0))
                    svc.plans.append(plan)
            session.commit()

        if os.getenv('OVERWRITE_DB_FROM_CONFIG', 'false').lower() in ('1', 'true', 'yes'):
            session.query(Plan).delete()
            session.query(Service).delete()
            session.commit()
            for sk, sd in SERVICES_CONFIG.items():
                name = sd.get('name', '')
                parts = name.split(' ', 1)
                emoji = parts[0] if len(parts) > 1 else ''
                display_name = parts[1] if len(parts) > 1 else name or sk
                svc = Service(service_key=sk, display_name=display_name, emoji=emoji, category=sd.get('category', ''), active=sd.get('active', True), visible=sd.get('visible', True))
                session.add(svc)
                for pk, pd in sd.get('plans', {}).items():
                    plan = Plan(service_key=sk, plan_key=pk, label=pd.get('label', pk), price=float(pd.get('price', 0.0) or 0.0), cost=float(pd.get('cost', 0.0) or 0.0))
                    svc.plans.append(plan)
            session.commit()
            print("DB overwritten from SERVICES_CONFIG (OVERWRITE_DB_FROM_CONFIG enabled).")

    except Exception as e:
        session.rollback()
        print("init_db error:", e)
        traceback.print_exc()
    finally:
        session.close()
    load_services_from_db()

def load_services_from_db():
    global SERVICES_CONFIG_IN_MEMORY
    session = SessionLocal()
    try:
        services = {}
        svc_rows = session.query(Service).all()
        for s in svc_rows:
            services[s.service_key] = {
                'name': f"{(s.emoji or '').strip()} {s.display_name}".strip(),
                'active': bool(s.active),
                'visible': bool(s.visible),
                'category': s.category or '',
                'plans': {}
            }
        plan_rows = session.query(Plan).all()
        for p in plan_rows:
            if p.service_key not in services:
                continue
            services[p.service_key]['plans'][p.plan_key] = {
                'label': p.label,
                'price': float(p.price or 0.0),
                'cost': float(p.cost or 0.0)
            }
        SERVICES_CONFIG_IN_MEMORY = services
        print(f"=== Loaded {len(services)} services from DB ===")
    except Exception as e:
        print("Erreur load_services_from_db:", e)
        traceback.print_exc()
    finally:
        session.close()

init_db()

# Helper functions
def update_user_activity(user_id, username, first_name, last_name):
    session = SessionLocal()
    now = datetime.now().isoformat()
    try:
        user = session.get(User, user_id)
        if user:
            user.last_activity = now
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
        else:
            user = User(user_id=user_id, username=username, first_name=first_name, last_name=last_name, first_seen=now, last_activity=now, total_orders=0)
            session.add(user)
        session.commit()
    except Exception as e:
        session.rollback()
        print("update_user_activity error:", e)
    finally:
        session.close()

def delete_other_admin_notifications(order_id: int, keeping_admin_id: int):
    if not BOT_TOKEN:
        return
    session = SessionLocal()
    try:
        rows = session.query(OrderMessage).filter(OrderMessage.order_id == order_id, OrderMessage.admin_id != keeping_admin_id).all()
        for om in rows:
            try:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage", json={"chat_id": om.admin_id, "message_id": om.message_id}, timeout=10)
            except Exception as e:
                print(f"[delete_message] Erreur admin {om.admin_id} msg {om.message_id}: {e}")
        session.query(OrderMessage).filter(OrderMessage.order_id == order_id, OrderMessage.admin_id != keeping_admin_id).delete()
        session.commit()
    except Exception as e:
        print("Erreur delete_other_admin_notifications:", e)
    finally:
        session.close()

def edit_admin_notification(order_id: int, admin_id: int, new_text: str):
    if not BOT_TOKEN:
        return
    session = SessionLocal()
    try:
        row = session.query(OrderMessage).filter(OrderMessage.order_id == order_id, OrderMessage.admin_id == admin_id).first()
        if row:
            try:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText", json={"chat_id": admin_id, "message_id": row.message_id, "text": new_text, "parse_mode": "Markdown"}, timeout=10)
            except Exception as e:
                print(f"[edit_message] Erreur admin {admin_id} msg {row.message_id}: {e}")
    except Exception as e:
        print("Erreur edit_admin_notification:", e)
    finally:
        session.close()

def edit_all_admin_notifications(order_id: int, new_text: str):
    if not BOT_TOKEN:
        return
    session = SessionLocal()
    try:
        rows = session.query(OrderMessage).filter(OrderMessage.order_id == order_id).all()
        for om in rows:
            try:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText", json={"chat_id": om.admin_id, "message_id": om.message_id, "text": new_text, "parse_mode": "Markdown"}, timeout=10)
            except Exception as e:
                print(f"[edit_message] Erreur admin {om.admin_id} msg {om.message_id}: {e}")
    except Exception as e:
        print("Erreur edit_all_admin_notifications:", e)
    finally:
        session.close()

def resend_order_to_all_admins(order_id: int):
    if not BOT_TOKEN:
        return
    session = SessionLocal()
    try:
        o = session.get(Order, order_id)
        if not o:
            return
        admin_text = f"🔔 *COMMANDE #{order_id} REMISE EN LIGNE*\n\n"
        if o.username:
            admin_text += f"👤 @{o.username}\n"
        else:
            admin_text += f"👤 ID: {o.user_id}\n"
        admin_text += (f"📦 {o.service}\n" f"📋 {o.plan}\n" f"💰 {o.price}€\n" f"💵 Coût: {o.cost}€\n" f"📈 Bénéf: {(o.price or 0) - (o.cost or 0)}€\n\n" f"👤 {o.first_name} {o.last_name}\n" f"📧 {o.email}\n")
        if o.payment_method:
            admin_text += f"💳 {o.payment_method}\n"
        admin_text += f"\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"

        keyboard = [[{"text": "✋ Prendre", "callback_data": f"admin_take_{order_id}"}, {"text": "❌ Annuler", "callback_data": f"admin_cancel_{order_id}"}]]
        for admin_id in ADMIN_IDS:
            try:
                response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": admin_id, "text": admin_text, "parse_mode": "Markdown", "reply_markup": {"inline_keyboard": keyboard}}, timeout=10)
                result = response.json()
                if result.get('ok'):
                    message_id = result['result']['message_id']
                    om = OrderMessage(order_id=order_id, admin_id=admin_id, message_id=message_id)
                    session.add(om)
            except Exception as e:
                print(f"Erreur envoi admin {admin_id}: {e}")
        session.commit()
    except Exception as e:
        print("Erreur resend_order_to_all_admins:", e)
    finally:
        session.close()

async def resend_order_to_all_admins_async(context, order_id, service_name, plan_label, price, cost, username, user_id, first_name, last_name, email, payment_method):
    admin_text = f"🔔 *COMMANDE #{order_id} REMISE EN LIGNE*\n\n"
    if username:
        admin_text += f"👤 @{username}\n"
    else:
        admin_text += f"👤 ID: {user_id}\n"
    admin_text += (f"📦 {service_name}\n" f"📋 {plan_label}\n" f"💰 {price}€\n" f"💵 Coût: {cost}€\n" f"📈 Bénéf: {price - cost}€\n\n" f"👤 {first_name} {last_name}\n" f"📧 {email}\n")
    if payment_method:
        admin_text += f"💳 {payment_method}\n"
    admin_text += f"\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✋ Prendre", callback_data=f"admin_take_{order_id}"), InlineKeyboardButton("❌ Annuler", callback_data=f"admin_cancel_{order_id}")]])
    session = SessionLocal()
    try:
        for admin_id in ADMIN_IDS:
            try:
                msg = await context.bot.send_message(chat_id=admin_id, text=admin_text, parse_mode='Markdown', reply_markup=keyboard)
                om = OrderMessage(order_id=order_id, admin_id=admin_id, message_id=msg.message_id)
                session.add(om)
            except Exception as e:
                print(f"Erreur envoi admin {admin_id}: {e}")
        session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()
# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"User_{user_id}"
    first_name = update.message.from_user.first_name or "Utilisateur"
    last_name = update.message.from_user.last_name or ""
    update_user_activity(user_id, username, first_name, last_name)
    
    # Menu principal avec TOUTES les catégories (9 au total)
    keyboard = [
        [InlineKeyboardButton("🎬 Streaming", callback_data="cat_streaming")],
        [InlineKeyboardButton("⚽ Sport", callback_data="cat_sport")],
        [InlineKeyboardButton("🎧 Musique", callback_data="cat_music")],
        [InlineKeyboardButton("🤖 IA", callback_data="cat_ai")],
        [InlineKeyboardButton("🏋️ Fitness", callback_data="cat_fitness")],
        [InlineKeyboardButton("🔒 VPN", callback_data="cat_vpn")],
        [InlineKeyboardButton("💻 Logiciels", callback_data="cat_software")],
        [InlineKeyboardButton("📚 Éducation", callback_data="cat_education")],
        [InlineKeyboardButton("🍎 Apple Services", callback_data="cat_apple")]  # ✅ AJOUTÉ
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
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
        "• Formations\n"
        "• Services Apple (TV + Music)\n\n"  # ✅ AJOUTÉ
        "Choisis une catégorie pour commencer :"
    )
    
    try:
        image_url = "https://raw.githubusercontent.com/Noallo312/serveur_express_bot/refs/heads/main/514B1CC0-791F-47CA-825C-F82A4100C02E.png"
        await update.message.reply_photo(photo=image_url, caption=welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
    except Exception as e:
        print(f"Erreur chargement image: {e}")
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or f"User_{user_id}"
    first_name = query.from_user.first_name or "Utilisateur"
    last_name = query.from_user.last_name or ""
    update_user_activity(user_id, username, first_name, last_name)

    # Gestion des catégories
    if data.startswith("cat_"):
        category = data.replace("cat_", "")
        keyboard = []
        for service_key, service_data in SERVICES_CONFIG_IN_MEMORY.items():
            if service_data['active'] and service_data.get('visible', True) and service_data['category'] == category:
                keyboard.append([InlineKeyboardButton(service_data['name'], callback_data=f"service_{service_key}")])
        keyboard.append([InlineKeyboardButton("⬅️ Retour au menu", callback_data="back_to_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        category_labels = {
            'streaming': '🎬 Streaming',
            'sport': '⚽ Sport',
            'music': '🎧 Musique',
            'ai': '🤖 Intelligence Artificielle',
            'fitness': '🏋️ Fitness',
            'vpn': '🔒 VPN',
            'software': '💻 Logiciels',
            'education': '📚 Éducation',
            'apple': '🍎 Apple Services'  # ✅ AJOUTÉ
        }
        
        await query.edit_message_caption(caption=f"*{category_labels.get(category, category)}*\n\nChoisis ton service :", parse_mode='Markdown', reply_markup=reply_markup)
        return

    # Gestion des services
    if data.startswith("service_"):
        service_key = data.replace("service_", "")
        service = SERVICES_CONFIG_IN_MEMORY[service_key]
        keyboard = []
        for plan_key, plan_data in service['plans'].items():
            keyboard.append([InlineKeyboardButton(f"{plan_data['label']} - {plan_data['price']}€", callback_data=f"plan_{service_key}_{plan_key}")])
        keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data=f"cat_{service['category']}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_caption(caption=f"*{service['name']}*\n\nChoisis ton abonnement :", parse_mode='Markdown', reply_markup=reply_markup)
        return

    # Gestion des plans
    if data.startswith("plan_"):
        parts = data.replace("plan_", "").split("_")
        service_key = parts[0]
        plan_key = "_".join(parts[1:])
        service = SERVICES_CONFIG_IN_MEMORY[service_key]
        plan = service['plans'][plan_key]
        user_states[user_id] = {
            'service': service_key, 'plan': plan_key,
            'service_name': service['name'], 'plan_label': plan['label'],
            'price': plan['price'], 'cost': plan['cost'],
            'step': 'waiting_payment'
        }
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 PayPal", callback_data=f"pay_paypal_{service_key}_{plan_key}")],
            [InlineKeyboardButton("₿ Bitcoin (BTC)", callback_data=f"pay_btc_{service_key}_{plan_key}")],
            [InlineKeyboardButton("⟠ Ethereum (ETH)", callback_data=f"pay_eth_{service_key}_{plan_key}")],
            [InlineKeyboardButton("Ł Litecoin (LTC)", callback_data=f"pay_ltc_{service_key}_{plan_key}")],
            [InlineKeyboardButton("⬅️ Retour", callback_data=f"service_{service_key}")]
        ])
        await query.message.reply_text(
            f"✅ *{plan['label']} — {plan['price']}€*\n\n💳 Choisis ton mode de paiement :",
            parse_mode='Markdown', reply_markup=keyboard
        )
        return

    # Gestion du paiement choisi
    if data.startswith("pay_"):
        parts = data.split("_")
        method = parts[1].capitalize()  # paypal, virement, revolut
        service_key = parts[2]
        plan_key = "_".join(parts[3:])
        state = user_states.get(user_id)
        if not state:
            await query.message.reply_text("❌ Session expirée. Recommence depuis /start.")
            return

        # Créer la commande en DB
        session = SessionLocal()
        try:
            order = Order(
                user_id=user_id,
                username=username,
                service=state['service_name'],
                plan=state['plan_label'],
                price=state['price'],
                cost=state['cost'],
                first_name=first_name,
                last_name=last_name,
                email=None,
                payment_method=method,
                timestamp=datetime.now().isoformat(),
                status='en_attente'
            )
            session.add(order)
            session.flush()
            order_id = order.id
            user_obj = session.get(User, user_id)
            if user_obj:
                user_obj.total_orders = (user_obj.total_orders or 0) + 1
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur création commande: {e}")
            await query.message.reply_text("❌ Erreur lors de la création de la commande.")
            session.close()
            return
        finally:
            session.close()

        # Instructions selon mode de paiement
        PAYPAL_EMAIL = os.getenv('PAYPAL_EMAIL', 'votre@paypal.com')
        BTC_WALLET = os.getenv('BTC_WALLET', '1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf4Na')
        ETH_WALLET = os.getenv('ETH_WALLET', '0x0000000000000000000000000000000000000000')
        LTC_WALLET = os.getenv('LTC_WALLET', 'LZ1DPGnXnHMHDqBqDeBiYpNqJRB3TDsGpB')

        # Récupération des taux crypto en temps réel
        try:
            import requests as _req
            resp = _req.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,litecoin&vs_currencies=eur",
                timeout=5
            )
            prices = resp.json()
            btc_rate = prices['bitcoin']['eur']
            eth_rate = prices['ethereum']['eur']
            ltc_rate = prices['litecoin']['eur']
        except Exception:
            btc_rate, eth_rate, ltc_rate = 85000, 2000, 90

        price_eur = state['price']

        if method == 'Paypal':
            instructions = (
                f"💳 *Paiement PayPal*\n\n"
                f"📦 {state['service_name']}\n"
                f"📋 {state['plan_label']}\n"
                f"💰 {price_eur}€\n"
                f"📌 Commande #{order_id}\n\n"
                f"1️⃣ Connecte-toi à PayPal\n"
                f"2️⃣ Envoie *{price_eur}€* à : `{PAYPAL_EMAIL}`\n"
                f"3️⃣ ⚠️ ENVOIE EN TANT QU'AMI / PROCHE\n"
                f"4️⃣ Note : `{user_id}-{order_id}`\n"
                f"5️⃣ Envoie la capture ici 📸\n\n"
                f"⏱️ Livraison dès validation admin"
            )
        elif method == 'Btc':
            amt = round(price_eur / btc_rate, 8)
            instructions = (
                f"₿ *Paiement Bitcoin (BTC)*\n\n"
                f"📦 {state['service_name']}\n"
                f"📋 {state['plan_label']}\n"
                f"💰 {price_eur}€ = `{amt}` BTC\n"
                f"📈 Taux : 1 BTC = {btc_rate:,.0f}€\n"
                f"📌 Commande #{order_id}\n\n"
                f"Adresse BTC :\n`{BTC_WALLET}`\n\n"
                f"1️⃣ Envoie exactement `{amt}` BTC\n"
                f"2️⃣ Envoie la capture ici 📸\n\n"
                f"⚠️ Livraison après validation admin"
            )
        elif method == 'Eth':
            amt = round(price_eur / eth_rate, 6)
            instructions = (
                f"⟠ *Paiement Ethereum (ETH)*\n\n"
                f"📦 {state['service_name']}\n"
                f"📋 {state['plan_label']}\n"
                f"💰 {price_eur}€ = `{amt}` ETH\n"
                f"📈 Taux : 1 ETH = {eth_rate:,.0f}€\n"
                f"📌 Commande #{order_id}\n\n"
                f"Adresse ETH :\n`{ETH_WALLET}`\n\n"
                f"1️⃣ Envoie exactement `{amt}` ETH\n"
                f"2️⃣ Envoie la capture ici 📸\n\n"
                f"⚠️ Livraison après validation admin"
            )
        else:  # Ltc
            amt = round(price_eur / ltc_rate, 6)
            instructions = (
                f"Ł *Paiement Litecoin (LTC)*\n\n"
                f"📦 {state['service_name']}\n"
                f"📋 {state['plan_label']}\n"
                f"💰 {price_eur}€ = `{amt}` LTC\n"
                f"📈 Taux : 1 LTC = {ltc_rate:,.0f}€\n"
                f"📌 Commande #{order_id}\n\n"
                f"Adresse LTC :\n`{LTC_WALLET}`\n\n"
                f"1️⃣ Envoie exactement `{amt}` LTC\n"
                f"2️⃣ Envoie la capture ici 📸\n\n"
                f"⚠️ Livraison après validation admin"
            )

        await query.message.reply_text(instructions, parse_mode='Markdown')
        user_states.pop(user_id, None)
        return

    # Retour au menu
    if data == "back_to_menu":
        keyboard = [
            [InlineKeyboardButton("🎬 Streaming", callback_data="cat_streaming")],
            [InlineKeyboardButton("⚽ Sport", callback_data="cat_sport")],
            [InlineKeyboardButton("🎧 Musique", callback_data="cat_music")],
            [InlineKeyboardButton("🤖 IA", callback_data="cat_ai")],
            [InlineKeyboardButton("🏋️ Fitness", callback_data="cat_fitness")],
            [InlineKeyboardButton("🔒 VPN", callback_data="cat_vpn")],
            [InlineKeyboardButton("💻 Logiciels", callback_data="cat_software")],
            [InlineKeyboardButton("📚 Éducation", callback_data="cat_education")],
            [InlineKeyboardButton("🍎 Apple Services", callback_data="cat_apple")]  # ✅ AJOUTÉ
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_caption(caption="🎯 *B4U Deals*\n\nChoisis une catégorie :", parse_mode='Markdown', reply_markup=reply_markup)
        return

    # ========== ADMIN PREND LA COMMANDE ==========
    if data.startswith("admin_take_"):
        order_id = int(data.replace("admin_take_", ""))
        admin_id = query.from_user.id
        admin_username = query.from_user.username or f"Admin_{admin_id}"
        
        session = SessionLocal()
        try:
            order = session.get(Order, order_id)
            if not order:
                await query.answer("❌ Commande introuvable", show_alert=True)
                session.close()
                return
            
            if order.status != 'en_attente':
                await query.answer("❌ Commande déjà prise", show_alert=True)
                session.close()
                return
            
            # Mettre à jour la commande
            order.status = 'en_cours'
            order.admin_id = admin_id
            order.admin_username = admin_username
            order.taken_at = datetime.now().isoformat()
            session.commit()
            
            # Récupérer toutes les infos pour le nouveau message
            service_name = order.service
            plan_label = order.plan
            price = order.price
            cost = order.cost
            username_order = order.username
            user_id_order = order.user_id
            first_name_order = order.first_name
            last_name_order = order.last_name
            email_order = order.email
            payment_method_order = order.payment_method
            
        except Exception as e:
            session.rollback()
            print(f"Erreur prise commande: {e}")
            await query.answer("❌ Erreur", show_alert=True)
            session.close()
            return
        finally:
            session.close()
        
        # Supprimer les notifications des autres admins
        delete_other_admin_notifications(order_id, admin_id)
        
        # Modifier le message de l'admin qui a pris - AVEC TOUTES LES INFOS
        taken_text = f"🔒 *COMMANDE #{order_id} — PRISE EN CHARGE*\n\n"
        if username_order:
            taken_text += f"👤 @{username_order}\n"
        else:
            taken_text += f"👤 ID: {user_id_order}\n"
        taken_text += (
            f"📦 {service_name}\n"
            f"📋 {plan_label}\n"
            f"💰 {price}€\n"
            f"💵 Coût: {cost}€\n"
            f"📈 Bénéf: {price - cost}€\n\n"
            f"👤 {first_name_order} {last_name_order}\n"
            f"📧 {email_order}\n"
        )
        if payment_method_order:
            taken_text += f"💳 {payment_method_order}\n"
        taken_text += f"\n✅ Pris en charge par @{admin_username}\n"
        taken_text += f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Terminer", callback_data=f"admin_complete_{order_id}"),
                InlineKeyboardButton("❌ Annuler", callback_data=f"admin_cancel_{order_id}")
            ],
            [
                InlineKeyboardButton("🔄 Remettre", callback_data=f"admin_restore_{order_id}")
            ]
        ])
        
        await query.edit_message_text(text=taken_text, parse_mode='Markdown', reply_markup=keyboard)
        await query.answer("✅ Commande prise en charge")
        return
    
    # ========== ADMIN TERMINE LA COMMANDE ==========
    if data.startswith("admin_complete_"):
        order_id = int(data.replace("admin_complete_", ""))
        
        session = SessionLocal()
        try:
            order = session.get(Order, order_id)
            if not order:
                await query.answer("❌ Commande introuvable", show_alert=True)
                session.close()
                return
            
            price = order.price or 0.0
            cost = order.cost or 0.0
            
            # Mettre à jour les stats cumulatives
            cs = session.get(CumulativeStats, 1)
            if cs:
                cs.total_revenue = (cs.total_revenue or 0.0) + price
                cs.total_profit = (cs.total_profit or 0.0) + (price - cost)
                cs.last_updated = datetime.now().isoformat()
            
            order.status = 'terminee'
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur terminer commande: {e}")
            await query.answer("❌ Erreur", show_alert=True)
            session.close()
            return
        finally:
            session.close()
        
        # Modifier tous les messages admin
        completed_text = (
            f"✅ *COMMANDE #{order_id} — TERMINÉE*\n\n"
            f"Terminée par @{query.from_user.username or 'Admin'}\n"
            f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        
        edit_all_admin_notifications(order_id, completed_text)
        await query.answer("✅ Commande terminée")
        return
    
    # ========== ADMIN ANNULE LA COMMANDE ==========
    if data.startswith("admin_cancel_"):
        order_id = int(data.replace("admin_cancel_", ""))
        
        session = SessionLocal()
        try:
            order = session.get(Order, order_id)
            if not order:
                await query.answer("❌ Commande introuvable", show_alert=True)
                session.close()
                return
            
            order.status = 'annulee'
            order.cancelled_by = query.from_user.id
            order.cancelled_at = datetime.now().isoformat()
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur annulation commande: {e}")
            await query.answer("❌ Erreur", show_alert=True)
            session.close()
            return
        finally:
            session.close()
        
        # Modifier tous les messages admin
        cancelled_text = (
            f"❌ *COMMANDE #{order_id} — ANNULÉE*\n\n"
            f"Annulée par @{query.from_user.username or 'Admin'}\n"
            f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        
        edit_all_admin_notifications(order_id, cancelled_text)
        await query.answer("❌ Commande annulée")
        return
    
    # ========== ADMIN REMET LA COMMANDE EN LIGNE ==========
    if data.startswith("admin_restore_"):
        order_id = int(data.replace("admin_restore_", ""))
        
        session = SessionLocal()
        try:
            order = session.get(Order, order_id)
            if not order:
                await query.answer("❌ Commande introuvable", show_alert=True)
                session.close()
                return
            
            # Récupérer les infos avant de remettre en attente
            service_name = order.service
            plan_label = order.plan
            price = order.price
            cost = order.cost
            username_order = order.username
            user_id_order = order.user_id
            first_name_order = order.first_name
            last_name_order = order.last_name
            email_order = order.email
            payment_method_order = order.payment_method
            
            # Remettre en attente
            order.status = 'en_attente'
            order.admin_id = None
            order.admin_username = None
            order.taken_at = None
            
            # Supprimer les anciens messages admin
            session.query(OrderMessage).filter(OrderMessage.order_id == order_id).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur remise en ligne: {e}")
            await query.answer("❌ Erreur", show_alert=True)
            session.close()
            return
        finally:
            session.close()
        
        # Renvoyer aux admins
        await resend_order_to_all_admins_async(
            context, order_id, service_name, plan_label, price, cost,
            username_order, user_id_order, first_name_order, last_name_order,
            email_order, payment_method_order
        )
        
        await query.answer("🔄 Commande remise en ligne")
        return
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text("⚠️ Utilise /start pour commencer une commande.")


async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reçoit une photo du client → la transfère aux admins avec recap + boutons."""
    if not update.message.photo:
        return
    user = update.effective_user
    user_id = user.id
    username = user.username or f"User_{user_id}"

    session = SessionLocal()
    try:
        pending_orders = session.query(Order).filter(
            Order.user_id == user_id,
            Order.status == 'en_attente'
        ).order_by(Order.id.desc()).all()
    finally:
        session.close()

    if not pending_orders:
        await update.message.reply_text(
            "⚠️ Aucune commande en attente trouvée.\n"
            "Commence une commande avec /start avant d'envoyer ta preuve."
        )
        return

    order = pending_orders[0]
    recap = (
        f"📋 *PREUVE DE PAIEMENT REÇUE*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 Client : @{username}\n"
        f"🆔 ID : {user_id}\n\n"
        f"📦 {order.service}\n"
        f"📋 {order.plan}\n"
        f"💰 {order.price}€\n"
        f"💳 {order.payment_method or 'N/A'}\n"
        f"📌 Commande #{order.id}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Valider", callback_data=f"admin_complete_{order.id}"),
            InlineKeyboardButton("❌ Annuler", callback_data=f"admin_cancel_{order.id}")
        ],
        [InlineKeyboardButton("✋ Prendre en charge", callback_data=f"admin_take_{order.id}")]
    ])

    session = SessionLocal()
    try:
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.forward_message(
                    chat_id=admin_id,
                    from_chat_id=update.effective_chat.id,
                    message_id=update.message.message_id
                )
                msg = await context.bot.send_message(
                    chat_id=admin_id,
                    text=recap,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                om = OrderMessage(order_id=order.id, admin_id=admin_id, message_id=msg.message_id)
                session.add(om)
            except Exception as e:
                print(f"Erreur envoi admin {admin_id}: {e}")
        session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()

    await update.message.reply_text(
        f"✅ *Preuve reçue !*\n\n"
        f"📌 Commande #{order.id}\n"
        f"⏱️ Un admin va valider ton paiement rapidement !",
        parse_mode='Markdown'
    )


# ========== ROUTES FLASK
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == WEB_PASSWORD:
            session['logged_in'] = True
            return redirect('/dashboard')
        return render_template_string(HTML_LOGIN, error="Mot de passe incorrect")
    return render_template_string(HTML_LOGIN)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(HTML_DASHBOARD)

@app.route('/simulate')
@login_required
def simulate():
    return render_template_string(HTML_SIMULATE)

@app.route('/users')
@login_required
def users_page():
    return render_template_string(HTML_USERS)

@app.route('/manager')
@login_required
def manager_page():
    return render_template_string(HTML_REACT_MANAGER)

# ── API TOKEN (pour dashboard externe) ───────────────────────────────────────

def check_token():
    token = request.args.get('token') or request.headers.get('X-Auth-Token')
    return token == WEB_PASSWORD

@app.route('/api/token/dashboard')
def api_token_dashboard():
    if not check_token(): return jsonify({'error': 'Unauthorized'}), 401
    session = SessionLocal()
    try:
        orders_q = session.query(Order).order_by(Order.id.desc()).all()
        orders = [{'id': o.id, 'username': o.username, 'service': o.service,
            'plan': o.plan, 'price': o.price, 'first_name': o.first_name,
            'last_name': o.last_name, 'email': o.email,
            'payment_method': o.payment_method, 'status': o.status}
            for o in orders_q]
        total = session.query(func.count(Order.id)).scalar()
        pending = session.query(func.count(Order.id)).filter(Order.status == 'en_attente').scalar()
        cumul = session.get(CumulativeStats, 1)
        return jsonify({'orders': orders, 'stats': {
            'total_orders': total, 'pending_orders': pending,
            'revenue': cumul.total_revenue if cumul else 0,
            'profit': cumul.total_profit if cumul else 0}})
    finally:
        session.close()

@app.route('/api/token/users')
def api_token_users():
    if not check_token(): return jsonify({'error': 'Unauthorized'}), 401
    session = SessionLocal()
    try:
        users = [{'user_id': u.user_id, 'username': u.username or 'N/A',
            'first_name': u.first_name or '', 'last_name': u.last_name or '',
            'last_activity': u.last_activity, 'total_orders': u.total_orders}
            for u in session.query(User).order_by(User.last_activity.desc()).all()]
        return jsonify({'users': users})
    finally:
        session.close()

@app.route('/api/token/order/<int:order_id>/take', methods=['POST'])
def api_token_take(order_id):
    if not check_token(): return jsonify({'error': 'Unauthorized'}), 401
    session = SessionLocal()
    try:
        o = session.get(Order, order_id)
        if not o: return jsonify({'error': 'Not found'}), 404
        o.status = 'en_cours'
        session.commit()
        return jsonify({'success': True})
    finally:
        session.close()

@app.route('/api/token/order/<int:order_id>/complete', methods=['POST'])
def api_token_complete(order_id):
    if not check_token(): return jsonify({'error': 'Unauthorized'}), 401
    session = SessionLocal()
    try:
        o = session.get(Order, order_id)
        if not o: return jsonify({'error': 'Not found'}), 404
        o.status = 'terminee'
        session.commit()
        return jsonify({'success': True})
    finally:
        session.close()

@app.route('/api/token/order/<int:order_id>/cancel', methods=['POST'])
def api_token_cancel(order_id):
    if not check_token(): return jsonify({'error': 'Unauthorized'}), 401
    session = SessionLocal()
    try:
        o = session.get(Order, order_id)
        if not o: return jsonify({'error': 'Not found'}), 404
        o.status = 'annulee'
        session.commit()
        return jsonify({'success': True})
    finally:
        session.close()

@app.route('/api/reload_services', methods=['POST'])
@login_required
def api_reload_services():
    try:
        load_services_from_db()
        return jsonify({'success': True, 'message': 'Services rechargés depuis la DB', 'db': DATABASE_URL})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/services', methods=['GET'])
@login_required
def api_services_list():
    services = []
    for service_key, service_data in SERVICES_CONFIG_IN_MEMORY.items():
        plans = []
        for plan_key, plan_data in service_data.get('plans', {}).items():
            plans.append({
                'plan_key': plan_key,
                'label': plan_data.get('label', plan_key),
                'price': plan_data.get('price', 0.0),
                'cost': plan_data.get('cost', 0.0)
            })
        name_parts = service_data.get('name', '').split(' ', 1)
        emoji = name_parts[0] if len(name_parts) > 1 else (service_data.get('name') or '')
        display_name = name_parts[1] if len(name_parts) > 1 else (service_data.get('name') or service_key)
        services.append({
            'service_key': service_key,
            'emoji': emoji,
            'display_name': display_name,
            'active': service_data.get('active', True),
            'visible': service_data.get('visible', True),
            'category': service_data.get('category', ''),
            'plans': plans
        })
    return jsonify({'services': services})

@app.route('/api/services', methods=['POST'])
@login_required
def api_create_service():
    data = request.get_json(force=True)
    service_key = data.get('service_key')
    display_name = data.get('display_name') or service_key
    emoji = data.get('emoji') or ''
    category = data.get('category') or ''
    active = bool(data.get('active', True))
    visible = bool(data.get('visible', True))
    if not service_key:
        return jsonify({'error': 'service_key_required'}), 400
    session = SessionLocal()
    try:
        existing = session.get(Service, service_key)
        if existing:
            return jsonify({'error': 'service_exists'}), 409
        svc = Service(service_key=service_key, display_name=display_name, emoji=emoji, category=category, active=active, visible=visible)
        session.add(svc)
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({'error': 'db_error', 'detail': str(e)}), 500
    finally:
        session.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/services/<service_key>', methods=['PUT'])
@login_required
def api_update_service(service_key):
    data = request.get_json(force=True)
    display_name = data.get('display_name') or ''
    emoji = data.get('emoji') or ''
    category = data.get('category') or ''
    active = bool(data.get('active', True))
    visible = bool(data.get('visible', True))
    session = SessionLocal()
    try:
        svc = session.get(Service, service_key)
        if not svc:
            return jsonify({'error': 'Service not found'}), 404
        svc.display_name = display_name
        svc.emoji = emoji
        svc.category = category
        svc.active = active
        svc.visible = visible
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({'error': 'db_error', 'detail': str(e)}), 500
    finally:
        session.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/services/<service_key>', methods=['DELETE'])
@login_required
def api_delete_service(service_key):
    session = SessionLocal()
    try:
        svc = session.get(Service, service_key)
        if not svc:
            return jsonify({'error': 'Service not found'}), 404
        session.delete(svc)
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({'error': 'db_error', 'detail': str(e)}), 500
    finally:
        session.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/services/<service_key>/plans', methods=['POST'])
@login_required
def api_create_plan(service_key):
    data = request.get_json(force=True)
    plan_key = data.get('plan_key')
    label = data.get('label') or plan_key
    price = float(data.get('price', 0) or 0)
    cost = float(data.get('cost', 0) or 0)
    if not plan_key:
        return jsonify({'error': 'plan_key_required'}), 400
    session = SessionLocal()
    try:
        svc = session.get(Service, service_key)
        if not svc:
            return jsonify({'error': 'Service not found'}), 404
        existing = session.query(Plan).filter_by(service_key=service_key, plan_key=plan_key).first()
        if existing:
            return jsonify({'error': 'plan_exists'}), 409
        plan = Plan(service_key=service_key, plan_key=plan_key, label=label, price=price, cost=cost)
        session.add(plan)
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({'error': 'db_error', 'detail': str(e)}), 500
    finally:
        session.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/services/<service_key>/plans/<plan_key>', methods=['PUT'])
@login_required
def api_update_plan(service_key, plan_key):
    data = request.get_json(force=True)
    label = data.get('label') if 'label' in data else None
    price = float(data.get('price')) if 'price' in data and data.get('price') is not None else None
    cost = float(data.get('cost')) if 'cost' in data and data.get('cost') is not None else None
    session = SessionLocal()
    try:
        plan = session.query(Plan).filter_by(service_key=service_key, plan_key=plan_key).first()
        if not plan:
            return jsonify({'error': 'Plan not found'}), 404
        if label is not None:
            plan.label = label
        if price is not None:
            plan.price = price
        if cost is not None:
            plan.cost = cost
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({'error': 'db_error', 'detail': str(e)}), 500
    finally:
        session.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/services/<service_key>/plans/<plan_key>', methods=['DELETE'])
@login_required
def api_delete_plan(service_key, plan_key):
    session = SessionLocal()
    try:
        plan = session.query(Plan).filter_by(service_key=service_key, plan_key=plan_key).first()
        if not plan:
            return jsonify({'error': 'Plan not found'}), 404
        session.delete(plan)
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({'error': 'db_error', 'detail': str(e)}), 500
    finally:
        session.close()
    load_services_from_db()
    return jsonify({'success': True})

@app.route('/api/users')
@login_required
def api_users():
    session = SessionLocal()
    try:
        total_users = session.query(func.count(User.user_id)).scalar()
        active_users = session.query(func.count(User.user_id)).filter(User.total_orders > 0).scalar()
        conversion_rate = (active_users / total_users * 100) if total_users and total_users > 0 else 0
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        new_users = session.query(func.count(User.user_id)).filter(User.first_seen >= seven_days_ago).scalar()
        users_q = session.query(User).order_by(User.last_activity.desc()).all()
        users = []
        for u in users_q:
            users.append({
                'user_id': u.user_id,
                'username': u.username or 'N/A',
                'first_name': u.first_name or 'Inconnu',
                'last_name': u.last_name or '',
                'first_seen': u.first_seen,
                'last_activity': u.last_activity,
                'total_orders': u.total_orders
            })
        return jsonify({
            'stats': {
                'total_users': total_users,
                'active_users': active_users,
                'conversion_rate': round(conversion_rate, 1),
                'new_users': new_users
            },
            'users': users
        })
    finally:
        session.close()

@app.route('/api/users/<int:user_id>')
@login_required
def api_user_details(user_id):
    session = SessionLocal()
    try:
        orders_q = session.query(Order).filter(Order.user_id == user_id).order_by(Order.timestamp.desc()).all()
        orders = []
        for o in orders_q:
            orders.append({
                'id': o.id,
                'service': o.service,
                'plan': o.plan,
                'price': o.price,
                'timestamp': o.timestamp,
                'status': o.status
            })
        return jsonify({'orders': orders})
    finally:
        session.close()
@app.route('/api/dashboard')
@login_required
def api_dashboard():
    session = SessionLocal()
    try:
        orders_q = session.query(Order).order_by(Order.id.desc()).all()
        orders = []
        for o in orders_q:
            orders.append({
                'id': o.id,
                'username': o.username,
                'service': o.service,
                'plan': o.plan,
                'price': o.price,
                'cost': o.cost,
                'first_name': o.first_name,
                'last_name': o.last_name,
                'email': o.email,
                'payment_method': o.payment_method,
                'status': o.status,
                'admin_id': o.admin_id,
                'admin_username': o.admin_username
            })
        total = session.query(func.count(Order.id)).scalar()
        pending = session.query(func.count(Order.id)).filter(Order.status == 'en_attente').scalar()
        inprogress = session.query(func.count(Order.id)).filter(Order.status == 'en_cours').scalar()
        completed = session.query(func.count(Order.id)).filter(Order.status == 'terminee').scalar()
        cumul = session.get(CumulativeStats, 1)
        revenue = cumul.total_revenue if cumul else 0
        profit = cumul.total_profit if cumul else 0
        return jsonify({
            'orders': orders,
            'stats': {
                'total_orders': total,
                'pending_orders': pending,
                'inprogress_orders': inprogress,
                'completed_orders': completed,
                'revenue': revenue,
                'profit': profit
            }
        })
    finally:
        session.close()

@app.route('/api/order/<int:order_id>/take', methods=['POST'])
@login_required
def take_order(order_id):
    session = SessionLocal()
    try:
        o = session.get(Order, order_id)
        if not o:
            return jsonify({'error': 'Order not found'}), 404
        o.status = 'en_cours'
        o.admin_id = 999999
        o.admin_username = 'web_admin'
        o.taken_at = datetime.now().isoformat()
        session.commit()
    except Exception as e:
        session.rollback()
        print("take_order error:", e)
    finally:
        session.close()
    try:
        delete_other_admin_notifications(order_id, 999999)
        edit_admin_notification(order_id, 999999, f"🔒 *COMMANDE #{order_id} — PRISE EN CHARGE*\n\n✅ Pris en charge via le dashboard\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    except Exception as e:
        print("Erreur notifications:", e)
    return jsonify({'success': True})

@app.route('/api/order/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_order(order_id):
    session = SessionLocal()
    try:
        o = session.get(Order, order_id)
        if o:
            price = o.price or 0.0
            cost = o.cost or 0.0
            cs = session.get(CumulativeStats, 1)
            if cs:
                cs.total_revenue = (cs.total_revenue or 0.0) + price
                cs.total_profit = (cs.total_profit or 0.0) + (price - cost)
                cs.last_updated = datetime.now().isoformat()
            o.status = 'terminee'
            session.commit()
    except Exception as e:
        session.rollback()
        print("complete_order error:", e)
    finally:
        session.close()
    try:
        edit_all_admin_notifications(order_id, f"✅ *COMMANDE #{order_id} — TERMINÉE*\n\nTerminée via le dashboard\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    except Exception as e:
        print("Erreur notifications:", e)
    return jsonify({'success': True})

@app.route('/api/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    session = SessionLocal()
    try:
        o = session.get(Order, order_id)
        if o:
            o.status = 'annulee'
            o.cancelled_at = datetime.now().isoformat()
            session.commit()
    except Exception as e:
        session.rollback()
        print("cancel_order error:", e)
    finally:
        session.close()
    try:
        edit_all_admin_notifications(order_id, f"❌ *COMMANDE #{order_id} — ANNULÉE*\n\nAnnulée via le dashboard\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    except Exception as e:
        print("Erreur notifications:", e)
    return jsonify({'success': True})

@app.route('/api/order/<int:order_id>/restore', methods=['POST'])
@login_required
def restore_order(order_id):
    session = SessionLocal()
    try:
        o = session.get(Order, order_id)
        if o:
            o.status = 'en_attente'
            o.admin_id = None
            o.admin_username = None
            o.taken_at = None
            o.cancelled_by = None
            o.cancelled_at = None
            session.query(OrderMessage).filter(OrderMessage.order_id == order_id).delete()
            session.commit()
    except Exception as e:
        session.rollback()
        print("restore_order error:", e)
    finally:
        session.close()
    try:
        resend_order_to_all_admins(order_id)
    except Exception as e:
        print("Erreur renvoi notifications:", e)
    return jsonify({'success': True})

# ── HUB USERS (comptes dashboard) ────────────────────────────────────────────
import json, hashlib

HUB_USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hub_users.json')

def hub_load_users():
    if not os.path.exists(HUB_USERS_FILE):
        default = [{'username': 'admin', 'password': hashlib.sha256('Jamal2laleague'.encode()).hexdigest(), 'role': 'admin', 'perms': ['overview','b4u-orders','shop-orders','b4u-users','shop-users','shop-stock','actions','settings']}]
        with open(HUB_USERS_FILE, 'w') as f: json.dump(default, f)
        return default
    with open(HUB_USERS_FILE, 'r') as f: return json.load(f)

def hub_save_users(users):
    with open(HUB_USERS_FILE, 'w') as f: json.dump(users, f)

@app.route('/api/hub/login', methods=['POST'])
def hub_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = hashlib.sha256(data.get('password', '').encode()).hexdigest()
    users = hub_load_users()
    user = next((u for u in users if u['username'] == username and u['password'] == password), None)
    if not user: return jsonify({'error': 'Identifiants incorrects'}), 401
    return jsonify({'username': user['username'], 'role': user['role'], 'perms': user['perms']})

@app.route('/api/hub/users', methods=['GET'])
def hub_get_users():
    if not check_token(): return jsonify({'error': 'Unauthorized'}), 401
    users = hub_load_users()
    return jsonify([{'username': u['username'], 'role': u['role'], 'perms': u['perms']} for u in users])

@app.route('/api/hub/users', methods=['POST'])
def hub_create_user():
    if not check_token(): return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    perms = data.get('perms', [])
    if not username or not password: return jsonify({'error': 'Champs manquants'}), 400
    users = hub_load_users()
    if any(u['username'] == username for u in users): return jsonify({'error': 'Existe déjà'}), 400
    users.append({'username': username, 'password': hashlib.sha256(password.encode()).hexdigest(), 'role': 'user', 'perms': perms})
    hub_save_users(users)
    return jsonify({'success': True})

@app.route('/api/hub/users/<username>', methods=['DELETE'])
def hub_delete_user(username):
    if not check_token(): return jsonify({'error': 'Unauthorized'}), 401
    users = hub_load_users()
    users = [u for u in users if u['username'] != username or u['role'] == 'admin']
    hub_save_users(users)
    return jsonify({'success': True})

@app.route('/')
def index():
    return redirect('/dashboard')

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'bot': 'running'})

@app.route('/api/simulate', methods=['POST'])
@login_required
def api_simulate():
    try:
        data = request.get_json(force=True)
        if data is None:
            raise ValueError("Corps JSON vide")
    except Exception as e:
        return jsonify({'success': False, 'error': 'invalid_json', 'detail': str(e)}), 400
    try:
        count = int(data.get('count', 1))
    except Exception as e:
        return jsonify({'success': False, 'error': 'invalid_count'}), 400
    service_filter = data.get('service', 'all')
    status = data.get('status', 'terminee')
    first_names = ['Lucas', 'Emma', 'Louis', 'Léa', 'Hugo', 'Chloé', 'Arthur', 'Manon', 'Jules', 'Camille']
    last_names = ['Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand']
    payment_methods = ['PayPal', 'Virement', 'Revolut']
    services_list = []
    for service_key, service_data in SERVICES_CONFIG_IN_MEMORY.items():
        for plan_key, plan_data in service_data['plans'].items():
            services_list.append({
                'key': service_key,
                'name': service_data['name'],
                'plan_key': plan_key,
                'plan_label': plan_data['label'],
                'price': plan_data['price'],
                'cost': plan_data['cost']
            })
    session = SessionLocal()
    created_orders = []
    try:
        for i in range(count):
            if service_filter == 'all':
                service = random.choice(services_list)
            else:
                filtered = [s for s in services_list if s['key'] == service_filter]
                service = random.choice(filtered) if filtered else random.choice(services_list)
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@email.com"
            user_id = random.randint(100000000, 999999999)
            username = f"user_{random.randint(1000, 9999)}"
            payment_method = random.choice(payment_methods)
            days_ago = random.randint(0, 30)
            timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
            user = session.get(User, user_id)
            if not user:
                user = User(user_id=user_id, username=username, first_name=first_name, last_name=last_name, first_seen=timestamp, last_activity=timestamp, total_orders=0)
                session.add(user)
            user.last_activity = timestamp
            user.total_orders = (user.total_orders or 0) + 1
            if service['key'] == 'deezer':
                o = Order(user_id=user_id, username=username, service=service['name'], plan=service['plan_label'], price=service['price'], cost=service['cost'], timestamp=timestamp, status=status, first_name=last_name, last_name=first_name, email=email)
            else:
                o = Order(user_id=user_id, username=username, service=service['name'], plan=service['plan_label'], price=service['price'], cost=service['cost'], timestamp=timestamp, status=status, first_name=first_name, last_name=last_name, email=email, payment_method=payment_method)
            session.add(o)
            session.flush()
            if status == 'terminee':
                cs = session.get(CumulativeStats, 1)
                if cs:
                    cs.total_revenue = (cs.total_revenue or 0.0) + (service['price'] or 0.0)
                    cs.total_profit = (cs.total_profit or 0.0) + ((service['price'] or 0.0) - (service['cost'] or 0.0))
                    cs.last_updated = datetime.now().isoformat()
            created_orders.append({
                'id': o.id,
                'service': service['name'],
                'price': service['price']
            })
        session.commit()
    except Exception as e:
        session.rollback()
        tb = traceback.format_exc()
        print("Erreur génération commandes:", e)
        print(tb)
        return jsonify({'success': False, 'error': 'exception_during_insert', 'detail': str(e)}), 500
    finally:
        session.close()
    return jsonify({'success': True, 'created': len(created_orders), 'orders': created_orders})

# BOT TELEGRAM MAIN
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
    print(f"🌐 Serveur Flask démarré sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
