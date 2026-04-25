import streamlit as st
import pandas as pd
import random
import requests
import html
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor

# =====================
# API QUESTIONS (DOMAIN BASED)
# =====================
def fetch_api_questions(domain, amount=5):

    if domain == "Computer Science":
        url = f"https://opentdb.com/api.php?amount={amount}&category=18&type=multiple"
    else:
        url = f"https://opentdb.com/api.php?amount={amount}&type=multiple"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        api_questions = []

        for item in data["results"]:
            q_text = html.unescape(item["question"])
            correct = html.unescape(item["correct_answer"])
            options = [html.unescape(opt) for opt in item["incorrect_answers"]]
            options.append(correct)
            random.shuffle(options)

            api_questions.append({
                "q": q_text,
                "options": options,
                "answer": correct,
                "skill": domain,
                "difficulty": 2
            })

        return api_questions

    except:
        return []

# =====================
# LOCAL QUESTION BANK
# =====================
question_bank = {
    "Python": [
        {"q": "What is 2+2?", "options": ["2","4"], "answer": "4", "difficulty": 1},
        {"q": "Keyword to define function?", "options": ["def","func"], "answer": "def", "difficulty": 1}
    ],
    "DSA": [
        {"q": "FIFO?", "options": ["Stack","Queue"], "answer": "Queue", "difficulty": 1},
        {"q": "Binary Search complexity?", "options": ["O(n)","O(log n)"], "answer": "O(log n)", "difficulty": 2}
    ],
    "DBMS": [
        {"q": "Primary key is?", "options": ["Unique","Duplicate"], "answer": "Unique", "difficulty": 1}
    ]
}

# =====================
# GENERATE QUESTIONS (HYBRID)
# =====================
def generate_questions(domain, n=10):

    all_q = []

    # Local
    if domain in question_bank:
        for q in question_bank[domain]:
            q_copy = q.copy()
            q_copy["skill"] = domain
            all_q.append(q_copy)

    # API
    api_q = fetch_api_questions("Computer Science" if domain != "General" else "General", 10)
    all_q.extend(api_q)

    # Remove duplicates by question text
    unique_q = {q["q"]: q for q in all_q}.values()
    all_q = list(unique_q)

    # Fill if less
    while len(all_q) < n:
        if domain in question_bank:
            extra = random.choice(question_bank[domain]).copy()
            extra["skill"] = domain
            all_q.append(extra)
        else:
            break

    random.shuffle(all_q)
    return all_q[:n]

# =====================
# UI CONFIG
# =====================
st.set_page_config(page_title="Skill Gap AI", layout="wide")

st.markdown("""
<div style='background:linear-gradient(135deg,#1e293b,#0f172a);
padding:25px;border-radius:12px;text-align:center;color:white;
font-size:28px;font-weight:bold;'>
🎯 Skill Gap Intelligence Engine (AI Powered)
</div>
""", unsafe_allow_html=True)

# =====================
# SESSION STATE
# =====================
if "page" not in st.session_state:
    st.session_state.page = 1
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = []
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "domain" not in st.session_state:
    st.session_state.domain = "Python"

# =====================
# PAGE 1 (INPUT)
# =====================
if st.session_state.page == 1:

    st.header("Start Quiz")

    name = st.text_input("Enter Name")

    domain = st.selectbox("Select Domain", [
        "Python",
        "DSA",
        "DBMS",
        "General"
    ])

    st.session_state.domain = domain

    if st.button("Start Quiz"):

        st.session_state.questions = generate_questions(domain)
        st.session_state.page = 2

    st.stop()

# =====================
# PAGE 2 (QUIZ)
# =====================
if st.session_state.page == 2:

    q = st.session_state.questions[st.session_state.current_q]

    st.subheader(f"Question {st.session_state.current_q + 1}")

    st.markdown(f"**{q['q']}**")
    st.caption(f"Domain: {q['skill']} | Difficulty: {q['difficulty']}")

    ans = st.radio("Choose answer:", q["options"], key=str(st.session_state.current_q))

    if st.button("Next"):

        st.session_state.answers.append({
            "skill": q["skill"],
            "correct": 1 if ans == q["answer"] else 0
        })

        if st.session_state.current_q < len(st.session_state.questions) - 1:
            st.session_state.current_q += 1
        else:
            st.session_state.page = 3

    st.progress((st.session_state.current_q + 1) / len(st.session_state.questions))

    st.stop()

# =====================
# PAGE 3 (RESULTS)
# =====================
if st.session_state.page == 3:

    df = pd.DataFrame(st.session_state.answers)

    st.success("Quiz Completed 🎉")

    skill_acc = df.groupby("skill")["correct"].mean()

    st.subheader("Skill Performance")
    st.bar_chart(skill_acc)

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Accuracy", f"{df['correct'].mean()*100:.1f}%")
    col2.metric("Total Questions", len(df))
    col3.metric("Weak Skills", len(skill_acc[skill_acc < 0.6]))

    # Clustering
    if len(df) > 3:
        kmeans = KMeans(n_clusters=2, random_state=42)
        df["cluster"] = kmeans.fit_predict(df[["correct"]])

        st.subheader("Cluster Analysis")
        st.dataframe(df)

    # ML Model
    if len(df) > 3:
        model = RandomForestRegressor()
        X = df[["correct"]]
        y = df["correct"]
        model.fit(X, y)

        st.subheader("Feature Importance")
        st.write(model.feature_importances_)

    # Recommendation
    weak = skill_acc[skill_acc < 0.6]

    st.subheader("Recommendation")
    if len(weak) > 0:
        st.error(f"Focus on: {', '.join(weak.index)}")
    else:
        st.success("Excellent Performance 🚀")

    if st.button("Restart"):
        st.session_state.page = 1
        st.session_state.current_q = 0
        st.session_state.answers = []