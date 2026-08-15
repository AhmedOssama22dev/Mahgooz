import {
  defineConfig,
  minimal2023Preset,
} from '@vite-pwa/assets-generator/config'

export default defineConfig({
  headLinkOptions: { preset: '2023' },
  preset: {
    ...minimal2023Preset,
    maskable: {
      sizes: [512],
      resizeOptions: { background: '#1B7A4E', fit: 'contain' },
    },
    apple: {
      sizes: [180],
      resizeOptions: { background: '#F4F7F5', fit: 'contain' },
    },
  },
  images: ['public/mahgouz-logo-badge.png'],
})
