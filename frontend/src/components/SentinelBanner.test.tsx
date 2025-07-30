import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SentinelBanner from './SentinelBanner';

describe('SentinelBanner', () => {
  test('renders the banner with correct title', () => {
    render(<SentinelBanner />);
    const titleElement = screen.getByText(/Mutation Sentinel/i);
    expect(titleElement).toBeInTheDocument();
  });

  test('renders the version number', () => {
    render(<SentinelBanner />);
    const versionElement = screen.getByText(/v0.5/i);
    expect(versionElement).toBeInTheDocument();
  });

  test('renders all capability items', () => {
    render(<SentinelBanner />);
    const capabilities = [
      'Mutation on demand via prompt or API',
      'Broker-agnostic trade execution',
      'JavaScript-aware Selenium intelligence',
      'Cloud-native deployment at scale',
      'Live UI control from mobile, browser, or bot'
    ];

    capabilities.forEach(capability => {
      const capabilityElement = screen.getByText(capability);
      expect(capabilityElement).toBeInTheDocument();
    });
  });

  test('renders webhook information', () => {
    render(<SentinelBanner />);
    const tradeWebhooksTitle = screen.getByText(/Trade Webhooks/i);
    const slackWebhooksTitle = screen.getByText(/Slack Webhooks/i);
    
    expect(tradeWebhooksTitle).toBeInTheDocument();
    expect(slackWebhooksTitle).toBeInTheDocument();
  });

  test('renders the motto and tagline', () => {
    render(<SentinelBanner />);
    const mottoElement = screen.getByText(/Adapt. Scale. Mutate./i);
    const taglineElement = screen.getByText(/Trade smarter — without borders, without breaks./i);
    
    expect(mottoElement).toBeInTheDocument();
    expect(taglineElement).toBeInTheDocument();
  });

  test('applies custom className', () => {
    render(<SentinelBanner className="custom-class" />);
    const bannerElement = document.querySelector('.sentinel-banner.custom-class');
    expect(bannerElement).toBeInTheDocument();
  });
});