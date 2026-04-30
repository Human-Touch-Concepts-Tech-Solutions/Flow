"use client";
import { useState } from "react";
import Link from "next/link";
import { FiArrowRight, FiTag, FiInfo } from "react-icons/fi";
import { 
  Background, 
  Content, 
  Logo, 
  CTA, 
  TopNav, 
  NavGroup,
  NavLink 
} from "./LandingPageStyles";

export default function LandingPage() {
  return (
    <Background>
      <TopNav>
        <NavGroup>
          <NavLink as={Link} href="/discover">
            <FiInfo /> Discover
          </NavLink>
          <NavLink as={Link} href="/pricing">
            <FiTag /> Pricing
          </NavLink>
        </NavGroup>
      </TopNav>

      <Content>
        <Logo src="/logo.svg" alt="Flowtru Intelligent Assistant"/>
        <h2>Your Intelligent Assistant for Smarter Workflows</h2>
        <p>Automate tasks, organize ideas, and interact with AI in a seamless, secure environment.</p>

        <CTA as={Link} href="/account/login">
          Get Started <FiArrowRight />
        </CTA>
      </Content>
    </Background>
  );
}