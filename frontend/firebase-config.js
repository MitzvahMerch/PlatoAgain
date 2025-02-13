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

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Get Firebase Storage instance
const storage = firebase.storage();

// Function to upload image to Firebase Storage
async function uploadDesignImage(file, userId) {
  try {
      // Create a reference to 'plato/[userId]/[filename]'
      const designRef = storage.ref(`plato/${userId}/${file.name}`);
      
      // Upload the file
      const snapshot = await designRef.put(file);
      
      // Get the download URL
      const downloadURL = await snapshot.ref.getDownloadURL();
      
      return {
          success: true,
          url: downloadURL,
          path: `plato/${userId}/${file.name}`
      };
  } catch (error) {
      console.error('Error uploading file:', error);
      return {
          success: false,
          error: error.message
      };
  }
}

window.uploadDesignImage = uploadDesignImage;