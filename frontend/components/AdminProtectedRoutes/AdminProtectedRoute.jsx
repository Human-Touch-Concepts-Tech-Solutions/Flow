"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { jwtDecode } from "jwt-decode";

export default function AdminProtectedRoute({ children }) {
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(null);

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setIsAuthorized(false);
        router.push("/account/login");
        return;
      }

      try {
        const decoded = jwtDecode(token);
        const expiryTime = decoded.exp * 1000;

        if (expiryTime < Date.now()) {
          localStorage.removeItem("access_token");
          setIsAuthorized(false);
          router.push("/account/login");
          return;
        }

        // ROLE CHECK: Does the token have is_admin: true?
        if (decoded.is_admin === true) {
          setIsAuthorized(true);
        } else {
          // It's a valid user, but NOT an admin. Redirect to chat.
          setIsAuthorized(false);
          router.push("/account/portal/ChatInterface");
        }

      } catch (err) {
        localStorage.removeItem("access_token");
        setIsAuthorized(false);
        router.push("/account/login");
      }
    };

    checkAuth();
  }, [router]);

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