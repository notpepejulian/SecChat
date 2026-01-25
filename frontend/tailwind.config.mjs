/** @type {import('tailwindcss').Config} */
export default {
  content: [
      './src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}',
  ],
  theme: {
      extend: {
          colors: {
              // Definición de la paleta moderna 'primary' (Morado)
              primary: {
                  50: '#F5F3FF',
                  100: '#EDE9FE',
                  200: '#DDD6FE',
                  300: '#C4B5FD',
                  400: '#A78BFA',
                  500: '#8B5CF6', // Tono principal
                  600: '#7C3AED',
                  700: '#6D28D9',
                  800: '#5B21B6',
                  900: '#4C1D95',
                  950: '#2F1360',
              },
              // Definición de la paleta 'dark' (Negro/Gris Oscuro)
              dark: {
                  50: '#18181B', // Base más oscura
                  100: '#27272A', // Fondo de tarjetas
                  200: '#3F3F46', // Bordes y separadores
                  900: '#09090B', // Tono más profundo
              }
          },
          fontFamily: {
              sans: ['Inter', 'sans-serif'], // Fuente moderna
          },
      },
  },
  plugins: [],
}