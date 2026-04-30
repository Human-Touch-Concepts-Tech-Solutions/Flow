"use client";
import styled from "styled-components";

export const Container = styled.div`
  max-width: 1000px;
  margin: 0 auto;
  padding: 60px 24px;
  font-family: var(--font-geist-sans), sans-serif;
`;

// New Header to align buttons
export const CheckoutHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
`;

export const BackBtn = styled.button`
  background: none; border: none; display: flex; align-items: center; gap: 8px;
  color: #64748b; font-weight: 600; cursor: pointer;
  transition: color 0.2s;
  &:hover { color: var( --lightblue); }
`;

// New Quit Button style
export const QuitBtn = styled.button`
  background: #fee2e2; border: none; display: flex; align-items: center; gap: 8px;
  color: #ef4444; font-weight: 600; cursor: pointer;
  padding: 8px 16px; border-radius: 12px;
  transition: all 0.2s;
  &:hover { background: #fecaca; transform: scale(1.02); }
`;

export const CheckoutGrid = styled.div`
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 40px;
  @media (max-width: 768px) { grid-template-columns: 1fr; }
`;

export const SummaryCard = styled.div`
  background: #fff; border: 1px solid #e2e8f0; border-radius: 24px; padding: 40px;
  h2 { font-size: 1.75rem; color: #0f172a; margin-bottom: 8px; }
  p { color: #64748b; margin-bottom: 32px; }
`;

export const PlanDetail = styled.div`
  display: flex; align-items: center; gap: 20px; background: #f8fafc;
  padding: 20px; border-radius: 16px; margin-bottom: 32px;
  .icon-box { background: var( --lightblue); color: white; width: 48px; height: 48px; 
    border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
  .details { display: flex; flex-direction: column; 
    strong { font-size: 1.1rem; color: #0f172a; }
    span { color: #64748b; font-size: 0.9rem; }
  }
`;

export const PriceTable = styled.div`
  .row { display: flex; justify-content: space-between; padding: 12px 0; color: #64748b;
    &.total { border-top: 2px solid #f1f5f9; margin-top: 12px; padding-top: 20px;
      font-weight: 800; font-size: 1.25rem; color: #0f172a; }
  }
`;

export const PaymentCard = styled.div`
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 24px; padding: 40px;
  text-align: center;
  h3 { font-size: 1.25rem; margin-bottom: 12px; }
  p { font-size: 0.9rem; color: #64748b; margin-bottom: 32px; }
`;

export const PayButton = styled.button`
  width: 100%; padding: 18px; background: #0f172a; color: white; border: none;
  border-radius: 14px; font-weight: 700; font-size: 1.1rem; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 12px;
  transition: transform 0.2s;
  &:hover { transform: translateY(-2px); background: #1e293b; }
`;

export const SecureNote = styled.span`
  display: block; margin-top: 20px; font-size: 0.8rem; color: #94a3b8;
`;