/**
 * Mutation Sentinel Banner Interactive Elements
 * Enhances the static banner with interactive elements and animations
 */

document.addEventListener('DOMContentLoaded', function() {
  // Get banner elements
  const banner = document.querySelector('.sentinel-banner');
  if (!banner) return;
  
  // Add hover effects to capabilities list items
  const capabilityItems = banner.querySelectorAll('.capabilities li');
  capabilityItems.forEach(item => {
    item.addEventListener('mouseenter', function() {
      this.style.transform = 'translateX(10px)';
      this.style.color = '#00b4d8';
    });
    
    item.addEventListener('mouseleave', function() {
      this.style.transform = 'translateX(0)';
      this.style.color = '';
    });
  });
  
  // Add pulse animation to webhook types
  const webhookTypes = banner.querySelectorAll('.webhook-type');
  webhookTypes.forEach(type => {
    type.addEventListener('click', function() {
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
    
    code.addEventListener('click', function() {
      const text = this.textContent;
      navigator.clipboard.writeText(text).then(() => {
        tooltip.textContent = 'Copied!';
        setTimeout(() => {
          tooltip.textContent = 'Click to copy';
        }, 2000);
      });
    });
  });
  
  // Add mutation effect to the motto
  const motto = banner.querySelector('.motto');
  if (motto) {
    const originalText = motto.textContent;
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    
    motto.addEventListener('mouseenter', function() {
      let iteration = 0;
      const interval = setInterval(() => {
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
        
        if (iteration >= originalText.length) {
          clearInterval(interval);
        }
        
        iteration += 1 / 3;
      }, 30);
    });
  }
  
  // Add CSS for animations
  const style = document.createElement('style');
  style.textContent = `
    .sentinel-banner .capabilities li {
      transition: transform 0.3s ease, color 0.3s ease;
    }
    
    .sentinel-banner .webhook-type {
      cursor: pointer;
      transition: background-color 0.3s ease;
    }
    
    .sentinel-banner .webhook-type:hover {
      background-color: rgba(0, 180, 216, 0.2);
    }
    
    .sentinel-banner .pulse {
      animation: pulse 1s;
    }
    
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(0, 180, 216, 0.7); }
      70% { box-shadow: 0 0 0 10px rgba(0, 180, 216, 0); }
      100% { box-shadow: 0 0 0 0 rgba(0, 180, 216, 0); }
    }
    
    .sentinel-banner code {
      cursor: pointer;
      position: relative;
    }
    
    .sentinel-banner .code-tooltip {
      position: absolute;
      bottom: 100%;
      left: 50%;
      transform: translateX(-50%);
      background-color: #1a1a2e;
      color: #e6e6e6;
      padding: 5px 8px;
      border-radius: 4px;
      font-size: 12px;
      opacity: 0;
      transition: opacity 0.3s ease;
      pointer-events: none;
      white-space: nowrap;
      z-index: 10;
    }
    
    .sentinel-banner code:hover .code-tooltip {
      opacity: 1;
    }
    
    .sentinel-banner .motto {
      cursor: pointer;
    }
  `;
  document.head.appendChild(style);
});