// static/script.js

const API_BASE_URL = "http://127.0.0.1:8000/api"; // Adjust if needed

// --- DOM Element References ---
// Owner Registration
const ownerNameInput = document.getElementById('owner-name');
const ownerPhoneInput = document.getElementById('owner-phone');
const ownerRegStatus = document.getElementById('owner-reg-status');
// Vehicle Registration
const regPlateInput = document.getElementById('reg-plate');
const vehicleOwnerPhoneInput = document.getElementById('vehicle-owner-phone'); // Use phone input
const regStatus = document.getElementById('reg-status');
const regQrResult = document.getElementById('reg-qr-result');
// Check-in
const checkinStatus = document.getElementById('checkin-status');
const checkinStep2Div = document.getElementById('checkin-step2');
const checkinQrDataSpan = document.getElementById('checkin-qr-data');
const checkinSpotInput = document.getElementById('checkin-spot');
const checkinScanBtn = document.getElementById('checkin-scan-btn');
// Check-out
const checkoutStatus = document.getElementById('checkout-status');
const checkoutStep2Div = document.getElementById('checkout-step2');
const checkoutQrDataSpan = document.getElementById('checkout-qr-data');
const checkoutScanBtn = document.getElementById('checkout-scan-btn');
// Parking Lot
const parkingLotDiv = document.getElementById('parking-lot');

// --- State Variables ---
let scannedQrForCheckin = null;
let scannedQrForCheckout = null;

// --- Helper Functions ---

/**
 * Updates the status message paragraph.
 * @param {HTMLElement} element The paragraph element to update.
 * @param {string} message The message to display.
 * @param {boolean} [isError=false] Whether the message indicates an error.
 */
function updateStatus(element, message, isError = false) {
    if (!element) return;
    element.textContent = message;
    element.className = 'status'; // Reset classes first
    if (message) { // Add class only if there is a message
        element.classList.add(isError ? 'error' : 'success');
    }
}

/**
 * Formats a datetime string or Date object.
 * @param {string|Date} dateTimeInput The date/time input.
 * @returns {string} Formatted date/time string or "Invalid Date".
 */
function formatDateTime(dateTimeInput) {
    if (!dateTimeInput) return "";
    try {
        const date = new Date(dateTimeInput);
        if (isNaN(date.getTime())) return "Invalid Date";
        return date.toLocaleString('sv-SE', { // Example format: 2024-04-02 15:30
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', hour12: false
        });
    } catch (error) {
        console.error("Error formatting date:", error);
        return "Invalid Date";
    }
}

// --- Core API Functions ---

/**
 * Fetches and displays the current status of all parking spots.
 */
async function fetchAndDisplaySpots() {
    if (!parkingLotDiv) return;
    parkingLotDiv.innerHTML = '<p>Loading parking spots...</p>';
    try {
        const response = await fetch(`${API_BASE_URL}/spots`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({})); // Try get error detail
            throw new Error(errorData.detail || `HTTP error ${response.status}`);
        }
        const spots = await response.json();
        parkingLotDiv.innerHTML = ''; // Clear loading/previous

        if (!spots || spots.length === 0) {
            parkingLotDiv.innerHTML = '<p>No parking spots found.</p>';
            return;
        }

        spots.forEach(spot => {
            const spotDiv = document.createElement('div');
            spotDiv.className = `spot ${spot.is_occupied ? 'occupied' : 'available'}`;
            spotDiv.id = `spot-${spot.spot_number}`;
            const formattedEntryTime = formatDateTime(spot.entry_time);
            // Display spot info, including owner details if occupied
            spotDiv.innerHTML = `
                <div class="spot-number">${spot.spot_number}</div>
                <div class="spot-status">${spot.is_occupied ? 'Occupied' : 'Available'}</div>
                ${spot.is_occupied && spot.license_plate ? `
                    <div class="spot-plate">${spot.license_plate}</div>
                    <div class="spot-owner">Owner: ${spot.owner_name || 'N/A'} (${spot.owner_phone_number || 'N/A'})</div>
                    <div class="spot-entry">Entered: ${formattedEntryTime}</div>
                ` : ''}
            `;
            parkingLotDiv.appendChild(spotDiv);
        });
    } catch (error) {
        console.error('Error fetching spots:', error);
        parkingLotDiv.innerHTML = `<p class="error">Could not load spots: ${error.message}</p>`;
    }
}

/**
 * Registers a new owner using the details from the form.
 */
