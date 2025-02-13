// Wait for Firebase SDK to be loaded
window.addEventListener('DOMContentLoaded', (event) => {
    // Initialize Firebase with your configuration
    const firebaseConfig = {
        apiKey: "AIzaSyDXzyHOuZvDORubiwNtrZUo3cVnBYT288s",
        authDomain: "mitzvahmerch-ac346.firebaseapp.com",
        projectId: "mitzvahmerch-ac346",
        storageBucket: "mitzvahmerch-ac346.appspot.com",
        messagingSenderId: "232131426361",
        appId: "1:232131426361:web:8c7852a8da0e2f7a8d35e8",
        measurementId: "G-XXFM5DPRZ6"
    };

    // Initialize Firebase with error handling
    try {
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }

        // Get Firebase Storage and Firestore instances
        window.storage = firebase.storage();
        window.db = firebase.firestore();

        console.log('Firebase initialized successfully');
    } catch (error) {
        console.error("Firebase initialization error:", error);
    }
});

// Function to upload image to Firebase Storage
async function uploadDesignImage(file, userId) {
    try {
        // Make sure Firebase is initialized
        if (!window.storage) {
            throw new Error('Firebase Storage is not initialized');
        }

        // Validate file exists
        if (!file) {
            throw new Error('No file provided');
        }

        // Create a reference with a timestamp to avoid name conflicts
        const timestamp = Date.now();
        const designRef = window.storage.ref(`designs/${userId}/${timestamp}_${file.name}`);
        
        // Upload the file with progress monitoring
        const uploadTask = designRef.put(file);
        
        // Get progress element
        const progressElement = document.getElementById('upload-progress');
        const progressFill = progressElement.querySelector('.progress-fill');
        const progressText = progressElement.querySelector('.progress-text');
        
        // Show progress bar
        progressElement.style.display = 'block';

        // Return a promise that resolves when the upload is complete
        return new Promise((resolve, reject) => {
            uploadTask.on('state_changed', 
                // Progress handler
                (snapshot) => {
                    const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
                    progressFill.style.width = progress + '%';
                    progressText.textContent = `Uploading: ${Math.round(progress)}%`;
                },
                // Error handler
                (error) => {
                    console.error('Upload error:', error);
                    progressElement.style.display = 'none';
                    reject(error);
                },
                // Success handler
                async () => {
                    try {
                        const downloadURL = await uploadTask.snapshot.ref.getDownloadURL();
                        
                        // Store metadata in Firestore
                        await window.db.collection('designs').add({
                            userId: userId,
                            fileName: file.name,
                            fileType: file.type,
                            fileSize: file.size,
                            uploadDate: firebase.firestore.FieldValue.serverTimestamp(),
                            downloadURL: downloadURL,
                            status: 'pending_review'
                        });

                        progressElement.style.display = 'none';
                        resolve({
                            success: true,
                            url: downloadURL,
                            path: `designs/${userId}/${timestamp}_${file.name}`
                        });
                    } catch (error) {
                        console.error('Error getting download URL:', error);
                        progressElement.style.display = 'none';
                        reject(error);
                    }
                }
            );
        });
    } catch (error) {
        console.error('Error in uploadDesignImage:', error);
        document.getElementById('upload-progress').style.display = 'none';
        throw error;
    }
}

window.uploadDesignImage = uploadDesignImage;