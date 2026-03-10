import React from 'react';
import { Container, Content, DisclaimerText } from "./FooterStyles";

export default function Footer() {
  return (
    <Container>
      <Content>
        <DisclaimerText>
          Flowtru is an AI and can make mistakes. Please confirm important information.
        </DisclaimerText>
      </Content>
    </Container>
  );
}