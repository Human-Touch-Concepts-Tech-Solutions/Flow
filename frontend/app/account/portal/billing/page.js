"use client";

import Payment from "@/components/Payment/Payment";
import Navigation from "@/components/Navigation/Navigation";
import Footer from "@/components/Footer/Footer";


export default function BillingPage() {

  return (
    <div style={{ minHeight: '100vh', background: '#ffffff' }}>
      
      <Navigation />
      <Payment /> {/* Optional: Pass user to Payment if needed */}
      <Footer />
    </div>
  );
}