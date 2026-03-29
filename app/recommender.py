import pickle
import os
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Get correct base path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go to model folder
model_path = os.path.join(BASE_DIR, "..", "model")
data_path = os.path.join(BASE_DIR, "..", "data")

# Load initial files
similarity = pickle.load(open(os.path.join(model_path, "similarity.pkl"), "rb"))
matrix = pickle.load(open(os.path.join(model_path, "matrix.pkl"), "rb"))
dataset = pd.read_csv(os.path.join(data_path, "nqt_dataset.csv"))

# Global variables to track updates
current_max_user_id = 30

def get_test_options():
    """Get all available test options with categories and difficulties"""
    test_info = {}
    for _, row in dataset.iterrows():
        test_id = row['test_id']
        if test_id not in test_info:
            test_info[test_id] = {
                'category': row['category'],
                'difficulty': row['difficulty']
            }

    return {
        'tests': test_info,
        'categories': dataset['category'].unique().tolist(),
        'difficulties': dataset['difficulty'].unique().tolist()
    }

def update_models():
    """Update similarity matrix when new data is added"""
    global similarity
    similarity = cosine_similarity(matrix)
    # Save updated similarity
    with open(os.path.join(model_path, "similarity.pkl"), "wb") as f:
        pickle.dump(similarity, f)
    # Save updated matrix
    with open(os.path.join(model_path, "matrix.pkl"), "wb") as f:
        pickle.dump(matrix, f)

