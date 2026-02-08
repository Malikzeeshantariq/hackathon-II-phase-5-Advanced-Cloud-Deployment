// T006: Tailwind CSS Configuration
// Spec Reference: plan.md - Styling: Tailwind CSS

import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors can be added here
      },
    },
  },
  plugins: [],
}

export default config
