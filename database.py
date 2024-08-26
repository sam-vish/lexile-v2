from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, EVALUATION_FACTORS
from lexile import get_initial_lexile

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_user(student_id, password, name, age, initial_lexile=None):
    if initial_lexile is None:
        lexile_level = get_initial_lexile(age)
    else:
        lexile_level = initial_lexile
    
    try:
        user = supabase.table('users').insert({
            'student_id': student_id,
            'password': password,  # Storing password as plain text (not recommended)
            'name': name,
            'age': age,
            'lexile_level': lexile_level
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
            if password == stored_password:  # Simple password comparison
                return student_id, True
        return None, False
    except Exception as e:
        print(f"Error verifying user: {e}")
        return None, False

def get_user_data(student_id):
    try:
        user = supabase.table('users').select('name', 'age', 'lexile_level').eq('student_id', student_id).execute()
        if user.data:
            return {
                'name': user.data[0]['name'],
                'age': user.data[0]['age'],
                'lexile_level': user.data[0]['lexile_level']
            }
        return None
    except Exception as e:
        print(f"Error getting user data: {e}")
        return None

def save_session(student_id, topic, lexile_level, content):
    try:
        session = supabase.table('sessions').insert({
            'student_id': student_id,
            'topic': topic,
            'lexile_level': lexile_level,
            'content': content
        }).execute()
        return session.data[0]['id']
    except Exception as e:
        print(f"Error saving session: {e}")
        return None

def update_user_answers_and_factors(student_id, user_answers, questions):
    from lexile import evaluate_answers
    scores, _ = evaluate_answers(questions, user_answers)
    
    # print(f"Scores to update: {scores}")  # Debug print
    
    try:
        for factor, score_change in scores.items():
            # print(f"Updating factor: {factor}, score change: {score_change}")  # Debug print
            
            # Fetch current score
            current_score_result = supabase.table('evaluation_factors').select('score').eq('student_id', student_id).eq('factor', factor).execute()
            
            if current_score_result.data:
                current_score = current_score_result.data[0]['score']
                new_score = max(current_score + score_change, 0)  # Ensure score doesn't go below 0
                
                # Update score
                result = supabase.table('evaluation_factors').update({
                    'score': new_score
                }).eq('student_id', student_id).eq('factor', factor).execute()
                
                # print(f"Update result: {result}")  # Debug print
            else:
                print(f"No existing score found for factor: {factor}")  # Debug print
    except Exception as e:
        print(f"Error updating user answers and factors: {e}")
        raise  # Re-raise the exception to see the full traceback

def update_user_lexile_level(student_id, lexile_level):
    try:
        supabase.table('users').update({
            'lexile_level': lexile_level
        }).eq('student_id', student_id).execute()
    except Exception as e:
        print(f"Error updating user lexile level: {e}")

def get_evaluation_scores(student_id):
    try:
        scores = supabase.table('evaluation_factors').select('factor', 'score').eq('student_id', student_id).execute()
        return {score['factor']: score['score'] for score in scores.data}
    except Exception as e:
        print(f"Error getting evaluation scores: {e}")
        return {}
    
def get_leaderboard():
    try:
        print("Fetching leaderboard data...")
        result = supabase.table('user_xp').select('student_id', 'xp_earned').execute()
        print(f"Leaderboard raw data: {result.data}")
        
        if not result.data:
            print("No data found in user_xp table")
            return []

        # Process the data to sum XP for each student
        xp_sum = {}
        for item in result.data:
            student_id = item['student_id']
            xp = item['xp_earned']
            xp_sum[student_id] = xp_sum.get(student_id, 0) + xp
        
        print(f"XP sum: {xp_sum}")

        # Get user names
        user_names = {}
        for student_id in xp_sum.keys():
            user_result = supabase.table('users').select('name').eq('student_id', student_id).execute()
            if user_result.data:
                user_names[student_id] = user_result.data[0]['name']
        
        print(f"User names: {user_names}")

        # Create leaderboard data
        leaderboard = [{'name': user_names.get(sid, 'Unknown'), 'xp': xp} for sid, xp in xp_sum.items()]
        leaderboard.sort(key=lambda x: x['xp'], reverse=True)
        
        print(f"Final leaderboard: {leaderboard[:10]}")
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
    
def test_supabase_connection():
    try:
        result = supabase.table('users').select('*').limit(1).execute()
        print(f"Supabase connection test result: {result}")
        return True
    except Exception as e:
        print(f"Supabase connection test failed: {e}")
        return False

def get_user_xp(student_id):
    try:
        result = supabase.table('user_xp').select('xp_earned').eq('student_id', student_id).execute()
        total_xp = sum(item['xp_earned'] for item in result.data)
        return total_xp
    except Exception as e:
        print(f"Error getting user XP: {e}")
        return 0