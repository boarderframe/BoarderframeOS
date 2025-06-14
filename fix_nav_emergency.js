// Emergency Navigation Fix for BoarderframeOS Corporate HQ
// Copy and paste this entire script into the browser console

console.log('[EMERGENCY FIX] Installing navigation fix...');

// 1. Define a working showTab function
window.showTab = function(tabName) {
    console.log('[FIX] Switching to tab:', tabName);

    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
        tab.style.display = 'none';
    });

    // Show selected tab
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
        selectedTab.style.display = 'block';
        console.log('[FIX] Tab shown:', tabName);
    } else {
        console.error('[FIX] Tab not found:', tabName);
    }

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });

    const activeLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }

    // Special handling for metrics tab
    if (tabName === 'metrics') {
        const metricsContent = document.getElementById('metrics-content');
        if (metricsContent && metricsContent.querySelector('.fa-spinner')) {
            console.log('[FIX] Auto-loading metrics...');
            if (typeof loadMetricsData === 'function') {
                loadMetricsData();
            }
        }
    }
};

// 2. Remove all existing handlers and add new ones
console.log('[FIX] Installing click handlers...');
document.querySelectorAll('.nav-link').forEach((link, index) => {
    // Clear any existing handlers
    const newLink = link.cloneNode(true);
    link.parentNode.replaceChild(newLink, link);

    // Add new handler
    newLink.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const tabName = this.getAttribute('data-tab');
        console.log('[FIX] Nav clicked:', tabName);
        if (tabName) {
            window.showTab(tabName);
        }
        return false;
    });

    // Ensure it's clickable
    newLink.style.pointerEvents = 'auto';
    newLink.style.cursor = 'pointer';
    newLink.disabled = false;

    console.log(`[FIX] Handler installed for nav item ${index}: ${newLink.getAttribute('data-tab')}`);
});

// 3. Fix any z-index issues
document.querySelectorAll('.nav-link').forEach(link => {
    link.style.position = 'relative';
    link.style.zIndex = '1005';
});

// 4. Test the fix
console.log('[FIX] Testing navigation...');
const testTabs = ['dashboard', 'agents', 'leaders', 'departments'];
let currentIndex = 0;

console.log('[FIX] Current tabs found:');
document.querySelectorAll('.tab-content').forEach(tab => {
    console.log(`  - ${tab.id} (display: ${tab.style.display}, active: ${tab.classList.contains('active')})`);
});

console.log('\n[FIX] ✅ Navigation fix installed!');
console.log('[FIX] Try clicking the menu items now.');
console.log('[FIX] If it still doesn\'t work, type: showTab("agents") to test directly');

// 5. Add keyboard shortcuts as bonus
document.addEventListener('keydown', function(e) {
    if (e.altKey) {
        switch(e.key) {
            case '1': showTab('dashboard'); break;
            case '2': showTab('agents'); break;
            case '3': showTab('leaders'); break;
            case '4': showTab('departments'); break;
            case '5': showTab('divisions'); break;
            case '6': showTab('registry'); break;
            case '7': showTab('database'); break;
            case '8': showTab('metrics'); break;
            case '9': showTab('services'); break;
            case '0': showTab('settings'); break;
        }
    }
});

console.log('[FIX] Bonus: Use Alt+1 through Alt+0 for keyboard navigation');

// 6. Show current status
setTimeout(() => {
    const activeTab = document.querySelector('.tab-content.active');
    if (activeTab) {
        console.log('[FIX] Currently showing tab:', activeTab.id);
    } else {
        console.log('[FIX] No active tab found, showing dashboard...');
        showTab('dashboard');
    }
}, 100);
