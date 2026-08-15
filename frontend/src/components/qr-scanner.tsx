import jsQR from 'jsqr'
import { useEffect, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { bookingCodeFromQr } from '@/lib/booking-code'

type StaffQrScannerProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onDetect: (code: string) => void
}

/** Rear-camera QR scan → booking code. Stops as soon as one valid code is found. */
export function StaffQrScanner({
  open,
  onOpenChange,
  onDetect,
}: StaffQrScannerProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Scan pass QR</DialogTitle>
          <DialogDescription>
            Point the camera at the customer&apos;s pass.
          </DialogDescription>
        </DialogHeader>
        {open ? (
          <CameraFeed
            onDetect={(code) => {
              onOpenChange(false)
              onDetect(code)
            }}
          />
        ) : null}
        <Button variant="outline" onClick={() => onOpenChange(false)}>
          Cancel
        </Button>
      </DialogContent>
    </Dialog>
  )
}

function CameraFeed({ onDetect }: { onDetect: (code: string) => void }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [error, setError] = useState<string | null>(null)
  const onDetectRef = useRef(onDetect)
  onDetectRef.current = onDetect

  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Camera needs HTTPS (or localhost).')
      return
    }

    let stopped = false
    let stream: MediaStream | undefined
    let timer = 0
    const canvas = document.createElement('canvas')

    async function start(preview: HTMLVideoElement) {
      try {
        const media = await navigator.mediaDevices.getUserMedia({
          audio: false,
          video: { facingMode: { ideal: 'environment' } },
        })
        stream = media
        if (stopped) {
          media.getTracks().forEach((t) => t.stop())
          return
        }
        preview.srcObject = media
        await preview.play()
      } catch {
        if (!stopped) setError('Allow camera to scan a pass.')
        return
      }

      const tick = () => {
        if (stopped) return
        const raw = readQr(preview, canvas)
        const code = raw ? bookingCodeFromQr(raw) : null
        if (code) {
          onDetectRef.current(code)
          return
        }
        timer = window.setTimeout(tick, 150)
      }
      tick()
    }

    void start(video)
    return () => {
      stopped = true
      window.clearTimeout(timer)
      stream?.getTracks().forEach((t) => t.stop())
      video.srcObject = null
    }
  }, [])

  return (
    <>
      <video
        ref={videoRef}
        className="aspect-4/3 w-full rounded-[12px] bg-black object-cover"
        playsInline
        muted
        autoPlay
      />
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </>
  )
}

function readQr(video: HTMLVideoElement, canvas: HTMLCanvasElement) {
  const w = video.videoWidth
  const h = video.videoHeight
  if (!w || !h) return null
  const scale = Math.min(1, 480 / w)
  canvas.width = Math.round(w * scale)
  canvas.height = Math.round(h * scale)
  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  if (!ctx) return null
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  const img = ctx.getImageData(0, 0, canvas.width, canvas.height)
  return (
    jsQR(img.data, img.width, img.height, { inversionAttempts: 'dontInvert' })
      ?.data ?? null
  )
}
