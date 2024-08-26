# app.py

import streamlit as st
from streamlit_option_menu import option_menu
from database import get_leaderboard, save_user_xp, verify_user, get_user_data, save_session, update_user_answers_and_factors, get_evaluation_scores, update_user_lexile_level, create_user, get_user_xp
from lexile import adjust_lexile_level, display_lexile_scale, evaluate_answers
from content_generation import generate_content_and_mcqs
from config import EVALUATION_FACTORS, TOPICS, DIFFICULTY_LEVELS, DIFFICULTY_TO_LEXILE
import time

# Custom CSS
st.markdown("""
<style>
    :root {
        --primary-color: #F7BC31;
        --secondary-color: #F9F6ED;
        --accent-green: #03A77F;
        --accent-blue: #26C8E1;
        --accent-lilac: #AB7FD3;
        --accent-red: #F35A2D;
        --accent-pink: #FBD9DB;
        --text-color: #03A77F;
    }

    body {
        color: var(--text-color);
        background-color: var(--secondary-color);
    }

    .stApp > header {
        background-color: var(--primary-color);
    }

    .stButton>button {
        color: white;
        background-color: var(--accent-green);
        border-radius: 20px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }

    .stProgress > div > div > div {
        background-color: var(--accent-blue);
    }

    .metric-box {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: var(--accent-lilac);
    }

    .metric-label {
        font-size: 14px;
        font-weight: bold;
        color: var(--text-color);
    }

    .leaderboard-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
        background-color: var(--secondary-color);
    }

    .leaderboard-item span {
        color: var(--text-color);
    }

    .leaderboard-item:nth-child(odd) {
        background-color: rgba(255, 255, 255, 0.1);
    }

    .leaderboard-item:hover {
        background-color: rgba(255, 255, 255, 0.2);
        transition: background-color 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("Lexile Learning Adventure")

    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    # Login/Registration Page
    if st.session_state.page == 'login':
        login_register()
    
    # Main Application
    elif st.session_state.page == 'main':
        if 'user_xp' not in st.session_state:
            st.session_state.user_xp = get_user_xp(st.session_state.user_id)
        # Sidebar navigation
        with st.sidebar:
            selected = option_menu(
                "Main Menu",
                ["Dashboard", "Lexile Test", "Leaderboard"],
                icons=['house', 'book', 'trophy'],
                menu_icon="cast",
                default_index=0,
            )

        if selected == "Dashboard":
            display_dashboard()
        elif selected == "Lexile Test":
            run_lexile_test()
        elif selected == "Leaderboard":
            display_leaderboard()

        # Logout button
        if st.sidebar.button("Logout", key="logout_button"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def login_register():
    st.header("Welcome to Lexile Learning Adventure")
    
    login_tab, register_tab = st.tabs(["Login", "Register"])
    
    with login_tab:
        student_id = st.text_input("Student ID", key="login_student_id")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_button"):
            if student_id and password:
                user_id, verified = verify_user(student_id, password)
                if verified:
                    st.session_state.user_id = user_id
                    user_data = get_user_data(user_id)
                    st.session_state.current_lexile = user_data['lexile_level']
                    st.session_state.user_xp = get_user_xp(user_id)  # Store XP in session state
                    st.session_state.page = 'main'
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid student ID or password. Please try again.")
            else:
                st.error("Please enter both student ID and password.")
    
    with register_tab:
        new_student_id = st.text_input("New Student ID", key="register_student_id")
        new_password = st.text_input("New Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=5, max_value=18, value=10)
        
        if st.button("Register", key="register_button"):
            if new_student_id and new_password and confirm_password and name and age:
                if new_password == confirm_password:
                    user_id = create_user(new_student_id, new_password, name, age)
                    if user_id:
                        st.success("Registration successful! Please log in with your new credentials.")
                    else:
                        st.error("Student ID already exists. Please choose a different one.")
                else:
                    st.error("Passwords do not match. Please try again.")
            else:
                st.error("Please fill in all fields.")

def display_dashboard():
    user_data = get_user_data(st.session_state.user_id)
    st.header(f"Welcome, {user_data['name']}!")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{st.session_state.current_lexile}L</div>
            <div class="metric-label">Your Lexile</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        xp = get_user_xp(st.session_state.user_id)
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{xp} XP</div>
            <div class="metric-label">Total XP</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        streak = 5  # Replace with actual streak calculation if you have this feature
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{streak} days</div>
            <div class="metric-label">Current Streak</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.subheader("Evaluation Scores:")
    scores = get_evaluation_scores(st.session_state.user_id)
    
    # Create two columns for evaluation factors
    col1, col2 = st.columns(2)
    
    for i, factor in enumerate(EVALUATION_FACTORS):
        score = scores.get(factor, 0)  # Default to 0 if score is not found
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <div style="font-weight: bold;">{factor}</div>
                <div style="background-color: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="width: {score}%; height: 100%; background-color: var(--accent-blue);"></div>
                </div>
                <div style="text-align: right;">{score}%</div>
            </div>
            """, unsafe_allow_html=True)

