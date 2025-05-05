from flask import Flask, render_template, request, redirect, session, url_for
import csv
import os



app = Flask(__name__)
app.secret_key = "super_secret_key"  # Needed for session

# Load questions from CSV
def load_questions():
    questions = []
    try:
        base_dir = os.path.dirname(__file__)
        file_path = os.path.join(base_dir, 'personality_ques.csv')
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                questions.append({
                    "question": row["question"],
                    "options": {
                        "1": "Strongly Disagree",
                        "2": "Disagree",
                        "3": "Neutral",
                        "4": "Agree",
                        "5": "Strongly Agree"
                    },
                    "reverse": row["reverse"] == "True",
                    "trait": row["trait"]
                })
    except Exception as e:
        print(f"Failed to load questions: {e}")
    return questions

# Process responses and calculate the personality score
def calculate_score(responses):
    score = {
        "Extraversion": 0,
        "Agreeableness": 0,
        "Conscientiousness": 0,
        "Neuroticism": 0,
        "Openness": 0
    }
    
    for question, response in responses.items():
        try:
            question_index = int(question)
            response_val = int(response)
        except (ValueError, TypeError):
            continue  # Skip invalid entries

        question_data = session['questions'][question_index]
        trait = question_data["trait"]
        reverse = question_data["reverse"]
        
        if reverse:
            response_val = 6 - response_val

        score[trait] += response_val
    return score

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session["username"] = request.form["username"]
        session["responses"] = {}
        session["question_index"] = 0
        session["questions"] = load_questions()
        return redirect(url_for("quiz"))
    return render_template("index.html")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    questions = session.get("questions", [])
    index = session.get("question_index", 0)
    try:
        index = int(index)
    except (ValueError, TypeError):
        index = 0

    if index >= len(questions):
        return redirect(url_for("result"))

    current_question = questions[index]

    if request.method == "POST":
        selected = request.form.get("option")
        responses = session.get("responses", {})
        responses[str(index)] = selected  # store key as string to maintain JSON serializable keys
        session["responses"] = responses
        session["question_index"] = index + 1
        return redirect(url_for("quiz"))

    return render_template("quiz.html", question=current_question, qno=index + 1, total=len(questions))

@app.route("/result")
def result():
    responses = session.get("responses", {})
    score = calculate_score(responses)
    username = session.get("username", "Anonymous")

    # Save result to a file (optional for local testing, might be disabled on Render)
    try:
        base_dir = os.path.dirname(__file__)
        data_file_path = os.path.join(base_dir, 'personalitydata.txt')
        with open(data_file_path, "a") as f:
            f.write(f"{username}, {score}\n")
    except Exception as e:
        print("Could not save result:", e)

    return render_template("result.html", username=username, score=score)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # default to 5000 for local testing
    app.run(host="0.0.0.0", port=port, debug=True)