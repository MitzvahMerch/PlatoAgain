// ReactFrontend/lib/firebase.ts

import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import {
  getStorage,
  ref,
  uploadBytesResumable,
  getDownloadURL,
  UploadTaskSnapshot,
  StorageReference,
} from 'firebase/storage';

// Firebase config pulled from environment variables
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY as string,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN as string,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID as string,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET as string,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID as string,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID as string,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID as string,
};

let firebaseApp: FirebaseApp;

/**
 * Initializes Firebase app if not already initialized.
 */
export function initializeFirebase(): void {
  if (!getApps().length) {
    firebaseApp = initializeApp(firebaseConfig);
    console.log('Firebase initialized');
  } else {
    firebaseApp = getApps()[0];
  }
}

export interface UploadResult {
  success: true;
  url: string;
  path: string;
}

/**
 * Uploads a design file to Firebase Storage under designs/{userId}/{filename}.
 * @param file The file/blob to upload (e.g., from input[type="file"]).
 * @param userId The current user ID (without "user_" prefix).
 * @returns Resolves with the uploaded file's URL and storage path.
 */
export function uploadDesignImage(
  file: File | Blob,
  userId: string,
  onProgress?: (percent: number) => void
): Promise<UploadResult> {
  initializeFirebase();
  const storage = getStorage(firebaseApp);

  if (!file) {
    return Promise.reject(new Error('No file provided'));
  }

  const fullUserId = userId.startsWith('user_') ? userId : `user_${userId}`;
  const storageRef: StorageReference = ref(
    storage,
    `designs/${fullUserId}/${(file as File).name || Date.now()}`
  );

  const uploadTask = uploadBytesResumable(storageRef, file as Blob);

  return new Promise<UploadResult>((resolve, reject) => {
    uploadTask.on(
      'state_changed',
      (snapshot: UploadTaskSnapshot) => {
        const progress =
          (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
        onProgress?.(progress);
      },
      (error) => {
        console.error('Upload error:', error);
        reject(error);
      },
      async () => {
        try {
          const downloadURL = await getDownloadURL(uploadTask.snapshot.ref);
          resolve({
            success: true,
            url: downloadURL,
            path: uploadTask.snapshot.ref.fullPath,
          });
        } catch (error) {
          console.error('Error getting download URL:', error);
          reject(error);
        }
      }
    );
  });
}
