import os
import sqlite3
import json
import time
import uuid
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='frontend')

# Database Setup
DB_NAME = "experiments.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    server_url TEXT,
                    tool_name TEXT,
                    arguments TEXT,
                    iterations INTEGER,
                    timestamp TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS results (
                    experiment_id TEXT,
                    iteration_index INTEGER,
                    duration_ms REAL,
                    status TEXT,
                    response TEXT,
                    FOREIGN KEY(experiment_id) REFERENCES experiments(id)
                )''')
    conn.commit()
    conn.close()

init_db()

# Helpers
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def mcp_rpc_call(server_url, method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1
    }
    if params:
        payload["params"] = params
    
    headers = {"Content-Type": "application/json"}
    try:
        # Assuming the server URL is the endpoint for JSON-RPC messages
        # If the user provides the base URL, we might need to append /mcp or similar, 
        # but the prompt implies "Register an MCP server HTTP endpoint by URL", so we assume the full URL.
        response = requests.post(server_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    except ValueError:
        return {"error": "Invalid JSON response"}

# Routes
@app.route('/')
def serve_index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('frontend', filename)

@app.route('/api/tools', methods=['POST'])
def list_tools():
    data = request.json
    server_url = data.get('serverUrl')
    if not server_url:
        return jsonify({"error": "Server URL is required"}), 400
    
    # Call tools/list
    result = mcp_rpc_call(server_url, "tools/list")
    
    if "error" in result:
        # Check if it's a transport error or JSON-RPC error
        if isinstance(result["error"], str):
             return jsonify({"error": result["error"]}), 500
        else:
             return jsonify({"error": result["error"].get("message", "Unknown RPC error")}), 500
             
    if "result" in result and "tools" in result["result"]:
        return jsonify({"tools": result["result"]["tools"]})
    
    return jsonify({"error": "Invalid response format from server", "raw": result}), 502

@app.route('/api/run', methods=['POST'])
def run_experiment():
    data = request.json
    server_url = data.get('serverUrl')
    tool_name = data.get('toolName')
    arguments_str = data.get('arguments')
    iterations = int(data.get('iterations', 10))
    
    try:
        arguments = json.loads(arguments_str) if arguments_str else {}
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON arguments"}), 400

    experiment_id = str(uuid.uuid4())[:8] # Short ID
    timestamp = datetime.now().isoformat()
    
    conn = get_db_connection()
    conn.execute('INSERT INTO experiments (id, server_url, tool_name, arguments, iterations, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                 (experiment_id, server_url, tool_name, arguments_str, iterations, timestamp))
    
    results = []
    
    for i in range(iterations):
        start_time = time.time()
        # Call tools/call
        rpc_response = mcp_rpc_call(server_url, "tools/call", {"name": tool_name, "arguments": arguments})
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        status = "success"
        response_text = ""
        
        if "error" in rpc_response:
            status = "error"
            err = rpc_response["error"]
            response_text = err if isinstance(err, str) else err.get("message", json.dumps(err))
        elif "result" in rpc_response:
            response_text = json.dumps(rpc_response["result"])
        else:
            status = "unknown"
            response_text = json.dumps(rpc_response)

        conn.execute('INSERT INTO results (experiment_id, iteration_index, duration_ms, status, response) VALUES (?, ?, ?, ?, ?)',
                     (experiment_id, i, duration_ms, status, response_text))
        
        results.append({
            "iteration": i + 1,
            "duration_ms": duration_ms,
            "status": status,
            "response": response_text
        })
        
    conn.commit()
    conn.close()
    
    return jsonify({
        "experimentId": experiment_id,
        "results": results
    })

@app.route('/api/experiments/<experiment_id>', methods=['GET'])
def get_experiment(experiment_id):
    conn = get_db_connection()
    experiment = conn.execute('SELECT * FROM experiments WHERE id = ?', (experiment_id,)).fetchone()
    
    if not experiment:
        conn.close()
        return jsonify({"error": "Experiment not found"}), 404
        
    rows = conn.execute('SELECT * FROM results WHERE experiment_id = ? ORDER BY iteration_index', (experiment_id,)).fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "iteration": row["iteration_index"] + 1,
            "duration_ms": row["duration_ms"],
            "status": row["status"],
            "response": row["response"]
        })
        
    return jsonify({
        "experiment": {
            "id": experiment["id"],
            "serverUrl": experiment["server_url"],
            "toolName": experiment["tool_name"],
            "arguments": experiment["arguments"],
            "iterations": experiment["iterations"],
            "timestamp": experiment["timestamp"]
        },
        "results": results
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

