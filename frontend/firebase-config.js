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

// Get Firebase Storage and Firestore instances
const storage = firebase.storage();
const db = firebase.firestore();

// Function to upload image to Firebase Storage
async function uploadDesignImage(file, userId) {
  try {
      // Create a reference to 'designs/[userId]/[filename]'
      const designRef = storage.ref(`designs/${userId}/${file.name}`);
      
      // Upload the file
      const snapshot = await designRef.put(file);
      
      // Get the download URL
      const downloadURL = await snapshot.ref.getDownloadURL();
      
      // Store metadata in Firestore
      await db.collection('designs').add({
          userId: userId,
          fileName: file.name,
          fileType: file.type,
          fileSize: file.size,
          uploadDate: firebase.firestore.FieldValue.serverTimestamp(),
          downloadURL: downloadURL,
          status: 'pending_review'
      });

      return {
          success: true,
          url: downloadURL,
          path: `designs/${userId}/${file.name}`
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