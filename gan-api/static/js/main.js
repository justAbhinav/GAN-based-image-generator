// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', () => {
    const classInput = document.getElementById('class-input');
    const fashionSelect = document.getElementById('fashion-select');
    const generateButton = document.getElementById('generate-btn');
    const modelButtons = document.querySelectorAll('.model-btn');
    
    // Initially disable the generate button
    generateButton.disabled = true;
    
    // Add input validation for number input
    classInput.addEventListener('input', (e) => {
        let value = parseInt(e.target.value);
        
        // Handle empty input
        if (e.target.value === '') {
            generateButton.disabled = true;
            return;
        }
        
        // Handle invalid input
        if (isNaN(value)) {
            generateButton.disabled = true;
            return;
        }
        
        // Clamp value between 0 and 9
        if (value < 0) {
            value = 0;
            e.target.value = 0;
        }
        if (value > 9) {
            value = 9;
            e.target.value = 9;
        }
        
        // Enable/disable generate button based on input validity
        generateButton.disabled = false;
    });

    // Add change event for fashion select
    fashionSelect.addEventListener('change', () => {
        generateButton.disabled = !fashionSelect.value;
    });

    // Handle model selection
    modelButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active state
            modelButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // Update input method
            const model = button.dataset.model;
            if (model === 'mnist') {
                classInput.style.display = 'block';
                fashionSelect.style.display = 'none';
                classInput.value = '';
            } else {
                classInput.style.display = 'none';
                fashionSelect.style.display = 'block';
                fashionSelect.value = '';
            }

            // Reset the result and error states
            hideResult();
            hideError();
            
            // Disable generate button
            generateButton.disabled = true;
        });
    });
});

async function generate() {
    const classInput = document.getElementById('class-input');
    const fashionSelect = document.getElementById('fashion-select');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const result = document.getElementById('result');
    const activeModel = document.querySelector('.model-btn.active').dataset.model;
    
    // Get the selected value based on active model
    const classId = activeModel === 'mnist' ? classInput.value : fashionSelect.value;
    
    // Input validation
    if (!classId || classId < 0 || classId > 9) {
        showError('Please select a valid class');
        return;
    }

    // Show loading state
    showLoading();
    hideError();
    hideResult();

    try {
        const endpoint = activeModel === 'mnist' ? '/generate/mnist' : '/generate/fashion';
        const formData = new FormData();
        formData.append(activeModel === 'mnist' ? 'digit' : 'class_id', classId);

        console.log(`Sending request to ${endpoint} with classId: ${classId}`);
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Server error: ${response.status} - ${errorText}`);
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }

        const contentType = response.headers.get('content-type');
        console.log(`Response content type: ${contentType}`);
        
        if (!contentType || !contentType.includes('image/png')) {
            console.error(`Unexpected content type: ${contentType}`);
            throw new Error('Server returned invalid content type');
        }

        const blob = await response.blob();
        console.log(`Received image blob of size: ${blob.size}`);
        
        if (blob.size === 0) {
            throw new Error('Received empty image data');
        }

        // Revoke any existing object URL to prevent memory leaks
        if (result.src) {
            URL.revokeObjectURL(result.src);
        }

        const imageUrl = URL.createObjectURL(blob);
        console.log(`Created image URL: ${imageUrl}`);

        // Set up image load handlers before setting the source
        result.onload = () => {
            console.log('Image loaded successfully');
            hideLoading();
        };
        
        result.onerror = (e) => {
            console.error('Error loading image:', e);
            showError('Failed to load generated image');
            hideLoading();
        };

        // Set the image source
        result.src = imageUrl;
        result.style.display = 'block';
        showResult();
    } catch (err) {
        console.error('Generation error:', err);
        showError(err.message);
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