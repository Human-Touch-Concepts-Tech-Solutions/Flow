"use client";
import { useEffect, useState } from "react";

export default function PresentationPage() {
  const [content, setContent] = useState("<h1>Waiting for presentation...</h1>");

  useEffect(() => {
    // 1. Listen for data coming from the ChatInterface
    const handleMessage = (event) => {
      if (event.data.type === "UPDATE_PRESENTATION") {
        setContent(event.data.htmlContent);
      }
    };

    window.addEventListener("message", handleMessage);

    // 2. Tell the ChatInterface that we are open and ready
    if (window.opener) {
      window.opener.postMessage({ type: "CHILD_READY" }, "*");
    }

    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden' }}>
      <div dangerouslySetInnerHTML={{ __html: content }} />
    </div>
  );
}