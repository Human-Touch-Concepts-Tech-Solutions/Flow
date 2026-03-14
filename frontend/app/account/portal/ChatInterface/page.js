"use client";
import { useState } from "react";
import Navigation from "@/components/Navigation/Navigation";
import Footer from "@/components/Footer/Footer";
import UserInput from "@/components/UserInput/UserInput";
import MessageList from "@/components/MessageList/MessageList";
// Import your authenticated fetch utility
import { authenticatedFetch } from "@/lib/api"; 

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Navigation />
      <main style={{ flex: 1, overflowY: 'auto' }}>
        <MessageList messages={messages} isLoading={isLoading} />
      </main>
      <UserInput onSend={handleSendMessage} />
      <Footer />
    </div>
  );
}