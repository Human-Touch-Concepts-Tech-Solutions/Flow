"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { FiMail, FiPhone, FiMapPin, FiArrowLeft, FiMessageCircle } from "react-icons/fi";
import * as S from "./ContactStyles";

export default function Contact() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleReturnToChat = () => {
    // 1. Try to get the last active session ID from storage
    const lastSessionId = typeof window !== "undefined" ? localStorage.getItem("chat_session_id") : null;
    const isAdmin = typeof window !== "undefined" && window.location.pathname.includes("/admin/");

    // 2. Construct path: If we have an ID, go to that session, otherwise go to base interface
    let targetPath;
    if (lastSessionId) {
      targetPath = isAdmin 
        ? `/account/portal/admin/ChatInterface/${lastSessionId}` 
        : `/account/portal/ChatInterface/${lastSessionId}`;
    } else {
      targetPath = isAdmin ? "/account/portal/admin/ChatInterface" : "/account/portal/ChatInterface";
    }

    router.push(targetPath);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      alert("Message sent! Our team will reach out shortly.");
      setLoading(false);
      handleReturnToChat();
    }, 1500);
  };

  return (
    <S.ContactContainer>
      <S.ContactCard>
        {/* Left Sidebar */}
        <S.Sidebar>
          <div>
            {/* <button onClick={() => router.back()} className="back-link">
              <FiArrowLeft /> Back
            </button> */}
            <h2>Get in Touch</h2>
            <p>
             Have questions about Flowtru or need a custom solution? 
             Our team is here to help you orchestrate your success.
            </p>

            <S.InfoItem>
              <FiMail className="icon" />
              <span>enterprise@flowtru.ai</span>
            </S.InfoItem>
            <S.InfoItem>
              <FiPhone className="icon" />
              <span>+234 (0) 123 456 7890</span>
            </S.InfoItem>
            <S.InfoItem>
              <FiMapPin className="icon" />
              <span>Lekki, Lagos, Nigeria</span>
            </S.InfoItem>
          </div>
          <div className="copyright">
            © 2026 Flowtru AI Technology.
          </div>
        </S.Sidebar>

        {/* Right Section */}
        <S.FormSection>
          <S.HeaderFlex>
            <h3>Send us a message</h3>
            <S.ReturnBtn type="button" onClick={handleReturnToChat}>
               <FiMessageCircle /> Return 
            </S.ReturnBtn>
          </S.HeaderFlex>

          <S.FormGrid onSubmit={handleSubmit}>
            <S.InputGroup>
              <label>Full Name</label>
              <input type="text" placeholder="John Doe" required />
            </S.InputGroup>

            <S.InputGroup>
              <label>Email</label>
              <input type="email" placeholder="john@company.com" required />
            </S.InputGroup>

            <S.InputGroup className="full">
              <label>Company Name </label>
              <input type="text" placeholder="TechCorp Intl." required />
            </S.InputGroup>

            <S.InputGroup className="full">
              <label>How can we help?</label>
              <select required defaultValue="enterprise">
                <option value="enterprise">Enterprise Plan Inquiry</option>
                <option value="billing">Billing Issue</option>
                <option value="technical">Technical Support</option>
                <option value="Sales">Sales</option>
                <option value="other">Other</option>
              </select>
            </S.InputGroup>

            <S.InputGroup className="full">
              <label>Inquiry Details</label>
              <textarea 
                rows="4" 
                placeholder="We’ll get back to you within 24 hours." 
                required
              />
            </S.InputGroup>

            <div className="full">
              <S.SubmitButton type="submit" disabled={loading}>
                {loading ? "Sending..." : "Send Message"}
              </S.SubmitButton>
            </div>
          </S.FormGrid>
        </S.FormSection>
      </S.ContactCard>
    </S.ContactContainer>
  );
}