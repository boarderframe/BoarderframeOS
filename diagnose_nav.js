// Copy and paste this entire script into the browser console at http://localhost:8888

console.log("=== BoarderframeOS Navigation Diagnostics ===");

// 1. Check if showTab exists
console.log("\n1. Checking showTab function:");
if (typeof showTab === 'function') {
    console.log("✅ showTab is defined as a function");
} else if (typeof window.showTab === 'function') {
    console.log("✅ window.showTab is defined");
    // Make it available globally
    showTab = window.showTab;
} else {
    console.log("❌ showTab is NOT defined");
}

// 2. Check for JavaScript errors
console.log("\n2. Checking for JavaScript errors:");
const scripts = document.querySelectorAll('script');
console.log(`Found ${scripts.length} script tags`);

// 3. Check navigation elements
console.log("\n3. Checking navigation elements:");
const navLinks = document.querySelectorAll('.nav-link');
console.log(`Found ${navLinks.length} navigation links:`);
navLinks.forEach((link, i) => {
    const tabName = link.getAttribute('data-tab');
    const onclick = link.getAttribute('onclick');
    console.log(`  ${i+1}. ${link.textContent.trim()} -> Tab: ${tabName}, onclick: ${onclick}`);
});

// 4. Check tab content elements
console.log("\n4. Checking tab content elements:");
const tabs = document.querySelectorAll('.tab-content');
console.log(`Found ${tabs.length} tab contents:`);
tabs.forEach((tab, i) => {
    console.log(`  ${i+1}. ID: ${tab.id}, Display: ${tab.style.display}, Classes: ${tab.className}`);
});

// 5. Try to manually fix navigation
console.log("\n5. Attempting manual fix:");
if (typeof showTab !== 'function' && typeof window.showTab !== 'function') {
    console.log("Creating showTab function...");
    window.showTab = function(tabName) {
        console.log('[MANUAL FIX] Switching to tab:', tabName);

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
        }

        // Update nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`.nav-link[data-tab="${tabName}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    };

    // Rebind all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.onclick = function() {
            const tab = this.getAttribute('data-tab');
            window.showTab(tab);
            return false;
        };
    });

    console.log("✅ Manual fix applied! Try clicking the navigation links now.");
} else {
    console.log("✅ showTab already exists, no manual fix needed.");
}

// 6. Test navigation
console.log("\n6. Testing navigation:");
console.log("Try running: showTab('agents')");
console.log("Or click any navigation link to test.");

console.log("\n=== End of diagnostics ===");
