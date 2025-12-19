# RAG Research Assistant

A research assistance system based on RAG (Retrieval-Augmented Generation).

## Requirements

- Node.js 18+ or 20+ (LTS version)
- npm 9+

## Quick Start

### Install Dependencies

```bash
npm install
```

### Start Development Server

```bash
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### Run Tests

```bash
npm test
```

Launches the test runner in interactive watch mode.\
Non-interactive mode: `npm test -- --watchAll=false`

Non-interactive mode: `npm test -- --watchAll=false`

### Production Build

```bash
npm run build
```

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

## Features

- **File Upload**: Upload research documents
- **Document Search**: RAG-based intelligent search
- **Document Display**: View search results and document content

## Troubleshooting

### "command not found" error

Make sure Node.js and npm are installed correctly. Check versions:

```bash
node -v
npm -v
```

### Permission denied error

If files in `node_modules/.bin/` don't have execute permission:

```bash
chmod +x node_modules/.bin/*
```


## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
