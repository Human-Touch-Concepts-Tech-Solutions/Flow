"use client";
import Navigation from "@/components/Navigation/Navigation";
import Footer from "@/components/Footer/Footer";
export default function ChatInterface() {
  

  return (
   <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Navigation />
        <main style={{ flex: 1, overflowY: 'auto' }}>
          {/* Chat logic here */}
        </main>
        <Footer />
      </div>
  );
}