"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { jwtDecode } from "jwt-decode";// Make sure this is installed: npm install jwt-decode

export default function ProtectedRoute({ children }) {
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(null); // null = checking, true/false = result

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setIsAuthorized(false);
        router.push("/account/login"); // or "/account/login"
        return;
      }

      try {
        const decoded = jwtDecode(token);
        const expiryTime = decoded.exp * 1000; // exp is in seconds → ms

        if (expiryTime < Date.now()) {
          // Expired
          localStorage.removeItem("access_token");
          setIsAuthorized(false);
          router.push("/account/login");
          return;
        }

        // Token is valid
        setIsAuthorized(true);

        // Optional: Auto-logout timer (1 min before expiry)
        const timeLeft = expiryTime - Date.now();
        if (timeLeft > 0) {
          const timeoutId = setTimeout(() => {
            localStorage.removeItem("access_token");
            router.push("/account/login");
          }, timeLeft - 60000);

          return () => clearTimeout(timeoutId);
        }
      } catch (err) {
        // Invalid token format
        localStorage.removeItem("access_token");
        setIsAuthorized(false);
        router.push("/account/login");
      }
    };

    checkAuth();
  }, [router]);

  // While checking auth (first render)
if (isAuthorized === null) {
  // Use a Fragment here so the layout doesn't "jump" when this disappears
  return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
       Loading security...
    </div>
  );
}

if (!isAuthorized) return null;

return <>{children}</>;
}