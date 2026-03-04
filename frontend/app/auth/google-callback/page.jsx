import { Suspense } from 'react';
import GoogleCallbackHandler from './GoogleCallbackHandler'; // We will create this

export default function GoogleCallbackPage() {
  return (
    // This Suspense boundary is what fixes the build error
    <Suspense fallback={<div>Loading authentication...</div>}>
      <GoogleCallbackHandler />
    </Suspense>
  );
}