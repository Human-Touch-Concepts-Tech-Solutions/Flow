"use client";
import Payment from "@/components/Payment/Payment";
import Navigation from "@/components/Navigation/Navigation";
import { UserProvider } from "@/providers/UserProvider"; // Ensure provider is present

export default function BillingPage() {
  return (
    <UserProvider> 
      <div style={{ minHeight: '100vh', background: '#ffffff' }}>
        <Navigation />
        <Payment />
      </div>
    </UserProvider>
  );
}