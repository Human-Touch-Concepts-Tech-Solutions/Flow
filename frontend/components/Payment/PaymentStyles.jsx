"use client";
import styled, { keyframes, css } from "styled-components";

const fadeInUp = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;


export const PlanInfo = styled.div`
  margin-bottom: 24px;
`;


export const PageContainer = styled.div`
  max-width: 1240px;
  margin: 0 auto;
  padding: 40px 24px 100px;
  background: #ffffff;
  font-family: var(--font-geist-sans), sans-serif;
  animation: ${fadeInUp} 0.5s ease-out;
`;

export const BackButton = styled.button`
  display: flex; align-items: center; gap: 10px; background: #f1f5f9; 
  border: 1px solid #e2e8f0; border-radius: 12px;
  color: #475569; font-weight: 600; cursor: pointer; margin-bottom: 40px;
  padding: 10px 18px; transition: all 0.2s ease;
  &:hover { background: #e2e8f0; transform: translateX(-3px); }
`;

export const HeaderSection = styled.div`
  text-align: left; margin-bottom: 48px;
  h1 { font-size: 2.5rem; font-weight: 800; color: #0f172a; letter-spacing: -0.02em; }
  p { color: #64748b; font-size: 1.1rem; margin-top: 12px; }
`;

export const Chip = styled.span`
  background: #f0fdf4; color: #16a34a; padding: 6px 14px; border-radius: 99px;
  font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 16px;
  display: inline-block;
`;

export const ToggleWrapper = styled.div`
  display: flex; justify-content: flex-start; align-items: center; gap: 20px; margin-bottom: 40px;
`;

export const ToggleLabel = styled.span`
  font-weight: 700; font-size: 0.95rem;
  color: ${props => props.$active ? '#0f172a' : '#94a3b8'};
`;

export const Switch = styled.div`
  width: 50px; height: 26px; background: #0f172a; border-radius: 30px; position: relative; cursor: pointer;
  &::after {
    content: ''; position: absolute; width: 20px; height: 20px; background: white; border-radius: 50%;
    top: 3px; left: ${props => props.$isYearly ? '27px' : '3px'}; transition: 0.2s ease-in-out;
  }
`;

export const DiscountBadge = styled.span`
  background: #dcfce7; color: #15803d; padding: 2px 8px; border-radius: 6px; font-size: 0.7rem;
`;

export const SliderCard = styled.div`
  background: #ffffff; border: 1px solid #e2e8f0; border-radius: 20px;
  padding: 32px; margin-bottom: 48px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);

  .card-top {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;
  }
  .val-group .num { font-size: 2.5rem; font-weight: 800; color: #2563eb; }
  .val-group .unit { color: #64748b; font-weight: 600; }
`;

export const SliderBox = styled.div`
  position: relative; padding: 20px 0;
  input[type=range] {
    width: 100%; -webkit-appearance: none; background: transparent; position: relative; z-index: 10;
    &::-webkit-slider-thumb {
      -webkit-appearance: none; height: 28px; width: 28px; border-radius: 50%; background: #2563eb;
      border: 3px solid #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); cursor: grab;
    }
  }
`;

export const TrackFill = styled.div`
  position: absolute; top: 31px; height: 6px; width: 100%; background: #f1f5f9; border-radius: 10px;
  &::after {
    content: ''; position: absolute; height: 100%; width: ${props => props.$progress}%; 
    background: #2563eb; border-radius: 10px;
  }
`;

export const TicksContainer = styled.div` position: relative; height: 30px; margin-top: 15px; width: 100%; `;

export const TickMarker = styled.div`
  position: absolute; left: ${props => props.$left}%; transform: translateX(-50%); 
  display: flex; flex-direction: column; align-items: center;
  .line { width: 1px; height: 6px; background: ${props => props.$active ? '#2563eb' : '#cbd5e1'}; }
  span { font-size: 0.7rem; margin-top: 6px; color: ${props => props.$current ? '#2563eb' : '#94a3b8'}; font-weight: 600; }
`;

export const PlanGrid = styled.div`
  display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 24px;
`;

export const PlanCard = styled.div`
  background: #fff; border: 1px solid ${props => props.$featured ? '#2563eb' : '#e2e8f0'};
  border-radius: 20px; padding: 32px; display: flex; flex-direction: column; position: relative;
  ${props => props.$disabled && css` opacity: 0.4; pointer-events: none; `}
`;

export const FeaturedBadge = styled.div`
  position: absolute; top: 16px; right: 16px; background: #eff6ff;
  color: #2563eb; padding: 4px 10px; border-radius: 8px; font-size: 0.7rem; font-weight: 700;
`;

export const PlanName = styled.h3` font-size: 1.25rem; font-weight: 700; color: #0f172a; `;
export const PlanDesc = styled.p` color: #64748b; font-size: 0.85rem; margin-top: 4px; `;

export const PriceArea = styled.div`
  margin: 24px 0;
  .price-val { font-size: 2rem; font-weight: 800; color: #0f172a; span { font-size: 1.2rem; color: #94a3b8; } }
  .price-sub { color: #64748b; font-size: 0.85rem; }
`;

export const FeatureList = styled.ul`
  list-style: none; padding: 0; margin-bottom: 32px; flex-grow: 1;
  li { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; color: #475569; font-size: 0.85rem; .icon { color: #22c55e; } }
`;

export const PlanButton = styled.button`
  width: 100%; padding: 14px; border-radius: 10px; border: none; font-weight: 700; cursor: pointer;
  background: ${props => props.$primary ? '#0f172a' : '#f1f5f9'};
  color: ${props => props.$primary ? '#fff' : '#0f172a'};
  &:hover { opacity: 0.9; }
`;

