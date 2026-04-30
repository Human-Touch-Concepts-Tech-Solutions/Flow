"use client";
import React, { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { FiCreditCard, FiPackage, FiArrowLeft, FiX, FiCheckCircle } from "react-icons/fi"; // Added FiX
import * as S from "./CheckoutStyles";
import { authenticatedFetch } from "@/lib/api";


export default function Checkout() {

  const [isSuccess, setIsSuccess] = useState(false);
const [loading, setLoading] = useState(false);


  const router = useRouter();
  
  const [order, setOrder] = useState(() => {
    if (typeof window !== "undefined") {
      const data = sessionStorage.getItem("pending_plan");
      return data ? JSON.parse(data) : null;
    }
    return null;
  });

  useEffect(() => {
    if (!order) {
      router.replace("/pricing");
    }
  }, [order, router]);

  const totals = useMemo(() => {
    if (!order) return { subtotal: 0, tax: 0, total: 0 };
    
    // 1. Convert to string safely, then strip commas, then parse to float
    // This handles both Number and String types perfectly
    const rawValue = String(order.totalPrice).replace(/,/g, "");
    const subtotal = parseFloat(rawValue) || 0;

    // 2. Calculate VAT and Total
    const tax = subtotal * 0.075; 
    const total = subtotal + tax;
    
    return { subtotal, tax, total };
  }, [order]);

  const handleQuit = () => {
   sessionStorage.removeItem("pending_plan");
    const lastSessionId = localStorage.getItem("chat_session_id");
    const isAdmin = window.location.pathname.includes("/admin/");
    
    let targetPath = lastSessionId 
      ? `/account/portal${isAdmin ? '/admin' : ''}/ChatInterface/${lastSessionId}`
      : `/account/portal${isAdmin ? '/admin' : ''}/ChatInterface`;
    
    router.push(targetPath);
  };

 const handlePayment = async () => {
  setLoading(true);
  try {
    const result = await authenticatedFetch("/auth/billing/checkout/complete", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        planType: order.planType,
        credits: order.credits,
        billingCycle: order.billingCycle,
        totalPrice: totals.total,
      }),
    });

    // If authenticatedFetch returns the DATA directly, check it here
    // If it returns { status: 'success' }, then we are good!
    if (result && (result.status === "success" || result.message)) {
      setIsSuccess(true);
      sessionStorage.removeItem("pending_plan");

      setTimeout(() => {
        handleQuit();
      }, 6000);
    } else {
      alert(`Payment failed: ${result?.detail || "Unknown error"}`);
    }
  } catch (error) {
    console.error("Checkout Request Error:", error);
    // This is where your 'response.json is not a function' was likely caught
    alert("An error occurred. Check the console for details.");
  } finally {
    setLoading(false);
  }
};
if (isSuccess) {
  return (
    <S.Container style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <S.SummaryCard style={{ textAlign: 'center', padding: '3rem' }}>
        <FiCheckCircle size={80} color="#10b981" style={{ marginBottom: '1.5rem' }} />
        <h2 style={{ fontSize: '2rem' }}>Payment Successful!</h2>
        <p style={{ fontSize: '1.1rem', color: '#64748b' }}>
          {order.credits.toLocaleString()} credits have been added to your account.
        </p>
        <p style={{ marginTop: '2rem', fontSize: '0.9rem' }}>
          Redirecting to dashboard in 6 seconds...
        </p>
        <S.PayButton onClick={handleQuit} style={{ marginTop: '1rem' }}>
          Go to Dashboard Now
        </S.PayButton>
      </S.SummaryCard>
    </S.Container>
  );
}
  if (!order) return null;

  return (
    <S.Container>
      <S.CheckoutHeader>
        <S.BackBtn onClick={() => router.push("billing")}>
          <FiArrowLeft /> Change Plan
        </S.BackBtn>

        <S.QuitBtn onClick={handleQuit}>
          <FiX /> Quit Checkout
        </S.QuitBtn>
      </S.CheckoutHeader>

      <S.CheckoutGrid>
        <S.SummaryCard>
          <h2>Confirm your subscription</h2>
          <p>Review your plan details before proceeding to payment.</p>
          
          <S.PlanDetail>
            <div className="icon-box"><FiPackage /></div>
            <div className="details">
              <strong>{order.planType} Plan</strong>
              <span>{order.credits.toLocaleString()} Credits / {order.billingCycle}</span>
            </div>
          </S.PlanDetail>

          <S.PriceTable>
            <div className="row">
              <span>Subtotal ({order.billingCycle})</span>
              <span>₦{totals.subtotal.toLocaleString()}</span>
            </div>
            <div className="row">
              <span>VAT (7.5%)</span>
              <span>₦{totals.tax.toLocaleString()}</span>
            </div>
            <div className="row total">
              <span>Total to Pay</span>
              <span>₦{totals.total.toLocaleString()}</span>
            </div>
          </S.PriceTable>
        </S.SummaryCard>

        <S.PaymentCard>
          <h3>Secure Checkout</h3>
          <p>Payments are processed securely via encrypted channels.</p>
          
          <S.PayButton onClick={handlePayment}>
            <FiCreditCard /> Pay ₦{totals.total.toLocaleString()}
          </S.PayButton>
          
          <S.SecureNote>
            Guaranteed safe checkout. Cancel anytime from your settings.
          </S.SecureNote>
        </S.PaymentCard>
      </S.CheckoutGrid>
    </S.Container>
  );
}