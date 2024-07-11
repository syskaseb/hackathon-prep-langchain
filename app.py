import logging

import psycopg2
from flask import Flask, jsonify
from langchain import OpenAI, SQLDatabase
from langchain_experimental.sql.base import SQLDatabaseChain
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

app = Flask(__name__)

openai_api_key = '<openai-api-key>'
db_uri = 'postgresql://postgres:mysecretpassword@localhost:5432/jobboard'
engine = create_engine(db_uri)

db = SQLDatabase(engine)
llm = OpenAI(api_key=openai_api_key)
sql_chain = SQLDatabaseChain(llm=llm, database=db, verbose=True)


def get_db_connection():
    return psycopg2.connect(
        dbname="jobboard",
        user="postgres",
        password="mysecretpassword",
        host="localhost",
        port="5432"
    )


def get_initial_data():
    # Fetching initial aggregated data
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT job_id, COUNT(*) as application_count FROM job_data GROUP BY job_id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.route('/analyze', methods=['GET'])
def analyze_data():
    data = get_initial_data()
    initial_data = ''.join([f"Job ID {job[0]} has {job[1]} applications.\n" for job in data])
    initial_summary = (
        f"Review this data: '{initial_data}' and check for any anomalies. "
        f"If you think you may need more data for a better analysis"
        f"your response MUST be a postgresql SELECT statement for further data from the db")

    responses = []
    query_prompt = initial_summary
    for _ in range(3):  # Loop up to 3 times
        query_response = sql_chain.run(query_prompt)
        if "SELECT" in query_response:
            try:
                detailed_data = db.run(query_response)
                responses.append({
                    "prompt": query_prompt,
                    "sql_query": query_response,
                    "detailed_data": detailed_data
                })
                # Update the prompt with new data summary for further analysis
                query_prompt = (f"Review this data: '{detailed_data}' and check for any anomalies. "
                                f"If you think you may need more data for a better analysis "
                                f"your response MUST be a postgresql SELECT statement for further data from the db")

            except Exception as e:
                logger.error(f"error during running db query: {e}")

        else:
            responses.append({
                "prompt": query_prompt,
                "ai_decision": "No further data needed."
            })
            break  # Exit the loop if no more data is needed

    return jsonify(responses)


if __name__ == '__main__':
    app.run(debug=True)
