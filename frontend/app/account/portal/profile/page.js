"use client";


import Navigation from "@/components/Navigation/Navigation";
import Footer from "@/components/Footer/Footer";
import Profile from "@/components/Profile/Profile";

export default function ProfilePage() {

  return (
    <div style={{ minHeight: '100vh', background: '#ffffff' }}>
      
      <Navigation />
        <Profile />
      <Footer />
    </div>
  );
}