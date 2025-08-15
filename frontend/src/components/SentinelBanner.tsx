import React, { useEffect, useRef, useState } from 'react';
import './SentinelBanner.css';

interface SentinelBannerProps {
  className?: string;
}

const SentinelBanner: React.FC<SentinelBannerProps> = ({ className = '' }) => {
  const bannerRef = useRef<HTMLDivElement>(null);
  const [btcPrice, setBtcPrice] = useState('105,498.76');
  const [btcChange, setBtcChange] = useState('+2.500%');
  const [volume, setVolume] = useState('$2.14B');
  const [volumeChange, setVolumeChange] = useState('+5.2%');
  const [currentSignal, setCurrentSignal] = useState('WAIT');
  const [confidence, setConfidence] = useState('39%');
  const [pnlToday, setPnlToday] = useState('+$1,247.83');
  const [activeTrades, setActiveTrades] = useState('3');
  const [nextUpdate, setNextUpdate] = useState('04:00:00');
  
  // Simulate countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setNextUpdate(prev => {
        const [hours, minutes, seconds] = prev.split(':').map(Number);
        let newSeconds = seconds - 1;
        let newMinutes = minutes;
        let newHours = hours;
        
        if (newSeconds < 0) {
          newSeconds = 59;
          newMinutes -= 1;
        }
        
        if (newMinutes < 0) {
          newMinutes = 59;
          newHours -= 1;
        }
        
        if (newHours < 0) {
          return '04:00:00';
        }
        
        return `${newHours.toString().padStart(2, '0')}:${newMinutes.toString().padStart(2, '0')}:${newSeconds.toString().padStart(2, '0')}`;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);

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
        item.removeEventListener('mouseenter', function() { this.style.transform = 'translateX(10px)'; this.style.color = '#00b4d8'; });
        item.removeEventListener('mouseleave', function() { this.style.transform = 'translateX(0)'; this.style.color = ''; });
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
        <h1>
          <img src="/logo.svg" alt="AI Trading Sentinel" className="logo" />
          <span className="version">v2.0</span>
        </h1>
      </div>
      
      <div className="banner-content">
        <div className="dashboard-grid">
          {/* Main stats row */}
          <div className="main-stats">
            <div className="stat-card">
              <div className="stat-title">BTC/USD</div>
              <div className="stat-value">${btcPrice}</div>
              <div className={`stat-change ${btcChange.startsWith('+') ? 'positive' : 'negative'}`}>{btcChange}</div>
            </div>
            
            <div className="stat-card">
              <div className="stat-title">Next Update In</div>
              <div className="stat-value countdown">{nextUpdate}</div>
            </div>
            
            <div className="stat-card">
              <div className="stat-title">Current Signal (4H)</div>
              <div className={`stat-value signal ${currentSignal.toLowerCase()}`}>{currentSignal}</div>
              <div className="stat-subtitle">Confidence {confidence}</div>
            </div>
          </div>
          
          {/* Analysis section */}
          <div className="analysis-section">
            <h2>Real-time Volume Analysis</h2>
            <div className="analysis-tags">
              <span className="analysis-tag">Liquidity-based signals only</span>
              <span className="analysis-tag highlight">MEDIUM Volume</span>
              <span className="analysis-tag">NO LAGGING INDICATORS</span>
            </div>
          </div>
          
          {/* Metrics section */}
          <div className="metrics-section">
            <h2>Key Metrics</h2>
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="metric-label">24h Volume</div>
                <div className="metric-value">{volume} <span className="metric-change">{volumeChange}</span></div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Liquidity Score</div>
                <div className="metric-value">78<span className="metric-unit">/100</span></div>
              </div>
              <div className="metric-item">
                <div className="metric-label">P&L Today</div>
                <div className={`metric-value ${pnlToday.startsWith('+') ? 'positive' : 'negative'}`}>{pnlToday}</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">Active Trades</div>
                <div className="metric-value">{activeTrades}</div>
              </div>
            </div>
          </div>
          
          {/* ML Performance */}
          <div className="ml-performance">
            <h2>ML Performance</h2>
            <div className="performance-stats">
              <div className="performance-item">
                <div className="performance-label">Model Accuracy</div>
                <div className="performance-value">87.3%</div>
              </div>
              <div className="performance-item">
                <div className="performance-label">Learning Status</div>
                <div className="performance-value offline">OFFLINE</div>
              </div>
              <div className="performance-item">
                <div className="performance-label">Signal Quality</div>
                <div className="performance-value high">HIGH</div>
              </div>
              <div className="performance-item">
                <div className="performance-label">Model Version</div>
                <div className="performance-value">v2.0</div>
              </div>
            </div>
          </div>
          
          {/* Confluence Analysis */}
          <div className="confluence-analysis">
            <h2>Smart Money Confluence Analysis</h2>
            <div className="confluence-total">
              <div className="confluence-label">Total Confluence</div>
              <div className="confluence-value">58%</div>
            </div>
            <div className="confluence-grid">
              <div className="confluence-item">
                <div className="confluence-name">liquidity Sweep</div>
                <div className="confluence-score">0/20</div>
              </div>
              <div className="confluence-item">
                <div className="confluence-name">Equal highs/lows detection</div>
                <div className="confluence-score">fair</div>
              </div>
              <div className="confluence-item">
                <div className="confluence-name">Value Gap</div>
                <div className="confluence-score">12/15</div>
              </div>
              <div className="confluence-item">
                <div className="confluence-name">Imbalance zones</div>
                <div className="confluence-score">ote Zone</div>
              </div>
              <div className="confluence-item">
                <div className="confluence-name">15/20</div>
                <div className="confluence-score">61.8-79% Fibonacci</div>
              </div>
              <div className="confluence-item">
                <div className="confluence-name">volume Analysis</div>
                <div className="confluence-score">8/15</div>
              </div>
              <div className="confluence-item">
                <div className="confluence-name">Institutional vs retail</div>
                <div className="confluence-score">market Structure</div>
              </div>
              <div className="confluence-item">
                <div className="confluence-name">10/15</div>
                <div className="confluence-score">Break of structure</div>
              </div>
              <div className="confluence-item">
                <div className="confluence-name">session Timing</div>
                <div className="confluence-score">10/10</div>
              </div>
              <div className="confluence-item">
                <div className="confluence-name">NY/London overlap</div>
                <div className="confluence-score"></div>
              </div>
            </div>
          </div>
          
          {/* Real-Time Signals */}
          <div className="real-time-signals">
            <h2>Real-Time Signals</h2>
            <div className="signal-card">
              <div className="signal-type">Simulated</div>
              <div className="signal-value wait">🟡WAIT</div>
              <div className="signal-strategy">Strategy: FVG + OTE Zone</div>
              <div className="signal-confidence">39% Confidence</div>
              <div className="signal-factors">
                <h3>Active Confluence Factors</h3>
                <div className="factor-item">
                  <div className="factor-name">FVG</div>
                  <div className="factor-value">38%</div>
                </div>
                <div className="factor-item">
                  <div className="factor-name">OTE</div>
                  <div className="factor-value">63%</div>
                </div>
                <div className="factor-item">
                  <div className="factor-name">VOLUME</div>
                  <div className="factor-value">95%</div>
                </div>
              </div>
              <div className="signal-timestamp">Last Update: 4:40:03 AM</div>
            </div>
          </div>
          
          {/* Trade Execution */}
          <div className="trade-execution">
            <h2>Trade Execution</h2>
            <div className="execution-stats">
              <div className="execution-item">
                <div className="execution-label">Daily Trades</div>
                <div className="execution-value">0/5</div>
              </div>
            </div>
            <div className="current-signal">
              <h3>Current Signal</h3>
              <div className="signal-details">
                <div className="signal-row">
                  <div className="signal-label">Signal</div>
                  <div className="signal-value wait">WAIT (39%)</div>
                </div>
                <div className="signal-row">
                  <div className="signal-label">Strategy</div>
                  <div className="signal-value">FVG_OTE</div>
                </div>
                <div className="signal-row">
                  <div className="signal-label">Risk</div>
                  <div className="signal-value">2%</div>
                </div>
                <div className="signal-row">
                  <div className="signal-label">Lot Size</div>
                  <div className="signal-value">0.01 lots</div>
                </div>
              </div>
            </div>
            <div className="risk-management">
              <h3>Risk Management</h3>
              <div className="risk-details">
                <div className="risk-row">
                  <div className="risk-label">Risk per Trade: 2%</div>
                </div>
                <div className="risk-options">
                  <div className="risk-option">Conservative (1%)</div>
                  <div className="risk-option">Aggressive (5%)</div>
                </div>
                <div className="risk-row">
                  <div className="risk-label">Stop Loss</div>
                  <div className="risk-value">-2%</div>
                </div>
                <div className="risk-row">
                  <div className="risk-label">Take Profit</div>
                  <div className="risk-value">+4.0%</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Footer */}
          <div className="dashboard-footer">
            <div className="footer-title">AI Trading Sentinel</div>
            <div className="footer-status">❌ ML Engine - OFFLINE</div>
            <div className="footer-version">v2.0 Enhanced</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SentinelBanner;