async function registerOwner() {
    if (!ownerNameInput || !ownerPhoneInput || !ownerRegStatus) return;
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
        ownerNameInput.value = ''; ownerPhoneInput.value = ''; // Clear inputs
    } catch (error) {
        console.error('Owner registration error:', error);
        updateStatus(ownerRegStatus, `Owner registration failed: ${error.message}`, true);
    }
}

/**
 * Registers a new vehicle using details from the form.
 */
async function registerVehicle() {
    if (!regPlateInput || !vehicleOwnerPhoneInput || !regStatus || !regQrResult) return;
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
            body: JSON.stringify({ license_plate: licensePlate, owner_phone_number: ownerPhone }) // Send owner PHONE
        });
        const result = await response.json(); // Contains message, vehicle object, qr_code_path
        if (!response.ok) throw new Error(result.detail || `Registration failed: ${response.statusText}`);

        updateStatus(regStatus, result.message || "Registration successful!", false);
        regPlateInput.value = ''; vehicleOwnerPhoneInput.value = ''; // Clear inputs

        // Display result including QR code image and download link
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

// --- QR Scanning Flow ---

/**
 * Starts the QR scanner for the specified action (checkin/checkout).
 * @param {string} action - 'checkin' or 'checkout'.
 */
function startScanner(action) {
    // --- Debug log added previously ---
    console.log(">>> startScanner called! Action:", action);

    const regionId = action === 'checkin' ? 'checkin-scanner-region' : 'checkout-scanner-region';
    const statusElement = action === 'checkin' ? checkinStatus : checkoutStatus;
    if (!document.getElementById(regionId) || !statusElement) {
        console.error("Scanner region or status element not found for action:", action);
        return;
    }

    updateStatus(statusElement, "Starting QR scanner...", false);
    // Reset relevant UI before starting scanner
    if (action === 'checkin') resetCheckInUI(); else resetCheckOutUI();

    // Call the function from qr-scanner.js
    startHtml5QrCodeScanner(
        regionId,
        (qrData) => { // Success callback
            console.log(`QR Scanned (${action}):`, qrData);
            handleQrScanResult(qrData, action); // Process the result
            // Status updated inside handleQrScanResult now maybe more appropriate
            // updateStatus(statusElement, `QR Code scanned successfully!`, false);
        },
        (errorMessage) => { // Error callback
            console.error(`QR Scan Error (${action}):`, errorMessage);
            updateStatus(statusElement, `QR Scanner Error: ${errorMessage}`, true);
            stopHtml5QrCodeScanner(); // Stop scanner on error too
        }
    );
}

/**
 * Handles the result after a QR code is successfully scanned.
 * Updates the UI to proceed to the next step.
 * @param {string} qrData - The data decoded from the QR code.
 * @param {string} action - 'checkin' or 'checkout'.
 */
function handleQrScanResult(qrData, action) {
    console.log(">>> Entering handleQrScanResult with action:", action);

    // stopHtml5QrCodeScanner(); // Scanner is stopped in success callback of startHtml5QrCodeScanner

    if (action === 'checkin') {
        console.log(">>> Handling checkin action...");
        scannedQrForCheckin = qrData;

        const qrDataSpan = document.getElementById('checkin-qr-data');
        const step2Div = document.getElementById('checkin-step2');
        const scanBtn = document.getElementById('checkin-scan-btn');
        console.log(">>> Element checkin-qr-data:", qrDataSpan);
        console.log(">>> Element checkin-step2:", step2Div);
        console.log(">>> Element checkin-scan-btn:", scanBtn);

        if (qrDataSpan) qrDataSpan.textContent = qrData; else console.error("!!! Element 'checkin-qr-data' not found!");
        if (step2Div) step2Div.style.display = 'block'; else console.error("!!! Element 'checkin-step2' not found!");
        if (scanBtn) scanBtn.style.display = 'none'; else console.error("!!! Element 'checkin-scan-btn' not found!");
        // Focus spot input automatically
        if (checkinSpotInput) checkinSpotInput.focus();
        updateStatus(checkinStatus, "QR scanned. Please enter spot number.", false); // Update status

    } else if (action === 'checkout') {
        console.log(">>> Handling checkout action...");
        scannedQrForCheckout = qrData;

        const checkoutQrDataSpan = document.getElementById('checkout-qr-data');
        const checkoutStep2Div = document.getElementById('checkout-step2');
        const checkoutScanBtn = document.getElementById('checkout-scan-btn');
        console.log(">>> Element checkout-qr-data:", checkoutQrDataSpan);
        console.log(">>> Element checkout-step2:", checkoutStep2Div);
        console.log(">>> Element checkout-scan-btn:", checkoutScanBtn);

        if (checkoutQrDataSpan) checkoutQrDataSpan.textContent = qrData; else console.error("!!! checkout-qr-data not found!");
        if (checkoutStep2Div) checkoutStep2Div.style.display = 'block'; else console.error("!!! checkout-step2 not found!");
        if (checkoutScanBtn) checkoutScanBtn.style.display = 'none'; else console.error("!!! checkout-scan-btn not found!");
        updateStatus(checkoutStatus, "QR scanned. Confirm check-out.", false); // Update status
    }
}

