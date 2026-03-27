import pickle
import os

# Get correct base path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go to model folder
model_path = os.path.join(BASE_DIR, "..", "model")

# Load files
similarity = pickle.load(open(os.path.join(model_path, "similarity.pkl"), "rb"))
matrix = pickle.load(open(os.path.join(model_path, "matrix.pkl"), "rb"))


# 🔹 NEW: Detect weak areas
def get_weak_areas(user_index):
    weak_tests = []

    for test in matrix.columns:
        score = matrix.iloc[user_index][test]
        if score > 0 and score < 50:
            weak_tests.append(test)

    return weak_tests


# 🔹 UPDATED: Smart recommendation
def recommend_tests(user_id):
    try:
        user_index = user_id - 1

        scores = list(enumerate(similarity[user_index]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        recommended_tests = []
        weak_areas = get_weak_areas(user_index)

        for i in scores[1:6]:
            similar_user = i[0]

            for test in matrix.columns:
                if matrix.iloc[similar_user][test] > 0 and matrix.iloc[user_index][test] == 0:
                    
                    # 🔥 prioritize weak area improvement
                    if any(area.split("_")[0] in test for area in weak_areas):
                        recommended_tests.insert(0, test)  # higher priority
                    else:
                        recommended_tests.append(test)

        return {
            "recommended_tests": list(set(recommended_tests))[:5],
            "weak_areas": weak_areas,
            "reason": "Based on similar users and your weak performance areas"
        }

    except Exception as e:
        return {
            "recommended_tests": [],
            "weak_areas": [],
            "reason": f"Error: {str(e)}"
        }