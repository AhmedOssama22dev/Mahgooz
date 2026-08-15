import { defineConfig, loadEnv } from 'vite'
import type { Plugin } from 'vite'
import { devtools } from '@tanstack/devtools-vite'

import { tanstackRouter } from '@tanstack/router-plugin/vite'

import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

import { handleMock } from './src/lib/api/mock.ts'

const API_PREFIX = '/api/v1'

function mahgouzMockPlugin(): Plugin {
  return {
    name: 'mahgouz-mock',
    configureServer(server) {
      console.info(
        `[mahgouz] mock API at ${API_PREFIX} (set VITE_API_BASE_URL to use the backend)`,
      )
      server.middlewares.use((req, res, next) => {
        const url = new URL(req.url ?? '/', 'http://mahgouz.local')
        if (!url.pathname.startsWith(API_PREFIX)) {
          next()
          return
        }

        let raw = ''
        req.on('data', (chunk: string | Uint8Array) => {
          raw +=
            typeof chunk === 'string' ? chunk : new TextDecoder().decode(chunk)
        })
        req.on('end', () => {
          let body: unknown
          if (raw) {
            try {
              body = JSON.parse(raw)
            } catch {
              res.statusCode = 400
              res.setHeader('Content-Type', 'application/json')
              res.end(
                JSON.stringify({
                  error: { code: 'INVALID_JSON', message: 'Invalid JSON body' },
                }),
              )
              return
            }
          }

          const path = url.pathname.slice(API_PREFIX.length) || '/'
          const result = handleMock({
            method: req.method ?? 'GET',
            path,
            query: url.searchParams,
            body,
            authorization: header(req.headers.authorization),
          })
          res.statusCode = result.status
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify(result.body))
        })
      })
    },
  }
}

function header(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value
}

function backendOrigin(apiBase: string | undefined) {
  if (!apiBase?.trim() || !/^https?:\/\//.test(apiBase)) return undefined
  return new URL(apiBase).origin
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const origin = backendOrigin(env.VITE_API_BASE_URL)

  return {
    resolve: { tsconfigPaths: true },
    server: origin
      ? {
          proxy: {
            '/api': { target: origin, changeOrigin: true },
          },
        }
      : undefined,
    plugins: [
      ...(!origin ? [mahgouzMockPlugin()] : []),
      devtools(),
      tailwindcss(),
      tanstackRouter({ target: 'react', autoCodeSplitting: true }),
      viteReact(),
    ],
  }
})
