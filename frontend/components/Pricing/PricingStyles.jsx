"use client";
import styled, { keyframes, css } from "styled-components";

const fadeInUp = keyframes`
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
`;

export const PageContainer = styled.div`
  max-width: 1240px;
  margin: 0 auto;
  padding: 60px 24px 100px;
  background: #ffffff;
  font-family: var(--font-geist-sans), sans-serif;
  animation: ${fadeInUp} 0.8s cubic-bezier(0.16, 1, 0.3, 1);
`;

export const BackButton = styled.button`
  display: flex; align-items: center; gap: 10px; background: none; border: none;
  color: #64748b; font-weight: 600; cursor: pointer; margin-bottom: 40px;
  transition: all 0.3s ease;
  &:hover { color: var(--darkblue); transform: translateX(-5px); }
`;

export const HeaderSection = styled.div`
  text-align: center; margin-bottom: 48px;
  h1 { font-size: clamp(2rem, 5vw, 3.5rem); font-family:var(--font-geist-sans); font-weight: 800; color: #000000; letter-spacing: -0.02em; }
  p { color: #64748b; font-size: 1.1rem; margin-top: 16px;  font-family:(--font-geist-sans);}
`;

export const Chip = styled.span`
  background: #eff6ff; color: var(--lightblue); padding: 8px 20px; border-radius: 99px;
  font-size: 0.8rem; font-weight: 800; text-transform: uppercase;
`;

export const ToggleWrapper = styled.div`
  display: flex; justify-content: center; align-items: center; gap: 20px; margin-bottom: 60px;
`;

export const ToggleLabel = styled.span`
  font-weight: 700; font-size: 0.95rem;
  color: ${props => props.$active ? '#0f172a' : '#94a3b8'};
  transition: color 0.3s;
`;

export const Switch = styled.div`
  width: 54px; height: 28px; background: #0f172a; border-radius: 30px; position: relative; cursor: pointer;
  &::after {
    content: ''; position: absolute; width: 22px; height: 22px; background: white; border-radius: 50%;
    top: 3px; left: ${props => props.$isYearly ? '29px' : '3px'}; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }
`;

export const DiscountBadge = styled.span`
  background: #dcfce7; color: #15803d; padding: 2px 10px; border-radius: 8px; font-size: 0.75rem; margin-left: 8px;
`;

export const SliderCard = styled.div`
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 24px;
  padding: clamp(24px, 5vw, 48px); margin-bottom: 64px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);

  .card-top {
    display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 40px;
    @media (max-width: 768px) { flex-direction: column; align-items: center; text-align: center; gap: 24px; }
  }

  .text-group h3 { font-size: 1.5rem; color: #0f172a; font-weight: 700; }
  .text-group p { color: #64748b; margin-top: 4px; }

  .val-group {
      text-align: right;
      .num { display: block; font-size: 3rem; font-weight: 900; color: #2563eb; line-height: 1; }
      .unit { color: #64748b; font-weight: 600; font-size: 1rem; }
  }
`;

export const SliderBox = styled.div`
  position: relative; padding: 20px 0;
  input[type=range] {
    width: 100%; -webkit-appearance: none; background: transparent; position: relative; z-index: 10;
    &::-webkit-slider-thumb {
      -webkit-appearance: none; height: 32px; width: 32px; border-radius: 50%; background: #2563eb;
      border: 4px solid #fff; box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3); cursor: grab;
    }
  }
`;

export const TrackFill = styled.div`
  position: absolute; top: 33px; height: 8px; width: 100%; background: #e2e8f0; border-radius: 4px;
  &::after {
    content: ''; position: absolute; height: 100%; width: ${props => props.$progress}%; 
    background: #2563eb; border-radius: 4px;
  }
`;

export const TicksContainer = styled.div`
  position: relative; height: 40px; margin-top: 20px; width: 100%;
`;

export const TickMarker = styled.div`
  position: absolute;
  left: ${props => props.$left}%;
  transform: translateX(-50%); 
  display: flex; flex-direction: column; align-items: center;
  transition: all 0.2s ease;
  min-width: 40px; 

  .line {
    width: 2px;
    height: ${props => props.$current ? '14px' : '8px'};
    background: ${props => props.$active ? '#2563eb' : '#cbd5e1'};
  }

  span {
    font-size: 0.75rem; margin-top: 10px; white-space: nowrap;
    font-weight: ${props => props.$current ? '800' : '600'};
    color: ${props => props.$current ? '#2563eb' : '#94a3b8'};
  }
`;

export const PlanGrid = styled.div`
  display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 32px;
`;

export const PlanCard = styled.div`
  background: #fff; border: 2px solid ${props => props.$featured ? '#2563eb' : '#f1f5f9'};
  border-radius: 24px; padding: 40px; display: flex; flex-direction: column; position: relative;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1);
  ${props => props.$disabled && css` opacity: 0.5; filter: grayscale(1); pointer-events: none; `}
  &:hover { transform: translateY(-10px); box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
`;

export const FeaturedBadge = styled.div`
  position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: #2563eb;
  color: white; padding: 4px 16px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
`;

export const PlanInfo = styled.div` margin-bottom: 32px; `;
export const PlanName = styled.h3` font-size: 1.75rem; font-weight: 800; color: #0f172a; `;
export const PlanDesc = styled.p` color: #64748b; font-size: 0.95rem; margin-top: 8px; line-height: 1.5; `;

export const PriceArea = styled.div`
  margin-bottom: 32px;
  .price-val { font-size: 2.5rem; font-weight: 900; color: #0f172a; span { font-size: 1.5rem; color: #94a3b8; } }
  .price-sub { color: #64748b; font-size: 0.95rem; font-weight: 600; }
`;

export const FeatureList = styled.ul`
  list-style: none; padding: 0; margin-bottom: 40px; flex-grow: 1;
  li { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; color: #475569; font-size: 0.95rem; .icon { color: #22c55e; flex-shrink: 0; } }
`;

export const PlanButton = styled.button`
  width: 100%; padding: 16px; border-radius: 12px; border: none; font-weight: 700; font-size: 1rem; cursor: pointer;
  background: ${props => props.$primary ? '#2563eb' : '#f8fafc'};
  color: ${props => props.$primary ? '#fff' : '#0f172a'};
  transition: all 0.2s;
  &:hover { background: ${props => props.$primary ? '#1d4ed8' : '#e2e8f0'}; transform: scale(1.02); }
`;