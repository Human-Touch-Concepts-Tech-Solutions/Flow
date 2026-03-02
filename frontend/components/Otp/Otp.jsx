"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  PageWrapper,
  Card,
  Title,
  Subtitle,
  EmailText,
  OtpContainer,
  OtpInput,
  Button,
  ErrorText,
  ResendWrapper,
  ResendButton
} from "./OtpStyles";

const OTP_LENGTH = 6;
const RESEND_TIME = 60;

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Otp() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState(Array(OTP_LENGTH).fill(""));
  const [timer, setTimer] = useState(RESEND_TIME);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasAutoSubmitted, setHasAutoSubmitted] = useState(false);

  const inputsRef = useRef([]);

  // Load email
  useEffect(() => {
    const storedEmail = localStorage.getItem("pending_email");
    if (!storedEmail) {
      alert("Session expired. Please register again.");
      router.push("/register");
      return;
    }
    setEmail(storedEmail);
  }, [router]);

  // Timer
  useEffect(() => {
    if (timer === 0) return;
    const interval = setInterval(() => setTimer(t => t - 1), 1000);
    return () => clearInterval(interval);
  }, [timer]);

  // Reset auto-submit flag only when the OTP values actually change
  const handleOtpChange = (newOtp) => {
    setOtp(newOtp);
    setHasAutoSubmitted(false); // Unlock auto-submit because the user is typing
    setError(""); // Clear error while typing
  };

  const handleVerify = useCallback(async (code) => {
    if (loading) return;
    setError("");
    setLoading(true);

    try {
      // FIXED: Added /api/v1 prefix to match backend
      const res = await fetch(`${API_BASE}/api/v1/auth/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code })
      });

      const data = await res.json();

      if (!res.ok) {
        setError(
          data.detail === "Invalid or expired OTP"
            ? "Invalid or expired code. Please check and try again."
            : data.detail || "Verification failed"
        );
        // We keep hasAutoSubmitted as TRUE here so it doesn't loop.
        // It only resets via handleOtpChange when the user edits the boxes.
        setHasAutoSubmitted(true); 
        return;
      }

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.removeItem("pending_email");

      router.push("/account/ChatInterface");

    } catch (err) {
      setError("Network error. Please check your connection.");
    } finally {
      setLoading(false);
    }
  }, [email, router, loading]);

  // Auto-submit logic
  useEffect(() => {
    const code = otp.join("");
    if (
      code.length === OTP_LENGTH && 
      !loading && 
      !hasAutoSubmitted && 
      !error // Only auto-submit if there isn't an active error
    ) {
      setHasAutoSubmitted(true);
      handleVerify(code);
    }
  }, [otp, loading, hasAutoSubmitted, handleVerify, error]);

  const handleChange = (value, index) => {
    if (!/^\d?$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value;
    handleOtpChange(newOtp);
    
    if (value && index < OTP_LENGTH - 1) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (e, index) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  const handleResend = async () => {
    setError("");
    setLoading(true);
    
    try {
      // FIXED: Added /api/v1 prefix
      const res = await fetch(`${API_BASE}/api/v1/auth/send-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });

      if (res.ok) {
        setTimer(RESEND_TIME);
        setHasAutoSubmitted(false);
        setOtp(Array(OTP_LENGTH).fill("")); // Clear inputs on resend
        inputsRef.current[0]?.focus();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to resend code");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageWrapper>
      <Card>
        <Title>Verify your account</Title>
        <Subtitle>
          We sent a 6-digit code to <br />
          <EmailText>{email}</EmailText>
        </Subtitle>

        <OtpContainer>
          {otp.map((digit, index) => (
            <OtpInput
              key={index}
              ref={(el) => (inputsRef.current[index] = el)}
              value={digit}
              maxLength={1}
              onChange={(e) => handleChange(e.target.value, index)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              autoFocus={index === 0}
            />
          ))}
        </OtpContainer>

        {error && <ErrorText>{error}</ErrorText>}

        <Button
          onClick={() => handleVerify(otp.join(""))}
          disabled={loading || otp.join("").length < OTP_LENGTH}
        >
          {loading ? "Verifying..." : "Verify Code"}
        </Button>

        <ResendWrapper>
          {timer > 0 ? (
            <span>Resend code in {timer}s</span>
          ) : (
            <ResendButton onClick={handleResend} disabled={loading}>
              Resend code
            </ResendButton>
          )}
        </ResendWrapper>
      </Card>
    </PageWrapper>
  );
}