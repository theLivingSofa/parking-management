// static/qr-scanner.js

/**
 * Global variable to hold the active Html5Qrcode scanner instance.
 * We use a global variable to ensure we can stop the correct instance later.
 */
let html5QrCodeScanner = null;

/**
 * Starts the HTML5 QR Code scanner within a specified HTML element.
 *
 * @param {string} regionId The ID of the HTML element where the scanner UI should be rendered.
 * @param {function} successCallback A function to call when a QR code is successfully decoded.
 * It receives the decoded text (string) as an argument.
 * @param {function} errorCallback A function to call if there's an error starting the scanner
 * or during the scanning process (less frequent).
 * It receives an error message (string) as an argument.
 */
function startHtml5QrCodeScanner(regionId, successCallback, errorCallback) {
    console.log(`Attempting to start scanner in element ID: ${regionId}`);

    // Ensure any previous scanner instance is stopped before starting a new one.
    stopHtml5QrCodeScanner().then(() => {
        // Verify the target element exists
        const scannerRegionElement = document.getElementById(regionId);
        if (!scannerRegionElement) {
            const errorMsg = `Scanner region element with ID '${regionId}' not found.`;
            console.error(errorMsg);
            if (errorCallback) {
                errorCallback(errorMsg);
            }
            return; // Stop execution if element is missing
        }

        // Create a new scanner instance attached to the specified element ID.
        html5QrCodeScanner = new Html5Qrcode(regionId);

        // Configuration for the scanner.
        const config = {
            fps: 10, // Frames per second to attempt scanning.
            qrbox: (viewfinderWidth, viewfinderHeight) => {
                // Calculate desired QR box size (e.g., 60% of the smaller dimension).
                let edgePercentage = 0.60;
                let minEdgeSize = Math.min(viewfinderWidth, viewfinderHeight);
                let qrboxSize = Math.floor(minEdgeSize * edgePercentage);
                // Ensure minimum size if needed
                // qrboxSize = Math.max(qrboxSize, 150);
                return { width: qrboxSize, height: qrboxSize };
            },
            rememberLastUsedCamera: true, // Good for user experience.
            // supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA] // Optional: Limit scan types
        };

        // Define the function to handle successful scans.
        const qrCodeSuccessCallback = (decodedText, decodedResult) => {
            console.log(`Scan successful, decoded text: ${decodedText}`);
            // Stop the scanner first before invoking the callback provided by script.js
            stopHtml5QrCodeScanner().then(() => {
                 if (successCallback) {
                     successCallback(decodedText); // Pass result to the main script's handler
                 }
            }).catch(err => {
                 console.error("Error stopping scanner after success:", err);
                 // Still try to call the success callback
                 if (successCallback) {
                      successCallback(decodedText);
                 }
            });
        };

        // Define the function to handle non-fatal errors during scanning (optional).
        // This gets called frequently if no QR code is in view. Usually best left empty or minimal.
        const qrCodeErrorCallback = (errorMessage) => {
            // console.warn(`QR Code scanning error: ${errorMessage}`);
        };

        // Start scanning using the rear camera ('environment').
        html5QrCodeScanner.start(
            { facingMode: "environment" }, // Try rear camera first
            config,
            qrCodeSuccessCallback,
            qrCodeErrorCallback // Optional error callback during scanning
        )
        .catch((err) => {
            // Handle critical errors during scanner startup (e.g., camera permissions).
            console.error(">>> Full Error Object trying to start QR Scanner:", err);

            let detailedErrorMessage = "Unknown error starting scanner.";
            if (err) {
                // Prioritize specific error names if available
                if (err.name === 'NotAllowedError') {
                    detailedErrorMessage = "Camera permission denied. Please allow camera access in browser settings.";
                } else if (err.name === 'NotFoundError') {
                     detailedErrorMessage = "No suitable camera found.";
                } else if (err.name === 'NotReadableError') {
                     detailedErrorMessage = "Camera is already in use or unreadable.";
                } else {
                    detailedErrorMessage = err.message || err.name || JSON.stringify(err);
                }
            }

            if (errorCallback) {
                errorCallback(`Error starting scanner: ${detailedErrorMessage}`);
            }
            // Ensure the scanner instance is cleared on startup failure
             html5QrCodeScanner = null;
        });

    }).catch(err => {
        // This catch handles errors from the initial stopHtml5QrCodeScanner call
         console.error("Error during pre-scan stop:", err);
         if (errorCallback) {
              errorCallback(`Internal error before starting scanner: ${err.message || err}`);
         }
    });
}

/**
 * Stops the active QR Code scanner instance, if running.
 * Returns a Promise that resolves when stopping is complete or fails.
 */
function stopHtml5QrCodeScanner() {
    return new Promise((resolve, reject) => {
        if (html5QrCodeScanner) {
            // Check if the scanner is actually running before trying to stop
            if (html5QrCodeScanner.isScanning) {
                html5QrCodeScanner.stop()
                    .then(() => {
                        console.log("QR Code scanner stopped successfully via stop().");
                        // Attempt to clear the UI element associated with the scanner instance
                        try {
                             html5QrCodeScanner.clear();
                             console.log("Scanner UI cleared.");
                        } catch (clearError) {
                             console.warn("Error clearing scanner UI after stop:", clearError);
                        }
                        html5QrCodeScanner = null; // Clear the global instance
                        resolve();
                    })
                    .catch((err) => {
                        console.error("Error stopping QR Code scanner:", err);
                        html5QrCodeScanner = null; // Clear the instance even on error
                        reject(err);
                    });
            } else {
                 // If instance exists but is not scanning (e.g., failed to start), just clear UI and instance
                 try {
                     html5QrCodeScanner.clear();
                     console.log("Scanner UI cleared (was not scanning).");
                 } catch (clearError) {
                     console.warn("Error clearing scanner UI (was not scanning):", clearError);
                 }
                 html5QrCodeScanner = null;
                 resolve(); // Resolve as stopping wasn't needed
            }
        } else {
            // No active scanner instance to stop
            resolve();
        }
    });
}