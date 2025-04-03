// static/script.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Get DOM Element References ---
    // Owner Registration
    const ownerNameInput = document.getElementById('owner-name');
    const ownerPhoneInput = document.getElementById('owner-phone');
    const ownerRegStatus = document.getElementById('owner-reg-status');
    const ownerRegButton = document.querySelector('.control-box button[onclick="registerOwner()"]'); // More specific selector

    // Vehicle Registration
    const regPlateInput = document.getElementById('reg-plate');
    const vehicleOwnerPhoneInput = document.getElementById('vehicle-owner-phone');
    const regStatus = document.getElementById('reg-status');
    const regQrResult = document.getElementById('reg-qr-result');
    const vehicleRegButton = document.querySelector('.control-box button[onclick="registerVehicle()"]'); // More specific selector

    // Check-In
    const checkinStatus = document.getElementById('checkin-status');
    const checkinStep2Div = document.getElementById('checkin-step2');
    const checkinQrDataSpan = document.getElementById('checkin-qr-data');
    const checkinScanBtn = document.getElementById('checkin-scan-btn');
    const checkinConfirmBtn = document.querySelector('#checkin-step2 button[onclick="confirmCheckIn()"]');

    // Check-Out
    const checkoutStatus = document.getElementById('checkout-status');
    const checkoutStep2Div = document.getElementById('checkout-step2');
    const checkoutQrDataSpan = document.getElementById('checkout-qr-data');
    const checkoutScanBtn = document.getElementById('checkout-scan-btn');
    const checkoutConfirmBtn = document.querySelector('#checkout-step2 button[onclick="confirmCheckOut()"]');

    // Vehicle Status Check
    const statusScanBtn = document.getElementById('status-scan-btn');
    const statusResultDisplay = document.getElementById('status-result-display');
    const statusCheckStatus = document.getElementById('status-check-status');

    // API Base URL
    const API_BASE_URL = "http://127.0.0.1:8000/api"; // Adjust if needed

    // --- State Variables ---
    let scannedQrForCheckin = null;
    let scannedQrForCheckout = null;
    let scannedQrForStatus = null;

    // --- Helper Functions ---

    function updateStatus(element, message, isError = false) {
        if (!element) return;
        element.textContent = message;
        element.className = 'status'; // Reset classes
        if (message) {
            element.classList.add(isError ? 'error' : 'success');
        }
    }

    function formatDateTime(dateTimeInput) {
        if (!dateTimeInput) return "";
        try {
            const date = new Date(dateTimeInput);
            if (isNaN(date.getTime())) return "Invalid Date";
            return date.toLocaleString('sv-SE', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false });
        } catch (error) { console.error("Error formatting date:", error); return "Invalid Date"; }
    }

    // --- UI Reset Functions ---
    function resetCheckInUI() {
        scannedQrForCheckin = null;
        if(checkinQrDataSpan) checkinQrDataSpan.textContent = '';
        if(checkinStep2Div) checkinStep2Div.style.display = 'none';
        if(checkinScanBtn) checkinScanBtn.style.display = 'block';
        // Don't clear status message here - let caller decide
    }
    function resetCheckOutUI() {
        scannedQrForCheckout = null;
        if(checkoutQrDataSpan) checkoutQrDataSpan.textContent = '';
        if(checkoutStep2Div) checkoutStep2Div.style.display = 'none';
        if(checkoutScanBtn) checkoutScanBtn.style.display = 'block';
        // Don't clear status message here
    }
     function resetStatusCheckUI() {
        scannedQrForStatus = null;
        // Keep result displayed until next scan or page reload
        if (statusScanBtn) statusScanBtn.style.display = 'block';
        // Don't clear status message here
    }

    // --- API Call Functions ---

    async function registerOwner() {
        console.log(">>> registerOwner function called!"); // Debug log
        if (!ownerNameInput || !ownerPhoneInput || !ownerRegStatus) { console.error("Owner registration DOM elements missing!"); return; }
        const ownerName = ownerNameInput.value.trim();
        const ownerPhone = ownerPhoneInput.value.trim();

        if (!ownerName) { updateStatus(ownerRegStatus, "Please enter owner's name.", true); return; }
        if (!ownerPhone) { updateStatus(ownerRegStatus, "Please enter owner's phone number.", true); return; }

        updateStatus(ownerRegStatus, "Registering owner...", false);
        try {
            const response = await fetch(`${API_BASE_URL}/owners`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ name: ownerName, phone_number: ownerPhone })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || `Registration failed: ${response.statusText}`);
            updateStatus(ownerRegStatus, `Owner '${result.name}' (${result.phone_number}) registered!`, false);
            ownerNameInput.value = ''; ownerPhoneInput.value = '';
        } catch (error) {
            console.error('Owner registration error:', error);
            updateStatus(ownerRegStatus, `Owner registration failed: ${error.message}`, true);
        }
    }

    async function registerVehicle() {
        console.log(">>> registerVehicle function called!"); // Debug log
        if (!regPlateInput || !vehicleOwnerPhoneInput || !regStatus || !regQrResult) { console.error("Vehicle registration DOM elements missing!"); return; }
        const licensePlate = regPlateInput.value.trim();
        const ownerPhone = vehicleOwnerPhoneInput.value.trim();

        if (!licensePlate) { updateStatus(regStatus, "Please enter license plate.", true); return; }
        if (!ownerPhone) { updateStatus(regStatus, "Please enter owner's phone number.", true); return; }

        updateStatus(regStatus, "Registering vehicle...", false);
        regQrResult.innerHTML = '';
        try {
            const response = await fetch(`${API_BASE_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ license_plate: licensePlate, owner_phone_number: ownerPhone })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || `Registration failed: ${response.statusText}`);

            updateStatus(regStatus, result.message || "Registration successful!", false);
            regPlateInput.value = ''; vehicleOwnerPhoneInput.value = '';
            regQrResult.innerHTML = `
                <p>Vehicle: ${result.vehicle.license_plate}, Owner: ${result.vehicle.owner?.name || 'N/A'} (${result.vehicle.owner?.phone_number || 'N/A'})</p>
                <p>QR Code Data: <strong>${result.vehicle.qr_code}</strong></p>
                <p>Save this QR Code image:</p>
                <img src="${result.qr_code_path}" alt="QR Code for ${result.vehicle.license_plate}" width="150">
                <br>
                <a href="${result.qr_code_path}" download="${result.vehicle.qr_code}.png">Download QR Code</a>
            `;
        } catch (error) {
            console.error('Registration error:', error);
            updateStatus(regStatus, `Registration failed: ${error.message}`, true);
            regQrResult.innerHTML = '';
        }
    }

    async function confirmCheckIn() {
        console.log(">>> confirmCheckIn function called!"); // Debug log
        if (!scannedQrForCheckin || !checkinStatus) { console.error("Missing QR data or status element for check-in confirm!"); return; }
        updateStatus(checkinStatus, "Processing Check-In...", false);
        try {
            const response = await fetch(`${API_BASE_URL}/checkin`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ qr_code: scannedQrForCheckin }) // Only QR needed now
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || `Check-in failed: ${response.statusText}`);

            updateStatus(checkinStatus, result.message || "Check-in successful!", false);
            resetCheckInUI(); // Reset UI on success
            // No spot display to refresh

        } catch (error) {
            console.error('Check-in confirmation error:', error);
            updateStatus(checkinStatus, `Check-in failed: ${error.message}`, true);
            // Reset UI on error to allow new scan attempt
            resetCheckInUI();
            stopHtml5QrCodeScanner(); // Ensure scanner stops
        }
    }

    async function confirmCheckOut() {
        console.log(">>> confirmCheckOut function called!"); // Debug log
        if (!scannedQrForCheckout || !checkoutStatus) { console.error("Missing QR data or status element for check-out confirm!"); return; }
        updateStatus(checkoutStatus, "Processing Check-Out...", false);
        try {
            const response = await fetch(`${API_BASE_URL}/checkout`, {
                method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ qr_code: scannedQrForCheckout })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || `Check-out failed: ${response.statusText}`);

            const fee = parseFloat(result.fee).toFixed(2);
            const duration = parseFloat(result.duration_hours).toFixed(1);
            const successMessage = `${result.message} Duration: ${duration} hrs. Fee: £${fee}`;

            updateStatus(checkoutStatus, successMessage, false);
            resetCheckOutUI();
            // No spot display to refresh
        } catch (error) {
            console.error('Check-out confirmation error:', error);
            updateStatus(checkoutStatus, `Check-out failed: ${error.message}`, true);
            resetCheckOutUI();
            stopHtml5QrCodeScanner();
        }
    }

    async function confirmStatusCheck() {
        console.log(">>> confirmStatusCheck function called!"); // Debug log
        if (!scannedQrForStatus || !statusCheckStatus || !statusResultDisplay) { console.error("Missing QR data or status elements for status check!"); return; }
        updateStatus(statusCheckStatus, "Checking vehicle status...", false);
        statusResultDisplay.innerHTML = ''; // Clear previous results

        try {
            const response = await fetch(`${API_BASE_URL}/vehicle-status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ qr_code: scannedQrForStatus })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || `Status check failed: ${response.statusText}`);

            updateStatus(statusCheckStatus, result.message || "Status retrieved.", false);
            // Display formatted results
            let detailsHTML = `
                <p><strong>License Plate:</strong> ${result.license_plate || 'N/A'}</p>
                <p><strong>Owner:</strong> ${result.owner_name || 'N/A'} (${result.owner_phone_number || 'N/A'})</p>
                <p><strong>Status:</strong> ${result.is_checked_in ? '<span style="color:green; font-weight:bold;">Checked IN</span>' : '<span style="color:red; font-weight:bold;">Checked OUT</span>'}</p>
            `;
            if (result.is_checked_in && result.entry_time) {
                detailsHTML += `<p><strong>Checked In Since:</strong> ${formatDateTime(result.entry_time)}</p>`;
            }
            if (result.exit_time) { // Display last checkout info if available in response
                 const fee = result.fee !== null ? parseFloat(result.fee).toFixed(2) : 'N/A';
                 const duration = result.duration_hours !== null ? parseFloat(result.duration_hours).toFixed(1) : 'N/A';
                 detailsHTML += `<p><strong>Last Checkout:</strong> ${formatDateTime(result.exit_time)}</p>`;
                 detailsHTML += `<p><strong>Last Duration:</strong> ${duration} hrs</p>`;
                 detailsHTML += `<p><strong>Last Fee:</strong> £${fee}</p>`;
            }
            statusResultDisplay.innerHTML = detailsHTML;
            resetStatusCheckUI(); // Reset for next scan

        } catch (error) {
            console.error('Status check error:', error);
            updateStatus(statusCheckStatus, `Status check failed: ${error.message}`, true);
            statusResultDisplay.innerHTML = '<p class="error">Could not retrieve status.</p>';
            resetStatusCheckUI();
            stopHtml5QrCodeScanner(); // Ensure stopped
        }
    }

    // --- QR Scanning Flow ---

    function startScanner(action) {
        console.log(">>> startScanner called! Action:", action);
        let regionId;
        let statusElement;

        if (action === 'checkin') { regionId = 'checkin-scanner-region'; statusElement = checkinStatus; resetCheckInUI(); }
        else if (action === 'checkout') { regionId = 'checkout-scanner-region'; statusElement = checkoutStatus; resetCheckOutUI(); }
        else if (action === 'status') { regionId = 'status-scanner-region'; statusElement = statusCheckStatus; resetStatusCheckUI(); }
        else { console.error("Invalid action for startScanner:", action); return; }

        if (!document.getElementById(regionId) || !statusElement) { console.error("Scanner region/status element missing:", action); return; }
        updateStatus(statusElement, "Starting QR scanner...", false);

        startHtml5QrCodeScanner( regionId, (qrData) => {
            console.log(`QR Scanned (${action}):`, qrData); handleQrScanResult(qrData, action);
        }, (errorMessage) => {
            console.error(`QR Scan Error (${action}):`, errorMessage); updateStatus(statusElement, `QR Scanner Error: ${errorMessage}`, true); stopHtml5QrCodeScanner();
        });
    }

    function handleQrScanResult(qrData, action) {
        console.log(">>> Entering handleQrScanResult with action:", action);
        stopHtml5QrCodeScanner(); // Stop scanner after successful scan

        if (action === 'checkin') {
            console.log(">>> Handling checkin action...");
            scannedQrForCheckin = qrData;
            const qrDataSpan = document.getElementById('checkin-qr-data');
            const step2Div = document.getElementById('checkin-step2');
            const scanBtn = document.getElementById('checkin-scan-btn');
            console.log(">>> Element checkin-qr-data:", qrDataSpan); console.log(">>> Element checkin-step2:", step2Div); console.log(">>> Element checkin-scan-btn:", scanBtn);
            if (qrDataSpan) qrDataSpan.textContent = qrData; else console.error("!!! checkin-qr-data not found!");
            if (step2Div) step2Div.style.display = 'block'; else console.error("!!! checkin-step2 not found!");
            if (scanBtn) scanBtn.style.display = 'none'; else console.error("!!! checkin-scan-btn not found!");
            updateStatus(checkinStatus, "QR scanned. Confirm check-in.", false);
        } else if (action === 'checkout') {
            console.log(">>> Handling checkout action...");
            scannedQrForCheckout = qrData;
            const checkoutQrDataSpan = document.getElementById('checkout-qr-data');
            const checkoutStep2Div = document.getElementById('checkout-step2');
            const checkoutScanBtn = document.getElementById('checkout-scan-btn');
            console.log(">>> Element checkout-qr-data:", checkoutQrDataSpan); console.log(">>> Element checkout-step2:", checkoutStep2Div); console.log(">>> Element checkout-scan-btn:", checkoutScanBtn);
            if (checkoutQrDataSpan) checkoutQrDataSpan.textContent = qrData; else console.error("!!! checkout-qr-data not found!");
            if (checkoutStep2Div) checkoutStep2Div.style.display = 'block'; else console.error("!!! checkout-step2 not found!");
            if (checkoutScanBtn) checkoutScanBtn.style.display = 'none'; else console.error("!!! checkout-scan-btn not found!");
            updateStatus(checkoutStatus, "QR scanned. Confirm check-out.", false);
        } else if (action === 'status') {
             console.log(">>> Handling status action...");
             scannedQrForStatus = qrData;
             confirmStatusCheck(); // Trigger API call immediately
             if (statusScanBtn) statusScanBtn.style.display = 'none'; // Hide scan btn while processing
             updateStatus(statusCheckStatus, "QR scanned. Checking status...", false);
        }
    }

    // --- Add Event Listeners Directly ---
    // This avoids potential issues with inline onclick handlers if functions aren't globally defined when HTML parses
    // Make sure this runs AFTER the functions are defined.

    if (ownerRegButton) ownerRegButton.addEventListener('click', registerOwner); else console.error("Owner registration button not found");
    if (vehicleRegButton) vehicleRegButton.addEventListener('click', registerVehicle); else console.error("Vehicle registration button not found");

    if (checkinScanBtn) checkinScanBtn.addEventListener('click', () => startScanner('checkin')); else console.error("Check-in scan button not found");
    if (checkinConfirmBtn) checkinConfirmBtn.addEventListener('click', confirmCheckIn); else console.error("Check-in confirm button not found");

    if (checkoutScanBtn) checkoutScanBtn.addEventListener('click', () => startScanner('checkout')); else console.error("Check-out scan button not found");
    if (checkoutConfirmBtn) checkoutConfirmBtn.addEventListener('click', confirmCheckOut); else console.error("Check-out confirm button not found");

    if (statusScanBtn) statusScanBtn.addEventListener('click', () => startScanner('status')); else console.error("Status scan button not found");


    // --- Initialization ---
    console.log("Parking status page loaded. Initializing...");
    // Clear initial statuses
    updateStatus(ownerRegStatus, '', false);
    updateStatus(regStatus, '', false);
    updateStatus(checkinStatus, '', false);
    updateStatus(checkoutStatus, '', false);
    updateStatus(statusCheckStatus, '', false);
    // No initial spot fetch needed

}); // End DOMContentLoaded