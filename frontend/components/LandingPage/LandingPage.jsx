"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FiArrowRight, FiTag } from "react-icons/fi";

// Styled-components imports
import { 
  Background, 
  Content, 
  Logo, 
  CTA, 
  TopNav, 
  PricingLink 
} from "./LandingPageStyles";

export default function LandingPage() {
  const router = useRouter();

  // Loading state for the main CTA button
  const [loading, setLoading] = useState(false);

  const handleStart = () => {
    setLoading(true);
    // Synthetic delay for animation feel before routing
    setTimeout(() => {
      router.push("/account/login");
    }, 1000);
  };

  const goToPricing = () => {
    // Redirects to the guest pricing page
    router.push("/pricing");
  };

  return (
    <Background>
      {/* Permanent Top Navigation */}
      <TopNav>
        <PricingLink onClick={goToPricing}>
          <FiTag /> Pricing
        </PricingLink>
      </TopNav>

      {/* Central content container */}
      <Content>
        {/* App logo */}
        <Logo 
          src="/logo.svg" 
          alt="Logo"
        />

        {/* Marketing headline */}
        <h2>Your Intelligent Assistant for Smarter Workflows</h2>

        {/* Short product description */}
        <p>
          Automate tasks, organize ideas, and interact with AI in a seamless,
          secure environment designed for productivity.
        </p>

        {/* Call-to-action button */}
        <CTA 
          onClick={handleStart} 
          disabled={loading}
        >
          {loading ? (
            "Loading..."
          ) : (
            <>
              Get Started <FiArrowRight />
            </>
          )}
        </CTA>
      </Content>
    </Background>
  );
}