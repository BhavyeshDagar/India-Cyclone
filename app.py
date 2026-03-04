import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import random
import time
import math
import sqlite3
import smtplib
import socket
import os
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from inference import predict_6h

# =============================================================================
# 1. OFFLINE & DATABASE ENGINE
# =============================================================================
DB_FILE = "india_disaster_data.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS citizens (phone TEXT UNIQUE, timestamp TEXT)')
        conn.commit()
        conn.close()
    except:
        pass

def save_citizen(phone):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('INSERT INTO citizens (phone, timestamp) VALUES (?, ?)', (phone, dt))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_all_citizens():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT phone FROM citizens')
        data = [row[0] for row in c.fetchall()]
        conn.close()
        return data
    except:
        return []

def check_connection():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=1)
        return True
    except OSError:
        return False

init_db()

# =============================================================================
# 2. MASTER CITY DATABASE & CONFIGURATION
# =============================================================================
CONFIG = {
    "APP_TITLE": "India Coastal Command",
    "TARGET_CITY": "Pan-India",
    "CENTER_COORDS": [78.9629, 20.5937],
    "VERSION_HASH": "v75.0-Official-Data-Integrated",
}

CITY_DATABASE = {
    "Mumbai": {
        "center": [72.8777, 19.0760],
        "zones": {
            "Borivali": {"lat_range": [19.225, 19.255], "lon_range": [72.835, 72.865], "density": 22100, "population": 232271},
            "Dahisar": {"lat_range": [19.245, 19.280], "lon_range": [72.845, 72.885], "density": 21500, "population": 351525},
            "Magathane": {"lat_range": [19.215, 19.245], "lon_range": [72.855, 72.895], "density": 19200, "population": 268992},
            "Mulund": {"lat_range": [19.155, 19.195], "lon_range": [72.935, 72.975], "density": 23400, "population": 437580},
            "Vikhroli": {"lat_range": [19.095, 19.135], "lon_range": [72.915, 72.945], "density": 24100, "population": 338123},
            "Bhandup West": {"lat_range": [19.135, 19.165], "lon_range": [72.925, 72.955], "density": 25800, "population": 319884},
            "Jogeshwari East": {"lat_range": [19.125, 19.145], "lon_range": [72.855, 72.885], "density": 28300, "population": 254584},
            "Dindoshi": {"lat_range": [19.165, 19.195], "lon_range": [72.855, 72.885], "density": 26200, "population": 250138},
            "Kandivali East": {"lat_range": [19.195, 19.225], "lon_range": [72.855, 72.885], "density": 27500, "population": 289025},
            "Charkop": {"lat_range": [19.195, 19.225], "lon_range": [72.825, 72.855], "density": 24800, "population": 260648},
            "Malad West": {"lat_range": [19.175, 19.205], "lon_range": [72.815, 72.845], "density": 25100, "population": 263801},
            "Goregaon": {"lat_range": [19.145, 19.175], "lon_range": [72.835, 72.865], "density": 23700, "population": 249324},
            "Versova": {"lat_range": [19.115, 19.145], "lon_range": [72.805, 72.835], "density": 21400, "population": 225128},
            "Andheri West": {"lat_range": [19.105, 19.135], "lon_range": [72.825, 72.855], "density": 26800, "population": 281936},
            "Andheri East": {"lat_range": [19.105, 19.135], "lon_range": [72.855, 72.885], "density": 22500, "population": 244064},
            "Vile Parle": {"lat_range": [19.085, 19.115], "lon_range": [72.835, 72.865], "density": 20900, "population": 219868},
            "Chandivali": {"lat_range": [19.105, 19.135], "lon_range": [72.885, 72.915], "density": 21200, "population": 286416},
            "Ghatkopar West": {"lat_range": [19.075, 19.105], "lon_range": [72.895, 72.925], "density": 28900, "population": 304317},
            "Ghatkopar East": {"lat_range": [19.065, 19.095], "lon_range": [72.905, 72.935], "density": 27400, "population": 288522},
            "Mankhurd Shivaj": {"lat_range": [19.045, 19.075], "lon_range": [72.915, 72.945], "density": 33500, "population": 352755},
            "Anushakti Nagar": {"lat_range": [19.025, 19.055], "lon_range": [72.915, 72.945], "density": 15200, "population": 273780},
            "Chembur": {"lat_range": [19.045, 19.065], "lon_range": [72.885, 72.915], "density": 22300, "population": 277992},
            "Kurla (SC)": {"lat_range": [19.055, 19.085], "lon_range": [72.865, 72.895], "density": 34200, "population": 360126},
            "Kalina": {"lat_range": [19.065, 19.095], "lon_range": [72.855, 72.885], "density": 25700, "population": 257985},
            "Vandre East": {"lat_range": [19.035, 19.065], "lon_range": [72.835, 72.865], "density": 26400, "population": 271674},
            "Vandre West": {"lat_range": [19.035, 19.075], "lon_range": [72.815, 72.845], "density": 24100, "population": 338364},
            "Dharavi (SC)": {"lat_range": [19.035, 19.055], "lon_range": [72.845, 72.865], "density": 35400, "population": 165672},
            "Sion Koliwada": {"lat_range": [19.025, 19.045], "lon_range": [72.865, 72.885], "density": 28100, "population": 221130},
            "Wadala": {"lat_range": [19.005, 19.025], "lon_range": [72.845, 72.875], "density": 26700, "population": 199368},
            "Mahim": {"lat_range": [19.015, 19.045], "lon_range": [72.835, 72.855], "density": 29300, "population": 205686},
            "Worli": {"lat_range": [18.995, 19.025], "lon_range": [72.815, 72.835], "density": 27800, "population": 195156},
            "Shivadi": {"lat_range": [18.985, 19.005], "lon_range": [72.835, 72.865], "density": 26100, "population": 186030},
            "Byculla": {"lat_range": [18.965, 18.985], "lon_range": [72.825, 72.845], "density": 32500, "population": 162864},
            "Malabar Hill": {"lat_range": [18.945, 18.975], "lon_range": [72.795, 72.815], "density": 18700, "population": 127946},
            "Mumbadevi": {"lat_range": [18.945, 18.965], "lon_range": [72.825, 72.835], "density": 42400, "population": 99216},
            "Colaba": {"lat_range": [18.895, 18.945], "lon_range": [72.805, 72.845], "density": 16300, "population": 381746},
        }
    },
    "Chennai": {
        "center": [80.2707, 13.0827],
        "zones": {
            "Dr. Radhakrishna": {"lat_range": [13.115, 13.145], "lon_range": [80.275, 80.305], "density": 29100, "population": 316317},
            "Perambur": {"lat_range": [13.105, 13.135], "lon_range": [80.245, 80.275], "density": 28600, "population": 310882},
            "Kolathur": {"lat_range": [13.115, 13.145], "lon_range": [80.205, 80.245], "density": 22300, "population": 288055},
            "Villivakkam": {"lat_range": [13.095, 13.115], "lon_range": [80.205, 80.235], "density": 25400, "population": 263054},
            "Thiru. Vi. Ka. Nar": {"lat_range": [13.085, 13.115], "lon_range": [80.245, 80.275], "density": 32500, "population": 353275},
            "Egmore (SC)": {"lat_range": [13.065, 13.095], "lon_range": [80.235, 80.265], "density": 24200, "population": 201550},
            "Royapuram": {"lat_range": [13.095, 13.125], "lon_range": [80.275, 80.305], "density": 30500, "population": 331535},
            "Harbour": {"lat_range": [13.085, 13.105], "lon_range": [80.275, 80.305], "density": 20100, "population": 145725},
            "Chepauk-Thiruva": {"lat_range": [13.055, 13.075], "lon_range": [80.265, 80.295], "density": 27300, "population": 213150},
            "Thousand Lights": {"lat_range": [13.045, 13.075], "lon_range": [80.235, 80.265], "density": 23400, "population": 254358},
            "Anna Nagar": {"lat_range": [13.075, 13.105], "lon_range": [80.205, 80.235], "density": 21800, "population": 273088},
            "Virugampakkam": {"lat_range": [13.045, 13.065], "lon_range": [80.185, 80.215], "density": 24500, "population": 189950},
            "Saidapet": {"lat_range": [13.005, 13.035], "lon_range": [80.215, 80.245], "density": 22200, "population": 196475},
            "Thiyagarayanaga": {"lat_range": [13.025, 13.055], "lon_range": [80.225, 80.255], "density": 26400, "population": 287232},
            "Mylapore": {"lat_range": [13.015, 13.045], "lon_range": [80.255, 80.285], "density": 25600, "population": 278528},
            "Velachery": {"lat_range": [12.965, 13.005], "lon_range": [80.215, 80.265], "density": 18500, "population": 447330}
        }
    },
    "Kolkata": {
        "center": [88.3639, 22.5726],
        "zones": {
            "Kolkata Port": {"lat_range": [22.525, 22.565], "lon_range": [88.285, 88.325], "density": 18500, "population": 338365},
            "Bhabanipur": {"lat_range": [22.525, 22.555], "lon_range": [88.335, 88.355], "density": 25400, "population": 174244},
            "Rashbehari": {"lat_range": [22.505, 22.535], "lon_range": [88.335, 88.365], "density": 23200, "population": 170128},
            "Ballygunge": {"lat_range": [22.515, 22.545], "lon_range": [88.355, 88.385], "density": 22800, "population": 159152},
            "Chowrangee": {"lat_range": [22.545, 22.575], "lon_range": [88.345, 88.365], "density": 20500, "population": 140630},
            "Entally": {"lat_range": [22.535, 22.565], "lon_range": [88.365, 88.395], "density": 26400, "population": 201684},
            "Beleghata": {"lat_range": [22.555, 22.585], "lon_range": [88.385, 88.415], "density": 25300, "population": 177100}, 
            "Jorasanko": {"lat_range": [22.575, 22.605], "lon_range": [88.355, 88.375], "density": 35600, "population": 244216},
            "Shyampukur": {"lat_range": [22.595, 22.615], "lon_range": [88.355, 88.385], "density": 32500, "population": 222950},
            "Maniktala": {"lat_range": [22.575, 22.605], "lon_range": [88.375, 88.405], "density": 28400, "population": 198800}, 
            "Kashipur-Belgacl": {"lat_range": [22.605, 22.635], "lon_range": [88.375, 88.405], "density": 24200, "population": 169400}, 
        }
    },
    "Surat": {
        "center": [72.8311, 21.1702],
        "zones": {
            "Olpad": {"lat_range": [21.255, 21.355], "lon_range": [72.755, 72.855], "density": 2500, "population": 288550},
            "Surat East": {"lat_range": [21.195, 21.215], "lon_range": [72.825, 72.845], "density": 28000, "population": 129360},
            "Surat North": {"lat_range": [21.215, 21.245], "lon_range": [72.815, 72.845], "density": 26500, "population": 265000}, 
            "Varachha Road": {"lat_range": [21.225, 21.255], "lon_range": [72.855, 72.895], "density": 29100, "population": 403326},
            "Karanj": {"lat_range": [21.215, 21.235], "lon_range": [72.865, 72.895], "density": 27800, "population": 278000}, 
            "Limbayat": {"lat_range": [21.165, 21.195], "lon_range": [72.855, 72.895], "density": 31200, "population": 432432},
            "Udhna": {"lat_range": [21.145, 21.175], "lon_range": [72.835, 72.865], "density": 30500, "population": 317200},
            "Majura": {"lat_range": [21.165, 21.195], "lon_range": [72.795, 72.825], "density": 18400, "population": 184000}, 
            "Katargam": {"lat_range": [21.235, 21.265], "lon_range": [72.815, 72.845], "density": 25600, "population": 256000}, 
            "Surat West": {"lat_range": [21.195, 21.225], "lon_range": [72.785, 72.815], "density": 19800, "population": 198000} 
        }
    },
    "Visakhapatnam": {
        "center": [83.2185, 17.6868],
        "zones": {
            "Bheemili": {"lat_range": [17.855, 17.955], "lon_range": [83.355, 83.455], "density": 1400, "population": 165046},
            "Visakhapatnam E": {"lat_range": [17.725, 17.755], "lon_range": [83.325, 83.355], "density": 12500, "population": 150000}, 
            "Visakhapatnam S": {"lat_range": [17.685, 17.725], "lon_range": [83.285, 83.325], "density": 15400, "population": 290444},
            "Visakhapatnam": {"lat_range": [17.735, 17.765], "lon_range": [83.295, 83.335], "density": 14200, "population": 160000}, 
            "Visakhapatnam V": {"lat_range": [17.705, 17.745], "lon_range": [83.225, 83.285], "density": 11300, "population": 120000}, 
            "Gajuwaka": {"lat_range": [17.655, 17.705], "lon_range": [83.185, 83.245], "density": 8400, "population": 297108}
        }
    },
    "Kochi": {
        "center": [76.2673, 9.9312],
        "zones": {
            "Vypeen": {"lat_range": [9.985, 10.055], "lon_range": [76.205, 76.255], "density": 4600, "population": 196604},
            "Kochi": {"lat_range": [9.935, 9.975], "lon_range": [76.225, 76.285], "density": 8800, "population": 257928},
            "Thrippunithura": {"lat_range": [9.925, 9.965], "lon_range": [76.325, 76.365], "density": 4200, "population": 150000}, 
            "Ernakulam": {"lat_range": [9.965, 10.025], "lon_range": [76.265, 76.315], "density": 9300, "population": 340659},
            "Thrikkakara": {"lat_range": [10.005, 10.055], "lon_range": [76.305, 76.365], "density": 3900, "population": 140000} 
        }
    },
    "Mangaluru": {
        "center": [74.8560, 12.9141],
        "zones": {
            "Mangalore City N": {"lat_range": [12.935, 13.005], "lon_range": [74.785, 74.855], "density": 3600, "population": 212760},
            "Mangalore City S": {"lat_range": [12.855, 12.925], "lon_range": [74.825, 74.885], "density": 5800, "population": 294060},
            "Mangalore (Ullal)": {"lat_range": [12.785, 12.845], "lon_range": [74.845, 74.905], "density": 2900, "population": 150000} 
        }
    },
    "Panaji": {
        "center": [73.8278, 15.4909],
        "zones": {
            "Panaji": {"lat_range": [15.485, 15.515], "lon_range": [73.815, 73.845], "density": 3200, "population": 34240},
            "Taleigao": {"lat_range": [15.455, 15.485], "lon_range": [73.805, 73.835], "density": 2800, "population": 29960}
        }
    },
    "Puducherry": {
        "center": [79.8144, 11.9416],
        "zones": {
            "Muthialpet": {"lat_range": [11.945, 11.965], "lon_range": [79.825, 79.845], "density": 15200, "population": 72960},
            "Raj Bhavan": {"lat_range": [11.925, 11.945], "lon_range": [79.825, 79.845], "density": 12500, "population": 60000},
            "Oupalam": {"lat_range": [11.915, 11.935], "lon_range": [79.815, 79.835], "density": 13800, "population": 65000}, 
            "Orleampeth": {"lat_range": [11.925, 11.945], "lon_range": [79.805, 79.825], "density": 14500, "population": 68000}, 
            "Nellithope": {"lat_range": [11.935, 11.955], "lon_range": [79.805, 79.825], "density": 14200, "population": 67000} 
        }
    },
    "Puri": {
        "center": [85.8315, 19.8135],
        "zones": {
            "Puri": {"lat_range": [19.785, 19.825], "lon_range": [85.805, 85.855], "density": 4500, "population": 104850}
        }
    }
}

