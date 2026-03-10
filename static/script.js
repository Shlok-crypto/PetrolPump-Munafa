const refreshInterval = 60; // seconds
let timeRemaining = refreshInterval;
let progressInterval = null;

// Settings Configuration
let fipoConfig = {
    base_retail_petrol: 94.69,
    critical_brent_level: 115.00,
    critical_inr_level: 92.00,
    tank_capacity_liters: 20000
};

function loadConfig() {
    const saved = localStorage.getItem('fipoConfig');
    if (saved) {
        try {
            fipoConfig = { ...fipoConfig, ...JSON.parse(saved) };
        } catch (e) {
            console.error('Failed to parse saved config', e);
        }
    }
}

function saveConfig() {
    localStorage.setItem('fipoConfig', JSON.stringify(fipoConfig));
}

async function fetchFipoData() {
    try {
        const queryParams = new URLSearchParams(fipoConfig).toString();
        const response = await fetch(`/api/predict?${queryParams}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        updateDashboard(data);
        resetTimer();
    } catch (error) {
        console.error('Error fetching FIPO data:', error);
        const rationaleEl = document.getElementById('rationale-text');
        if (rationaleEl) rationaleEl.textContent = 'Connection error. Retrying...';
    }
}

function updateDashboard(data) {
    // Basic values
    animateValue('brent-val', parseFloat(document.getElementById('brent-val').textContent) || 0, data.indian_basket, 1000, 2);
    animateValue('inr-val', parseFloat(document.getElementById('inr-val').textContent) || 0, data.usd_inr, 1000, 2);
    // Profit Calculator setup
    const hikeInput = document.getElementById('predicted-hike-input');
    if (data.predicted_hike_per_liter !== undefined) {
        hikeInput.value = data.predicted_hike_per_liter.toFixed(1);
    }

    recalculateProfit();

    const mcxValElement = document.getElementById('mcx-val');
    if (typeof data.mcx_percent === 'number') {
        animateValue('mcx-val', parseFloat(mcxValElement.textContent) || 0, data.mcx_percent, 1000, 2);
    } else {
        mcxValElement.textContent = data.mcx_percent || "N/A";
    }

    document.getElementById('rationale-text').textContent = data.rationale;

    // Update individual card rationales
    function updateCardRationale(id, text, recommendation) {
        const el = document.getElementById(id);
        if (!el) return;
        if (text) {
            el.textContent = text;
            const recClass = recommendation.toLowerCase().replace('_', '-');
            el.className = `card-rationale show ${recClass}`;
        } else {
            el.className = 'card-rationale';
            el.textContent = '';
        }
    }

    updateCardRationale('brent-rat', data.rationale_brent, data.recommendation);
    updateCardRationale('inr-rat', data.rationale_inr, data.recommendation);
    updateCardRationale('mcx-rat', data.rationale_mcx, data.recommendation);
    updateCardRationale('news-rat', data.rationale_news, data.recommendation);

    const newsList = document.getElementById('news-list');
    if (newsList && data.news_headlines) {
        newsList.innerHTML = '';
        if (data.news_headlines.length > 0) {
            data.news_headlines.forEach(headline => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <a href="${headline.link}" target="_blank" class="news-item news-link">
                        <div class="news-content">
                            <span class="news-title">${headline.title}</span>
                            <span class="news-source">${headline.source}</span>
                        </div>
                        <span class="news-time">${headline.time}</span>
                    </a>
                `;
                newsList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.className = 'news-item empty-news';
            li.textContent = 'No relevant news catalysts at this time.';
            newsList.appendChild(li);
        }
    }

    // Time
    const date = new Date(data.timestamp);
    document.getElementById('last-updated').textContent = `Updated: ${date.toLocaleTimeString()}`;

    // Probability Circle
    const probCircle = document.getElementById('prob-circle-path');
    const probText = document.getElementById('prob-text');

    probCircle.setAttribute('stroke-dasharray', `${data.hike_probability}, 100`);
    animateValue('prob-text', parseInt(probText.textContent) || 0, data.hike_probability, 1000, 0, '%');

    // Probability Colors
    let strokeColor = '';
    if (data.hike_probability > 70) {
        strokeColor = 'var(--accent-red)';
    } else if (data.hike_probability > 40) {
        strokeColor = 'var(--accent-yellow)';
    } else {
        strokeColor = 'var(--accent-green)';
    }
    probCircle.style.stroke = strokeColor;
    probText.style.fill = strokeColor;

    // Recommendation Badge
    const badge = document.getElementById('recommendation-badge');
    badge.className = 'badge'; // Reset
    if (data.recommendation === 'MAX_INDENT') {
        badge.textContent = 'MAX INDENT';
        badge.classList.add('max-indent');
    } else if (data.recommendation === 'MINIMIZE') {
        badge.textContent = 'MINIMIZE';
        badge.classList.add('minimize');
    } else {
        badge.textContent = 'NORMAL';
        badge.classList.add('normal');
    }
}

