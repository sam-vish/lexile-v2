# lexile.py

import random
from config import AGE_TO_LEXILE, EVALUATION_FACTORS
from utils import get_session_question  # Updated import

def get_initial_lexile(age):
    for age_range, lexile_range in AGE_TO_LEXILE.items():
        if age in age_range:
            return random.randint(lexile_range[0], lexile_range[1])
    return None  # Return None instead of 500 if age is out of all ranges

def adjust_lexile_level(current_lexile, percentage_correct):
    if percentage_correct >= 70:
        return current_lexile + 10
    elif percentage_correct <= 30:
        return max(0, current_lexile - 10)
    return current_lexile

def display_lexile_scale(current_lexile):
    scale = list(range(max(0, current_lexile - 500), current_lexile + 50, 50))
    scale_str = " ".join([f"[{level}L]" if level == current_lexile else f"{level}L" for level in scale])
    return scale_str

# In lexile.py
from utils import get_session_question

def evaluate_answers(session_id, user_answers):
    scores = {factor: 0 for factor in EVALUATION_FACTORS}
    total_questions = len(user_answers)
    correct_answers = 0

    for i, user_answer in enumerate(user_answers, start=1):
        question = get_session_question(session_id, i)
        if not question:
            print(f"Lexile File:::: Question {i} not found for session {session_id}")
            continue

        factor = question["evaluation_factor"]
        if factor not in scores:
            # Find the closest matching factor
            matching_factor = next((f for f in EVALUATION_FACTORS if f.lower() in factor.lower()), None)
            if matching_factor:
                factor = matching_factor
            else:
                print(f"No matching factor found for question {i}")
                continue  # Skip this question if no matching factor is found

        if user_answer == question["correct_answer"]:
            scores[factor] += 1
            correct_answers += 1
        else:
            scores[factor] -= 1

        print(f"Question {i}: User Answer = {user_answer}, Correct Answer = {question['correct_answer']}, Factor = {factor}, Score Change = {scores[factor]}")

    # Calculate percentage of correct answers
    percentage_correct = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    print(f"Evaluation Scores: {scores}")
    print(f"Percentage Correct: {percentage_correct}")

    return scores, percentage_correct
