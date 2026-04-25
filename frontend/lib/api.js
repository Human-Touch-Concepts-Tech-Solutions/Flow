// lib/api.js


const getBrowserName = () => {
  const ua = navigator.userAgent;
  if (ua.includes("Firefox")) return "Mozilla Firefox";
  if (ua.includes("SamsungBrowser")) return "Samsung Internet";
  if (ua.includes("Opera") || ua.includes("OPR")) return "Opera";
  if (ua.includes("Trident")) return "Internet Explorer";
  if (ua.includes("Edge")) return "Microsoft Edge";
  if (ua.includes("Chrome")) return "Google Chrome";
  if (ua.includes("Safari")) return "Apple Safari";
  return "Unknown Browser";
};


// Client details gathering for analytics and debugging
const getClientMetadata = () => {
  if (typeof window === 'undefined') return {};

  const now = new Date();
  
  return {
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    // 1. Capture time EXACTLY as shown on the device clock
    client_time: now.toLocaleString(), 
    // 2. Identify the specific browser
    browser: getBrowserName(),
    screen_resolution: `${window.screen.width}x${window.screen.height}`,
    viewport_size: `${window.innerWidth}x${window.innerHeight}`,
    device_platform: navigator.platform,
    user_agent: navigator.userAgent,
    is_touch_device: 'ontouchstart' in window || navigator.maxTouchPoints > 0
  };
};


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
// lib/api.js

export const authenticatedFetch = async (endpoint, options = {}) => {
  let token = typeof window !== 'undefined' ? localStorage.getItem("access_token") : null;
  let sessionId = typeof window !== 'undefined' ? localStorage.getItem("chat_session_id") : null;
  if (!token) {
    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
      window.location.href = "/account/login";
    }
    return null;
  }

  const metadata = getClientMetadata();

  const fullUrl = getVersionedUrl(endpoint);
  const headers = {
    "Authorization": `Bearer ${token}`,
    "X-Session-ID": sessionId,
    "ngrok-skip-browser-warning": "69420",
    // Client metadata for analytics and debugging
    "X-Client-Timezone": metadata.timezone,
    "X-Client-Time": metadata.client_time,
    "X-Client-Resolution": metadata.screen_resolution,
    "X-Client-Platform": metadata.device_platform,

    "X-Client-Viewport": metadata.viewport_size,
    "X-Client-Browser": metadata.browser,
    "X-Client-Is-Touch-Device": String(metadata.is_touch_device),
    ...options.headers,
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  try {
    let res = await fetch(fullUrl, { ...options, headers });

    // 1. Handle Version Upgrade
    if (res.status === 426) {
      const data = await res.json();
      localStorage.setItem("user_api_version", data.required_version || "v2");
      window.location.href = "/account/complete-profile"; 
      return null;
    }

    // 2. SMART REFRESH LOGIC (The "Assistant")
    if (res.status === 401) {
      const refreshToken = localStorage.getItem("refresh_token");

      if (refreshToken) {
        try {
          // Attempt to get a new access token
          const refreshRes = await fetch(getVersionedUrl("/auth/refresh"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (refreshRes.ok) {
            const data = await refreshRes.json();
            // Save the new pair
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);

            // RETRY the original request with the new token
            headers["Authorization"] = `Bearer ${data.access_token}`;
            res = await fetch(fullUrl, { ...options, headers });
          } else {
            // Refresh token expired too!
            throw new Error("Refresh failed");
          }
        } catch (refreshErr) {
          // Everything failed, go to login
          localStorage.clear();
          window.location.href = "/account/login";
          return null;
        }
      } else {
        window.location.href = "/account/login";
        return null;
      }
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
  const metadata = getClientMetadata();

  try {
    const res = await fetch(fullUrl, {
      ...options,
      headers: {
        "Content-Type": "application/json",

        // Client metadata for analytics and debugging
    "X-Client-Timezone": metadata.timezone,
    "X-Client-Time": metadata.client_time,
    "X-Client-Resolution": metadata.screen_resolution,
    "X-Client-Platform": metadata.device_platform,

    "X-Client-Viewport": metadata.viewport_size,
    "X-Client-Browser": metadata.browser,
    "X-Client-Is-Touch-Device": String(metadata.is_touch_device),

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
// lib/api.js

export const getSecureSocket = (endpoint, passedSessionId = null) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem("access_token") : null;
  const sessionId = passedSessionId || (typeof window !== 'undefined' ? localStorage.getItem("chat_session_id") : null);

  if (!token) return null;

  const metadata = getClientMetadata(); // Uses the helper we created
  const httpUrl = getVersionedUrl(endpoint);
  const wsUrl = httpUrl.replace(/^http/, "ws");
  
  // Build the Query Parameters
  const params = new URLSearchParams({
    token: token,
    session_id: sessionId || "",
    tz: metadata.timezone,
    res: metadata.screen_resolution,
    plt: metadata.device_platform,
    ctime: metadata.client_time, // Important for the TimeManager drift check
    touch: metadata.is_touch_device ? "1" : "0"
    
  });

  const finalUrl = `${wsUrl}?${params.toString()}`;

  return new WebSocket(finalUrl);
};