function recalculateProfit() {
    const tankLiters = parseFloat(document.getElementById('tank-cap-input').value) || 0;
    const hikePerLiter = parseFloat(document.getElementById('predicted-hike-input').value) || 0;
    const commissionPerLiter = 3.2; // Fixed requirement

    const availableSpace = Math.max(0, fipoConfig.tank_capacity_liters - tankLiters);

    const extraGain = availableSpace * hikePerLiter;
    const commissionTotal = fipoConfig.tank_capacity_liters * commissionPerLiter;
    const totalGain = extraGain + commissionTotal;

    // Update dynamically without animation so it feels instant
    document.getElementById('extra-gain-val').textContent = Math.floor(extraGain).toLocaleString();
    const summaryGainEl = document.getElementById('summary-gain-val');
    if (summaryGainEl) summaryGainEl.textContent = Math.floor(extraGain).toLocaleString();

    // Update Summary Per-Liter Breakdown
    const summaryHikeEl = document.getElementById('summary-hike-val');
    if (summaryHikeEl) summaryHikeEl.textContent = hikePerLiter.toFixed(1);

    const summaryCombinedEl = document.getElementById('summary-combined-val');
    if (summaryCombinedEl) summaryCombinedEl.textContent = (hikePerLiter + commissionPerLiter).toFixed(1);

    document.getElementById('dealer-commission-total').textContent = commissionTotal.toLocaleString(undefined, { maximumFractionDigits: 1 });
    document.getElementById('total-gain-val').textContent = Math.floor(totalGain).toLocaleString();

    const msg = document.getElementById('tank-full-msg');
    if (msg) {
        if (availableSpace <= 0) {
            msg.style.display = 'block';
        } else {
            msg.style.display = 'none';
        }
    }
}

// Number animation util
function animateValue(id, start, end, duration, decimals = 0, suffix = '') {
    if (start === end) return;
    const obj = document.getElementById(id);
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        // easeOutQuart
        const ease = 1 - Math.pow(1 - progress, 4);
        let current = start + ease * (end - start);

        obj.textContent = (decimals > 0 ? current.toFixed(decimals) : Math.floor(current).toLocaleString()) + suffix;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            // ensure exact end value
            obj.textContent = (decimals > 0 ? end.toFixed(decimals) : end.toLocaleString()) + suffix;
        }
    };
    window.requestAnimationFrame(step);
}

