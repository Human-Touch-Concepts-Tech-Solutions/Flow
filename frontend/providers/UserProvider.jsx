"use client";
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { authenticatedFetch } from "@/lib/api";

const UserContext = createContext(null);

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // We use useCallback so this function can be passed around safely
  const fetchUserData = useCallback(async () => {
    try {
      const data = await authenticatedFetch("/auth/user-info");
      if (data) {
        setUser(data);
      } else {
        // If fetch returns null (e.g., 401), we clear user
        setUser(null);
      }
    } catch (err) {
      console.error("Portal fetch error:", err);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  return (
    <UserContext.Provider value={{ user, isLoading, refreshUser: fetchUserData }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
};