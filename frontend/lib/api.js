// lib/api.js

/**
 * Helper: Constructs the full URL including the dynamic API version.
 * If no version is found in localStorage, it defaults to 'v1'.
 */
const getVersionedUrl = (endpoint) => {
  const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/$/, "");
  
  let version = "v1";
  if (typeof window !== 'undefined') {
    // We check if the backend has pinned this user to a specific version (e.g., v2)
    version = localStorage.getItem("user_api_version") || "v1";
  }

  // Ensure endpoint starts with a single slash for consistency
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  
  // Final Structure: https://your-api.com/api/v1/auth/register
  return `${baseUrl}/api/${version}${cleanEndpoint}`;
};

/**
 * Authenticated Fetch: Reuses JWT token and handles version-based redirects.
 */
export const authenticatedFetch = async (endpoint, options = {}) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem("access_token") : null;
  
  if (!token) {
    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
      window.location.href = "/account/login";
    }
    return null;
  }

  const fullUrl = getVersionedUrl(endpoint);

  const headers = {
    "Authorization": `Bearer ${token}`,
    "ngrok-skip-browser-warning": "69420", // Bypass for development
    ...options.headers,
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const res = await fetch(fullUrl, { ...options, headers });

    // 1. Handle Version Upgrade (426 Upgrade Required)
    if (res.status === 426) {
      const data = await res.json();
      // Backend tells us: "You need v2 for this user"
      localStorage.setItem("user_api_version", data.required_version || "v2");
      window.location.href = "/account/complete-profile"; 
      return null;
    }

    // 2. Handle Token Expiration
    if (res.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/account/login";
      return null;
    }

    if (!res.ok) return null;

    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return await res.json();
    }
    return null;

  } catch (error) {
    console.warn("API Connection hiccup:", error);
    return null; 
  }
};

/**
 * Public Fetch: No token required, used for Register, Login, and Professions.
 */
export const publicFetch = async (endpoint, options = {}) => {
  const fullUrl = getVersionedUrl(endpoint);

  try {
    const res = await fetch(fullUrl, {
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

    return await res.json();
  } catch (error) {
    throw error;
  }
};

/**
 * Secure WebSocket: Reuses the same versioning logic as HTTP.
 */
export const getSecureSocket = (endpoint) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem("access_token") : null;
  
  if (!token) {
    console.error("WebSocket failed: No access token found.");
    return null;
  }

  // Generate the versioned HTTP URL and convert to WS
  const httpUrl = getVersionedUrl(endpoint);
  
  // Converts http://... to ws://... and https://... to wss://...
  const wsUrl = httpUrl.replace(/^http/, "ws");
  
  // Append token as query param for the FastAPI handshake
  const finalUrl = `${wsUrl}?token=${token}`;

  return new WebSocket(finalUrl);
};