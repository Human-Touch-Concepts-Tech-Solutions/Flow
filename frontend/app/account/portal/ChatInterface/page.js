"use client";
import { useState, useEffect, useRef } from "react";
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
  // Use effect logic for WebSocket connection and notifications
  const wsRef = useRef(null);
  const [notification, setNotification] = useState(null);


  

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




useEffect(() => {
    // 1. Prevent duplicate connections if already connected or connecting
    if (wsRef.current !== null) return; 

    console.log("WebSocket: Attempting to connect...");
    const ws = getSecureSocket("/ws/notifications");
    
    if (!ws) {
      console.error("WebSocket: getSecureSocket returned null!");
      return;
    }

    wsRef.current = ws; // Store the instance in the ref

    ws.onopen = () => {
      console.log("WebSocket: Connection established!");
      ws.send(JSON.stringify({ type: 'PING' }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case "popup":
            setNotification(data);
            break;
          case "PONG":
            console.log("WebSocket: PONG received");
            break;
          default:
            console.log("WebSocket: Received", data.type);
        }
      } catch (err) {
        console.error("WebSocket: Parse error", err);
      }
    };

    ws.onerror = (error) => {
  // Check readyState: if it's closing or closed, ignore the error
  if (ws.readyState === WebSocket.CLOSING || ws.readyState === WebSocket.CLOSED) {
    return;
  }
  console.error("WebSocket: Actual connection error:", error);
};

    ws.onclose = (event) => {
      console.log(`WebSocket: Closed. Code: ${event.code}`);
      wsRef.current = null; // Important: Clear ref so it can reconnect if needed
    };

    // Keep alive
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'PING' }));
      }
    }, 30000);

    return () => {
  clearInterval(ping);
  if (wsRef.current) {
    // Only close if it's actually open
    if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
    }
    wsRef.current = null;
  }
};
  }, []);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
     {/* THE POPUP CONTAINER */}
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