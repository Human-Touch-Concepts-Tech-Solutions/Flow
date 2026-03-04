"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FiArrowLeft, FiEye, FiEyeOff, FiRefreshCw } from "react-icons/fi";
import { publicFetch } from "@/lib/api";
import {
  Background, Card, Header, BackButton, Title, Subtitle, 
  InputGroup, Input, Label, SubmitButton, FooterLink,
  ErrorMessage, SuccessMessage, PasswordHintList, PasswordHintItem, PasswordToggle,
  LogoWrapper, TimerText
} from "./RecoveryStyles";

export default function RecoveryPage() {
  const router = useRouter();
  const [step, setStep] = useState(1); 
  const [value, setValue] = useState(""); 
  const [otp, setOtp] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [timer, setTimer] = useState(300);

  // Countdown Logic
  useEffect(() => {
    let interval;
    if (step === 2 && timer > 0) {
      interval = setInterval(() => setTimer((prev) => prev - 1), 1000);
    }
    return () => clearInterval(interval);
  }, [step, timer]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const passwordRules = {
    length: newPassword.length >= 8,
    uppercase: /[A-Z]/.test(newPassword),
    lowercase: /[a-z]/.test(newPassword),
    number: /[0-9]/.test(newPassword),
    symbol: /[^A-Za-z0-9]/.test(newPassword),
  };

  const passwordStrong = Object.values(passwordRules).every(Boolean);
  const passwordsMatch = newPassword === confirmPassword && newPassword.length > 0;

  const handleSendCode = async (e, isResend = false) => {
    if (e) e.preventDefault();
    setError(""); 
    if(!isResend) setSuccess(""); 
    setLoading(true);

    try {
      await publicFetch("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email: value }),
      });
      
      // Clear success from step 1 once we move to step 2
      if (!isResend) {
        setStep(2);
        setTimer(300);
      } else {
        setSuccess("New code sent!");
        setTimer(300);
        setTimeout(() => setSuccess(""), 3000);
      }
    } catch (err) {
      setError(err.message || "Failed to send code");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const data = await publicFetch("/auth/verify-reset-otp", {
        method: "POST",
        body: JSON.stringify({ email: value, otp }),
      });
      setResetToken(data.reset_token);
      setSuccess(""); // Clear old success messages
      setStep(3);
    } catch (err) {
      setError("Invalid or expired code.");
    } finally {
      setLoading(false);
    }
  };

  const handleFinalReset = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await publicFetch("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({
          reset_token: resetToken,
          new_password: newPassword,
        }),
      });
      setSuccess("Password updated! Redirecting to login...");
      setTimeout(() => router.push("/account/login"), 2500);
    } catch (err) {
      setError("Session expired. Please start over.");
      setStep(1);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Background>
      <Card>
        <LogoWrapper>
           <img src="https://flowtru.vercel.app/logo.svg" alt="Logo" />
        </LogoWrapper>

        <Header>
          <BackButton onClick={() => step === 1 ? router.back() : setStep(step - 1)}>
            <FiArrowLeft />
          </BackButton>
          <Title>
            {step === 1 && "Reset Password"}
            {step === 2 && "Enter Code"}
            {step === 3 && "New Password"}
          </Title>
        </Header>

        {step === 1 && (
          <form onSubmit={handleSendCode}>
            <Subtitle>Enter your email to receive a reset code.</Subtitle>
            <InputGroup>
              <Label>Email Address</Label>
              <Input type="email" value={value} onChange={(e) => setValue(e.target.value)} required placeholder="name@example.com" />
            </InputGroup>
            {error && <ErrorMessage>{error}</ErrorMessage>}
            <SubmitButton type="submit" disabled={loading}>Send Reset Code</SubmitButton>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handleVerifyOTP}>
            <Subtitle>Code sent to <strong>{value}</strong></Subtitle>
            <InputGroup>
              <Label>6-Digit Code</Label>
              <Input type="text" maxLength={6} value={otp} onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))} required style={{ textAlign: 'center', letterSpacing: '8px', fontSize: '1.2rem'}} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
                <TimerText $warning={timer < 60}>
                  {timer > 0 ? `Expires in ${formatTime(timer)}` : "Expired"}
                </TimerText>
                
                <button 
                  type="button" 
                  onClick={(e) => handleSendCode(e, true)} 
                  disabled={loading || timer > 240} // Prevent spamming resend (wait 60s)
                  style={{ background: 'none', border: 'none', color: 'var(--lightblue)', cursor: 'pointer', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <FiRefreshCw className={loading ? "spin" : ""} /> Resend
                </button>
              </div>
            </InputGroup>
            {success && <SuccessMessage>{success}</SuccessMessage>}
            {error && <ErrorMessage>{error}</ErrorMessage>}
            <SubmitButton type="submit" disabled={loading || otp.length !== 6 || timer === 0}>Verify Code</SubmitButton>
          </form>
        )}

        {step === 3 && (
          <form onSubmit={handleFinalReset}>
            <InputGroup>
              <Label>New Password</Label>
              <div style={{ position: "relative" }}>
                <Input type={showPassword ? "text" : "password"} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
                <PasswordToggle type="button" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <FiEyeOff /> : <FiEye />}
                </PasswordToggle>
              </div>
              <PasswordHintList>
                <PasswordHintItem $valid={passwordRules.length}>8+ Characters</PasswordHintItem>
                <PasswordHintItem $valid={passwordRules.uppercase}>Uppercase Letter</PasswordHintItem>
                <PasswordHintItem $valid={passwordRules.lowercase}>Lowercase Letter</PasswordHintItem>
                <PasswordHintItem $valid={passwordRules.number}>Number</PasswordHintItem>
                <PasswordHintItem $valid={passwordRules.symbol}>Special Symbol</PasswordHintItem>
              </PasswordHintList>
            </InputGroup>
            <InputGroup>
              <Label>Confirm Password</Label>
              <div style={{ position: "relative" }}>
                <Input type={showConfirmPassword ? "text" : "password"} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
                <PasswordToggle type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                  {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
                </PasswordToggle>
              </div>
            </InputGroup>
            {success && <SuccessMessage>{success}</SuccessMessage>}
            {error && <ErrorMessage>{error}</ErrorMessage>}
            <SubmitButton type="submit" disabled={loading || !passwordStrong || !passwordsMatch}>Update Password</SubmitButton>
          </form>
        )}

        <FooterLink onClick={() => router.push("/account/login")}>Back to Login</FooterLink>
      </Card>
    </Background>
  );
}