import logging

import psycopg2
from flask import Flask, jsonify
from langchain_openai import OpenAI
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql.base import SQLDatabaseChain
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

app = Flask(__name__)

openai_api_key = '<openai_api_key>'

db_name = 'jobboard'
db_user = 'postgres'
db_password = 'mysecretpassword'
db_host = 'localhost'
db_port = '5432'

db_uri = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
engine = create_engine(db_uri)

db = SQLDatabase(engine)
llm = OpenAI(api_key=openai_api_key)
sql_chain = SQLDatabaseChain.from_llm(llm=llm, db=db, verbose=True)


def get_db_connection():
    return psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
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


@app.route('/analyze', methods=['POST'])
def analyze_data():
    data = get_initial_data()
    initial_summary_data = ''.join([f"Job ID {job[0]} has {job[1]} applications.\n" for job in data])
    initial_summary = (
        f"Review this data: '{initial_summary_data}' and check for any anomalies. "
        f"If you think you may need more data for a better analysis"
        f"your response MUST be a PostgresSQL SELECT statement to retrieve further details")

    responses = []
    query_prompt = initial_summary
    for _ in range(3):  # Loop up to 3 times
        query_response = sql_chain.run(query_prompt)
        if query_response.startswith("SELECT"):
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
                                f"your response MUST be a PostgreSQL SELECT statement to retrieve further details")

            except Exception as e:
                logger.error(f"Error during running db query: {e}")

        else:
            responses.append({
                "prompt": query_prompt,
                "ai_decision": "No further data needed."
            })
            break  # Exit the loop if no more data is needed

    return jsonify(responses)


if __name__ == '__main__':
    app.run(debug=True)
