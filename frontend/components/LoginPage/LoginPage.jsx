"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FiLogIn } from "react-icons/fi";
import { FcGoogle } from "react-icons/fc";
import { FaApple } from "react-icons/fa";
import { publicFetch } from "@/lib/api";

import {
  Background,
  Content,
  Logo,
  Input,
  Button,
  BackLink,
  Divider,
  OAuthButton,
  SignupText,
  ForgotPasswordLink,
} from "./LoginPageStyles";

export default function LoginPage() {
  const router = useRouter();

  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleAppleSignin = () => {
    alert("Sign in with Apple is not available yet. Coming soon");
  };

  const handleLogin = async () => {
    if (!email || !password) {
        setError("Please fill in all fields");
        return;
    }

    setLoading(true);
    setError("");

    try {
        const result = await publicFetch("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        });
  
        // Store tokens
        localStorage.setItem("access_token", result.access_token);
        localStorage.setItem("refresh_token", result.refresh_token);

        // --- NEW REDIRECT LOGIC ---
        
        // 1. Check if they are an admin
        if (result.role === "admin") {
           
            router.push("/account/portal/admin/ChatInterface");
            return;
        }

        // 2. Handle specific "upgrade" intent for regular users
        const params = new URLSearchParams(window.location.search);
        const isUpgrading = params.get("intent") === "upgrade";
        const pendingPlanRaw = sessionStorage.getItem("pending_plan");

        if (pendingPlanRaw && isUpgrading) {
            const plan = JSON.parse(pendingPlanRaw);
            if (plan.planType !== "Free") {
                router.push("/account/portal/checkout");
                return; 
            }
        }

        // 3. Default: Regular User Chat
        router.push("/account/portal/ChatInterface");

    } catch (err) {
        if (err.message === "VERIFY_REQUIRED") {
            localStorage.setItem("pending_email", email);
            router.push("/account/verify-otp");
        } else {
            setError(err.message || "Login failed");
        }
    } finally {
        setLoading(false);
    }
};

  const handleOAuth = (provider) => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/auth/oauth/${provider}`;
  };

  return (
    <Background>
      <Content>
        <Logo src="/logo.svg" alt="Logo" />

        <h2>Welcome Back</h2>
        <p>Sign in to continue to your AI workspace</p>

        {error && <p style={{ color: "red", fontWeight: "600", textAlign: "center" }}>{error}</p>}

        <Input
          type="email"
          placeholder="Email address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
        />

        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />

        <ForgotPasswordLink onClick={() => router.push("/account/recovery")}>
          Forgot password?
        </ForgotPasswordLink>

        <Button onClick={handleLogin} disabled={loading}>
          {loading ? "Signing in..." : <>Sign In <FiLogIn /></>}
        </Button>

        <Divider>or</Divider>

        <OAuthButton onClick={() => handleOAuth("google")}>
          <FcGoogle /> Continue with Google
        </OAuthButton>

        <OAuthButton $apple onClick={handleAppleSignin}>
          <FaApple /> Continue with Apple
        </OAuthButton>

        <SignupText>
          Don’t have an account?
          <span onClick={() => router.push("/account/register")}> Create one </span>
        </SignupText>

        <BackLink onClick={() => router.push("/")}> ← Back to home </BackLink>
      </Content>
    </Background>
  );
}