function resetTimer() {
    timeRemaining = refreshInterval;
    const progressBar = document.getElementById('refresh-progress');

    if (progressInterval) clearInterval(progressInterval);

    progressInterval = setInterval(() => {
        timeRemaining--;
        const percentage = ((refreshInterval - timeRemaining) / refreshInterval) * 100;
        progressBar.style.width = `${percentage}%`;

        if (timeRemaining <= 0) {
            clearInterval(progressInterval);
            fetchFipoData();
        }
    }, 1000);
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    fetchFipoData();

    const tankInput = document.getElementById('tank-cap-input');
    const hikeInput = document.getElementById('predicted-hike-input');

    if (tankInput) {
        tankInput.max = fipoConfig.tank_capacity_liters;
        tankInput.addEventListener('input', recalculateProfit);
    }
    if (hikeInput) hikeInput.addEventListener('input', recalculateProfit);

    // Toggle expand logic
    const profitCard = document.getElementById('profit-calculator-card');
    const summaryView = document.getElementById('calculator-summary');
    const expandedView = document.getElementById('calculator-expanded');
    const expandIcon = document.getElementById('expand-icon');
    const cardHeader = document.getElementById('profit-card-header');

    if (profitCard && summaryView && expandedView && expandIcon && cardHeader) {
        const toggleExpand = () => {
            if (expandedView.style.display === 'none') {
                expandedView.style.display = 'block';
                summaryView.style.display = 'none';
                expandIcon.textContent = '▲ Click to collapse';
            } else {
                expandedView.style.display = 'none';
                summaryView.style.display = 'block';
                expandIcon.textContent = '▼ Click to expand';
            }
        };

        // Allow clicking the card itself to expand if it's currently collapsed
        profitCard.addEventListener('click', (e) => {
            if (expandedView.style.display === 'none') {
                toggleExpand();
            }
        });

        // Allow clicking the header to toggle (both expand and collapse)
        cardHeader.addEventListener('click', (e) => {
            e.stopPropagation(); // prevent card click from firing again
            toggleExpand();
        });

        // Ensure clicking inside the expanded view doesn't collapse it
        expandedView.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    // Modal Logic
    const settingsBtn = document.getElementById('settings-btn');
    const closeSettingsBtn = document.getElementById('close-settings-btn');
    const cancelSettingsBtn = document.getElementById('cancel-settings-btn');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const settingsModal = document.getElementById('settings-modal');

    // Inputs
    const basePetrolIn = document.getElementById('setting-base-petrol');
    const critBrentIn = document.getElementById('setting-critical-brent');
    const critInrIn = document.getElementById('setting-critical-inr');
    const tankCapIn = document.getElementById('setting-tank-capacity');

    const openSettings = () => {
        if (basePetrolIn) basePetrolIn.value = fipoConfig.base_retail_petrol;
        if (critBrentIn) critBrentIn.value = fipoConfig.critical_brent_level;
        if (critInrIn) critInrIn.value = fipoConfig.critical_inr_level;
        if (tankCapIn) tankCapIn.value = fipoConfig.tank_capacity_liters;
        if (settingsModal) settingsModal.style.display = 'flex';
    };

    const closeSettings = () => {
        if (settingsModal) settingsModal.style.display = 'none';
    };

    if (settingsBtn) settingsBtn.addEventListener('click', openSettings);
    if (closeSettingsBtn) closeSettingsBtn.addEventListener('click', closeSettings);
    if (cancelSettingsBtn) cancelSettingsBtn.addEventListener('click', closeSettings);

    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', () => {
            fipoConfig.base_retail_petrol = parseFloat(basePetrolIn.value) || fipoConfig.base_retail_petrol;
            fipoConfig.critical_brent_level = parseFloat(critBrentIn.value) || fipoConfig.critical_brent_level;
            fipoConfig.critical_inr_level = parseFloat(critInrIn.value) || fipoConfig.critical_inr_level;
            fipoConfig.tank_capacity_liters = parseInt(tankCapIn.value) || fipoConfig.tank_capacity_liters;

            saveConfig();

            if (tankInput) tankInput.max = fipoConfig.tank_capacity_liters;

            recalculateProfit();
            fetchFipoData();
            closeSettings();
        });
    }

    // Click outside modal content to close
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            closeSettings();
        }
    });

});