# Dynamically construct INDIA_ZONES from CITY_DATABASE
INDIA_ZONES = {"All India": {"coords": [78.9629, 20.5937], "zoom": 4.0}}
for city, data in CITY_DATABASE.items():
    INDIA_ZONES[city] = {"coords": data["center"], "zoom": 11.5}


# --- COMPREHENSIVE TRANSLATIONS ---
TRANSLATIONS = {
    "en": {
        "app_title": "INDIA COASTAL COMMAND", "auth_req": "Authentication Required", "sel_lang": "Select Language", "sel_base": "Select Operations Base", "enter": "ENTER SYSTEM",
        "sb_title": "NDRF COMMAND", "sb_online": "🟢 ONLINE MODE", "sb_offline": "🔴 OFFLINE MODE", "sb_lang": "Language", "sb_base": "Base", "sb_users": "👥 Users in DB", "logout": "LOGOUT",
        "tab1": "🤖 AI Mission Control", "tab2": "🎛️ Simulation", "tab3": "🚀 Global Tactical Overview", "tab4": "⛑️ Zone Rescue",
        "t1_live": "🔴 LIVE SATELLITE FEED", "t1_status": "STATUS: ONLINE", "t1_pred": "📊 AI Atmospheric Prediction", "t1_low": "Predicted Low", "t1_prob": "Probability", "t1_imp": "Impact",
        "t1_reg": "🚨 Emergency Citizen Registry", "t1_phone": "Citizen Phone Number", "t1_save": "SAVE RECORD", "t1_recent": "Recent Database Entries", "t1_empty": "Database empty.",
        "t1_alert": "📡 Emergency Broadcast System", "t1_conf": "Configure Email Alert Settings", "t1_sender": "Sender Gmail", "t1_pass": "App Password", "t1_target": "Target Email", "t1_msg": "Alert Message", "t1_send_btn": "🔴 SEND EMERGENCY ALERT",
        "t2_param": "Parameters", "t2_pres": "Pressure (hPa)", "t2_wind": "Wind Speed (km/h)", "t2_proj": "Projected Outcome", "t2_min": "Simulated Min", "t2_risk": "Risk Level",
        "t3_layers": "Map Layers", "t3_heat": "Cyclone Heatmap", "t3_path": "Cyclone Path", "t3_pop": "Pop. Density", "t3_route": "Traffic Routes", "t3_safe": "Safe Radius",
        "t4_sel_city": "🏙️ Select City / Region", "t4_sel_zone": "📍 Select Specific Zone", "t4_ana": "Zone Analytics", "t4_cap": "Shelter Capacity", "t4_occ": "Current Occupancy", "t4_full": "Full", "t4_log": "📦 Logistics", "t4_wat": "💧 Water Needed", "t4_food": "🍞 Food Packets", "t4_act": "Active Shelters",
        "t4_pop": "Zone Population", "t4_cit": "Citizens", "t4_spa": "Spaces", "t4_peo": "People", "t4_no_data": "No real-world shelter data found for this specific area.", "t4_no_shelters": "No active shelters."
    },
    "hi": {
        "app_title": "भारत तटीय कमान", "auth_req": "प्रमाणीकरण आवश्यक", "sel_lang": "भाषा चुनें", "sel_base": "ऑपरेशन बेस चुनें", "enter": "सिस्टम में प्रवेश करें",
        "sb_title": "NDRF कमान", "sb_online": "🟢 ऑनलाइन मोड", "sb_offline": "🔴 ऑफलाइन मोड", "sb_lang": "भाषा", "sb_base": "बेस", "sb_users": "👥 डेटाबेस में उपयोगकर्ता", "logout": "लॉग आउट",
        "tab1": "🤖 AI मिशन नियंत्रण", "tab2": "🎛️ सिमुलेशन", "tab3": "🚀 वैश्विक सामरिक अवलोकन", "tab4": "⛑️ क्षेत्र बचाव",
        "t1_live": "🔴 लाइव सैटेलाइट फीड", "t1_status": "स्थिति: ऑनलाइन", "t1_pred": "📊 AI वायुमंडलीय भविष्यवाणी", "t1_low": "अनुमानित निम्न", "t1_prob": "संभावना", "t1_imp": "प्रभाव",
        "t1_reg": "🚨 आपातकालीन नागरिक रजिस्ट्री", "t1_phone": "नागरिक फोन नंबर", "t1_save": "रिकॉर्ड सहेजें", "t1_recent": "हालिया डेटाबेस प्रविष्टियां", "t1_empty": "डेटाबेस खाली है।",
        "t1_alert": "📡 आपातकालीन प्रसारण प्रणाली", "t1_conf": "ईमेल अलर्ट सेटिंग्स कॉन्फ़िगर करें", "t1_sender": "प्रेषक जीमेल", "t1_pass": "ऐप पासवर्ड", "t1_target": "लक्ष्य ईमेल", "t1_msg": "अलर्ट संदेश", "t1_send_btn": "🔴 आपातकालीन अलर्ट भेजें",
        "t2_param": "मापदंड", "t2_pres": "दबाव (hPa)", "t2_wind": "हवा की गति (किमी/घंटा)", "t2_proj": "अनुमानित परिणाम", "t2_min": "सिम्युलेटेड न्यूनतम", "t2_risk": "जोखिम स्तर",
        "t3_layers": "मानचित्र परतें", "t3_heat": "चक्रवात हीटमैप", "t3_path": "चक्रवात पथ", "t3_pop": "जनसंख्या घनत्व", "t3_route": "यातायात मार्ग", "t3_safe": "सुरक्षित त्रिज्या",
        "t4_sel_city": "🏙️ शहर / क्षेत्र चुनें", "t4_sel_zone": "📍 विशिष्ट क्षेत्र चुनें", "t4_ana": "क्षेत्र विश्लेषण", "t4_cap": "आश्रय क्षमता", "t4_occ": "वर्तमान अधिभोग", "t4_full": "भरा हुआ", "t4_log": "📦 रसद", "t4_wat": "💧 पानी की आवश्यकता", "t4_food": "🍞 भोजन के पैकेट", "t4_act": "सक्रिय आश्रय",
        "t4_pop": "क्षेत्र की जनसंख्या", "t4_cit": "नागरिक", "t4_spa": "स्थान", "t4_peo": "लोग", "t4_no_data": "इस विशिष्ट क्षेत्र के लिए कोई वास्तविक आश्रय डेटा नहीं मिला।", "t4_no_shelters": "कोई सक्रिय आश्रय नहीं।"
    },
    "te": {
        "app_title": "భారత తీరప్రాంత కమాండ్", "auth_req": "ప్రామాణీకరణ అవసరం", "sel_lang": "భాషను ఎంచుకోండి", "sel_base": "ఆపరేషన్స్ బేస్ ఎంచుకోండి", "enter": "సిస్టమ్‌లోకి ప్రవేశించండి",
        "sb_title": "NDRF కమాండ్", "sb_online": "🟢 ఆన్‌లైన్ మోడ్", "sb_offline": "🔴 ఆఫ్‌లైన్ మోడ్", "sb_lang": "భాష", "sb_base": "బేస్", "sb_users": "👥 DB లో వినియోగదారులు", "logout": "లాగ్అవుట్",
        "tab1": "🤖 AI మిషన్ కంట్రోల్", "tab2": "🎛️ అనుకరణ", "tab3": "🚀 గ్లోబల్ టాక్టికల్ ఓవర్‌వ్యూ", "tab4": "⛑️ జోన్ రెస్క్యూ",
        "t1_live": "🔴 లైవ్ శాటిలైట్ ఫీడ్", "t1_status": "స్థితి: ఆన్‌లైన్", "t1_pred": "📊 AI వాతావరణ అంచనా", "t1_low": "అంచనా వేయబడిన కనిష్టం", "t1_prob": "సంభావ్యత", "t1_imp": "ప్రభావం",
        "t1_reg": "🚨 అత్యవసర పౌర రిజిస్ట్రీ", "t1_phone": "పౌరుల ఫోన్ నంబర్", "t1_save": "రికార్డ్ సేవ్ చేయండి", "t1_recent": "ఇటీవలి డేటాబేస్ ఎంట్రీలు", "t1_empty": "డేటాబేస్ ఖాళీగా ఉంది.",
        "t1_alert": "📡 అత్యవసర ప్రసార వ్యవస్థ", "t1_conf": "ఇమెయిల్ హెచ్చరిక సెట్టింగ్‌లను కాన్ఫిగర్ చేయండి", "t1_sender": "పంపినవారి Gmail", "t1_pass": "యాప్ పాస్‌వర్డ్", "t1_target": "లక్ష్య ఇమెయిల్", "t1_msg": "హెచ్చరిక సందేశం", "t1_send_btn": "🔴 అత్యవసర హెచ్చరికను పంపండి",
        "t2_param": "పారామితులు", "t2_pres": "పీడనం (hPa)", "t2_wind": "గాలి వేగం (km/h)", "t2_proj": "అంచనా ఫలితం", "t2_min": "అనుకరణ కనిష్టం", "t2_risk": "ప్రమాద స్థాయి",
        "t3_layers": "మ్యాప్ లేయర్‌లు", "t3_heat": "సైక్లోన్ హీట్‌మ్యాప్", "t3_path": "సైక్లోన్ మార్గం", "t3_pop": "జనాభా సాంద్రత", "t3_route": "ట్రాఫిక్ మార్గాలు", "t3_safe": "సురక్షిత వ్యాసార్థం",
        "t4_sel_city": "🏙️ నగరం / ప్రాంతాన్ని ఎంచుకోండి", "t4_sel_zone": "📍 నిర్దిష్ట జోన్‌ను ఎంచుకోండి", "t4_ana": "జోన్ విశ్లేషణలు", "t4_cap": "ఆశ్రయ సామర్థ్యం", "t4_occ": "ప్రస్తుత ఆక్యుపెన్సీ", "t4_full": "పూర్తి", "t4_log": "📦 లాజిస్టిక్స్", "t4_wat": "💧 నీరు అవసరం", "t4_food": "🍞 ఆహార ప్యాకెట్లు", "t4_act": "క్రియాశీల ఆశ్రయాలు",
        "t4_pop": "జోన్ జనాభా", "t4_cit": "పౌరులు", "t4_spa": "ఖాళీలు", "t4_peo": "ప్రజలు", "t4_no_data": "ఈ నిర్దిష్ట ప్రాంతానికి వాస్తవ ప్రపంచ ఆశ్రయ డేటా కనుగొనబడలేదు.", "t4_no_shelters": "క్రియాశీల ఆశ్రయాలు లేవు."
    },
    "ta": {
        "app_title": "இந்திய கடலோரக் கட்டளை", "auth_req": "அங்கீகாரம் தேவை", "sel_lang": "மொழியைத் தேர்ந்தெடு", "sel_base": "செயல்பாட்டு தளத்தைத் தேர்ந்தெடு", "enter": "கணினியில் நுழைய",
        "sb_title": "NDRF கட்டளை", "sb_online": "🟢 ஆன்லைன் பயன்முறை", "sb_offline": "🔴 ஆஃப்லைன் பயன்முறை", "sb_lang": "மொழி", "sb_base": "தளம்", "sb_users": "👥 DB இல் பயனர்கள்", "logout": "வெளியேறு",
        "tab1": "🤖 AI பணி கட்டுப்பாடு", "tab2": "🎛️ உருவகப்படுத்துதல்", "tab3": "🚀 உலகளாவிய தந்திரோபாய கண்ணோட்டம்", "tab4": "⛑️ மண்டல மீட்பு",
        "t1_live": "🔴 நேரடி செயற்கைக்கோள் ஊட்டம்", "t1_status": "நிலை: ஆன்லைன்", "t1_pred": "📊 AI வளிமண்டல கணிப்பு", "t1_low": "கணிக்கப்பட்ட குறைவு", "t1_prob": "நிகழ்தகவு", "t1_imp": "தாக்கம்",
        "t1_reg": "🚨 அவசரகால குடிமக்கள் பதிவு", "t1_phone": "குடிமகன் தொலைபேசி எண்", "t1_save": "பதிவை சேமி", "t1_recent": "சமீபத்திய தரவுத்தள உள்ளீடுகள்", "t1_empty": "தரவுத்தளம் காலியாக உள்ளது.",
        "t1_alert": "📡 அவசர ஒளிபரப்பு அமைப்பு", "t1_conf": "மின்னஞ்சல் எச்சரிக்கை அமைப்புகளை உள்ளமைக்கவும்", "t1_sender": "அனுப்புநர் ஜிமெயில்", "t1_pass": "பயன்பாட்டு கடவுச்சொல்", "t1_target": "இலக்கு மின்னஞ்சல்", "t1_msg": "எச்சரிக்கை செய்தி", "t1_send_btn": "🔴 அவசர எச்சரிக்கையை அனுப்பு",
        "t2_param": "அளவுருக்கள்", "t2_pres": "அழுத்தம் (hPa)", "t2_wind": "காற்றின் வேகம் (km/h)", "t2_proj": "கணிக்கப்பட்ட முடிவு", "t2_min": "உருவகப்படுத்தப்பட்ட நிமிடம்", "t2_risk": "ஆபத்து நிலை",
        "t3_layers": "வரைபட அடுக்குகள்", "t3_heat": "சூறாவளி வெப்ப வரைபடம்", "t3_path": "சூறாவளி பாதை", "t3_pop": "மக்கள் தொகை அடர்த்தி", "t3_route": "போக்குவரத்து வழிகள்", "t3_safe": "பாதுகாப்பான ஆரம்",
        "t4_sel_city": "🏙️ நகரம் / பகுதியைத் தேர்ந்தெடுக்கவும்", "t4_sel_zone": "📍 குறிப்பிட்ட மண்டலத்தைத் தேர்ந்தெடுக்கவும்", "t4_ana": "மண்டல பகுப்பாய்வு", "t4_cap": "தங்குமிட திறன்", "t4_occ": "தற்போதைய ஆக்கிரமிப்பு", "t4_full": "முழுமையானது", "t4_log": "📦 தளவாடங்கள்", "t4_wat": "💧 தண்ணீர் தேவை", "t4_food": "🍞 உணவுப் பொட்டலங்கள்", "t4_act": "செயலில் உள்ள தங்குமிடங்கள்",
        "t4_pop": "மண்டல மக்கள் தொகை", "t4_cit": "குடிமக்கள்", "t4_spa": "இடங்கள்", "t4_peo": "மக்கள்", "t4_no_data": "இந்தக் குறிப்பிட்ட பகுதிக்கான உண்மையான தங்குமிடத் தரவு எதுவும் கிடைக்கவில்லை.", "t4_no_shelters": "செயலில் உள்ள தங்குமிடங்கள் இல்லை."
    },
    "bn": {
        "app_title": "ইন্ডিয়া কোস্টাল কমান্ড", "auth_req": "প্রমাণীকরণ প্রয়োজন", "sel_lang": "ভাষা নির্বাচন করুন", "sel_base": "অপারেশন বেস নির্বাচন করুন", "enter": "সিস্টেমে প্রবেশ করুন",
        "sb_title": "NDRF কমান্ড", "sb_online": "🟢 অনলাইন মোড", "sb_offline": "🔴 অফলাইন মোড", "sb_lang": "ভাষা", "sb_base": "বেস", "sb_users": "👥 ডিবিতে ব্যবহারকারী", "logout": "লগআউট",
        "tab1": "🤖 এআই মিশন কন্ট্রোল", "tab2": "🎛️ সিমুলেশন", "tab3": "🚀 গ্লোবাল ট্যাকটিক্যাল ওভারভিউ", "tab4": "⛑️ জোন রেসকিউ",
        "t1_live": "🔴 লাইভ স্যাটেলাইট ফিড", "t1_status": "স্ট্যাটাস: অনলাইন", "t1_pred": "📊 এআই বায়ুমণ্ডলীয় পূর্বাভাস", "t1_low": "পূর্বাভাসিত নিম্ন", "t1_prob": "সম্ভাবনা", "t1_imp": "প্রভাব",
        "t1_reg": "🚨 জরুরী নাগরিক রেজিস্ট্রি", "t1_phone": "নাগরিক ফোন নম্বর", "t1_save": "রেকর্ড সংরক্ষণ করুন", "t1_recent": "সাম্প্রতিক ডাটাবেস এন্ট্রি", "t1_empty": "ডাটাবেস খালি।",
        "t1_alert": "📡 জরুরী সম্প্রচার ব্যবস্থা", "t1_conf": "ইমেল সতর্কতা সেটিংস কনফিগার করুন", "t1_sender": "প্রেরক জিমেইল", "t1_pass": "অ্যাপ পাসওয়ার্ড", "t1_target": "লক্ষ্য ইমেল", "t1_msg": "সতর্কতা বার্তা", "t1_send_btn": "🔴 জরুরী সতর্কতা পাঠান",
        "t2_param": "পরামিতি", "t2_pres": "চাপ (hPa)", "t2_wind": "বাতাসের গতি (কিমি/ঘন্টা)", "t2_proj": "প্রক্ষিপ্ত ফলাফল", "t2_min": "সিমুলেটেড ন্যূনতম", "t2_risk": "ঝুঁকির স্তর",
        "t3_layers": "ম্যাপ লেয়ার", "t3_heat": "ঘূর্ণিঝড় হিটম্যাপ", "t3_path": "ঘূর্ণিঝড়ের পথ", "t3_pop": "জনসংখ্যার ঘনত্ব", "t3_route": "ট্র্যাফিক রুট", "t3_safe": "নিরাপদ ব্যাসার্ধ",
        "t4_sel_city": "🏙️ শহর / অঞ্চল নির্বাচন করুন", "t4_sel_zone": "📍 নির্দিষ্ট জোন নির্বাচন করুন", "t4_ana": "জোন বিশ্লেষণ", "t4_cap": "আশ্রয় ক্ষমতা", "t4_occ": "বর্তমান দখল", "t4_full": "পূর্ণ", "t4_log": "📦 লজিস্টিকস", "t4_wat": "💧 জল প্রয়োজন", "t4_food": "🍞 খাবারের প্যাকেট", "t4_act": "সক্রিয় আশ্রয়কেন্দ্র",
        "t4_pop": "জোন জনসংখ্যা", "t4_cit": "নাগরিক", "t4_spa": "স্থান", "t4_peo": "মানুষ", "t4_no_data": "এই নির্দিষ্ট এলাকার জন্য কোন বাস্তব-জগতের আশ্রয় তথ্য পাওয়া যায়নি।", "t4_no_shelters": "কোনো সক্রিয় আশ্রয়কেন্দ্র নেই।"
    }
}

