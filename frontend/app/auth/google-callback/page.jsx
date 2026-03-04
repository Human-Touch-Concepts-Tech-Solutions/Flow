"use client";

import { useEffect, suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function GoogleCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");

    if (accessToken && refreshToken) {
      // 1. Save tokens to localStorage
      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);

      // 2. Security: Clear the URL parameters immediately 
      // This removes the tokens from the browser address bar 
      // so they don't stay in the history.
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);

      // 3. Redirect to the main interface
      router.push("/account/ChatInterface");
    } else {
      // Handle the case where tokens are missing
      const error = searchParams.get("error");
      console.error("OAuth Error:", error);
      
      alert("Google login failed. Please try again.");
      router.push("/account/login");
    }
  }, [searchParams, router]);

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      alignItems: 'center', 
      justifyContent: 'center',
      fontFamily: 'var(--font-geist-sans)',
      color: '#4a5568'
    }}>
      <div style={{ textAlign: 'center' }}>
        <p>Logging you in securely...</p>
        {/* You could add a spinner component here */}
      </div>
    </div>
  );
}