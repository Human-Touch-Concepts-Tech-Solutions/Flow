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
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    dob: "",
    gender: "",
    profession: "",
    password: "",
    confirmPassword: "",
  });

  // Helper for Age Limit (15 years)
  const getMaxDate = () => {
    const today = new Date();
    const maxDate = new Date(today.getFullYear() - 15, today.getMonth(), today.getDate());
    return maxDate.toISOString().split("T")[0];
  };

  // 1. Fetch Professions from Backend on Mount
  useEffect(() => {
    const loadProfessions = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/professions`);
        if (res.ok) {
          const data = await res.json();
          setProfessionSuggestions(data);
        }
      } catch (err) {
        setProfessionSuggestions(["Student", "Developer", "Designer", "Writer"]);
      }
    };
    loadProfessions();
  }, []);

  // Validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const phoneValid = /^[0-9]{7,15}$/.test(form.phone); // Now Required

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

    const payload = {
      first_name: form.firstName,
      last_name: form.lastName,
      email: form.email,
      phone: form.phone,
      date_of_birth: form.dob,
      gender: form.gender.toLowerCase(),
      profession: form.profession,
      password: form.password,
    };

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        setServerError(data.detail || "Registration failed.");
        return;
      }

      localStorage.setItem("pending_email", form.email);
      router.push("/account/verify-otp");
    } catch (err) {
      setServerError("Connection error.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Background>
      <Content>
        <Logo src="/logo.svg" alt="Logo" />
        <StepIndicator>Step {step} of 2</StepIndicator>

        {step === 1 && (
          <>
            <h2>Personal Information</h2>
            <Row>
              <Input $valid={touched.firstName ? !!form.firstName : null} placeholder="First Name" value={form.firstName} onBlur={() => handleBlur("firstName")} onChange={(e) => handleChange("firstName", e.target.value)} />
              <Input $valid={touched.lastName ? !!form.lastName : null} placeholder="Last Name" value={form.lastName} onBlur={() => handleBlur("lastName")} onChange={(e) => handleChange("lastName", e.target.value)} />
            </Row>
            <Input $valid={touched.email ? emailRegex.test(form.email) : null} placeholder="Email Address" type="email" value={form.email} onBlur={() => handleBlur("email")} onChange={(e) => handleChange("email", e.target.value)} />
            <Input $valid={touched.phone ? phoneValid : null} placeholder="Phone Number" type="tel" value={form.phone} onBlur={() => handleBlur("phone")} onChange={(e) => handleChange("phone", e.target.value.replace(/\D/g, ""))} />
            <Input $valid={touched.dob ? (form.dob !== "" && form.dob <= getMaxDate()) : null} type="date" max={getMaxDate()} value={form.dob} onBlur={() => handleBlur("dob")} onChange={(e) => handleChange("dob", e.target.value)} />
            <GenderGroup>
              {["Male", "Female"].map((g) => (
                <GenderOption key={g} $active={form.gender === g} onClick={() => { handleChange("gender", g); handleBlur("gender"); }}>{g}</GenderOption>
              ))}
            </GenderGroup>
            <Button disabled={!stepOneValid} onClick={() => setStep(2)}>Next</Button>
          </>
        )}

        {step === 2 && (
          <>
            <p style={{ cursor: "pointer", fontSize: "14px", color: "#475569", marginBottom: "10px" }} onClick={() => setStep(1)}>← Back</p>
            <h2>Account Setup</h2>
            <div style={{ position: "relative" }}>
                <Input $valid={touched.profession ? !!form.profession : null} placeholder="Field of Work" value={form.profession} autoComplete="off" name="work-field" onBlur={() => { handleBlur("profession"); setTimeout(() => setShowSuggestions(false), 150); }} onChange={(e) => { handleChange("profession", e.target.value); setShowSuggestions(true); }} />
                {showSuggestions && filteredSuggestions.length > 0 && (
                <SuggestionBox>
                    {filteredSuggestions.map((item) => (
                    <SuggestionItem key={item} onClick={() => { handleChange("profession", item); setShowSuggestions(false); }}>{item}</SuggestionItem>
                    ))}
                </SuggestionBox>
                )}
            </div>
            <div style={{ position: "relative" }}>
                <Input $valid={touched.password ? passwordStrong : null} placeholder="Password" type={showPassword ? "text" : "password"} value={form.password} onBlur={() => handleBlur("password")} onChange={(e) => handleChange("password", e.target.value)} />
                <span style={{ position: "absolute", right: "15px", top: "12px", cursor: "pointer" }} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <FiEyeOff /> : <FiEye />}</span>
            </div>
            <PasswordHintList>
              <PasswordHintItem $valid={passwordRules.length}>8+ chars</PasswordHintItem>
              <PasswordHintItem $valid={passwordRules.uppercase}>Uppercase</PasswordHintItem>
              <PasswordHintItem $valid={passwordRules.lowercase}>Lowercase</PasswordHintItem>
              <PasswordHintItem $valid={passwordRules.number}>Number</PasswordHintItem>
              <PasswordHintItem $valid={passwordRules.symbol}>Symbol</PasswordHintItem>
            </PasswordHintList>
            <Input $valid={touched.confirmPassword ? (form.password && form.password === form.confirmPassword) : null} placeholder="Confirm Password" type="password" value={form.confirmPassword} onBlur={() => handleBlur("confirmPassword")} onChange={(e) => handleChange("confirmPassword", e.target.value)} />
            {serverError && <div style={{ color: "#ef4444", fontSize: "14px", textAlign: "center", padding: "8px", background: "#fee2e2", borderRadius: "8px", marginBottom: "10px" }}>{serverError}</div>}
            <Button disabled={!stepTwoValid || isLoading} onClick={handleSubmit}>{isLoading ? "Creating..." : "Create Account"}</Button>
          </>
        )}
      </Content>
    </Background>
  );
}