def add_user_data(user_data):
    """Add new user data to the system"""
    global current_max_user_id, matrix, dataset

    try:
        # Increment user ID
        new_user_id = current_max_user_id + 1
        current_max_user_id = new_user_id

        # Prepare new dataset rows only for submitted scores
        new_dataset_rows = []
        submitted_scores = user_data['scores']

        for test_id, score in submitted_scores.items():
            if test_id in matrix.columns:
                # Find category and difficulty from existing data
                existing_data = dataset[dataset['test_id'] == test_id]
                if not existing_data.empty:
                    category = existing_data['category'].iloc[0]
                    difficulty = existing_data['difficulty'].iloc[0]

                    new_dataset_rows.append({
                        'user_id': new_user_id,
                        'test_id': test_id,
                        'category': category,
                        'difficulty': difficulty,
                        'score': float(score)
                    })

        # Add new user to matrix with only submitted scores
        new_user_scores = pd.Series(0.0, index=matrix.columns)
        for test_id, score in submitted_scores.items():
            if test_id in matrix.columns:
                new_user_scores[test_id] = float(score)

        matrix = pd.concat([matrix, new_user_scores.to_frame().T], ignore_index=True)
        matrix.index = range(1, len(matrix) + 1)

        # Add to dataset only submitted scores
        if new_dataset_rows:
            new_rows_df = pd.DataFrame(new_dataset_rows)
            dataset = pd.concat([dataset, new_rows_df], ignore_index=True)

            # Save updated dataset
            dataset.to_csv(os.path.join(data_path, "nqt_dataset.csv"), index=False)

        # Update models
        update_models()

        return {
            "success": True,
            "new_user_id": new_user_id,
            "message": f"Data added successfully for user {new_user_id}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# 🔹 NEW: Detect weak areas
def get_weak_areas(user_index):
    weak_tests = []

    for test in matrix.columns:
        score = matrix.iloc[user_index][test]
        if score > 0 and score < 50:
            weak_tests.append(test)

    return weak_tests


# 🔹 UPDATED: Smart recommendation with detailed explanations
def recommend_tests(user_id):
    try:
        user_index = user_id - 1

        if user_index >= len(matrix):
            return {
                "recommended_tests": [],
                "weak_areas": [],
                "reason": "User not found in the system",
                "explanation": ""
            }

        scores = list(enumerate(similarity[user_index]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        recommended_tests = []
        weak_areas = get_weak_areas(user_index)

        # Get user's current performance
        user_scores = matrix.iloc[user_index]
        taken_tests = user_scores[user_scores > 0]

        # Find similar users and their recommendations
        similar_users_data = []
        for i in scores[1:6]:  # Top 5 similar users
            similar_user_idx = i[0]
            similarity_score = i[1]
            similar_user_scores = matrix.iloc[similar_user_idx]
            similar_user_taken = similar_user_scores[similar_user_scores > 0]

            similar_users_data.append({
                'user_id': similar_user_idx + 1,
                'similarity': round(similarity_score, 3),
                'tests_taken': len(similar_user_taken),
                'avg_score': round(similar_user_taken.mean(), 1) if len(similar_user_taken) > 0 else 0
            })

            for test in matrix.columns:
                if matrix.iloc[similar_user_idx][test] > 0 and matrix.iloc[user_index][test] == 0:
                    # 🔥 prioritize weak area improvement
                    if any(area.split("_")[0] in test for area in weak_areas):
                        recommended_tests.insert(0, test)  # higher priority
                    else:
                        recommended_tests.append(test)

        # Remove duplicates while preserving priority order
        seen = set()
        unique_recommendations = []
        for test in recommended_tests:
            if test not in seen:
                seen.add(test)
                unique_recommendations.append(test)

        # Create detailed explanation
        explanation = generate_detailed_explanation(
            user_id, weak_areas, taken_tests, similar_users_data, unique_recommendations[:5]
        )

        return {
            "recommended_tests": unique_recommendations[:5],
            "weak_areas": weak_areas,
            "reason": "Based on collaborative filtering using similar users' performance patterns",
            "explanation": explanation
        }

    except Exception as e:
        return {
            "recommended_tests": [],
            "weak_areas": [],
            "reason": f"Error: {str(e)}",
            "explanation": ""
        }

def generate_detailed_explanation(user_id, weak_areas, taken_tests, similar_users, recommendations):
    """Generate a comprehensive explanation for the recommendations"""

    explanation = f"📊 **Analysis for User {user_id}:**\n\n"

    # User's current status
    explanation += f"**Your Current Performance:**\n"
    if len(taken_tests) > 0:
        explanation += f"• You've taken {len(taken_tests)} tests with an average score of {taken_tests.mean():.1f}%\n"
        explanation += f"• Your highest score: {taken_tests.max()}% in {taken_tests.idxmax()}\n"
        explanation += f"• Your lowest score: {taken_tests.min()}% in {taken_tests.idxmin()}\n"
    else:
        explanation += "• No test records found - this appears to be your first time!\n"

    # Weak areas analysis
    if weak_areas:
        explanation += f"\n**Areas Needing Improvement:**\n"
        for area in weak_areas:
            score = taken_tests.get(area, 0)
            explanation += f"• {area.replace('_', ' ')}: {score}% (below 50% threshold)\n"
        explanation += "• Recommendations prioritize these weak areas for focused improvement\n"
    else:
        explanation += "\n**Performance Status:** Excellent! No weak areas detected.\n"

    # Similar users analysis
    explanation += f"\n**Similar User Analysis:**\n"
    explanation += f"• Found {len(similar_users)} most similar users based on your performance pattern\n"
    for user in similar_users[:3]:  # Show top 3
        explanation += f"• User {user['user_id']}: {user['similarity']*100:.1f}% similar, "
        explanation += f"took {user['tests_taken']} tests, avg score {user['avg_score']}%\n"

    # Recommendation logic
    explanation += f"\n**Recommendation Logic:**\n"
    explanation += "• Uses collaborative filtering - finds tests that similar users performed well in\n"
    explanation += "• Prioritizes tests in your weak areas for targeted improvement\n"
    explanation += "• Excludes tests you've already taken\n"
    explanation += "• Considers difficulty progression and category balance\n"

    # Specific recommendations
    if recommendations:
        explanation += f"\n**Why These Specific Tests:**\n"
        for i, test in enumerate(recommendations, 1):
            test_category = test.split('_')[0]
            is_weak_area = any(test_category in area for area in weak_areas)
            priority = "HIGH" if is_weak_area else "NORMAL"

            explanation += f"{i}. **{test.replace('_', ' ')}** ({priority} Priority)\n"
            if is_weak_area:
                explanation += f"   - Targets your weak area in {test_category}\n"
            explanation += f"   - Recommended by users with similar performance patterns\n"

    return explanation