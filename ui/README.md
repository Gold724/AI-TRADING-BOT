# AI Trading Sentinel UI Components

## Overview

This directory contains standalone UI components that can be used independently or integrated into the main React frontend application. These components showcase the system's capabilities and provide visual elements for the AI Trading Sentinel system.

## Components

### Mutation Sentinel Banner

The banner is a visual representation of the system's capabilities, including:

- Mutation capabilities
- Broker-agnostic trade execution
- JavaScript-aware Selenium intelligence
- Cloud-native deployment
- Live UI control
- Webhook infrastructure

#### Files

- `banner.html` - The HTML structure of the banner
- `banner.js` - Interactive JavaScript elements
- `banner_preview.html` - A standalone preview page for the banner

#### Integration with Frontend

The banner has been integrated into the React frontend as a component. See `frontend/BANNER_INTEGRATION.md` for details on how this was done and how to customize it further.

## Usage

### Standalone Usage

You can use the banner as a standalone component by including the HTML and JavaScript files in your project:

```html
<!-- Include the banner HTML -->
<div id="banner-container"></div>
<script>
  // Load the banner HTML into the container
  fetch('path/to/banner.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('banner-container').innerHTML = html;
      
      // Load the banner JavaScript
      const script = document.createElement('script');
      script.src = 'path/to/banner.js';
      document.body.appendChild(script);
    });
</script>
```

### Iframe Embedding

You can also embed the banner using an iframe:

```html
<iframe src="path/to/banner_preview.html" width="100%" height="400" frameborder="0"></iframe>
```

## Preview

To preview the banner locally:

1. Navigate to the `ui` directory
2. Start a simple HTTP server:
   ```
   python -m http.server 8000
   ```
3. Open a browser and go to `http://localhost:8000/banner_preview.html`

## Customization

### Styling

The banner uses a dark theme with blue accents by default. You can customize the colors by modifying the CSS variables in the `<style>` section of `banner.html`.

### Content

To update the content of the banner, modify the HTML structure in `banner.html`. The main sections are:

- Banner header (title and version)
- Capabilities list
- Webhook information
- Footer with motto and tagline

### Interactive Elements

The interactive elements are defined in `banner.js`. You can modify or add new interactions by editing this file.

## React Integration

For details on how the banner has been integrated into the React frontend, see the `frontend/BANNER_INTEGRATION.md` file.