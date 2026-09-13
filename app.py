import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import os
import re
import sqlite3
import requests
from datetime import datetime

st.set_page_config(
    page_title="MOBA FT 330 & FL 330 AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# ----------------------------------------------------
# 1. SAMBUNGAN GOOGLE INTERACTIONS API (GEMINI-3.8-FLASH)
# ----------------------------------------------------
raw_api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
if not raw_api_key:
    st.error("API Key Gemini tidak ditemui! Sila semak GEMINI_API_KEY dalam Streamlit Secrets.")
    st.stop()

CLEAN_API_KEY = str(raw_api_key).strip().strip('"').strip("'")

def extract_text_from_response(data):
    """Mengekstrak teks respons secara selamat tanpa mengira hierarki JSON (dict/list)."""
    if isinstance(data, list):
        for entry in data:
            res = extract_text_from_response(entry)
            if res:
                return res
        return None

    if isinstance(data, dict):
        # Semak kunci teks terus
        if "output_text" in data and isinstance(data["output_text"], str):
            return data["output_text"]
        if data.get("type") == "text" and "text" in data:
            return data["text"]

        # Semak struktur steps -> model_output (Interactions API)
        steps = data.get("steps")
        if isinstance(steps, list):
            for step in reversed(steps):
                if isinstance(step, dict) and step.get("type") == "model_output":
                    content = step.get("content")
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("text"):
                                return item.get("text")
                            elif isinstance(item, str):
                                return item
                    elif isinstance(content, str):
                        return content
                elif isinstance(step, (dict, list)):
                    res = extract_text_from_response(step)
                    if res:
                        return res

        # Semak struktur standard candidates -> parts
        candidates = data.get("candidates")
        if isinstance(candidates, list) and len(candidates) > 0:
            first_cand = candidates[0]
            if isinstance(first_cand, dict):
                parts = first_cand.get("content", {}).get("parts", [])
                if isinstance(parts, list):
                    for p in parts:
                        if isinstance(p, dict) and "text" in p:
                            return p["text"]

        # Carian rekursif pada setiap nilai dictionary
        for val in data.values():
            if isinstance(val, (dict, list)):
                res = extract_text_from_response(val)
                if res:
                    return res

    return None

def call_gemini_api(full_prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    headers = {
        "x-goog-api-key": CLEAN_API_KEY,
        "Content-Type": "application/json",
        "Api-Revision": "2026-05-20"
    }
    payload = {
        "model": "gemini-3.8-flash",
        "input": full_prompt
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=45)
    
    if response.status_code == 200:
        data = response.json()
        extracted_text = extract_text_from_response(data)
        if extracted_text:
            return extracted_text
        return f"Respons diterima tetapi struktur teks tidak dijangka:\n\n```json\n{data}\n
