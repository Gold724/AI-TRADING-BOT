# Mutation Sentinel Banner Integration Guide

## Overview

This guide explains how the Mutation Sentinel Banner has been integrated into the AI Trading Sentinel system and provides instructions for different integration scenarios.

## Integration Options

The banner can be integrated in several ways:

1. **React Component Integration** - The banner has been converted to a React component and integrated into the main frontend application.
2. **Standalone HTML/JS** - The original HTML/JS implementation can be used independently.
3. **Iframe Embedding** - The banner can be embedded as an iframe in any web page.

## React Component Integration

### Files Created

- `frontend/src/components/SentinelBanner.tsx` - The React component
- `frontend/src/components/SentinelBanner.css` - The component's styles
- `frontend/src/components/SentinelBanner.test.tsx` - Tests for the component
- `frontend/src/setupTests.ts` - Jest setup for testing
- `frontend/jest.config.js` - Jest configuration

### Integration in App.tsx

The banner has been added to the main layout in `App.tsx`:

```tsx
import SentinelBanner from './components/SentinelBanner';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-gray-800 text-white p-4">
          {/* ... */}
        </nav>

        <div className="container mx-auto py-6">
          <SentinelBanner className="mb-6" />
          <Routes>
            {/* ... */}
          </Routes>
        </div>

        <footer className="bg-gray-800 text-white p-4 mt-8">
          {/* ... */}
        </footer>
      </div>
    </Router>
  );
}
```

### Testing the Integration

To test the React component integration:

1. Install the required dependencies:
   ```
   cd frontend
   npm install
   ```

2. Run the tests:
   ```
   npm test
   ```

   Or use the provided test scripts:
   ```
   # Windows
   .\test_banner_integration.bat

   # Unix/Linux/macOS
   ./test_banner_integration.sh
   ```

## Standalone HTML/JS Integration

The original HTML/JS implementation can be used independently in any web application.

### Files

- `ui/banner.html` - The HTML structure and CSS
- `ui/banner.js` - The interactive JavaScript

### Integration Steps

1. Copy the `banner.html` and `banner.js` files to your project.

2. Include the banner in your HTML:
   ```html
   <div id="banner-container"></div>
   <script>
     // Load the banner HTML
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

## Iframe Embedding

The banner can be embedded as an iframe in any web page.

### Files

- `ui/banner_preview.html` - A standalone preview page for the banner

### Integration Steps

1. Copy the `ui` directory to your web server.

2. Embed the banner using an iframe:
   ```html
   <iframe src="path/to/banner_preview.html" width="100%" height="400" frameborder="0"></iframe>
   ```

## Customization

### Content Customization

To update the content of the banner:

#### React Component

Edit the JSX in `frontend/src/components/SentinelBanner.tsx`.

#### Standalone HTML

Edit the HTML structure in `ui/banner.html`.

### Style Customization

To modify the styles:

#### React Component

Edit the CSS in `frontend/src/components/SentinelBanner.css`.

#### Standalone HTML

Edit the `<style>` section in `ui/banner.html`.

### Interactive Features

To modify the interactive features:

#### React Component

Edit the `useEffect` hook in `frontend/src/components/SentinelBanner.tsx`.

#### Standalone HTML

Edit the JavaScript in `ui/banner.js`.

## Troubleshooting

### React Component Issues

- **CSS Conflicts**: If you experience styling conflicts, make the CSS more specific by prefixing all selectors with `.sentinel-banner`.
- **Event Listener Cleanup**: Ensure all event listeners are properly cleaned up in the `useEffect` return function.
- **Testing Issues**: Make sure all testing dependencies are installed and the Jest configuration is correct.
- **Environment Variables**: If you see a `process is not defined` error, make sure to use `import.meta.env.VITE_*` instead of `process.env.REACT_APP_*` since the project uses Vite.

### API Connection Issues

- **API Errors**: When running the frontend without the backend, you'll see API connection errors in the console. These are expected and don't affect the banner functionality.
- **Backend Connection**: To fully test the application, start the backend server as well.

### Standalone HTML Issues

- **Script Loading**: Ensure the `banner.js` file is loaded after the HTML content is inserted.
- **CSS Conflicts**: If you experience styling conflicts, wrap the banner in a container with a unique ID and scope the CSS to that ID.

## Additional Resources

- `frontend/BANNER_INTEGRATION.md` - Detailed information about the React component integration
- `ui/README.md` - Information about the standalone UI components

## Next Steps

1. **State Management**: Consider moving the banner content to a state management solution if it needs to be dynamic.
2. **Theme Integration**: The banner could be updated to use the application's theme system if one exists.
3. **Animation Library**: For more complex animations, consider using a library like Framer Motion instead of direct DOM manipulation.