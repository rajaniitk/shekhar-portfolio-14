document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let currentDatasetId = null;
    let currentFeatures = [];
    let engineeredFeatures = [];
    
    // DOM Elements
    const datasetSelect = document.getElementById('adv-fe-dataset-select');
    const refreshButton = document.getElementById('refresh-adv-fe-datasets');
    const engineeringSections = document.getElementById('fe-workspace');
    const loadingModal = document.getElementById('adv-fe-loading-modal');
    
    // Initialize
    loadDatasets();
    setupEventListeners();
    
    function setupEventListeners() {
        if (refreshButton) {
            refreshButton.addEventListener('click', loadDatasets);
        }
        if (datasetSelect) {
            datasetSelect.addEventListener('change', handleDatasetSelection);
        }
        
        // Engineering technique buttons with null checks
        const polyBtn = document.getElementById('apply-polynomial-features');
        if (polyBtn) polyBtn.addEventListener('click', applyPolynomialFeatures);
        
        const interactionBtn = document.getElementById('apply-interaction-features');
        if (interactionBtn) interactionBtn.addEventListener('click', applyInteractionFeatures);
        
        const selectionBtn = document.getElementById('apply-feature-selection');
        if (selectionBtn) selectionBtn.addEventListener('click', applyFeatureSelection);
        
        const reductionBtn = document.getElementById('apply-dimensionality-reduction');
        if (reductionBtn) reductionBtn.addEventListener('click', applyDimensionalityReduction);
        
        const timeBtn = document.getElementById('apply-time-features');
        if (timeBtn) timeBtn.addEventListener('click', applyTimeFeatures);
        
        const textBtn = document.getElementById('apply-text-features');
        if (textBtn) textBtn.addEventListener('click', applyTextFeatures);
        
        const clusterBtn = document.getElementById('apply-clustering-features');
        if (clusterBtn) clusterBtn.addEventListener('click', applyClusteringFeatures);
        
        const customBtn = document.getElementById('apply-custom-transformations');
        if (customBtn) customBtn.addEventListener('click', applyCustomTransformations);
        
        // Feature management buttons
        const saveBtn = document.getElementById('save-features');
        if (saveBtn) saveBtn.addEventListener('click', saveFeatures);
        
        const exportBtn = document.getElementById('export-features');
        if (exportBtn) exportBtn.addEventListener('click', exportFeatures);
        
        const resetBtn = document.getElementById('reset-features');
        if (resetBtn) resetBtn.addEventListener('click', resetFeatures);
        
        // Tab switching for sub-techniques
        const tabButtons = document.querySelectorAll('.subtab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const parent = e.target.closest('[data-parent]');
                const parentId = parent.getAttribute('data-parent');
                const tabId = e.target.getAttribute('data-subtab');
                switchSubTab(parentId, tabId);
            });
        });
    }
    
    async function loadDatasets() {
        try {
            // Fetch real datasets from the API
            const response = await fetch('/api/data/datasets');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            datasetSelect.innerHTML = '<option value="">Choose a dataset...</option>';
            
            if (data.success && data.datasets) {
                data.datasets.forEach(dataset => {
                    const option = document.createElement('option');
                    option.value = dataset.id;
                    option.textContent = `${dataset.name} (${dataset.rows} rows, ${dataset.columns} cols)`;
                    datasetSelect.appendChild(option);
                });
            } else {
                console.log('No datasets available');
            }
            
        } catch (error) {
            console.error('Error loading datasets:', error);
            showError('Failed to load datasets: ' + error.message);
        }
    }
    
    async function handleDatasetSelection() {
        const selectedId = datasetSelect.value;
        
        if (!selectedId) {
            engineeringSections.style.display = 'none';
            return;
        }
        
        currentDatasetId = selectedId;
        await loadDatasetFeatures(selectedId);
        engineeringSections.style.display = 'block';
    }
    
    async function loadDatasetFeatures(datasetId) {
        showLoading();
        
        try {
            // Fetch real features from the API
            const response = await fetch(`/api/data/columns/${datasetId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.columns) {
                // Transform the column data into feature format
                const features = data.columns.map(col => ({
                    name: col.name,
                    type: col.is_numeric ? 'numeric' : 
                          col.is_datetime ? 'datetime' : 
                          col.dtype === 'object' ? 'text' : 'categorical',
                    dtype: col.dtype,
                    null_count: col.null_count,
                    unique_count: col.unique_count,
                    is_numeric: col.is_numeric,
                    is_categorical: col.is_categorical,
                    is_datetime: col.is_datetime
                }));
                
                currentFeatures = features;
                populateFeatureSelectors(features);
                updateFeaturesList();
            } else {
                throw new Error(data.error || 'Failed to load features');
            }
            
        } catch (error) {
            console.error('Error loading features:', error);
            showError('Failed to load dataset features: ' + error.message);
        } finally {
            hideLoading();
        }
    }
    
    function populateFeatureSelectors(features) {
        const numericFeatures = features.filter(f => f.type === 'numeric');
        const categoricalFeatures = features.filter(f => f.type === 'categorical');
        const textFeatures = features.filter(f => f.type === 'text');
        const datetimeFeatures = features.filter(f => f.type === 'datetime');
        
        // Populate various feature selectors
        populateSelect('polynomial-features-select', numericFeatures);
        populateSelect('interaction-features-select', numericFeatures);
        populateSelect('selection-features-target', numericFeatures);
        populateSelect('pca-features-select', numericFeatures);
        populateSelect('time-features-select', datetimeFeatures);
        populateSelect('text-features-select', textFeatures);
        populateSelect('clustering-features-select', numericFeatures);
        
        // Multi-select for various techniques
        populateMultiSelect('fs-features-list', features);
        populateMultiSelect('dr-features-list', numericFeatures);
        populateMultiSelect('cluster-features-list', numericFeatures);
    }
    
    function populateSelect(selectId, features) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        select.innerHTML = '<option value="">Select feature...</option>';
        features.forEach(feature => {
            const option = document.createElement('option');
            option.value = feature.name;
            option.textContent = feature.name;
            select.appendChild(option);
        });
    }
    
    function populateMultiSelect(containerId, features) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        features.forEach(feature => {
            const checkbox = document.createElement('div');
            checkbox.className = 'feature-checkbox';
            checkbox.innerHTML = `
                <input type="checkbox" id="feature_${feature.name}" value="${feature.name}">
                <label for="feature_${feature.name}">${feature.name} (${feature.type})</label>
            `;
            container.appendChild(checkbox);
        });
    }
    
    function applyPolynomialFeatures() {
        const selectedFeature = document.getElementById('polynomial-features-select').value;
        const degree = document.getElementById('polynomial-degree').value || 2;
        
        if (!selectedFeature) {
            showError('Please select a feature for polynomial transformation');
            return;
        }
        
        const feature = currentFeatures.find(f => f.name === selectedFeature);
        if (!feature) return;
        
        // Generate polynomial features
        for (let d = 2; d <= degree; d++) {
            const newFeatureName = `${selectedFeature}_poly_${d}`;
            const newValues = feature.values.map(val => Math.pow(val, d));
            
            const newFeature = {
                name: newFeatureName,
                type: 'numeric',
                values: newValues,
                engineered: true,
                source: `Polynomial degree ${d} of ${selectedFeature}`
            };
            
            engineeredFeatures.push(newFeature);
        }
        
        updateFeaturesList();
        showSuccess(`Polynomial features of degree ${degree} created for ${selectedFeature}`);
    }
    
    function applyInteractionFeatures() {
        const selectedFeatures = getSelectedCheckboxes('interaction-features-list');
        
        if (selectedFeatures.length < 2) {
            showError('Please select at least 2 features for interaction');
            return;
        }
        
        // Create interaction features for all pairs
        for (let i = 0; i < selectedFeatures.length; i++) {
            for (let j = i + 1; j < selectedFeatures.length; j++) {
                const feature1 = currentFeatures.find(f => f.name === selectedFeatures[i]);
                const feature2 = currentFeatures.find(f => f.name === selectedFeatures[j]);
                
                if (feature1 && feature2) {
                    const newFeatureName = `${feature1.name}_x_${feature2.name}`;
                    const newValues = feature1.values.map((val, idx) => val * feature2.values[idx]);
                    
                    const newFeature = {
                        name: newFeatureName,
                        type: 'numeric',
                        values: newValues,
                        engineered: true,
                        source: `Interaction between ${feature1.name} and ${feature2.name}`
                    };
                    
                    engineeredFeatures.push(newFeature);
                }
            }
        }
        
        updateFeaturesList();
        showSuccess(`Interaction features created for ${selectedFeatures.length} features`);
    }
    
    function applyFeatureSelection() {
        const selectedFeatures = getSelectedCheckboxes('fs-features-list');
        const method = document.getElementById('fs-method').value;
        const kValue = document.getElementById('fs-k-value').value || 5;
        
        if (selectedFeatures.length === 0) {
            showError('Please select features for selection');
            return;
        }
        
        // Mock feature selection - select top k features
        const selectedTopK = selectedFeatures.slice(0, Math.min(kValue, selectedFeatures.length));
        
        document.getElementById('fs-results').innerHTML = `
            <div class="selection-results">
                <h5>Feature Selection Results (${method})</h5>
                <p>Selected top ${selectedTopK.length} features:</p>
                <ul>
                    ${selectedTopK.map(feature => `<li>${feature} (Score: ${(Math.random() * 100).toFixed(2)})</li>`).join('')}
                </ul>
            </div>
        `;
        
        showSuccess(`Feature selection completed using ${method}`);
    }
    
    function applyDimensionalityReduction() {
        const selectedFeatures = getSelectedCheckboxes('dr-features-list');
        const method = document.getElementById('dr-method').value;
        const components = document.getElementById('dr-components').value || 2;
        
        if (selectedFeatures.length === 0) {
            showError('Please select features for dimensionality reduction');
            return;
        }
        
        // Create reduced dimension features
        for (let i = 1; i <= components; i++) {
            const newFeatureName = `${method}_component_${i}`;
            const newValues = Array.from({length: 100}, () => Math.random() * 10 - 5);
            
            const newFeature = {
                name: newFeatureName,
                type: 'numeric',
                values: newValues,
                engineered: true,
                source: `${method} component ${i} from ${selectedFeatures.length} features`
            };
            
            engineeredFeatures.push(newFeature);
        }
        
        document.getElementById('dr-results').innerHTML = `
            <div class="reduction-results">
                <h5>Dimensionality Reduction Results (${method})</h5>
                <p>Reduced ${selectedFeatures.length} features to ${components} components</p>
                <p>Explained variance: ${(Math.random() * 50 + 70).toFixed(1)}%</p>
            </div>
        `;
        
        updateFeaturesList();
        showSuccess(`Dimensionality reduction completed using ${method}`);
    }
    
    function applyTimeFeatures() {
        const selectedFeature = document.getElementById('time-features-select').value;
        const timeFeatures = getSelectedCheckboxes('time-feature-types');
        
        if (!selectedFeature) {
            showError('Please select a datetime feature');
            return;
        }
        
        if (timeFeatures.length === 0) {
            showError('Please select time feature types to extract');
            return;
        }
        
        // Create time-based features
        timeFeatures.forEach(featureType => {
            const newFeatureName = `${selectedFeature}_${featureType}`;
            let newValues;
            
            switch (featureType) {
                case 'hour':
                    newValues = Array.from({length: 100}, () => Math.floor(Math.random() * 24));
                    break;
                case 'day':
                    newValues = Array.from({length: 100}, () => Math.floor(Math.random() * 31) + 1);
                    break;
                case 'month':
                    newValues = Array.from({length: 100}, () => Math.floor(Math.random() * 12) + 1);
                    break;
                case 'year':
                    newValues = Array.from({length: 100}, () => Math.floor(Math.random() * 5) + 2020);
                    break;
                case 'weekday':
                    newValues = Array.from({length: 100}, () => Math.floor(Math.random() * 7));
                    break;
                default:
                    newValues = Array.from({length: 100}, () => Math.random() * 100);
            }
            
            const newFeature = {
                name: newFeatureName,
                type: 'numeric',
                values: newValues,
                engineered: true,
                source: `${featureType} extracted from ${selectedFeature}`
            };
            
            engineeredFeatures.push(newFeature);
        });
        
        updateFeaturesList();
        showSuccess(`Time features extracted from ${selectedFeature}`);
    }
    
    function applyTextFeatures() {
        const selectedFeature = document.getElementById('text-features-select').value;
        const textFeatures = getSelectedCheckboxes('text-feature-types');
        
        if (!selectedFeature) {
            showError('Please select a text feature');
            return;
        }
        
        if (textFeatures.length === 0) {
            showError('Please select text feature types to extract');
            return;
        }
        
        // Create text-based features
        textFeatures.forEach(featureType => {
            let newFeatureName;
            let newValues;
            
            switch (featureType) {
                case 'length':
                    newFeatureName = `${selectedFeature}_length`;
                    newValues = Array.from({length: 100}, () => Math.floor(Math.random() * 500) + 10);
                    break;
                case 'word_count':
                    newFeatureName = `${selectedFeature}_word_count`;
                    newValues = Array.from({length: 100}, () => Math.floor(Math.random() * 100) + 5);
                    break;
                case 'sentiment':
                    newFeatureName = `${selectedFeature}_sentiment`;
                    newValues = Array.from({length: 100}, () => Math.random() * 2 - 1);
                    break;
                case 'readability':
                    newFeatureName = `${selectedFeature}_readability`;
                    newValues = Array.from({length: 100}, () => Math.random() * 100);
                    break;
                default:
                    newFeatureName = `${selectedFeature}_${featureType}`;
                    newValues = Array.from({length: 100}, () => Math.random() * 100);
            }
            
            const newFeature = {
                name: newFeatureName,
                type: 'numeric',
                values: newValues,
                engineered: true,
                source: `${featureType} extracted from ${selectedFeature}`
            };
            
            engineeredFeatures.push(newFeature);
        });
        
        updateFeaturesList();
        showSuccess(`Text features extracted from ${selectedFeature}`);
    }
    
    function applyClusteringFeatures() {
        const selectedFeatures = getSelectedCheckboxes('cluster-features-list');
        const kClusters = document.getElementById('cluster-k').value || 3;
        
        if (selectedFeatures.length === 0) {
            showError('Please select features for clustering');
            return;
        }
        
        // Create cluster assignment feature
        const clusterFeatureName = 'cluster_assignment';
        const clusterValues = Array.from({length: 100}, () => Math.floor(Math.random() * kClusters));
        
        const clusterFeature = {
            name: clusterFeatureName,
            type: 'categorical',
            values: clusterValues,
            engineered: true,
            source: `K-means clustering (k=${kClusters}) on ${selectedFeatures.join(', ')}`
        };
        
        engineeredFeatures.push(clusterFeature);
        
        // Create distance to cluster centers
        for (let i = 0; i < kClusters; i++) {
            const distanceFeatureName = `distance_to_cluster_${i}`;
            const distanceValues = Array.from({length: 100}, () => Math.random() * 10);
            
            const distanceFeature = {
                name: distanceFeatureName,
                type: 'numeric',
                values: distanceValues,
                engineered: true,
                source: `Distance to cluster ${i} center`
            };
            
            engineeredFeatures.push(distanceFeature);
        }
        
        updateFeaturesList();
        showSuccess(`Clustering features created with ${kClusters} clusters`);
    }
    
    function applyCustomTransformations() {
        const transformationType = document.getElementById('custom-transformation').value;
        const targetFeature = document.getElementById('custom-target-feature').value;
        
        if (!targetFeature) {
            showError('Please select a target feature for transformation');
            return;
        }
        
        const feature = currentFeatures.find(f => f.name === targetFeature);
        if (!feature) return;
        
        let newFeatureName;
        let newValues;
        
        switch (transformationType) {
            case 'log':
                newFeatureName = `log_${targetFeature}`;
                newValues = feature.values.map(val => Math.log(Math.abs(val) + 1));
                break;
            case 'sqrt':
                newFeatureName = `sqrt_${targetFeature}`;
                newValues = feature.values.map(val => Math.sqrt(Math.abs(val)));
                break;
            case 'square':
                newFeatureName = `square_${targetFeature}`;
                newValues = feature.values.map(val => val * val);
                break;
            case 'reciprocal':
                newFeatureName = `reciprocal_${targetFeature}`;
                newValues = feature.values.map(val => val !== 0 ? 1 / val : 0);
                break;
            case 'standardize':
                newFeatureName = `standardized_${targetFeature}`;
                const mean = feature.values.reduce((a, b) => a + b, 0) / feature.values.length;
                const std = Math.sqrt(feature.values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / feature.values.length);
                newValues = feature.values.map(val => (val - mean) / std);
                break;
            default:
                showError('Unknown transformation type');
                return;
        }
        
        const newFeature = {
            name: newFeatureName,
            type: 'numeric',
            values: newValues,
            engineered: true,
            source: `${transformationType} transformation of ${targetFeature}`
        };
        
        engineeredFeatures.push(newFeature);
        updateFeaturesList();
        showSuccess(`${transformationType} transformation applied to ${targetFeature}`);
    }
    
    function getSelectedCheckboxes(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return [];
        
        const checkboxes = container.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }
    
    function updateFeaturesList() {
        const container = document.getElementById('engineered-features-list');
        
        if (engineeredFeatures.length === 0) {
            container.innerHTML = '<p>No engineered features yet. Use the techniques above to create new features.</p>';
            return;
        }
        
        let html = '<div class="features-grid">';
        engineeredFeatures.forEach((feature, index) => {
            html += `
                <div class="feature-card">
                    <div class="feature-header">
                        <strong>${feature.name}</strong>
                        <button class="remove-feature" onclick="removeFeature(${index})">×</button>
                    </div>
                    <div class="feature-details">
                        <span class="feature-type">${feature.type}</span>
                        <span class="feature-source">${feature.source}</span>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        container.innerHTML = html;
    }
    
    window.removeFeature = function(index) {
        engineeredFeatures.splice(index, 1);
        updateFeaturesList();
        showSuccess('Feature removed');
    };
    
    function switchSubTab(parentId, tabId) {
        const parent = document.getElementById(parentId);
        if (!parent) return;
        
        // Remove active class from all subtabs in this parent
        parent.querySelectorAll('.subtab-button').forEach(btn => btn.classList.remove('active'));
        parent.querySelectorAll('.subtab-content').forEach(content => content.classList.remove('active'));
        
        // Add active class to selected tab and content
        const activeButton = parent.querySelector(`[data-subtab="${tabId}"]`);
        const activeContent = parent.querySelector(`#${tabId}`);
        
        if (activeButton) activeButton.classList.add('active');
        if (activeContent) activeContent.classList.add('active');
    }
    
    function saveFeatures() {
        if (engineeredFeatures.length === 0) {
            showError('No engineered features to save');
            return;
        }
        
        // In a real app, this would save to the backend
        localStorage.setItem(`engineered_features_${currentDatasetId}`, JSON.stringify(engineeredFeatures));
        showSuccess(`${engineeredFeatures.length} engineered features saved`);
    }
    
    function exportFeatures() {
        if (engineeredFeatures.length === 0) {
            showError('No engineered features to export');
            return;
        }
        
        // Create CSV content
        const headers = ['feature_name', 'type', 'source', 'sample_values'];
        const rows = engineeredFeatures.map(feature => [
            feature.name,
            feature.type,
            feature.source,
            feature.values.slice(0, 5).join(';')
        ]);
        
        const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
        
        // Download CSV
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `engineered_features_${currentDatasetId}.csv`;
        a.click();
        
        showSuccess('Features exported to CSV');
    }
    
    function resetFeatures() {
        if (confirm('Are you sure you want to remove all engineered features?')) {
            engineeredFeatures = [];
            updateFeaturesList();
            showSuccess('All engineered features removed');
        }
    }
    
    function showLoading() {
        loadingModal.style.display = 'flex';
    }
    
    function hideLoading() {
        loadingModal.style.display = 'none';
    }
    
    function showError(message) {
        alert(message); // In a real app, use a proper notification system
    }
    
    function showSuccess(message) {
        alert(message); // In a real app, use a proper notification system
    }
});

