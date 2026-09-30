from flask import Flask, render_template, request, redirect
import psycopg2

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="finance_tracker",
        user="postgres",
        password="Tuhin@2008",
        port="5432"
    )

@app.route("/")
def home():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name;")
    categories = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("add_expense.html", categories=categories)

@app.route("/add", methods=["POST"])
def add_expense():
    amount = request.form["amount"]
    description = request.form["description"]
    category_id = request.form["category_id"]
    transaction_date = request.form["transaction_date"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (amount, description, category_id, transaction_date) VALUES (%s, %s, %s, %s)",
        (amount, description, category_id, transaction_date)
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")

@app.route("/expenses")
def view_expenses():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id, t.amount, t.description, c.name, t.transaction_date
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        ORDER BY t.transaction_date DESC;
    """)
    expenses = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("view_expenses.html", expenses=expenses)

import ollama

@app.route("/insights")
def insights():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.name, SUM(t.amount) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        GROUP BY c.name
        ORDER BY total DESC;
    """)
    spending_by_category = cur.fetchall()

    cur.execute("SELECT SUM(amount) FROM transactions;")
    total_spent = cur.fetchone()[0]

    cur.close()
    conn.close()

    # Build a plain-text summary to feed the LLM
    summary_lines = [f"{name}: ${total}" for name, total in spending_by_category]
    summary_text = f"Total spending: ${total_spent}\n" + "\n".join(summary_lines)

    prompt = f"""You are a personal finance assistant. Here is a breakdown of someone's spending by category:

{summary_text}

Give 3 short, practical suggestions on how they could save money, based on this data. Be specific about which categories stand out. Keep it concise."""

    response = ollama.chat(model='llama3.2:3b', messages=[{'role': 'user', 'content': prompt}])
    ai_suggestions = response['message']['content']

    return render_template("insights.html", spending=spending_by_category, total=total_spent, ai_suggestions=ai_suggestions)

@app.route("/delete/<int:transaction_id>", methods=["POST"])
def delete_expense(transaction_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id = %s;", (transaction_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/expenses")

if __name__ == "__main__":
    app.run(debug=True)