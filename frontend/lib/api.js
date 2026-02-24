// lib/api.js

// Protected fetch – requires token, used after login (e.g. chat messages)
export const authenticatedFetch = async (endpoint, options = {}) => {
  // 1. Token Management
  const token = typeof window !== 'undefined' ? localStorage.getItem("access_token") : null;
  
  if (!token) {
    // If we're on the client and have no token, redirect to login
    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
      window.location.href = "/account/login";
    }
    return null;
  }

  // 2. URL Preparation
  const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/$/, "");
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const fullUrl = `${baseUrl}${cleanEndpoint}`;

  // 3. Header Construction
  const headers = {
    "Authorization": `Bearer ${token}`,
    "ngrok-skip-browser-warning": "69420", // Bypasses the ngrok interstitial page
    ...options.headers,
  };

  // Only set application/json if we aren't sending a file (FormData)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const res = await fetch(fullUrl, {
      ...options,
      headers: headers,
    });

    // 4. Handle Auth Expiration
    if (res.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/account/login";
      return null;
    }

    // 5. Handle Server Errors (404, 500, etc.)
    if (!res.ok) {
      // Try to get error details, but don't crash if it's not JSON
      try {
        const errorData = await res.json();
        console.warn(`API Error (${res.status}):`, errorData.detail || "Request failed");
      } catch (e) {
        console.warn(`API Error (${res.status}): could not parse error response.`);
      }
      return null;
    }

    // 6. Verify Content Type before parsing
    const contentType = res.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      return null; 
    }

    return await res.json();

  } catch (error) {
    // This catches the "Failed to fetch" (Network timeout, Server restart, Ngrok limit)
    // We log it as a warning instead of an error to keep the console clean during polling
    console.warn("Connection hiccup, sync pending...");
    return null; 
  }
};

// Public fetch  with out authentication, used for things like landing page data or public resources. Still handles errors gracefully.
export const publicFetch = async (endpoint, options = {}) => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    let errorMessage = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      errorMessage = data.detail?.[0]?.msg || data.detail || errorMessage;
    } catch {}
    throw new Error(errorMessage);
  }

  return res.json();
};




// Secure WebSocket connection with token authentication
export const getSecureSocket = (endpoint) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem("access_token") : null;
  
  if (!token) {
    console.error("No token found for WebSocket connection.");
    return null;
  }

  // 1. Prepare Base URL (ws:// or wss://)
  const baseApiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
  const wsBase = baseApiUrl.replace(/^http/, "ws"); // converts http/https to ws/wss
  
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  
  // 2. Append token as query parameter for backend validation
  const fullUrl = `${wsBase}${cleanEndpoint}?token=${token}`;

  // 3. Create the native WebSocket instance
  const socket = new WebSocket(fullUrl);

  return socket;
};