def display_leaderboard():
    st.header("Leaderboard")
    leaderboard_data = get_leaderboard()
    if leaderboard_data:
        for i, entry in enumerate(leaderboard_data, 1):
            st.markdown(f"""
            <div class="leaderboard-item">
                <span>{i}. {entry['name']}</span>
                <span>{entry['xp']} XP</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("No leaderboard data available. Complete a test to see your ranking!")

def display_results(xp, time_taken, accuracy):
    st.header("Test Completed!")
    
    time_display = f"{time_taken:.1f} seconds" if time_taken < 60 else f"{int(time_taken // 60)} min {int(time_taken % 60)} sec"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{xp} ⚡</div>
            <div class="metric-label">TOTAL XP</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{time_display} ⏱️</div>
            <div class="metric-label">TIME TAKEN</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{accuracy}% 🎯</div>
            <div class="metric-label">ACCURACY</div>
        </div>
        """, unsafe_allow_html=True)


def calculate_xp_reward(accuracy, time_taken, question_count):
    base_xp = 20
    
    # Accuracy-based XP calculation
    if accuracy < 20:
        xp = 0
    elif accuracy < 40:
        xp = 5
    elif accuracy < 60:
        xp = 10
    elif accuracy < 80:
        xp = 15
    else:
        xp = base_xp

    # Perfect score bonus
    if accuracy == 100:
        xp += 10

    # Time bonus calculation
    average_time_per_question = 5  # Assuming 5 seconds per question is average
    expected_time = average_time_per_question * question_count
    if time_taken < expected_time:
        time_bonus = min(10, int((expected_time - time_taken) / 10))  # Max 10 XP bonus for time
        xp += time_bonus

    return xp

def run_lexile_test():
    st.header("Lexile Test")
    
    topic = st.selectbox("Select a topic", TOPICS)
    difficulty = st.selectbox("Select Difficulty Level", DIFFICULTY_LEVELS)

    if 'test_start_time' not in st.session_state:
        st.session_state.test_start_time = None 

    with st.form(key='test_form'):
        if st.form_submit_button("Start New Test"):
            st.session_state.answers_submitted = False
            st.session_state.xp_claimed = False
            st.session_state.test_start_time = time.time()
            with st.spinner("Generating test content..."):
                lexile_range = DIFFICULTY_TO_LEXILE[difficulty]
                target_lexile = (lexile_range[0] + lexile_range[1]) // 2

                st.session_state.content, st.session_state.questions = generate_content_and_mcqs(
                    get_user_data(st.session_state.user_id)['age'], 
                    topic, 
                    target_lexile
                )
            
                if st.session_state.content is None or st.session_state.questions is None:
                    st.error("Failed to generate content. Please try again.")
                else:
                    st.session_state.session_id = save_session(
                        st.session_state.user_id,
                        topic,
                        target_lexile,
                        st.session_state.content
                    )

        if st.session_state.get('content') and st.session_state.get('questions') and not st.session_state.get('answers_submitted', False):
            st.subheader("Read the following passage:")
            st.write(st.session_state.content)

            st.subheader("Answer the questions:")
            user_answers = []
            start_time = time.time()
            for i, q in enumerate(st.session_state.questions, 1):
                st.write(f"{i}. {q['text']}")
                options = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(q['options'])]
                answer = st.radio(f"Question {i}", options, key=f"q{i}")
                user_answers.append(answer[0])

            if st.form_submit_button("Submit Answers"):
                end_time = time.time()
                if st.session_state.test_start_time:
                    time_taken = end_time - st.session_state.test_start_time
                else:
                    time_taken = 0
                
                scores, percentage_correct = evaluate_answers(st.session_state.questions, user_answers)
                
                update_user_answers_and_factors(
                    st.session_state.user_id,
                    user_answers,
                    st.session_state.questions
                )
                
                old_lexile = st.session_state.current_lexile
                new_lexile = adjust_lexile_level(old_lexile, percentage_correct)
                st.session_state.current_lexile = new_lexile
                update_user_lexile_level(st.session_state.user_id, new_lexile)
                
                xp_earned = calculate_xp_reward(percentage_correct, time_taken, len(st.session_state.questions))
                
                st.session_state.answers_submitted = True
                st.session_state.old_lexile = old_lexile
                st.session_state.new_lexile = new_lexile
                st.session_state.percentage_correct = percentage_correct
                st.session_state.user_answers = user_answers
                st.session_state.total_xp = xp_earned
                st.session_state.time_taken = time_taken

    if st.session_state.get('answers_submitted', False) and not st.session_state.get('xp_claimed', False):
        display_results(st.session_state.total_xp, st.session_state.time_taken, round(st.session_state.percentage_correct))
        st.button("CLAIM XP", on_click=claim_xp_callback, type="primary")

    if st.session_state.get('xp_claimed', False):
        st.success(f"You have claimed {st.session_state.total_xp} XP for this session.")

def claim_xp_callback():
    if not st.session_state.xp_claimed and st.session_state.answers_submitted:
        xp_id = save_user_xp(st.session_state.user_id, st.session_state.total_xp, st.session_state.session_id)
        if xp_id:
            st.session_state.xp_claimed = True
            st.session_state.user_xp += st.session_state.total_xp  # Update session state XP
            st.success(f"XP claimed successfully! You earned {st.session_state.total_xp} XP.")
            
            # Check if user has earned enough XP to increase Lexile Level
            if st.session_state.user_xp >= 100:
                lexile_increase = st.session_state.user_xp // 100
                new_lexile = st.session_state.current_lexile + lexile_increase
                update_user_lexile_level(st.session_state.user_id, new_lexile)
                st.session_state.current_lexile = new_lexile
                st.session_state.user_xp %= 100  # Reset XP, keeping remainder
                st.success(f"Congratulations! Your Lexile Level has increased to {new_lexile}L!")
        else:
            st.error("Failed to claim XP. Please try again.")


if __name__ == "__main__":
    main()
