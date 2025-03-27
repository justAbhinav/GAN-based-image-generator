// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', () => {
    const digitInput = document.getElementById('digit');
    const generateButton = document.querySelector('button');
    
    // Initially disable the button
    generateButton.disabled = true;
    
    // Add input validation
    digitInput.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        if (value < 0) e.target.value = 0;
        if (value > 9) e.target.value = 9;
        
        // Enable/disable button based on input validity
        generateButton.disabled = e.target.value === '' || isNaN(value) || value < 0 || value > 9;
    });
});

async function generate() {
    const digit = document.getElementById('digit').value;
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const result = document.getElementById('result');
    
    // Input validation
    if (digit < 0 || digit > 9) {
        showError('Please enter a number between 0 and 9');
        return;
    }

    // Show loading state
    showLoading();
    hideError();
    hideResult();

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `digit=${digit}`
        });

        if (!response.ok) {
            throw new Error('Failed to generate digit');
        }

        const blob = await response.blob();
        result.src = URL.createObjectURL(blob);
        showResult();
        hideError();
    } catch (err) {
        showError('An error occurred while generating the digit. Please try again.');
    } finally {
        hideLoading();
    }
}

function showLoading() {
    document.getElementById('loading').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading').classList.remove('active');
}

function showError(message) {
    const error = document.getElementById('error');
    error.textContent = message;
    error.classList.add('active');
}

function hideError() {
    document.getElementById('error').classList.remove('active');
}

function showResult() {
    const result = document.getElementById('result');
    result.style.display = 'block';
}

function hideResult() {
    const result = document.getElementById('result');
    result.style.display = 'none';
} 