// static/qr-scanner.js

let html5QrCodeScanner = null; // Global scanner instance variable

/**
 * Starts the QR Code scanner.
 * @param {string} regionId The ID of the HTML element to render the scanner in.
 * @param {function} successCallback Function to call when a QR code is successfully scanned. Takes qrCodeMessage as argument.
 * @param {function} errorCallback Function to call on error (optional).
 */
function startHtml5QrCodeScanner(regionId, successCallback, errorCallback) {
    // If scanner already exists, stop it first
    stopHtml5QrCodeScanner();

    // Create a new scanner instance
    html5QrCodeScanner = new Html5Qrcode(regionId);

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 }, // Configure the scanning box size
        rememberLastUsedCamera: true, // Try to use the same camera as last time
        // supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA] // Use only camera
    };

    // Start scanning using the back camera ('environment')
    html5QrCodeScanner.start(
        { facingMode: "environment" }, // Use rear camera
        config,
        (decodedText, decodedResult) => {
            // Success callback - handle the decoded text
            stopHtml5QrCodeScanner(); // Stop scanning after success
            if (successCallback) {
                successCallback(decodedText); // Pass the decoded text
            }
        },
        (errorMessage) => {
            // Optional: handle scan failure (e.g., QR code not found)
            // This gets called frequently, so maybe only log serious errors
            if (errorCallback) {
                 // errorCallback(errorMessage); // Can be noisy
            }
        })
        .catch((err) => {
            // Handle errors during starting the scanner (e.g., camera permission denied)
            console.error("Error starting QR Scanner:", err);
            if (errorCallback) {
                errorCallback(`Error starting scanner: ${err.message}`);
            }
            // Reset the scanner variable if start fails
             html5QrCodeScanner = null;
        });
}

/**
 * Stops the active QR Code scanner instance, if running.
 */
function stopHtml5QrCodeScanner() {
    if (html5QrCodeScanner && html5QrCodeScanner.isScanning) {
        html5QrCodeScanner.stop()
            .then(() => {
                console.log("QR Code scanner stopped.");
                html5QrCodeScanner.clear(); // Clear the scanner UI element
                 html5QrCodeScanner = null;
            })
            .catch((err) => {
                console.error("Error stopping QR Code scanner:", err);
                 html5QrCodeScanner = null; // Still reset on error
            });
    } else if (html5QrCodeScanner) {
         // If not scanning but instance exists, clear it
         html5QrCodeScanner.clear();
         html5QrCodeScanner = null;
    }
}