"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { FiArrowLeft, FiCheckCircle } from "react-icons/fi";
import * as S from "./PricingStyles";

export default function Pricing() {
  const router = useRouter();
  const [isYearly, setIsYearly] = useState(false);
  
  // milestones for the measurement-style track
  const milestones = [100, 1000, 2000, 3000, 5000, 7500, 10000, 10100];
  
  // sliderVal tracks the POSITION (0 to 7), not the credits
  const [sliderVal, setSliderVal] = useState(0);

  // Math to convert slider position (0-7) to actual credits
  const getCreditsFromSlider = (val) => {
    const index = Math.floor(val);
    const remainder = val - index;
    
    if (index >= milestones.length - 1) return milestones[milestones.length - 1];
    
    const start = milestones[index];
    const end = milestones[index + 1];
    
    // Smoothly calculate credits between milestones
    const exactCredits = start + (end - start) * remainder;
    
    // Round to nearest 100 for a professional "ruler" feel
    return Math.round(exactCredits / 100) * 100;
  };

  const credits = getCreditsFromSlider(sliderVal);

  const calculatePrice = (creditCount, pkg) => {
    if (pkg.type === "Free") return "0";
    if (pkg.type === "Enterprise" || (pkg.max && creditCount > pkg.max)) {
        return pkg.type === "Enterprise" ? "Custom" : "—";
    }

    // BUSINESS FLOOR LOGIC: Team plan stays at 30k (300 credits) minimum
    let effectiveCredits = creditCount;
    if (pkg.type === "Team") {
      effectiveCredits = Math.max(300, creditCount);
    }

    const monthlyPrice = effectiveCredits * 100;
    
    if (!isYearly) return monthlyPrice.toLocaleString();
    
    const yearlyTotal = (monthlyPrice * 12) * 0.9;
    return Math.round(yearlyTotal).toLocaleString();
  };

 const handlePlanSelection = (pkg) => {
    if (pkg.type === "Enterprise") {
      router.push("/contact");
      return;
    }

    // ✅ This is allowed because it only runs when a user clicks, 
    // not every time the component renders.
    const now = Date.now(); 

    const selection = {
      planType: pkg.type,
      credits: credits,
      billingCycle: isYearly ? "yearly" : "monthly",
      totalPrice: calculatePrice(credits, pkg),
      timestamp: now 
    };

    sessionStorage.setItem("pending_plan", JSON.stringify(selection));
    router.push(`/account/login?intent=upgrade&plan=${pkg.type.toLowerCase()}`);
  };

  const packages = [
    {
      name: "Explorer",
      type: "Free",
      desc: "Perfect for testing advanced AI workflows.",
      features: ["10 Free Credits", "Core platform access", "Standard support"]
    },
    {
      name: "Professional",
      type: "Professional",
      desc: "For individual power users.",
      primary: true,
      max: 3000, 
      features: ["Priority processing", "Personal Workspace", "Continuous automation"]
    },
    {
      name: "Business Team",
      type: "Team",
      desc: "Collaborative workspace for teams.",
      max: 10000, 
      features: ["Shared Credit Pool", "Team Management", "Unlimited task chains"]
    },
    {
      name: "Enterprise",
      type: "Enterprise",
      desc: "Custom high-volume infrastructure.",
      features: ["Unlimited Users", "10,000+ Credits", "24/7 VIP Support", "On-premise option"]
    }
  ];

  return (
    <S.PageContainer>
      <S.BackButton onClick={() => router.back()}>
        <FiArrowLeft /> Back to Home
      </S.BackButton>

      <S.HeaderSection>
        <S.Chip>Flexible Pricing</S.Chip>
        <h1>Scale your AI as you grow</h1>
        <p>Simple ₦100/credit pricing. Sliding scale volume discounts apply automatically.</p>
      </S.HeaderSection>

      <S.ToggleWrapper>
        <S.ToggleLabel $active={!isYearly}>Monthly</S.ToggleLabel>
        <S.Switch $isYearly={isYearly} onClick={() => setIsYearly(!isYearly)} />
        <S.ToggleLabel $active={isYearly}>
          Yearly <S.DiscountBadge>Save 10%</S.DiscountBadge>
        </S.ToggleLabel>
      </S.ToggleWrapper>

      <S.SliderCard>
        <div className="card-top">
          <div className="text-group">
            <h3>Custom Credit Volume</h3>
            <p>Drag to select your required monthly capacity</p>
          </div>
          <div className="val-group">
            <span className="num">{credits > 10000 ? "10,000+" : credits.toLocaleString()}</span>
            <span className="unit">Credits / mo</span>
          </div>
        </div>
        
        <S.SliderBox>
          <input 
            type="range" 
            min="0" 
            max={milestones.length - 1} 
            step="0.01" // High precision for smooth ruler movement
            value={sliderVal} 
            onChange={(e) => setSliderVal(parseFloat(e.target.value))} 
          />
          <S.TrackFill $progress={(sliderVal / (milestones.length - 1)) * 100} />
          
          <S.TicksContainer>
            {milestones.map((m, idx) => (
              <S.TickMarker 
                key={m} 
                $active={idx <= sliderVal} 
                $left={(idx / (milestones.length - 1)) * 100}
                $current={Math.round(sliderVal) === idx}
              >
                <div className="line" />
                <span>{m === 10100 ? "10k+" : (m >= 1000 ? `${m/1000}k` : m)}</span>
              </S.TickMarker>
            ))}
          </S.TicksContainer>
        </S.SliderBox>
      </S.SliderCard>

      <S.PlanGrid>
        {packages.map((pkg, index) => {
          const isOverLimit = pkg.max && credits > pkg.max;
          const isEnterpriseState = credits > 10000 && pkg.type === "Enterprise";
          const currentPrice = calculatePrice(credits, pkg);

          return (
            <S.PlanCard 
                key={index} 
                $featured={pkg.primary || isEnterpriseState} 
                $disabled={isOverLimit}
            >
              {pkg.primary && !isOverLimit && <S.FeaturedBadge>Recommended</S.FeaturedBadge>}
              <S.PlanInfo>
                <S.PlanName>{pkg.name}</S.PlanName>
                <S.PlanDesc>{pkg.desc}</S.PlanDesc>
              </S.PlanInfo>
              
              <S.PriceArea>
                <div className="price-val">
                  {currentPrice === "Custom" || currentPrice === "—" ? (
                      currentPrice
                  ) : (
                      <><span>₦</span>{currentPrice}</>
                  )}
                </div>
                {currentPrice !== "Custom" && currentPrice !== "—" && pkg.type !== "Free" && (
                  <div className="price-sub">per {isYearly ? 'year' : 'month'}</div>
                )}
              </S.PriceArea>

              <S.FeatureList>
                {pkg.features.map((feat, i) => (
                  <li key={i}><FiCheckCircle className="icon" /> {feat}</li>
                ))}
              </S.FeatureList>

              <S.PlanButton 
                $primary={pkg.primary || isEnterpriseState}
                disabled={isOverLimit}
                onClick={() => handlePlanSelection(pkg)}
              >
                {pkg.type === "Enterprise" ? "Contact Sales" : "Select Plan"}
              </S.PlanButton>
            </S.PlanCard>
          );
        })}
      </S.PlanGrid>
    </S.PageContainer>
  );
}