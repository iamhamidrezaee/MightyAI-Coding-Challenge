document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const setupSection = document.getElementById('setup-section');
    const configSection = document.getElementById('config-section');
    const resultsSection = document.getElementById('results-section');
    
    const serverUrlInput = document.getElementById('server-url');
    const connectBtn = document.getElementById('connect-btn');
    const connectError = document.getElementById('connect-error');
    
    const toolSelect = document.getElementById('tool-select');
    const toolArgs = document.getElementById('tool-args');
    const iterationsInput = document.getElementById('iterations');
    const runBtn = document.getElementById('run-btn');
    const runError = document.getElementById('run-error');
    
    const avgLatencyEl = document.getElementById('avg-latency');
    const minLatencyEl = document.getElementById('min-latency');
    const maxLatencyEl = document.getElementById('max-latency');
    const successRateEl = document.getElementById('success-rate');
    
    const resultsTableBody = document.querySelector('#results-table tbody');
    const shareLink = document.getElementById('share-link');
    const newTestBtn = document.getElementById('new-test-btn');
    
    let chartInstance = null;

    // Check for existing experiment ID in URL
    const urlParams = new URLSearchParams(window.location.search);
    const experimentId = urlParams.get('id');
    
    if (experimentId) {
        loadExperiment(experimentId);
    }

    // Event Listeners
    connectBtn.addEventListener('click', async () => {
        const url = serverUrlInput.value.trim();
        if (!url) return showError(connectError, "Please enter a URL");
        
        connectBtn.disabled = true;
        connectBtn.textContent = "Connecting...";
        hideError(connectError);
        
        try {
            const res = await fetch('/api/tools', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ serverUrl: url })
            });
            
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.error || "Failed to connect");
            
            populateTools(data.tools);
            setupSection.classList.add('hidden');
            configSection.classList.remove('hidden');
        } catch (err) {
            showError(connectError, err.message);
        } finally {
            connectBtn.disabled = false;
            connectBtn.textContent = "Fetch Tools";
        }
    });

    runBtn.addEventListener('click', async () => {
        const tool = toolSelect.value;
        const argsStr = toolArgs.value;
        const iterations = iterationsInput.value;
        const serverUrl = serverUrlInput.value;
        
        // Validate JSON
        try {
            JSON.parse(argsStr);
        } catch (e) {
            return showError(runError, "Invalid JSON arguments");
        }
        
        runBtn.disabled = true;
        runBtn.textContent = "Running Experiment...";
        hideError(runError);
        
        try {
            const res = await fetch('/api/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    serverUrl,
                    toolName: tool,
                    arguments: argsStr,
                    iterations
                })
            });
            
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.error || "Experiment failed");
            
            renderResults(data.results, data.experimentId);
            configSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            
            // Update URL without reloading
            const newUrl = `${window.location.pathname}?id=${data.experimentId}`;
            window.history.pushState({ path: newUrl }, '', newUrl);
            
        } catch (err) {
            showError(runError, err.message);
        } finally {
            runBtn.disabled = false;
            runBtn.textContent = "Run Experiment";
        }
    });
    
    newTestBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        setupSection.classList.remove('hidden');
        // Clear ID from URL
        window.history.pushState({}, '', window.location.pathname);
        // Reset form? maybe keep server url
    });

    // Functions
    function populateTools(tools) {
        toolSelect.innerHTML = '';
        if (tools.length === 0) {
            const option = document.createElement('option');
            option.text = "No tools found";
            toolSelect.add(option);
            return;
        }
        
        tools.forEach(tool => {
            const option = document.createElement('option');
            option.value = tool.name;
            option.text = tool.name;
            toolSelect.add(option);
        });
    }
    
    function showError(element, msg) {
        element.textContent = msg;
        element.classList.remove('hidden');
    }
    
    function hideError(element) {
        element.classList.add('hidden');
    }
    
    async function loadExperiment(id) {
        try {
            const res = await fetch(`/api/experiments/${id}`);
            if (!res.ok) return; // Silent fail or show generic error
            
            const data = await res.json();
            
            // Pre-fill setup in case user wants to run again
            serverUrlInput.value = data.experiment.serverUrl;
            
            renderResults(data.results, id);
            setupSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');
        } catch (e) {
            console.error(e);
        }
    }
    
    function renderResults(results, id) {
        // Update share link
        shareLink.href = `${window.location.origin}${window.location.pathname}?id=${id}`;
        
        // Stats
        const durations = results.map(r => r.duration_ms);
        const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
        const min = Math.min(...durations);
        const max = Math.max(...durations);
        const successCount = results.filter(r => r.status === 'success').length;
        const successRate = (successCount / results.length) * 100;
        
        avgLatencyEl.textContent = `${avg.toFixed(2)} ms`;
        minLatencyEl.textContent = `${min.toFixed(2)} ms`;
        maxLatencyEl.textContent = `${max.toFixed(2)} ms`;
        successRateEl.textContent = `${successRate.toFixed(1)}%`;
        
        // Table
        resultsTableBody.innerHTML = '';
        results.forEach(r => {
            const row = resultsTableBody.insertRow();
            row.innerHTML = `
                <td>${r.iteration}</td>
                <td class="${r.status === 'success' ? 'status-success' : 'status-error'}">${r.status}</td>
                <td>${r.duration_ms.toFixed(2)}</td>
                <td title="${escapeHtml(r.response)}">${truncate(r.response, 50)}</td>
            `;
        });
        
        // Chart
        renderChart(results);
    }
    
    function renderChart(results) {
        const ctx = document.getElementById('latency-chart').getContext('2d');
        
        if (chartInstance) {
            chartInstance.destroy();
        }
        
        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: results.map(r => r.iteration),
                datasets: [{
                    label: 'Latency (ms)',
                    data: results.map(r => r.duration_ms),
                    borderColor: '#000000',
                    backgroundColor: 'rgba(0,0,0,0.1)',
                    borderWidth: 2,
                    tension: 0.1,
                    pointRadius: 4,
                    pointBackgroundColor: results.map(r => r.status === 'success' ? '#000' : '#d32f2f')
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#e0e0e0'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    function truncate(str, n) {
        return (str.length > n) ? str.substr(0, n-1) + '...' : str;
    }
    
    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});

