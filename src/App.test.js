import { render, screen } from '@testing-library/react';
import App from './App';

test('renders RAG research system title', () => {
  render(<App />);
  const titleElement = screen.getByText(/RAG-based Research Assistance System/i);
  expect(titleElement).toBeInTheDocument();
});
