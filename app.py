import streamlit as st
from streamlit_option_menu import option_menu
from database import get_leaderboard, get_session_question, get_user_leaderboard_range, save_session_questions, save_user_xp, update_user_streak, verify_user, get_user_data, save_session, update_user_answers_and_factors, get_evaluation_scores, update_user_lexile_level, create_user, get_user_xp
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
        --duolingo-green: #58CC02;
        -duolingo-red: #FF4B4B;
        --duolingo-blue: #1CB0F6;
        --duolingo-yellow: #FFC800;
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
        transition: background-color 0.3s ease;
        width: 100%;
        max-width: 300px;
    }

    .stButton>button:hover {
        background-color: var(--accent-red);
        color: var(--secondary-color);
    }
            
    .stButton>button:selected {
        background-color: #C35A2A;
        color: var(--secondary-color);
    }

    .stProgress > div > div > div {
        background-color: var(--accent-blue);
    }

    .metric-box {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 10px;
    }

    .metric-value {
        font-size: 20px;
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
        color: var(--secondary-color);
        font-size: 16px;
    }

    .leaderboard-item:nth-child(odd) {
        background-color: rgba(255, 255, 255, 0.1);
    }

    .leaderboard-item:hover {
        background-color: rgba(255, 255, 255, 0.2);
        transition: background-color 0.3s ease;
    }

    .evaluation-factor {
        margin-bottom: 10px;
    }

    .evaluation-factor-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        font-size: 14px;
    }

    .evaluation-factor-progress {
        height: 15px;
        background-color: #e0e0e0;
        border-radius: 7.5px;
        overflow: hidden;
    }

    .evaluation-factor-bar {
        height: 100%;
        background-color: var(--accent-blue);
        transition: width 0.5s ease-in-out;
    }

    .lexile-progress {
        height: 20px;
        background-color: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
    }
            
    .lexile-bar-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        font-size: 14px;
    }

    .lexile-bar {
        height: 100%;
        background-color: var(--accent-green);
        transition: width 0.5s ease-in-out;
    }
            
    .option-button {
        display: inline-block;
        padding: 0.5em 1em;
        margin: 0.5em 0;
        width: 100%;
        background-color: black !important;
        color: white;
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 0.25rem;
        text-align: center;
        text-decoration: none;
        font-size: 1em;
        cursor: pointer;
    }
    .option-button:hover {
        border-color: #000000;
        background-color: #0a0a0b !important;
    }
    }
    .option-button.correct {
        background-color: #28a475;
        border-color: #28a430;
        color: white !important;
    }
    .option-button.incorrect {
        background-color: #dc3545;
        border-color: #dc3530;
        color: white !important;
    }
    .streak-badge {
        background-color: #ffd700;
        color: #000;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
    }

    /* Mobile-specific styles */
    @media (max-width: 768px) {
        .stButton>button {
            padding: 8px 16px;
            font-size: 14px;
        }

        .metric-box {
            padding: 10px;
        }

        .metric-value {
            font-size: 18px;
        }

        .metric-label {
            font-size: 12px;
        }

        .leaderboard-item span {
            font-size: 12px;
        }

        .evaluation-factor-label {
            font-size: 12px;
        }

        .evaluation-factor-progress {
            height: 12px;
            border-radius: 6px;
        }

        .lexile-progress {
            height: 15px;
            border-radius: 7.5px;
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("LexiLeap: Lexile Learning Adventure")

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
                styles={
                    "container": {"padding": "5px"},
                    "icon": {"color": "orange", "font-size": "20px"}, 
                    "nav-link": {
                        "fontSize": "14px", 
                        "textAlign": "left", 
                        "margin": "0px", 
                        "--hover-color": "#000000", 
                    },
                    "nav-link-selected": {"background-color": "#02ab21"},
                }
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
    st.header("Welcome to LexiLeap")
    
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
                    st.session_state.user_xp = get_user_xp(user_id)
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

    user_data = get_user_data(st.session_state.user_id)
    if user_data is None:
        st.error("Failed to load user data. Please try logging in again.")
        return

    st.header(f"Welcome, {user_data['name']}!")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{user_data['lexile_level']}L</div>
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
        streak = user_data.get('streak', 0)
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">
                <span class="streak-badge">{streak} 🔥</span>
            </div>
            <div class="metric-label">Day Streak</div>
        </div>
        """, unsafe_allow_html=True)

    # Display Lexile progress bar
    range_start, range_end = get_user_leaderboard_range(st.session_state.user_id)
    if range_start is None or range_end is None:
        st.warning("Take the Lexile Test to see your Lexile Level on the Leaderboard.")
    else:
        lexile_range = range_end - range_start
        current_lexile = user_data['lexile_level']
        progress = (current_lexile - range_start) / lexile_range

        st.markdown(f"""
        <br></br>
        <div class="lexile-bar-label">
            <span>{range_start}L</span>
            <span>{range_end}L</span>
        </div>
        <div class="lexile-progress">
            <div class="lexile-bar" style="width: {progress*100}%;"></div>
        </div>
        <br></br>
        """, unsafe_allow_html=True)
    
    st.subheader("Evaluation Scores:")
    scores = get_evaluation_scores(st.session_state.user_id)
    
    for factor in EVALUATION_FACTORS:
        score = scores.get(factor, 0)
        st.markdown(f"""
        <div class="evaluation-factor">
            <div class="evaluation-factor-label">
                <span>{factor}</span>
                <span>{score}/3</span>
            </div>
            <div class="evaluation-factor-progress">
                <div class="evaluation-factor-bar" style="width: {(score/3)*100}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Debug print to check if the correct values are being displayed
    print(f"User Data: {user_data}")
    print(f"Evaluation Scores: {scores}")

    
def display_leaderboard():
    st.header("Leaderboard")
    leaderboard_data = get_leaderboard(st.session_state.user_id)
    
    range_start, range_end = get_user_leaderboard_range(st.session_state.user_id)
    st.markdown(f"### Your Lexile Range: {range_start}L - {range_end}L")
    
    if leaderboard_data:
        for i, entry in enumerate(leaderboard_data, 1):
            st.markdown(f"""
            <div class="leaderboard-item">
                <span>{i}. {entry['name']}</span>
                <span>{entry['xp']} XP</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("No leaderboard data available for your Lexile range.")




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

    # Debug print to check if the correct values are being passed
    print(f"XP: {xp}, Time Taken: {time_display}, Accuracy: {accuracy}%")


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

    print(f"Calculated XP: {xp}, Accuracy: {accuracy}, Time Taken: {time_taken}, Question Count: {question_count}")

    return xp


def option_button(label, key, is_correct, is_selected):
    class_name = "option-button"
    if is_selected:
        class_name += " correct" if is_correct else " incorrect"
    return st.markdown(f'<button class="{class_name}" name="{key}">{label}</button>', unsafe_allow_html=True)

def run_lexile_test():
    st.header("Lexile Test")

    # Initialize session state variables
    if 'total_xp' not in st.session_state:
        st.session_state.total_xp = 0
    if 'time_taken' not in st.session_state:
        st.session_state.time_taken = 0
    if 'percentage_correct' not in st.session_state:
        st.session_state.percentage_correct = 0
    if 'test_completed' not in st.session_state:
        st.session_state.test_completed = False
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 1
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = []
    if 'answer_selected' not in st.session_state:
        st.session_state.answer_selected = False
    if 'answers_submitted' not in st.session_state:
        st.session_state.answers_submitted = False
    
    if not st.session_state.answers_submitted:
        topic = st.selectbox("Select a topic", TOPICS)
        difficulty = st.selectbox("Select Difficulty Level", DIFFICULTY_LEVELS)

        if 'test_start_time' not in st.session_state:
            st.session_state.test_start_time = None 

        if st.button("Start New Test"):
            st.session_state.answers_submitted = False
            st.session_state.xp_claimed = False
            st.session_state.test_start_time = time.time()
            st.session_state.user_answers = []
            st.session_state.current_question = 1
            st.session_state.answer_selected = False
            
            with st.spinner("Generating test content..."):
                lexile_range = DIFFICULTY_TO_LEXILE[difficulty]
                target_lexile = (lexile_range[0] + lexile_range[1]) // 2

                evaluation_scores = get_evaluation_scores(st.session_state.user_id)
                st.session_state.content, questions = generate_content_and_mcqs(
                    get_user_data(st.session_state.user_id)['age'], 
                    topic, 
                    target_lexile,
                    evaluation_scores
                )
            
                if st.session_state.content is None or questions is None:
                    st.error("Failed to generate content. Please try again.")
                else:
                    session_id = save_session(
                        st.session_state.user_id,
                        topic,
                        target_lexile,
                        st.session_state.content
                    )
                    if session_id:
                        st.session_state.session_id = session_id
                        if save_session_questions(session_id, questions):
                            print("Test content generated successfully!")
                        else:
                            st.error("Failed to save questions. Please try again.")
                    else:
                        st.error("Failed to save session. Please try again.")

        if hasattr(st.session_state, 'content') and hasattr(st.session_state, 'session_id'):
            st.subheader("Read the following passage:")
            st.write(st.session_state.content)

            st.subheader("Answer the questions:")
            current_question = get_session_question(st.session_state.session_id, st.session_state.current_question)
            
            if current_question:
                st.write(f"{st.session_state.current_question}. {current_question['question_text']}")
                options = [current_question[f'option_{opt}'] for opt in ['a', 'b', 'c', 'd']]
                
                col1, col2 = st.columns(2)
                for i, (col, option) in enumerate(zip([col1, col1, col2, col2], options)):
                    option_letter = chr(65 + i)  # A, B, C, or D
                    is_correct = current_question['correct_answer'] == option_letter
                    is_selected = st.session_state.answer_selected and len(st.session_state.user_answers) == st.session_state.current_question and st.session_state.user_answers[-1] == option_letter
                    
                    button_class = "option-button"
                    if st.session_state.answer_selected:
                        button_class += " correct" if is_correct else " incorrect"
                    
                    if col.button(option, key=f"q{st.session_state.current_question}{chr(97+i)}", disabled=st.session_state.answer_selected, type="primary" if is_selected else "secondary"):
                        st.session_state.user_answers.append(option_letter)
                        st.session_state.answer_selected = True
                        st.rerun()
                    
                    # Apply the CSS class after the button is created
                    st.markdown(f"""
                    <style>
                        div.stButton > button:nth-child(1)[key=q{st.session_state.current_question}{chr(97+i)}] {{
                            {f"background-color: {'#28a475' if is_correct else '#dc3545'};" if st.session_state.answer_selected else ""}
                            color: {'white' if st.session_state.answer_selected else 'inherit'};
                        }}
                    </style>
                    """, unsafe_allow_html=True)

                if st.session_state.answer_selected:
                    if st.session_state.current_question < 5:
                        if st.button("Next Question"):
                            st.session_state.current_question += 1
                            st.session_state.answer_selected = False
                            st.rerun()
                    else:
                        if st.button("Submit Answers"):
                            st.session_state.answers_submitted = True
                            end_time = time.time()
                            time_taken = end_time - st.session_state.test_start_time if st.session_state.test_start_time else 0
                            
                            # Retrieve all questions for this session
                            all_questions = [get_session_question(st.session_state.session_id, i) for i in range(1, 6)]

                            print(f"User Answers: {st.session_state.user_answers}")
                            print(f"All Questions: {all_questions}")

                            scores, percentage_correct = evaluate_answers(st.session_state.session_id, st.session_state.user_answers)
                            
                            update_user_answers_and_factors(
                                st.session_state.user_id,
                                st.session_state.user_answers,
                                st.session_state.session_id
                            )
                            
                            old_lexile = st.session_state.current_lexile
                            new_lexile = adjust_lexile_level(old_lexile, percentage_correct)
                            st.session_state.current_lexile = new_lexile
                            update_user_lexile_level(st.session_state.user_id, new_lexile)
                            
                            xp_earned = calculate_xp_reward(percentage_correct, time_taken, len(st.session_state.user_answers))
                            
                            st.session_state.old_lexile = old_lexile
                            st.session_state.new_lexile = new_lexile
                            st.session_state.percentage_correct = percentage_correct
                            st.session_state.total_xp = xp_earned
                            st.session_state.time_taken = time_taken
                            st.session_state.test_completed = True

                            # Update user streak
                            update_user_streak(st.session_state.user_id)
                            
                            st.rerun()
            else:
                st.write("No more questions.")

    if st.session_state.answers_submitted:
        display_results(st.session_state.total_xp, st.session_state.time_taken, round(st.session_state.percentage_correct))
        st.button("CLAIM XP", on_click=claim_xp_callback, type="primary")


def claim_xp_callback():
    if not st.session_state.xp_claimed and st.session_state.answers_submitted:
        session_id = st.session_state.get('session_id')
        if not session_id:
            st.error("Session ID is missing. Cannot claim XP.")
            return
        xp_id = save_user_xp(st.session_state.user_id, st.session_state.total_xp, st.session_state.session_id)
        if xp_id:
            st.session_state.xp_claimed = True
            st.session_state.user_xp += st.session_state.total_xp  # Update session state XP
            st.success(f"You earned {st.session_state.total_xp} XP.")
            
            # Check if user has earned enough XP to increase Lexile Level
            if st.session_state.user_xp >= 100:
                lexile_increase = st.session_state.user_xp // 100
                new_lexile = st.session_state.current_lexile + lexile_increase
                update_user_lexile_level(st.session_state.user_id, new_lexile)
                st.session_state.current_lexile = new_lexile
                st.session_state.user_xp %= 100  # Reset XP, keeping remainder
                
                # Check if the new Lexile level has crossed the upper bound of the current range
                range_start, range_end = get_user_leaderboard_range(st.session_state.user_id)
                if new_lexile >= range_end:
                    st.success(f"Congratulations! You've advanced to a new Lexile range: {range_end}L to {range_end + 100}L")
                else:
                    st.success(f"Congratulations! Your Lexile Level has increased to {new_lexile}L!")
        else:
            st.error("Failed to claim XP. Please try again.")
    
    # Reset the test state
    st.session_state.answers_submitted = False
    st.session_state.xp_claimed = False
    st.session_state.test_start_time = None
    st.session_state.user_answers = []
    st.session_state.current_question = 1
    st.session_state.answer_selected = False
    st.session_state.content = None
    st.session_state.session_id = None


if __name__ == "__main__":
    main()
