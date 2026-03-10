"use client";


import Navigation from "@/components/Navigation/Navigation";
import Footer from "@/components/Footer/Footer";
import Settings from "@/components/Settings/Settings";

export default function SettingsPage() {

  return (
    <div style={{ minHeight: '100vh', background: '#ffffff' }}>
      
      <Navigation />
        <Settings />
      <Footer />
    </div>
  );
}