
document.getElementById('fetch-button').addEventListener('click', async function() {
    const userUrl = document.getElementById('user-company-url').value;
    const targetUrl = document.getElementById('target-company-url').value;
    const reportOutput = document.getElementById('report-output');
    const fetchButton = this;

    if (!userUrl || !targetUrl) {
        alert('Please enter both company URLs.');
        return;
    }

    // --- 1. Start Loading State ---
    reportOutput.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p><strong>AI is analyzing...</strong></p>
            <p>This may take a moment. The agent is researching both companies and generating a detailed report.</p>
        </div>
    `;
    fetchButton.disabled = true;
    fetchButton.textContent = 'Analyzing...';

    try {
        // --- 2. Send URLs to the new backend endpoint ---
        const response = await fetch('/fetch-and-analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_url: userUrl,
                target_url: targetUrl
            }),
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.status === 'error') {
            throw new Error(`Analysis error: ${result.message}`);
        }

        // --- 3. Auto-fill the form fields ---
        const userProfile = result.user_profile;
        document.getElementById('user-company-name').value = userProfile.company_name;
        document.getElementById('user-company-desc').value = userProfile.company_description;
        document.getElementById('user-company-industry').value = userProfile.industry_type;
        document.getElementById('user-company-size').value = userProfile.company_size;
        document.getElementById('user-company-specialties').value = userProfile.specialties.join('\n');
        
        const targetProfile = result.target_profile;
        document.getElementById('target-company-name').value = targetProfile.company_name;
        document.getElementById('target-company-desc').value = targetProfile.company_description;
        document.getElementById('target-company-industry').value = targetProfile.industry_type;
        document.getElementById('target-company-size').value = targetProfile.company_size;
        document.getElementById('target-company-specialties').value = targetProfile.specialties.join('\n');

        // --- 4. Dynamically build and display the new report ---
        displayModernReport(result.analysis_report);

    } catch (error) {
        console.error("Error during analysis:", error);
        reportOutput.innerHTML = `<div class="error-message"><strong>An error occurred:</strong><p>${error.message}</p></div>`;
    } finally {
        // --- 5. Reset Loading State ---
        fetchButton.disabled = false;
        fetchButton.textContent = 'Fetch Information & Analyze';
    }
});

function displayModernReport(report) {
    const reportOutput = document.getElementById('report-output');

    // Helper function to create list items
    const createListItems = (items) => items.map(item => `<li>${item}</li>`).join('');

    // Determine badge color based on score
    let badgeColor = 'common';
    if (report.match_score.toLowerCase() === 'strong') badgeColor = 'strong';
    if (report.match_score.toLowerCase() === 'weak') badgeColor = 'weak';

    reportOutput.innerHTML = `
        <div class="report-container">
            <div class="report-header">
                <h2>Business Match Analysis Report</h2>
                <div class="score-badge ${badgeColor}">
                    Match Score: <strong>${report.match_score}</strong>
                </div>
            </div>

            <div class="summary-card">
                <h3>Executive Summary</h3>
                <p>${report.summary}</p>
            </div>

            <div class="comparison-grid">
                <div class="factor-card similarities">
                    <h3>✅ Similarities</h3>
                    <ul>${createListItems(report.similarities)}</ul>
                </div>
                <div class="factor-card differences">
                    <h3>❌ Differences</h3>
                    <ul>${createListItems(report.differences)}</ul>
                </div>
            </div>
        </div>
    `;
}