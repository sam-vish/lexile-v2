from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, EVALUATION_FACTORS
from lexile import get_initial_lexile, adjust_lexile_level, evaluate_answers
from datetime import datetime, timedelta
from utils import get_session_question

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_user(student_id, password, name, age, initial_lexile=None):
    if initial_lexile is None:
        lexile_level = get_initial_lexile(age)
    else:
        lexile_level = initial_lexile
    
    try:
        user = supabase.table('users').insert({
            'student_id': student_id,
            'password': password,  # Note: In a production environment, use proper password hashing
            'name': name,
            'age': age,
            'lexile_level': lexile_level,
            'streak': 0,
            'last_activity_date': datetime.now().date().isoformat()
        }).execute()
        
        for factor in EVALUATION_FACTORS:
            result = supabase.table('evaluation_factors').insert({
                'student_id': student_id,
                'factor': factor,
                'score': 0
            }).execute()
            print(f"Created factor {factor} for user {student_id}: {result}")
        
        return student_id
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def verify_user(student_id, password):
    try:
        user = supabase.table('users').select('password').eq('student_id', student_id).execute()
        if user.data:
            stored_password = user.data[0]['password']
            if password == stored_password:  # In production, use proper password verification
                return student_id, True
        return None, False
    except Exception as e:
        print(f"Error verifying user: {e}")
        return None, False

def get_user_data(student_id):
    try:
        user = supabase.table('users').select('name', 'age', 'lexile_level', 'streak', 'last_activity_date').eq('student_id', student_id).execute()
        if user.data and len(user.data) > 0:
            return {
                'name': user.data[0]['name'],
                'age': user.data[0]['age'],
                'lexile_level': user.data[0]['lexile_level'],
                'streak': user.data[0].get('streak', 0),
                'last_activity_date': user.data[0].get('last_activity_date')
            }
        else:
            print(f"No user data found for student_id: {student_id}")
            return None
    except Exception as e:
        print(f"Error getting user data: {e}")
        return None

def save_session(student_id, topic, lexile_level, content):
    try:
        print(f"Attempting to save session: student_id={student_id}, topic={topic}, lexile_level={lexile_level}")
        session = supabase.table('sessions').insert({
            'student_id': student_id,
            'topic': topic,
            'lexile_level': lexile_level,
            'content': content
        }).execute()
        print(f"Session save result: {session}")
        if session.data:
            print(f"Successfully saved session with ID: {session.data[0]['id']}")
            return session.data[0]['id']
        else:
            print("No data returned from session save operation")
            return None
    except Exception as e:
        print(f"Error saving session: {e}")
        print(f"Error details: {str(e)}")
        return None

# Ensure this import is present

def update_user_answers_and_factors(student_id, user_answers, session_id):
    print(f"Updating user answers and factors for student_id: {student_id}, session_id: {session_id}")
    print(f"User Answers: {user_answers}")
    
    scores, percentage_correct = evaluate_answers(session_id, user_answers)

    try:
        for factor, score_change in scores.items():
            current_result = supabase.table('evaluation_factors').select('score').eq('student_id', student_id).eq('factor', factor).execute()

            if current_result.data:
                current_score = current_result.data[0]['score']
                new_score = max(min(current_score + score_change, 100), 0)  # Ensure score is between 0 and 100

                result = supabase.table('evaluation_factors').update({
                    'score': new_score
                }).eq('student_id', student_id).eq('factor', factor).execute()

                # Check if factor score reached 100 and award XP
                if new_score == 100 and current_score < 100:
                    award_xp(student_id, 5)  # Award 5 XP for completing a factor

                print(f"Updated {factor} score for user {student_id}: {new_score}")

        # Adjust lexile level based on percentage correct
        current_lexile = get_user_data(student_id)['lexile_level']
        new_lexile = adjust_lexile_level(current_lexile, percentage_correct)
        update_user_lexile_level(student_id, new_lexile)

        print(f"Updated Lexile Level for user {student_id}: {new_lexile}")

        return percentage_correct
    except Exception as e:
        print(f"Error updating user answers and factors: {e}")
        raise

