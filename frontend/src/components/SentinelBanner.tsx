import React, { useEffect, useRef } from 'react';
import './SentinelBanner.css';

interface SentinelBannerProps {
  className?: string;
}

const SentinelBanner: React.FC<SentinelBannerProps> = ({ className = '' }) => {
  const bannerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const banner = bannerRef.current;
    if (!banner) return;
    
    // Add hover effects to capabilities list items
    const capabilityItems = banner.querySelectorAll('.capabilities li');
    capabilityItems.forEach(item => {
      item.addEventListener('mouseenter', function(this: HTMLElement) {
        this.style.transform = 'translateX(10px)';
        this.style.color = '#00b4d8';
      });
      
      item.addEventListener('mouseleave', function(this: HTMLElement) {
        this.style.transform = 'translateX(0)';
        this.style.color = '';
      });
    });
    
    // Add pulse animation to webhook types
    const webhookTypes = banner.querySelectorAll('.webhook-type');
    webhookTypes.forEach(type => {
      type.addEventListener('click', function(this: HTMLElement) {
        this.classList.add('pulse');
        setTimeout(() => {
          this.classList.remove('pulse');
        }, 1000);
      });
    });
    
    // Add tooltip functionality to code elements
    const codeElements = banner.querySelectorAll('code');
    codeElements.forEach(code => {
      const tooltip = document.createElement('div');
      tooltip.className = 'code-tooltip';
      tooltip.textContent = 'Click to copy';
      code.appendChild(tooltip);
      
      code.addEventListener('click', function(this: HTMLElement) {
        const text = this.textContent;
        if (text) {
          navigator.clipboard.writeText(text).then(() => {
            tooltip.textContent = 'Copied!';
            setTimeout(() => {
              tooltip.textContent = 'Click to copy';
            }, 2000);
          });
        }
      });
    });
    
    // Add mutation effect to the motto
    const motto = banner.querySelector('.motto');
    if (motto && motto.textContent) {
      const originalText = motto.textContent;
      const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
      
      motto.addEventListener('mouseenter', function() {
        let iteration = 0;
        const interval = setInterval(() => {
          if (motto.textContent) {
            motto.textContent = originalText
              .split('')
              .map((letter, index) => {
                if (index < iteration) {
                  return originalText[index];
                }
                if (letter === ' ') return ' ';
                if (letter === '.') return '.';
                return letters[Math.floor(Math.random() * 26)];
              })
              .join('');
          }
          
          if (iteration >= originalText.length) {
            clearInterval(interval);
          }
          
          iteration += 1 / 3;
        }, 30);
      });
    }

    // Cleanup event listeners on component unmount
    return () => {
      capabilityItems.forEach(item => {
        item.removeEventListener('mouseenter', () => {});
        item.removeEventListener('mouseleave', () => {});
      });
      
      webhookTypes.forEach(type => {
        type.removeEventListener('click', () => {});
      });
      
      codeElements.forEach(code => {
        code.removeEventListener('click', () => {});
      });
      
      if (motto) {
        motto.removeEventListener('mouseenter', () => {});
      }
    };
  }, []);

  return (
    <div ref={bannerRef} className={`sentinel-banner ${className}`}>
      <div className="banner-header">
        <h1>🧬 Mutation Sentinel <span className="version">v0.5</span></h1>
      </div>
      
      <div className="banner-content">
        <div className="capabilities">
          <h2>Your Trading Sentinel Powers:</h2>
          <ul>
            <li><span className="icon">🧠</span> Mutation on demand via prompt or API</li>
            <li><span className="icon">🌐</span> Broker-agnostic trade execution</li>
            <li><span className="icon">⚡</span> JavaScript-aware Selenium intelligence</li>
            <li><span className="icon">☁️</span> Cloud-native deployment at scale</li>
            <li><span className="icon">📱</span> Live UI control from mobile, browser, or bot</li>
          </ul>
        </div>
        
        <div className="webhook-info">
          <h2>🔔 Webhook Infrastructure</h2>
          <div className="webhook-types">
            <div className="webhook-type">
              <h3>✅ Trade Webhooks</h3>
              <p>Execute trades via <code>/api/trade/stealth</code> or <code>/api/webhook</code></p>
            </div>
            <div className="webhook-type">
              <h3>📢 Slack Webhooks</h3>
              <p>Real-time notifications for login status, trades, and errors</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="banner-footer">
        <p className="motto">Adapt. Scale. Mutate.</p>
        <p className="tagline">Trade smarter — without borders, without breaks.</p>
      </div>


    </div>
  );
};

export default SentinelBanner;