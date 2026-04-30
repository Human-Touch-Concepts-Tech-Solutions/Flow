"use client";
import { useState } from "react";
import Link from "next/link";
import { FiMenu, FiX, FiArrowRight, FiCheckCircle } from "react-icons/fi";
import {
  DiscoverWrapper,
  Nav,
  NavContainer,
  Logo,
  NavLinkContainer,
  NavLink,
  MenuButton,
  MobileMenu,
  Section,
  Grid,
  Card,
  FAQItem,
  StartBox
} from "./DiscoverStyles";

export default function DiscoverPage() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const capabilities = [
    { title: "No-Code Automation", desc: "Transform complex, repetitive workflows into streamlined operations without writing a single line of code." },
    { title: "Omnichannel Integration", desc: "Enjoy a unified professional experience with multi-platform sync that keeps your assistant accessible wherever you work." },
    { title: "Enterprise-Grade Security", desc: "Operate with peace of mind in a secure environment featuring end-to-end encryption and robust data protection." },
    { title: "Adaptive Intelligence", desc: "Experience a smart assistant that learns your unique professional rhythm, personalizing its support to meet your evolving needs." },
    { title: "Scalable Architecture:", desc: "Whether you are a solo practitioner or leading a global team, Flowtru scales its performance to match your workload without increasing overhead." },
    { title: "Intelligent Insights", desc: "Beyond execution, Flowtru analyzes your workflows to provide actionable insights, identifying bottlenecks before they impact your productivity." }
  ];

  const scrollTo = (id) => {
    setIsMenuOpen(false);
    const element = document.getElementById(id);
    element?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <DiscoverWrapper>
      <Nav>
        <NavContainer>
          <Link href="/"><Logo src="/logo.svg" alt="Flowtru" /></Link>
          
          <NavLinkContainer>
            <NavLink onClick={() => scrollTo("about")}>What is Flowtru</NavLink>
            <NavLink onClick={() => scrollTo("how-to")}>How to Use</NavLink>
            <NavLink onClick={() => scrollTo("faq")}>FAQ</NavLink>
            <Link href="/account/login" className="get-started">Get Started</Link>
          </NavLinkContainer>

          <MenuButton onClick={() => setIsMenuOpen(!isMenuOpen)}>
            {isMenuOpen ? <FiX /> : <FiMenu />}
          </MenuButton>
        </NavContainer>

        {isMenuOpen && (
          <MobileMenu>
            <NavLink onClick={() => scrollTo("about")}>What is Flowtru</NavLink>
            <NavLink onClick={() => scrollTo("how-to")}>How to Use</NavLink>
            <NavLink onClick={() => scrollTo("faq")}>FAQ</NavLink>
            <Link href="/account/login" className="get-started">Get Started</Link>
          </MobileMenu>
        )}
      </Nav>

      <Section id="about">
        <h1>What is Flowtru?</h1>
        <p>
        Flowtru is your intelligent professional orchestrator, bridging the gap between complex tasks and seamless execution through advanced automation. Built for versatility, Flowtru scales across industries—from creative agencies to technical operations—empowering professionals to automate the mundane and focus on what truly matters.

        </p>
        <Grid>
          {capabilities.map((cap, i) => (
            <Card key={i}>
              <FiCheckCircle color="#2f496e" size={24} />
              <h3>{cap.title}</h3>
              <p>{cap.desc}</p>
            </Card>
          ))}
        </Grid>
      </Section>

      {/* <Section id="how-to" $light>
  <h2>How to Use Flowtru</h2>
  <div className="steps">
     <p><strong>1. Create Account:</strong> Securely sign up and set your professional profile.</p>
  </div>
</Section> */}

      <Section id="faq">
        <h2>Frequently Asked Questions</h2>
        <FAQItem>
          <h4>Is my data secure?</h4>
          <p>Yes, Flowtru uses end-to-end encryption for all user data and professional files.</p>
        </FAQItem>
        <FAQItem>
          <h4>Can I use it for my team?</h4>
          <p>Flowtru offers collaborative plans designed for team-wide productivity.</p>
        </FAQItem>
      </Section>

      <StartBox>
        <h3>Ready to optimize your workflow?</h3>
        <Link href="/account/login" className="cta">
          Get Started Now <FiArrowRight />
        </Link>
      </StartBox>
    </DiscoverWrapper>
  );
}