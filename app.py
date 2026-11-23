# language: Python, file: app.py
import os
import requests
import threading
import discord
from discord.ext import commands
from flask import Flask, request, render_template_string

app = Flask(__name__)

# 1. YOUR WEBHOOK IS SET
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# 2. PUT YOUR BOT TOKEN HERE (Do not share this)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# 3. YOUR RAILWAY DOMAIN
RAILWAY_URL = "https://rnbw-production.up.railway.app"
