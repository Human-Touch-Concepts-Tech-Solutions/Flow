"use client";
import { useState, useEffect } from "react";
import Navigation from "@/components/Navigation/Navigation";
import Footer from "@/components/Footer/Footer";
import UserInput from "@/components/UserInput/UserInput";
import MessageList from "@/components/MessageList/MessageList";
import SystemPopup from "@/components/SystemPopup/SystemPopup";
// Import your authenticated fetch utility
import { authenticatedFetch , getSecureSocket} from "@/lib/api"; 

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);


  

  // Inside ChatInterface/page.js
const handleSendMessage = async (text, files = []) => { 
  // Safety check: ensure 'files' is always an array
  const safeFiles = Array.isArray(files) ? files : [files].filter(Boolean);

  const userMsg = { 
    role: "user", 
    text, 
    files: safeFiles.map(f => ({ name: f.name })) 
  };
  
  setMessages((prev) => [...prev, userMsg]);
  setIsLoading(true);

  try {
    const formData = new FormData();
    if (text) formData.append("message", text);
    
    // Send using the array
    safeFiles.forEach((file) => {
      formData.append("files", file);
    });

    const data = await authenticatedFetch("/chat/", {
      method: "POST",
      body: formData,
    });

    setMessages((prev) => [
      ...prev, 
      { 
        role: "ai", 
        text: data.reply,
        files: data.files_received || [] // Default to empty array
      }
    ]);
  } catch (error) {
    setMessages((prev) => [...prev, { role: "system", text: `Error: ${error.message}` }]);
  } finally {
    setIsLoading(false);
  }
};


const [notification, setNotification] = useState(null);

 useEffect(() => {
    let ws = getSecureSocket("/ws/notifications");
    if (!ws) return;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "popup") {
        setNotification(data);
      }
    };

    ws.onclose = () => {
      console.log("Socket closed. Not reloading page, just logging.");
      // REMOVE: window.location.reload(); 
    };

    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'PING' }));
      }
    }, 30000); // Send a ping every 30 seconds

    // Remember to clear it!
    return () => {
      clearInterval(pingInterval);
      ws.close();
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <SystemPopup 
        isOpen={!!notification} 
        data={notification} 
        onClose={() => setNotification(null)} 
      />
      <Navigation />
      <main style={{ flex: 1, overflowY: 'auto' }}>
        <MessageList messages={messages} isLoading={isLoading} />
      </main>
      <UserInput onSend={handleSendMessage} />
      <Footer />
    </div>
  );
}