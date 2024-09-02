from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_session_question(session_id, question_order):
    try:
        result = supabase.table('session_questions').select('*').eq('session_id', session_id).eq('question_order', question_order).execute()
        if result.data:
            print(f"Retrieved question {question_order} for session {session_id}: {result.data[0]}")
            return result.data[0]
        print(f"No question found for session {session_id} and question order {question_order}")
        return None
    except Exception as e:
        print(f"Error getting session question: {e}")
        return None
