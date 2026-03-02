"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { 
  PageWrapper, Card, Title, Subtitle, 
  EmailText, AdminInput, Button, ErrorText 
} from "@/components/AdminPass/AdminPassStyles";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function AdminVerify() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [masterKey, setMasterKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const storedEmail = localStorage.getItem("pending_email");
    if (!storedEmail) {
      router.push("/register");
      return;
    }
    setEmail(storedEmail);
  }, [router]);

  const handleVerify = async () => {
    if (!masterKey) return;
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code: masterKey }),
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        localStorage.removeItem("pending_email");
        router.push("/admin/dashboard");
      } else {
        setError(data.detail || "Invalid Master Key");
      }
    } catch (err) {
      setError("Server connection failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageWrapper>
      <Card>
        <Title>Admin Access</Title>
        <Subtitle>
          System identity detected for <br />
          <EmailText>{email}</EmailText> <br />
          Enter Master Key to continue
        </Subtitle>

        <AdminInput 
          type="password" 
          placeholder="Enter Master Key" 
          value={masterKey} 
          onChange={(e) => setMasterKey(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleVerify()}
          autoFocus 
        />

        {error && <ErrorText>{error}</ErrorText>}

        <Button onClick={handleVerify} disabled={loading || !masterKey}>
          {loading ? "Verifying..." : "Confirm Access"}
        </Button>
      </Card>
    </PageWrapper>
  );
}