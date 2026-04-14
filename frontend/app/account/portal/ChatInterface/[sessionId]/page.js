"use client";
import { useState, useEffect, useRef } from "react";
import {useParams, useRouter} from "next/navigation";
import Navigation from "@/components/Navigation/Navigation";
import Footer from "@/components/Footer/Footer";
import UserInput from "@/components/UserInput/UserInput";
import MessageList from "@/components/MessageList/MessageList";
import SystemPopup from "@/components/SystemPopup/SystemPopup";
import PreviewPanel from "@/components/PreviewPanel/PreviewPanel";
// Import your authenticated fetch utility
import { authenticatedFetch , getSecureSocket} from "@/lib/api"; 

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Use effect logic for WebSocket connection and notifications
  const wsRef = useRef(null);
  const [notification, setNotification] = useState(null);
  const [preview, setPreview] = useState(null);

  // for presentation
  const presentationWindow = useRef(null);
  const pendingPresentationData = useRef(null);

  // for seesion management
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId;

useEffect(() => {
    // This listens for the "I am open!" signal from the new tab
    const handleChildMessage = (event) => {
        if (event.data.type === "CHILD_READY" && presentationWindow.current) {
            console.log("Tab is ready, beaming data...");
            presentationWindow.current.postMessage({
                type: "UPDATE_PRESENTATION",
                htmlContent: pendingPresentationData.current
            }, "*");
        }
    };

    window.addEventListener("message", handleChildMessage);

    window.initPresentation = () => {
        // Close the popup first
        if (window.closeSystemPopup) window.closeSystemPopup();
        
        // Open the tab (This works because it's triggered by the button click)
        presentationWindow.current = window.open(
            "/account/portal/presentation",
            "_blank",
            "resizable=yes,scrollbars=yes,status=yes"
        );
    };

    return () => {
        window.removeEventListener("message", handleChildMessage);
        delete window.initPresentation;
    };
}, []);




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
  // 
  if (!sessionId) {
            const savedId = localStorage.getItem('chat_session_id');
            if (savedId) {
                router.replace(`/account/portal/ChatInterface/${savedId}`);
            }
            return;
        }
  
  // localStorage for api.js to find
  console.log("DEBUG: Found Session ID in URL:", sessionId);
  localStorage.setItem('chat_session_id', sessionId);
  
  const connectWS = () => {
    const token = localStorage.getItem("access_token");
    if (!token) return; // Exit silently if we are logging out

    if (wsRef.current !== null) return;

    const ws = getSecureSocket("/ws/notifications", sessionId);
    if (!ws) return;

    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Event Received:", data.type);

        switch (data.type) {
          case "popup":
            setNotification(data);
            break;
          case "preview":
            setPreview(data);
            break;
          case "presentation_prompt":
    // 1. Save the big HTML payload for later
    pendingPresentationData.current = data.payload; 
    
    // 2. Show the popup with the button we sent from backend
    setNotification({
        title: data.title,
        htmlContent: data.htmlContent
    });
    break;
          case "PONG":
            break;
          default:
            console.log("WebSocket: Unknown type", data.type);
        }
      } catch (err) {
        console.error("WebSocket: Parse error", err);
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket: Closed (${event.code}). Reconnecting in 2s...`);
      wsRef.current = null;
      // THE FIX: Automatically try to reconnect after 2 seconds
      setTimeout(connectWS, 2000); 
    };

    ws.onerror = (error) => {
      if (ws.readyState !== WebSocket.CLOSED) {
        console.error("WebSocket Error:", error);
      }
    };
  };

  connectWS();

  // Heartbeat to keep Docker from killing the connection
  const ping = setInterval(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'PING' }));
    }
  }, 20000);

  return () => {
    clearInterval(ping);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };
}, [sessionId]);
 return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', position: 'relative' }}>
      
      {/* 1. OVERLAY COMPONENTS (Always fixed/absolute) */}
      <SystemPopup 
        isOpen={!!notification} 
        data={notification} 
        onClose={() => setNotification(null)} 
      />

      {/* 2. THE MAIN WRAPPER (Flex Row) */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        
        {/* 3. CHAT COLUMN (Takes all available space) */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <Navigation />
          <main style={{ flex: 1, overflowY: 'auto' }}>
            <MessageList messages={messages} isLoading={isLoading} />
          </main>
          <UserInput onSend={handleSendMessage} />
          <Footer />
        </div>

        {/* 4. PREVIEW PANEL (Slides in from the right) */}
        <PreviewPanel 
          data={preview} 
          onClose={() => setPreview(null)} 
        />
        
      </div>
    </div>
  );
}