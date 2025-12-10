# Mini MCP Server Tester

A lightweight, full-stack application to monitor the performance and reliability of Model Context Protocol (MCP) servers.

## Features

- **Connect**: Connect to any HTTP-based MCP server endpoint.
- **Discover**: Automatically lists available tools from the server.
- **Experiment**: Run repeated tool calls to measure latency and reliability.
- **Analyze**: View results with a latency chart and detailed request log.
- **Share**: Share experiment results via URL.

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository (or download the bundle).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`.

## Design Decisions

- **Architecture**: A simple Flask backend with a vanilla JS/HTML/CSS frontend. This ensures the "quickest route" to a working MVP without build steps (like Webpack/Vite) or heavy frontend frameworks (React/Vue).
- **Database**: SQLite is used for zero-configuration persistence of experiment results. It is built into Python, requiring no external service.
- **MCP Integration**: The application assumes the MCP server exposes a JSON-RPC 2.0 interface over HTTP (via POST requests). This allows for a stateless and simple integration model compatible with many MCP server implementations.
- **UI/UX**: Minimalist black-and-white aesthetic using the Inter font. The interface is divided into three logical steps (Connect -> Configure -> Results) to guide the user. Chart.js is used for visualization.
- **Single Folder Frontend**: To keep the repository structure clean as requested, all frontend assets are served from the `frontend/` directory.

## AI Coding Tools Used

This project was built with the assistance of an AI coding agent. The agent helped with:
- Scaffolding the Flask application structure.
- Generating the boilerplate HTML/CSS for a responsive layout.
- Implementing the SQLite schema and query logic.
- Writing the `README.md` documentation.

## API Endpoints

- `POST /api/tools`: List tools from a given MCP server URL.
- `POST /api/run`: Execute a performance experiment.
- `GET /api/experiments/<id>`: Retrieve saved experiment results.