LANG_MAP = {
    "English": "en", "Hindi (हिन्दी)": "hi", "Telugu (తెలుగు)": "te", "Tamil (தமிழ்)": "ta", "Bengali (বাংলা)": "bn"
}

st.set_page_config(page_title="India Coastal Command", page_icon="🌪️", layout="wide", initial_sidebar_state="expanded")

# --- Safety: define tab placeholders to avoid NameError if blocks shift ---
tab1 = tab2 = tab3 = tab4 = st.container()


# CSS STYLING
st.markdown("""
<style>
    .stApp { background-color: #050505; color: #e0e0e0; font-family: 'Roboto', sans-serif; }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01));
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px;
    }
    .stButton button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%); 
        color: white; border: none; border-radius: 6px; font-weight: bold; width: 100%;
        text-transform: uppercase; letter-spacing: 1px;
    }
    div[data-testid="stExpander"] { border: 1px solid rgba(0, 255, 0, 0.3); border-radius: 10px; background-color: #0e1117; }
    h1, h2, h3 { color: #ffffff; }
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 3. DATA LOADERS & HELPER LOGIC
# =============================================================================

if 'app_mode' not in st.session_state: st.session_state['app_mode'] = 'login'
if 'lang_code' not in st.session_state: st.session_state['lang_code'] = "en"
if 'sim_time' not in st.session_state: st.session_state['sim_time'] = 0
if 'user_city' not in st.session_state: st.session_state['user_city'] = "All India"

def get_txt(key):
    code = st.session_state['lang_code']
    lang_dict = TRANSLATIONS.get(code, TRANSLATIONS['en'])
    return lang_dict.get(key, TRANSLATIONS['en'].get(key, key))

@st.cache_data
def load_real_shelters():
    try:
        # Load the newly generated CSV from the OSMnx/NBC pipeline
        df = pd.read_csv("india_shelters.csv")
        
        # Add visual columns for PyDeck mapping
        df['height'] = df['capacity']  
        df['color'] = df.apply(lambda _: [0, 255, 128, 255], axis=1) # Green
        
        # Make sure occupancy exists in case it was missed in export
        if 'occupancy' not in df.columns:
            df['occupancy'] = 0
            
        # Map population from the CITY_DATABASE
        def get_zone_pop(row):
            city = row['city']
            zone = row['zone']
            if city in CITY_DATABASE and zone in CITY_DATABASE[city]["zones"]:
                return CITY_DATABASE[city]["zones"][zone].get("population", 0)
            return 0
            
        df['population'] = df.apply(get_zone_pop, axis=1)
        return df

    except FileNotFoundError:
        st.error("🚨 Critical Error: 'india_shelters.csv' not found. Please run the nbc_shelter_generator.py script first.")
        # Return an empty dataframe with correct columns to prevent the app from crashing entirely
        return pd.DataFrame(columns=['city', 'zone', 'label', 'lat', 'lon', 'capacity', 'occupancy', 'height', 'color', 'population'])

# Bind it to the variable used by the map
india_shelter_registry = load_real_shelters()

def render_geospatial_heatmap(offset=0):
    data = []
    center = [87.5 - (offset * 0.05), 18.0 + (offset * 0.05)] 
    for _ in range(300):
        data.append([center[0] + random.gauss(0, 1.5), center[1] + random.gauss(0, 1.5), random.uniform(0.5, 1.0)])
    return pd.DataFrame(data, columns=['lon', 'lat', 'weight'])

def generate_cyclone_path(offset=0):
    shift = offset * 0.1
    return [[89.0 - shift, 15.0 + shift], [88.5 - shift, 15.5 + shift], [88.0 - shift, 16.0 + shift]]

def generate_population_data(city_name="All India"):
    data = []
    if city_name == "All India" or city_name not in CITY_DATABASE:
        for _ in range(300):
            lat = 20.0 + random.uniform(-5, 5)
            lon = 78.0 + random.uniform(-5, 5)
            data.append([lon, lat])
    else:
        city_data = CITY_DATABASE[city_name]
        for zone_name, zone_info in city_data["zones"].items():
            points_to_render = int(zone_info["density"] / 150) 
            for _ in range(points_to_render):
                lat = random.uniform(zone_info["lat_range"][0], zone_info["lat_range"][1])
                lon = random.uniform(zone_info["lon_range"][0], zone_info["lon_range"][1])
                data.append([lon, lat])
                
    return pd.DataFrame(data, columns=['lon', 'lat'])

def generate_traffic_routes(center_lat, center_lon):
    routes = []
    for _ in range(10):
        start = [center_lon + random.uniform(-0.05, 0.05), center_lat + random.uniform(-0.05, 0.05)]
        end = [center_lon + random.uniform(-0.05, 0.05), center_lat + random.uniform(-0.05, 0.05)]
        routes.append({"path": [start, end], "color": [255, 0, 0] if random.random() > 0.7 else [0, 255, 255]})
    return routes

def generate_safe_radius(center_lat, center_lon):
    return [{"lon": center_lon, "lat": center_lat, "radius": 5000}]

def execute_physics_simulation(base_p, is_auto=False):
    times, vals = [], []
    curr = base_p + random.uniform(-2, 2)
    trend = -0.8 if is_auto else -0.5
    for i in range(24): 
        times.append((datetime.now() + timedelta(hours=i)).strftime("%H:%M"))
        curr += (trend + random.uniform(-0.3, 0.3))
        if curr < 880: curr = 880
        vals.append(curr)
    return pd.DataFrame({"Time": times, "Pressure": vals})

def send_email_alert(sender_email, app_password, receiver_email, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = "🚨 NATIONAL ALERT: EMERGENCY BROADCAST"
        msg['From'] = sender_email
        msg['To'] = receiver_email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return True, "✅ Alert Broadcasted Successfully"
    except Exception as e:
        return False, f"❌ Broadcast Failed: {str(e)}"

# =============================================================================
# 4. APP UI
# =============================================================================

if st.session_state['app_mode'] == 'login':
    st.container()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/561/561127.png", width=100)
        st.title(get_txt('app_title'))
        st.markdown(f"### {get_txt('auth_req')}")
        
        choice = st.selectbox(get_txt('sel_lang'), list(LANG_MAP.keys()), key="login_lang_selector")
        
        city_list = sorted([k for k in INDIA_ZONES.keys() if k != "All India"])
        city_list.insert(0, "All India")
        selected_base = st.selectbox(get_txt('sel_base'), city_list, key="login_city_selector")
        
        if st.button(get_txt('enter'), key="login_btn_enter", width="stretch"):
            st.session_state['lang_code'] = LANG_MAP[choice]
            st.session_state['user_city'] = selected_base
            st.session_state['app_mode'] = 'dashboard'
            st.rerun()

else:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/561/561127.png", width=60)
        st.title(get_txt('sb_title'))
        
        if check_connection():
            st.success(get_txt('sb_online'))
        else:
            st.error(get_txt('sb_offline'))
            
        st.caption(f"{get_txt('sb_lang')}: {st.session_state['lang_code']}")
        st.info(f"⚓ {get_txt('sb_base')}: {st.session_state['user_city']}")
        try:
            count = len(get_all_citizens())
            st.metric(get_txt('sb_users'), count)
        except:
            st.metric(get_txt('sb_users'), 0)
        st.markdown("---")
        if st.button(get_txt('logout'), key="sidebar_logout_btn"):
            st.session_state['app_mode'] = 'login'
            st.rerun()

    live_p = 1008
    tab1, tab2, tab3, tab4 = st.tabs([get_txt('tab1'), get_txt('tab2'), get_txt('tab3'), get_txt('tab4')])

    # TAB 1: MISSION CONTROL
    with tab1:
        st.markdown(f"### {get_txt('t1_live')}")
        live_mode = st.toggle(get_txt('t1_status'), value=False, key="live_mode_toggle")
        
        if live_mode:
            time.sleep(1.5)
            st.session_state['sim_time'] += 1
            st.rerun()
            
        st.markdown("---")
        st.subheader(f"{get_txt('t1_pred')}")
        
        atmospheric_data_df = execute_physics_simulation(live_p, is_auto=True)
        min_p = atmospheric_data_df['Pressure'].min()
        
        prob_val = 0
        if min_p < 1000:
            prob_val = (1000 - min_p) * 0.9 
            if prob_val > 99: prob_val = 99
            
        cat_val = "CAT 1"
        if min_p < 965: cat_val = "CAT 2"
        if min_p < 945: cat_val = "CAT 3"
        if min_p < 920: cat_val = "CAT 4"
        if min_p < 900: cat_val = "CAT 5"

        c1, c2, c3 = st.columns(3)
        c1.metric(get_txt('t1_low'), f"{min_p:.1f} hPa", "-24 hPa", delta_color="inverse")
        c2.metric(get_txt('t1_prob'), f"{prob_val:.1f}%", "+8%")
        c3.metric(get_txt('t1_imp'), cat_val, "Severe")
        st.line_chart(atmospheric_data_df.set_index("Time")["Pressure"], color="#00d4ff")

        # =====================================
        # 🤖 AI 6-HOUR CYCLONE FORECAST (PyTorch LSTM)
        # =====================================
        st.markdown("---")
        st.subheader("🤖 AI 6-Hour Cyclone Forecast (LSTM)")

        # Demo-friendly defaults from the simulated atmosphere series
        try:
            default_pressure = float(atmospheric_data_df["Pressure"].min())
        except Exception:
            default_pressure = 1000.0
        default_wind = float(max(0.0, (1013.0 - default_pressure) * 1.5))

        cA, cB, cC = st.columns(3)
        with cA:
            ai_lat = st.number_input("Latitude (°)", value=float(CONFIG["CENTER_COORDS"][1]), format="%.3f", key="ai_lat")
            ai_pres = st.number_input("Pressure (hPa)", value=default_pressure, step=1.0, key="ai_pres")
        with cB:
            ai_lon = st.number_input("Longitude (°)", value=float(CONFIG["CENTER_COORDS"][0]), format="%.3f", key="ai_lon")
            ai_wind = st.number_input("Wind (knots)", value=default_wind, step=1.0, key="ai_wind")
        with cC:
            ai_ptrend = st.number_input("Pressure trend (Δ per 6h)", value=0.0, step=0.5, key="ai_ptrend")
            ai_wtrend = st.number_input("Wind trend (Δ per 6h)", value=0.0, step=0.5, key="ai_wtrend")

        if st.button("🚀 Predict 6H Forecast", width="stretch", key="btn_predict_6h"):
            input_data = {
                "LAT": float(ai_lat),
                "LON": float(ai_lon),
                "USA_WIND": float(ai_wind),
                "USA_PRES": float(ai_pres),
                "pressure_trend": float(ai_ptrend),
                "wind_trend": float(ai_wtrend),
            }

            try:
                result = predict_6h(input_data)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Future Pressure (hPa)", f"{result['future_pressure']:.1f}")
                m2.metric("Future Wind (knots)", f"{result['future_wind']:.1f}")
                m3.metric("Future Lat", f"{result['future_lat']:.3f}")
                m4.metric("Future Lon", f"{result['future_lon']:.3f}")

                if result["future_wind"] >= 64:
                    st.error("🔴 HIGH RISK: Severe Cyclone possible in ~6 hours")
                elif result["future_wind"] >= 34:
                    st.warning("🟠 MODERATE RISK: Storm strengthening")
                else:
                    st.success("🟢 LOW RISK: Weak system")

                # Map: current vs predicted using PyDeck (matches app style)
                map_df = pd.DataFrame([
                    {"name": "Current", "lat": float(ai_lat), "lon": float(ai_lon), "size": 9000, "r": 0, "g": 160, "b": 255},
                    {"name": "Predicted (6h)", "lat": float(result["future_lat"]), "lon": float(result["future_lon"]), "size": 11000, "r": 255, "g": 60, "b": 60},
                ])

                st.pydeck_chart(pdk.Deck(
                    map_style=None,
                    initial_view_state=pdk.ViewState(
                        latitude=float(ai_lat),
                        longitude=float(ai_lon),
                        zoom=5.5,
                        pitch=35
                    ),
                    layers=[
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=map_df,
                            get_position=["lon", "lat"],
                            get_radius="size",
                            get_fill_color=["r", "g", "b"],
                            pickable=True,
                        )
                    ],
                    tooltip={"text": "{name}\nLat: {lat}\nLon: {lon}"}
                ))
            except Exception as e:
                st.error(f"Prediction failed: {e}")


        st.markdown("---")
        st.subheader(f"{get_txt('t1_reg')}")
        
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            phone_entry = st.text_input(get_txt('t1_phone'), placeholder="+91 99999 99999", key="db_phone_input")
        with col_btn:
            st.write("") 
            st.write("") 
            if st.button(get_txt('t1_save'), width="stretch"):
                if len(phone_entry) >= 10:
                    if save_citizen(phone_entry):
                        st.success(f"✅ Saved")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("⚠️ Exists")
                else:
                    st.error("❌ Invalid")

        st.caption(get_txt('t1_recent'))
        try:
            conn = sqlite3.connect(DB_FILE)
            df_db = pd.read_sql_query("SELECT * FROM citizens ORDER BY timestamp DESC LIMIT 5", conn)
            conn.close()
            if not df_db.empty:
                st.dataframe(df_db, width="stretch", hide_index=True)
            else:
                st.info(get_txt('t1_empty'))
        except:
            st.error("DB Error")

        st.markdown("---")
        st.subheader(f"{get_txt('t1_alert')}")
        with st.expander(get_txt('t1_conf'), expanded=True):
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                sender_mail = st.text_input(get_txt('t1_sender'), placeholder="your_email@gmail.com")
            with e_col2:
                app_pass = st.text_input(get_txt('t1_pass'), type="password")
            target_mail = st.text_input(get_txt('t1_target'), placeholder="rescue_team@example.com")
            alert_msg = st.text_area(get_txt('t1_msg'), value="URGENT: Cyclone Alert Level CAT 1.", height=100)
            if st.button(get_txt('t1_send_btn'), width="stretch"):
                if check_connection():
                    if sender_mail and app_pass and target_mail:
                        with st.spinner("Sending..."):
                            success, resp_msg = send_email_alert(sender_mail, app_pass, target_mail, alert_msg)
                            if success: st.success(resp_msg)
                            else: st.error(resp_msg)
                    else:
                        st.warning("⚠️ Fill credentials.")
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        with open("offline_outbox.txt", "a") as f:
                            f.write(f"[{timestamp}] QUEUED | TO: {target_mail} | MSG: {alert_msg}\n")
                        st.success(f"✅ Alert Saved to Offline Outbox.")
                    except Exception as e:
                        st.error(f"Write Error: {e}")

    # TAB 2: SIMULATION
    with tab2:
        st.subheader(get_txt('tab2'))
        c1, c2 = st.columns([1,3])
        with c1:
            st.markdown(f"### {get_txt('t2_param')}")
            sim_p = st.slider(get_txt('t2_pres'), 880, 1050, live_p, key="sim_p_slider")
            sim_w = st.slider(get_txt('t2_wind'), 0, 250, 120, key="sim_w_slider")
        with c2:
            st.markdown(f"### {get_txt('t2_proj')}")
            df_sim = execute_physics_simulation(sim_p)
            st.line_chart(df_sim.set_index("Time")["Pressure"], color="#ff4b4b")
            m1, m2 = st.columns(2)
            m1.metric(get_txt('t2_min'), f"{df_sim['Pressure'].min():.1f} hPa")
            risk_txt = "EXTREME" if sim_w > 180 else "HIGH"
            m2.metric(get_txt('t2_risk'), risk_txt)

    # TAB 3: GLOBAL TACTICAL OVERVIEW
    with tab3:
        st.subheader(f"🚀 {get_txt('tab3')}")
        c_layers, c_map = st.columns([1, 4])
        with c_layers:
            st.markdown(f"### {get_txt('t3_layers')}")
            show_heat = st.checkbox(get_txt('t3_heat'), True)
            show_path = st.checkbox(get_txt('t3_path'), True)
            show_hex = st.checkbox(get_txt('t3_pop'), True)
            show_routes = st.checkbox(get_txt('t3_route'), True)
            show_safe = st.checkbox(get_txt('t3_safe'), True)
            
        with c_map:
            layers = []
            t_offset = st.session_state['sim_time'] % 15
            
            # 1. Base Shelter Columns (Now pulling from the highly accurate india_shelter_registry)
            if not india_shelter_registry.empty:
                layers.append(pdk.Layer("ColumnLayer", data=india_shelter_registry, get_position=["lon", "lat"], get_elevation="height", radius=2000, get_fill_color=[0, 255, 100, 255], elevation_scale=5, extruded=True, pickable=True, auto_highlight=True))

            # 2. Heatmap
            if show_heat:
                 layers.append(pdk.Layer("HeatmapLayer", data=render_geospatial_heatmap(t_offset), get_position=['lon', 'lat'], get_weight="weight", radiusPixels=50, opacity=0.6))
            
            # 3. Cyclone Path
            if show_path:
                 layers.append(pdk.Layer("PathLayer", data=[{"path": generate_cyclone_path(t_offset), "color": [255, 165, 0]}], get_path="path", get_color="color", width_scale=20, width_min_pixels=3))
            
            # 4. Hexagon Pop Density
            if show_hex:
                 layers.append(pdk.Layer("HexagonLayer", data=generate_population_data(st.session_state['user_city']), get_position=['lon', 'lat'], radius=200 if st.session_state['user_city'] != "All India" else 20000, elevation_scale=10, elevation_range=[0, 1000], pickable=True, extruded=True))
            
            # 5. Traffic Routes
            if show_routes:
                city_d = INDIA_ZONES.get(st.session_state['user_city'], INDIA_ZONES["All India"])
                traffic_data = generate_traffic_routes(city_d["coords"][1], city_d["coords"][0])
                layers.append(pdk.Layer("PathLayer", data=traffic_data, get_path="path", get_color="color", width_scale=20, width_min_pixels=2))

            # 6. Safe Radius
            if show_safe:
                city_d = INDIA_ZONES.get(st.session_state['user_city'], INDIA_ZONES["All India"])
                safe_data = generate_safe_radius(city_d["coords"][1], city_d["coords"][0])
                layers.append(pdk.Layer("ScatterplotLayer", data=safe_data, get_position=["lon", "lat"], get_radius="radius", get_fill_color=[0, 0, 0, 0], get_line_color=[0, 255, 0], stroked=True, line_width_min_pixels=2))

            # Dynamic Centering
            map_lat = CONFIG["CENTER_COORDS"][1]
            map_lon = CONFIG["CENTER_COORDS"][0]
            map_zoom = 4.5
            
            if st.session_state['user_city'] != "All India":
                city_data = INDIA_ZONES.get(st.session_state['user_city'])
                if city_data:
                    map_lat = city_data["coords"][1]
                    map_lon = city_data["coords"][0]
                    map_zoom = city_data["zoom"]

            st.pydeck_chart(pdk.Deck(
                map_style=None, 
                initial_view_state=pdk.ViewState(latitude=map_lat, longitude=map_lon, zoom=map_zoom, pitch=50), 
                layers=layers
            ))
            st.caption("ℹ️ Tactical Vector Mode active (High Contrast).")

    # TAB 4: RESCUE (NEW CASCADING LOGIC WITH REAL DATA)
    with tab4:
        st.subheader(f"⛑️ {get_txt('tab4')}")
        
        # 1. City / Region Select
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            city_options = ["All India"] + sorted(list(CITY_DATABASE.keys()))
            user_home_base = st.session_state.get('user_city', "All India")
            default_city_idx = city_options.index(user_home_base) if user_home_base in city_options else 0
            
            selected_city = st.selectbox(get_txt('t4_sel_city'), city_options, index=default_city_idx, key="tab4_city_select")
            
        # 2. Zone Select (Dynamic based on City)
        with col_sel2:
            if selected_city == "All India":
                zone_options = ["All Zones"]
            else:
                zone_options = ["All Zones"] + sorted(list(CITY_DATABASE[selected_city]["zones"].keys()))
            
            selected_zone = st.selectbox(get_txt('t4_sel_zone'), zone_options, key="tab4_subzone_select")
            
        # 3. Filtering Data & Adjusting Viewport
        if selected_city == "All India":
            zone_subset = india_shelter_registry
            view_zoom = 4.5
            view_lat = CONFIG["CENTER_COORDS"][1]
            view_lon = CONFIG["CENTER_COORDS"][0]
            display_title = "Pan-India Data"
        else:
            if selected_zone == "All Zones":
                zone_subset = india_shelter_registry[india_shelter_registry['city'] == selected_city]
                view_zoom = INDIA_ZONES[selected_city]["zoom"]
                view_lat = INDIA_ZONES[selected_city]["coords"][1]
                view_lon = INDIA_ZONES[selected_city]["coords"][0]
                display_title = f"{selected_city} (All Zones)"
            else:
                zone_subset = india_shelter_registry[(india_shelter_registry['city'] == selected_city) & (india_shelter_registry['zone'] == selected_zone)]
                z_data = CITY_DATABASE[selected_city]["zones"][selected_zone]
                view_zoom = 13.5 
                view_lat = sum(z_data["lat_range"]) / 2.0
                view_lon = sum(z_data["lon_range"]) / 2.0
                display_title = f"{selected_city} - {selected_zone}"

        col_map, col_stats = st.columns([3, 1])

        with col_map:
            if not zone_subset.empty:
                rescue_layers = [
                    pdk.Layer("ColumnLayer", data=zone_subset, get_position=["lon", "lat"], get_elevation="height", radius=800 if selected_zone != "All Zones" else 1500, get_fill_color=[0, 255, 128, 255], elevation_scale=10 if selected_zone != "All Zones" else 10, extruded=True, pickable=True),
                    pdk.Layer("ScatterplotLayer", data=zone_subset, get_position=["lon", "lat"], get_radius=1500 if selected_zone != "All Zones" else 3000, get_fill_color=[0, 255, 255, 30], stroked=True, get_line_color=[0, 255, 255, 200], line_width_min_pixels=2),
                    pdk.Layer("TextLayer", data=zone_subset, get_position=["lon", "lat"], get_text="label", get_color=[255, 255, 255], get_size=16, get_angle=0, get_text_anchor="middle", get_alignment_baseline="center")
                ]
                
                st.pydeck_chart(pdk.Deck(
                    map_style=None,
                    initial_view_state=pdk.ViewState(latitude=view_lat, longitude=view_lon, zoom=view_zoom, pitch=45),
                    layers=rescue_layers,
                    tooltip={"html": "<b>Shelter:</b> {label}<br/><b>Capacity:</b> {capacity}<br/><b>Zone Population:</b> {population}", "style": {"color": "white"}}
                ))
            else:
                st.warning(get_txt('t4_no_data'))

        with col_stats:
            st.markdown(f"### {get_txt('t4_ana')}")
            st.info(f"📍 {display_title}")
            
            # --- POPULATION & CAPACITY CALCULATION LOGIC ---
            if selected_city == "All India":
                total_pop = sum(z.get("population", 0) for c in CITY_DATABASE.values() for z in c["zones"].values())
            elif selected_zone == "All Zones":
                total_pop = sum(z.get("population", 0) for z in CITY_DATABASE[selected_city]["zones"].values())
            else:
                total_pop = CITY_DATABASE[selected_city]["zones"][selected_zone].get("population", 0)

            total_cap = zone_subset['capacity'].sum() if not zone_subset.empty else 0
            total_occ = zone_subset['occupancy'].sum() if not zone_subset.empty else 0
            
            st.metric(get_txt('t4_pop'), f"{total_pop:,} {get_txt('t4_cit')}")
            st.metric(get_txt('t4_cap'), f"{total_cap:,} {get_txt('t4_spa')}")
            st.metric(get_txt('t4_occ'), f"{total_occ:,} {get_txt('t4_peo')}")
            
            perc = (total_occ / total_cap) * 100 if total_cap > 0 else 0
            st.progress(min(int(perc), 100))
            st.caption(f"{perc:.1f}% {get_txt('t4_full')}")
            
            st.markdown("---")
            st.markdown(f"### {get_txt('t4_log')}")
            req_water = total_occ * 3
            req_food = total_occ * 2
            st.metric(get_txt('t4_wat'), f"{req_water:,} L")
            st.metric(get_txt('t4_food'), f"{req_food:,} Pkts")
            
            st.markdown("---")
            st.write(f"**{get_txt('t4_act')}:**")
            if not zone_subset.empty:
                st.dataframe(zone_subset[['zone', 'label', 'capacity', 'population']], width="stretch", hide_index=True)
            else:
                st.write(get_txt('t4_no_shelters'))
