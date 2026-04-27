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
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, func
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
<title>B4U Deals — Connexion</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'DM Sans',sans-serif;background:#0d0f14;min-height:100vh;display:flex;align-items:center;justify-content:center;overflow:hidden}
.bg{position:fixed;inset:0;background:radial-gradient(ellipse 80% 60% at 50% -10%,rgba(102,126,234,0.25) 0%,transparent 70%)}
.card{position:relative;z-index:1;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:24px;padding:48px 40px;width:100%;max-width:420px;backdrop-filter:blur(20px)}
.logo{text-align:center;margin-bottom:36px}
.logo-icon{width:64px;height:64px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:16px;display:inline-flex;align-items:center;justify-content:center;font-size:28px;margin-bottom:16px}
.logo h1{font-family:'Syne',sans-serif;font-size:26px;font-weight:800;color:#fff;letter-spacing:-0.5px}
.logo p{color:rgba(255,255,255,0.4);font-size:13px;margin-top:4px}
label{display:block;color:rgba(255,255,255,0.5);font-size:12px;font-weight:500;letter-spacing:0.8px;text-transform:uppercase;margin-bottom:8px}
input{width:100%;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:14px 16px;color:#fff;font-size:15px;font-family:'DM Sans',sans-serif;outline:none;transition:border-color .2s}
input:focus{border-color:rgba(102,126,234,0.6)}
.input-wrap{margin-bottom:24px}
button{width:100%;padding:15px;background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:10px;color:#fff;font-family:'Syne',sans-serif;font-size:15px;font-weight:700;letter-spacing:0.3px;cursor:pointer;transition:opacity .2s}
button:hover{opacity:0.9}
.error{background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3);color:#fca5a5;padding:12px 16px;border-radius:10px;font-size:13px;margin-bottom:20px}
</style>
</head>
<body>
<div class="bg"></div>
<div class="card">
  <div class="logo">
    <div class="logo-icon">🎯</div>
    <h1>B4U Deals</h1>
    <p>Panneau d'administration</p>
  </div>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <div class="input-wrap">
      <label>Mot de passe</label>
      <input type="password" name="password" placeholder="••••••••" required autofocus>
    </div>
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
<title>B4U Deals — Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0d0f14;--surface:#161920;--surface2:#1e2129;--border:rgba(255,255,255,0.07);--text:#e8eaf0;--text2:rgba(232,234,240,0.5);--accent:#667eea;--accent2:#764ba2;--green:#10b981;--orange:#f59e0b;--red:#ef4444;--blue:#3b82f6}
body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex}
/* SIDEBAR */
.sidebar{width:240px;min-height:100vh;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;flex-shrink:0;position:fixed;top:0;left:0;height:100vh;z-index:100}
.sidebar-logo{padding:24px 20px;border-bottom:1px solid var(--border)}
.sidebar-logo .name{font-family:'Syne',sans-serif;font-size:18px;font-weight:800;color:#fff}
.sidebar-logo .sub{font-size:11px;color:var(--text2);margin-top:2px}
.sidebar-nav{padding:16px 12px;flex:1}
.nav-section{font-size:10px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;color:var(--text2);padding:0 8px;margin:16px 0 8px}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;color:var(--text2);text-decoration:none;font-size:14px;font-weight:500;transition:all .15s;cursor:pointer;border:none;background:none;width:100%}
.nav-item:hover{background:rgba(255,255,255,0.05);color:var(--text)}
.nav-item.active{background:linear-gradient(135deg,rgba(102,126,234,0.2),rgba(118,75,162,0.1));color:#fff;border:1px solid rgba(102,126,234,0.25)}
.nav-item .icon{font-size:16px;width:20px;text-align:center}
.sidebar-footer{padding:16px 12px;border-top:1px solid var(--border)}
/* MAIN */
.main{margin-left:240px;flex:1;min-height:100vh;display:flex;flex-direction:column}
.topbar{padding:20px 28px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:var(--surface)}
.topbar h2{font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:#fff}
.topbar-right{display:flex;align-items:center;gap:12px}
.badge{background:rgba(102,126,234,0.15);border:1px solid rgba(102,126,234,0.3);color:var(--accent);padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600}
.refresh-btn{background:rgba(255,255,255,0.06);border:1px solid var(--border);color:var(--text2);padding:8px 14px;border-radius:8px;font-size:13px;cursor:pointer;transition:all .15s;font-family:'DM Sans',sans-serif}
.refresh-btn:hover{background:rgba(255,255,255,0.1);color:var(--text)}
.content{padding:24px 28px;flex:1}
/* KPI CARDS */
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:20px 22px;transition:transform .15s}
.kpi:hover{transform:translateY(-2px)}
.kpi-label{font-size:12px;color:var(--text2);font-weight:500;letter-spacing:0.3px;margin-bottom:10px}
.kpi-value{font-family:'Syne',sans-serif;font-size:28px;font-weight:700;color:#fff}
.kpi-sub{font-size:12px;color:var(--text2);margin-top:4px}
.kpi.green .kpi-value{color:var(--green)}
.kpi.orange .kpi-value{color:var(--orange)}
.kpi.blue .kpi-value{color:var(--blue)}
/* FILTERS */
.filters{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;align-items:center}
.filter-btn{background:var(--surface2);border:1px solid var(--border);color:var(--text2);padding:7px 14px;border-radius:8px;font-size:13px;cursor:pointer;transition:all .15s;font-family:'DM Sans',sans-serif}
.filter-btn:hover,.filter-btn.active{background:rgba(102,126,234,0.15);border-color:rgba(102,126,234,0.4);color:var(--accent)}
.search-input{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:8px 14px;border-radius:8px;font-size:13px;outline:none;font-family:'DM Sans',sans-serif;margin-left:auto;width:220px}
.search-input::placeholder{color:var(--text2)}
.search-input:focus{border-color:rgba(102,126,234,0.4)}
/* TABLE */
.table-wrap{background:var(--surface);border:1px solid var(--border);border-radius:16px;overflow:hidden}
.table-header{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.table-header h3{font-family:'Syne',sans-serif;font-size:15px;font-weight:700;color:#fff}
table{width:100%;border-collapse:collapse}
thead tr{background:var(--surface2)}
th{padding:11px 16px;text-align:left;font-size:11px;font-weight:600;letter-spacing:0.6px;text-transform:uppercase;color:var(--text2);border-bottom:1px solid var(--border)}
td{padding:13px 16px;font-size:14px;border-bottom:1px solid rgba(255,255,255,0.04)}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(255,255,255,0.02)}
.status-badge{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600}
.status-badge.attente{background:rgba(245,158,11,0.12);color:#fbbf24;border:1px solid rgba(245,158,11,0.25)}
.status-badge.cours{background:rgba(59,130,246,0.12);color:#60a5fa;border:1px solid rgba(59,130,246,0.25)}
.status-badge.terminee{background:rgba(16,185,129,0.12);color:#34d399;border:1px solid rgba(16,185,129,0.25)}
.status-badge.annulee{background:rgba(239,68,68,0.1);color:#f87171;border:1px solid rgba(239,68,68,0.2)}
.action-btn{padding:5px 10px;border:none;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;font-family:'DM Sans',sans-serif;transition:opacity .15s}
.action-btn:hover{opacity:0.8}
.btn-take{background:rgba(59,130,246,0.2);color:#60a5fa;border:1px solid rgba(59,130,246,0.3)}
.btn-complete{background:rgba(16,185,129,0.2);color:#34d399;border:1px solid rgba(16,185,129,0.3)}
.btn-cancel{background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.25)}
.btn-restore{background:rgba(245,158,11,0.15);color:#fbbf24;border:1px solid rgba(245,158,11,0.25)}
.empty{text-align:center;padding:48px;color:var(--text2);font-size:14px}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.dot.attente{background:#fbbf24}
.dot.cours{background:#60a5fa}
.dot.terminee{background:#34d399}
.dot.annulee{background:#f87171}
.page-hidden{display:none!important}
/* Modal */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px)}
.modal{background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:28px;width:100%;max-width:500px}
.modal h3{font-family:'Syne',sans-serif;font-size:17px;font-weight:700;color:#fff;margin-bottom:20px}
.modal-field{margin-bottom:16px}
.modal-field label{display:block;font-size:11px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:var(--text2);margin-bottom:6px}
.modal-field input,.modal-field select{width:100%;background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:10px 14px;border-radius:8px;font-size:14px;font-family:'DM Sans',sans-serif;outline:none}
.modal-field select option{background:var(--surface2);color:var(--text)}
.modal-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:20px}
.btn-primary{background:linear-gradient(135deg,#667eea,#764ba2);border:none;color:#fff;padding:10px 20px;border-radius:8px;font-family:'Syne',sans-serif;font-weight:700;font-size:14px;cursor:pointer}
.btn-ghost{background:rgba(255,255,255,0.06);border:1px solid var(--border);color:var(--text2);padding:10px 20px;border-radius:8px;font-family:'DM Sans',sans-serif;font-size:14px;cursor:pointer}
.send-link-btn{background:rgba(102,126,234,0.15);border:1px solid rgba(102,126,234,0.3);color:var(--accent);padding:5px 10px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;font-family:'DM Sans',sans-serif}
</style>
</head>
<body>
<aside class="sidebar">
  <div class="sidebar-logo">
    <div style="font-size:24px;margin-bottom:8px">🎯</div>
    <div class="name">B4U Deals</div>
    <div class="sub">Panneau Admin</div>
  </div>
  <nav class="sidebar-nav">
    <div class="nav-section">Principal</div>
    <button class="nav-item active" onclick="showPage('dashboard',this)"><span class="icon">📊</span>Dashboard</button>
    <button class="nav-item" onclick="showPage('orders',this)"><span class="icon">📦</span>Commandes</button>
    <button class="nav-item" onclick="showPage('users',this)"><span class="icon">👥</span>Utilisateurs</button>
    <div class="nav-section">Configuration</div>
    <button class="nav-item" onclick="showPage('manager',this)"><span class="icon">🎛️</span>Services</button>
    <button class="nav-item" onclick="showPage('simulate',this)"><span class="icon">🎲</span>Simuler</button>
  </nav>
  <div class="sidebar-footer">
    <a href="/logout" class="nav-item" style="text-decoration:none"><span class="icon">🚪</span>Déconnexion</a>
  </div>
</aside>

<div class="main">
  <!-- PAGE DASHBOARD -->
  <div id="page-dashboard">
    <div class="topbar">
      <h2>Vue d'ensemble</h2>
      <div class="topbar-right">
        <span class="badge" id="live-badge">● Live</span>
        <button class="refresh-btn" onclick="loadAll()">↻ Actualiser</button>
      </div>
    </div>
    <div class="content">
      <div class="kpi-grid">
        <div class="kpi"><div class="kpi-label">📦 Total commandes</div><div class="kpi-value" id="kpi-total">—</div><div class="kpi-sub">depuis le début</div></div>
        <div class="kpi orange"><div class="kpi-label">⏳ En attente</div><div class="kpi-value" id="kpi-pending">—</div><div class="kpi-sub">à traiter</div></div>
        <div class="kpi green"><div class="kpi-label">💰 Chiffre d'affaires</div><div class="kpi-value" id="kpi-revenue">—</div><div class="kpi-sub">cumulé total</div></div>
        <div class="kpi blue"><div class="kpi-label">💵 Bénéfice net</div><div class="kpi-value" id="kpi-profit">—</div><div class="kpi-sub">cumulé total</div></div>
      </div>
      <div class="table-wrap">
        <div class="table-header">
          <h3>Commandes récentes</h3>
          <button class="filter-btn" onclick="showPage('orders',document.querySelectorAll('.nav-item')[1])">Voir tout →</button>
        </div>
        <table>
          <thead><tr><th>#</th><th>Service</th><th>Client</th><th>Montant</th><th>Paiement</th><th>Statut</th><th>Actions</th></tr></thead>
          <tbody id="recent-orders"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- PAGE ORDERS -->
  <div id="page-orders" class="page-hidden">
    <div class="topbar">
      <h2>Commandes</h2>
      <div class="topbar-right">
        <span id="orders-count" class="badge">0</span>
        <button class="refresh-btn" onclick="loadOrders()">↻ Actualiser</button>
      </div>
    </div>
    <div class="content">
      <div class="filters">
        <button class="filter-btn active" onclick="filterOrders('all',this)">Toutes</button>
        <button class="filter-btn" onclick="filterOrders('en_attente',this)">⏳ Attente</button>
        <button class="filter-btn" onclick="filterOrders('en_cours',this)">🔵 En cours</button>
        <button class="filter-btn" onclick="filterOrders('terminee',this)">✅ Terminées</button>
        <button class="filter-btn" onclick="filterOrders('annulee',this)">❌ Annulées</button>
        <input type="text" class="search-input" id="orders-search" placeholder="🔍 Rechercher..." oninput="renderOrders()">
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>#</th><th>Service / Plan</th><th>Client</th><th>Email</th><th>Montant</th><th>Paiement</th><th>Statut</th><th>Actions</th></tr></thead>
          <tbody id="orders-table"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- PAGE USERS -->
  <div id="page-users" class="page-hidden">
    <div class="topbar">
      <h2>Utilisateurs</h2>
      <div class="topbar-right"><span id="users-count" class="badge">0</span></div>
    </div>
    <div class="content">
      <div class="kpi-grid" style="grid-template-columns:repeat(4,1fr);margin-bottom:24px">
        <div class="kpi"><div class="kpi-label">👥 Total</div><div class="kpi-value" id="u-total">—</div></div>
        <div class="kpi green"><div class="kpi-label">🛒 Actifs</div><div class="kpi-value" id="u-active">—</div></div>
        <div class="kpi blue"><div class="kpi-label">📈 Conversion</div><div class="kpi-value" id="u-conv">—</div></div>
        <div class="kpi orange"><div class="kpi-label">🆕 7 derniers jours</div><div class="kpi-value" id="u-new">—</div></div>
      </div>
      <div class="filters">
        <input type="text" class="search-input" id="users-search" placeholder="🔍 Rechercher..." oninput="renderUsers()" style="margin-left:0">
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Utilisateur</th><th>Telegram</th><th>ID</th><th>Commandes</th><th>Première visite</th><th>Dernière activité</th></tr></thead>
          <tbody id="users-table"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- PAGE MANAGER -->
  <div id="page-manager" class="page-hidden">
    <div class="topbar">
      <h2>Gestion des services</h2>
      <div class="topbar-right">
        <button class="refresh-btn" onclick="loadManager()">↻ Actualiser</button>
        <button class="btn-primary" onclick="openAddServiceModal()" style="font-size:13px;padding:8px 16px">+ Ajouter service</button>
      </div>
    </div>
    <div class="content">
      <div id="manager-content"></div>
    </div>
  </div>

  <!-- PAGE SIMULATE -->
  <div id="page-simulate" class="page-hidden">
    <div class="topbar"><h2>Simuler des commandes</h2></div>
    <div class="content">
      <div class="table-wrap" style="padding:28px;max-width:520px">
        <h3 style="font-family:Syne,sans-serif;font-size:17px;font-weight:700;color:#fff;margin-bottom:24px">🎲 Génération de données test</h3>
        <div class="modal-field">
          <label>Nombre de commandes</label>
          <input type="number" id="sim-count" value="5" min="1" max="100" style="background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:10px 14px;border-radius:8px;width:100%;font-size:14px;outline:none">
        </div>
        <div class="modal-field">
          <label>Service</label>
          <select id="sim-service" style="background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:10px 14px;border-radius:8px;width:100%;font-size:14px;outline:none">
            <option value="all">Tous les services</option>
          </select>
        </div>
        <div class="modal-field">
          <label>Statut</label>
          <select id="sim-status" style="background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:10px 14px;border-radius:8px;width:100%;font-size:14px;outline:none">
            <option value="terminee">Terminée</option>
            <option value="en_attente">En attente</option>
            <option value="en_cours">En cours</option>
            <option value="annulee">Annulée</option>
          </select>
        </div>
        <button class="btn-primary" onclick="runSimulate()" style="width:100%;margin-top:8px;padding:12px">Générer</button>
        <div id="sim-result" style="margin-top:16px;font-size:13px;color:var(--text2)"></div>
      </div>
    </div>
  </div>
</div>

<!-- MODALS -->
<div id="modal-overlay" style="display:none" class="modal-overlay" onclick="if(event.target===this)closeModal()">
  <div class="modal" id="modal-content"></div>
</div>
<!-- SEND LINK MODAL -->
<div id="link-modal-overlay" style="display:none" class="modal-overlay" onclick="if(event.target===this)closeLinkModal()">
  <div class="modal" id="link-modal-content">
    <h3>📨 Envoyer un lien</h3>
    <div class="modal-field">
      <label>Lien à envoyer</label>
      <input type="text" id="link-input" placeholder="https://..." style="background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:10px 14px;border-radius:8px;width:100%;font-size:14px;outline:none">
    </div>
    <div class="modal-actions">
      <button class="btn-ghost" onclick="closeLinkModal()">Annuler</button>
      <button class="btn-primary" onclick="sendLink()">Envoyer</button>
    </div>
  </div>
</div>

<script>
let allOrders = [];
let allUsers = [];
let currentFilter = 'all';
let currentLinkOrderId = null;

// Navigation
function showPage(page, btn) {
  document.querySelectorAll('[id^="page-"]').forEach(p => p.classList.add('page-hidden'));
  document.getElementById('page-' + page).classList.remove('page-hidden');
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  if (page === 'dashboard') loadDashboard();
  if (page === 'orders') loadOrders();
  if (page === 'users') loadUsers();
  if (page === 'manager') loadManager();
  if (page === 'simulate') loadSimServices();
}

// === DASHBOARD ===
async function loadDashboard() {
  const r = await fetch('/api/dashboard'); const d = await r.json();
  document.getElementById('kpi-total').textContent = d.stats.total_orders;
  document.getElementById('kpi-pending').textContent = d.stats.pending_orders;
  document.getElementById('kpi-revenue').textContent = d.stats.revenue.toFixed(2) + '€';
  document.getElementById('kpi-profit').textContent = d.stats.profit.toFixed(2) + '€';
  const tbody = document.getElementById('recent-orders');
  const recent = d.orders.slice(0, 10);
  if (!recent.length) { tbody.innerHTML = '<tr><td colspan="7" class="empty">Aucune commande</td></tr>'; return; }
  tbody.innerHTML = recent.map(o => `<tr>
    <td><strong>#${o.id}</strong></td>
    <td>${o.service}<br><small style="color:var(--text2)">${o.plan||''}</small></td>
    <td>${o.first_name||''} ${o.last_name||''}<br><small style="color:var(--text2)">@${o.username||'N/A'}</small></td>
    <td><strong>${o.price}€</strong></td>
    <td>${o.payment_method||'—'}</td>
    <td>${statusBadge(o.status)}</td>
    <td>${actionBtns(o)}</td>
  </tr>`).join('');
}

// === ORDERS ===
async function loadOrders() {
  const r = await fetch('/api/dashboard'); const d = await r.json();
  allOrders = d.orders;
  document.getElementById('orders-count').textContent = d.orders.length;
  renderOrders();
}
function filterOrders(f, btn) {
  currentFilter = f;
  document.querySelectorAll('#page-orders .filter-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderOrders();
}
function renderOrders() {
  const q = (document.getElementById('orders-search').value||''). toLowerCase();
  let list = allOrders.filter(o => currentFilter === 'all' || o.status === currentFilter);
  if (q) list = list.filter(o => JSON.stringify(o).toLowerCase().includes(q));
  const tbody = document.getElementById('orders-table');
  if (!list.length) { tbody.innerHTML = '<tr><td colspan="8" class="empty">Aucune commande</td></tr>'; return; }
  tbody.innerHTML = list.map(o => `<tr>
    <td><strong>#${o.id}</strong></td>
    <td>${o.service}<br><small style="color:var(--text2)">${o.plan||''}</small></td>
    <td>${o.first_name||''} ${o.last_name||''}<br><small style="color:var(--text2)">@${o.username||'N/A'}</small></td>
    <td style="color:var(--text2);font-size:13px">${o.email||'—'}</td>
    <td><strong>${o.price}€</strong><br><small style="color:var(--text2)">coût ${o.cost||0}€</small></td>
    <td>${o.payment_method||'—'}</td>
    <td>${statusBadge(o.status)}</td>
    <td style="white-space:nowrap">${actionBtns(o)} <button class="send-link-btn" onclick="openLinkModal(${o.id})">🔗</button></td>
  </tr>`).join('');
}

// === USERS ===
async function loadUsers() {
  const r = await fetch('/api/users'); const d = await r.json();
  allUsers = d.users;
  document.getElementById('users-count').textContent = d.users.length;
  document.getElementById('u-total').textContent = d.stats.total_users;
  document.getElementById('u-active').textContent = d.stats.active_users;
  document.getElementById('u-conv').textContent = d.stats.conversion_rate + '%';
  document.getElementById('u-new').textContent = d.stats.new_users;
  renderUsers();
}
function renderUsers() {
  const q = (document.getElementById('users-search').value||''). toLowerCase();
  let list = allUsers;
  if (q) list = list.filter(u => JSON.stringify(u).toLowerCase().includes(q));
  const tbody = document.getElementById('users-table');
  if (!list.length) { tbody.innerHTML = '<tr><td colspan="6" class="empty">Aucun utilisateur</td></tr>'; return; }
  tbody.innerHTML = list.map(u => `<tr>
    <td><strong>${u.first_name} ${u.last_name}</strong></td>
    <td>@${u.username}</td>
    <td style="color:var(--text2);font-size:12px">${u.user_id}</td>
    <td><span class="status-badge cours">${u.total_orders} commande${u.total_orders>1?'s':''}</span></td>
    <td style="color:var(--text2);font-size:13px">${fmtDate(u.first_seen)}</td>
    <td style="color:var(--text2);font-size:13px">${fmtDate(u.last_activity)}</td>
  </tr>`).join('');
}

// === MANAGER ===
async function loadManager() {
  const r = await fetch('/api/services'); const d = await r.json();
  const cats = {streaming:'🎬 Streaming',sport:'⚽ Sport',music:'🎧 Musique',ai:'🤖 IA',fitness:'🏋️ Fitness',vpn:'🔒 VPN',software:'💻 Logiciels',education:'📚 Éducation',apple:'🍎 Apple'};
  const bycat = {};
  d.services.forEach(s => { const c = s.category||'other'; if(!bycat[c]) bycat[c]=[]; bycat[c].push(s); });
  let html = '';
  for (const [cat, svcs] of Object.entries(bycat)) {
    html += `<div style="margin-bottom:24px">
      <h4 style="font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:var(--text2);letter-spacing:1px;text-transform:uppercase;margin-bottom:12px">${cats[cat]||cat}</h4>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Service</th><th>Plan</th><th>Prix</th><th>Coût</th><th>Marge</th><th>Statut</th><th>Actions</th></tr></thead>
          <tbody>`;
    svcs.forEach(s => {
      if (s.plans.length === 0) {
        html += `<tr><td><strong>${s.emoji} ${s.display_name}</strong></td><td colspan="4" style="color:var(--text2)">Aucun plan</td>
          <td>${s.active ? '<span class="status-badge terminee">Actif</span>' : '<span class="status-badge annulee">Inactif</span>'}</td>
          <td><button class="action-btn btn-take" onclick='editService(${JSON.stringify(s)})'>✏️</button>
              <button class="action-btn btn-cancel" onclick="deleteService('${s.service_key}')">🗑️</button>
              <button class="action-btn btn-restore" onclick='addPlanModal("${s.service_key}")'>+ Plan</button></td></tr>`;
      } else {
        s.plans.forEach((p, i) => {
          const margin = ((p.price - p.cost) / p.price * 100).toFixed(0);
          html += `<tr>
            ${i===0 ? `<td rowspan="${s.plans.length}" style="vertical-align:top;padding-top:15px"><strong>${s.emoji} ${s.display_name}</strong><br><small style="color:var(--text2)">${s.service_key}</small></td>` : ''}
            <td>${p.label}</td><td><strong>${p.price}€</strong></td><td>${p.cost}€</td>
            <td><span style="color:${margin>50?'#34d399':'#fbbf24'}">${margin}%</span></td>
            ${i===0 ? `<td rowspan="${s.plans.length}" style="vertical-align:top;padding-top:15px">${s.active ? '<span class="status-badge terminee">Actif</span>' : '<span class="status-badge annulee">Inactif</span>'}</td>` : ''}
            ${i===0 ? `<td rowspan="${s.plans.length}" style="vertical-align:top;padding-top:12px;white-space:nowrap">
              <button class="action-btn btn-take" onclick='editService(${JSON.stringify(s)})'>✏️</button>
              <button class="action-btn btn-cancel" onclick="deleteService('${s.service_key}')">🗑️</button>
              <button class="action-btn btn-restore" onclick='addPlanModal("${s.service_key}")'>+ Plan</button>
              <button class="action-btn" style="background:rgba(239,68,68,0.1);color:#f87171;border:1px solid rgba(239,68,68,0.2)" onclick='deletePlan("${s.service_key}","${p.plan_key}")'>✕</button>
              </td>` : `<td><button class="action-btn" style="background:rgba(239,68,68,0.1);color:#f87171;border:1px solid rgba(239,68,68,0.2)" onclick='deletePlan("${s.service_key}","${p.plan_key}")'>✕</button></td>`}
          </tr>`;
        });
      }
    });
    html += `</tbody></table></div></div>`;
  }
  document.getElementById('manager-content').innerHTML = html;
}

function openAddServiceModal() {
  document.getElementById('modal-content').innerHTML = `
    <h3>➕ Nouveau service</h3>
    <div class="modal-field"><label>Clé (ex: netflix)</label><input id="m-key" placeholder="netflix"></div>
    <div class="modal-field"><label>Emoji</label><input id="m-emoji" placeholder="🎬"></div>
    <div class="modal-field"><label>Nom</label><input id="m-name" placeholder="Netflix"></div>
    <div class="modal-field"><label>Catégorie</label>
      <select id="m-cat"><option value="streaming">streaming</option><option value="sport">sport</option><option value="music">music</option><option value="ai">ai</option><option value="fitness">fitness</option><option value="vpn">vpn</option><option value="software">software</option><option value="education">education</option><option value="apple">apple</option></select>
    </div>
    <div class="modal-actions">
      <button class="btn-ghost" onclick="closeModal()">Annuler</button>
      <button class="btn-primary" onclick="createService()">Créer</button>
    </div>`;
  document.getElementById('modal-overlay').style.display = 'flex';
}
async function createService() {
  const r = await fetch('/api/services', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({service_key:document.getElementById('m-key').value,emoji:document.getElementById('m-emoji').value,display_name:document.getElementById('m-name').value,category:document.getElementById('m-cat').value,active:true,visible:true})});
  closeModal(); loadManager();
}
function editService(s) {
  document.getElementById('modal-content').innerHTML = `
    <h3>✏️ Modifier ${s.emoji} ${s.display_name}</h3>
    <div class="modal-field"><label>Emoji</label><input id="m-emoji" value="${s.emoji}"></div>
    <div class="modal-field"><label>Nom</label><input id="m-name" value="${s.display_name}"></div>
    <div class="modal-field"><label>Catégorie</label>
      <select id="m-cat"><option value="streaming" ${s.category==='streaming'?'selected':''}>streaming</option><option value="sport" ${s.category==='sport'?'selected':''}>sport</option><option value="music" ${s.category==='music'?'selected':''}>music</option><option value="ai" ${s.category==='ai'?'selected':''}>ai</option><option value="fitness" ${s.category==='fitness'?'selected':''}>fitness</option><option value="vpn" ${s.category==='vpn'?'selected':''}>vpn</option><option value="software" ${s.category==='software'?'selected':''}>software</option><option value="education" ${s.category==='education'?'selected':''}>education</option><option value="apple" ${s.category==='apple'?'selected':''}>apple</option></select>
    </div>
    <div class="modal-field"><label>Actif</label><select id="m-active"><option value="1" ${s.active?'selected':''}>Oui</option><option value="0" ${!s.active?'selected':''}>Non</option></select></div>
    <div class="modal-actions">
      <button class="btn-ghost" onclick="closeModal()">Annuler</button>
      <button class="btn-primary" onclick="updateService('${s.service_key}')">Sauvegarder</button>
    </div>`;
  document.getElementById('modal-overlay').style.display = 'flex';
}
async function updateService(key) {
  await fetch('/api/services/'+key, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({emoji:document.getElementById('m-emoji').value,display_name:document.getElementById('m-name').value,category:document.getElementById('m-cat').value,active:document.getElementById('m-active').value==='1'})});
  closeModal(); loadManager();
}
async function deleteService(key) {
  if(!confirm('Supprimer ce service ?')) return;
  await fetch('/api/services/'+key, {method:'DELETE'});
  loadManager();
}
function addPlanModal(serviceKey) {
  document.getElementById('modal-content').innerHTML = `
    <h3>➕ Ajouter un plan</h3>
    <div class="modal-field"><label>Clé du plan (ex: standard)</label><input id="p-key" placeholder="standard"></div>
    <div class="modal-field"><label>Label</label><input id="p-label" placeholder="Netflix Premium"></div>
    <div class="modal-field"><label>Prix (€)</label><input id="p-price" type="number" step="0.01" placeholder="9.00"></div>
    <div class="modal-field"><label>Coût (€)</label><input id="p-cost" type="number" step="0.01" placeholder="1.50"></div>
    <div class="modal-actions">
      <button class="btn-ghost" onclick="closeModal()">Annuler</button>
      <button class="btn-primary" onclick="createPlan('${serviceKey}')">Ajouter</button>
    </div>`;
  document.getElementById('modal-overlay').style.display = 'flex';
}
async function createPlan(serviceKey) {
  await fetch('/api/services/'+serviceKey+'/plans',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan_key:document.getElementById('p-key').value,label:document.getElementById('p-label').value,price:parseFloat(document.getElementById('p-price').value),cost:parseFloat(document.getElementById('p-cost').value)})});
  closeModal(); loadManager();
}
async function deletePlan(serviceKey, planKey) {
  if(!confirm('Supprimer ce plan ?')) return;
  await fetch('/api/services/'+serviceKey+'/plans/'+planKey, {method:'DELETE'});
  loadManager();
}
function closeModal() { document.getElementById('modal-overlay').style.display='none'; }

// SEND LINK
function openLinkModal(orderId) { currentLinkOrderId = orderId; document.getElementById('link-input').value=''; document.getElementById('link-modal-overlay').style.display='flex'; }
function closeLinkModal() { document.getElementById('link-modal-overlay').style.display='none'; }
async function sendLink() {
  const link = document.getElementById('link-input').value.trim();
  if (!link) return;
  await fetch('/api/order/'+currentLinkOrderId+'/send_link', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({link})});
  closeLinkModal();
}

// SIMULATE
async function loadSimServices() {
  const r = await fetch('/api/services'); const d = await r.json();
  const sel = document.getElementById('sim-service');
  sel.innerHTML = '<option value="all">Tous les services</option>' + d.services.map(s => `<option value="${s.service_key}">${s.emoji} ${s.display_name}</option>`).join('');
}
async function runSimulate() {
  const el = document.getElementById('sim-result');
  el.textContent = 'Génération en cours...';
  const r = await fetch('/api/simulate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({count:parseInt(document.getElementById('sim-count').value),service:document.getElementById('sim-service').value,status:document.getElementById('sim-status').value})});
  const d = await r.json();
  el.textContent = d.success ? `✅ ${d.created} commande(s) créée(s)` : `❌ Erreur: ${d.error}`;
  el.style.color = d.success ? 'var(--green)' : 'var(--red)';
}

// ORDER ACTIONS
async function takeOrder(id) { await fetch('/api/order/'+id+'/take',{method:'POST'}); loadAll(); }
async function completeOrder(id) { await fetch('/api/order/'+id+'/complete',{method:'POST'}); loadAll(); }
async function cancelOrder(id) { await fetch('/api/order/'+id+'/cancel',{method:'POST'}); loadAll(); }
async function restoreOrder(id) { await fetch('/api/order/'+id+'/restore',{method:'POST'}); loadAll(); }

function loadAll() { loadDashboard(); if(!document.getElementById('page-orders').classList.contains('page-hidden')) loadOrders(); }

// HELPERS
function statusBadge(s) {
  const map = {en_attente:'attente',en_cours:'cours',terminee:'terminee',annulee:'annulee'};
  const lbl = {en_attente:'⏳ Attente',en_cours:'🔵 En cours',terminee:'✅ Terminée',annulee:'❌ Annulée'};
  return `<span class="status-badge ${map[s]||''}">${lbl[s]||s}</span>`;
}
function actionBtns(o) {
  let btns = '';
  if (o.status==='en_attente') btns += `<button class="action-btn btn-take" onclick="takeOrder(${o.id})">Prendre</button> `;
  if (o.status==='en_cours') btns += `<button class="action-btn btn-complete" onclick="completeOrder(${o.id})">Terminer</button> `;
  if (o.status!=='annulee') btns += `<button class="action-btn btn-cancel" onclick="cancelOrder(${o.id})">Annuler</button> `;
  if (o.status==='annulee'||o.status==='terminee') btns += `<button class="action-btn btn-restore" onclick="restoreOrder(${o.id})">↩️</button>`;
  return btns;
}
function fmtDate(s) { if(!s) return '—'; try { return new Date(s).toLocaleDateString('fr-FR',{day:'2-digit',month:'2-digit',year:'numeric'}); } catch(e){return s;} }

// Init
loadDashboard();
setInterval(loadAll, 20000);
</script>
</body>
</html>
'''

HTML_USERS = ''''''
HTML_REACT_MANAGER = ''''''
HTML_SIMULATE = ''''''

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
    return redirect('/dashboard')

@app.route('/users')
@login_required
def users_page():
    return redirect('/dashboard')

@app.route('/manager')
@login_required
def manager_page():
    return redirect('/dashboard')

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


@app.route('/api/order/<int:order_id>/send_link', methods=['POST'])
@login_required
def send_link_route(order_id):
    data = request.get_json(force=True)
    link = data.get('link', '').strip()
    if not link:
        return jsonify({'error': 'link_required'}), 400
    session = SessionLocal()
    try:
        o = session.get(Order, order_id)
        if not o:
            return jsonify({'error': 'not_found'}), 404
        user_id = o.user_id
    finally:
        session.close()
    try:
        import asyncio
        async def _send():
            from telegram import Bot
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(chat_id=user_id, text=f"🔗 Voici votre lien :\n{link}")
        asyncio.run(_send())
    except Exception as e:
        print(f"Erreur send_link: {e}")
        return jsonify({'error': str(e)}), 500
    return jsonify({'success': True})

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