def calculate_lexile_range(lexile_level):
    range_start = (lexile_level // 100) * 100
    range_end = range_start + 100
    return range_start, range_end

def update_user_lexile_level(student_id, lexile_level):
    try:
        current_range_start, current_range_end = get_user_leaderboard_range(student_id)
        new_range_start, new_range_end = calculate_lexile_range(lexile_level)
        
        supabase.table('users').update({
            'lexile_level': lexile_level,
            'leaderboard_range_start': new_range_start,
            'leaderboard_range_end': new_range_end
        }).eq('student_id', student_id).execute()
        
        if new_range_start != current_range_start or new_range_end != current_range_end:
            print(f"User {student_id} moved to a new Lexile range: {new_range_start}L - {new_range_end}L")
    except Exception as e:
        print(f"Error updating user lexile level: {e}")

def get_user_leaderboard_range(student_id):
    try:
        result = supabase.table('users').select('leaderboard_range_start', 'leaderboard_range_end').eq('student_id', student_id).execute()
        if result.data:
            return result.data[0]['leaderboard_range_start'], result.data[0]['leaderboard_range_end']
        return None, None
    except Exception as e:
        print(f"Error getting user leaderboard range: {e}")
        return None, None

def get_evaluation_scores(student_id):
    try:
        scores = supabase.table('evaluation_factors').select('factor', 'score').eq('student_id', student_id).execute()
        return {score['factor']: score['score'] for score in scores.data}
    except Exception as e:
        print(f"Error getting evaluation scores: {e}")
        return {}
    
def update_user_leaderboard_range(student_id, lexile_level):
    range_start = (lexile_level // 100) * 100
    range_end = range_start + 100
    try:
        supabase.table('users').update({
            'leaderboard_range_start': range_start,
            'leaderboard_range_end': range_end
        }).eq('student_id', student_id).execute()
    except Exception as e:
        print(f"Error updating user leaderboard range: {e}")

    
def get_leaderboard(student_id):
    try:
        range_start, range_end = get_user_leaderboard_range(student_id)
        if range_start is None or range_end is None:
            return []

        # Fetch users within the Lexile range
        users_in_range = supabase.table('users').select('student_id', 'name', 'lexile_level').gte('lexile_level', range_start).lt('lexile_level', range_end).execute()
        
        if not users_in_range.data:
            print(f"No users found in Lexile range {range_start}-{range_end}")
            return []

        # Get XP for these users
        xp_data = {}
        for user in users_in_range.data:
            user_id = user['student_id']
            xp_result = supabase.table('user_xp').select('xp_earned').eq('student_id', user_id).execute()
            total_xp = sum(item['xp_earned'] for item in xp_result.data)
            xp_data[user_id] = total_xp

        # Create leaderboard data
        leaderboard = [{'name': user['name'], 'xp': xp_data.get(user['student_id'], 0), 'lexile': user['lexile_level']} for user in users_in_range.data]
        leaderboard.sort(key=lambda x: x['xp'], reverse=True)
        
        return leaderboard[:10]  # Return top 10
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return []
    
def save_user_xp(student_id, xp_earned, session_id):
    try:
        print(f"Attempting to save XP: student_id={student_id}, xp_earned={xp_earned}, session_id={session_id}")
        result = supabase.table('user_xp').insert({
            'student_id': student_id,
            'xp_earned': xp_earned,
            'session_id': session_id
        }).execute()
        print(f"XP save result: {result}")
        if result.data:
            print(f"Successfully saved XP with ID: {result.data[0]['id']}")
            return result.data[0]['id']
        else:
            print("No data returned from XP save operation")
            return None
    except Exception as e:
        print(f"Error saving user XP: {e}")
        print(f"Error details: {str(e)}")
        return None

def award_xp(student_id, xp):
    try:
        supabase.table('user_xp').insert({
            'student_id': student_id,
            'xp_earned': xp,
            'session_id': None  # or provide a session ID if available
        }).execute()
    except Exception as e:
        print(f"Error awarding XP: {e}")
    
def get_user_xp(student_id):
    try:
        result = supabase.table('user_xp').select('xp_earned').eq('student_id', student_id).execute()
        total_xp = sum(item['xp_earned'] for item in result.data)
        return total_xp
    except Exception as e:
        print(f"Error getting user XP: {e}")
        return 0

def update_user_streak(student_id):
    try:
        user_data = get_user_data(student_id)
        current_date = datetime.now().date()
        last_activity_date = user_data.get('last_activity_date')
        current_streak = user_data.get('streak', 0)

        if last_activity_date:
            last_activity_date = datetime.strptime(last_activity_date, '%Y-%m-%d').date()
            if current_date - last_activity_date == timedelta(days=1):
                # Consecutive day, increase streak
                new_streak = current_streak + 1
            elif current_date == last_activity_date:
                # Same day, maintain streak
                new_streak = current_streak
            else:
                # Streak broken
                new_streak = 1
        else:
            # First activity
            new_streak = 1

        result = supabase.table('users').update({
            'streak': new_streak,
            'last_activity_date': str(current_date)
        }).eq('student_id', student_id).execute()

        print(f"Updated streak for user {student_id}: {result}")
        return new_streak
    except Exception as e:
        print(f"Error updating user streak: {e}")
        return None

def save_session_questions(session_id, questions):
    try:
        for i, question in enumerate(questions, start=1):
            supabase.table('session_questions').insert({
                'session_id': session_id,
                'question_text': question['text'],
                'option_a': question['options'][0],
                'option_b': question['options'][1],
                'option_c': question['options'][2],
                'option_d': question['options'][3],
                'correct_answer': question['correct_answer'],
                'evaluation_factor': question['evaluation_factor'],
                'question_order': i
            }).execute()
        return True
    except Exception as e:
        print(f"Error saving session questions: {e}")
        return False

def test_supabase_connection():
    try:
        result = supabase.table('users').select('*').limit(1).execute()
        print(f"Supabase connection test result: {result}")
        return True
    except Exception as e:
        print(f"Supabase connection test failed: {e}")
        return False
