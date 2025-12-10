from flask import Flask, request, jsonify
import time
import random

app = Flask(__name__)

@app.route('/mcp', methods=['POST'])
def handle_rpc():
    data = request.json
    method = data.get('method')
    id = data.get('id')
    
    if method == 'tools/list':
        return jsonify({
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "tools": [
                    {
                        "name": "echo",
                        "description": "Echoes back the input",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"}
                            }
                        }
                    },
                    {
                        "name": "random_number",
                        "description": "Returns a random number",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "min": {"type": "integer"},
                                "max": {"type": "integer"}
                            }
                        }
                    },
                     {
                        "name": "error_tool",
                        "description": "Always returns an error",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        })
    
    elif method == 'tools/call':
        params = data.get('params', {})
        tool_name = params.get('name')
        args = params.get('arguments', {})
        
        # Simulate latency
        time.sleep(random.uniform(0.05, 0.2))
        
        if tool_name == 'echo':
            return jsonify({
                "jsonrpc": "2.0",
                "id": id,
                "result": {
                    "content": [{"type": "text", "text": f"Echo: {args.get('message', '')}"}]
                }
            })
        elif tool_name == 'random_number':
            min_val = int(args.get('min', 0))
            max_val = int(args.get('max', 100))
            return jsonify({
                "jsonrpc": "2.0",
                "id": id,
                "result": {
                    "content": [{"type": "text", "text": str(random.randint(min_val, max_val))}]
                }
            })
        elif tool_name == 'error_tool':
             return jsonify({
                "jsonrpc": "2.0",
                "id": id,
                "error": {
                    "code": -32000,
                    "message": "This tool always fails"
                }
            })
            
    return jsonify({"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": id})

if __name__ == '__main__':
    app.run(port=8000)

