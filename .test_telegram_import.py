#!/usr/bin/env python3
"""Test telegram import"""
try:
    import telegram
    print(f"✅ python-telegram-bot is working: {telegram.__version__}")
except ImportError as e:
    print(f"❌ Import error: {e}")