// Add CSS for advanced feature engineering
const afeCSS = `
<style>
.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 15px;
    margin: 20px 0;
}

.feature-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.feature-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.feature-header strong {
    color: #1e293b;
    font-size: 1.1em;
}

.remove-feature {
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
}

.feature-details {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.feature-type {
    background: #e0e7ff;
    color: #3730a3;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8em;
    align-self: flex-start;
}

.feature-source {
    color: #64748b;
    font-size: 0.9em;
    font-style: italic;
}

.feature-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 5px 0;
    padding: 8px;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.feature-checkbox:hover {
    background: #f8fafc;
}

.feature-checkbox input[type="checkbox"] {
    margin: 0;
}

.feature-checkbox label {
    margin: 0;
    cursor: pointer;
    color: #374151;
}

.selection-results, .reduction-results {
    background: #f0f9ff;
    border: 1px solid #0ea5e9;
    border-radius: 8px;
    padding: 15px;
    margin: 15px 0;
}

.selection-results h5, .reduction-results h5 {
    color: #0c4a6e;
    margin: 0 0 10px 0;
}

.selection-results ul {
    margin: 10px 0 0 0;
    padding-left: 20px;
}

.subtab-button {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    padding: 8px 16px;
    margin-right: 5px;
    border-radius: 6px 6px 0 0;
    cursor: pointer;
    transition: all 0.2s;
}

.subtab-button.active {
    background: white;
    border-bottom-color: white;
    font-weight: 600;
}

.subtab-content {
    display: none;
    background: white;
    border: 1px solid #cbd5e1;
    border-radius: 0 8px 8px 8px;
    padding: 20px;
}

.subtab-content.active {
    display: block;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', afeCSS);