// --- Check-In / Check-Out Confirmation ---

/**
 * Confirms check-in after QR scan and spot number entry.
 */
async function confirmCheckIn() {
    if (!scannedQrForCheckin || !checkinSpotInput || !checkinStatus) return;
    const spotNumber = checkinSpotInput.value.trim();
    if (!spotNumber) { updateStatus(checkinStatus, "Please enter the spot number.", true); if(checkinSpotInput) checkinSpotInput.focus(); return; }

    updateStatus(checkinStatus, "Processing Check-In...", false);
    try {
        const response = await fetch(`${API_BASE_URL}/checkin`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body: JSON.stringify({ qr_code: scannedQrForCheckin, spot_number: spotNumber })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || `Check-in failed: ${response.statusText}`);

        updateStatus(checkinStatus, result.message || "Check-in successful!", false);
        resetCheckInUI(); // Reset UI fully on success
        await fetchAndDisplaySpots(); // Refresh spots
    } catch (error) {
        console.error('Check-in confirmation error:', error);
        updateStatus(checkinStatus, `Check-in failed: ${error.message}`, true);
        // Keep step 2 visible, focus input for correction
        if (checkinSpotInput) { checkinSpotInput.focus(); checkinSpotInput.select(); }
        // stopHtml5QrCodeScanner(); // Should be stopped already
    }
}

/**
 * Confirms check-out after QR scan.
 */
async function confirmCheckOut() {
    if (!scannedQrForCheckout || !checkoutStatus) return;
    updateStatus(checkoutStatus, "Processing Check-Out...", false);
    try {
        const response = await fetch(`${API_BASE_URL}/checkout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body: JSON.stringify({ qr_code: scannedQrForCheckout })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || `Check-out failed: ${response.statusText}`);

        const fee = parseFloat(result.fee).toFixed(2);
        const duration = parseFloat(result.duration_hours).toFixed(1);
        const successMessage = `${result.message} Duration: ${duration} hrs. Fee: ₹${fee}`;

        updateStatus(checkoutStatus, successMessage, false);
        resetCheckOutUI(); // Reset UI on success
        await fetchAndDisplaySpots(); // Refresh spots
    } catch (error) {
        console.error('Check-out confirmation error:', error);
        updateStatus(checkoutStatus, `Check-out failed: ${error.message}`, true);
        resetCheckOutUI(); // Reset UI elements on error
        stopHtml5QrCodeScanner(); // Ensure scanner is stopped on error
    }
}

// --- UI Reset Functions ---

/** Resets the Check-In UI area to its initial state (ready to scan). */
function resetCheckInUI() {
     scannedQrForCheckin = null;
     if(checkinQrDataSpan) checkinQrDataSpan.textContent = '';
     if(checkinSpotInput) checkinSpotInput.value = '';
     if(checkinStep2Div) checkinStep2Div.style.display = 'none'; // Hide step 2
     if(checkinScanBtn) checkinScanBtn.style.display = 'block'; // Show scan button
     // Don't clear status here, let the calling function manage messages
}

/** Resets the Check-Out UI area to its initial state (ready to scan). */
function resetCheckOutUI() {
     scannedQrForCheckout = null;
     if(checkoutQrDataSpan) checkoutQrDataSpan.textContent = '';
     if(checkoutStep2Div) checkoutStep2Div.style.display = 'none'; // Hide step 2
     if(checkoutScanBtn) checkoutScanBtn.style.display = 'block'; // Show scan button
     // Don't clear status here
}

// --- Initialization ---
// Fetch initial parking spot status when the page is fully loaded
document.addEventListener('DOMContentLoaded', fetchAndDisplaySpots);