"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FiEye, FiEyeOff } from "react-icons/fi";
import {
  Background, Content, Logo, Input, Button, Row,
  StepIndicator, GenderGroup, GenderOption,
  PasswordHintList, PasswordHintItem,
  SuggestionBox, SuggestionItem,
} from "./RegisterPageStyles";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [showPassword, setShowPassword] = useState(false);
  const [touched, setTouched] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState(null);
  const [professionSuggestions, setProfessionSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const [form, setForm] = useState({
    firstName: "", lastName: "", email: "", phone: "",
    dob: "", gender: "", profession: "", password: "", confirmPassword: "",
  });

  const getMaxDate = () => {
    const today = new Date();
    const maxDate = new Date(today.getFullYear() - 10, today.getMonth(), today.getDate());
    return maxDate.toISOString().split("T")[0];
  };

  useEffect(() => {
    const loadProfessions = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/auth/professions`);
        if (res.ok) {
          const data = await res.json();
          setProfessionSuggestions(data.professions);
        }
      } catch (error) {
        setProfessionSuggestions(["Student", "Developer", "Designer", "Writer", "Teacher", "Researcher", "Marketer", "Entrepreneur"]);
      }
    };
    loadProfessions();
  }, []);

  // Validation Rules
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const phoneValid = /^[0-9]{7,15}$/.test(form.phone);

  const passwordRules = {
    length: form.password.length >= 8,
    uppercase: /[A-Z]/.test(form.password),
    lowercase: /[a-z]/.test(form.password),
    number: /[0-9]/.test(form.password),
    symbol: /[^A-Za-z0-9]/.test(form.password),
  };

  const passwordStrong = Object.values(passwordRules).every(Boolean);

  const stepOneValid =
    form.firstName && form.lastName && emailRegex.test(form.email) &&
    phoneValid && form.dob && form.dob <= getMaxDate() && form.gender;

  const stepTwoValid =
    form.profession && passwordStrong && form.password === form.confirmPassword;

  const filteredSuggestions = (professionSuggestions || []).filter((p) =>
    p.toLowerCase().includes(form.profession.toLowerCase())
  );

  const handleChange = (key, value) => setForm({ ...form, [key]: value });
  const handleBlur = (field) => setTouched((prev) => ({ ...prev, [field]: true }));

  const handleSubmit = async () => {
    setServerError(null);
    setIsLoading(true);

    // Format phone to international standard
    const phoneNumber = form.phone.startsWith("0") 
      ? "+234" + form.phone.slice(1) 
      : form.phone;

    const payload = {
      first_name: form.firstName,
      last_name: form.lastName,
      email: form.email.toLowerCase(), // Normalize email for backend checks
      phone: phoneNumber,
      date_of_birth: form.dob,
      gender: form.gender.toLowerCase(),
      profession: form.profession,
      password: form.password,
    };

    try {
      // 1. Register User
      const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        setServerError(Array.isArray(data.detail) ? data.detail[0].msg : data.detail);
        setIsLoading(false);
        return;
      }

      // 2. Trigger OTP or Admin Check via backend
      const otpRes = await fetch(`${API_BASE}/api/v1/auth/send-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.email.toLowerCase() }),
      });

      const otpData = await otpRes.json();

      if (!otpRes.ok) {
        setServerError("Account created, but failed to initiate verification.");
        setIsLoading(false);
        return;
      }

      // 3. Success - Set email for verification pages
      localStorage.setItem("pending_email", form.email.toLowerCase());
      
      // 4. NEW REDIRECT LOGIC based on backend response
      if (otpData.next_step === "admin_verify") {
        router.push("/account/admin/admin-verify");
      } else {
        router.push("/account/verify-otp");
      }

    } catch (err) {
      setServerError("Connection error to backend.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Background>
      <Content>
        <Logo src="/logo.svg" alt="Logo" />
        <StepIndicator>Step {step} of 2</StepIndicator>
        
        {step === 1 ? (
          <>
            <h2>Personal Information</h2>
            <Row>
              <Input $valid={touched.firstName ? !!form.firstName : null} placeholder="First Name" value={form.firstName} onBlur={() => handleBlur("firstName")} onChange={(e) => handleChange("firstName", e.target.value)} />
              <Input $valid={touched.lastName ? !!form.lastName : null} placeholder="Last Name" value={form.lastName} onBlur={() => handleBlur("lastName")} onChange={(e) => handleChange("lastName", e.target.value)} />
            </Row>
            <Input $valid={touched.email ? emailRegex.test(form.email) : null} placeholder="Email" type="email" value={form.email} onBlur={() => handleBlur("email")} onChange={(e) => handleChange("email", e.target.value)} />
            <Input $valid={touched.phone ? phoneValid : null} placeholder="Phone" type="tel" value={form.phone} onBlur={() => handleBlur("phone")} onChange={(e) => handleChange("phone", e.target.value.replace(/\D/g, ""))} />
            
            <Input 
              type="date" 
              max={getMaxDate()} 
              value={form.dob} 
              $valid={touched.dob ? (form.dob !== "" && form.dob <= getMaxDate()) : null}
              onBlur={() => handleBlur("dob")}
              onChange={(e) => handleChange("dob", e.target.value)} 
            />
            
            <GenderGroup>
              {["Male", "Female"].map((g) => (
                <GenderOption key={g} $active={form.gender === g} onClick={() => { handleChange("gender", g); handleBlur("gender"); }}>{g}</GenderOption>
              ))}
            </GenderGroup>
            <Button disabled={!stepOneValid} onClick={() => setStep(2)}>Next</Button>
          </>
        ) : (
          <>
            <p style={{ cursor: "pointer", fontSize: "14px", color: "#475569", marginBottom: "10px" }} onClick={() => setStep(1)}>← Back</p>
            <h2>Account Setup</h2>
            
            <div style={{ position: "relative" }}>
              <Input 
                $valid={touched.profession ? !!form.profession : null}
                placeholder="Field of Work" 
                value={form.profession} 
                onBlur={() => { handleBlur("profession"); setTimeout(() => setShowSuggestions(false), 150); }}
                onChange={(e) => { handleChange("profession", e.target.value); setShowSuggestions(true); }} 
              />
              {showSuggestions && filteredSuggestions.length > 0 && (
                <SuggestionBox>
                  {filteredSuggestions.map((p) => (
                    <SuggestionItem key={p} onClick={() => { handleChange("profession", p); setShowSuggestions(false); }}>{p}</SuggestionItem>
                  ))}
                </SuggestionBox>
              )}
            </div>

            <div style={{ position: "relative" }}>
              <Input 
                $valid={touched.password ? passwordStrong : null}
                placeholder="Password" 
                type={showPassword ? "text" : "password"} 
                value={form.password} 
                onBlur={() => handleBlur("password")}
                onChange={(e) => handleChange("password", e.target.value)} 
              />
              <span style={{ position: "absolute", right: "15px", top: "12px", cursor: "pointer" }} onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <FiEyeOff /> : <FiEye />}
              </span>
            </div>

            <PasswordHintList>
              <PasswordHintItem $valid={passwordRules.length}>At least 8 characters</PasswordHintItem>
              <PasswordHintItem $valid={passwordRules.uppercase}>Include uppercase</PasswordHintItem>
              <PasswordHintItem $valid={passwordRules.lowercase}>Include lowercase</PasswordHintItem>
              <PasswordHintItem $valid={passwordRules.number}>Include number</PasswordHintItem>
              <PasswordHintItem $valid={passwordRules.symbol}>Include symbol</PasswordHintItem>
            </PasswordHintList>

            <Input 
              $valid={touched.confirmPassword ? (form.password && form.password === form.confirmPassword) : null}
              placeholder="Confirm Password" 
              type="password" 
              value={form.confirmPassword} 
              onBlur={() => handleBlur("confirmPassword")}
              onChange={(e) => handleChange("confirmPassword", e.target.value)} 
            />

            {serverError && <p style={{color: '#ef4444', fontSize: '14px', textAlign: 'center', background: '#fee2e2', padding: '8px', borderRadius: '8px'}}>{serverError}</p>}
            
            <Button disabled={!stepTwoValid || isLoading} onClick={handleSubmit}>
              {isLoading ? "Creating account..." : "Create Account"}
            </Button>
          </>
        )}
      </Content>
    </Background>
  );
}