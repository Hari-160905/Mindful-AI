import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
import os
import json

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="Mindful AI", page_icon="🌙")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-latest')

# Create a CSV file to store data if it doesn't exist
DB_FILE = "mood_history.csv"
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["Date", "Mood", "Score"])
    df.to_csv(DB_FILE, index=False)

# Mood to Score mapping for the chart
MOOD_MAP = {"Sad": 1, "Anxious": 2, "Neutral": 3, "Productive": 4, "Happy": 5}

# --- 2. THE AI LOGIC ---
def analyze_entry(text):
    prompt = f"""Analyze this journal entry: "{text}". 
    Return ONLY a JSON-style response: {{"response": "empathetic text", "mood": "One-word Mood", "score": 1-5}}
    Moods: Happy(5), Productive(4), Neutral(3), Anxious(2), Sad(1)."""
    
    raw_res = model.generate_content(prompt)
    
    # Clean the text: Remove markdown code blocks (```json and ```)
    clean_text = raw_res.text.replace("```json", "").replace("```", "").strip()
    
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        # Fallback in case the model adds extra conversational text
        import re
        match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        else:
            # Emergency fallback if everything fails
            return {"response": "I'm having trouble processing that, but I'm here for you.", "mood": "Neutral", "score": 3}

# --- 3. UI LAYOUT ---
st.title("🌙 Mindful AI Journal")

tab1, tab2 = st.tabs(["Today's Entry", "Mood History"])

with tab1:
    user_input = st.text_area("What's on your mind?", height=150)
    if st.button("Submit Reflection"):
        if user_input:
            with st.spinner("Reflecting..."):
                result = analyze_entry(user_input)
                
                # Show AI Response
                st.write(f"### ✨ AI Reflection")
                st.write(result['response'])
                
                # Save to CSV
                new_data = pd.DataFrame([[datetime.date.today(), result['mood'], result['score']]], 
                                        columns=["Date", "Mood", "Score"])
                new_data.to_csv(DB_FILE, mode='a', header=False, index=False)
                st.success(f"Log saved as: {result['mood']}")
        else:
            st.warning("Write something first!")

with tab2:
    st.header("Your Journey")
    history_df = pd.read_csv(DB_FILE)
    
    if not history_df.empty:
        # Display the trend chart
        st.line_chart(history_df.set_index("Date")["Score"])
        
        # Show recent entries
        st.table(history_df.tail(5))
    else:
        st.write("No history yet. Start writing!")