
import Navigation from "@/components/Navigation/Navigation";
import Footer from "@/components/Footer/Footer";
import Checkout from "@/components/Checkout/Checkout";

export default function CheckoutPage() {
  return (
    <main style={{ minHeight: '100vh', background: '#ffffff' }}>
      <Navigation />
     <Checkout />
    
    </main>
  );
}